#!/usr/bin/env python3
"""Preview or create a local release with an atomic branch-and-tag transaction."""

from __future__ import annotations

import argparse
import difflib
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PLUGIN_MANIFEST = "plugins/senzing-bootcamp/plugin.json"
SEMVER = re.compile(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)")
ORIGINS = {
    "git@github.com:docktermj/senzing-bootcamp-copilot-plugin-development.git",
    "https://github.com/docktermj/senzing-bootcamp-copilot-plugin-development.git",
    "https://github.com/docktermj/senzing-bootcamp-copilot-plugin-development",
}


def git(root: Path, *arguments: str, data: bytes | None = None, index: Path | None = None) -> bytes:
    environment = os.environ.copy()
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE",
                 "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES"):
        environment.pop(name, None)
    if index is not None:
        environment["GIT_INDEX_FILE"] = str(index)
    return subprocess.run(
        ["git", "--no-optional-locks", "-C", str(root), *arguments], input=data,
        capture_output=True, check=True, env=environment,
    ).stdout


def repository(root: Path, branch: str) -> None:
    if (not re.fullmatch(r"[A-Za-z0-9._/-]+", branch) or ".." in branch
            or branch.startswith(("/", "-")) or branch.endswith("/")):
        raise ValueError("Release branch must be a simple, explicit branch name")
    if not (root / ".git").is_dir() or (root / ".git").is_symlink():
        raise ValueError("Release requires a standalone checkout with its .git directory inside it")
    if Path(git(root, "rev-parse", "--show-toplevel").decode().strip()).resolve() != root.resolve():
        raise ValueError("Release must run at the repository root")
    common = Path(git(root, "rev-parse", "--git-common-dir").decode().strip())
    if (root / common).resolve() != root / ".git":
        raise ValueError("External Git metadata is not supported")
    if git(root, "remote", "get-url", "origin").decode().strip() not in ORIGINS:
        raise ValueError("Release origin must be the development repository")
    if branch in {"main", "master"} or git(root, "symbolic-ref", "--short", "HEAD").decode().strip() != branch:
        raise ValueError("Use the explicitly named, checked-out release review branch, never main")
    if any((root / ".git" / name).exists() for name in
           ("MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "rebase-merge", "rebase-apply", "index.lock")):
        raise ValueError("Finish the in-progress Git operation before releasing")


def inside(root: Path, name: str) -> Path:
    path = root / name
    if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()) or ".." in Path(name).parts:
        raise ValueError(f"Release path escapes the repository or is a symlink: {name}")
    return path


def validate_record(root: Path, version: str) -> None:
    record = inside(root, f"docs/test-records/{version}.md")
    if not record.is_file():
        raise ValueError(f"Missing test record: {record.relative_to(root)}")
    text = record.read_text()
    if not re.search(rf"(?m)^\*\*Release candidate:\*\* {re.escape(version)}[ \t]*$", text):
        raise ValueError("Test record must name the exact release candidate")
    if not re.search(r"(?m)^\*\*Status:\*\* PASS\b", text):
        raise ValueError("Test record status must be PASS")
    for field in ("Tested on", "Tester", "Copilot client/version", "Platform", "Plugin build"):
        match = re.search(rf"(?m)^\*\*{re.escape(field)}:\*\* (.+)$", text)
        value = match.group(1).strip() if match else ""
        if (not value or value in {"name", "version and channel", "operating system/version"}
                or re.search(r"Not recorded|NOT RUN|YYYY|X\.Y\.Z", value, re.I)):
            raise ValueError(f"Test record lacks observed {field}")
        if field == "Tested on":
            dt.date.fromisoformat(value)
        if field == "Plugin build" and not re.search(rf"(?<![\w.+-]){re.escape(version)}(?![\w.+-])", value):
            raise ValueError("Test record must identify the tested exact plugin version")
    if not re.search(r"(?m)^\*\*Hooks reviewed and trusted:\*\* PASS\b", text):
        raise ValueError("Hook trust must be recorded as PASS")
    checklist = (root / "docs/test-checklist.md").read_text()
    critical = set(re.findall(r"(?m)^\| (TC-\d+) \| Yes \|", checklist))
    if not critical:
        raise ValueError("No critical test cases found in the host checklist")
    rows: dict[str, list[str]] = {}
    for line in text.splitlines():
        cells = [cell.strip() for cell in line.split("|")[1:-1]]
        if cells and cells[0] in critical:
            if cells[0] in rows:
                raise ValueError(f"Duplicate test result: {cells[0]}")
            rows[cells[0]] = cells
    for identifier in sorted(critical):
        cells = rows.get(identifier, [])
        if (len(cells) != 4 or cells[1] != "PASS" or not cells[2] or not cells[3]
                or re.search(r"Not recorded|NOT RUN|YYYY|TODO", " ".join(cells[2:]), re.I)):
            raise ValueError(f"Critical test {identifier} needs PASS, observed evidence, and tester/date")
        date = re.search(r"\b\d{4}-\d{2}-\d{2}\b", cells[3])
        if not date:
            raise ValueError(f"Critical test {identifier} needs a tester and ISO date")
        dt.date.fromisoformat(date.group())
    confirmation = re.search(r"(?m)^\*\*Exact-version checks:\*\* PASS (.+)$", text)
    if not confirmation or not re.search(
        rf"(?<![\w.+-]){re.escape(version)}(?![\w.+-])", confirmation.group(1)
    ) or not critical <= set(re.findall(r"TC-\d+", confirmation.group(1))):
        raise ValueError("Exact-version checks must record PASS, version, and every critical test case")


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2) + "\n").encode()


