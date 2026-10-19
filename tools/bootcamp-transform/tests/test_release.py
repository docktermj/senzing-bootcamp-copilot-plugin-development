from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import release


class ReleaseGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "docs/test-records").mkdir(parents=True)
        (self.root / "docs/test-checklist.md").write_text(
            "| ID | Required | Test |\n| TC-01 | Yes | Install plugin |\n"
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_missing_record_blocks_release(self) -> None:
        with self.assertRaisesRegex(ValueError, "Missing test record"):
            release.validate_record(self.root, "1.2.3")

    def test_blocked_record_blocks_release(self) -> None:
        (self.root / "docs/test-records/1.2.3.md").write_text(
            "**Release candidate:** 1.2.3\n**Status:** BLOCKED\n"
        )
        with self.assertRaisesRegex(ValueError, "status must be PASS"):
            release.validate_record(self.root, "1.2.3")


if __name__ == "__main__":
    unittest.main()
