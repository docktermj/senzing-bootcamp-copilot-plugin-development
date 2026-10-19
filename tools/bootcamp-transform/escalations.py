#!/usr/bin/env python3
"""Verify R7 parity evidence and optionally close a local awaiting-parity issue."""

from __future__ import annotations

import argparse
import json
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


class EvidenceError(RuntimeError):
    """The parity evidence is incomplete or contradictory."""


def command(*args: str, cwd: Path | None = None) -> str:
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)
    if result.returncode:
        raise EvidenceError(result.stderr.strip() or f"command failed: {' '.join(args)}")
    return result.stdout.strip()


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


def plugin_version(checkout: Path, tag: str) -> str:
    raw = command(
        "git", "-C", str(checkout), "show",
        f"{tag}:plugins/senzing-bootcamp/.claude-plugin/plugin.json",
    )
    try:
        return str(json.loads(raw)["version"])
    except (KeyError, json.JSONDecodeError) as error:
        raise EvidenceError(f"Could not read the parent plugin version at tag {tag}") from error


def evaluate(
    local: dict,
    parent: dict,
    *,
    local_number: int,
    parent_number: int,
    tag: str,
    fix_commit: str,
    public_commit: str,
    development_tree: str,
    public_tree: str,
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
    if f"{PARENT_DEV}#{parent_number}" not in local_body:
        return result("blocked", "Local issue does not cross-reference the parent issue")
    if f"{LOCAL_REPO}#{local_number}" not in parent_body:
        return result("blocked", "Parent issue does not cross-reference the local issue")
    if development_tree != public_tree:
        return result("blocked", "Parent development and public plugin trees differ at the tag")
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
    return evaluate(
        local, parent, local_number=local_number, parent_number=parent_number, tag=tag,
        fix_commit=fix_commit, public_commit=public_sha,
        development_tree=tree(parent_checkout, tag), public_tree=tree(public_checkout, tag),
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
