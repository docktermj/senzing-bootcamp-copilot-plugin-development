#!/usr/bin/env python3
"""Package a bootcamp project into one self-describing, transferable zip archive.

A bootcamper who finishes the bootcamp had no way to archive the work or hand it to anyone else.
Graduation frames the recap PDF as "a keepsake to revisit and share with their team", and INV-094's
revisit bundle was built for the resume story -- but it is written **in place**, so it only helps on
the machine that produced it. Switching machines meant re-doing SDK setup, the database, the mapping
and the load by hand; showing the work to a colleague meant attaching four or five files with no
index; archiving before a reimage had no supported path at all.

The artifacts were never the gap. Nothing gathered them, nothing said what to open first, and
nothing decided what must **not** travel.

Two profiles, because the two audiences need different contents:

- ``share``    -- for someone looking at the results. Keepsakes, visualizations, ``production/``.
                  Never a database, never source data, never a credential.
- ``transfer`` -- for the bootcamper resuming elsewhere. Everything in ``share`` plus the INV-094
                  revisit bundle (state snapshot **and** database backup), ``config/``,
                  ``docs/mapping/`` and ``src/``.

⛔ **This script writes an archive and stops.** It never uploads, emails, attaches or opens an issue
with it (INV-135) -- moving the file off the machine is the Bootcamper's action. The output lands
**inside** the project (INV-200), under ``backups/packages/``.

⛔ **Nothing is reported as existing until it has been re-opened.** ``testzip()`` runs on the
finished archive and a ``.sha256`` sidecar is written before the success line prints (INV-067's
discipline): an archive that cannot be read is worse than no archive, because the Bootcamper will
discover it on the machine that no longer has the original.

Format is **zip**, not tar: it opens natively on Windows, macOS and Linux with no extra tool
(INV-066). Stdlib only (INV-108-adjacent: no third-party dependency in a bundled script).

Usage::

    python3 "${PLUGIN_ROOT}/scripts/package_bootcamp.py" --profile share --dry-run
    python3 "${PLUGIN_ROOT}/scripts/package_bootcamp.py" --profile transfer

``--dry-run`` prints the manifest and the total uncompressed size and writes **nothing**. The
conversation layer (`skills/bootcamp-onboarding/packaging.md`) runs it first so the consent question
can quote a real size rather than an estimate.
"""
import argparse
import hashlib
import json
import os
import sys
import textwrap
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from secret_patterns import find_secret
except ImportError:  # pragma: no cover - the helper ships beside this file
    def find_secret(_text):
        """Fail CLOSED, not open: with no scanner, nothing text-like is packaged.

        An ImportError here must not silently downgrade to "package everything unscanned".
        """
        return "secret scanner unavailable"

#: One top-level directory inside every archive, so extraction never scatters files into the
#: recipient's working directory.
ROOT_PREFIX = "senzing-bootcamp-{profile}-{date}"

#: Paths never included in ANY profile. Named in the manifest rather than dropped quietly, so a
#: recipient can tell what is missing without guessing.
ALWAYS_EXCLUDE = (
    ".env",
    ".env.production",
    "licenses",
    "config/license.json",
    "data/raw",
    "data/temp",
    "logs",
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    "target",
    "backups/packages",
)

#: `share` additionally drops every backup, every database file, and the mapping layer.
#: ⛔ `docs/mapping/` is transfer-only by design: it describes the Bootcamper's own source schema
#: (field names, sample values), which the results audience does not need and which belongs with
#: the data rather than with the findings.
SHARE_EXCLUDE = ("backups", "docs/mapping")
DATABASE_SUFFIXES = (".db", ".sqlite", ".sqlite3")

#: What each profile reaches for. A missing entry is recorded as absent, never an error: the flow
#: runs at any point in the bootcamp, so most of this legitimately does not exist yet.
SHARE_INCLUDE = (
    "docs",
    "production",
)
TRANSFER_EXTRA = (
    "backups/revisit",
    "config",
    "src",
)

#: Above this, moving the file is awkward enough to be worth saying so.
SIZE_WARN_BYTES = 2 * 1024 * 1024 * 1024

