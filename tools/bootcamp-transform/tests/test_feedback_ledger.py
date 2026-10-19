from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import feedback_ledger


class FeedbackLedgerTests(unittest.TestCase):
    def test_duplicate_content_is_not_recorded_twice(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            entry = root / "entry.md"
            entry.write_text("feedback text\n")
            ledger = root / "feedback.jsonl"
            first = feedback_ledger.record(
                entry, "local", "this-repository", "filed",
                "https://github.com/docktermj/senzing-bootcamp-copilot-plugin-development/issues/1",
                ledger,
            )
            second = feedback_ledger.record(
                entry, "local", "this-repository", "filed",
                "https://github.com/docktermj/senzing-bootcamp-copilot-plugin-development/issues/1",
                ledger,
            )
            self.assertEqual(first["status"], "recorded")
            self.assertEqual(second["status"], "already-processed")
            self.assertEqual(len(feedback_ledger.read_entries(ledger)), 1)

    def test_failed_outcome_cannot_be_archived(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            entry = root / "entry.md"
            entry.write_text("feedback text")
            with self.assertRaisesRegex(ValueError, "issue URL"):
                feedback_ledger.record(
                    entry, "local", "this-repository", "filed", ledger_path=root / "ledger",
                )

    def test_active_lock_prevents_a_concurrent_append(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            entry = root / "entry.md"
            entry.write_text("feedback text")
            ledger = root / "feedback.jsonl"
            (root / "feedback.jsonl.lock").touch()
            with self.assertRaisesRegex(ValueError, "ledger is locked"):
                feedback_ledger.record(
                    entry, "local", "this-repository", "filed",
                    "https://github.com/docktermj/senzing-bootcamp-copilot-plugin-development/issues/1",
                    ledger,
                )
            self.assertFalse(ledger.exists())


if __name__ == "__main__":
    unittest.main()
