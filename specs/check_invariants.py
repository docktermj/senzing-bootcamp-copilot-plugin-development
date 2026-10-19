#!/usr/bin/env python3
"""Lint the Copilot-native invariant register and its subject index."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "specs/INVARIANTS.md"
text = LEDGER.read_text(encoding="utf-8")
definitions = re.findall(r"(?m)^- \*\*CPINV-(\d{3})\*\* — (.+)$", text)
errors: list[str] = []
numbers = [int(number) for number, _ in definitions]
if numbers != list(range(1, len(numbers) + 1)):
    errors.append("CPINV definitions must be unique, sequential, and append-only")
for number, statement in definitions:
    if " MUST " not in f" {statement} " and " ALWAYS " not in f" {statement} ":
        errors.append(f"CPINV-{number} must be phrased as one testable MUST/ALWAYS")

index = re.search(r"(?ms)^## Index by subject\n(.*?)(?=^## |\Z)", text)
indexed = re.findall(r"CPINV-(\d{3})", index.group(1)) if index else []
if sorted(indexed) != [f"{number:03d}" for number in numbers] or len(indexed) != len(set(indexed)):
    errors.append("each CPINV must appear exactly once in the subject index")

superseded = re.findall(r"(?m)^- \*\*Superseded by:\*\* CPINV-(\d{3}) — .+$", text)
supersedes = re.findall(r"(?m)^- \*\*Supersedes:\*\* CPINV-(\d{3})$", text)
all_supersession_mentions = re.findall(r"(?m)^- \*\*Superseded by:\*\* CPINV-\d{3} — .+$|^- \*\*Supersedes:\*\* CPINV-\d{3}$", text)
if len(all_supersession_mentions) != len(superseded) + len(supersedes):
    errors.append("supersession markers must use only the exact two-bullet R12 syntax")
if bool(superseded) != bool(supersedes) or len(superseded) != len(supersedes):
    errors.append("each supersession requires both R12 bullets")
if errors:
    print("Invariant register failed:")
    for error in errors:
        print(f"- {error}")
    raise SystemExit(1)
print(f"Copilot invariant register passed ({len(definitions)} active CPINV identifiers)")
