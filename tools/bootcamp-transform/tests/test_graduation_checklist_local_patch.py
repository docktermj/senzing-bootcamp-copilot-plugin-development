"""Regression checks for graduation's generated production migration checklist guidance."""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "plugins" / "senzing-bootcamp"
SKILL = PLUGIN_ROOT / "skills" / "graduation" / "SKILL.md"
MODULE_07 = (
    PLUGIN_ROOT
    / "skills"
    / "module-07-query-visualize-discover"
    / "phase1-query-visualize.md"
)
PATCH = (
    REPO_ROOT
    / "tools"
    / "bootcamp-transform"
    / "patches"
    / "graduation-production-checklist.patch"
)


def checklist_item(text: str, heading: str) -> str:
    match = re.search(
        rf"{re.escape(heading)}.*?— ⚠️ \*\"(?P<item>.*?)\"\*",
        text,
        re.DOTALL,
    )
    if match is None:
        raise AssertionError(f"missing quoted checklist item: {heading}")
    return match.group("item")


def compact(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


class GraduationChecklistLocalPatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = SKILL.read_text(encoding="utf-8")
        cls.module_07 = MODULE_07.read_text(encoding="utf-8")
        cls.patch = PATCH.read_text(encoding="utf-8")

    def test_database_item_guides_evaluation_to_production_without_overclaiming(self) -> None:
        item = compact(
            checklist_item(
                self.skill, "The Database section MUST carry the production-database item"
            )
        )
        self.assertIn("SQLite is an evaluation and starter database", item)
        self.assertIn("move to a supported production database", item)
        self.assertIn("recommends PostgreSQL for anything beyond evaluation", item)
        self.assertIn("this starter is not ready to deploy unchanged", item)
        self.assertNotIn("SQLite cannot run in production", item)

    def test_export_warning_and_output_safeguard_are_inside_the_checklist_item(self) -> None:
        item = compact(
            checklist_item(
                self.skill, "The Performance section MUST carry the DEFAULT-flags item"
            )
        )
        self.assertIn("including the export call", item)
        self.assertIn("RELATED_ENTITIES", item)
        self.assertIn(
            "confirm that every field and relationship your code reads is still present",
            item,
        )
        self.assertIn("leave this item unchecked", item)
        guidance = compact(self.skill)
        self.assertIn("The export call is not exempt", guidance)
        self.assertIn(
            "`SZ_EXPORT_DEFAULT_FLAGS` is itself a composite whose members include "
            "`SZ_ENTITY_DEFAULT_FLAGS`",
            guidance,
        )

    def test_module_seven_references_the_export_qualification(self) -> None:
        module_07 = compact(self.module_07)
        self.assertIn(
            "item's own qualification says the export call is where the replacement "
            "must not be applied",
            module_07,
        )
        self.assertNotIn("item's own carve-out", module_07)

    def test_patch_is_limited_to_guidance_and_does_not_migrate_or_rewrite_code(self) -> None:
        paths = re.findall(r"^diff --git a/(.*?) b/", self.patch, re.MULTILINE)
        self.assertEqual(
            [
                "skills/graduation/SKILL.md",
                "skills/module-07-query-visualize-discover/phase1-query-visualize.md",
            ],
            paths,
        )
        skill = compact(self.skill)
        self.assertIn("asks for a migration the team carries out", skill)
        self.assertIn("graduation changes no template and migrates no data", skill)
        self.assertIn("src/query/**` is copied into `production/src/`", skill)


if __name__ == "__main__":
    unittest.main()
