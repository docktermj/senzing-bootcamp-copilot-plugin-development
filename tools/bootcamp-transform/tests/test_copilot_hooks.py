from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import threading
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HOOK = ROOT / "plugins/senzing-bootcamp/scripts/copilot-hooks.py"


def load_hook_module():
    spec = importlib.util.spec_from_file_location("copilot_hooks_under_test", HOOK)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class WriteInputTests(unittest.TestCase):
    def setUp(self) -> None:
        self.write_input = load_hook_module()._write_input

    def test_dict_args_are_merged(self) -> None:
        result = self.write_input({"args": {"content": "x", "mode": "w"}}, "a.md")
        self.assertEqual(result, {"content": "x", "mode": "w", "file_path": "a.md"})

    def test_json_string_args_are_parsed(self) -> None:
        result = self.write_input({"args": json.dumps({"content": "x"})}, "a.md")
        self.assertEqual(result, {"content": "x", "file_path": "a.md"})

    def test_non_json_string_becomes_content(self) -> None:
        patch = "*** Begin Patch\n*** Add File: a.md\n+x\n*** End Patch\n"
        result = self.write_input({"args": patch}, "a.md")
        self.assertEqual(result, {"content": patch, "file_path": "a.md"})

    def test_missing_or_non_mapping_args_keep_only_target(self) -> None:
        self.assertEqual(self.write_input({}, "a.md"), {"file_path": "a.md"})
        self.assertEqual(self.write_input({"args": "[1]"}, "a.md"), {"file_path": "a.md"})

    def test_target_overrides_path_keys_in_args(self) -> None:
        result = self.write_input(
            {"args": {"file_path": "/etc/x", "path": "/etc/y", "filePath": "/etc/z"}}, "a.md"
        )
        self.assertEqual(result["file_path"], "a.md")


