#!/usr/bin/env python3
"""Read-only report of the public quick-start page against the payload being propagated."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUBLIC_SLUG = "Senzing/senzing-bootcamp-copilot-plugin"
PAGE = "docs/index.html"
LOCAL_PAGE = "site/index.html"
PUBLIC_MARKETPLACE = "senzing-bootcamp"
CATALOG = ".github/plugin/marketplace.json"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _plain(fragment: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", fragment)).split())


def client_status(page: str) -> str:
    match = re.search(r'<p class="callout"><strong>(.*?)</p>', page, re.S)
    return _plain(match.group(1)) if match else "not found"


def record_status(record: Path) -> str:
    if not record.is_file():
        return "test record not found"
    match = re.search(r"(?ms)^\*\*Status:\*\*\s*(.*?)(?=^\*\*|\Z)", _text(record))
    return _plain(match.group(1)) if match else "status line not found"


def check(public: Path, payload: Path, record: Path) -> dict:
    catalog = public / CATALOG
    marketplace = json.loads(_text(catalog))["name"] if catalog.is_file() else PUBLIC_MARKETPLACE
    return check_page(public / PAGE, marketplace, payload, record)


def check_page(page_path: Path, marketplace: str, payload: Path, record: Path) -> dict:
    if not page_path.is_file():
        return {"page": "not found", "facts": [], "status": None}
    page = _text(page_path)
    manifest = json.loads(_text(payload / "plugin.json"))
    identifier = f"{manifest['name']}@{marketplace}"
    versions = sorted(set(re.findall(r"version\s+(\d+\.\d+\.\d+)", page)))
    facts = [
        ("version", ", ".join(versions) or "absent", manifest["version"],
         versions == [manifest["version"]]),
        ("plugin identifier", identifier if identifier in page else "absent", identifier,
         identifier in page),
        ("marketplace add command", "present" if f"marketplace add {PUBLIC_SLUG}" in page
         else "absent", f"marketplace add {PUBLIC_SLUG}", f"marketplace add {PUBLIC_SLUG}" in page),
        ("install command", "present" if f"plugin install {identifier}" in page else "absent",
         f"plugin install {identifier}", f"plugin install {identifier}" in page),
    ]
    return {
        "page": "found",
        "facts": [
            {"fact": name, "page": found, "payload": expected, "match": matched}
            for name, found, expected, matched in facts
        ],
        "status": {"page": client_status(page), "record": record_status(record)},
    }


def render(result: dict, location: str = PAGE) -> str:
    if result["page"] == "not found":
        return f"Quick-start page not found at {location}; nothing to compare."
    lines = ["| Fact | Public page | Payload | Result |", "|---|---|---|---|"]
    for item in result["facts"]:
        lines.append(
            f"| {item['fact']} | {item['page']} | {item['payload']} | "
            f"{'match' if item['match'] else 'MISMATCH'} |"
        )
    status = result["status"]
    lines += [
        "",
        "Client status text (human review; not compared):",
        f"- Public page: {status['page']}",
        f"- Test record: {status['record']}",
    ]
    mismatches = sum(not item["match"] for item in result["facts"])
    lines.append(f"\n{mismatches} mismatch(es); informational, propagation is not blocked.")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--public", type=Path, help="explicit public checkout")
    mode.add_argument("--local", action="store_true", help=f"check {LOCAL_PAGE} in this repository")
    parser.add_argument("--payload", type=Path, default=ROOT / "plugins/senzing-bootcamp")
    parser.add_argument("--record-dir", type=Path, default=ROOT / "docs/test-records")
    arguments = parser.parse_args()
    version = _text(ROOT / "RELEASE_VERSION").strip()
    record = arguments.record_dir / f"{version}.md"
    if arguments.local:
        result = check_page(ROOT / LOCAL_PAGE, PUBLIC_MARKETPLACE, arguments.payload, record)
        print(render(result, LOCAL_PAGE))
        return 1 if result["page"] == "not found" or not all(i["match"] for i in result["facts"]) else 0
    if not (arguments.public / CATALOG).is_file():
        print(f"Blocked: {arguments.public} is not a public checkout", file=sys.stderr)
        return 2
    print(render(check(arguments.public, arguments.payload, record)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
