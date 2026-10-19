#!/usr/bin/env python3
"""Build the Copilot plugin from an exact, tagged parent release."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "tools/bootcamp-transform/contract.yaml"
VERSION_FILE = ROOT / "PARENT_VERSION"
COMMIT_FILE = ROOT / "PARENT_COMMIT"
BUILD_MANIFEST = ROOT / ".build-manifest.json"
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
SHA = re.compile(r"^[0-9a-f]{40}$")


class TransformError(RuntimeError):
    """An invalid contract, source release, or reconciliation state."""


def run(*args: str, cwd: Path | None = None) -> str:
    try:
        result = subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=True)
    except subprocess.CalledProcessError as error:
        detail = error.stderr.strip() or error.stdout.strip()
        raise TransformError(f"{' '.join(args)} failed: {detail}") from error
    return result.stdout.strip()


def load_json_yaml(path: Path) -> dict[str, Any]:
    text = "\n".join(line for line in path.read_text(encoding="utf-8").splitlines()
                     if not line.lstrip().startswith("#"))
    try:
        value = json.loads(text)
    except json.JSONDecodeError as error:
        raise TransformError(f"E_INVALID_CONTRACT: {path}: {error}") from error
    if not isinstance(value, dict):
        raise TransformError(f"E_INVALID_CONTRACT: {path} must contain an object")
    return value


def _matches(relative: str, patterns: str | list[str]) -> bool:
    items = [patterns] if isinstance(patterns, str) else patterns
    return any(fnmatch.fnmatchcase(relative, pattern) for pattern in items)


def plan_files(source_root: Path, contract: dict[str, Any]) -> list[tuple[Path, dict[str, Any]]]:
    plan: list[tuple[Path, dict[str, Any]]] = []
    for source in sorted(path for path in source_root.rglob("*") if path.is_file()):
        relative = source.relative_to(source_root).as_posix()
        matches = [rule for rule in contract["rules"] if _matches(relative, rule["match"])]
        if not matches:
            raise TransformError(f"E_UNMATCHED_FILE: {relative}")
        if len(matches) != 1:
            ids = ", ".join(str(rule.get("id", "<unnamed>")) for rule in matches)
            raise TransformError(f"E_AMBIGUOUS_FILE: {relative}: {ids}")
        plan.append((source.relative_to(source_root), matches[0]))
    return plan


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def file_hashes(root: Path) -> dict[str, str]:
    if not root.exists():
        return {}
    return {
        path.relative_to(root).as_posix(): sha256(path)
        for path in sorted(root.rglob("*")) if path.is_file()
    }


def _expand(value: Any, variables: dict[str, str]) -> Any:
    if isinstance(value, str):
        for name, replacement in variables.items():
            value = value.replace(f"${{{name}}}", replacement)
        return value
    if isinstance(value, list):
        return [_expand(item, variables) for item in value]
    if isinstance(value, dict):
        return {key: _expand(item, variables) for key, item in value.items()}
    return value


def _substitute(path: Path, contract: dict[str, Any]) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return
    original = text
    for operation in contract.get("substitutions", []):
        text = text.replace(operation["old"], operation["new"])
    if text != original:
        path.write_text(text, encoding="utf-8")


def _copy_generated_artifacts(
    staging: Path, contract: dict[str, Any], variables: dict[str, str]
) -> None:
    for artifact in contract.get("generated_artifacts", []):
        destination = staging / artifact["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        if "source" in artifact:
            source = ROOT / artifact["source"]
            if not source.is_file():
                raise TransformError(f"E_MISSING_ARTIFACT_SOURCE: {artifact['source']}")
            shutil.copy2(source, destination)
        elif artifact.get("format") == "json":
            destination.write_text(
                json.dumps(_expand(artifact["value"], variables), indent=2) + "\n",
                encoding="utf-8",
            )
        else:
            raise TransformError(f"E_INVALID_CONTRACT: unsupported generated artifact {artifact}")


def render(
    source_root: Path, staging: Path, contract: dict[str, Any], variables: dict[str, str]
) -> dict[str, str]:
    plan = plan_files(source_root, contract)
    staging.mkdir(parents=True)
    for relative, rule in plan:
        if rule["kind"] == "ignore":
            continue
        if rule["kind"] != "copy":
            raise TransformError(f"E_INVALID_CONTRACT: unsupported rule kind {rule['kind']!r}")
        target = staging / rule.get("destination", relative.as_posix())
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_root / relative, target)

    for path in sorted(file for file in staging.rglob("*") if file.is_file()):
        _substitute(path, contract)
    _copy_generated_artifacts(staging, contract, variables)
    return file_hashes(staging)


def validate_manifest(manifest_path: Path, version: str, expected_ids: set[str]) -> None:
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        entries = manifest["invariants"]
        actual_ids = {entry["id"] for entry in entries}
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as error:
        raise TransformError(f"E_INVALID_INVARIANT_MANIFEST: {manifest_path}: {error}") from error
    if (not entries or len(actual_ids) != len(entries)
            or manifest.get("count") != len(entries)):
        raise TransformError("E_INVALID_INVARIANT_MANIFEST: invariant IDs must be nonempty and unique")
    if actual_ids != expected_ids:
        missing = sorted(expected_ids - actual_ids)
        extra = sorted(actual_ids - expected_ids)
        raise TransformError(
            f"E_INVARIANT_REGISTER: manifest mismatch for {version}; missing={missing}, extra={extra}"
        )
    for entry in entries:
        if not re.fullmatch(r"INV-\d{3}", entry["id"]) or not entry.get("statement"):
            raise TransformError(f"E_INVALID_INVARIANT_MANIFEST: malformed entry {entry!r}")


def check_dispositions(contract: dict[str, Any], manifest_path: Path, version: str) -> None:
    register = contract.get("invariant_disposition_register", {})
    if register.get("source_version") != version:
        raise TransformError(
            "E_INVARIANT_REVIEW: parent version changed; review both invariant registers before building"
        )
    if register.get("source_commit") != COMMIT_FILE.read_text(encoding="utf-8").strip():
        raise TransformError("E_INVARIANT_REVIEW: disposition source commit differs from PARENT_COMMIT")
    source = json.loads(manifest_path.read_text(encoding="utf-8"))
    ids = {item["id"] for item in source["invariants"]}
    restated = [item.get("id") for item in register.get("preserved_restated", [])]
    discounted = [item.get("id") for item in register.get("discounted", [])]
    if len(restated) != len(set(restated)) or len(discounted) != len(set(discounted)):
        raise TransformError("E_INVARIANT_REGISTER: disposition IDs must be unique")
    if set(restated) & set(discounted):
        raise TransformError("E_INVARIANT_REGISTER: an invariant has multiple dispositions")
    if not set(restated + discounted) <= ids:
        raise TransformError(f"E_INVARIANT_REGISTER: unknown invariant IDs {set(restated + discounted) - ids}")
    for item in register.get("preserved_restated", []):
        if not item.get("mechanism"):
            raise TransformError(f"E_INVARIANT_REGISTER: {item.get('id')} has no mechanism")
    for item in register.get("discounted", []):
        if not item.get("conflictsWith") or not item.get("resolution"):
            raise TransformError(f"E_INVARIANT_REGISTER: {item.get('id')} needs a conflict and resolution")
    if register.get("honored") != (
        "all parent INV-NNN identifiers except those explicitly preserved_restated or discounted"
    ):
        raise TransformError("E_INVARIANT_REGISTER: inherited invariant disposition is not exhaustive")
    validate_manifest(manifest_path, version, ids)


def _previous_manifest() -> dict[str, Any]:
    if not BUILD_MANIFEST.is_file():
        return {"files": {}}
    try:
        value = json.loads(BUILD_MANIFEST.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise TransformError(f"E_INVALID_BUILD_MANIFEST: {error}") from error
    if not isinstance(value.get("files"), dict):
        raise TransformError("E_INVALID_BUILD_MANIFEST: files must be an object")
    return value


def reconcile(
    old: dict[str, Any], current: dict[str, str], generated: dict[str, str]
) -> list[tuple[str, str]]:
    report: list[tuple[str, str]] = []
    old_files = old.get("files", {})
    for name in sorted(set(old_files) | set(current) | set(generated)):
        previous = old_files.get(name, {})
        prior_generated = previous.get("generated")
        prior_output = previous.get("output")
        fresh = generated.get(name)
        live = current.get(name)
        parent_changed = prior_generated is not None and fresh != prior_generated
        local_changed = name in old_files and live != prior_output
        collision = name not in old_files and live is not None and fresh is not None and live != fresh
        if (parent_changed and local_changed) or collision:
            state = "conflict"
        elif name not in old_files and fresh is not None:
            state = "added"
        elif fresh is None and prior_generated is not None:
            state = "conflict" if local_changed else "removed"
        elif local_changed or (name not in old_files and live is not None):
            state = "preserved"
        elif parent_changed:
            state = "modified"
        else:
            continue
        report.append((state, name))
    return report


def _clone_tag(repository: str, tag: str, destination: Path) -> Path:
    run("git", "clone", "--quiet", "--depth", "1", "--branch", tag, repository, str(destination))
    return destination


def _source_commit(source: Path) -> str:
    return run("git", "rev-parse", "HEAD", cwd=source)


def _ensure_pinned_source(source: Path, version: str, commit: str, contract: dict[str, Any]) -> Path:
    source_root = source / contract["upstream"]["source_root"]
    version_path = source_root / contract["upstream"]["version_file"]
    try:
        source_version = json.loads(version_path.read_text(encoding="utf-8"))["version"]
    except (OSError, KeyError, json.JSONDecodeError) as error:
        raise TransformError(f"E_INVALID_SOURCE_MANIFEST: {version_path}: {error}") from error
    if source_version != version:
        raise TransformError(f"E_TAG_MISMATCH: requested {version}, parent manifest says {source_version}")
    actual_commit = _source_commit(source)
    if actual_commit != commit:
        raise TransformError(f"E_COMMIT_MISMATCH: expected {commit}, got {actual_commit}")
    return source_root


def _write_output(target: Path, staging: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    backup = target.with_name(f".{target.name}.previous")
    if backup.exists():
        raise TransformError(f"E_STALE_BACKUP: remove or inspect {backup} before building")
    had_target = target.exists()
    if had_target:
        target.rename(backup)
    try:
        staging.rename(target)
    except OSError:
        if had_target:
            backup.rename(target)
        raise
    if had_target:
        shutil.rmtree(backup)


def build(
    tag: str,
    source: Path,
    manifest_path: Path,
    contract_path: Path = CONTRACT,
) -> None:
    if not SEMVER.fullmatch(tag):
        raise TransformError("--tag must be an exact stable SemVer tag, for example 0.6.1")
    version = VERSION_FILE.read_text(encoding="utf-8").strip()
    commit = COMMIT_FILE.read_text(encoding="utf-8").strip()
    if not SEMVER.fullmatch(version) or not SHA.fullmatch(commit):
        raise TransformError("PARENT_VERSION must be stable SemVer and PARENT_COMMIT a full lowercase SHA")
    if tag != version:
        raise TransformError(f"E_UNPINNED_TAG: requested {tag}; this checkout pins {version}")
    contract = load_json_yaml(contract_path)
    upstream_root = _ensure_pinned_source(source, version, commit, contract)
    check_dispositions(contract, manifest_path, version)
    release_version = (ROOT / "RELEASE_VERSION").read_text(encoding="utf-8").strip()
    if not SEMVER.fullmatch(release_version):
        raise TransformError("RELEASE_VERSION must be stable SemVer")
    variables = {"PARENT_VERSION": version, "PARENT_COMMIT": commit, "RELEASE_VERSION": release_version}
    target = ROOT / contract["output_root"]
    target.parent.mkdir(parents=True, exist_ok=True)
    previous = _previous_manifest()
    current = file_hashes(target)

    with tempfile.TemporaryDirectory(prefix="copilot-port-", dir=target.parent) as temp:
        stage = Path(temp) / "plugin"
        generated = render(upstream_root, stage, contract, variables)
        report = reconcile(previous, current, generated)
        print("Reconciliation report (before write):")
        for status, path in report:
            print(f"- {status}: {path}")
        if not report:
            print("- unchanged")
        conflicts = [path for status, path in report if status == "conflict"]
        if conflicts:
            raise TransformError(
                "E_RECONCILIATION_CONFLICT: no files were written; resolve these paths: "
                + ", ".join(conflicts)
            )

        if target.exists():
            for name, live_hash in current.items():
                if name not in generated:
                    destination = stage / name
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(target / name, destination)
                elif name in previous.get("files", {}) and live_hash != previous["files"][name].get("output"):
                    destination = stage / name
                    if target.joinpath(name).is_file():
                        shutil.copy2(target / name, destination)
            for name, old_file in previous.get("files", {}).items():
                if name in generated and name not in current and old_file.get("output") is not None:
                    (stage / name).unlink(missing_ok=True)
        output_hashes = file_hashes(stage)
        next_manifest = {
            "schema_version": 1,
            "parent_version": version,
            "parent_commit": commit,
            "release_version": release_version,
            "files": {
                name: {"generated": generated.get(name), "output": output_hashes.get(name)}
                for name in sorted(set(generated) | set(output_hashes))
            },
        }
        _write_output(target, stage)
        BUILD_MANIFEST.write_text(json.dumps(next_manifest, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True, help="exact parent SemVer tag; must equal PARENT_VERSION")
    parser.add_argument("--source-dir", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--invariants-file", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        if bool(args.source_dir) != bool(args.invariants_file):
            raise TransformError("--source-dir and --invariants-file must be supplied together")
        if args.source_dir:
            source = args.source_dir.resolve()
            invariant_file = args.invariants_file.resolve()
            build(args.tag, source, invariant_file)
        else:
            contract = load_json_yaml(CONTRACT)
            with tempfile.TemporaryDirectory(prefix="copilot-parent-") as temp:
                work = Path(temp)
                source = _clone_tag(contract["upstream"]["repository"], args.tag, work / "source")
                dev = _clone_tag(
                    contract["invariant_manifest"]["repository"], args.tag, work / "parent-development"
                )
                build(args.tag, source, dev / contract["invariant_manifest"]["path"])
    except TransformError as error:
        print(error, file=sys.stderr)
        return 1
    except OSError as error:
        print(f"E_IO: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
