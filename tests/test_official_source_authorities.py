from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import official_source_authorities  # noqa: E402
from registry_snapshot import load_registry_snapshot  # noqa: E402
from registry_yaml import RegistryYAMLError, load_yaml_strict  # noqa: E402


ACTIVE_AUTHORITIES = {
    "qe-official-docs",
    "vasp-official-wiki",
    "cp2k-official-manual",
    "siesta-official-docs",
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
        self.assertEqual(len(planned), 19)
        self.assertEqual(
            {entries[name]["provider_id"] for name in planned},
            set(self.software["planned_software"]),
        )

    def test_active_projection_is_frozen_and_excludes_every_placeholder(self) -> None:
        projection = official_source_authorities.active_authority_snapshot(
            self.authorities,
            software_data=self.software,
            source_root=ROOT,
        )
        self.assertEqual(set(projection), ACTIVE_AUTHORITIES)
        expected_fields = {
            "lifecycle",
            "provider_id",
            "allowed_https_origins",
            "allowed_path_prefixes",
            "locator_policy",
            "canonical_urls",
            "source_kinds",
            "version_scopes",
            "content_identity_policy",
            "canonical_snapshot",
            "license_status",
            "license_identifier",
            "license_terms_urls",
            "redistribution",
        }
        for authority_id, entry in projection.items():
            with self.subTest(authority_id=authority_id):
                self.assertEqual(set(entry), expected_fields)
                self.assertEqual(entry["lifecycle"], "active")
                self.assertTrue(entry["allowed_https_origins"])
                self.assertTrue(entry["allowed_path_prefixes"])
                self.assertTrue(entry["version_scopes"])

        cp2k = projection["cp2k-official-manual"]["canonical_snapshot"]
        self.assertEqual(
            set(cp2k),
            {"snapshot_id", "manifest_raw_sha256", "integrity_verified", "sources_by_id"},
        )
        self.assertIs(cp2k["integrity_verified"], True)
        self.assertEqual(len(cp2k["sources_by_id"]), 86)
        for authority_id in ACTIVE_AUTHORITIES - {"cp2k-official-manual"}:
            self.assertIsNone(projection[authority_id]["canonical_snapshot"])
        self.assertEqual(
            {
                authority_id: entry["license_status"]
                for authority_id, entry in projection.items()
            },
            {
                "qe-official-docs": "unknown",
                "vasp-official-wiki": "known-restricted",
                "cp2k-official-manual": "known-open",
                "siesta-official-docs": "known-restricted",
            },
        )
        self.assertEqual(projection["qe-official-docs"]["redistribution"], ["unknown"])
        self.assertIsNone(projection["qe-official-docs"]["license_identifier"])
        self.assertEqual(projection["qe-official-docs"]["license_terms_urls"], [])
        self.assertEqual(
            {
                authority_id: (
                    entry["license_identifier"],
                    entry["license_terms_urls"],
                )
                for authority_id, entry in projection.items()
                if authority_id != "qe-official-docs"
            },
            {
                "vasp-official-wiki": (
                    "VASP website terms of use",
                    ["https://vasp.at/footer/termsofuse/"],
                ),
                "cp2k-official-manual": (
                    "GPL-2.0-or-later",
                    ["https://github.com/cp2k/cp2k/blob/master/LICENSE"],
                ),
                "siesta-official-docs": (
                    "CC-BY-NC-SA-4.0",
                    [
                        "https://gitlab.com/siesta-project/documentation/siesta-docs/-/blob/master/LICENSE"
                    ],
                ),
            },
        )
        self.assertEqual(projection["cp2k-official-manual"]["redistribution"], ["redistributable"])
        for authority_id in {"vasp-official-wiki", "siesta-official-docs"}:
            self.assertEqual(
                projection[authority_id]["redistribution"],
                ["runtime-only", "restricted"],
            )

        projection["qe-official-docs"]["version_scopes"][0]["exact_version"] = "tampered"
        self.assertEqual(
            self.authorities["authorities"]["qe-official-docs"]["version_policy"][
                "registered_scopes"
            ][0]["exact_version"],
            "7.5",
        )

    def test_planned_authority_cannot_claim_origin_version_or_license(self) -> None:
        invalid = copy.deepcopy(self.authorities)
        entry = invalid["authorities"]["gaussian-official-reference"]
        entry["allowed_https_origins"] = ["https://example.invalid"]
        entry["version_policy"]["allowed_scopes"] = ["unversioned"]
        entry["license_policy"]["status"] = "known-open"
        failures = self.errors(invalid)
        self.assertTrue(any("planned authority must not claim" in item for item in failures))
        self.assertTrue(any("planned authority must remain unresolved" in item for item in failures))

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

    def test_fact_urls_are_bound_to_locator_or_exact_license_terms(self) -> None:
        invalid = copy.deepcopy(self.authorities)
        invalid["authorities"]["qe-official-docs"]["provenance"]["official_fact_urls"] = [
            "https://www.quantum-espresso.org/unrelated/"
        ]
        failures = self.errors(invalid)
        self.assertTrue(any("outside authority locator policy" in item for item in failures))

        encoded = copy.deepcopy(self.authorities)
        encoded["authorities"]["vasp-official-wiki"]["license_policy"]["terms_urls"] = [
            "https://vasp.at/footer/%2e%2e/private/"
        ]
        self.assertTrue(any("public HTTPS URL" in item for item in self.errors(encoded)))

    def test_authority_urls_reject_parser_ambiguity_and_origin_spoofing(self) -> None:
        cases = (
            "https://user@www.quantum-espresso.org/Doc/",
            "https://www.quantum-espresso.org:444/Doc/",
            "https://www.quantum-espresso.org.evil.example/Doc/",
            "https://www.quantum-espresso.org/Doc/?q=x",
            "https://www.quantum-espresso.org/Doc/#fragment",
            "https://www.quantum-espresso.org/Doc/%2e%2e/private/",
            "https://www.quantum-espresso.org/Doc/../private/",
            "https://www.quantum-espresso.org/Doc\\private/",
        )
        for value in cases:
            with self.subTest(value=value):
                invalid = copy.deepcopy(self.authorities)
                invalid["authorities"]["qe-official-docs"]["provenance"][
                    "official_fact_urls"
                ] = [value]
                self.assertTrue(self.errors(invalid))

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

    def test_provider_lifecycle_is_owned_by_software_registry(self) -> None:
        invalid = copy.deepcopy(self.authorities)
        invalid["authorities"]["gromacs-official-reference"]["provider_id"] = "gaussian"
        failures = self.errors(invalid)
        self.assertTrue(any("planned provider_id values must be unique" in item for item in failures))
        self.assertTrue(any("planned providers must exactly match" in item for item in failures))

        software = copy.deepcopy(self.software)
        software["software"]["qe"]["lifecycle"] = "deprecated"
        self.assertTrue(
            any("active providers must exactly match" in item for item in self.errors(software=software))
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
        snapshot = load_registry_snapshot(ROOT)
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
