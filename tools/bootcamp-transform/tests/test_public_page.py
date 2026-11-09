from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools/bootcamp-transform"))
import public_page

PAGE = """<p>(displayed as <code>senzing-bootcamp</code>, version {version})</p>
<pre><code>copilot plugin marketplace add Senzing/senzing-bootcamp-copilot-plugin
copilot plugin install senzing-bootcamp@senzing-bootcamp</code></pre>
<p class="callout"><strong>Published; app verification partial:</strong> some checks remain unrun.</p>
"""


class PublicPageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.public = base / "public"
        self.payload = base / "payload"
        (self.public / "docs").mkdir(parents=True)
        (self.public / ".github/plugin").mkdir(parents=True)
        self.payload.mkdir()
        (self.public / ".github/plugin/marketplace.json").write_text(
            json.dumps({"name": "senzing-bootcamp"}))
        (self.payload / "plugin.json").write_text(
            json.dumps({"name": "senzing-bootcamp", "version": "0.6.1"}))
        self.record = base / "0.6.1.md"
        self.record.write_text("# Record\n\n**Status:** PASS — CLI only.\n**Parent:** x\n")

    def page(self, version: str = "0.6.1") -> None:
        (self.public / "docs/index.html").write_text(PAGE.format(version=version))

    def test_matching_page_reports_no_mismatch(self) -> None:
        self.page()
        result = public_page.check(self.public, self.payload, self.record)
        self.assertTrue(all(item["match"] for item in result["facts"]))
        self.assertIn("0 mismatch(es)", public_page.render(result))

    def test_stale_version_is_a_mismatch(self) -> None:
        self.page("0.6.0")
        result = public_page.check(self.public, self.payload, self.record)
        versions = [item for item in result["facts"] if item["fact"] == "version"]
        self.assertFalse(versions[0]["match"])

    def test_wrong_marketplace_name_is_a_mismatch(self) -> None:
        self.page()
        (self.public / ".github/plugin/marketplace.json").write_text(
            json.dumps({"name": "other"}))
        result = public_page.check(self.public, self.payload, self.record)
        names = {item["fact"]: item["match"] for item in result["facts"]}
        self.assertFalse(names["plugin identifier"])
        self.assertFalse(names["install command"])

    def test_client_status_is_shown_but_never_compared(self) -> None:
        self.page()
        result = public_page.check(self.public, self.payload, self.record)
        self.assertIn("app verification partial", result["status"]["page"])
        self.assertEqual(result["status"]["record"], "PASS — CLI only.")
        self.assertEqual({item["fact"] for item in result["facts"]},
                         {"version", "plugin identifier", "marketplace add command",
                          "install command"})

    def test_missing_page_is_reported_not_an_error(self) -> None:
        result = public_page.check(self.public, self.payload, self.record)
        self.assertEqual(result["page"], "not found")
        self.assertIn("not found", public_page.render(result))

    def test_non_public_checkout_is_blocked(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools/bootcamp-transform/public_page.py"),
             "--public", self.temp.name],
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("Blocked", result.stderr)


if __name__ == "__main__":
    unittest.main()
