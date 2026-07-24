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


class GaussianOfficialDocumentSeedTests(unittest.TestCase):
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
                "contracts/official-document-source-catalog.schema.json",
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

    def test_scope_provider_mapping_is_total_and_fail_closed(self) -> None:
        provider_ids = {item["input_id"] for item in self.seed["providers"]}
        self.assertEqual(
            provider_ids,
            {"gaussian-g16-c01-public", "gaussian-g16-c02-delta"},
        )
        dispositions = {}
        for subject in self.scope["subjects"]:
            dispositions[subject["subject_id"]] = subject["expected_disposition"]
            mapped = set(subject["provider_input_ids"])
            self.assertLessEqual(mapped, provider_ids)
            if subject["evidence_class"] == "official-provider-required":
                self.assertTrue(mapped)
            else:
                self.assertEqual(mapped, set())
        self.assertEqual(dispositions["g16-licensed-runtime"], "blocked")
        self.assertEqual(self.seed["status_ceiling"], "partial")
        self.assertEqual(self.seed["blockers"], [])

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
            declared = {item["subject_id"] for item in catalog["subjects"]}
            sliced = {
                subject_id
                for source in catalog["sources"]
                for item in source["slices"]
                for subject_id in item["subject_ids"]
            }
            blocked = {
                subject_id
                for subject_id in expected
                if scope_subjects[subject_id]["expected_disposition"]
                == "blocked"
            }
            self.assertEqual(declared, expected)
            self.assertEqual(blocked, {"g16-licensed-runtime"})
            self.assertTrue(blocked.isdisjoint(sliced))
            self.assertEqual(sliced, expected - blocked)

    def test_catalogs_are_https_metadata_only_and_exactly_registered(self) -> None:
        self.assertEqual(
            [item["version_scope"]["kind"] for item in self.catalogs],
            ["exact", "exact"],
        )
        self.assertEqual(
            [item["version_scope"]["value"] for item in self.catalogs],
            ["16-C.01-public-reference", "16-C.02-release-delta"],
        )
        for catalog in self.catalogs:
            self.assertFalse(catalog["upstream_universe_complete"])
            self.assertNotIn("http://", json.dumps(catalog))
            for source in catalog["sources"]:
                self.assertTrue(source["locator"].startswith("https://"))
                self.assertNotIn("content_ref", source)
                self.assertIn("external_identity", source)
                for item in source["slices"]:
                    self.assertNotIn("content_ref", item)
                    self.assertIn("external_receipt", item)
            self.assertNotIn(
                "embedded-open",
                catalog["license"]["allowed_storage_modes"],
            )

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
        for authority in self.proposal["authority_entries"].values():
            self.assertEqual(authority["content_policy"]["query_policy"], "forbidden")
            self.assertEqual(
                authority["redistribution_policy"]["bundle_content"],
                "forbidden",
            )

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
