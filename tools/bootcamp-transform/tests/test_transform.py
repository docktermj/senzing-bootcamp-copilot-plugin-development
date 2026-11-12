from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import transform


class TransformTests(unittest.TestCase):
    def test_exactly_one_file_rule_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp)
            (source / "nested").mkdir()
            (source / "nested/kept.md").write_text("content")
            rules = [
                {"id": "keep", "kind": "copy", "match": ["**/*.md"]},
                {"id": "exclude", "kind": "ignore", "match": ["*.md"]},
            ]
            with self.assertRaisesRegex(transform.TransformError, "E_AMBIGUOUS_FILE"):
                transform.plan_files(source, {"rules": rules})

    def test_unmatched_file_fails_with_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp)
            (source / "new-parent-file.txt").write_text("content")
            with self.assertRaisesRegex(transform.TransformError, "new-parent-file.txt"):
                transform.plan_files(source, {"rules": []})

    def test_reconciliation_reports_all_change_categories(self) -> None:
        old = {
            "files": {
                "edited.md": {"generated": "old", "output": "old"},
                "removed.md": {"generated": "gone", "output": "gone"},
                "modified.md": {"generated": "old", "output": "old"},
                "preserved.md": {"generated": "same", "output": "before"},
            }
        }
        current = {
            "edited.md": "edited",
            "removed.md": "gone",
            "modified.md": "old",
            "preserved.md": "local",
            "local-only.md": "local",
        }
        generated = {
            "edited.md": "new",
            "added.md": "added",
            "modified.md": "new",
            "preserved.md": "same",
        }
        report = {path: status for status, path in transform.reconcile(old, current, generated)}
        self.assertEqual(report["edited.md"], "conflict")
        self.assertEqual(report["removed.md"], "removed")
        self.assertEqual(report["modified.md"], "modified")
        self.assertEqual(report["preserved.md"], "preserved")
        self.assertEqual(report["added.md"], "added")
        self.assertEqual(report["local-only.md"], "preserved")

    def test_added_path_collision_is_a_conflict(self) -> None:
        report = transform.reconcile(
            {"files": {}},
            {"new.md": "hand-edited"},
            {"new.md": "generated"},
        )
        self.assertEqual(report, [("conflict", "new.md")])

    def test_only_exact_stable_semver_is_accepted(self) -> None:
        for invalid in ("main", "HEAD", "v0.6.1", "0.6", "0.6.1-rc.1"):
            with self.subTest(invalid=invalid), self.assertRaises(transform.TransformError):
                transform.build(invalid, Path("."), Path("missing"))


