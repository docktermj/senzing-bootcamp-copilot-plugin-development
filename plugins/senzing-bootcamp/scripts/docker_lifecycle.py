#!/usr/bin/env python3
"""Shared helper for the bootcamp container lifecycle hooks (INV-101).

Any container the bootcamp starts is recorded in ``config/bootcamp_progress.json``
under a ``docker_containers`` list (each entry carrying at least a ``name``, and a
``runtime`` naming the CLI that started it). This module lets the sessionEnd hook
stop those recorded containers when the session ends, and the sessionStart hook
surface them on resume so the guide can restart or regenerate them.

The bootcamp does not always run on Docker. Docker Desktop cannot be installed
non-interactively (it needs administrator privileges an agent cannot supply), so on
macOS Apple Silicon a bootcamp may legitimately run under Apple's ``container`` CLI
instead. Each entry therefore records the runtime that started it, and every action
here dispatches on that runtime rather than assuming ``docker``. An entry with no
``runtime`` key is treated as ``docker``, so progress files written by earlier runs
keep working unchanged.

The list key stays ``docker_containers`` even though its entries are no longer
Docker-only: renaming it to ``containers`` would read better but would break every
in-flight bootcamp's progress file for a cosmetic gain.

All container-CLI interaction is OPTIONAL and gated on that runtime's CLI being
present: when the CLI is absent, missing, or erroring, every function
warns-and-continues and never blocks the hook. Pure Python 3 stdlib, no third-party
dependency (INV-052/INV-001/INV-002).

This is NOT a hook itself. It is imported by the sessionEnd and sessionStart hook
scripts, which run as ``python3 "<hook>.py"``; Python puts each hook
script's own directory (this ``scripts/`` directory) on ``sys.path``, so
``import docker_lifecycle`` resolves here on Linux, macOS, and Windows alike.
"""
import json
import os
import shutil
import subprocess

PROGRESS = os.path.join("config", "bootcamp_progress.json")

DEFAULT_RUNTIME = "docker"

# Container runtimes the bootcamp can start, mapped to the CLI that manages each.
# Deliberately a closed set: an entry naming anything else is reported but never
# acted on, so a hook cannot be made to execute an arbitrary binary named in a
# progress file, and no speculative runtime gets guidance nobody has exercised.
KNOWN_RUNTIMES = {
    "docker": "docker",
    "podman": "podman",
    "container": "container",  # Apple's container CLI (macOS Apple Silicon)
}

# Runtimes whose CLI implements docker's ``ps -a --filter ... --format ...``
# interface, so a container's state can be read. Apple's ``container`` uses a
# different list syntax that this plugin has not verified, so its state is reported
# as unknown rather than guessed at with a command that would merely fail.
STATE_PROBE_RUNTIMES = ("docker", "podman")


