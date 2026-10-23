#!/usr/bin/env python3
"""Adapt the parent plugin's hook helpers to GitHub Copilot CLI hook payloads."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
WRITE_TOOLS = {"apply_patch", "create", "edit", "write", "write_file", "str_replace_editor"}


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


def _tool_calls(payload: dict[str, Any]) -> list[dict[str, Any]]:
    calls = payload.get("toolCalls")
    if isinstance(calls, list):
        if not calls or not all(isinstance(call, dict) for call in calls):
            raise ValueError("preToolUse toolCalls must be a non-empty array of objects")
        if not all(isinstance(call.get("name"), str) for call in calls):
            raise ValueError("preToolUse toolCalls must include a tool name")
        return calls
    if "toolName" in payload:
        if not isinstance(payload["toolName"], str):
            raise ValueError("preToolUse toolName must be text")
        return [{"name": payload["toolName"], "args": payload.get("toolArgs")}]
    if "tool_name" in payload:
        if not isinstance(payload["tool_name"], str):
            raise ValueError("preToolUse tool_name must be text")
        return [{"name": payload["tool_name"], "args": payload.get("tool_input")}]
    raise ValueError("preToolUse payload did not include toolCalls or a tool name")


def _write_targets(call: dict[str, Any]) -> list[str]:
    name = call.get("name")
    if isinstance(name, str):
        name = name.lower()
    args = call.get("args")
    if isinstance(args, str) and name == "apply_patch":
        prefixes = (
            "*** Add File: ",
            "*** Update File: ",
            "*** Delete File: ",
            "*** Move to: ",
        )
        return [
            line[len(prefix):].strip()
            for line in args.splitlines()
            for prefix in prefixes
            if line.startswith(prefix)
        ]
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except json.JSONDecodeError:
            return []
    if isinstance(args, dict):
        path = args.get("file_path") or args.get("filePath") or args.get("path")
        if isinstance(path, str) and path:
            return [path]
    return []


def pre_tool() -> None:
    payload = _payload()
    for call in _tool_calls(payload):
        name = call["name"]
        if name.lower() not in WRITE_TOOLS:
            continue
        targets = _write_targets(call)
        if not targets:
            raise ValueError(f"Could not determine the write target for {name}")
        for target in targets:
            result = _run("write-gate.py", {
                "tool_name": name,
                "tool_input": {"file_path": target},
            })
            if result.returncode == 2:
                print(json.dumps({
                    "permissionDecision": "deny",
                    "permissionDecisionReason": result.stderr.strip()
                    or "Bootcamp write gate denied this operation.",
                }))
                return
            if result.returncode:
                raise RuntimeError(result.stderr.strip() or f"write-gate helper exited {result.returncode}")


def _transcript_message(path: Path) -> str | None:
    records = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(event, dict):
                records.append(event)
    last_user = max(
        (index for index, event in enumerate(records) if event.get("type") == "user.message"),
        default=-1,
    )
    assistant_events = [
        event for event in records[last_user + 1:] if event.get("type") == "assistant.message"
    ]
    if not assistant_events:
        return None
    data = assistant_events[-1].get("data")
    content = data.get("content") if isinstance(data, dict) else None
    if isinstance(content, str):
        return content or None
    if isinstance(content, list):
        blocks = [block for block in content if isinstance(block, dict)]
        if blocks and blocks[-1].get("type") == "tool_use":
            return None
        text = "\n".join(
            block["text"] for block in blocks
            if block.get("type") == "text" and isinstance(block.get("text"), str)
        )
        return text or None
    return None


def _has_clean_closing_question(message: str) -> bool:
    lines = message.rstrip().splitlines()
    if sum(line.count("👉") for line in lines) != 1:
        return False
    question_line = next(index for index, line in enumerate(lines) if "👉" in line)
    trailing = lines[question_line + 1:]
    nonempty = [line for line in trailing if line.strip()]
    if not nonempty:
        return True
    if not re.match(r"^\s*(?:>\s*)?\d+\.\s+", nonempty[0]):
        return False
    return all(
        not line.strip()
        or re.match(r"^\s*(?:>\s*)?\d+\.\s+", line)
        or line.startswith(("  ", "\t", ">"))
        for line in trailing
    )


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
        transcript = payload.get("transcriptPath") or payload.get("transcript_path")
        if not isinstance(transcript, str) or not transcript:
            raise ValueError("agentStop did not provide a transcript path")
        deadline = time.monotonic() + 1
        while True:
            last_message = _transcript_message(Path(transcript))
            if last_message is not None:
                break
            if time.monotonic() >= deadline:
                raise ValueError("agentStop transcript contained no settled assistant message")
            time.sleep(0.05)
    if not isinstance(last_message, str):
        raise ValueError("agentStop transcript contained no assistant message")
    if not last_message.strip() or _has_clean_closing_question(last_message):
        return
    print(json.dumps({
        "decision": "block",
        "reason": (
            "A bootcamp is active. Review your last message. It must end with exactly one 👉 "
            "closing question, followed only by its numbered answer options if any. Remove any "
            "post-question narration; do not repeat the question. If no question is pending, only "
            "when you have finished a bootcamp step and are yielding, add its prescribed question. "
            "Add nothing mid-step or after bootcamp completion."
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
