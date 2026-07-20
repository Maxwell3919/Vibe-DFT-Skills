from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

from skill_registry import source_tree_digest
import validate_promotion


CHECK_IDS = [
    "identity-and-routing",
    "primary-source-provenance",
    "capability-boundary",
    "deterministic-gates",
    "lineage-and-hashes",
    "scientific-gate-separation",
    "shared-interfaces",
    "side-effect-boundary",
    "idempotency-recovery-cancel",
    "validation-evidence",
    "privacy-and-license",
    "portability-and-environment",
    "maintenance-and-forward-test",
]


class PromotionFixture:
    def __init__(self, root: Path) -> None:
        self.root = root
        self._git("init", "-q")
        self._git("config", "user.email", "test@example.invalid")
        self._git("config", "user.name", "Promotion Test")

    def _git(self, *args: str) -> str:
        completed = subprocess.run(
            ["git", "-C", str(self.root), *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            raise AssertionError(completed.stderr)
        return completed.stdout.strip()

    def write(self, path: str, content: str | bytes) -> None:
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            target.write_bytes(content)
        else:
            target.write_text(content, encoding="utf-8")

    def write_json(self, path: str, value: object) -> str:
        raw = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
        self.write(path, raw)
        return hashlib.sha256(raw).hexdigest()

    def commit(self, message: str) -> str:
        self._git("add", "-A")
        self._git("commit", "-q", "-m", message)
        return self._git("rev-parse", "HEAD")

    def show_bytes(self, commit: str, path: str) -> bytes:
        completed = subprocess.run(
            ["git", "-C", str(self.root), "show", f"{commit}:{path}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if completed.returncode != 0:
            raise AssertionError(completed.stderr.decode(errors="replace"))
        return completed.stdout

    def diff_paths(self, base: str, candidate: str) -> list[str]:
        output = self._git("diff", "--name-only", base, candidate, "--")
        return sorted(line for line in output.splitlines() if line)


def _skill_registry(lifecycle: str, source_hash: str) -> str:
    requirements = (
        "    activation_requirements:\n"
        "      software_profiles: []\n"
        "      interface_ids: []\n"
        "      activation_check_ids: []\n"
        "      task_catalog_ids: []\n"
    )
    return (
        'schema_version: "1.0"\n'
        "skills:\n"
        "  example-skill:\n"
        "    display_name: Example Skill\n"
        "    kind: advisory\n"
        f"    lifecycle: {lifecycle}\n"
        "    path: skills/example-skill\n"
        f'    source_tree_sha256: "{source_hash}"\n'
        "    side_effects: []\n"
        "    consumes: []\n"
        "    produces: []\n"
        f"{requirements}"
    )


def _operation_routes(lifecycle: str, routable: bool) -> str:
    return (
        'schema_version: "1.0"\n'
        "routes:\n"
        "  example-skill:\n"
        f"    lifecycle: {lifecycle}\n"
        f"    routable: {'true' if routable else 'false'}\n"
        "    required_reads: [skills/example-skill/SKILL.md]\n"
        f"    first_tool: {'{}' if routable else 'null'}\n"
        f"    tool_sequence: {'{}' if routable else 'null'}\n"
        "    side_effects: []\n"
        "    minimum_evidence: []\n"
        "    maximum_claim: documented_behavior_only\n"
    )


def _maturity(evidence_sha: str) -> dict[str, object]:
    evidence_path = "skills/example-skill/validation/evidence.txt"
    evidence = [
        {
            "evidence_id": "example-invocation",
            "axis": "invocation",
            "maturity_level": "tool-integration-validated",
            "kind": "invocation-tool-integration-test",
            "provider_version": "1.0",
            "source": "skill-local",
            "path": evidence_path,
            "external_record_ref": None,
            "sha256": evidence_sha,
        },
        {
            "evidence_id": "example-parser",
            "axis": "parser",
            "maturity_level": "real-artifact-validated",
            "kind": "parser-real-artifact-test",
            "provider_version": "1.0",
            "source": "skill-local",
            "path": evidence_path,
            "external_record_ref": None,
            "sha256": evidence_sha,
        },
        {
            "evidence_id": "example-science",
            "axis": "scientific_validation",
            "maturity_level": "real-artifact-validated",
            "kind": "scientific-real-artifact-validation",
            "provider_version": "1.0",
            "source": "skill-local",
            "path": evidence_path,
            "external_record_ref": None,
            "sha256": evidence_sha,
        },
    ]
    return {
        "schema_version": "1.1",
        "contract_name": "task-maturity",
        "catalog_id": "example-maturity",
        "skill_id": "example-skill",
        "aggregate": False,
        "routes": [
            {
                "route_id": "example/primary",
                "provider_id": "example-provider",
                "provider_lifecycle": "active",
                "task_id": "example-task",
                "parent_route": None,
                "provider_version": "1.0",
                "implementation": "implemented",
                "invocation_maturity": "tool-integration-validated",
                "parser_maturity": "real-artifact-validated",
                "scientific_validation_maturity": "real-artifact-validated",
                "overall_maturity": {
                    "declared": "real-artifact-validated",
                    "computed": "real-artifact-validated",
                },
                "claim_ceiling": "numerical_candidate_only",
                "advertised": True,
                "execution_capability": True,
                "unknown_version_policy": "block",
                "evidence": evidence,
                "limitations": ["Synthetic promotion-validator integration fixture"],
            }
        ],
        "provenance": {
            "producer": "promotion-test",
            "producer_version": "1.0",
            "generated_utc": "2026-07-21T00:00:00Z",
        },
    }


def _activation(candidate: str, evidence_sha: str, *, corrupt_hash: bool) -> dict[str, object]:
    selected_hash = "0" * 64 if corrupt_hash else evidence_sha
    checks = []
    for index, check_id in enumerate(CHECK_IDS):
        checks.append(
            {
                "check_id": check_id,
                "status": "pass",
                "evidence": [
                    {
                        "evidence_id": f"evidence-{index:02d}",
                        "kind": "test-report",
                        "path": "skills/example-skill/validation/evidence.txt",
                        "sha256": selected_hash,
                    }
                ],
                "reviewer": {
                    "reviewer_id": f"reviewer-{index:02d}",
                    "role": "independent-technical-reviewer",
                    "independent_of_implementation": True,
                },
                "validated_utc": "2026-07-21T00:00:00Z",
                "not_applicable_reason": None,
                "limitations": [],
            }
        )
    return {
        "schema_version": "1.1",
        "contract_name": "activation-checklist",
        "checklist_id": "example-activation",
        "subject": {
            "skill_id": "example-skill",
            "software_ids": [],
            "candidate_commit": candidate,
        },
        "profile_ids": ["example-profile"],
        "checks": checks,
        "summary": {
            "decision": "eligible",
            "blocker_check_ids": [],
            "limitations": [],
        },
        "provenance": {
            "producer": "promotion-test",
            "producer_version": "1.0",
            "generated_utc": "2026-07-21T00:00:00Z",
        },
    }


class PromotionValidatorTests(unittest.TestCase):
    def _build(
        self,
        root: Path,
        *,
        omit_candidate_path: bool = False,
        corrupt_source_hash: bool = False,
        corrupt_evidence_hash: bool = False,
        review_escape: bool = False,
    ) -> tuple[Path, str]:
        fixture = PromotionFixture(root)
        fixture.write("skills/example-skill/SKILL.md", "development\n")
        base_source_hash = source_tree_digest(root / "skills" / "example-skill").sha256
        fixture.write("registry/skill-registry.yaml", _skill_registry("development", base_source_hash))
        fixture.write("registry/interface-registry.yaml", 'schema_version: "1.0"\ninterfaces: {}\n')
        fixture.write("registry/operation-routes.yaml", _operation_routes("development", False))
        fixture.write(
            "registry/software-registry.yaml",
            'schema_version: "1.0"\naggregate_codes: []\nsoftware: {}\nplanned_software: {}\n',
        )
        fixture.write(
            "registry/environment-profiles.yaml",
            'schema_version: "1.0"\nas_of: "2026-07-21"\nsnapshot: {}\nprofiles: {}\n',
        )
        base = fixture.commit("base development state")
        base_registry_sha = hashlib.sha256(
            fixture.show_bytes(base, "registry/skill-registry.yaml")
        ).hexdigest()

        evidence_raw = b"synthetic promotion evidence\n"
        evidence_sha = hashlib.sha256(evidence_raw).hexdigest()
        fixture.write("skills/example-skill/SKILL.md", "active candidate\n")
        fixture.write("skills/example-skill/validation/evidence.txt", evidence_raw)
        maturity_path = "skills/example-skill/references/task-maturity.json"
        maturity_sha = fixture.write_json(maturity_path, _maturity(evidence_sha))
        candidate_source_hash = source_tree_digest(root / "skills" / "example-skill").sha256
        recorded_source_hash = "0" * 64 if corrupt_source_hash else candidate_source_hash
        fixture.write("registry/skill-registry.yaml", _skill_registry("active", recorded_source_hash))
        fixture.write(
            "registry/interface-registry.yaml",
            '# candidate routing review\nschema_version: "1.0"\ninterfaces: {}\n',
        )
        fixture.write("registry/operation-routes.yaml", _operation_routes("active", True))
        candidate = fixture.commit("candidate source state")
        candidate_diff = fixture.diff_paths(base, candidate)
        domain = [path for path in candidate_diff if path.startswith("skills/example-skill/")]
        shared = [path for path in candidate_diff if not path.startswith("skills/example-skill/")]
        if omit_candidate_path:
            domain = domain[1:]

        review_root = "evidence/promotions/example-skill"
        privacy_path = f"{review_root}/privacy.txt"
        forward_path = f"{review_root}/forward.txt"
        activation_path = f"{review_root}/activation.json"
        promotion_path = f"{review_root}/promotion.json"
        privacy_sha = hashlib.sha256(b"privacy pass\n").hexdigest()
        forward_sha = hashlib.sha256(b"forward pass\n").hexdigest()
        fixture.write(privacy_path, b"privacy pass\n")
        fixture.write(forward_path, b"forward pass\n")
        activation_sha = fixture.write_json(
            activation_path,
            _activation(candidate, evidence_sha, corrupt_hash=corrupt_evidence_hash),
        )
        promotion = {
            "schema_version": "1.1",
            "contract_name": "promotion-delta",
            "promotion_id": "example-promotion",
            "skill_id": "example-skill",
            "skill_kind": "advisory",
            "software_backed": False,
            "base_commit": base,
            "candidate_commit": candidate,
            "base_registry_sha256": base_registry_sha,
            "review_artifact_root": review_root,
            "lifecycle_transition": {"from": "development", "to": "active"},
            "path_transition": {
                "from": "skills/example-skill",
                "to": "skills/example-skill",
                "source_tree_sha256": recorded_source_hash,
            },
            "domain_owned_files_changed": domain,
            "shared_files_changed": shared,
            "software_entries_moved": [],
            "interface_changes": [],
            "contracts_changed": [],
            "observable_route_decisions": [],
            "task_maturity_catalog": {"path": maturity_path, "sha256": maturity_sha},
            "activation_checklist": {"path": activation_path, "sha256": activation_sha},
            "installer_set": {
                "before": [],
                "after": ["example-skill"],
                "added": ["example-skill"],
                "removed": [],
            },
            "reports": {
                "privacy_license": {
                    "report_id": "privacy-report",
                    "path": privacy_path,
                    "sha256": privacy_sha,
                    "status": "pass",
                    "validated_utc": "2026-07-21T00:00:00Z",
                },
                "forward_tests": [
                    {
                        "report_id": "forward-report",
                        "path": forward_path,
                        "sha256": forward_sha,
                        "status": "pass",
                        "validated_utc": "2026-07-21T00:00:00Z",
                    }
                ],
            },
            "known_limitations": ["Synthetic integration fixture only"],
            "blockers": [],
            "decision": "eligible",
            "provenance": {
                "producer": "promotion-test",
                "producer_version": "1.0",
                "generated_utc": "2026-07-21T00:00:00Z",
            },
        }
        fixture.write_json(promotion_path, promotion)
        if review_escape:
            fixture.write("outside-review-root.txt", "forbidden review change\n")
        review = fixture.commit("review evidence state")
        return root / promotion_path, review

    def _codes(self, root: Path, path: Path, review: str) -> tuple[set[str], dict[str, object]]:
        findings, report = validate_promotion.validate_promotion(
            root,
            path,
            review_commit=review,
            contracts_dir=ROOT / "contracts",
        )
        return {finding.code for finding in findings}, report

    def test_valid_two_phase_promotion_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path, review = self._build(root)
            codes, report = self._codes(root, path, review)
            self.assertEqual(codes, set())
            self.assertTrue(report["eligible"])

    def test_candidate_diff_omission_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path, review = self._build(root, omit_candidate_path=True)
            codes, _report = self._codes(root, path, review)
            self.assertIn("PROMOTION_CANDIDATE_DIFF_MISMATCH", codes)

    def test_source_hash_tampering_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path, review = self._build(root, corrupt_source_hash=True)
            codes, _report = self._codes(root, path, review)
            self.assertIn("PROMOTION_SOURCE_TREE_HASH_MISMATCH", codes)

    def test_review_diff_escape_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path, review = self._build(root, review_escape=True)
            codes, _report = self._codes(root, path, review)
            self.assertIn("PROMOTION_REVIEW_DIFF_ESCAPES_ARTIFACT_ROOT", codes)

    def test_candidate_evidence_hash_tampering_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path, review = self._build(root, corrupt_evidence_hash=True)
            codes, _report = self._codes(root, path, review)
            self.assertIn("PROMOTION_CANDIDATE_EVIDENCE_REF_HASH_MISMATCH", codes)


if __name__ == "__main__":
    unittest.main()
