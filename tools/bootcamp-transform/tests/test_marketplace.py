from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import validate


class MarketplaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "repository"
        self.catalog_path = self.root / ".github/plugin/marketplace.json"
        self.catalog_path.parent.mkdir(parents=True)
        self.plugin = self.root / "plugins/senzing-bootcamp"
        self.plugin.mkdir(parents=True)
        self.manifest = {"name": "senzing-bootcamp", "version": "0.6.1"}
        (self.plugin / "plugin.json").write_text(json.dumps(self.manifest), encoding="utf-8")
        self.entry = {"name": "senzing-bootcamp", "source": "./plugins/senzing-bootcamp"}
        self.catalog = {
            "name": "senzing-bootcamp-development",
            "owner": {"name": "example-owner"},
            "plugins": [self.entry],
        }

    def check_catalog(self, catalog: object = None) -> list[str]:
        value = self.catalog if catalog is None else catalog
        self.catalog_path.write_text(json.dumps(value), encoding="utf-8")
        return self.run_check()

    def run_check(self) -> list[str]:
        with patch.object(validate, "ROOT", self.root), patch.object(validate, "errors", []):
            validate.check_marketplace()
            return list(validate.errors)

    def test_valid_catalog_with_optional_matching_version(self) -> None:
        self.assertEqual(self.check_catalog(), [])
        self.entry["version"] = "0.6.1"
        self.assertEqual(self.check_catalog(), [])

    def test_malformed_and_nonobject_catalogs(self) -> None:
        self.catalog_path.write_text("{", encoding="utf-8")
        self.assertIn("marketplace catalog is missing or invalid", "\n".join(self.run_check()))
        self.assertIn("must contain a JSON object", "\n".join(self.check_catalog([])))

    def test_invalid_required_fields(self) -> None:
        cases = [
            ("name", "", "marketplace name"),
            ("owner", [], "marketplace owner"),
            ("owner", {"name": 1}, "marketplace owner"),
            ("owner", {"name": " "}, "marketplace owner"),
            ("plugins", {}, "nonempty array"),
            ("plugins", [], "nonempty array"),
            ("plugins", [False], "must be an object"),
        ]
        for field, value, message in cases:
            with self.subTest(field=field, value=value):
                catalog = {**self.catalog, field: value}
                self.assertIn(message, "\n".join(self.check_catalog(catalog)))

    def test_invalid_entry_fields(self) -> None:
        for field in ("name", "source"):
            for value in (None, {}, "", " "):
                with self.subTest(field=field, value=value):
                    catalog = {**self.catalog, "plugins": [{**self.entry, field: value}]}
                    self.assertIn(f"{field} must be a nonempty", "\n".join(self.check_catalog(catalog)))

    def test_duplicate_and_missing_bootcamp_entries(self) -> None:
        self.catalog["plugins"] = [self.entry, dict(self.entry)]
        self.assertIn("duplicate plugin name", "\n".join(self.check_catalog()))
        self.entry["name"] = "other"
        self.catalog["plugins"] = [self.entry]
        self.assertIn("must include senzing-bootcamp", "\n".join(self.check_catalog()))

    def test_unsafe_sources(self) -> None:
        for source in (str(self.plugin), "../outside", "C:/outside", r"..\outside"):
            with self.subTest(source=source):
                self.entry["source"] = source
                messages = "\n".join(self.check_catalog())
                self.assertTrue("relative path" in messages or "escapes the repository" in messages)

    def test_unresolvable_source(self) -> None:
        self.entry["source"] = "./invalid\x00path"
        self.assertIn("source cannot be resolved", "\n".join(self.check_catalog()))

    def test_source_and_manifest_symlink_escapes(self) -> None:
        outside = Path(self.temp.name) / "outside"
        outside.mkdir()
        (outside / "plugin.json").write_text(json.dumps(self.manifest), encoding="utf-8")
        link = self.root / "linked"
        link.symlink_to(outside, target_is_directory=True)
        self.entry["source"] = "./linked"
        self.assertIn("source escapes the repository", "\n".join(self.check_catalog()))
        self.entry["source"] = "./plugins/senzing-bootcamp"
        manifest_path = self.plugin / "plugin.json"
        manifest_path.unlink()
        manifest_path.symlink_to(outside / "plugin.json")
        self.assertIn("manifest escapes the repository", "\n".join(self.check_catalog()))

    def test_missing_source_and_invalid_manifest(self) -> None:
        self.entry["source"] = "./missing"
        self.assertIn("plugin manifest is missing or invalid", "\n".join(self.check_catalog()))
        self.entry["source"] = "./plugins/senzing-bootcamp"
        (self.plugin / "plugin.json").write_text("[]", encoding="utf-8")
        self.assertIn("plugin manifest must contain a JSON object", "\n".join(self.check_catalog()))

    def test_manifest_disagreement(self) -> None:
        self.entry["name"] = "different"
        self.assertIn("name differs from plugin manifest", "\n".join(self.check_catalog()))
        self.entry["name"] = "senzing-bootcamp"
        for version in ("different", 1, None, ""):
            with self.subTest(version=version):
                self.entry["version"] = version
                self.assertIn("version differs", "\n".join(self.check_catalog()))

    def test_bootcamp_source_must_remain_stable(self) -> None:
        self.entry["source"] = "./plugins/senzing-bootcamp/."
        self.assertIn("source must be ./plugins/senzing-bootcamp", "\n".join(self.check_catalog()))


if __name__ == "__main__":
    unittest.main()
