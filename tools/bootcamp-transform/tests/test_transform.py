from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import transform


class TransformTests(unittest.TestCase):
    def test_exactly_one_file_rule_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp)
            (source / "nested").mkdir()
            (source / "nested/kept.md").write_text("content")
            rules = [
                {"id": "keep", "kind": "copy", "match": ["**/*.md"]},
                {"id": "exclude", "kind": "ignore", "match": ["*.md"]},
            ]
            with self.assertRaisesRegex(transform.TransformError, "E_AMBIGUOUS_FILE"):
                transform.plan_files(source, {"rules": rules})

    def test_unmatched_file_fails_with_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp)
            (source / "new-parent-file.txt").write_text("content")
            with self.assertRaisesRegex(transform.TransformError, "new-parent-file.txt"):
                transform.plan_files(source, {"rules": []})

    def test_reconciliation_reports_all_change_categories(self) -> None:
        old = {
            "files": {
                "edited.md": {"generated": "old", "output": "old"},
                "removed.md": {"generated": "gone", "output": "gone"},
                "modified.md": {"generated": "old", "output": "old"},
                "preserved.md": {"generated": "same", "output": "before"},
            }
        }
        current = {
            "edited.md": "edited",
            "removed.md": "gone",
            "modified.md": "old",
            "preserved.md": "local",
            "local-only.md": "local",
        }
        generated = {
            "edited.md": "new",
            "added.md": "added",
            "modified.md": "new",
            "preserved.md": "same",
        }
        report = {path: status for status, path in transform.reconcile(old, current, generated)}
        self.assertEqual(report["edited.md"], "conflict")
        self.assertEqual(report["removed.md"], "removed")
        self.assertEqual(report["modified.md"], "modified")
        self.assertEqual(report["preserved.md"], "preserved")
        self.assertEqual(report["added.md"], "added")
        self.assertEqual(report["local-only.md"], "preserved")

    def test_added_path_collision_is_a_conflict(self) -> None:
        report = transform.reconcile(
            {"files": {}},
            {"new.md": "hand-edited"},
            {"new.md": "generated"},
        )
        self.assertEqual(report, [("conflict", "new.md")])

    def test_only_exact_stable_semver_is_accepted(self) -> None:
        for invalid in ("main", "HEAD", "v0.6.1", "0.6", "0.6.1-rc.1"):
            with self.subTest(invalid=invalid), self.assertRaises(transform.TransformError):
                transform.build(invalid, Path("."), Path("missing"))


if __name__ == "__main__":
    unittest.main()
