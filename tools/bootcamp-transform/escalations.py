#!/usr/bin/env python3
"""Verify R7 parity evidence and optionally close a local awaiting-parity issue."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PARENT_DEV = "docktermj/senzing-bootcamp-claude-plugin-development"
PARENT_PUBLIC = "Senzing/senzing-bootcamp-claude-plugin"
LOCAL_REPO = "docktermj/senzing-bootcamp-copilot-plugin-development"
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
SHA = re.compile(r"^[0-9a-f]{40}$")
MANIFEST_PATH = b".claude-plugin/plugin.json"
EXPECTED_MANIFEST_URLS = {
    PARENT_DEV: f"https://github.com/{PARENT_DEV}",
    PARENT_PUBLIC: f"https://github.com/{PARENT_PUBLIC}",
}


class EvidenceError(RuntimeError):
    """The parity evidence is incomplete or contradictory."""


def command(*args: str, cwd: Path | None = None) -> str:
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)
    if result.returncode:
        raise EvidenceError(result.stderr.strip() or f"command failed: {' '.join(args)}")
    return result.stdout.strip()


def git_bytes(checkout: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(checkout), *args],
        capture_output=True,
        check=False,
    )
    if result.returncode:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise EvidenceError(message or f"command failed: git -C {checkout} {' '.join(args)}")
    return result.stdout


def _unique_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> object:
    raise ValueError(f"invalid JSON constant {value}")


def parse_manifest(raw: bytes, location: str) -> dict[str, object]:
    try:
        manifest = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_json_object,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeDecodeError, RecursionError, ValueError) as error:
        raise EvidenceError(f"Invalid manifest at {location}: {error}") from error
    if not isinstance(manifest, dict):
        raise EvidenceError(f"Invalid manifest at {location}: expected a JSON object")
    return manifest


def issue(repo: str, number: int) -> dict:
    try:
        value = json.loads(command(
            "gh", "issue", "view", str(number), "--repo", repo,
            "--json", "body,state,stateReason,url,labels",
        ))
    except json.JSONDecodeError as error:
        raise EvidenceError(f"GitHub returned invalid issue JSON for {repo}#{number}") from error
    if not isinstance(value, dict):
        raise EvidenceError(f"GitHub issue response is not an object for {repo}#{number}")
    return value


def tag_commit(checkout: Path, tag: str) -> str:
    return command("git", "-C", str(checkout), "rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}")


def ancestor(checkout: Path, commit: str, tag: str) -> bool:
    shallow = command("git", "-C", str(checkout), "rev-parse", "--is-shallow-repository")
    if shallow == "true":
        raise EvidenceError(f"{checkout} is shallow; fetch complete history before checking parity")
    result = subprocess.run(
        ["git", "-C", str(checkout), "merge-base", "--is-ancestor", commit, tag],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode == 1:
        return False
    if result.returncode:
        raise EvidenceError(result.stderr.strip() or "could not verify parent commit ancestry")
    return True


def tree(checkout: Path, tag: str) -> str:
    return command(
        "git", "-C", str(checkout), "rev-parse", "--verify",
        f"{tag}:plugins/senzing-bootcamp",
    )


def _tree_inventory(checkout: Path, tree_id: str) -> dict[bytes, tuple[bytes, bytes, bytes]]:
    entries: dict[bytes, tuple[bytes, bytes, bytes]] = {}
    records = git_bytes(
        checkout, "ls-tree", "-r", "-z", "--full-tree", tree_id,
    ).split(b"\0")
    for record in records:
        if not record:
            continue
        try:
            metadata, path = record.split(b"\t", 1)
            mode, object_type, object_id = metadata.split(b" ", 2)
        except ValueError as error:
            raise EvidenceError(f"Could not read the tagged plugin inventory in {checkout}") from error
        if object_type != b"blob":
            raise EvidenceError(
                f"Unsupported {object_type.decode('ascii', errors='replace')} entry in "
                f"{checkout}: {os.fsdecode(path)}"
            )
        entries[path] = (
            mode,
            object_type,
            git_bytes(checkout, "cat-file", "blob", object_id.decode("ascii")),
        )
    return entries


def _first_json_difference(left: object, right: object, path: str = "$") -> str | None:
    if type(left) is not type(right):
        return path
    if isinstance(left, dict):
        if not isinstance(right, dict):
            return path
        right_dict = right
        for key in sorted(left.keys() | right_dict.keys()):
            if key not in left or key not in right_dict:
                return f"{path}.{key}"
            difference = _first_json_difference(left[key], right_dict[key], f"{path}.{key}")
            if difference:
                return difference
        return None
    if isinstance(left, list):
        if not isinstance(right, list):
            return path
        right_list = right
        if len(left) != len(right_list):
            return path
        for index, (left_item, right_item) in enumerate(zip(left, right_list)):
            difference = _first_json_difference(left_item, right_item, f"{path}[{index}]")
            if difference:
                return difference
        return None
    return None if left == right else path


def plugin_tree_difference(
    development_checkout: Path,
    development_tree: str,
    public_checkout: Path,
    public_tree: str,
) -> str | None:
    if development_tree == public_tree:
        return None

    development = _tree_inventory(development_checkout, development_tree)
    public = _tree_inventory(public_checkout, public_tree)
    for path in sorted(development.keys() - public.keys()):
        return f"File is missing from the public tree: {os.fsdecode(path)}"
    for path in sorted(public.keys() - development.keys()):
        return f"File is missing from the development tree: {os.fsdecode(path)}"

    for path in sorted(development):
        development_mode, development_type, development_content = development[path]
        public_mode, public_type, public_content = public[path]
        display_path = os.fsdecode(path)
        if development_mode != public_mode or development_type != public_type:
            return f"File mode or type differs: {display_path}"
        if path != MANIFEST_PATH:
            if development_content != public_content:
                return f"File contents differ: {display_path}"
            continue

        development_manifest = parse_manifest(development_content, f"development {display_path}")
        public_manifest = parse_manifest(public_content, f"public {display_path}")
        for manifest, repository, label in (
            (development_manifest, PARENT_DEV, "development"),
            (public_manifest, PARENT_PUBLIC, "public"),
        ):
            expected_url = EXPECTED_MANIFEST_URLS[repository]
            for field in ("homepage", "repository"):
                if manifest.get(field) != expected_url:
                    raise EvidenceError(
                        f"Unexpected {label} manifest {field} at {display_path}: "
                        f"expected {expected_url!r}, got {manifest.get(field)!r}"
                    )

        for manifest in (development_manifest, public_manifest):
            manifest.pop("homepage")
            manifest.pop("repository")
        field_difference = _first_json_difference(development_manifest, public_manifest)
        if field_difference:
            return f"Manifest content differs at {display_path}:{field_difference}"
    return None


def plugin_version(checkout: Path, tag: str) -> str:
    raw = git_bytes(
        checkout, "show",
        f"{tag}:plugins/senzing-bootcamp/.claude-plugin/plugin.json",
    )
    location = f"{checkout} {tag}:plugins/senzing-bootcamp/{os.fsdecode(MANIFEST_PATH)}"
    manifest = parse_manifest(raw, location)
    version = manifest.get("version")
    if not isinstance(version, str):
        raise EvidenceError(f"Could not read the parent plugin version at tag {tag}")
    return version


def has_issue_reference(body: str, repository: str, number: int) -> bool:
    repository_path = re.escape(repository)
    canonical = re.compile(
        rf"(?<![\w./-]){repository_path}#{number}(?![\w/])",
        re.IGNORECASE,
    )
    url = re.compile(
        rf"(?<![\w.-])https://github\.com/{repository_path}/issues/{number}(?![\w/])",
        re.IGNORECASE,
    )
    return canonical.search(body) is not None or url.search(body) is not None


def evaluate(
    local: dict,
    parent: dict,
    *,
    local_number: int,
    parent_number: int,
    tag: str,
    fix_commit: str,
    public_commit: str,
    tree_difference: str | None,
    pinned_version: str,
    pinned_commit: str,
    fix_in_tag: bool,
) -> dict[str, str]:
    def result(status: str, reason: str) -> dict[str, str]:
        return {"status": status, "reason": reason}

    if not SEMVER.fullmatch(tag) or not SHA.fullmatch(fix_commit):
        return result("blocked", "Provide an exact stable SemVer tag and full fix commit SHA")
    if parent.get("state") != "CLOSED":
        return result("awaiting-parent", "The parent issue is still open")
    if (parent.get("stateReason") or "").lower().replace(" ", "_") == "not_planned":
        return result("human-decision", "The parent declined the fix; leave the local issue open")
    if (parent.get("stateReason") or "").lower() != "completed":
        return result("blocked", "Parent issue closure is not confirmed as completed")
    if local.get("state") != "OPEN":
        return result("blocked", "Local issue is not open")
    labels = {item.get("name") for item in local.get("labels", []) if isinstance(item, dict)}
    if "awaiting-parity" not in labels:
        return result("blocked", "Local issue is not labeled awaiting-parity")
    local_body = str(local.get("body", ""))
    parent_body = str(parent.get("body", ""))
    if not has_issue_reference(local_body, PARENT_DEV, parent_number):
        return result("blocked", "Local issue does not cross-reference the parent issue")
    if not has_issue_reference(parent_body, LOCAL_REPO, local_number):
        return result("blocked", "Parent issue does not cross-reference the local issue")
    if tree_difference is not None:
        return result("blocked", tree_difference)
    if not fix_in_tag:
        return result("awaiting-release", "The target parent tag does not contain the fix commit")
    if pinned_version != tag or pinned_commit != public_commit:
        return result("awaiting-pin", "The local PARENT_VERSION/PARENT_COMMIT do not identify this released fix")
    return result("ready-to-close", "The completed fix is present in the exact pinned production tag")


def parity_status(
    local_number: int,
    parent_number: int,
    tag: str,
    fix_commit: str,
    parent_checkout: Path,
    public_checkout: Path,
) -> dict[str, str]:
    local = issue(LOCAL_REPO, local_number)
    parent = issue(PARENT_DEV, parent_number)
    if (parent.get("state") == "CLOSED"
            and (parent.get("stateReason") or "").lower().replace(" ", "_") == "not_planned"):
        return {"status": "human-decision", "reason": "The parent declined the fix; leave the local issue open"}
    parent_sha = tag_commit(parent_checkout, tag)
    public_sha = tag_commit(public_checkout, tag)
    if plugin_version(parent_checkout, tag) != tag or plugin_version(public_checkout, tag) != tag:
        raise EvidenceError("The development or public plugin manifest version differs from the parent tag")
    if public_sha != ROOT.joinpath("PARENT_COMMIT").read_text(encoding="utf-8").strip():
        raise EvidenceError("PARENT_COMMIT does not equal the public tag's full commit SHA")
    development_tree = tree(parent_checkout, tag)
    public_tree = tree(public_checkout, tag)
    return evaluate(
        local, parent, local_number=local_number, parent_number=parent_number, tag=tag,
        fix_commit=fix_commit, public_commit=public_sha,
        tree_difference=plugin_tree_difference(
            parent_checkout, development_tree, public_checkout, public_tree,
        ),
        pinned_version=ROOT.joinpath("PARENT_VERSION").read_text(encoding="utf-8").strip(),
        pinned_commit=ROOT.joinpath("PARENT_COMMIT").read_text(encoding="utf-8").strip(),
        fix_in_tag=ancestor(parent_checkout, fix_commit, tag),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local-issue", type=int, required=True)
    parser.add_argument("--parent-issue", type=int, required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--fix-commit", required=True)
    parser.add_argument("--parent-checkout", type=Path, required=True)
    parser.add_argument("--public-checkout", type=Path, required=True)
    parser.add_argument("--apply", action="store_true", help="close the local issue only if every R7 check passes")
    args = parser.parse_args()
    try:
        decision = parity_status(
            args.local_issue, args.parent_issue, args.tag, args.fix_commit,
            args.parent_checkout.resolve(), args.public_checkout.resolve(),
        )
        print(json.dumps(decision, indent=2))
        if args.apply and decision["status"] == "ready-to-close":
            command(
                "gh", "issue", "close", str(args.local_issue), "--repo", LOCAL_REPO,
                "--comment", (
                    f"Parity confirmed in tagged parent release {args.tag}; the parent fix "
                    f"{args.fix_commit} is present in the generated public plugin."
                ),
            )
            print(f"Closed {LOCAL_REPO}#{args.local_issue} after tagged parity verification.")
        elif args.apply and decision["status"] == "human-decision":
            print("Human decision required; local issue was not closed.", file=sys.stderr)
        return 0 if decision["status"] != "blocked" else 1
    except (EvidenceError, OSError, subprocess.CalledProcessError) as error:
        print(json.dumps({"status": "blocked", "reason": str(error)}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
