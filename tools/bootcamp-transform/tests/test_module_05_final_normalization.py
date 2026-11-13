from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[3]
PHASE1 = ROOT / (
    "plugins/senzing-bootcamp/skills/module-05-data-quality-mapping/phase1-quality-assessment.md"
)
FINAL_PASS_START = '<a id="the-final-pass"></a>'
FINAL_PASS_END = (
    "⛔ **(INV-284) Never offer an improvement option when nothing mechanical is left to fix.**"
)


def collapse(text: str) -> str:
    return " ".join(text.split())


class Module05FinalNormalizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.phase1 = PHASE1.read_text(encoding="utf-8")
        start = cls.phase1.index(FINAL_PASS_START)
        end = cls.phase1.index(FINAL_PASS_END, start)
        cls.final_pass = cls.phase1[start:end]
        cls.phase1_compact = collapse(cls.phase1)
        cls.final_pass_compact = collapse(cls.final_pass)

    def test_quality_gate_and_step_7b_gate_the_final_pass(self) -> None:
        self.assertIn("closed list in [Step 7b's final pass](#the-final-pass)",
                      self.phase1_compact)
        self.assertIn(
            "A source at 80% or more reaches no gate, so nothing is declared and no final pass runs.",
            self.phase1_compact,
        )
        self.assertIn(
            "first time, after a Step 7a pass that fixed everything, and after one that found nothing",
            self.final_pass_compact,
        )
        self.assertIn("every applicable field Step 6 measured for this source, emails included",
                      self.final_pass_compact)
        self.assertIn(
            "Step 7b's final pass confirms that before its form is presented.",
            self.phase1_compact,
        )

    def test_only_the_closed_value_preserving_correction_list_is_fixable(self) -> None:
        list_start = self.final_pass.index("**The closed list of corrections")
        list_end = self.final_pass.index("Nothing else is a correction here.", list_start)
        correction_list = self.final_pass[list_start:list_end]
        items = re.findall(r"(?m)^- (.+)$", correction_list)

        self.assertEqual(4, len(items))
        for expected in (
            "leading or trailing whitespace trimmed",
            "an email's domain lower-cased",
            "phone punctuation and date layout",
            "coded values (state, country) cased",
        ):
            self.assertTrue(any(expected in item for item in items), expected)
        self.assertIn("same record's raw value", self.final_pass_compact)
        self.assertIn("nothing from another record or an outside source", self.final_pass_compact)
        self.assertIn("Nothing else is a correction here.", self.final_pass_compact)
        self.assertIn("A missing value is never filled", self.final_pass_compact)
        self.assertIn("a value that differs in meaning rather than in form is never normalized away",
                      self.final_pass_compact)

    def test_corrections_reuse_step_7a_and_an_empty_pass_does_not_loop(self) -> None:
        self.assertIn("apply them through Step 7a steps 3 to 5 unchanged",
                      self.final_pass_compact)
        self.assertIn("a new improved copy, every registry field it changes, and a re-score",
                      self.final_pass_compact)
        self.assertIn("The gate is re-presented with the new score", self.final_pass_compact)
        self.assertIn("the pass runs again and must find nothing", self.final_pass_compact)
        self.assertIn("without looping", self.final_pass_compact)
        self.assertIn("not repeated for the same file", self.final_pass_compact)
        self.assertIn("a `provenance: synthesized` source the pass runs the same way",
                      self.final_pass_compact)


if __name__ == "__main__":
    unittest.main()