def plan_release(root: Path, version: str, notes: str, branch: str) -> dict[str, bytes]:
    repository(root, branch)
    if (root / ".git/release-transaction").exists():
        raise ValueError("An interrupted release exists; use --recover before continuing")
    if git(root, "status", "--porcelain", "--untracked-files=all").strip():
        raise ValueError("Release requires a clean checkout; commit the genuine test record first")
    match = SEMVER.fullmatch(version)
    current = inside(root, "RELEASE_VERSION").read_text().strip()
    current_match = SEMVER.fullmatch(current)
    if not match or not current_match or tuple(map(int, match.groups())) <= tuple(map(int, current_match.groups())):
        raise ValueError("Release version must be an exact, increasing stable SemVer version")
    if not notes.strip():
        raise ValueError("Release notes are required")
    if git(root, "tag", "--list", version, f"v{version}").strip():
        raise ValueError("Release tag already exists; tags are never replaced")
    validate_record(root, version)
    manifest = json.loads(inside(root, PLUGIN_MANIFEST).read_bytes())
    build = json.loads(inside(root, ".build-manifest.json").read_bytes())
    if manifest.get("version") != current or build.get("release_version") != current:
        raise ValueError("Restore the release version and rebuild before releasing")
    if (build.get("parent_version") != inside(root, "PARENT_VERSION").read_text().strip()
            or build.get("parent_commit") != inside(root, "PARENT_COMMIT").read_text().strip()):
        raise ValueError("Build manifest disagrees with parent provenance")
    manifest["version"] = version
    manifest_data = json_bytes(manifest)
    digest = hashlib.sha256(manifest_data).hexdigest()
    build["release_version"] = version
    build["files"]["plugin.json"] = {"generated": digest, "output": digest}
    changelog = inside(root, "CHANGELOG.md").read_text()
    if re.search(rf"(?m)^## \[{re.escape(version)}\]", changelog):
        raise ValueError("Release already appears in the changelog")
    if not changelog.startswith("# Changelog\n"):
        raise ValueError("Expected a # Changelog heading")
    updates = {
        "RELEASE_VERSION": f"{version}\n".encode(), PLUGIN_MANIFEST: manifest_data,
        ".build-manifest.json": json_bytes(build),
        "CHANGELOG.md": ("# Changelog\n\n" + f"## [{version}]\n\n{notes.strip()}\n\n"
                         + changelog.removeprefix("# Changelog\n").lstrip()).encode(),
    }
    for name in updates:
        inside(root, name)
    return updates


def run_checks(root: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="release-checks-", dir=root / ".git") as temporary:
        environment = os.environ.copy()
        environment.update({"TMPDIR": temporary, "TEMP": temporary, "TMP": temporary,
                            "PYTHONDONTWRITEBYTECODE": "1"})
        environment.pop("PYTHONPYCACHEPREFIX", None)
        for arguments in (
            ("-m", "unittest", "discover", "-s", "tools/bootcamp-transform/tests", "-p", "test_*.py"),
            ("specs/check_invariants.py",),
            ("tools/bootcamp-transform/check_operations.py",),
            ("tools/bootcamp-transform/validate.py",),
        ):
            subprocess.run([sys.executable, *arguments], cwd=root, env=environment, check=True)


def materialize(root: Path, state: dict) -> None:
    index = root / ".git/index"
    lock = root / ".git/index.lock"
    locked_index = lock.open("xb")
    try:
        with locked_index:
            if index.read_bytes().hex() not in {state["old_index"], state["new_index"]}:
                raise ValueError("Index changed during release; retain the journal and resolve manually")
            for name, values in state["files"].items():
                path = inside(root, name)
                if path.read_bytes().hex() not in {values["old"], values["new"]}:
                    raise ValueError(f"{name} changed during release; retain the journal and resolve manually")
            for name, values in state["files"].items():
                path = inside(root, name)
                temporary = root / ".git/release-transaction/file"
                temporary.write_bytes(bytes.fromhex(values["new"]))
                temporary.chmod(path.stat().st_mode & 0o777)
                os.replace(temporary, path)
            locked_index.write(bytes.fromhex(state["new_index"]))
            locked_index.flush()
            os.fsync(locked_index.fileno())
        os.replace(lock, index)
    finally:
        if lock.exists():
            lock.unlink()


