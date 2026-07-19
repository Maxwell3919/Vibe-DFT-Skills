from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import environment_profiles  # noqa: E402


EXPECTED_PROVIDERS = {
    "catmap-v041",
    "deepmd-cpu-macos",
    "fairchem-v1-equiformer-v2",
    "fairchem-v1-gemnet-oc",
    "fairchem-v2-uma",
    "gaussian-g16-c02",
    "gpumd-cuda",
    "gpumd-rocm",
    "gromacs-cpu",
    "lammps-cpu",
    "lasp-commercial",
    "lobster-5",
    "mace-python",
    "multiwfn-community-macos",
    "multiwfn-official-linux-x64",
    "nequip-python",
    "ovito-basic",
    "ovito-pro",
    "phonopy-pypi",
    "pymatgen-core",
    "pymatgen-wrapper",
    "rdkit-pypi",
    "vaspkit-linux-x64",
    "vaspkit-macos-intel",
}


class EnvironmentProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = environment_profiles.load_registry()

    def errors(self, mutation) -> list[str]:
        candidate = copy.deepcopy(self.registry)
        mutation(candidate)
        return environment_profiles.validation_errors(candidate)

    @staticmethod
    def attestation(provider_id: str, software_version: str) -> dict:
        record = {
            "attestation_id": f"att-{provider_id}-20260718",
            "issued_on": "2026-07-18",
            "provider_id": provider_id,
            "software_version": software_version,
            "user_authorized": True,
            "legal_use_confirmed": True,
            "installation_scope": "runtime-local",
            "verification_method": "user-authorized-hash-bound",
            "authorization_evidence_sha256": "1" * 64,
            "binary_sha256": "2" * 64,
            "capability_evidence_sha256": "3" * 64,
            "binary_redistribution": False,
            "manual_redistribution": False,
            "fixture_redistribution": False,
        }
        canonical = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        record["attestation_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return record

    @staticmethod
    def rehash_attestation(record: dict) -> None:
        payload = {key: value for key, value in record.items() if key != "attestation_sha256"}
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        record["attestation_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def declare_restricted_receipt(self, data: dict, provider_id: str) -> dict:
        profile = data["profiles"][provider_id]
        profile["authorization"] = {
            "required": True,
            "provenance": "declared-requires-external-trust",
            "receipt": self.attestation(provider_id, profile["software"]["version"]),
        }
        return profile

    def test_registry_is_valid_and_covers_every_provider_split(self) -> None:
        self.assertEqual(environment_profiles.validation_errors(self.registry), [])
        self.assertEqual(set(self.registry["profiles"]), EXPECTED_PROVIDERS)
        self.assertEqual(len(EXPECTED_PROVIDERS), 24)

    def test_load_registry_has_a_shared_strict_yaml_loader_injection_seam(self) -> None:
        selected = ROOT / "registry" / "environment-profiles.yaml"
        loaded_paths: list[Path] = []

        def strict_loader(path: Path) -> object:
            loaded_paths.append(path)
            return copy.deepcopy(self.registry)

        loaded = environment_profiles.load_registry(selected, yaml_loader=strict_loader)
        self.assertEqual(loaded, self.registry)
        self.assertEqual(loaded_paths, [selected])

    def assert_cli_yaml_error(self, filename: str, content: str, expected: str) -> None:
        command = [sys.executable, str(ROOT / "tools" / "environment_profiles.py")]
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory) / filename
            candidate.write_text(content, encoding="utf-8")
            rejected = subprocess.run(
                command + ["--registry", str(candidate)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(rejected.returncode, 2)
            self.assertEqual(rejected.stdout, "")
            self.assertEqual(rejected.stderr, f"ERROR: {expected}\n")
            self.assertNotIn("Traceback", rejected.stderr)
            self.assertNotIn(str(candidate), rejected.stderr)
            self.assertNotIn(str(Path(directory).resolve()), rejected.stderr)

    def test_cli_rejects_nested_duplicate_yaml_with_a_stable_private_error(self) -> None:
        self.assert_cli_yaml_error(
            "duplicate.yaml",
            "root:\n  nested:\n    status: one\n    status: two\n",
            "YAML_DUPLICATE_KEY duplicate.yaml: duplicate mapping key",
        )

    def test_cli_rejects_unsafe_yaml_tag_with_a_stable_private_error(self) -> None:
        self.assert_cli_yaml_error(
            "unsafe.yaml",
            "root: !!python/object/apply:os.system ['echo not-executed']\n",
            "YAML_UNSAFE_TAG unsafe.yaml: unsupported or unsafe YAML tag",
        )

    def test_cli_rejects_nonmapping_yaml_root_with_a_stable_private_error(self) -> None:
        self.assert_cli_yaml_error(
            "nonmapping.yaml",
            "- item\n",
            "YAML_ROOT_NOT_MAPPING nonmapping.yaml: document root must be a mapping",
        )

    def test_registry_is_an_immutable_dated_machine_snapshot(self) -> None:
        self.assertEqual(
            self.registry["snapshot"],
            {
                "kind": "fixed-current-machine-observation",
                "observed_on": "2026-07-18",
                "machine_class": "apple-silicon-macos",
                "dynamic_detection": False,
            },
        )

        def mutate(data) -> None:
            data["snapshot"]["dynamic_detection"] = True

        self.assertTrue(any("dynamic_detection" in item for item in self.errors(mutate)))

    def test_current_machine_caps_are_fail_closed(self) -> None:
        profiles = self.registry["profiles"]
        self.assertEqual(profiles["pymatgen-wrapper"]["maximum_validation_level"], "environment-verified")
        self.assertEqual(profiles["pymatgen-core"]["current_machine"]["status"], "version-mismatch")
        self.assertTrue(
            all(
                profile["maximum_validation_level"] == "planned"
                for name, profile in profiles.items()
                if name != "pymatgen-wrapper"
            )
        )

    def test_empty_software_version_is_rejected(self) -> None:
        failures = self.errors(
            lambda data: data["profiles"]["rdkit-pypi"]["software"].__setitem__("version", "")
        )
        self.assertTrue(any("software/version" in failure for failure in failures))

    def test_non_official_url_domain_is_rejected(self) -> None:
        failures = self.errors(
            lambda data: data["profiles"]["phonopy-pypi"]["official_urls"].append(
                "https://untrusted.example/download"
            )
        )
        self.assertTrue(any("non-official URL domain" in failure for failure in failures))

    def test_provider_authority_rejects_same_domain_owner_and_project_swaps(self) -> None:
        mutations = (
            ("rdkit-pypi", 0, "https://github.com/untrusted/malware"),
            ("pymatgen-wrapper", 1, "https://pypi.org/project/another-project/"),
        )
        for provider_id, index, replacement in mutations:
            with self.subTest(provider_id=provider_id, replacement=replacement):
                candidate = copy.deepcopy(self.registry)
                candidate["profiles"][provider_id]["official_urls"][index] = replacement
                failures = environment_profiles.validation_errors(candidate)
                self.assertTrue(
                    any("URL set differs from reviewed provider authority" in item for item in failures),
                    failures,
                )

    def test_reviewed_github_pypi_and_sourceforge_paths_are_exact(self) -> None:
        mutations = (
            ("rdkit-pypi", 0, "https://github.com/rdkit/rdkit/releases"),
            ("pymatgen-wrapper", 1, "https://pypi.org/project/pymatgen/1.0/"),
            ("vaspkit-linux-x64", 1, "https://sourceforge.net/projects/vaspkit/files/Other/"),
        )
        for provider_id, index, replacement in mutations:
            with self.subTest(provider_id=provider_id, replacement=replacement):
                candidate = copy.deepcopy(self.registry)
                candidate["profiles"][provider_id]["official_urls"][index] = replacement
                failures = environment_profiles.validation_errors(candidate)
                self.assertTrue(
                    any("URL set differs from reviewed provider authority" in item for item in failures),
                    failures,
                )

    def test_reviewed_urls_reject_query_fragment_and_userinfo_drift(self) -> None:
        mutations = (
            ("rdkit-pypi", 0, "https://github.com/rdkit/rdkit/releases/latest?download=1"),
            ("pymatgen-wrapper", 1, "https://pypi.org/project/pymatgen/#files"),
            ("rdkit-pypi", 0, "https://user@github.com/rdkit/rdkit/releases/latest"),
        )
        for provider_id, index, replacement in mutations:
            with self.subTest(provider_id=provider_id, replacement=replacement):
                candidate = copy.deepcopy(self.registry)
                candidate["profiles"][provider_id]["official_urls"][index] = replacement
                failures = environment_profiles.validation_errors(candidate)
                self.assertTrue(
                    any("URL set differs from reviewed provider authority" in item for item in failures),
                    failures,
                )
                if "@" in replacement:
                    self.assertTrue(any("URL user information is forbidden" in item for item in failures))

    def test_new_provider_requires_an_explicit_reviewed_url_mapping(self) -> None:
        def mutate(data) -> None:
            profile = copy.deepcopy(data["profiles"]["rdkit-pypi"])
            profile["provider_id"] = "future-provider"
            data["profiles"]["future-provider"] = profile

        failures = self.errors(mutate)
        self.assertTrue(
            any("provider has no reviewed URL authority mapping" in item for item in failures),
            failures,
        )

    def test_multiwfn_community_source_keeps_its_reviewed_tier_and_url(self) -> None:
        profile = self.registry["profiles"]["multiwfn-community-macos"]
        self.assertEqual(
            profile["source_tier"],
            "third-party-community-referenced-by-official",
        )
        self.assertEqual(profile["official_urls"], ["http://sobereva.com/multiwfn/download.html"])
        self.assertEqual(environment_profiles.validation_errors(self.registry), [])

    def test_profile_role_mismatch_is_rejected(self) -> None:
        failures = self.errors(
            lambda data: data["profiles"]["gromacs-cpu"].__setitem__("role", "structure-library")
        )
        self.assertTrue(any("incompatible with role" in failure for failure in failures))

    def test_license_redistribution_mismatch_is_rejected(self) -> None:
        failures = self.errors(
            lambda data: data["profiles"]["lammps-cpu"]["license"].__setitem__(
                "redistribution", "prohibited"
            )
        )
        self.assertTrue(any("incompatible with redistribution" in failure for failure in failures))

    def test_no_external_trust_keeps_every_restricted_provider_blocked_and_planned(self) -> None:
        restricted = {
            provider_id: profile
            for provider_id, profile in self.registry["profiles"].items()
            if profile["license"]["category"] == "restricted-proprietary"
        }
        self.assertEqual(
            set(restricted),
            {"gaussian-g16-c02", "lasp-commercial", "lobster-5", "ovito-pro"},
        )
        for provider_id, profile in restricted.items():
            with self.subTest(provider_id=provider_id):
                self.assertEqual(
                    profile["authorization"],
                    {
                        "required": True,
                        "provenance": "declared-requires-external-trust",
                        "receipt": None,
                    },
                )
                self.assertEqual(profile["current_machine"]["status"], "restricted-unavailable")
                self.assertEqual(profile["maximum_validation_level"], "planned")
                self.assertTrue(
                    any("external trust" in blocker.lower() for blocker in profile["planned_blockers"])
                )

    def test_restricted_provider_cannot_claim_trust_by_changing_registry_state(self) -> None:
        def mutate(data) -> None:
            profile = data["profiles"]["gaussian-g16-c02"]
            profile["current_machine"]["status"] = "restricted-installed"
            profile["maximum_validation_level"] = "environment-verified"
            profile["planned_blockers"] = ["Only a numerical fixture remains."]

        failures = self.errors(mutate)
        self.assertTrue(any("requires external trust" in failure for failure in failures), failures)
        self.assertTrue(any("external trust blocker" in failure for failure in failures), failures)

    def test_complete_receipt_is_valid_provenance_but_does_not_establish_trust(self) -> None:
        candidate = copy.deepcopy(self.registry)
        profile = self.declare_restricted_receipt(candidate, "gaussian-g16-c02")
        self.assertEqual(profile["current_machine"]["status"], "restricted-unavailable")
        self.assertEqual(profile["maximum_validation_level"], "planned")
        self.assertEqual(environment_profiles.validation_errors(candidate), [])

    def test_self_authored_complete_attestation_never_establishes_external_trust(self) -> None:
        candidate = copy.deepcopy(self.registry)
        profile = self.declare_restricted_receipt(candidate, "gaussian-g16-c02")
        attestation = profile["authorization"]["receipt"]
        self.assertEqual(
            attestation["attestation_sha256"],
            environment_profiles.attestation_digest(attestation),
        )
        profile["current_machine"]["status"] = "restricted-installed"
        profile["maximum_validation_level"] = "environment-verified"
        failures = environment_profiles.validation_errors(candidate)
        self.assertTrue(any("requires external trust" in failure for failure in failures), failures)

    def test_default_machine_summary_reports_all_external_trust_requirements(self) -> None:
        summary = environment_profiles.machine_summary(self.registry)
        self.assertFalse(summary["external_trust_resolver_configured"])
        self.assertEqual(
            summary["requires_external_trust"],
            ["gaussian-g16-c02", "lasp-commercial", "lobster-5", "ovito-pro"],
        )

    def test_restricted_providers_always_prohibit_redistribution(self) -> None:
        restricted = [
            profile
            for profile in self.registry["profiles"].values()
            if profile["license"]["category"] == "restricted-proprietary"
        ]
        self.assertTrue(restricted)
        self.assertTrue(
            all(profile["license"]["redistribution"] == "prohibited" for profile in restricted)
        )

    def test_reviewed_restricted_provider_identity_cannot_be_reclassified(self) -> None:
        def mutate(data) -> None:
            profile = data["profiles"]["ovito-pro"]
            profile.pop("authorization")
            profile["license"]["category"] = "custom"
            profile["license"]["redistribution"] = "not-established"
            profile["current_machine"]["status"] = "unverified"
            profile["maximum_validation_level"] = "planned"

        failures = self.errors(mutate)
        self.assertTrue(
            any("reviewed restricted provider identity" in failure for failure in failures),
            failures,
        )

    def test_receipt_requires_consistent_declarations_scope_and_hash_evidence(self) -> None:
        mutations = (
            ("user_authorized", False, "declaration must be true"),
            ("legal_use_confirmed", False, "declaration must be true"),
            ("installation_scope", "shared-installation", "must be 'runtime-local'"),
            ("authorization_evidence_sha256", "not-a-digest", "expected SHA-256"),
            ("capability_evidence_sha256", "not-a-digest", "expected SHA-256"),
        )
        for field, value, expected in mutations:
            with self.subTest(field=field):
                candidate = copy.deepcopy(self.registry)
                profile = self.declare_restricted_receipt(candidate, "gaussian-g16-c02")
                record = profile["authorization"]["receipt"]
                record[field] = value
                self.rehash_attestation(record)
                failures = environment_profiles.validation_errors(candidate)
                self.assertTrue(any(expected in failure for failure in failures), failures)

    def test_receipt_tampering_and_identity_mismatch_are_rejected(self) -> None:
        def tamper(data) -> None:
            profile = self.declare_restricted_receipt(data, "gaussian-g16-c02")
            profile["authorization"]["receipt"]["software_version"] = "Rev C.01"

        failures = self.errors(tamper)
        self.assertTrue(any("software version must match" in failure for failure in failures))
        self.assertTrue(any("receipt digest mismatch" in failure for failure in failures))

    def test_receipt_cannot_enable_redistribution_or_raise_claim_ceiling(self) -> None:
        def mutate(data) -> None:
            profile = self.declare_restricted_receipt(data, "gaussian-g16-c02")
            attestation = profile["authorization"]["receipt"]
            attestation["binary_redistribution"] = True
            self.rehash_attestation(attestation)
            profile["maximum_validation_level"] = "integration-verified"

        failures = self.errors(mutate)
        self.assertTrue(any("redistribution flags must all be false" in failure for failure in failures))
        self.assertTrue(any("requires external trust and must remain planned" in failure for failure in failures))

    def test_restricted_provider_rejects_nonprohibited_redistribution(self) -> None:
        def mutate(data) -> None:
            profile = data["profiles"]["lasp-commercial"]
            profile["license"]["redistribution"] = "not-established"

        failures = self.errors(mutate)
        self.assertTrue(any("restricted redistribution must be prohibited" in failure for failure in failures))

    def test_invalid_python_bounds_are_rejected(self) -> None:
        failures = self.errors(
            lambda data: data["profiles"]["fairchem-v2-uma"]["environment"]["python"].__setitem__(
                "min_inclusive", "3.14"
            )
        )
        self.assertTrue(any("minimum must be below maximum" in failure for failure in failures))

    def test_current_platform_semantics_are_rejected_when_inconsistent(self) -> None:
        failures = self.errors(
            lambda data: data["profiles"]["vaspkit-linux-x64"]["current_machine"].__setitem__(
                "status", "not-installed-compatible"
            )
        )
        self.assertTrue(any("compatible status conflicts with environment" in failure for failure in failures))

    def test_empty_planned_blockers_are_rejected(self) -> None:
        failures = self.errors(
            lambda data: data["profiles"]["mace-python"].__setitem__("planned_blockers", [])
        )
        self.assertTrue(any("planned_blockers: expected a nonempty list" in failure for failure in failures))

    def test_sensitive_identity_field_is_rejected(self) -> None:
        def mutate(data) -> None:
            data["profiles"]["phonopy-pypi"]["current_machine"]["account"] = "researcher"

        failures = self.errors(mutate)
        self.assertTrue(any("sensitive identity or location field" in failure for failure in failures))

    def test_real_local_location_is_rejected(self) -> None:
        failures = self.errors(
            lambda data: data["profiles"]["phonopy-pypi"]["current_machine"]["observations"].append(
                "Installed under /Users/researcher/private-environment"
            )
        )
        self.assertTrue(any("real local filesystem location" in failure for failure in failures))

    def test_runtime_probe_execution_policy_is_an_exact_machine_enum(self) -> None:
        failures = self.errors(
            lambda data: data["profiles"]["rdkit-pypi"]["runtime_probe"].__setitem__(
                "execution_policy", "network"
            )
        )
        self.assertTrue(
            any("must be 'documentary-read-only'" in failure for failure in failures),
            failures,
        )

    def test_runtime_probe_legacy_side_effects_field_is_rejected(self) -> None:
        def mutate(data) -> None:
            probe = data["profiles"]["rdkit-pypi"]["runtime_probe"]
            probe["side_effects"] = probe.pop("execution_policy")

        failures = self.errors(mutate)
        self.assertTrue(any("runtime_probe" in failure and "side_effects" in failure for failure in failures))

    def test_community_provider_cannot_be_marked_verified(self) -> None:
        def mutate(data) -> None:
            profile = data["profiles"]["multiwfn-community-macos"]
            profile["current_machine"]["status"] = "installed-compatible"
            profile["maximum_validation_level"] = "environment-verified"

        failures = self.errors(mutate)
        self.assertTrue(any("community provider must remain unverified and planned" in failure for failure in failures))

    def test_cli_returns_zero_for_registry_and_two_for_mutation(self) -> None:
        command = [sys.executable, str(ROOT / "tools" / "environment_profiles.py")]
        valid = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(valid.returncode, 0, valid.stderr)
        self.assertEqual(
            json.loads(valid.stdout),
            {
                "registry_valid": True,
                "dynamic_detection": False,
                "software_executed": False,
                "external_trust_resolver_configured": False,
                "requires_external_trust": [
                    "gaussian-g16-c02",
                    "lasp-commercial",
                    "lobster-5",
                    "ovito-pro",
                ],
                "profile_count": 24,
                "current_status_counts": {
                    "installed-compatible": 1,
                    "not-installed-compatible": 5,
                    "restricted-unavailable": 4,
                    "unverified": 4,
                    "unsupported-architecture": 1,
                    "unsupported-hardware": 2,
                    "unsupported-platform": 2,
                    "unsupported-runtime": 4,
                    "version-mismatch": 1,
                },
                "maximum_current_machine_validation_level": "environment-verified",
            },
        )
        self.assertNotIn("PASS", valid.stdout)

        invalid = copy.deepcopy(self.registry)
        invalid["profiles"]["lobster-5"]["planned_blockers"] = []
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory) / "invalid.yaml"
            candidate.write_text(yaml.safe_dump(invalid, sort_keys=False), encoding="utf-8")
            rejected = subprocess.run(
                command + ["--registry", str(candidate)], capture_output=True, text=True
            )
        self.assertEqual(rejected.returncode, 2)
        self.assertIn("planned_blockers", rejected.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
