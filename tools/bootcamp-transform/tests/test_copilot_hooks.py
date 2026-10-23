from __future__ import annotations

import json
import subprocess
import tempfile
import threading
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HOOK = ROOT / "plugins/senzing-bootcamp/scripts/copilot-hooks.py"


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
            self.assertIn("post-question narration", response["reason"])

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


if __name__ == "__main__":
    unittest.main()
