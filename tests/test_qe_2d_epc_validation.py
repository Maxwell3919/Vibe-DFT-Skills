from __future__ import annotations

import copy
import hashlib
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import validate_qe_2d_epc as validator


GOLDEN_ROOT = ROOT / "golden-bundles" / "qe-2d-epc-v1"
EVIDENCE_PATH = GOLDEN_ROOT / "evidence.json"


class QE2DEPCValidationTests(unittest.TestCase):
    def _evidence(self) -> dict[str, object]:
        return json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))

    def _validate_mutation(
        self,
        mutator,
    ) -> tuple[set[str], dict[str, object]]:
        data = copy.deepcopy(self._evidence())
        mutator(data)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "evidence.json"
            path.write_text(
                json.dumps(data, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            findings, report = validator.validate_evidence(
                path,
                contracts_dir=ROOT / "contracts",
            )
        return {finding.code for finding in findings}, report

    def test_golden_evidence_passes_and_recomputes_expected_values(self) -> None:
        findings, report = validator.validate_evidence(
            EVIDENCE_PATH,
            contracts_dir=ROOT / "contracts",
        )
        self.assertEqual(findings, [])
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["maximum_claim"], "technical_run_gates_only")
        self.assertFalse(report["native_execution_established"])
        self.assertFalse(report["scientific_acceptance_established"])
        computed = report["computed"]
        self.assertTrue(
            math.isclose(
                computed["lambda_integrated"],
                0.8632857142857143,
                rel_tol=1.0e-14,
            )
        )
        self.assertTrue(
            math.isclose(
                computed["omega_log_mev_integrated"],
                17.071652491805146,
                rel_tol=1.0e-14,
            )
        )
        self.assertTrue(
            math.isclose(
                computed["tc_kelvin_recomputed"],
                10.764537564017099,
                rel_tol=1.0e-14,
            )
        )

    def test_alpha2f_lambda_mismatch_is_blocked(self) -> None:
        codes, _report = self._validate_mutation(
            lambda data: data["epc"].__setitem__("lambda_reported", 1.2)
        )
        self.assertIn("QE_EPC_ALPHA2F_LAMBDA_MISMATCH", codes)

    def test_q_weight_mismatch_is_blocked(self) -> None:
        def mutate(data: dict[str, object]) -> None:
            data["phonons"]["q_points"][0]["weight"] = 0.20

        codes, _report = self._validate_mutation(mutate)
        self.assertIn("QE_EPC_Q_WEIGHT_NOT_CLOSED", codes)

    def test_unresolved_imaginary_mode_is_blocked(self) -> None:
        def mutate(data: dict[str, object]) -> None:
            data["phonons"]["imaginary_modes_mev"] = [-2.0]
            data["phonons"]["unresolved_imaginary_modes"] = True

        codes, _report = self._validate_mutation(mutate)
        self.assertIn("QE_EPC_IMAGINARY_MODES_UNRESOLVED", codes)
        self.assertIn("QE_EPC_IMAGINARY_MODE_TOLERANCE_EXCEEDED", codes)

    def test_stage_pseudopotential_identity_mismatch_is_blocked(self) -> None:
        def mutate(data: dict[str, object]) -> None:
            data["stage_identity"][2]["pseudopotential_set_sha256"] = "0" * 64

        codes, _report = self._validate_mutation(mutate)
        self.assertIn("QE_EPC_STAGE_IDENTITY_MISMATCH", codes)

    def test_synthetic_evidence_cannot_claim_expert_readiness(self) -> None:
        codes, _report = self._validate_mutation(
            lambda data: data.__setitem__(
                "claim_ceiling",
                "eligible_for_expert_review",
            )
        )
        self.assertIn("QE_EPC_CLAIM_CEILING_OVERSTATED", codes)

    def test_manifest_hashes_match_exact_golden_bytes(self) -> None:
        manifest = json.loads(
            (GOLDEN_ROOT / "manifest.json").read_text(encoding="utf-8")
        )
        for entry in manifest["files"]:
            raw = (GOLDEN_ROOT / entry["path"]).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), entry["sha256"])

    def test_numeric_helpers_reject_invalid_frequency_grid(self) -> None:
        with self.assertRaises(ValueError):
            validator.integrate_alpha2f([5.0, 5.0, 10.0], [0.1, 0.2, 0.3])


if __name__ == "__main__":
    unittest.main()
