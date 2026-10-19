#!/usr/bin/env python3
"""Check canonical operation names and cross-repository write boundaries."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "tools/bootcamp-transform/operations.json"
SKILLS = ROOT / ".github/skills"
EXPECTED = {
    "parity-check",
    "escalate-to-parent",
    "feedback-to-issues",
    "implement-github-issue",
    "retrofit-from-public",
    "production-readiness-audit",
    "dry-run",
    "release",
    "propagate-to-public",
}
errors: list[str] = []
registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
if set(registry.get("canonical_operations", [])) != EXPECTED:
    errors.append("operation registry differs from the required canonical operation set")
if registry.get("external_issue_writers") != ["escalate-to-parent"]:
    errors.append("escalate-to-parent must be the sole external issue writer")
if registry.get("public_worktree_writers") != ["propagate-to-public"]:
    errors.append("propagate-to-public must be the sole public working-tree writer")
if registry.get("git_publishers") != []:
    errors.append("no operation may publish to a remote repository")

actual = {path.parent.name for path in SKILLS.glob("*/SKILL.md")}
if actual != EXPECTED:
    errors.append(f"operation skill set mismatch: missing={sorted(EXPECTED - actual)}, extra={sorted(actual - EXPECTED)}")

external_issue_write = re.compile(
    r"\b(?:gh\s+issue\s+(?:create|edit|close|reopen|comment)|"
    r"gh\s+api\s+repos/(?!docktermj/senzing-bootcamp-copilot-plugin-development)[^\s]+"
    r".*(?:POST|PATCH|PUT|DELETE))\b",
    re.I,
)
for skill in sorted(SKILLS.glob("*/SKILL.md")):
    if skill.parent.name != "escalate-to-parent" and external_issue_write.search(
        skill.read_text(encoding="utf-8")
    ):
        errors.append(f"{skill.parent.name} contains an external issue-write command")

script_issue_write = re.compile(
    r"\bgh\s+issue\s+(?:create|edit|close|reopen|comment)\b",
    re.I,
)
scripts = ROOT / "tools/bootcamp-transform"
for script in sorted(scripts.glob("*.py")):
    text = script.read_text(encoding="utf-8")
    if script_issue_write.search(text):
        if script.name != "escalations.py":
            errors.append(f"{script.name} contains an unregistered issue-write command")
        elif not re.search(
            r'LOCAL_REPO\s*=\s*["\']docktermj/senzing-bootcamp-copilot-plugin-development["\']',
            text,
        ) or not re.search(r'"--repo",\s*LOCAL_REPO', text):
            errors.append("escalations.py issue writes must target the local repository explicitly")
if errors:
    print("Maintainer operation checks failed:")
    for error in errors:
        print(f"- {error}")
    raise SystemExit(1)
print(f"Maintainer operation checks passed ({len(EXPECTED)} canonical operations)")
