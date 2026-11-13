from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PLUGIN = ROOT / "plugins/senzing-bootcamp"
SCRIPTS = PLUGIN / "scripts"


def project(test: unittest.TestCase, progress: dict | str | None,
            preferences: str | None = None) -> Path:
    temp = tempfile.TemporaryDirectory()
    test.addCleanup(temp.cleanup)
    root = Path(temp.name)
    (root / "config").mkdir()
    if progress is not None:
        contents = json.dumps(progress) if isinstance(progress, dict) else progress
        (root / "config/bootcamp_progress.json").write_text(contents, encoding="utf-8")
    if preferences is not None:
        (root / "config/bootcamp_preferences.yaml").write_text(preferences, encoding="utf-8")
    return root


def run_script(test: unittest.TestCase, script: str, root: Path,
               payload: dict | None = None) -> str:
    env = dict(os.environ)
    env.pop("SENZING_BOOTCAMP_DISABLE_STOP_NUDGE", None)
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / script)],
        cwd=root,
        input=json.dumps(payload or {}),
        text=True,
        capture_output=True,
        check=False,
        timeout=10,
        env=env,
    )
    test.assertEqual(0, result.returncode, result.stderr)
    return result.stdout


def predicate(test: unittest.TestCase, root: Path) -> bool:
    code = (
        f"import sys; sys.path.insert(0, {str(SCRIPTS)!r}); "
        "import module_start_apparatus; print(module_start_apparatus.bootcamp_complete())"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
        timeout=10,
    )
    test.assertEqual(0, result.returncode, result.stderr)
    return result.stdout.strip() == "True"


class CompletionStateTests(unittest.TestCase):
    def test_completion_is_recognized_from_either_store(self) -> None:
        cases = (
            (
                "progress only",
                {"current_module": "graduation", "bootcamp_complete": True},
                "bootcamp_complete: false\n",
                True,
            ),
            (
                "legacy preferences only",
                {"current_module": "query_visualize_discover"},
                "bootcamp_complete: true\n",
                True,
            ),
            ("missing progress", None, "bootcamp_complete: true\n", True),
            ("malformed progress", "{", "bootcamp_complete: 'YES'\n", True),
            (
                "neither",
                {"current_module": "sdk_setup", "current_step": 2},
                "bootcamp_complete: false\n",
                False,
            ),
        )
        for name, progress, preferences, expected in cases:
            with self.subTest(name=name):
                self.assertEqual(expected, predicate(self, project(self, progress, preferences)))

    def test_false_progress_flags_do_not_mark_an_active_project_finished(self) -> None:
        for value in (False, "false", "no", 0, None):
            with self.subTest(value=value):
                self.assertFalse(predicate(self, project(
                    self,
                    {"current_module": "sdk_setup", "bootcamp_complete": value},
                )))

    def test_session_start_never_resumes_a_finished_or_fresh_project(self) -> None:
        finished = (
            ({"current_module": "graduation", "bootcamp_complete": True}, None),
            ({"current_module": "query_visualize_discover"}, "bootcamp_complete: true\n"),
            ("{", "bootcamp_complete: true\n"),
        )
        for progress, preferences in finished:
            with self.subTest(progress=progress, preferences=preferences):
                output = run_script(
                    self, "session-start.py", project(self, progress, preferences)
                )
                self.assertIn("bootcamp is complete", output)
                self.assertIn("the package-bootcamp skill", output)
                self.assertNotIn("offer to resume from", output)
                self.assertNotIn("Module-start reminder", output)
                output.encode("ascii")

        fresh = (
            (None, None),
            ("", None),
            ("{", None),
            ('{"current_module": null}', None),
        )
        for progress, preferences in fresh:
            with self.subTest(fresh_progress=progress):
                self.assertEqual(
                    "",
                    run_script(self, "session-start.py", project(self, progress, preferences)),
                )

    def test_stop_nudge_stands_down_only_for_completed_projects(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            transcript = Path(temp) / "transcript.jsonl"
            transcript.write_text(json.dumps({
                "type": "assistant",
                "message": {"content": "The step is complete."},
            }) + "\n", encoding="utf-8")
            payload = {"stop_hook_active": False, "transcript_path": str(transcript)}
            completed = (
                ({"current_module": "graduation", "bootcamp_complete": True}, None),
                ({"current_module": "query_visualize_discover"}, "bootcamp_complete: true\n"),
            )
            for progress, preferences in completed:
                with self.subTest(progress=progress, preferences=preferences):
                    self.assertEqual(
                        "",
                        run_script(
                            self, "stop-nudge.py", project(self, progress, preferences), payload
                        ),
                    )

            active = run_script(
                self, "stop-nudge.py",
                project(self, {"current_module": "sdk_setup"}, "bootcamp_complete: false\n"),
                payload,
            )
            self.assertEqual("block", json.loads(active)["decision"])

    def test_module_number_reminder_stands_down_after_completion(self) -> None:
        root = project(self, {"current_module": "graduation", "bootcamp_complete": True})
        self.assertEqual("", run_script(self, "module-number-reminder.py", root, {}))

    def test_graduation_records_both_paths_without_completing_early(self) -> None:
        graduation = (PLUGIN / "skills/graduation/SKILL.md").read_text(encoding="utf-8")
        exploration = graduation.split("**Wants to keep exploring**", 1)[1].split(
            "**Declines**", 1
        )[0]
        self.assertNotIn("bootcamp_complete", exploration)
        self.assertNotIn("bootcamp_progress.json", exploration)

        decline = graduation.split("**Declines**", 1)[1].split(
            "2. **Render the terminal banner", 1
        )[0]
        for clause in (
            "bootcamp_complete: true",
            "completed_at",
            'current_module: "graduation"',
            "current_step: null",
            "append `graduation` to `modules_completed` if it is absent",
            "keeping every other key as it is",
            "normal path and after Step 2's Abort alike",
        ):
            with self.subTest(clause=clause):
                self.assertIn(clause, decline)

        banner = graduation.index("END OF SENZING BOOTCAMP")
        package_line = graduation.index("Run `the package-bootcamp skill` anytime", banner)
        self.assertLess(banner, package_line)
        self.assertIn("That line is the final output", graduation[package_line:])

    def test_onboarding_and_journey_map_state_the_finished_case(self) -> None:
        onboarding = (PLUGIN / "skills/bootcamp-onboarding/SKILL.md").read_text(
            encoding="utf-8"
        )
        onboarding = " ".join(onboarding.split())
        finished = onboarding.index("- **Finished**")
        missing = onboarding.index("- **Missing**")
        self.assertLess(finished, missing)
        self.assertIn("Run no onboarding and make no resume offer", onboarding[finished:missing])

        ground_rules = (
            PLUGIN / "skills/bootcamp-onboarding/ground-rules.md"
        ).read_text(encoding="utf-8")
        self.assertIn("marks every row `✅ done`, Bootcamp graduation included", ground_rules)
        self.assertIn("`current_module` still reads `graduation` then", ground_rules)


if __name__ == "__main__":
    unittest.main()
