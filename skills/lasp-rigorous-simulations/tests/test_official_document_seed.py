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


class LaspOfficialDocumentSeedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.seed = load_json(SEED_PATH)
        cls.scope = load_json(SCOPE_PATH)
        cls.proposal = load_json(PROPOSAL_PATH)
        cls.catalog = load_json(
            REPO_ROOT / cls.seed["providers"][0]["source_ref"]["path"]
        )

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

    def test_seed_scope_and_catalog_match_strict_schemas(self) -> None:
        self.validate_schema(
            self.seed,
            "contracts/official-document-pack-seed.schema.json",
        )
        self.validate_schema(
            self.scope,
            "contracts/official-document-scope-catalog.schema.json",
        )
        self.validate_schema(
            self.catalog,
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

    def test_scope_is_complete_about_literature_ceiling_and_native_blockers(self) -> None:
        self.assertEqual(
            [item["input_id"] for item in self.seed["providers"]],
            ["lasp-author-literature"],
        )
        subjects = {
            item["subject_id"]: item for item in self.scope["subjects"]
        }
        for subject in subjects.values():
            mapped = set(subject["provider_input_ids"])
            self.assertLessEqual(mapped, {"lasp-author-literature"})
            if subject["evidence_class"] == "official-provider-required":
                self.assertEqual(mapped, {"lasp-author-literature"})
            else:
                self.assertEqual(mapped, set())
        self.assertEqual(
            subjects["lasp-3-7-capability-context"]["expected_disposition"],
            "partial",
        )
        self.assertEqual(
            subjects["lasp-3-7-3-native-contract"]["expected_disposition"],
            "blocked",
        )
        self.assertNotIn("lasp-3-7-3-license-terms", subjects)
        self.assertEqual(self.seed["status_ceiling"], "blocked")
        self.assertTrue(self.seed["blockers"])

    def test_catalog_subjects_exactly_match_scope_without_fake_blocked_slices(
        self,
    ) -> None:
        input_id = self.seed["providers"][0]["input_id"]
        scope_subjects = {
            item["subject_id"]: item for item in self.scope["subjects"]
        }
        expected = {
            subject_id
            for subject_id, item in scope_subjects.items()
            if item["evidence_class"] == "official-provider-required"
            and input_id in item["provider_input_ids"]
        }
        declared = set(self.catalog["subjects"])
        sliced = {
            subject_id
            for source in self.catalog["discovered_sources"].values()
            if source["disposition"] == "included"
            for item in source["selectors"]
            for subject_id in item["subject_ids"]
        }
        blocked = {
            subject_id
            for subject_id in expected
            if scope_subjects[subject_id]["expected_disposition"] == "blocked"
        }
        self.assertEqual(declared, expected)
        self.assertEqual(
            blocked,
            {"lasp-3-7-3-native-contract"},
        )
        self.assertTrue(blocked.isdisjoint(sliced))
        self.assertEqual(sliced, expected - blocked)

    def test_catalog_is_https_metadata_only_and_keeps_native_payloads_out(self) -> None:
        self.assertEqual(len(self.catalog["discovered_sources"]), 5)
        rendered = json.dumps(self.catalog)
        self.assertNotIn("http://", rendered)
        self.assertNotIn("www.lasphub.com", rendered)
        self.assertFalse(self.catalog["upstream_universe_complete"])
        self.assertNotIn("license", self.catalog)
        locators = {
            item["content"]["locator"]
            for item in self.catalog["discovered_sources"].values()
        }
        self.assertTrue(
            any(item.startswith("https://doi.org/") for item in locators)
        )
        self.assertIn(
            "https://pmc.ncbi.nlm.nih.gov/articles/PMC11672538/",
            locators,
        )
        for source in self.catalog["discovered_sources"].values():
            self.assertEqual(source["disposition"], "included")
            self.assertTrue(source["content"]["locator"].startswith("https://"))
            self.assertEqual(source["content"]["content_mode"], "external-content")
            self.assertNotIn("content_ref", source)
            self.assertIn("receipt", source["content"])
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
        authority = self.proposal["authority_entries"]["lasp-author-literature"]
        self.assertEqual(authority["provider_class"], "publisher")
        self.assertEqual(authority["content_policy"]["query_policy"], "forbidden")
        self.assertEqual(
            authority["redistribution_policy"]["bundle_content"],
            "forbidden",
        )
        self.assertTrue(
            all(
                item.startswith("https://")
                for item in authority["allowed_https_origins"]
            )
        )

    def test_http_hub_is_blocked_proposal_metadata_only(self) -> None:
        blocked = self.proposal["blocked_native_sources"]
        self.assertEqual(len(blocked), 1)
        self.assertEqual(blocked[0]["disposition"], "blocked")
        self.assertTrue(all(item.startswith("http://") for item in blocked[0]["locators"]))
        active_json = json.dumps(
            {
                "seed": self.seed,
                "catalog": self.catalog,
                "authority": self.proposal["authority_entries"],
            }
        )
        self.assertNotIn("http://", active_json)
        self.assertNotIn("www.lasphub.com", active_json)

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
