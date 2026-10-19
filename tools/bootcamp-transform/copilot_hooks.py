#!/usr/bin/env python3
"""Adapt the parent plugin's hook helpers to GitHub Copilot CLI hook payloads."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

PLUGIN_ROOT = Path(__file__).resolve().parents[1]


def _payload() -> dict[str, Any]:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw or "{}")
    except json.JSONDecodeError as error:
        raise ValueError(f"Copilot hook received invalid JSON: {error}") from error
    if not isinstance(payload, dict):
        raise ValueError("Copilot hook payload must be a JSON object")
    return payload


def _run(script: str, payload: dict[str, Any] | None = None) -> subprocess.CompletedProcess[str]:
    path = PLUGIN_ROOT / "scripts" / script
    if not path.is_file():
        raise FileNotFoundError(f"Hook helper does not exist: {path}")
    return subprocess.run(
        ["python3", str(path)],
        input=json.dumps(payload or {}),
        text=True,
        capture_output=True,
        check=False,
    )


def _additional_context(result: subprocess.CompletedProcess[str]) -> str:
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or f"hook helper exited {result.returncode}")
    if not result.stdout.strip():
        return ""
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError:
        return result.stdout.strip()
    context = value.get("hookSpecificOutput", {}).get("additionalContext", "")
    if not isinstance(context, str):
        raise ValueError("Parent hook returned a non-text additionalContext")
    return context


def session_start() -> None:
    result = _run("session-start.py")
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or f"session-start helper exited {result.returncode}")
    if result.stdout.strip():
        print(json.dumps({"additionalContext": result.stdout.strip()}))


def user_prompt() -> None:
    payload = _payload()
    if "prompt" not in payload and "user_prompt" in payload:
        payload["prompt"] = payload["user_prompt"]
    contexts = []
    for helper in ("feedback-capture.py", "checkpoint-tick.py"):
        context = _additional_context(_run(helper, payload))
        if context:
            contexts.append(context)
    if contexts:
        print(json.dumps({"additionalContext": "\n\n".join(contexts)}))


def pre_tool() -> None:
    payload = _payload()
    result = _run("write-gate.py", payload)
    if result.returncode == 2:
        print(json.dumps({
            "permissionDecision": "deny",
            "permissionDecisionReason": result.stderr.strip() or "Bootcamp write gate denied this operation.",
        }))
    elif result.returncode:
        raise RuntimeError(result.stderr.strip() or f"write-gate helper exited {result.returncode}")


def agent_stop() -> None:
    payload = _payload()
    if payload.get("stop_hook_active") is True:
        return
    if not (Path.cwd() / "config/bootcamp_progress.json").is_file():
        return
    preferences = Path.cwd() / "config/bootcamp_preferences.yaml"
    if preferences.is_file() and "bootcamp_complete: true" in preferences.read_text(
        encoding="utf-8", errors="replace"
    ).lower():
        return
    last_message = payload.get("last_assistant_message") or payload.get("lastAssistantMessage")
    if not isinstance(last_message, str):
        raise ValueError(
            "agentStop did not provide last_assistant_message; verify the active Copilot harness payload"
        )
    if not last_message.strip() or "👉" in last_message:
        return
    print(json.dumps({
        "decision": "block",
        "reason": (
            "A bootcamp is active. Review your last message. If it already ends with a single "
            "👉 closing question, do not repeat it. Otherwise, only when you have finished a "
            "bootcamp step and are yielding, add exactly one closing question. Add nothing "
            "mid-step or after bootcamp completion."
        ),
    }, ensure_ascii=False))


def session_end() -> None:
    result = subprocess.run(
        ["python3", str(PLUGIN_ROOT / "scripts/session-end.py")],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or f"session-end helper exited {result.returncode}")
    if result.stderr:
        sys.stderr.write(result.stderr)


def main() -> int:
    actions = {
        "session-start": session_start,
        "user-prompt": user_prompt,
        "pre-tool": pre_tool,
        "agent-stop": agent_stop,
        "session-end": session_end,
    }
    if len(sys.argv) != 2 or sys.argv[1] not in actions:
        print("Expected one of: " + ", ".join(actions), file=sys.stderr)
        return 2
    try:
        actions[sys.argv[1]]()
    except (OSError, RuntimeError, ValueError) as error:
        print(f"Copilot hook {sys.argv[1]} failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