class LocalPatchTests(unittest.TestCase):
    local_issue = "https://github.com/docktermj/senzing-bootcamp-copilot-plugin-development/issues/57"
    parent_issue = "https://github.com/docktermj/senzing-bootcamp-claude-plugin-development/issues/881"
    commit = "a" * 40

    def _entry(self, patch_name: str = "sample.patch", patch_id: str = "sample-patch") -> dict:
        return {
            "id": patch_id,
            "issue": self.local_issue,
            "patch": f"{transform.LOCAL_PATCH_ROOT}/{patch_name}",
            "upstream": {"issue": self.parent_issue, "commit": self.commit},
            "reason": "Backport the confirmed parent fix until a stable parent tag includes it.",
        }

    @staticmethod
    def _replace_patch(path: str, old: str, new: str) -> str:
        return (
            f"diff --git a/{path} b/{path}\n"
            f"--- a/{path}\n"
            f"+++ b/{path}\n"
            "@@ -1 +1 @@\n"
            f"-{old}\n"
            f"+{new}\n"
        )

    def _fixture(self, repository_root: Path, source_root: Path, patch_text: str) -> tuple[dict, Path]:
        patch_path = repository_root / transform.LOCAL_PATCH_ROOT / "sample.patch"
        patch_path.parent.mkdir(parents=True)
        patch_path.write_text(patch_text, encoding="utf-8")
        (source_root / ".claude-plugin").mkdir(parents=True)
        (source_root / ".claude-plugin/plugin.json").write_text(
            '{"version":"0.6.1"}\n', encoding="utf-8"
        )
        return {
            "upstream": {
                "source_root": ".",
                "version_file": ".claude-plugin/plugin.json",
            },
            "output_root": "plugins/senzing-bootcamp",
            "rules": [
                {"id": "copy-skills", "kind": "copy", "match": ["skills/**"]},
                {"id": "ignore-manifest", "kind": "ignore", "match": [".claude-plugin/**"]},
            ],
            "local_patches": [self._entry()],
            "substitutions": [],
            "generated_artifacts": [],
        }, patch_path

    def _run_build(self, root: Path, source: Path, contract: dict, contract_path: Path) -> None:
        commit_file = root / "PARENT_COMMIT"
        with (
            mock.patch.multiple(
                transform,
                ROOT=root,
                VERSION_FILE=root / "PARENT_VERSION",
                COMMIT_FILE=commit_file,
                BUILD_MANIFEST=root / ".build-manifest.json",
            ),
            mock.patch.object(transform, "_source_commit", return_value=self.commit),
            mock.patch.object(transform, "check_dispositions"),
        ):
            transform.build("0.6.1", source, root / "parent-invariants.json", contract_path)

    def test_patch_registry_rejects_missing_or_orphaned_patch_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            contract = {"local_patches": [self._entry()]}
            errors = transform.validate_local_patch_registry(contract, root)
            self.assertTrue(any(error.startswith("E_PATCH_MISSING") for error in errors))

            patch_path = root / transform.LOCAL_PATCH_ROOT / "orphan.patch"
            patch_path.parent.mkdir(parents=True)
            patch_path.write_text("not a registered patch", encoding="utf-8")
            errors = transform.validate_local_patch_registry({"local_patches": []}, root)
            self.assertTrue(any(error.startswith("E_PATCH_ORPHANED") for error in errors))

    def test_patch_registry_rejects_symlinked_patch_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            outside = Path(temp) / "outside"
            outside.mkdir()
            (outside / "sample.patch").write_text("patch", encoding="utf-8")
            patch_directory = root / transform.LOCAL_PATCH_ROOT
            patch_directory.parent.mkdir(parents=True)
            patch_directory.symlink_to(outside, target_is_directory=True)

            errors = transform.validate_local_patch_registry(
                {"local_patches": [self._entry()]}, root
            )

            self.assertTrue(
                any("patch directory must not traverse symlinks" in error for error in errors)
            )

    def test_patch_registry_rejects_duplicate_references_and_invalid_issue_links(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            patch_path = root / transform.LOCAL_PATCH_ROOT / "sample.patch"
            patch_path.parent.mkdir(parents=True)
            patch_path.write_text("patch", encoding="utf-8")
            first = self._entry()
            second = self._entry(patch_id="second-patch")
            second["issue"] = "https://example.com/issues/57"
            contract = {"local_patches": [first, second]}
            errors = transform.validate_local_patch_registry(contract, root)
            self.assertTrue(any(error.startswith("E_PATCH_DUPLICATE_REFERENCE") for error in errors))
            self.assertTrue(any("must link a local issue" in error for error in errors))

    def test_local_patch_applies_before_substitutions_and_is_manifested(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            source = Path(temp) / "source"
            source.mkdir()
            (source / "skills").mkdir()
            (source / "skills/guide.md").write_text("old Claude\n", encoding="utf-8")
            contract, patch_path = self._fixture(
                root, source, self._replace_patch("skills/guide.md", "old Claude", "new Claude")
            )
            contract["substitutions"] = [{"old": "Claude", "new": "Copilot"}]
            with tempfile.TemporaryDirectory() as scratch:
                patched, records = transform.apply_local_patches(
                    source, Path(scratch), contract, root
                )
                output = Path(scratch) / "plugin"
                hashes = transform.render(patched, output, contract, {})
                self.assertIn("skills/guide.md", hashes)
                self.assertEqual(
                    (output / "skills/guide.md").read_text(encoding="utf-8"),
                    "new Copilot\n",
                )
            self.assertEqual(
                records,
                [{"id": "sample-patch", "sha256": hashlib.sha256(patch_path.read_bytes()).hexdigest()}],
            )

    def test_registered_routes_patch_preserves_pinned_count_after_render(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            source = Path(temp) / "source"
            source.mkdir()
            target = source / "skills/module-05-data-quality-mapping/phase2-data-mapping.md"
            target.parent.mkdir(parents=True)
            target.write_text(
                "**One mechanism, three known reachings — recognize the fourth on sight rather than filing it as a\n"
                "discovery.** `sz_verbatim_check.py` harvests the allowed set from source **values**, and every\n"
                "entry in this block is that one scope limit reached by a different route:\n"
                "\n"
                "| The emitted value is derived from… | Where it is documented here |\n"
                "|---|---|\n"
                "| row 1 |\n"
                "| row 2 |\n"
                "| row 3 |\n",
                encoding="utf-8",
            )
            patch_text = (
                transform.ROOT
                / "tools/bootcamp-transform/patches/module-05-routes-wording.patch"
            ).read_text(encoding="utf-8")
            contract, _ = self._fixture(root, source, patch_text)
            entry = contract["local_patches"][0]
            entry.update(
                {
                    "id": "module-05-routes-wording",
                    "issue": (
                        "https://github.com/docktermj/"
                        "senzing-bootcamp-copilot-plugin-development/issues/11"
                    ),
                    "upstream": {
                        "issue": (
                            "https://github.com/docktermj/"
                            "senzing-bootcamp-claude-plugin-development/issues/881"
                        ),
                        "commit": "9466b0a36e98d405ceecb95af48fd55e5bbbf34b",
                    },
                    "reason": "Preserve the pinned table and count while correcting the wording.",
                }
            )
            contract["substitutions"] = transform.load_json_yaml(
                transform.CONTRACT
            )["substitutions"]

            with tempfile.TemporaryDirectory(dir=transform.ROOT / "plugins") as scratch:
                patched, _ = transform.apply_local_patches(
                    source, Path(scratch), contract, root
                )
                output = Path(scratch) / "plugin"
                transform.render(patched, output, contract, {})
                generated = (
                    output / "skills/module-05-data-quality-mapping/phase2-data-mapping.md"
                ).read_text(encoding="utf-8")

            self.assertIn(
                "three known routes — recognize the fourth on sight",
                generated,
            )
            self.assertNotIn("reachings", generated.lower())
            self.assertEqual(generated.count("| row "), 3)

    def test_local_patches_apply_in_contract_order(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            source = Path(temp) / "source"
            source.mkdir()
            (source / "skills").mkdir()
            (source / "skills/guide.md").write_text("old\n", encoding="utf-8")
            contract, _ = self._fixture(
                root, source, self._replace_patch("skills/guide.md", "old", "middle")
            )
            second = root / transform.LOCAL_PATCH_ROOT / "second.patch"
            second.write_text(
                self._replace_patch("skills/guide.md", "middle", "new"),
                encoding="utf-8",
            )
            contract["local_patches"].append(
                self._entry(patch_name="second.patch", patch_id="second-patch")
            )
            with tempfile.TemporaryDirectory() as scratch:
                patched, records = transform.apply_local_patches(
                    source, Path(scratch), contract, root
                )
                output = Path(scratch) / "plugin"
                transform.render(patched, output, contract, {})
                self.assertEqual(
                    (output / "skills/guide.md").read_text(encoding="utf-8"),
                    "new\n",
                )
            self.assertEqual([record["id"] for record in records], ["sample-patch", "second-patch"])

    def test_local_patch_addition_is_copied_by_contract_rule(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            source = Path(temp) / "source"
            source.mkdir()
            patch = (
                "diff --git a/skills/new.md b/skills/new.md\n"
                "new file mode 100644\n"
                "--- /dev/null\n"
                "+++ b/skills/new.md\n"
                "@@ -0,0 +1 @@\n"
                "+added by patch\n"
            )
            contract, _ = self._fixture(root, source, patch)
            with tempfile.TemporaryDirectory() as scratch:
                patched, _ = transform.apply_local_patches(source, Path(scratch), contract, root)
                output = Path(scratch) / "plugin"
                transform.render(patched, output, contract, {})
                self.assertEqual(
                    (output / "skills/new.md").read_text(encoding="utf-8"),
                    "added by patch\n",
                )

    def test_local_patch_addition_without_copy_rule_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            source = Path(temp) / "source"
            source.mkdir()
            patch = (
                "diff --git a/commands/new.md b/commands/new.md\n"
                "new file mode 100644\n"
                "--- /dev/null\n"
                "+++ b/commands/new.md\n"
                "@@ -0,0 +1 @@\n"
                "+not copied\n"
            )
            contract, _ = self._fixture(root, source, patch)
            with tempfile.TemporaryDirectory() as scratch:
                patched, _ = transform.apply_local_patches(source, Path(scratch), contract, root)
                with self.assertRaisesRegex(
                    transform.TransformError, r"E_UNMATCHED_FILE: commands/new\.md"
                ):
                    transform.render(patched, Path(scratch) / "plugin", contract, {})

    def test_local_patch_rejects_ignored_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            source = Path(temp) / "source"
            source.mkdir()
            (source / "commands").mkdir()
            (source / "commands/old.md").write_text("old\n", encoding="utf-8")
            contract, _ = self._fixture(
                root, source, self._replace_patch("commands/old.md", "old", "new")
            )
            contract["rules"].append(
                {"id": "ignore-commands", "kind": "ignore", "match": ["commands/**"]}
            )
            with tempfile.TemporaryDirectory() as scratch, self.assertRaisesRegex(
                transform.TransformError, r"E_PATCH_IGNORED_PATH: sample-patch: commands/old\.md"
            ):
                transform.apply_local_patches(source, Path(scratch), contract, root)

    def test_failed_build_does_not_write_plugin_or_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            source = Path(temp) / "source"
            root.mkdir()
            source.mkdir()
            (source / "skills").mkdir()
            (source / "skills/guide.md").write_text("unrelated\n", encoding="utf-8")
            contract, _ = self._fixture(
                root, source, self._replace_patch("skills/guide.md", "expected", "patched")
            )
            contract_path = root / "tools/bootcamp-transform/contract.yaml"
            contract_path.parent.mkdir(parents=True, exist_ok=True)
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            for name, value in (
                ("PARENT_VERSION", "0.6.1\n"),
                ("PARENT_COMMIT", f"{self.commit}\n"),
                ("RELEASE_VERSION", "0.6.1\n"),
            ):
                (root / name).write_text(value, encoding="utf-8")
            target = root / contract["output_root"]
            target.mkdir(parents=True)
            (target / "sentinel.txt").write_text("preserve\n", encoding="utf-8")
            manifest = root / ".build-manifest.json"
            manifest.write_text('{"files": {}}\n', encoding="utf-8")
            before_plugin = transform.file_hashes(target)
            before_manifest = manifest.read_bytes()

            with self.assertRaisesRegex(
                transform.TransformError,
                r"E_PATCH_DOES_NOT_APPLY: sample-patch: skills/guide\.md",
            ):
                self._run_build(root, source, contract, contract_path)

            self.assertEqual(transform.file_hashes(target), before_plugin)
            self.assertEqual(manifest.read_bytes(), before_manifest)

    def test_already_upstream_patch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            source = Path(temp) / "source"
            source.mkdir()
            (source / "skills").mkdir()
            (source / "skills/guide.md").write_text("patched\n", encoding="utf-8")
            contract, _ = self._fixture(
                root, source, self._replace_patch("skills/guide.md", "original", "patched")
            )
            with tempfile.TemporaryDirectory() as scratch, self.assertRaisesRegex(
                transform.TransformError, r"E_PATCH_ALREADY_UPSTREAM: sample-patch: skills/guide\.md"
            ):
                transform.apply_local_patches(source, Path(scratch), contract, root)

    def test_build_manifest_records_patch_identity_and_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            source = Path(temp) / "source"
            root.mkdir()
            source.mkdir()
            (source / "skills").mkdir()
            (source / "skills/guide.md").write_text("original\n", encoding="utf-8")
            contract, patch_path = self._fixture(
                root, source, self._replace_patch("skills/guide.md", "original", "patched")
            )
            contract_path = root / "tools/bootcamp-transform/contract.yaml"
            contract_path.parent.mkdir(parents=True, exist_ok=True)
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            for name, value in (
                ("PARENT_VERSION", "0.6.1\n"),
                ("PARENT_COMMIT", f"{self.commit}\n"),
                ("RELEASE_VERSION", "0.6.1\n"),
            ):
                (root / name).write_text(value, encoding="utf-8")

            self._run_build(root, source, contract, contract_path)

            self.assertEqual(
                json.loads((root / ".build-manifest.json").read_text(encoding="utf-8"))[
                    "local_patches"
                ],
                [{
                    "id": "sample-patch",
                    "sha256": hashlib.sha256(patch_path.read_bytes()).hexdigest(),
                }],
            )
            self.assertEqual(
                (root / contract["output_root"] / "skills/guide.md").read_text(encoding="utf-8"),
                "patched\n",
            )

    def test_empty_patch_registry_does_not_change_manifest_schema(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            source = Path(temp) / "source"
            root.mkdir()
            source.mkdir()
            (source / "skills").mkdir()
            (source / "skills/guide.md").write_text("original\n", encoding="utf-8")
            contract, _ = self._fixture(root, source, "unused")
            contract["local_patches"] = []
            (root / transform.LOCAL_PATCH_ROOT / "sample.patch").unlink()
            contract_path = root / "tools/bootcamp-transform/contract.yaml"
            contract_path.parent.mkdir(parents=True, exist_ok=True)
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            for name, value in (
                ("PARENT_VERSION", "0.6.1\n"),
                ("PARENT_COMMIT", f"{self.commit}\n"),
                ("RELEASE_VERSION", "0.6.1\n"),
            ):
                (root / name).write_text(value, encoding="utf-8")

            self._run_build(root, source, contract, contract_path)

            manifest = json.loads((root / ".build-manifest.json").read_text(encoding="utf-8"))
            self.assertNotIn("local_patches", manifest)
            self.assertEqual(
                (root / contract["output_root"] / "skills/guide.md").read_text(encoding="utf-8"),
                "original\n",
            )


if __name__ == "__main__":
    unittest.main()
