#!/usr/bin/env python3
"""Record content-addressed feedback outcomes without storing feedback text."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "docs/feedback-ledger.jsonl"
DECISIONS = {"parent-bound", "local"}
OUTCOMES = {"filed", "updated", "server-feedback"}


def read_entries(path: Path = LEDGER) -> list[dict[str, Any]]:
    if path.is_symlink():
        raise ValueError(f"Feedback ledger must not be a symlink: {path}")
    if not path.exists():
        return []
    entries: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        try:
            entry = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid feedback ledger JSON at line {line_number}: {error}") from error
        if not isinstance(entry, dict) or not isinstance(entry.get("sha256"), str):
            raise ValueError(f"Invalid feedback ledger entry at line {line_number}")
        entries.append(entry)
    return entries


def record(
    entry_file: Path,
    decision: str,
    destination: str,
    outcome: str,
    issue_url: str = "",
    ledger_path: Path = LEDGER,
) -> dict[str, Any]:
    if decision not in DECISIONS:
        raise ValueError(f"decision must be one of {sorted(DECISIONS)}")
    if outcome not in OUTCOMES:
        raise ValueError(f"outcome must be one of {sorted(OUTCOMES)}")
    if not destination.strip():
        raise ValueError("destination must not be empty")
    if outcome in {"filed", "updated"} and not issue_url.startswith("https://github.com/"):
        raise ValueError("filed/updated outcomes require the resulting GitHub issue URL")
    if outcome == "server-feedback" and not issue_url:
        raise ValueError("server-feedback outcome requires a reference or receipt")
    content = entry_file.read_bytes()
    if not content.strip():
        raise ValueError("feedback entry is empty")
    digest = hashlib.sha256(content.replace(b"\r\n", b"\n")).hexdigest()
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    item = {
        "sha256": digest,
        "decision": decision,
        "destination": destination,
        "outcome": outcome,
        "issue_url": issue_url,
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }
    lock_path = ledger_path.with_name(ledger_path.name + ".lock")
    try:
        lock_descriptor = os.open(
            lock_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600,
        )
    except FileExistsError as error:
        raise ValueError(
            f"Feedback ledger is locked; verify no recorder is active before removing {lock_path}"
        ) from error
    os.close(lock_descriptor)
    try:
        entries = read_entries(ledger_path)
        existing = next((entry for entry in entries if entry["sha256"] == digest), None)
        if existing:
            return {"status": "already-processed", "entry": existing}
        descriptor = os.open(
            ledger_path,
            os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0),
            0o644,
        )
        with os.fdopen(descriptor, "a", encoding="utf-8") as ledger:
            ledger.write(json.dumps(item, sort_keys=True) + "\n")
            ledger.flush()
            os.fsync(ledger.fileno())
    finally:
        lock_path.unlink(missing_ok=True)
    return {"status": "recorded", "entry": item}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="action", required=True)
    record_parser = subparsers.add_parser("record")
    record_parser.add_argument("--entry-file", type=Path, required=True)
    record_parser.add_argument("--decision", required=True, choices=sorted(DECISIONS))
    record_parser.add_argument("--destination", required=True)
    record_parser.add_argument("--outcome", required=True, choices=sorted(OUTCOMES))
    record_parser.add_argument("--issue-url", default="")
    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--ledger", type=Path, default=LEDGER)
    args = parser.parse_args()
    try:
        if args.action == "list":
            print(json.dumps(read_entries(args.ledger), indent=2))
        else:
            print(json.dumps(record(
                args.entry_file, args.decision, args.destination, args.outcome, args.issue_url,
            ), indent=2))
    except (OSError, ValueError) as error:
        print(f"Feedback ledger failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
