from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


class CspellConfigTests(unittest.TestCase):
    def test_dev_config_only_imports_public_config_and_adds_reachings(self) -> None:
        config = json.loads((ROOT / ".vscode/cspell.dev.json").read_text(encoding="utf-8"))
        self.assertEqual(config["import"], ["./cspell.json"])
        # Exception for the wording tracked by #11; remove when #11 closes.
        self.assertEqual(config["words"], ["reachings"])
        self.assertEqual(set(config), {"version", "import", "words"})

    def test_propagated_files_exist_and_dev_config_is_not_among_them(self) -> None:
        skill = (ROOT / ".github/skills/propagate-to-public/SKILL.md").read_text(encoding="utf-8")
        for name in ("cspell.json", "cspell-bootcamp.txt"):
            self.assertTrue((ROOT / ".vscode" / name).is_file())
            self.assertIn(f".vscode/{name}", skill)
        self.assertIn("Never copy `.vscode/cspell.dev.json`", skill)

    def test_ci_runs_pinned_cspell_on_payload_and_site(self) -> None:
        workflow = (ROOT / ".github/workflows/verify-build-determinism.yml").read_text(encoding="utf-8")
        self.assertIn("cspell@9.2.1", workflow)
        self.assertIn(".vscode/cspell.dev.json", workflow)
        self.assertIn("plugins/senzing-bootcamp/**", workflow)
        self.assertIn("site/**", workflow)


if __name__ == "__main__":
    unittest.main()
