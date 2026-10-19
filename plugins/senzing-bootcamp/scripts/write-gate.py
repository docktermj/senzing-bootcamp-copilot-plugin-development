#!/usr/bin/env python3
"""preToolUse gate for Write/Edit: to block writes outside the Bootcamper's project,
and block obvious secrets -- DURING a bootcamp only.

Two independent checks, governed by two different invariants:

* **Location (INV-200)** -- every file the bootcamp writes lives inside the Bootcamper's
  project. Blocks any resolved target outside it, including one reached by a ``..``
  escape; allows project-relative and in-project absolute paths, including a project
  that legitimately lives beneath a temp directory (resolve, then compare). System temp
  and ``~/Downloads`` are not a separate rule -- they are the cases that get a more
  specific message than the general boundary one.
* **Secrets (INV-109)** -- PEM private keys, AWS access-key IDs and Senzing ``AQAAAD``
  license blobs are blocked whatever the path. Runs independently of the location logic
  and fails closed.

Cross-platform: invoked as a ``type: command`` hook whose ``command`` names the
interpreter and this script, quoted (``python3 "<path>"``), per INV-052.
Native JSON parsing replaces the previous grep/sed field extraction.
"""
import json
import os
import re
import sys

data = sys.stdin.read()

# Gate: only enforce when a bootcamp is active, so the plugin never blocks writes in
# unrelated GitHub Copilot sessions.
if not os.path.isfile(os.path.join("config", "bootcamp_progress.json")):
    sys.exit(0)

LOC_MSG = (
    "Write blocked: use a project-relative path, not a system temp or Downloads "
    "directory."
)
OUTSIDE_MSG = (
    "Write blocked: that path is outside the Bootcamp project. Every file the bootcamp "
    "writes stays inside the project directory -- use a project-relative path."
)
SECRET_MSG = (
    "Write blocked: a possible hardcoded secret was detected. Use environment "
    "variables instead."
)

# System temp / Downloads locations to block (outside-project writes only). Prefix
# entries match the start of the normalized, lower-cased path; substring entries
# match anywhere (Downloads and the Windows temp dir can appear mid-path).
TEMP_PREFIXES = ("/tmp/", "/var/tmp/", "/private/tmp/", "/private/var/folders/")
# `/windows/temp/` is the SYSTEM account's temp dir on Windows (%SystemRoot%\Temp) — the
# Windows counterpart of /tmp, and previously the one uncovered system temp location.
TEMP_SUBSTRINGS = ("/downloads/", "/appdata/local/temp/", "/windows/temp/")


def block(message):
    sys.stderr.write(message + "\n")
    sys.exit(2)


# Extract the write target (tool_input.file_path). Prefer JSON; fall back to a field
# match. File paths do not contain double quotes, so the first match is the real
# target; fail open (allow on location grounds) if extraction yields nothing.
file_path = ""
try:
    file_path = (json.loads(data).get("tool_input") or {}).get("file_path") or ""
except (ValueError, AttributeError):
    m = re.search(r'"file_path"\s*:\s*"([^"]*)"', data)
    file_path = m.group(1) if m else ""

# Expand a leading ~ / ~user so a home-relative target (e.g. ~/Downloads/x) is
# classified by its real location instead of being treated as a bogus in-project
# segment joined onto the cwd. (No-op on empty/absolute/%TEMP% paths.)
if file_path:
    file_path = os.path.expanduser(file_path)

# An unexpanded Windows temp env-var reference (%TEMP%/%TMP%) is always a temp
# target, independent of the project directory. Windows env-var names are
# case-insensitive, so compare case-folded (%Temp%, %tmp%, ... all count).
_fp_upper = file_path.upper()
if "%TEMP%" in _fp_upper or "%TMP%" in _fp_upper:
    block(LOC_MSG)

# Resolve to an absolute path. A relative path is, by definition, inside the project,
# so it is always allowed on location grounds.
if file_path.startswith("/") or re.match(r"^[A-Za-z]:[\\/]", file_path):
    abs_path = file_path                       # POSIX or Windows-drive absolute
elif file_path == "":
    abs_path = ""                              # extraction failed -> fail open
else:
    abs_path = os.path.join(os.getcwd(), file_path)


def norm(path):
    """Backslash-normalize, collapse repeated slashes, and resolve `.`/`..`
    segments (portably, without touching the filesystem) so Windows and POSIX
    targets compare correctly and cannot escape the project via `..`."""
    p = re.sub(r"/+", "/", path.replace("\\", "/"))
    leading = "/" if p.startswith("/") else ""
    out = []
    for seg in p.split("/"):
        if seg in ("", "."):
            continue
        if seg == "..":
            if out and out[-1] != "..":
                out.pop()
            elif not leading:
                out.append("..")
        else:
            out.append(seg)
    return leading + "/".join(out)


# Location check: exempt the project directory FIRST, then block everything outside it.
# The gate's intent is "don't write outside the project" (INV-200), so the temp/Downloads
# lists below do NOT decide *whether* to block -- they only choose the more specific
# message. A project that merely lives under a path containing /tmp/ (e.g.
# /home/user/tmp/proj) must not trip the gate for its own in-project writes, which is
# why the exemption is checked first.
if abs_path:
    target = norm(abs_path)          # `..` resolved, so escapes can't slip the block
    here = norm(os.getcwd())
    # Case-fold both sides of the exemption with the SAME rule the temp/Downloads
    # checks use below (Windows/macOS filesystems are case-insensitive), so an
    # in-project path whose case differs from the cwd is exempted, not blocked.
    low = target.lower()
    here_low = here.lower()
    if low == here_low or low.startswith(here_low + "/"):
        pass  # inside the project -> allowed on location grounds (checked FIRST)
    else:
        if any(low.startswith(p) for p in TEMP_PREFIXES) or any(
            s in low for s in TEMP_SUBSTRINGS
        ):
            block(LOC_MSG)
        else:
            # Per-user / relocated temp dirs the prefix lists cannot enumerate: macOS puts
            # its under $TMPDIR (e.g. /var/folders/...), Windows under %TEMP%/%TMP%. Consult
            # all three so no platform is covered less well than the others (INV-001).
            # These now only refine the message -- the fall-through blocks them anyway.
            for var in ("TMPDIR", "TEMP", "TMP"):
                env_tmp = os.environ.get(var, "")
                if not env_tmp:
                    continue
                tmp_norm = norm(env_tmp.rstrip("/\\")).lower()
                if tmp_norm and low.startswith(tmp_norm + "/"):
                    block(LOC_MSG)
            # Anything else that resolved outside the project. Without this the gate was
            # a temp-and-Downloads blocker, not the boundary INV-200 states: a target
            # outside the project that named no list -- including one reached by a `..`
            # escape -- fell through here and was ALLOWED.
            block(OUTSIDE_MSG)

# Secrets: PEM private keys, AWS access-key IDs, and raw Senzing license payloads
# (base64 blobs with the documented AQAAAD prefix). The long base64 tail keeps the
# check off prose that merely mentions "AQAAAD" and off .lic file *paths*.
if re.search(
    r"BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY"
    r"|AKIA[0-9A-Z]{16}"
    r"|AQAAAD[A-Za-z0-9+/=]{16,}",
    data,
):
    block(SECRET_MSG)

sys.exit(0)