def _load_progress():
    try:
        with open(PROGRESS, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def entry_runtime(entry):
    """Return the runtime recorded for an entry, defaulting to ``docker``.

    Legacy entries (a bare name string, or a dict with no ``runtime``) predate
    runtime recording and were all Docker, so they keep behaving exactly as before.
    """
    runtime = ""
    if isinstance(entry, dict):
        runtime = str(entry.get("runtime") or "").strip().lower()
    return runtime or DEFAULT_RUNTIME


def runtime_cli(runtime):
    """Return the path to the CLI managing ``runtime``, or None.

    None means "do not act": either the runtime is not one the bootcamp starts, or
    its CLI is not on PATH. Both are warn-and-continue conditions, never errors.
    """
    cli = KNOWN_RUNTIMES.get(runtime)
    if not cli:
        return None
    return shutil.which(cli)


def tracked_containers():
    """Return the recorded bootcamp-started containers (list of dicts).

    Each returned entry carries at least a ``name`` and a resolved ``runtime``.
    Tolerates a bare list of name strings, and returns ``[]`` when the field is
    absent or unreadable.
    """
    data = _load_progress()
    if not isinstance(data, dict):
        return []
    raw = data.get("docker_containers") or []
    if not isinstance(raw, list):
        return []
    out = []
    for entry in raw:
        if isinstance(entry, str) and entry.strip():
            out.append({"name": entry.strip(), "runtime": DEFAULT_RUNTIME})
        elif isinstance(entry, dict) and entry.get("name"):
            resolved = dict(entry)
            resolved["runtime"] = entry_runtime(entry)
            out.append(resolved)
    return out


def _run(args, timeout=30):
    """Run a container-CLI command, returning (ok, stdout). Never raises."""
    try:
        proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return proc.returncode == 0, (proc.stdout or "")
    except (OSError, subprocess.SubprocessError):
        return False, ""


def stop_started_containers():
    """Stop each recorded container with the CLI that started it (``<cli> stop``,
    never remove) so it can be restarted on resume. Skips any entry whose runtime
    is unknown or whose CLI is unavailable — the hook never reaches for a different
    CLI than the one that started the container. Returns the names for which a stop
    succeeded. Warn-and-continue on every failure; never raises."""
    stopped = []
    for c in tracked_containers():
        name = c.get("name")
        if not name:
            continue
        cli = runtime_cli(entry_runtime(c))
        if not cli:
            continue
        ok, _ = _run([cli, "stop", name])
        if ok:
            stopped.append(name)
    return stopped


def _container_state(name, runtime=DEFAULT_RUNTIME):
    """Return 'running', 'stopped', 'missing', or 'unknown' for a container.

    'unknown' covers every case the probe cannot answer: an unavailable CLI, a
    failing command, or a runtime with no verified ``ps`` interface.
    """
    cli = runtime_cli(runtime)
    if not cli or runtime not in STATE_PROBE_RUNTIMES:
        return "unknown"
    ok, out = _run(
        [
            cli, "ps", "-a",
            "--filter", "name=^%s$" % name,
            "--format", "{{.Names}}\t{{.State}}",
        ]
    )
    if not ok:
        return "unknown"
    for line in out.splitlines():
        parts = line.split("\t")
        if parts and parts[0] == name:
            state = parts[1].strip().lower() if len(parts) > 1 else ""
            return "running" if state == "running" else "stopped"
    return "missing"


def _group_by_runtime(containers):
    """Group container names by recorded runtime, preserving first-seen order."""
    order = []
    grouped = {}
    for c in containers:
        name = c.get("name")
        if not name:
            continue
        runtime = entry_runtime(c)
        if runtime not in grouped:
            grouped[runtime] = []
            order.append(runtime)
        grouped[runtime].append(name)
    return [(runtime, grouped[runtime]) for runtime in order]


def resume_summary():
    """Return a one-paragraph resume message about recorded containers for the
    guide to act on, or '' when there are none. Names the runtime that actually
    started each container, so the message never claims Docker for a container
    Docker did not start. Never raises."""
    groups = _group_by_runtime(tracked_containers())
    if not groups:
        return ""
    clauses = []
    unavailable = []
    for runtime, names in groups:
        # An unrecognized runtime is reported under the name it was recorded with:
        # the guide can act on it even though this module will not run it.
        cli = KNOWN_RUNTIMES.get(runtime, runtime)
        if runtime_cli(runtime) is None:
            unavailable.append(cli)
            clauses.append(
                "`%s`: %s — the `%s` CLI is not available here"
                % (cli, ", ".join(names), cli)
            )
        else:
            states = ["%s (%s)" % (n, _container_state(n, runtime)) for n in names]
            clauses.append("`%s`: %s" % (cli, ", ".join(states)))
    message = (
        "This bootcamp started container(s) — "
        + "; ".join(clauses)
        + ". Offer to restart any that are stopped, or regenerate any that are "
        "missing, before resuming work that needs them."
    )
    if unavailable:
        seen = sorted(set(unavailable))
        message += (
            " For the container(s) whose CLI is unavailable, offer to help the "
            "bootcamper start %s or regenerate them." % " or ".join(seen)
        )
    return message
