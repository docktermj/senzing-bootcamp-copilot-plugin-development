from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import escalations

FIX = "1" * 40
PUBLIC = "3" * 40


def evidence(parent: dict | None = None, **overrides: object) -> dict:
    values = {
        "local": {
            "state": "OPEN",
            "body": "Fix: docktermj/senzing-bootcamp-claude-plugin-development#22",
            "labels": [{"name": "awaiting-parity"}],
        },
        "parent": {
            "state": "CLOSED",
            "stateReason": "completed",
            "body": "Child: docktermj/senzing-bootcamp-copilot-plugin-development#11",
        },
        "local_number": 11,
        "parent_number": 22,
        "tag": "0.6.2",
        "fix_commit": FIX,
        "public_commit": PUBLIC,
        "development_tree": "same-tree",
        "public_tree": "same-tree",
        "pinned_version": "0.6.2",
        "pinned_commit": PUBLIC,
        "fix_in_tag": True,
    }
    if parent is not None:
        values["parent"] = parent
    values.update(overrides)
    return escalations.evaluate(**values)


class EscalationParityTests(unittest.TestCase):
    def test_closes_only_when_tagged_fix_and_pin_match(self) -> None:
        self.assertEqual(evidence()["status"], "ready-to-close")

    def test_waits_for_release_containing_fix(self) -> None:
        self.assertEqual(evidence(fix_in_tag=False)["status"], "awaiting-release")

    def test_parent_not_planned_requires_human_decision(self) -> None:
        result = evidence(parent={
            "state": "CLOSED",
            "stateReason": "not_planned",
            "body": "",
        })
        self.assertEqual(result["status"], "human-decision")

    def test_missing_awaiting_parity_label_blocks_closure(self) -> None:
        self.assertEqual(evidence(local={
            "state": "OPEN", "body": "docktermj/senzing-bootcamp-claude-plugin-development#22",
            "labels": [],
        })["status"], "blocked")


if __name__ == "__main__":
    unittest.main()
