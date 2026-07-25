from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

from jsonschema import Draft202012Validator, FormatChecker


SKILL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
REFERENCES = SKILL_ROOT / "references"
SEED_PATH = REFERENCES / "source-pack-seed.json"
SCOPE_PATH = REFERENCES / "source-pack-scope-catalog.json"
PROPOSAL_PATH = REFERENCES / "source-authority-binding-proposal.json"


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{path} must contain an object")
    return value


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class LobsterOfficialDocumentSeedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.seed = load_json(SEED_PATH)
        cls.scope = load_json(SCOPE_PATH)
        cls.proposal = load_json(PROPOSAL_PATH)
        cls.catalogs = [
            load_json(REPO_ROOT / item["source_ref"]["path"])
            for item in cls.seed["providers"]
        ]

    def validate_schema(self, value: dict, relative_schema: str) -> None:
        schema = load_json(REPO_ROOT / relative_schema)
        errors = sorted(
            Draft202012Validator(
                schema, format_checker=FormatChecker()
            ).iter_errors(value),
            key=lambda item: list(item.path),
        )
        self.assertEqual(
            errors,
            [],
            "\n".join(
                f"{'/'.join(str(part) for part in item.path)}: {item.message}"
                for item in errors
            ),
        )

    def test_seed_scope_and_catalogs_match_strict_schemas(self) -> None:
        self.validate_schema(
            self.seed,
            "contracts/official-document-pack-seed.schema.json",
        )
        self.validate_schema(
            self.scope,
            "contracts/official-document-scope-catalog.schema.json",
        )
        for catalog in self.catalogs:
            self.validate_schema(
                catalog,
                "contracts/official-document-source-catalog-1.1.schema.json",
            )

    def test_every_seed_file_reference_is_exact(self) -> None:
        refs = [
            self.seed["scope_catalog_ref"],
            *(item["source_ref"] for item in self.seed["providers"]),
        ]
        for ref in refs:
            with self.subTest(path=ref["path"]):
                path = REPO_ROOT / ref["path"]
                self.assertTrue(path.is_file())
                self.assertEqual(digest(path), ref["sha256"])

    def test_scope_maps_native_gaps_to_literature_review_without_fake_provider(self) -> None:
        provider_ids = {item["input_id"] for item in self.seed["providers"]}
        self.assertEqual(
            provider_ids,
            {
                "lobster-acs-method-literature",
                "lobster-wiley-method-literature",
            },
        )
        subjects = {
            item["subject_id"]: item for item in self.scope["subjects"]
        }
        for subject in subjects.values():
            mapped = set(subject["provider_input_ids"])
            self.assertLessEqual(mapped, provider_ids)
            if subject["evidence_class"] == "official-provider-required":
                self.assertTrue(mapped)
            else:
                self.assertEqual(mapped, set())
        self.assertEqual(
            subjects["lobster-5-1-1-native-contract"][
                "expected_disposition"
            ],
            "blocked",
        )
        self.assertEqual(
            set(
                subjects["lobster-5-1-1-native-contract"][
                    "provider_input_ids"
                ]
            ),
            provider_ids,
        )
        self.assertNotIn("lobster-5-1-1-license-boundary", subjects)
        self.assertEqual(self.seed["status_ceiling"], "blocked")
        self.assertTrue(self.seed["blockers"])

    def test_catalog_subjects_exactly_match_scope_without_fake_blocked_slices(
        self,
    ) -> None:
        scope_subjects = {
            item["subject_id"]: item for item in self.scope["subjects"]
        }
        for provider, catalog in zip(
            self.seed["providers"], self.catalogs, strict=True
        ):
            input_id = provider["input_id"]
            expected = {
                subject_id
                for subject_id, item in scope_subjects.items()
                if item["evidence_class"] == "official-provider-required"
                and input_id in item["provider_input_ids"]
            }
            declared = set(catalog["subjects"])
            sliced = {
                subject_id
                for source in catalog["discovered_sources"].values()
                if source["disposition"] == "included"
                for item in source["selectors"]
                for subject_id in item["subject_ids"]
            }
            blocked = {
                subject_id
                for subject_id in expected
                if scope_subjects[subject_id]["expected_disposition"]
                == "blocked"
            }
            self.assertEqual(declared, expected)
            self.assertEqual(
                blocked,
                {"lobster-5-1-1-native-contract"},
            )
            self.assertTrue(blocked.isdisjoint(sliced))
            self.assertEqual(sliced, expected - blocked)

    def test_catalogs_are_https_doi_metadata_only_and_query_free(self) -> None:
        self.assertEqual(
            sum(len(item["discovered_sources"]) for item in self.catalogs),
            7,
        )
        for catalog in self.catalogs:
            rendered = json.dumps(catalog)
            self.assertNotIn("http://", rendered)
            self.assertNotIn("?", rendered)
            self.assertNotIn("schmeling.ac.rwth-aachen.de", rendered)
            self.assertFalse(catalog["upstream_universe_complete"])
            self.assertNotIn("license", catalog)
            for source in catalog["discovered_sources"].values():
                self.assertEqual(source["disposition"], "included")
                content = source["content"]
                self.assertTrue(
                    content["locator"].startswith("https://doi.org/")
                )
                self.assertEqual(content["content_mode"], "external-content")
                self.assertNotIn("content_ref", source)
                self.assertIn("receipt", content)
                for item in source["selectors"]:
                    self.assertNotIn("content_ref", item)
                    self.assertIn("selected_identity", item)

    def test_authority_and_binding_proposal_matches_seed_and_central_contract(self) -> None:
        sys.path.insert(0, str(REPO_ROOT / "tools"))
        import official_source_authorities  # noqa: PLC0415
        from registry_yaml import load_yaml_strict  # noqa: PLC0415

        authorities = load_yaml_strict(
            REPO_ROOT / "registry/official-source-authorities.yaml",
            "official-source-authorities.yaml",
        )
        software = load_yaml_strict(
            REPO_ROOT / "registry/software-registry.yaml",
            "software-registry.yaml",
        )
        merged = copy.deepcopy(authorities)
        merged["authorities"].update(
            copy.deepcopy(self.proposal["authority_entries"])
        )
        self.assertEqual(
            official_source_authorities.validation_errors(
                merged,
                software_data=software,
                source_root=REPO_ROOT,
            ),
            [],
        )
        proposed = {
            (item["input_id"], item["authority_id"], item["provider_id"])
            for item in self.proposal["seed_provider_bindings"]
        }
        seeded = {
            (item["input_id"], item["authority_id"], item["provider_id"])
            for item in self.seed["providers"]
        }
        self.assertEqual(proposed, seeded)
        self.assertEqual(
            {
                item["provider_class"]
                for item in self.proposal["authority_entries"].values()
            },
            {"publisher"},
        )
        for authority in self.proposal["authority_entries"].values():
            self.assertEqual(authority["content_policy"]["query_policy"], "forbidden")
            self.assertEqual(
                authority["redistribution_policy"]["bundle_content"],
                "forbidden",
            )

    def test_query_bearing_native_pages_are_blocked_proposal_metadata_only(self) -> None:
        blocked = self.proposal["blocked_native_sources"]
        self.assertEqual(len(blocked), 1)
        self.assertEqual(blocked[0]["disposition"], "blocked")
        self.assertTrue(all("?" in item for item in blocked[0]["locators"]))
        self.assertIn("query", blocked[0]["reason"].lower())
        active_json = json.dumps(
            {
                "seed": self.seed,
                "catalogs": self.catalogs,
                "authorities": self.proposal["authority_entries"],
            }
        )
        self.assertNotIn("schmeling.ac.rwth-aachen.de", active_json)

    def test_scope_extractor_is_offline_and_current(self) -> None:
        script = SKILL_ROOT / "scripts/extract_document_scope.py"
        text = script.read_text(encoding="utf-8")
        for forbidden in (
            "urllib",
            "requests",
            "socket",
            "curl",
            "verify=False",
            "_create_unverified_context",
        ):
            self.assertNotIn(forbidden, text)
        result = subprocess.run(
            [sys.executable, str(script), "--check"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)


if __name__ == "__main__":
    unittest.main()
