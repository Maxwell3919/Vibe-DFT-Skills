from __future__ import annotations

from contextlib import ExitStack
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import official_source_authorities  # noqa: E402
import registry_snapshot  # noqa: E402
from registry_yaml import RegistryYAMLError, load_yaml_strict  # noqa: E402


CORE_ACTIVE_AUTHORITIES = {
    "qe-official-docs",
    "qe-release-source-docs",
    "vasp-official-wiki",
    "cp2k-official-manual",
    "cp2k-release-source-docs",
    "siesta-official-docs",
    "siesta-release-source-docs",
}

SEED_AUTHORITY_PROVIDERS = {
    (provider["authority_id"], provider["provider_id"])
    for seed_path in sorted(
        (ROOT / "skills").glob("*/references/source-pack-seed.json")
    )
    for provider in json.loads(seed_path.read_text(encoding="utf-8"))["providers"]
}
ACTIVE_AUTHORITIES = {
    authority_id for authority_id, _provider_id in SEED_AUTHORITY_PROVIDERS
}


class OfficialSourceAuthorityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.authorities = official_source_authorities.load_registry()
        cls.software = load_yaml_strict(
            ROOT / "registry" / "software-registry.yaml",
            "software-registry.yaml",
        )

    def errors(self, value=None, software=None) -> list[str]:
        return official_source_authorities.validation_errors(
            value or self.authorities,
            software_data=software or self.software,
            source_root=ROOT,
        )

    def test_repository_registry_exactly_covers_active_and_planned_providers(self) -> None:
        self.assertEqual(self.errors(), [])
        entries = self.authorities["authorities"]
        active = {name for name, item in entries.items() if item["lifecycle"] == "active"}
        planned = {name for name, item in entries.items() if item["lifecycle"] == "planned"}
        self.assertEqual(active, ACTIVE_AUTHORITIES)
        self.assertEqual(
            {
                (authority_id, entries[authority_id]["provider_id"])
                for authority_id in active
            },
            SEED_AUTHORITY_PROVIDERS,
        )
        self.assertEqual(len(planned), 19)
        self.assertEqual(
            {entries[name]["provider_id"] for name in planned},
            set(self.software["planned_software"]),
        )

    def test_active_projection_is_frozen_and_excludes_every_placeholder(self) -> None:
        projection = official_source_authorities.active_authority_technical_snapshot(
            self.authorities,
            software_data=self.software,
            source_root=ROOT,
        )
        self.assertEqual(set(projection), ACTIVE_AUTHORITIES)
        expected_fields = {
            "lifecycle",
            "provider_class",
            "provider_id",
            "allowed_https_origins",
            "allowed_path_prefixes",
            "allowed_query_urls",
            "locator_policy",
            "canonical_urls",
            "source_kinds",
            "version_scopes",
            "content_identity_policy",
            "canonical_snapshot",
        }
        for authority_id, entry in projection.items():
            with self.subTest(authority_id=authority_id):
                self.assertEqual(set(entry), expected_fields)
                self.assertEqual(entry["lifecycle"], "active")
                self.assertIn(
                    entry["provider_class"],
                    {
                        "software",
                        "standard",
                        "platform",
                        "repository",
                        "model-artifact",
                        "dataset",
                        "publisher",
                    },
                )
                self.assertTrue(entry["allowed_https_origins"])
                self.assertTrue(entry["allowed_path_prefixes"])
                self.assertTrue(entry["version_scopes"])
                if authority_id == "vasp-official-wiki":
                    self.assertEqual(len(entry["allowed_query_urls"]), 81)
                else:
                    self.assertEqual(entry["allowed_query_urls"], [])

        cp2k = projection["cp2k-official-manual"]["canonical_snapshot"]
        self.assertEqual(
            set(cp2k),
            {
                "snapshot_id",
                "manifest_raw_sha256",
                "index_raw_sha256",
                "integrity_verified",
                "upstream_source_count",
                "upstream_universe_complete",
                "upstream_sources_by_id",
                "curated_source_count",
                "sources_by_id",
            },
        )
        self.assertIs(cp2k["integrity_verified"], False)
        self.assertIs(cp2k["upstream_universe_complete"], True)
        self.assertEqual(cp2k["upstream_source_count"], 3030)
        self.assertEqual(len(cp2k["upstream_sources_by_id"]), 3030)
        self.assertEqual(cp2k["curated_source_count"], 86)
        self.assertEqual(len(cp2k["sources_by_id"]), 86)
        for source in cp2k["sources_by_id"].values():
            self.assertEqual(
                set(source),
                {
                    "canonical_url",
                    "version_scope",
                    "raw_sha256",
                    "raw_bytes",
                    "raw_integrity_verified",
                    "topic_alias",
                    "derived_snapshot",
                },
            )
            self.assertIs(source["raw_integrity_verified"], False)
            self.assertIs(source["derived_snapshot"]["integrity_verified"], False)
            self.assertNotEqual(
                source["raw_sha256"],
                source["derived_snapshot"]["sha256"],
            )
        for authority_id in ACTIVE_AUTHORITIES - {"cp2k-official-manual"}:
            self.assertIsNone(projection[authority_id]["canonical_snapshot"])
        projection["qe-official-docs"]["version_scopes"][0]["exact_version"] = "tampered"
        self.assertEqual(
            self.authorities["authorities"]["qe-official-docs"]["version_policy"][
                "registered_scopes"
            ][0]["exact_version"],
            "7.5",
        )

    def test_planned_authority_cannot_claim_technical_origin_or_version(self) -> None:
        invalid = copy.deepcopy(self.authorities)
        entry = invalid["authorities"]["gaussian-official-reference"]
        entry["allowed_https_origins"] = ["https://example.invalid"]
        entry["version_policy"]["allowed_scopes"] = ["unversioned"]
        failures = self.errors(invalid)
        self.assertTrue(any("planned authority must not claim" in item for item in failures))

    def test_active_locator_and_content_identity_policy_fail_closed(self) -> None:
        invalid = copy.deepcopy(self.authorities)
        entry = invalid["authorities"]["qe-official-docs"]
        entry["allowed_https_origins"] = ["http://www.quantum-espresso.org"]
        entry["content_policy"]["allowed_path_prefixes"] = ["/Doc/../private/"]
        entry["canonical_snapshot"] = {
            "snapshot_id": "untrusted",
            "manifest_path": "skills/qe-rigorous-calculations/manifest.json",
            "manifest_raw_sha256": "0" * 64,
            "artifact_basis": "snapshot-file-exact-bytes",
        }
        failures = self.errors(invalid)
        self.assertTrue(any("canonical HTTPS origin" in item for item in failures))
        self.assertTrue(any("invalid absolute path prefix" in item for item in failures))
        self.assertTrue(any("forbids a snapshot" in item for item in failures))

    def test_nonproduction_policy_metadata_is_not_read_or_projected(self) -> None:
        mutated = copy.deepcopy(self.authorities)
        entry = mutated["authorities"]["qe-official-docs"]
        entry["license_policy"] = {"deliberately": "not-a-policy-contract"}
        entry["redistribution_policy"] = ["not", "a", "mapping"]
        entry["provenance"] = object()
        self.assertEqual(self.errors(mutated), [])
        projection = official_source_authorities.active_authority_technical_snapshot(
            mutated,
            software_data=self.software,
            source_root=ROOT,
        )
        self.assertNotIn("license_policy", projection["qe-official-docs"])
        self.assertNotIn("redistribution_policy", projection["qe-official-docs"])
        self.assertNotIn("provenance", projection["qe-official-docs"])

    def test_authority_urls_reject_parser_ambiguity_and_origin_spoofing(self) -> None:
        cases = (
            "https://user@www.quantum-espresso.org",
            "https://www.quantum-espresso.org:444",
            "https://www.quantum-espresso.org?q=x",
            "https://www.quantum-espresso.org#fragment",
            "https://127.0.0.1",
            "https://localhost",
        )
        for value in cases:
            with self.subTest(value=value):
                invalid = copy.deepcopy(self.authorities)
                invalid["authorities"]["qe-official-docs"][
                    "allowed_https_origins"
                ] = [value]
                self.assertTrue(self.errors(invalid))

    def test_vasp_exact_query_allowlist_matches_compact_catalog(self) -> None:
        compact = json.loads(
            (
                ROOT
                / "skills/vasp-rigorous-calculations/references/"
                "source-pack-input-catalog.json"
            ).read_text(encoding="utf-8")
        )
        expected = sorted(
            item["api_request_url"] for item in compact["pages"]
        )
        self.assertEqual(len(expected), 81)
        self.assertEqual(len(expected), len(set(expected)))

        policy = self.authorities["authorities"]["vasp-official-wiki"][
            "content_policy"
        ]
        self.assertEqual(policy["query_policy"], "exact-allowlist")
        self.assertEqual(policy["allowed_query_urls"], expected)

        projection = official_source_authorities.active_authority_snapshot(
            self.authorities,
            software_data=self.software,
            source_root=ROOT,
        )
        self.assertEqual(
            projection["vasp-official-wiki"]["allowed_query_urls"],
            expected,
        )
        for authority_id, entry in self.authorities["authorities"].items():
            if authority_id == "vasp-official-wiki":
                continue
            self.assertEqual(
                entry["content_policy"]["query_policy"],
                "forbidden",
            )
            self.assertEqual(
                entry["content_policy"]["allowed_query_urls"],
                [],
            )

    def test_query_policy_and_exact_url_list_shape_fail_closed(self) -> None:
        forbidden_nonempty = copy.deepcopy(self.authorities)
        forbidden_policy = forbidden_nonempty["authorities"][
            "qe-official-docs"
        ]["content_policy"]
        forbidden_policy["allowed_query_urls"] = [
            "https://www.quantum-espresso.org/Doc/index.php?a=1"
        ]
        self.assertTrue(
            any(
                "forbidden query policy requires an empty list" in item
                for item in self.errors(forbidden_nonempty)
            )
        )

        exact_empty = copy.deepcopy(self.authorities)
        exact_empty["authorities"]["vasp-official-wiki"][
            "content_policy"
        ]["allowed_query_urls"] = []
        self.assertTrue(
            any(
                "expected a nonempty string list" in item
                for item in self.errors(exact_empty)
            )
        )

        duplicate = copy.deepcopy(self.authorities)
        duplicate_urls = duplicate["authorities"]["vasp-official-wiki"][
            "content_policy"
        ]["allowed_query_urls"]
        duplicate_urls.append(duplicate_urls[0])
        self.assertTrue(
            any(
                "duplicate values are forbidden" in item
                for item in self.errors(duplicate)
            )
        )

        unsorted = copy.deepcopy(self.authorities)
        unsorted_urls = unsorted["authorities"]["vasp-official-wiki"][
            "content_policy"
        ]["allowed_query_urls"]
        unsorted_urls[0], unsorted_urls[1] = (
            unsorted_urls[1],
            unsorted_urls[0],
        )
        self.assertTrue(
            any(
                "exact URLs must be sorted by raw URL" in item
                for item in self.errors(unsorted)
            )
        )

    def test_exact_query_allowlist_rejects_ambiguous_or_outside_urls(self) -> None:
        original = self.authorities["authorities"]["vasp-official-wiki"][
            "content_policy"
        ]["allowed_query_urls"][0]
        cases = {
            "duplicate-query-key": (
                original + "&oldid=16120",
                "canonical query-bearing HTTPS URL",
            ),
            "alternate-percent-encoding": (
                original.replace("%7C", "%7c", 1),
                "canonical query-bearing HTTPS URL",
            ),
            "userinfo": (
                original.replace(
                    "https://www.vasp.at/",
                    "https://user@www.vasp.at/",
                    1,
                ),
                "canonical query-bearing HTTPS URL",
            ),
            "fragment": (
                original + "#section",
                "canonical query-bearing HTTPS URL",
            ),
            "wrong-origin": (
                original.replace(
                    "https://www.vasp.at/",
                    "https://evil.example/",
                    1,
                ),
                "outside the authority origin/path policy",
            ),
            "wrong-path": (
                original.replace("/wiki/api.php", "/private/api.php", 1),
                "outside the authority origin/path policy",
            ),
        }
        for label, (replacement, expected) in cases.items():
            with self.subTest(label=label):
                invalid = copy.deepcopy(self.authorities)
                urls = invalid["authorities"]["vasp-official-wiki"][
                    "content_policy"
                ]["allowed_query_urls"]
                urls[0] = replacement
                urls.sort()
                self.assertTrue(
                    any(expected in item for item in self.errors(invalid))
                )

    def test_active_authority_cannot_be_unresolved_or_claim_a_missing_pin(self) -> None:
        unresolved = copy.deepcopy(self.authorities)
        unresolved["authorities"]["qe-official-docs"]["content_identity_policy"][
            "mode"
        ] = "unresolved"
        self.assertTrue(
            any("implemented resolution mode" in item for item in self.errors(unresolved))
        )

        missing = copy.deepcopy(self.authorities)
        missing["authorities"]["cp2k-official-manual"]["canonical_snapshot"] = None
        self.assertTrue(
            any("pinned mode requires" in item for item in self.errors(missing))
        )

    def test_identity_pin_is_independent_of_nonproduction_policy_metadata(self) -> None:
        mutated = copy.deepcopy(self.authorities)
        entry = mutated["authorities"]["cp2k-official-manual"]
        entry["license_policy"] = None
        entry["redistribution_policy"] = None
        projection = official_source_authorities.active_authority_technical_snapshot(
            mutated,
            software_data=self.software,
            source_root=ROOT,
        )
        self.assertIs(
            projection["cp2k-official-manual"]["canonical_snapshot"][
                "integrity_verified"
            ],
            False,
        )

    def test_canonical_manifest_digest_is_verified_from_exact_bytes(self) -> None:
        invalid = copy.deepcopy(self.authorities)
        invalid["authorities"]["cp2k-official-manual"]["canonical_snapshot"][
            "manifest_raw_sha256"
        ] = "0" * 64
        failures = self.errors(invalid)
        self.assertTrue(any("declared digest does not match exact bytes" in item for item in failures))

    def test_canonical_manifest_parser_rejects_duplicate_bom_nan_and_nonobject(self) -> None:
        cases = (
            b'{"x":1,"x":2}',
            b"\xef\xbb\xbf{}",
            b'{"x":NaN}',
            b"[]",
        )
        for raw in cases:
            with self.subTest(raw=raw[:8]):
                value, error = official_source_authorities._load_json_object_strict(raw)
                self.assertIsNone(value)
                self.assertIsInstance(error, str)

    def test_software_provider_authority_lifecycle_is_independently_gated(
        self,
    ) -> None:
        invalid = copy.deepcopy(self.authorities)
        invalid["authorities"]["gromacs-official-reference"][
            "provider_id"
        ] = "unknown-engine"
        failures = self.errors(invalid)
        self.assertTrue(
            any(
                "software-class authority providers must exist" in item
                for item in failures
            )
        )

        missing_active = copy.deepcopy(self.authorities)
        for authority_id in (
            "qe-official-docs",
            "qe-release-source-docs",
        ):
            missing_active["authorities"][authority_id][
                "provider_id"
            ] = "cp2k"
        self.assertTrue(
            any(
                "every active software provider requires at least one active"
                in item
                for item in self.errors(missing_active)
            )
        )

        missing_planned = copy.deepcopy(self.authorities)
        for authority_id in tuple(missing_planned["authorities"]):
            if (
                missing_planned["authorities"][authority_id]["provider_id"]
                == "gromacs"
            ):
                missing_planned["authorities"].pop(authority_id)
        self.assertTrue(
            any(
                "every planned software provider requires at least one active "
                "or planned" in item
                for item in self.errors(missing_planned)
            )
        )

    def test_active_authority_does_not_promote_planned_software(self) -> None:
        expanded = copy.deepcopy(self.authorities)
        active = copy.deepcopy(
            expanded["authorities"]["qe-official-docs"]
        )
        active["display_name"] = "Gaussian verified official source"
        active["provider_id"] = "gaussian"
        expanded["authorities"]["gaussian-verified-source"] = active
        self.assertEqual(self.errors(expanded), [])
        projection = official_source_authorities.active_authority_snapshot(
            expanded,
            software_data=self.software,
            source_root=ROOT,
        )
        self.assertIn("gaussian-verified-source", projection)
        self.assertEqual(
            self.software["planned_software"]["gaussian"]["lifecycle"],
            "planned",
        )

    def test_nonsoftware_authority_has_an_independent_provider_namespace(
        self,
    ) -> None:
        expanded = copy.deepcopy(self.authorities)
        standard = copy.deepcopy(
            expanded["authorities"]["qe-official-docs"]
        )
        standard["display_name"] = "JSON Schema official standard"
        standard["provider_class"] = "standard"
        standard["provider_id"] = "json-schema"
        expanded["authorities"]["json-schema-standard"] = standard
        self.assertEqual(self.errors(expanded), [])
        projection = official_source_authorities.active_authority_snapshot(
            expanded,
            software_data=self.software,
            source_root=ROOT,
        )
        self.assertEqual(
            projection["json-schema-standard"]["provider_class"],
            "standard",
        )

        unsupported = copy.deepcopy(expanded)
        unsupported["authorities"]["json-schema-standard"][
            "provider_class"
        ] = "unknown-kind"
        self.assertTrue(
            any(
                "unsupported provider class" in item
                for item in self.errors(unsupported)
            )
        )

    def test_duplicate_secret_key_is_rejected_without_echoing_it(self) -> None:
        secret = "private_authority_token"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "official-source-authorities.yaml"
            path.write_text(
                f"schema_version: '1.0'\n{secret}: one\n{secret}: two\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(RegistryYAMLError, "YAML_DUPLICATE_KEY") as caught:
                official_source_authorities.load_registry(path)
        self.assertNotIn(secret, str(caught.exception))

    def test_shared_snapshot_hashes_exact_authority_bytes(self) -> None:
        with ExitStack() as stack:
            for name in (
                "environment_validation_errors",
                "interface_validation_errors",
                "skill_validation_errors",
                "software_validation_errors",
                "consumer_registry_validation_errors",
                "expectation_registry_validation_errors",
                "storage_discovery_validation_errors",
                "operation_validation_findings",
            ):
                stack.enter_context(
                    mock.patch.object(registry_snapshot, name, return_value=[])
                )
            snapshot = registry_snapshot.load_registry_snapshot(ROOT)
        raw = (ROOT / "registry" / "official-source-authorities.yaml").read_bytes()
        self.assertEqual(
            snapshot.registry_sha256["official-source-authorities.yaml"],
            hashlib.sha256(raw).hexdigest(),
        )
        self.assertEqual(
            set(snapshot.active_official_source_authorities()),
            ACTIVE_AUTHORITIES,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
