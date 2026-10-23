#!/usr/bin/env python3
"""Run static release checks against the generated GitHub Copilot plugin."""

from __future__ import annotations

import ast
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

import transform

ROOT = Path(__file__).resolve().parents[2]
PLUGIN = ROOT / "plugins/senzing-bootcamp"
CONTRACT = ROOT / "tools/bootcamp-transform/contract.yaml"
errors: list[str] = []
REQUIRED_OPERATIONS = {
    "parity-check",
    "escalate-to-parent",
    "feedback-to-issues",
    "implement-github-issue",
    "retrofit-from-public",
    "production-readiness-audit",
    "dry-run",
    "release",
    "propagate-to-public",
}


def read_json(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"{label} is missing or invalid: {error}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{label} must contain a JSON object")
        return {}
    return value


def check_operation_skills() -> None:
    found: set[str] = set()
    skills_root = ROOT / ".github/skills"
    for skill_file in sorted(skills_root.glob("*/SKILL.md")):
        text = skill_file.read_text(encoding="utf-8")
        frontmatter = re.match(r"\A---\n(.*?)\n---(?:\n|$)", text, re.S)
        name = re.search(r"(?m)^name:\s*([a-z0-9-]+)\s*$", frontmatter.group(1)) if frontmatter else None
        if not name:
            errors.append(f"{skill_file.relative_to(ROOT)} has no valid skill name")
            continue
        skill_name = name.group(1)
        if skill_name != skill_file.parent.name:
            errors.append(f"{skill_file.relative_to(ROOT)} name does not match its directory")
        if skill_name in found:
            errors.append(f"duplicate maintainer operation: {skill_name}")
        found.add(skill_name)
    missing = REQUIRED_OPERATIONS - found
    extra = found - REQUIRED_OPERATIONS
    if missing:
        errors.append(f"missing canonical maintainer operations: {sorted(missing)}")
    if extra:
        errors.append(f"unregistered maintainer operations: {sorted(extra)}")
    boundary_check = subprocess.run(
        [sys.executable, str(ROOT / "tools/bootcamp-transform/check_operations.py")],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if boundary_check.returncode:
        errors.append(boundary_check.stdout.strip() or boundary_check.stderr.strip())


def check_internal_markdown_links() -> None:
    link_pattern = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
    for markdown in PLUGIN.rglob("*.md"):
        text = markdown.read_text(encoding="utf-8", errors="replace")
        for raw_target in link_pattern.findall(text):
            target = raw_target.split(maxsplit=1)[0].strip("<>")
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or target.startswith("#") or target.startswith("${"):
                continue
            path = unquote(parsed.path)
            if (not path or path.startswith("/")
                    or not path.startswith(("./", "../"))
                    or "…" in path or "..." in path or "<" in path or "{" in path):
                continue
            resolved = (markdown.parent / path).resolve()
            if not resolved.is_file() and not resolved.is_dir():
                errors.append(
                    f"broken relative link in {markdown.relative_to(PLUGIN)}: {raw_target}"
                )


def check_python_sources() -> None:
    script_root = PLUGIN / "scripts"
    for script in sorted(script_root.glob("*.py")):
        try:
            tree = ast.parse(script.read_text(encoding="utf-8"), filename=str(script))
        except (OSError, SyntaxError) as error:
            errors.append(f"invalid Python source {script.relative_to(PLUGIN)}: {error}")
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.level:
                errors.append(
                    f"relative Python import is not supported in bundled script {script.relative_to(PLUGIN)}"
                )


def check() -> None:
    if not PLUGIN.is_dir():
        errors.append("generated plugin directory is missing")
        return
    try:
        contract = transform.load_json_yaml(CONTRACT)
    except transform.TransformError as error:
        errors.append(f"transformation contract is invalid: {error}")
        contract = {}
    plugin_manifest = read_json(PLUGIN / "plugin.json", "plugin manifest")
    release_version = (ROOT / "RELEASE_VERSION").read_text(encoding="utf-8").strip()
    parent_version = (ROOT / "PARENT_VERSION").read_text(encoding="utf-8").strip()
    parent_commit = (ROOT / "PARENT_COMMIT").read_text(encoding="utf-8").strip()
    if plugin_manifest.get("$schema") != "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json":
        errors.append("plugin manifest does not declare Agent Plugins 1.0")
    if plugin_manifest.get("name") != "senzing-bootcamp":
        errors.append("plugin manifest name must be senzing-bootcamp")
    if plugin_manifest.get("version") != release_version:
        errors.append("plugin manifest version differs from RELEASE_VERSION")

    mcp = read_json(PLUGIN / "mcp.json", "plugin MCP configuration")
    if mcp.get("$schema") != "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json":
        errors.append("plugin mcp.json does not declare the Agent Plugins 1.0 MCP schema")
    servers = mcp.get("mcpServers")
    if not isinstance(servers, dict) or "senzing" not in servers:
        errors.append("plugin mcp.json must define the Senzing server")
    else:
        senzing_server = servers["senzing"]
        if not isinstance(senzing_server, dict) or senzing_server.get("type") != "streamable-http":
            errors.append("plugin Senzing MCP server must use the streamable-http transport")

    hook_file = PLUGIN / "com.github.copilot/hooks/hooks.json"
    hooks_document = read_json(hook_file, "Copilot hooks")
    hooks = hooks_document.get("hooks")
    if hooks_document.get("version") != 1 or not isinstance(hooks, dict):
        errors.append("Copilot hooks must use version 1 and an event map")
        hooks = {}
    supported = {"sessionStart", "sessionEnd", "userPromptSubmitted", "preToolUse", "Stop"}
    if set(hooks) - supported:
        errors.append(f"unsupported Copilot hook events: {sorted(set(hooks) - supported)}")
    for event, entries in hooks.items():
        if not isinstance(entries, list) or not entries:
            errors.append(f"Copilot hook {event} must declare at least one handler")
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                errors.append(f"{event} handler must be an object")
                continue
            command = entry.get("command")
            if (
                entry.get("type") != "command"
                or not isinstance(command, str)
                or "${PLUGIN_ROOT}" not in command
                or entry.get("cwd") != "."
            ):
                errors.append(f"{event} handler must be rooted at PLUGIN_ROOT and run from the project root")
                continue
            script = re.search(r'\$\{PLUGIN_ROOT\}/([^"\s]+)', command)
            if not script or not (PLUGIN / script.group(1)).is_file():
                errors.append(f"{event} references a missing bundled script: {command}")

    residuals = re.compile(r"claude|\.claude|CLAUDE_PLUGIN_ROOT", re.I)
    for path in PLUGIN.rglob("*"):
        if not path.is_file() or path.suffix not in {".md", ".json", ".py", ".yaml", ".yml"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if residuals.search(text):
            errors.append(f"residual parent-host reference in {path.relative_to(PLUGIN)}")

    check_internal_markdown_links()
    check_python_sources()
    check_operation_skills()
    invariant_result = subprocess.run(
        [sys.executable, str(ROOT / "specs/check_invariants.py")],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if invariant_result.returncode:
        errors.append(invariant_result.stdout.strip() or invariant_result.stderr.strip())

    manifest = read_json(ROOT / ".build-manifest.json", "build manifest")
    if manifest.get("parent_version") != parent_version or manifest.get("parent_commit") != parent_commit:
        errors.append("build manifest does not match the pinned parent provenance")
    if manifest.get("release_version") != release_version:
        errors.append("build manifest release_version differs from RELEASE_VERSION")
    files = manifest.get("files", {})
    actual_files = {
        path.relative_to(PLUGIN).as_posix(): path
        for path in PLUGIN.rglob("*") if path.is_file()
    }
    if set(files) != set(actual_files):
        errors.append("build manifest file list differs from generated plugin contents")
    for name, path in actual_files.items():
        record = files.get(name, {})
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if record.get("output") != digest:
            errors.append(f"build manifest output hash is stale for {name}")
        if record.get("generated") != digest:
            errors.append(f"generated file was edited outside the transformation contract: {name}")

    if not (PLUGIN / "docs/copilot-interaction-contract.md").is_file():
        errors.append("Copilot interaction contract is missing")
    if not (PLUGIN / "docs/copilot-host-mechanisms.md").is_file():
        errors.append("Copilot host-mechanism findings are missing")
    if not isinstance(contract.get("invariant_disposition_register"), dict):
        errors.append("contract invariant disposition register is missing")


if __name__ == "__main__":
    check()
    if errors:
        print("Port checks failed:")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)
    print(f"Port checks passed for parent {ROOT.joinpath('PARENT_VERSION').read_text().strip()}")
