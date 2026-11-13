from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[3]
PHASE2 = ROOT / (
    "plugins/senzing-bootcamp/skills/module-05-data-quality-mapping/phase2-data-mapping.md"
)
PHASE3 = ROOT / (
    "plugins/senzing-bootcamp/skills/module-05-data-quality-mapping/phase3-test-load.md"
)
GATE_START = "> **Analyzer Python requirement for `sz_json_analyzer.py` only:**"
GATE_END = "> 1. **`sz_json_analyzer.py` (primary validation):**"


def collapse(text: str) -> str:
    return " ".join(" ".join(line.lstrip(" >").split()) for line in text.splitlines())


def gate_text(phase2: str) -> str:
    start = phase2.find(GATE_START)
    end = phase2.find(GATE_END, start + len(GATE_START))
    if start < 0 or end < 0:
        return ""
    return collapse(phase2[start:end])


class Module05CompatiblePythonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.phase2 = PHASE2.read_text(encoding="utf-8")
        cls.phase3 = collapse(PHASE3.read_text(encoding="utf-8"))
        cls.gate = gate_text(cls.phase2)

    def test_compatible_default_runs_without_a_probe_or_install_question(self) -> None:
        self.assertIn("At **3.10 or newer**, run the returned `analyze_record` command with `python3`;",
                      self.gate)
        self.assertIn("do not probe or ask about installation.", self.gate)

    def test_incompatible_default_probes_and_uses_the_first_compatible_interpreter(self) -> None:
        self.assertIn(
            "where the analyzer runs: inside the container on the `docker` route, and on the host "
            "on a native route",
            self.gate,
        )
        versions = [self.gate.index(f"`python3.{version}`") for version in ("13", "12", "11", "10")]
        self.assertEqual(sorted(versions), versions)
        self.assertIn("from `PATH`, newest first, each with `--version`", self.gate)
        self.assertIn("Use the first that reports 3.10 or newer.", self.gate)
        self.assertIn("Silently skip a candidate that fails or reports below 3.10", self.gate)
        self.assertIn("do not try any `py` launcher form", self.gate)
        self.assertIn("On Windows try the same four names", self.gate)
        self.assertIn("Search nothing outside `PATH`.", self.gate)
        self.assertIn("This interpreter choice applies only to `sz_json_analyzer.py`", self.gate)
        self.assertIn("schema-generator, verbatim-check and routing-report scripts keep `python3`",
                      self.gate)
        self.assertIn("say in one line, and ask nothing", self.gate)
        found = self.gate[self.gate.index("**The probe finds one:**"):
                          self.gate.index("**The probe finds none:**")]
        self.assertNotIn("👉", found)
        self.assertNotIn("?", found)
        self.assertIn(
            "Run the command returned by `analyze_record` with that interpreter named explicitly",
            found,
        )

    def test_no_compatible_interpreter_offers_one_setup_path_then_skips_later_runs(self) -> None:
        self.assertEqual(1, self.gate.count("👉"))
        none = self.gate.index("**The probe finds none:**")
        question = self.gate.index("👉")
        yes = self.gate.index("- **Yes:**")
        no = self.gate.index("- **No:**")
        later = self.gate.index("**Later analyzer runs:**")
        self.assertLess(none, question)
        self.assertLess(question, yes)
        self.assertLess(yes, no)
        self.assertLess(no, later)
        self.assertIn("Homebrew on macOS", self.gate)
        self.assertIn("distribution's package manager", self.gate)
        self.assertIn("python.org", self.gate)
        self.assertIn("`winget` on Windows", self.gate)
        self.assertIn("never replacing it", self.gate)
        self.assertIn("If installation fails, take the **No** path.", self.gate)
        self.assertIn("record the skip and reason in the source's mapping notes", self.gate)
        self.assertIn("The skip stands for the rest of the session; do not ask again", self.gate)

    def test_later_module_five_sites_reuse_the_selection_or_skip(self) -> None:
        later = self.gate[self.gate.index("**Later analyzer runs:**"):]
        self.assertIn("Step 14 and Phase 3's pre-load validation", later)
        self.assertIn("`phase3-test-load.md`", later)
        self.assertIn(
            "the session resumed without its outcome, run the check and probe there before the analyzer",
            later,
        )
        self.assertIn(
            "after **Yes** or a compatible probe result, use the selected interpreter explicitly",
            later,
        )
        self.assertIn("after **No**, skip the analyzer at every later site", later)
        self.assertIn("phase2-data-mapping.md` → \"Analyzer Python requirement", self.phase3)
        self.assertIn("Reuse this session's selected interpreter explicitly", self.phase3)
        self.assertIn(
            "If the **No** path was taken or installation failed, skip this analyzer run",
            self.phase3,
        )
        self.assertIn("workspace_dir='data/mapping'", self.phase3)


if __name__ == "__main__":
    unittest.main()
