from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import escalations

FIX = "1" * 40
PUBLIC = "3" * 40


def evidence(parent: dict | None = None, **overrides: object) -> dict:
    values = {
        "local": {
            "state": "OPEN",
            "body": "Fix: docktermj/senzing-bootcamp-claude-plugin-development#22",
            "labels": [{"name": "awaiting-parity"}],
        },
        "parent": {
            "state": "CLOSED",
            "stateReason": "completed",
            "body": "Child: docktermj/senzing-bootcamp-copilot-plugin-development#11",
        },
        "local_number": 11,
        "parent_number": 22,
        "tag": "0.6.2",
        "fix_commit": FIX,
        "public_commit": PUBLIC,
        "tree_difference": None,
        "pinned_version": "0.6.2",
        "pinned_commit": PUBLIC,
        "fix_in_tag": True,
    }
    if parent is not None:
        values["parent"] = parent
    values.update(overrides)
    return escalations.evaluate(**values)


class EscalationParityTests(unittest.TestCase):
    def test_closes_only_when_tagged_fix_and_pin_match(self) -> None:
        self.assertEqual(evidence()["status"], "ready-to-close")

    def test_mismatched_pin_blocks_closure(self) -> None:
        self.assertEqual(evidence(pinned_commit="4" * 40)["status"], "awaiting-pin")

    def test_waits_for_release_containing_fix(self) -> None:
        self.assertEqual(evidence(fix_in_tag=False)["status"], "awaiting-release")

    def test_parent_not_planned_requires_human_decision(self) -> None:
        result = evidence(parent={
            "state": "CLOSED",
            "stateReason": "not_planned",
            "body": "",
        })
        self.assertEqual(result["status"], "human-decision")

    def test_missing_awaiting_parity_label_blocks_closure(self) -> None:
        self.assertEqual(evidence(local={
            "state": "OPEN", "body": "docktermj/senzing-bootcamp-claude-plugin-development#22",
            "labels": [],
        })["status"], "blocked")

    def test_accepts_markdown_issue_urls_in_both_directions(self) -> None:
        local = {
            "state": "OPEN",
            "body": f"[parent](https://github.com/{escalations.PARENT_DEV}/issues/22)",
            "labels": [{"name": "awaiting-parity"}],
        }
        parent = {
            "state": "CLOSED",
            "stateReason": "completed",
            "body": f"[child](https://github.com/{escalations.LOCAL_REPO}/issues/11)",
        }
        self.assertEqual(evidence(local=local, parent=parent)["status"], "ready-to-close")

    def test_rejects_invalid_issue_references_and_number_prefixes(self) -> None:
        invalid_parent_refs = (
            f"{escalations.PARENT_DEV}#220",
            "https://evil.example/docktermj/senzing-bootcamp-claude-plugin-development/issues/22",
            f"https://github.com/{escalations.PARENT_DEV}/pull/22",
            "docktermj/another-repository#22",
        )
        for reference in invalid_parent_refs:
            with self.subTest(reference=reference):
                result = evidence(local={
                    "state": "OPEN",
                    "body": reference,
                    "labels": [{"name": "awaiting-parity"}],
                })
                self.assertEqual(result["status"], "blocked")
                self.assertIn("Local issue does not cross-reference", result["reason"])

        invalid_local_refs = (
            f"{escalations.LOCAL_REPO}#110",
            "https://evil.example/docktermj/senzing-bootcamp-copilot-plugin-development/issues/11",
            f"https://github.com/{escalations.LOCAL_REPO}/pull/11",
            "docktermj/another-repository#11",
        )
        for reference in invalid_local_refs:
            with self.subTest(reference=reference):
                parent = {
                    "state": "CLOSED",
                    "stateReason": "completed",
                    "body": reference,
                }
                result = evidence(parent=parent)
                self.assertEqual(result["status"], "blocked")
                self.assertIn("Parent issue does not cross-reference", result["reason"])


class PluginTreeComparisonTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _manifest(self, repository_name: str, **overrides: object) -> dict[str, object]:
        manifest: dict[str, object] = {
            "name": "senzing-bootcamp",
            "version": "0.6.1",
            "description": "Entity resolution bootcamp",
            "homepage": escalations.EXPECTED_MANIFEST_URLS[repository_name],
            "repository": escalations.EXPECTED_MANIFEST_URLS[repository_name],
        }
        manifest.update(overrides)
        return manifest

    def _tagged_repo(
        self,
        name: str,
        manifest: dict[str, object] | bytes,
        files: dict[str, bytes] | None = None,
    ) -> Path:
        checkout = self.root / name
        subprocess.run(["git", "init", "-q", str(checkout)], check=True)
        subprocess.run(["git", "-C", str(checkout), "config", "user.name", "Fixture"], check=True)
        subprocess.run(
            ["git", "-C", str(checkout), "config", "user.email", "fixture@example.invalid"],
            check=True,
        )
        subprocess.run(["git", "-C", str(checkout), "config", "commit.gpgsign", "false"], check=True)
        subprocess.run(["git", "-C", str(checkout), "config", "tag.gpgsign", "false"], check=True)
        manifest_path = checkout / "plugins/senzing-bootcamp/.claude-plugin/plugin.json"
        manifest_path.parent.mkdir(parents=True)
        manifest_bytes = manifest if isinstance(manifest, bytes) else json.dumps(manifest).encode()
        manifest_path.write_bytes(manifest_bytes)
        for relative_path, content in (files or {"README.md": b"same bytes"}).items():
            path = checkout / "plugins/senzing-bootcamp" / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        subprocess.run(["git", "-C", str(checkout), "add", "--all"], check=True)
        subprocess.run(["git", "-C", str(checkout), "commit", "-qm", "fixture"], check=True)
        subprocess.run(["git", "-C", str(checkout), "tag", "0.6.1"], check=True)
        return checkout

    def _difference(
        self,
        development_manifest: dict[str, object] | bytes | None = None,
        public_manifest: dict[str, object] | bytes | None = None,
        development_files: dict[str, bytes] | None = None,
        public_files: dict[str, bytes] | None = None,
    ) -> str | None:
        development = self._tagged_repo(
            "development",
            development_manifest or self._manifest(escalations.PARENT_DEV),
            development_files,
        )
        public = self._tagged_repo(
            "public",
            public_manifest or self._manifest(escalations.PARENT_PUBLIC),
            public_files,
        )
        return escalations.plugin_tree_difference(
            development,
            escalations.tree(development, "0.6.1"),
            public,
            escalations.tree(public, "0.6.1"),
        )

    def test_allows_only_the_expected_manifest_url_equivalence(self) -> None:
        self.assertIsNone(self._difference())

    def test_identical_trees_keep_the_fast_path(self) -> None:
        development = self._tagged_repo(
            "development",
            self._manifest(escalations.PARENT_DEV),
        )
        public = self._tagged_repo(
            "public",
            self._manifest(escalations.PARENT_DEV),
        )
        development_tree = escalations.tree(development, "0.6.1")
        public_tree = escalations.tree(public, "0.6.1")
        self.assertEqual(development_tree, public_tree)
        with mock.patch.object(escalations, "_tree_inventory", side_effect=AssertionError):
            self.assertIsNone(escalations.plugin_tree_difference(
                development, development_tree, public, public_tree,
            ))

    def test_rejects_other_manifest_field_drift(self) -> None:
        difference = self._difference(
            public_manifest=self._manifest(escalations.PARENT_PUBLIC, description="changed"),
        )
        self.assertEqual(
            difference,
            "Manifest content differs at .claude-plugin/plugin.json:$.description",
        )

    def test_rejects_non_manifest_content_drift(self) -> None:
        difference = self._difference(
            development_files={"README.md": b"development"},
            public_files={"README.md": b"public"},
        )
        self.assertEqual(difference, "File contents differ: README.md")

    def test_rejects_added_files(self) -> None:
        difference = self._difference(
            development_files={"README.md": b"same bytes", "new.txt": b"extra"},
        )
        self.assertEqual(difference, "File is missing from the public tree: new.txt")

    def test_rejects_files_missing_from_the_development_tree(self) -> None:
        difference = self._difference(
            public_files={"README.md": b"same bytes", "new.txt": b"extra"},
        )
        self.assertEqual(difference, "File is missing from the development tree: new.txt")

    def test_rejects_unexpected_manifest_urls(self) -> None:
        base = self.root
        cases = (
            (escalations.PARENT_DEV, "homepage"),
            (escalations.PARENT_DEV, "repository"),
            (escalations.PARENT_PUBLIC, "homepage"),
            (escalations.PARENT_PUBLIC, "repository"),
        )
        for index, (repository, field) in enumerate(cases):
            with self.subTest(repository=repository, field=field):
                self.root = base / str(index)
                self.root.mkdir()
                invalid_manifest = self._manifest(
                    repository,
                    **{field: "https://github.com/unexpected/repository"},
                )
                kwargs = (
                    {"development_manifest": invalid_manifest}
                    if repository == escalations.PARENT_DEV
                    else {"public_manifest": invalid_manifest}
                )
                with self.assertRaisesRegex(
                    escalations.EvidenceError,
                    f"Unexpected .* manifest {field}",
                ):
                    self._difference(**kwargs)
        self.root = base

    def test_malformed_manifest_blocks_comparison(self) -> None:
        with self.assertRaisesRegex(escalations.EvidenceError, "Invalid manifest.*plugin.json"):
            self._difference(public_manifest=b'{"version":')

    def test_invalid_tree_blocks_comparison_with_git_evidence(self) -> None:
        development = self._tagged_repo(
            "development",
            self._manifest(escalations.PARENT_DEV),
        )
        public = self._tagged_repo(
            "public",
            self._manifest(escalations.PARENT_PUBLIC),
        )
        with self.assertRaisesRegex(escalations.EvidenceError, "Not a valid object name"):
            escalations.plugin_tree_difference(development, "missing-tree", public, "other-tree")


if __name__ == "__main__":
    unittest.main()
