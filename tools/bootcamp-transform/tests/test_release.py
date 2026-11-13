from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import release


class ReleaseGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "docs/test-records").mkdir(parents=True)
        (self.root / "docs/test-checklist.md").write_text(
            "| ID | Required | Test |\n| TC-01 | Yes | Install plugin |\n"
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_missing_record_blocks_release(self) -> None:
        with self.assertRaisesRegex(ValueError, "Missing test record"):
            release.validate_record(self.root, "1.2.3")

    def test_blocked_record_blocks_release(self) -> None:
        (self.root / "docs/test-records/1.2.3.md").write_text(
            "**Release candidate:** 1.2.3\n**Status:** BLOCKED\n"
        )
        with self.assertRaisesRegex(ValueError, "status must be PASS"):
            release.validate_record(self.root, "1.2.3")


class ReleasePlanTests(unittest.TestCase):
    branch = "release-review"
    notes = "- Bootstrap the GitHub Copilot child development repository and pinned parent transform."
    parent_commit = "d3d99523f88957cd9dda2d29375892bf2c557663"

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        subprocess.run(
            ["git", "init", "-q", "--initial-branch", self.branch, str(self.root)],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(self.root), "config", "user.name", "Fixture"],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(self.root), "config", "user.email", "fixture@example.invalid"],
            check=True,
        )
        subprocess.run(["git", "-C", str(self.root), "config", "commit.gpgsign", "false"], check=True)
        subprocess.run(["git", "-C", str(self.root), "config", "tag.gpgsign", "false"], check=True)
        subprocess.run([
            "git", "-C", str(self.root), "remote", "add", "origin",
            "https://github.com/docktermj/senzing-bootcamp-copilot-plugin-development.git",
        ], check=True)
        self._write_fixture()
        subprocess.run(["git", "-C", str(self.root), "add", "--all"], check=True)
        subprocess.run(["git", "-C", str(self.root), "commit", "-qm", "fixture"], check=True)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _write_fixture(self) -> None:
        (self.root / "docs/test-records").mkdir(parents=True)
        (self.root / "docs/test-checklist.md").write_text(
            "| ID | Required | Test |\n| TC-01 | Yes | Install plugin |\n"
        )
        for version in ("0.6.1", "0.6.2"):
            (self.root / f"docs/test-records/{version}.md").write_text(
                f"**Release candidate:** {version}\n"
                "**Status:** PASS\n"
                "**Tested on:** 2026-01-01\n"
                "**Tester:** Fixture\n"
                "**Copilot client/version:** GitHub Copilot CLI fixture\n"
                "**Platform:** Fixture platform\n"
                f"**Plugin build:** {version}\n"
                "**Hooks reviewed and trusted:** PASS\n"
                f"**Exact-version checks:** PASS {version} - TC-01\n\n"
                "| TC-01 | PASS | Fixture passed | Fixture / 2026-01-01 |\n"
            )
        (self.root / "RELEASE_VERSION").write_text("0.6.1\n")
        (self.root / "PARENT_VERSION").write_text("0.6.1\n")
        (self.root / "PARENT_COMMIT").write_text(f"{self.parent_commit}\n")
        manifest = self.root / "plugins/senzing-bootcamp/plugin.json"
        manifest.parent.mkdir(parents=True)
        manifest.write_text('{"name":"senzing-bootcamp","version":"0.6.1"}\n')
        (self.root / ".build-manifest.json").write_text(
            f'{{"release_version":"0.6.1","parent_version":"0.6.1",'
            f'"parent_commit":"{self.parent_commit}","files":{{"plugin.json":{{}}}}}}\n'
        )
        (self.root / "CHANGELOG.md").write_text(
            f"# Changelog\n\n## [Unreleased]\n\n{self.notes}\n"
        )

    def _plan(self, version: str = "0.6.1", notes: str | None = None) -> dict[str, bytes]:
        return release.plan_release(
            self.root, version, self.notes if notes is None else notes, self.branch
        )

    def test_initial_release_moves_the_exact_unreleased_bullet(self) -> None:
        updates = self._plan()
        changelog = updates["CHANGELOG.md"].decode()
        self.assertIn(f"## [0.6.1]\n\n{self.notes}", changelog)
        self.assertIn("## [Unreleased]\n\n", changelog)
        self.assertEqual(changelog.count(self.notes), 1)

    def test_initial_release_requires_exactly_the_unreleased_bullet(self) -> None:
        with self.assertRaisesRegex(ValueError, "exactly match"):
            self._plan(notes="- Different release note")

    def test_initial_release_rejects_existing_tags(self) -> None:
        for tag in ("0.6.1", "v0.6.1"):
            with self.subTest(tag=tag):
                subprocess.run(
                    ["git", "-C", str(self.root), "tag", tag],
                    check=True,
                )
                with self.assertRaisesRegex(ValueError, "Release tag already exists"):
                    self._plan()
                subprocess.run(
                    ["git", "-C", str(self.root), "tag", "-d", tag],
                    check=True,
                    capture_output=True,
                )

    def test_release_version_must_be_stable_and_not_older(self) -> None:
        for version in ("0.6.0", "0.6.1-rc.1"):
            with self.subTest(version=version):
                with self.assertRaisesRegex(ValueError, "exact stable SemVer|not be older"):
                    self._plan(version)

    def test_later_release_remains_strictly_increasing(self) -> None:
        changelog = self._plan("0.6.2")["CHANGELOG.md"].decode()
        self.assertIn("## [0.6.2]", changelog)
        self.assertIn(f"## [Unreleased]\n\n{self.notes}", changelog)


if __name__ == "__main__":
    unittest.main()
