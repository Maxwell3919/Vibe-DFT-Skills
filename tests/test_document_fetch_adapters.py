from __future__ import annotations

import copy
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import document_fetch_adapters  # noqa: E402


class DocumentFetchAdapterRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = document_fetch_adapters.load_registry()

    def errors(self, value=None) -> list[str]:
        return document_fetch_adapters.validation_errors(value or self.registry, ROOT)

    def test_repository_registry_is_valid_and_requirement_derived(self) -> None:
        self.assertEqual(self.errors(), [])
        requirements = document_fetch_adapters.requirement_distributions(
            ROOT / "requirements-dev.txt"
        )
        self.assertEqual(
            set(self.registry["implementation_package_docs"]),
            set(requirements),
        )
        self.assertEqual(
            document_fetch_adapters.coverage_summary(self.registry, ROOT),
            {
                "adapters": 1,
                "community_profiles": 2,
                "implementation_packages": 11,
                "scientific_software": 23,
                "active_scientific_software": 4,
                "planned_scientific_software": 19,
            },
        )

    def test_native_routes_must_precede_browser_rendering(self) -> None:
        invalid = copy.deepcopy(self.registry)
        invalid["selection_policy"]["ordered_routes"].insert(0, "crawl4ai-render-v1")
        self.assertTrue(any("native routes must precede" in item for item in self.errors(invalid)))

    def test_every_security_control_is_fail_closed(self) -> None:
        invalid = copy.deepcopy(self.registry)
        invalid["adapters"]["crawl4ai-render-v1"]["security_controls"]["proxy_forbidden"] = False
        self.assertTrue(any("every fail-closed control" in item for item in self.errors(invalid)))

    def test_community_profile_rejects_credentials_and_private_literal_hosts(self) -> None:
        for origin in ("http://user@bbs.keinsci.com", "https://127.0.0.1"):
            with self.subTest(origin=origin):
                invalid = copy.deepcopy(self.registry)
                invalid["community_profiles"]["keinsci-public"]["allowed_origins"] = [origin]
                self.assertTrue(any("canonical public origin" in item for item in self.errors(invalid)))

    def test_requirement_mapping_cannot_silently_omit_a_package(self) -> None:
        invalid = copy.deepcopy(self.registry)
        invalid["implementation_package_docs"].pop("numpy")
        self.assertTrue(any("exactly cover" in item for item in self.errors(invalid)))

    def test_requirement_parser_rejects_duplicate_normalized_names(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "requirements-dev.txt"
            path.write_text("Example_Pkg>=1\nexample-pkg==2\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate distribution"):
                document_fetch_adapters.requirement_distributions(path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