#: How much of a member is read at a time when scanning it for secrets, and how much of the
#: previous block is carried forward so a pattern straddling a block boundary is still found.
#: The longest pattern is the license blob's ~22-byte prefix plus its base64 tail, so 4 KiB of
#: overlap is orders of magnitude more than required.
SCAN_BLOCK_BYTES = 1 << 20
SCAN_OVERLAP_BYTES = 4096

# ⛔ There is deliberately NO extension allowlist here. There was one until 2026-08-26 --
# `TEXT_SUFFIXES`, carrying .md/.py/.json/.csv and NOT .pem, .key, .crt or the empty extension --
# and `_scan()` returned None for anything unlisted, which the call site could not distinguish
# from "nothing found". Measured on a fixture: `src/keys/server.pem` and an extensionless
# `src/keys/id_rsa`, both carrying real PEM armor lines, were PACKAGED, while the identical key
# embedded in `src/loader.py` was correctly excluded. The scan skipped exactly the file types
# whose purpose is to hold a credential, in an archive whose reason to exist is being handed to
# someone else -- and `OPEN_ME_FIRST.md` told the recipient that anything matching a secret
# pattern had been excluded, which was then false.
#
# An allowlist answering "is this worth reading as text?" cannot answer "can this contain a
# secret?". Lengthening it would be the same defect with a later trigger, so it is gone: every
# member is read and scanned, and a member that cannot be read is EXCLUDED rather than included
# unexamined. `write-gate.py` has never had such a filter -- it scans every payload -- which is
# why asserting the two pattern *strings* equal said nothing about their application.
# See `specs/the-packager-secret-scan-skips-the-files-most-likely-to-be-secrets.md`.


def _rel(path, root):
    return path.relative_to(root).as_posix()


def is_excluded(relpath, profile):
    """Whether `relpath` (project-relative, posix) is excluded, and by which rule.

    Matches on path *segments* rather than substrings: a directory named ``logs`` is excluded and a
    file named ``changelogs.md`` is not.
    """
    parts = relpath.split("/")
    for rule in ALWAYS_EXCLUDE:
        rule_parts = rule.split("/")
        if parts[: len(rule_parts)] == rule_parts:
            return rule
        if len(rule_parts) == 1 and rule in parts:
            return rule
    if profile == "share":
        for rule in SHARE_EXCLUDE:
            rule_parts = rule.split("/")
            if parts[: len(rule_parts)] == rule_parts:
                return rule
        if Path(relpath).suffix.lower() in DATABASE_SUFFIXES:
            return "*%s (share profile carries no database)" % Path(relpath).suffix.lower()
    return None


def candidate_roots(profile):
    return list(SHARE_INCLUDE) + (list(TRANSFER_EXTRA) if profile == "transfer" else [])


def collect(project_root, profile):
    """(members, skipped) for the profile.

    ``members`` is a list of (absolute path, project-relative posix path).
    ``skipped`` is a list of dicts recording every path left out and why -- the manifest's whole
    value is that a recipient can tell what is absent.
    """
    project_root = project_root.resolve()
    members, skipped, seen = [], [], set()

    for top in candidate_roots(profile):
        base = project_root / top
        if not base.exists():
            skipped.append({"path": top, "reason": "not present in this project"})
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            here = Path(dirpath)
            # Prune excluded directories before descending, so a large excluded tree costs nothing.
            keep = []
            for name in sorted(dirnames):
                rel = _rel(here / name, project_root)
                rule = is_excluded(rel, profile)
                if rule:
                    skipped.append({"path": rel + "/", "reason": "excluded by rule: %s" % rule})
                else:
                    keep.append(name)
            dirnames[:] = keep

            for name in sorted(filenames):
                absolute = here / name
                rel = _rel(absolute, project_root)
                if rel in seen:
                    continue
                rule = is_excluded(rel, profile)
                if rule:
                    skipped.append({"path": rel, "reason": "excluded by rule: %s" % rule})
                    continue
                # Resolve, THEN compare -- the INV-200 rule, here because a symlink into ~/.ssh
                # would otherwise be packaged verbatim under an innocuous project-relative name.
                try:
                    resolved = absolute.resolve()
                except OSError as exc:
                    skipped.append({"path": rel, "reason": "unreadable (%s)" % exc})
                    continue
                if not str(resolved).startswith(str(project_root) + os.sep):
                    skipped.append({
                        "path": rel,
                        "reason": "resolves outside the project root; not packaged",
                    })
                    continue
                secret = _scan(resolved)
                if secret == UNEXAMINED:
                    # Fail CLOSED. An unreadable member is not a clean member, and including it
                    # unexamined is how the manifest's exclusion promise becomes false.
                    skipped.append({
                        "path": rel,
                        "reason": "excluded: could not be read, so it was NOT scanned for "
                                  "secrets; nothing unexamined is packaged",
                    })
                    continue
                if secret:
                    skipped.append({
                        "path": rel,
                        "reason": "excluded: content matched a secret pattern (%s)" % secret,
                    })
                    continue
                seen.add(rel)
                members.append((resolved, rel))
    return members, skipped


