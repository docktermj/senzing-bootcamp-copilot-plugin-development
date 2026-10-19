from __future__ import annotations

import json
import subprocess
import tempfile
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
                "tool_name": "edit",
                "tool_input": {"file_path": "/etc/copilot-bootcamp-test"},
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
                "tool_name": "edit",
                "tool_input": {"file_path": "notes.md"},
            })
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")

    def test_agent_stop_blocks_missing_closing_question(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            (workspace / "config").mkdir()
            (workspace / "config/bootcamp_progress.json").write_text("{}")
            result = self.run_hook("agent-stop", workspace, {
                "last_assistant_message": "The step is complete."
            })
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["decision"], "block")

    def test_agent_stop_allows_closing_question(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            (workspace / "config").mkdir()
            (workspace / "config/bootcamp_progress.json").write_text("{}")
            result = self.run_hook("agent-stop", workspace, {
                "last_assistant_message": "👉 **Ready to continue?**"
            })
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