class CopilotHookTests(unittest.TestCase):
    def run_hook(self, action: str, cwd: Path, payload: dict) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(HOOK), action],
            cwd=cwd,
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=False,
        )

    def test_pre_tool_denies_outside_project_write(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            (workspace / "config").mkdir()
            (workspace / "config/bootcamp_progress.json").write_text("{}")
            result = self.run_hook("pre-tool", workspace, {
                "toolCalls": [{
                    "name": "apply_patch",
                    "args": (
                        "*** Begin Patch\n"
                        "*** Add File: /etc/copilot-bootcamp-test\n"
                        "+blocked\n"
                        "*** End Patch\n"
                    ),
                }],
            })
            self.assertEqual(result.returncode, 0, result.stderr)
            response = json.loads(result.stdout)
            self.assertEqual(response["permissionDecision"], "deny")

    def test_pre_tool_allows_in_project_write(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            (workspace / "config").mkdir()
            (workspace / "config/bootcamp_progress.json").write_text("{}")
            result = self.run_hook("pre-tool", workspace, {
                "toolCalls": [{
                    "name": "apply_patch",
                    "args": (
                        "*** Begin Patch\n"
                        "*** Add File: notes.md\n"
                        "+allowed\n"
                        "*** End Patch\n"
                    ),
                }],
            })
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")

    def test_pre_tool_does_not_gate_external_read_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            (workspace / "config").mkdir()
            (workspace / "config/bootcamp_progress.json").write_text("{}")
            result = self.run_hook("pre-tool", workspace, {
                "toolCalls": [{
                    "name": "Read",
                    "args": {"file_path": "/tmp/plugin/skills/feedback.md"},
                }],
            })
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")

    def test_pre_tool_fails_closed_when_patch_target_cannot_be_parsed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            (workspace / "config").mkdir()
            (workspace / "config/bootcamp_progress.json").write_text("{}")
            result = self.run_hook("pre-tool", workspace, {
                "toolCalls": [{"name": "apply_patch", "args": "unrecognized patch"}],
            })
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Could not determine the write target", result.stderr)

    def test_agent_stop_blocks_missing_closing_question(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            (workspace / "config").mkdir()
            (workspace / "config/bootcamp_progress.json").write_text("{}")
            transcript = workspace / "events.jsonl"
            transcript.write_text(json.dumps({
                "type": "assistant.message",
                "data": {"content": "The step is complete."},
            }) + "\n")
            result = self.run_hook("agent-stop", workspace, {
                "stop_hook_active": False,
                "transcriptPath": str(transcript),
            })
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["decision"], "block")

    def test_agent_stop_accepts_vs_code_compatible_message_field(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            (workspace / "config").mkdir()
            (workspace / "config/bootcamp_progress.json").write_text("{}")
            result = self.run_hook("agent-stop", workspace, {
                "stop_hook_active": False,
                "last_assistant_message": "The step is complete.",
            })
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["decision"], "block")

    def test_agent_stop_waits_for_current_turn_transcript_message(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            (workspace / "config").mkdir()
            (workspace / "config/bootcamp_progress.json").write_text("{}")
            transcript = workspace / "events.jsonl"
            transcript.write_text(
                json.dumps({
                    "type": "assistant.message",
                    "data": {"content": "👉 **Previous turn?**"},
                }) + "\n" + json.dumps({"type": "user.message", "data": {"content": "Current turn"}})
                + "\n" + json.dumps({"type": "assistant.message", "data": {"content": ""}}) + "\n"
            )

            def append_final_message() -> None:
                time.sleep(0.1)
                with transcript.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps({
                        "type": "assistant.message",
                        "data": {"content": "The current step is complete."},
                    }) + "\n")

            writer = threading.Thread(target=append_final_message)
            writer.start()
            result = self.run_hook("agent-stop", workspace, {
                "stop_hook_active": False,
                "transcript_path": str(transcript),
            })
            writer.join()
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["decision"], "block")

    def test_agent_stop_allows_closing_question(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            (workspace / "config").mkdir()
            (workspace / "config/bootcamp_progress.json").write_text("{}")
            transcript = workspace / "events.jsonl"
            transcript.write_text(json.dumps({
                "type": "assistant.message",
                "data": {"content": "👉 **Ready to continue?**"},
            }) + "\n")
            result = self.run_hook("agent-stop", workspace, {
                "stop_hook_active": False,
                "transcriptPath": str(transcript),
            })
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")

    def test_agent_stop_blocks_arrow_marker_without_question(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            (workspace / "config").mkdir()
            (workspace / "config/bootcamp_progress.json").write_text("{}")
            result = self.run_hook("agent-stop", workspace, {
                "stop_hook_active": False,
                "last_assistant_message": "👉 **The step is complete.**",
            })
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["decision"], "block")

    def test_agent_stop_allows_closing_question_with_numbered_options(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            (workspace / "config").mkdir()
            (workspace / "config/bootcamp_progress.json").write_text("{}")
            result = self.run_hook("agent-stop", workspace, {
                "stop_hook_active": False,
                "last_assistant_message": (
                    "Choose an option.\n\n"
                    "👉 **Where should it run?**\n\n"
                    "1. Local\n"
                    "2. Cloud"
                ),
            })
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")

    def test_agent_stop_blocks_post_question_narration(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            (workspace / "config").mkdir()
            (workspace / "config/bootcamp_progress.json").write_text("{}")
            result = self.run_hook("agent-stop", workspace, {
                "stop_hook_active": False,
                "last_assistant_message": (
                    "👉 **Where should it run?**\n\n"
                    "1. Local\n"
                    "2. Cloud\n\n"
                    "I'm waiting for your answer."
                ),
            })
            self.assertEqual(result.returncode, 0, result.stderr)
            response = json.loads(result.stdout)
            self.assertEqual(response["decision"], "block")
            self.assertIn("do not repeat it", response["reason"])

    def test_agent_stop_reason_is_user_facing_and_never_asks_to_repeat(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            (workspace / "config").mkdir()
            (workspace / "config/bootcamp_progress.json").write_text("{}")
            result = self.run_hook("agent-stop", workspace, {
                "stop_hook_active": False,
                "last_assistant_message": "Working on it.",
            })
            reason = json.loads(result.stdout)["reason"]
            self.assertIn("module's prescribed closing question", reason)
            self.assertIn("do not repeat it", reason)
            self.assertNotIn("internal", reason.lower())

    def test_agent_stop_blocks_duplicate_closing_markers(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            (workspace / "config").mkdir()
            (workspace / "config/bootcamp_progress.json").write_text("{}")
            result = self.run_hook("agent-stop", workspace, {
                "stop_hook_active": False,
                "last_assistant_message": (
                    "👉 **First question?**\n\n👉 **Second question?**"
                ),
            })
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["decision"], "block")

    def run_in_project(self, action: str, payload: dict) -> tuple[subprocess.CompletedProcess[str], Path]:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        workspace = Path(temp.name)
        (workspace / "config").mkdir()
        (workspace / "config/bootcamp_progress.json").write_text("{}")
        return self.run_hook(action, workspace, payload), workspace

    def make_project(self, progress: dict | str | None, preferences: str | None = None) -> Path:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        workspace = Path(temp.name)
        (workspace / "config").mkdir()
        if progress is not None:
            contents = json.dumps(progress) if isinstance(progress, dict) else progress
            (workspace / "config/bootcamp_progress.json").write_text(contents, encoding="utf-8")
        if preferences is not None:
            (workspace / "config/bootcamp_preferences.yaml").write_text(
                preferences, encoding="utf-8"
            )
        return workspace

    def test_agent_stop_stays_silent_for_progress_only_completion(self) -> None:
        workspace = self.make_project({
            "current_module": "graduation",
            "bootcamp_complete": True,
        }, "bootcamp_complete: false\n")
        result = self.run_hook("agent-stop", workspace, {
            "stop_hook_active": False,
            "last_assistant_message": "END OF SENZING BOOTCAMP",
        })
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")

    def test_agent_stop_honors_legacy_preferences_only_completion(self) -> None:
        for flag in ("bootcamp_complete: true\n", "bootcamp_complete: 'YES'\n"):
            with self.subTest(flag=flag):
                workspace = self.make_project(
                    {"current_module": "query_visualize_discover"},
                    flag,
                )
                result = self.run_hook("agent-stop", workspace, {
                    "stop_hook_active": False,
                    "last_assistant_message": "END OF SENZING BOOTCAMP",
                })
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, "")

    def test_session_start_announces_completion_without_resume(self) -> None:
        workspace = self.make_project({
            "current_module": "graduation",
            "bootcamp_complete": True,
        })
        result = self.run_hook("session-start", workspace, {})
        self.assertEqual(result.returncode, 0, result.stderr)
        context = json.loads(result.stdout)["additionalContext"]
        self.assertIn("bootcamp is complete", context)
        self.assertIn("the package-bootcamp skill", context)
        self.assertNotIn("A Senzing bootcamp is in progress", context)

    def test_user_prompt_does_not_create_checkpoint_after_completion(self) -> None:
        cases = (
            ({
                "current_module": "graduation",
                "bootcamp_complete": True,
            }, "bootcamp_complete: false\n"),
            ({
                "current_module": "query_visualize_discover",
            }, "bootcamp_complete: true\n"),
        )
        for progress, preferences in cases:
            with self.subTest(progress=progress, preferences=preferences):
                workspace = self.make_project(progress, preferences)
                result = self.run_hook("user-prompt", workspace, {"prompt": "Continue"})
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, "")
                self.assertFalse((workspace / "docs/progress/recap_checkpoint.md").exists())

    # Assembled at runtime so no secret-shaped literal sits in the repository.
    SYNTHETIC_SECRET = "AKIA" + "1234567890ABCDEF"

    def test_pre_tool_denies_secret_in_write_content(self) -> None:
        result, _ = self.run_in_project("pre-tool", {
            "toolName": "write_file",
            "toolArgs": {"file_path": "notes.txt", "content": self.SYNTHETIC_SECRET},
        })
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["permissionDecision"], "deny")

    def test_pre_tool_allows_ordinary_write_content(self) -> None:
        result, _ = self.run_in_project("pre-tool", {
            "tool_name": "write_file",
            "tool_input": {"file_path": "notes.txt", "content": "Ordinary synthetic note."},
        })
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")

    def test_pre_tool_scans_apply_patch_text(self) -> None:
        result, _ = self.run_in_project("pre-tool", {
            "toolCalls": [{
                "name": "apply_patch",
                "args": (
                    "*** Begin Patch\n*** Add File: notes.txt\n"
                    f"+{self.SYNTHETIC_SECRET}\n*** End Patch"
                ),
            }],
        })
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["permissionDecision"], "deny")

    def test_pre_tool_denies_out_of_project_write_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp) / "project"
            (workspace / "config").mkdir(parents=True)
            (workspace / "config/bootcamp_progress.json").write_text("{}")
            result = self.run_hook("pre-tool", workspace, {
                "toolName": "write_file",
                "toolArgs": {
                    "file_path": str(workspace.parent / "outside.txt"),
                    "content": "Ordinary synthetic note.",
                },
            })
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["permissionDecision"], "deny")

    def test_stop_alias_payload_blocks_when_active_turn_has_no_question(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            (workspace / "config").mkdir()
            (workspace / "config/bootcamp_progress.json").write_text("{}")
            transcript = workspace / "transcript.jsonl"
            transcript.write_text(
                "\n".join((
                    json.dumps({"type": "user.message", "data": {"content": "Continue"}}),
                    json.dumps({"type": "assistant.message", "data": {"content": "DONE"}}),
                )),
                encoding="utf-8",
            )
            result = self.run_hook("agent-stop", workspace, {
                "hook_event_name": "Stop",
                "stop_hook_active": False,
                "transcript_path": str(transcript),
            })
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["decision"], "block")

    def test_stop_alias_does_not_block_its_own_continuation(self) -> None:
        result, workspace = self.run_in_project("agent-stop", {
            "hook_event_name": "Stop",
            "stop_hook_active": True,
            "transcript_path": "missing.jsonl",
        })
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
