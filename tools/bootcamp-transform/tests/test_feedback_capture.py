from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HOOK = ROOT / "plugins/senzing-bootcamp/scripts/feedback-capture.py"


class FeedbackCaptureTests(unittest.TestCase):
    def run_hook(self, prompt: str) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            (workspace / "config").mkdir()
            (workspace / "config/bootcamp_progress.json").write_text("{}")
            return subprocess.run(
                [sys.executable, str(HOOK)],
                cwd=workspace,
                input=json.dumps({"prompt": prompt}),
                text=True,
                capture_output=True,
                check=False,
            )

    def test_problem_in_earlier_sentence_does_not_capture_feedback(self) -> None:
        result = self.run_hook(
            "This is a live runtime check in a disposable test project. The saved progress "
            "says the current module is Discover the Business Problem. Yes, resume it. "
            "Use the plugin skill, ask only its next one question, and do not invent my "
            "business context or write project files."
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")

    def test_exact_business_problem_prompt_does_not_capture_feedback(self) -> None:
        result = self.run_hook("Discover the Business Problem. This mentions the plugin.")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")

    def test_fault_attribution_does_not_cross_sentence_boundaries(self) -> None:
        for boundary in ".!?;":
            for prompt in (
                f"The plugin{boundary} broken.",
                f"Broken{boundary} the plugin.",
            ):
                with self.subTest(prompt=prompt):
                    result = self.run_hook(prompt)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(result.stdout, "")

    def test_explicit_plugin_fault_still_captures_feedback(self) -> None:
        result = self.run_hook("The plugin is broken.")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("The bootcamper is submitting bootcamp feedback", result.stdout)

    def test_fault_before_referent_in_same_sentence_captures_feedback(self) -> None:
        result = self.run_hook("Broken: the plugin.")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("The bootcamper is submitting bootcamp feedback", result.stdout)

    def test_explicit_report_request_still_captures_feedback(self) -> None:
        result = self.run_hook("Please report an issue.")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("The bootcamper is submitting bootcamp feedback", result.stdout)
