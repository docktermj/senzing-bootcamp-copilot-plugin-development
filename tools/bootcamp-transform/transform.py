#!/usr/bin/env python3
"""Build the Copilot plugin from an exact, tagged parent release."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "tools/bootcamp-transform/contract.yaml"
VERSION_FILE = ROOT / "PARENT_VERSION"
COMMIT_FILE = ROOT / "PARENT_COMMIT"
BUILD_MANIFEST = ROOT / ".build-manifest.json"
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
SHA = re.compile(r"^[0-9a-f]{40}$")
LOCAL_PATCH_ROOT = "tools/bootcamp-transform/patches"
LOCAL_REPOSITORY = "docktermj/senzing-bootcamp-copilot-plugin-development"
PARENT_REPOSITORY = "docktermj/senzing-bootcamp-claude-plugin-development"


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


def _issue_url(value: Any, repository: str) -> bool:
    return (
        isinstance(value, str)
        and re.fullmatch(
            rf"https://github\.com/{re.escape(repository)}/issues/[1-9]\d*", value
        ) is not None
    )


def validate_local_patch_registry(
    contract: dict[str, Any], repository_root: Path | None = None
) -> list[str]:
    root = (ROOT if repository_root is None else repository_root).resolve()
    entries = contract.get("local_patches", [])
    if not isinstance(entries, list):
        return ["E_INVALID_LOCAL_PATCHES: local_patches must be a list"]

    errors: list[str] = []
    required_keys = {"id", "issue", "patch", "upstream", "reason"}
    patch_directory = root / LOCAL_PATCH_ROOT
    patch_root = patch_directory.resolve()
    patch_root_is_safe = patch_root == patch_directory
    if not patch_root_is_safe:
        errors.append("E_INVALID_LOCAL_PATCHES: patch directory must not traverse symlinks")
    referenced: list[str] = []
    identifiers: set[str] = set()

    for index, entry in enumerate(entries):
        label = f"local_patches[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"E_INVALID_LOCAL_PATCHES: {label} must be an object")
            continue
        missing = required_keys - entry.keys()
        extra = entry.keys() - required_keys
        if missing or extra:
            details = []
            if missing:
                details.append(f"missing {sorted(missing)}")
            if extra:
                details.append(f"unexpected {sorted(extra)}")
            errors.append(f"E_INVALID_LOCAL_PATCHES: {label}: {', '.join(details)}")

        patch_id = entry.get("id")
        if not isinstance(patch_id, str) or re.fullmatch(
            r"[a-z0-9]+(?:-[a-z0-9]+)*", patch_id
        ) is None:
            errors.append(f"E_INVALID_LOCAL_PATCHES: {label} has an invalid id")
        elif patch_id in identifiers:
            errors.append(f"E_PATCH_DUPLICATE_ID: {patch_id}")
        else:
            identifiers.add(patch_id)

        if not _issue_url(entry.get("issue"), LOCAL_REPOSITORY):
            errors.append(f"E_INVALID_LOCAL_PATCHES: {label} must link a local issue")

        upstream = entry.get("upstream")
        if not isinstance(upstream, dict):
            errors.append(f"E_INVALID_LOCAL_PATCHES: {label}.upstream must be an object")
        else:
            if set(upstream) - {"issue", "commit", "commits"}:
                errors.append(f"E_INVALID_LOCAL_PATCHES: {label}.upstream has unexpected fields")
            if not _issue_url(upstream.get("issue"), PARENT_REPOSITORY):
                errors.append(f"E_INVALID_LOCAL_PATCHES: {label}.upstream must link a parent issue")
            if "commit" in upstream and "commits" in upstream:
                errors.append(
                    f"E_INVALID_LOCAL_PATCHES: {label}.upstream must use commit or commits, not both"
                )
            if "commit" in upstream and (
                not isinstance(upstream["commit"], str)
                or SHA.fullmatch(upstream["commit"]) is None
            ):
                errors.append(f"E_INVALID_LOCAL_PATCHES: {label}.upstream.commit must be a full lowercase SHA")
            if "commits" in upstream:
                commits = upstream["commits"]
                if not isinstance(commits, list) or not commits:
                    errors.append(
                        f"E_INVALID_LOCAL_PATCHES: {label}.upstream.commits must be a non-empty list"
                    )
                elif any(
                    not isinstance(commit, str) or SHA.fullmatch(commit) is None
                    for commit in commits
                ):
                    errors.append(
                        f"E_INVALID_LOCAL_PATCHES: {label}.upstream.commits must contain full lowercase SHAs"
                    )
                elif len(set(commits)) != len(commits):
                    errors.append(
                        f"E_INVALID_LOCAL_PATCHES: {label}.upstream.commits must not contain duplicate SHAs"
                    )

        if not isinstance(entry.get("reason"), str) or not entry["reason"].strip():
            errors.append(f"E_INVALID_LOCAL_PATCHES: {label} must have a reason")

        patch_name = entry.get("patch")
        if not isinstance(patch_name, str):
            errors.append(f"E_PATCH_MISSING: {patch_id or label}: {patch_name}")
            continue
        relative = PurePosixPath(patch_name)
        if (
            relative.is_absolute()
            or "\\" in patch_name
            or str(relative) != patch_name
            or ".." in relative.parts
            or not patch_name.startswith(f"{LOCAL_PATCH_ROOT}/")
            or relative.suffix != ".patch"
        ):
            errors.append(f"E_INVALID_LOCAL_PATCHES: {label} has an unsafe patch path: {patch_name}")
            continue

        referenced.append(patch_name)
        candidate = root.joinpath(*relative.parts)
        resolved = candidate.resolve()
        if not patch_root_is_safe or resolved != candidate or not resolved.is_relative_to(patch_root):
            errors.append(
                f"E_INVALID_LOCAL_PATCHES: {label} patch path uses a symlink or escapes the patch directory"
            )
        elif candidate.is_symlink() or not candidate.is_file():
            errors.append(f"E_PATCH_MISSING: {patch_id or label}: {patch_name}")

    seen: set[str] = set()
    for patch_name in referenced:
        if patch_name in seen:
            errors.append(f"E_PATCH_DUPLICATE_REFERENCE: {patch_name}")
        seen.add(patch_name)

    patch_files = {
        path.relative_to(root).as_posix()
        for path in patch_directory.rglob("*.patch")
        if path.is_file() or path.is_symlink()
    } if patch_root_is_safe and patch_directory.is_dir() else set()
    for orphan in sorted(patch_files - set(referenced)):
        errors.append(f"E_PATCH_ORPHANED: {orphan}")
    return errors


def local_patch_records(
    contract: dict[str, Any], repository_root: Path | None = None
) -> list[dict[str, str]]:
    root = ROOT if repository_root is None else repository_root
    errors = validate_local_patch_registry(contract, root)
    if errors:
        raise TransformError(errors[0])
    return [
        {"id": patch["id"], "sha256": sha256(root / patch["patch"])}
        for patch in contract.get("local_patches", [])
    ]


def _patch_paths(
    patch_path: Path, source_root: Path, patch_id: str, git_env: dict[str, str]
) -> list[str]:
    result = subprocess.run(
        ["git", "apply", "--no-index", "--numstat", "-z", str(patch_path)],
        cwd=source_root,
        env=git_env,
        capture_output=True,
    )
    if result.returncode:
        detail = (result.stderr or result.stdout).decode("utf-8", errors="replace").strip()
        raise TransformError(f"E_PATCH_DOES_NOT_APPLY: {patch_id}: {detail or patch_path}")

    fields = result.stdout.split(b"\0")
    paths: list[str] = []
    index = 0
    while index < len(fields):
        record = fields[index]
        index += 1
        if not record:
            continue
        parts = record.split(b"\t", 2)
        if len(parts) != 3:
            raise TransformError(f"E_PATCH_DOES_NOT_APPLY: {patch_id}: invalid numstat output")
        encoded_paths = [parts[2]] if parts[2] else fields[index:index + 2]
        if not parts[2]:
            index += 2
        for encoded_path in encoded_paths:
            try:
                path = encoded_path.decode("utf-8")
            except UnicodeDecodeError as error:
                raise TransformError(
                    f"E_PATCH_DOES_NOT_APPLY: {patch_id}: patch path is not UTF-8"
                ) from error
            relative = PurePosixPath(path)
            if relative.is_absolute() or ".." in relative.parts or not path:
                raise TransformError(f"E_PATCH_DOES_NOT_APPLY: {patch_id}: unsafe path {path!r}")
            paths.append(path)
    if not paths:
        raise TransformError(f"E_PATCH_DOES_NOT_APPLY: {patch_id}: patch contains no file changes")
    return paths


def apply_local_patches(
    source_root: Path,
    temporary_root: Path,
    contract: dict[str, Any],
    repository_root: Path | None = None,
) -> tuple[Path, list[dict[str, str]]]:
    root = ROOT if repository_root is None else repository_root
    errors = validate_local_patch_registry(contract, root)
    if errors:
        raise TransformError(errors[0])
    entries = contract.get("local_patches", [])
    if not entries:
        return source_root, []

    original_root = temporary_root / "upstream-source"
    shutil.copytree(source_root, original_root)
    patched_root = temporary_root / "patched-source"
    shutil.copytree(original_root, patched_root)
    git_env = os.environ.copy()
    git_env["GIT_CEILING_DIRECTORIES"] = str(temporary_root)
    records: list[dict[str, str]] = []
    for entry in entries:
        patch_path = root / entry["patch"]
        paths = _patch_paths(patch_path, original_root, entry["id"], git_env)
        for path in paths:
            if any(
                rule.get("kind") == "ignore" and _matches(path, rule.get("match", []))
                for rule in contract.get("rules", [])
            ):
                raise TransformError(f"E_PATCH_IGNORED_PATH: {entry['id']}: {path}")

        reverse = subprocess.run(
            ["git", "apply", "--no-index", "--reverse", "--check", str(patch_path)],
            cwd=original_root,
            env=git_env,
            capture_output=True,
        )
        if reverse.returncode == 0:
            raise TransformError(f"E_PATCH_ALREADY_UPSTREAM: {entry['id']}: {', '.join(paths)}")

        check = subprocess.run(
            ["git", "apply", "--no-index", "--check", str(patch_path)],
            cwd=patched_root,
            env=git_env,
            capture_output=True,
        )
        if check.returncode:
            detail = (check.stderr or check.stdout).decode("utf-8", errors="replace").strip()
            raise TransformError(
                f"E_PATCH_DOES_NOT_APPLY: {entry['id']}: {', '.join(paths)}: {detail}"
            )
        applied = subprocess.run(
            ["git", "apply", "--no-index", str(patch_path)],
            cwd=patched_root,
            env=git_env,
            capture_output=True,
        )
        if applied.returncode:
            detail = (applied.stderr or applied.stdout).decode("utf-8", errors="replace").strip()
            raise TransformError(
                f"E_PATCH_DOES_NOT_APPLY: {entry['id']}: {', '.join(paths)}: {detail}"
            )
        records.append({"id": entry["id"], "sha256": sha256(patch_path)})
    return patched_root, records


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
        temporary_root = Path(temp)
        source_root, patch_records = apply_local_patches(
            upstream_root, temporary_root, contract, ROOT
        )
        stage = temporary_root / "plugin"
        generated = render(source_root, stage, contract, variables)
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
        if patch_records:
            next_manifest["local_patches"] = patch_records
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