#: Sentinel for the third outcome. `None` means "read it all and found nothing"; this means
#: "could not read it", which MUST NOT be treated as clean.
UNEXAMINED = "unexamined"


def _scan(path):
    """Three outcomes, and the third is the one an extension allowlist erased.

    Returns the name of the first secret class the file's bytes match, ``None`` when the file
    was read in full and matched nothing, or ``UNEXAMINED`` when it could not be read.

    ⛔ ``None`` and ``UNEXAMINED`` must stay distinct at the call site. Collapsing them is
    exactly how a `.pem` private key came to be packaged: "not scanned" was reported as
    "nothing found", and the caller had no way to tell.

    Every member is scanned regardless of extension. Bytes are decoded with ``errors="replace"``
    rather than sniffed for binary-ness, so a key concatenated into an image is still found --
    a credential does not stop being one because of the file it was pasted into. Binary members
    simply do not match, which is the correct outcome rather than a skipped one.
    """
    try:
        with open(path, "rb") as handle:
            carry = ""
            while True:
                block = handle.read(SCAN_BLOCK_BYTES)
                if not block:
                    return None
                text = carry + block.decode("utf-8", errors="replace")
                found = find_secret(text)
                if found:
                    return found
                # Carry the tail forward so a pattern straddling the boundary is still seen.
                carry = text[-SCAN_OVERLAP_BYTES:]
    except OSError:
        return UNEXAMINED


def sha256_of(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(131072), b""):
            digest.update(block)
    return digest.hexdigest()