def recover(root: Path, branch: str) -> None:
    repository(root, branch)
    transaction = root / ".git/release-transaction"
    state = json.loads((transaction / "state.json").read_text())
    if state["branch"] != branch:
        raise ValueError("Recovery branch differs from the recorded release branch")
    head = git(root, "rev-parse", "HEAD").decode().strip()
    tag = git(root, "tag", "--list", state["version"]).decode().strip()
    if head == state["new_commit"] and tag:
        if git(root, "rev-parse", f"refs/tags/{tag}^{{commit}}").decode().strip() != head:
            raise ValueError("Release tag moved; manual recovery required")
        materialize(root, state)
    elif head != state["old_commit"] or tag:
        raise ValueError("Branch or tag changed; manual recovery required")
    shutil.rmtree(transaction)


def apply_release(root: Path, version: str, notes: str, branch: str) -> str:
    old_commit = git(root, "rev-parse", "HEAD").decode().strip()
    updates = plan_release(root, version, notes, branch)
    run_checks(root)
    if (git(root, "rev-parse", "HEAD").decode().strip() != old_commit
            or updates != plan_release(root, version, notes, branch)):
        raise ValueError("Release inputs changed during validation")
    transaction = root / ".git/release-transaction"
    transaction.mkdir()
    try:
        alternate_index = transaction / "index"
        git(root, "read-tree", "HEAD", index=alternate_index)
        for name, data in updates.items():
            blob = git(root, "hash-object", "-w", "--stdin", data=data).decode().strip()
            mode = git(root, "ls-files", "-s", "--", name).decode().split()[0]
            git(root, "update-index", "--add", "--cacheinfo", mode, blob, name, index=alternate_index)
        tree = git(root, "write-tree", index=alternate_index).decode().strip()
        commit = git(root, "commit-tree", tree, "-p", old_commit, "-m", f"Release {version}\n\n{notes}").decode().strip()
        state = {
            "branch": branch, "version": version, "old_commit": old_commit, "new_commit": commit,
            "old_index": (root / ".git/index").read_bytes().hex(),
            "new_index": alternate_index.read_bytes().hex(),
            "files": {name: {"old": inside(root, name).read_bytes().hex(), "new": data.hex()}
                      for name, data in updates.items()},
        }
        with (transaction / "state.json").open("w") as journal:
            json.dump(state, journal)
            journal.flush()
            os.fsync(journal.fileno())
        if git(root, "status", "--porcelain", "--untracked-files=all").strip():
            raise ValueError("Checkout changed during release preparation")
        tagger = git(root, "var", "GIT_COMMITTER_IDENT").decode().strip()
        tag_data = (
            f"object {commit}\ntype commit\ntag {version}\ntagger {tagger}\n\n"
            f"Release {version}\n"
        ).encode()
        tag_object = git(root, "mktag", data=tag_data).decode().strip()
        git(root, "update-ref", "--stdin", data=(
            f"start\nupdate refs/heads/{branch} {commit} {old_commit}\n"
            f"create refs/tags/{version} {tag_object}\nprepare\ncommit\n"
        ).encode())
        recover(root, branch)
        return commit
    except BaseException:
        if not (transaction / "state.json").exists():
            shutil.rmtree(transaction)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--version")
    parser.add_argument("--notes")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--recover", action="store_true")
    args = parser.parse_args()
    try:
        if args.recover:
            recover(ROOT, args.branch)
            print("Local release recovery completed")
        else:
            if not args.version or not args.notes:
                parser.error("--version and --notes are required for preview or apply")
            updates = plan_release(ROOT, args.version, args.notes, args.branch)
            for name, data in updates.items():
                print("".join(difflib.unified_diff(
                    (ROOT / name).read_text().splitlines(True), data.decode().splitlines(True),
                    fromfile=name, tofile=name,
                )), end="")
            if args.apply:
                commit = apply_release(ROOT, args.version, args.notes, args.branch)
                print(f"Created local release {args.version} at {commit}; nothing pushed")
            else:
                print("Preview only; no release files, commits, or tags changed")
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        recovery = ""
        if (ROOT / ".git/release-transaction").exists():
            recovery = f"; retain the journal and run --branch {args.branch} --recover"
        detail = error.stderr.decode(errors="replace") if isinstance(error, subprocess.CalledProcessError) else str(error)
        raise SystemExit(f"Release blocked: {detail}{recovery}") from error


if __name__ == "__main__":
    main()