def read_progress(project_root):
    try:
        with open(project_root / "config" / "bootcamp_progress.json", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def plugin_version():
    """The plugin's own version, per INV-252's skill-relative resolution."""
    here = Path(__file__).resolve().parent
    for candidate in (here.parent / "plugin.json",):
        try:
            with open(candidate, encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, ValueError):
            continue
        version = data.get("version")
        if isinstance(version, str):
            return version
    return "unknown"


def business_problem_line(project_root):
    """One line naming what the bootcamp was about, for OPEN_ME_FIRST.md."""
    path = project_root / "docs" / "business_problem.md"
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return ""
    for index, line in enumerate(lines):
        if line.strip().startswith("## Problem Description"):
            for follow in lines[index + 1:]:
                text = follow.strip()
                if text and not text.startswith(("#", ">", "[")):
                    return text
            break
    return ""


def build_manifest(profile, members, skipped, project_root, date):
    progress = read_progress(project_root)
    files = []
    total = 0
    for absolute, rel in members:
        try:
            size = absolute.stat().st_size
        except OSError:
            size = 0
        total += size
        files.append({"path": rel, "size_bytes": size, "sha256": sha256_of(absolute)})
    return {
        "schema": 1,
        "profile": profile,
        "created": date,
        "plugin_version": plugin_version(),
        "modules_completed": progress.get("modules_completed", []),
        "root_directory": ROOT_PREFIX.format(profile=profile, date=date),
        "included_count": len(files),
        "total_uncompressed_bytes": total,
        "included": files,
        # ⛔ The exclusions are part of the manifest, not a footnote. A recipient must be able to
        # tell what is MISSING without guessing -- that is the difference between an archive and a
        # pile of files.
        "exclusion_rules_applied": {
            "always": list(ALWAYS_EXCLUDE),
            "share_only": list(SHARE_EXCLUDE) + ["*%s" % s for s in DATABASE_SUFFIXES]
            if profile == "share" else [],
        },
        "excluded": skipped,
    }


#: The width the prose of OPEN_ME_FIRST.md is wrapped to. 85 reproduces the line breaks of the
#: wording a complete package has always carried, so that wording is kept byte for byte.
WRAP_WIDTH = 85

#: Restore step for a database backup, by file type -- from `graduation/database-backup.md`'s
#: "Restore" section. A backup of any other type is named by path with no restore step.
SQLITE_RESTORE = "a SQLite file; copy it back to `database/` to restore it"
PG_DUMP_SUFFIX = ".dump"
#: The file is named by an argument, never a `<` redirection, which Windows PowerShell 5.1 rejects.
PG_RESTORE = ("a `pg_dump` file; restore it into a fresh database with "
              "`pg_restore -U <user> -d <db> <file>` (or `psql -U <user> -d <db> -f <file>` for a "
              "plain dump), never with a `<` redirection")


def _para(text):
    return textwrap.wrap(text, WRAP_WIDTH, break_long_words=False, break_on_hyphens=False)


def _series(items, last="and"):
    """``a``, ``a and b``, ``a, b and c`` -- the shape the original wording uses."""
    items = list(items)
    if len(items) < 2:
        return "".join(items)
    return "%s %s %s" % (", ".join(items[:-1]), last, items[-1])


def included_parts(manifest):
    """Which named parts the archive carries, from the manifest's ``included`` list ONLY.

    ⛔ Included means "listed in ``included``", never "exists on disk": a part that exists but
    was excluded (unreadable, or it matched a secret pattern) is not in the archive, and
    OPEN_ME_FIRST.md must not say it is (#321). Paths are the manifest's posix paths, so the
    result is the same on Windows.
    """
    paths = [entry["path"] for entry in manifest.get("included", [])]

    def under(prefix):
        return [p for p in paths if p.startswith(prefix)]

    keepsakes = [p for p in paths if p.startswith("docs/") and p.count("/") == 1
                 and p.lower().endswith(".pdf")]
    return {
        "recap": "docs/bootcamp_recap.pdf" in paths,
        "database": sorted(under("backups/revisit/database/")),
        "state": "backups/revisit/RESUME_STATE.json" in paths
                 or bool(under("backups/revisit/state/")),
        "guide": "docs/REVISIT_BOOTCAMP.md" in paths,
        "config": bool(under("config/")),
        "mappings": bool(under("docs/mapping/")),
        "src": bool(under("src/")),
        "keepsakes": bool(keepsakes),
        "visualizations": bool(under("docs/visualizations/")),
        "production": bool(under("production/")),
    }


def _restore_step(path):
    suffix = Path(path).suffix.lower()
    if suffix in DATABASE_SUFFIXES:
        return SQLITE_RESTORE
    if suffix == PG_DUMP_SUFFIX:
        return PG_RESTORE
    return None


def _share_block(parts):
    named = (
        ("keepsakes", "the keepsake documents", "the keepsake documents"),
        ("visualizations", "the visualizations", "the visualizations"),
        ("production", "the generated `production/` project", "the generated production project"),
    )
    carried = [label for key, label, _ in named if parts[key]]
    missing = [label for key, _, label in named if not parts[key]]
    head = "Profile **`share`** — the results, for reading."
    if not missing:
        text = "%s It carries %s." % (head, _series(carried))
    elif carried:
        text = ("%s It carries %s. It does not carry %s; `PACKAGE_MANIFEST.json`'s `included` "
                "list names every file it does carry." % (head, _series(carried),
                                                          _series(missing, "or")))
    else:
        text = ("%s It carries none of %s yet; `PACKAGE_MANIFEST.json`'s `included` list names "
                "every file it does carry." % (head, _series(missing, "or")))
    return _para(text) + [""] + _para(
        "It deliberately carries **no database, no source data and no credentials**, so it is "
        "safe to hand to someone who should see the results but not the inputs.")


def _transfer_block(parts):
    database, state, guide = parts["database"], parts["state"], parts["guide"]
    results = parts["keepsakes"] or parts["visualizations"] or parts["production"]
    resume = _para(
        "**To resume:** open **`docs/REVISIT_BOOTCAMP.md`** — it carries the restore and "
        "re-initialization commands for this project's database and state.")
    if (results and database and state and guide
            and parts["config"] and parts["mappings"] and parts["src"]):
        return _para(
            "Profile **`transfer`** — everything needed to continue the bootcamp on another "
            "machine: the results, plus the revisit bundle (state snapshot and database backup), "
            "`config/`, the mappings and `src/`.") + [""] + resume

    named = [("the results", "the results", results)]
    if database and state:
        named.append(("the revisit bundle (state snapshot and database backup)", None, True))
    else:
        named.append(("a database backup", None, bool(database)))
        named.append(("a state snapshot", "a state snapshot", state))
    named += [
        ("`config/`", "the project config", parts["config"]),
        ("the mappings", "the mappings", parts["mappings"]),
        ("`src/`", "the source code", parts["src"]),
    ]
    carried = [label for label, _, present in named if present]
    missing = [label for _, label, present in named if not present and label]
    text = "Profile **`transfer`** — for continuing the bootcamp on another machine. "
    text += ("This package is partial: it carries %s." % _series(carried) if carried
             else "This package is partial.")
    if missing:
        text += " It does not carry %s." % _series(missing, "or")
    lines = _para(text) + [""]

    if guide:
        lines += resume
        if not database:
            lines += [""] + _para(
                "This package carries **no database backup**, so there is no database to restore "
                "from it: set up the database and redo the load on the new machine instead.")
        return lines
    if database:
        for path in database:
            step = _restore_step(path)
            lines += _para("**Database backup:** `%s`%s." % (path, " is " + step if step else ""))
            lines += [""]
        return lines + _para(
            "No full restore guide is included: it is written at graduation. Set up the SDK on "
            "the new machine first, then restore the %s above."
            % ("backup" if len(database) == 1 else "backups"))
    return lines + _para(
        "This package carries **no database backup and no restore guide**, so on the new "
        "machine you must redo SDK setup, the database and the load.")


def open_me_first(manifest, project_root):
    """OPEN_ME_FIRST.md. Every statement about what the archive contains is built from the
    manifest's ``included`` list, so it can never contradict PACKAGE_MANIFEST.json (#321)."""
    profile = manifest["profile"]
    parts = included_parts(manifest)
    problem = business_problem_line(project_root)
    lines = [
        "# Open me first",
        "",
        "This is a packaged Senzing Bootcamp project.",
        "",
    ]
    if problem:
        lines += ["**The business problem it addresses:** %s" % problem, ""]
    lines += ["## Start here", ""]
    if parts["recap"]:
        lines += _para(
            "Open **`docs/bootcamp_recap.pdf`** first — it is the guided tour of what was built, "
            "in order, with the visualizations embedded.")
    else:
        lines += _para(
            "The recap PDF is written at graduation and is not in this package. Start with "
            "`PACKAGE_MANIFEST.json` instead: its `included` list names every file this "
            "package carries.")
    lines += ["", "## What this package is", ""]
    lines += _share_block(parts) if profile == "share" else _transfer_block(parts)
    lines += [
        "",
        "## What is NOT here, and why",
        "",
        "`PACKAGE_MANIFEST.json` lists every excluded path with its reason. The categories:",
        "",
        "- **Credentials and licenses** (`.env`, `licenses/`, `config/license.json`) — never",
        "  packaged, in either profile.",
        "- **Your own source data** (`data/raw/`) — never packaged. It is yours, it may be",
        "  sensitive, and the resolved results do not require it.",
        "- **Anything matching a secret pattern** — a PEM private key, an AWS access-key ID or a",
        "  Senzing license payload found in a file's contents excludes that file, and the",
        "  manifest names it.",
        "- **`.git/`** — excluded on purpose. This archive is a **snapshot, not a clone**: git",
        "  history can carry secrets that no longer exist in the working tree. If you want the",
        "  history, push the repository instead of relying on this package.",
        "- **Caches and virtualenvs** (`__pycache__/`, `.venv/`, `node_modules/`, `target/`) —",
        "  regenerated, not preserved.",
        "",
        "## Integrity",
        "",
        "The archive was re-opened and verified after writing, and a `.sha256` sidecar sits beside",
        "it. `PACKAGE_MANIFEST.json` records a SHA-256 for every included file, so you can check",
        "any single file rather than trusting the whole archive at once.",
        "",
        "---",
        "",
        "Packaged by the Senzing Bootcamp plugin %s on %s."
        % (manifest["plugin_version"], manifest["created"]),
        "",
    ]
    return "\n".join(lines)


def human(size):
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return "%.1f %s" % (size, unit) if unit != "B" else "%d B" % size
        size /= 1024.0
    return "%.1f GB" % size


def run(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--profile", choices=("share", "transfer"), required=True)
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--date", default=None,
                        help="YYYYMMDD stamp for the archive name (default: today, UTC).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the manifest and total size; write nothing.")
    parser.add_argument("--output", default=None,
                        help="Override the archive path (default: "
                             "backups/packages/senzing-bootcamp-<profile>-<date>.zip).")
    args = parser.parse_args(argv)

    project_root = Path(args.project_root).resolve()
    if not project_root.is_dir():
        sys.stderr.write("project root not found: %s\n" % project_root)
        return 1
    if args.date:
        date = args.date
    else:
        import datetime
        date = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d")

    members, skipped = collect(project_root, args.profile)
    manifest = build_manifest(args.profile, members, skipped, project_root, date)
    total = manifest["total_uncompressed_bytes"]

    if not members:
        sys.stderr.write(
            "nothing to package: no included path exists yet for profile '%s'. "
            "Run this after at least one module has produced artifacts.\n" % args.profile
        )
        return 1

    if args.dry_run:
        print(json.dumps(manifest, indent=2, sort_keys=True))
        print("", file=sys.stderr)
        print("profile: %s" % args.profile, file=sys.stderr)
        print("files:   %d" % manifest["included_count"], file=sys.stderr)
        print("size:    %s uncompressed (%d bytes)" % (human(total), total), file=sys.stderr)
        print("excluded: %d path(s) — see `excluded` in the manifest above" % len(skipped),
              file=sys.stderr)
        if total > SIZE_WARN_BYTES:
            print(
                "WARNING: %s is large enough to be awkward to move. Consider the 'share' "
                "profile, or drop the database backup, rather than producing this." % human(total),
                file=sys.stderr,
            )
        print("DRY RUN: nothing was written.", file=sys.stderr)
        return 0

    root = manifest["root_directory"]
    out = Path(args.output) if args.output else (
        project_root / "backups" / "packages" / ("%s.zip" % root))
    out.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=True) as archive:
        archive.writestr("%s/PACKAGE_MANIFEST.json" % root,
                         json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        archive.writestr("%s/OPEN_ME_FIRST.md" % root, open_me_first(manifest, project_root))
        for absolute, rel in members:
            archive.write(absolute, "%s/%s" % (root, rel))

    # ⛔ Re-open before reporting. An archive nobody read is a claim, not an artifact -- and this
    # one is most likely to be opened on a machine that no longer has the original.
    with zipfile.ZipFile(out) as check:
        bad = check.testzip()
        if bad is not None:
            sys.stderr.write("archive verification FAILED on member %s; removing %s\n"
                             % (bad, out))
            try:
                out.unlink()
            except OSError:
                pass
            return 1
        names = check.namelist()

    tops = {name.split("/")[0] for name in names}
    if tops != {root}:
        sys.stderr.write("archive does not extract into one directory (%s); removing %s\n"
                         % (sorted(tops), out))
        out.unlink()
        return 1

    digest = sha256_of(out)
    sidecar = out.with_suffix(out.suffix + ".sha256")
    sidecar.write_text("%s  %s\n" % (digest, out.name), encoding="utf-8")

    size = out.stat().st_size
    print("Package written: %s" % out)
    print("  size:    %s (%d bytes)" % (human(size), size))
    print("  sha256:  %s" % digest)
    print("  sidecar: %s" % sidecar)
    print("  files:   %d included, %d excluded (see PACKAGE_MANIFEST.json)"
          % (manifest["included_count"], len(skipped)))
    print("  verified: re-opened after writing; extracts into %s/" % root)
    print("")
    print("Move this file wherever you need it — the plugin does not transmit it anywhere.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
