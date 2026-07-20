#!/usr/bin/env python3
"""Validate QE two-dimensional phonon, EPC, alpha2F, and Tc evidence."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any, Iterable, Sequence

import strict_json
import validate_contract


MEV_TO_KELVIN = 11.604518121550082
CLAIM_ORDER = {
    "no_positive_claim": 0,
    "documented_behavior_only": 1,
    "input_gates_only": 2,
    "technical_run_gates_only": 3,
    "numerical_candidate_only": 4,
    "eligible_for_expert_review": 5,
}
REQUIRED_CONVERGENCE = frozenset(
    {"ecutwfc", "k-mesh", "q-mesh", "smearing", "vacuum"}
)
REQUIRED_STAGES = frozenset({"scf", "nscf", "phonon", "epc"})


@dataclass(frozen=True, order=True)
class Finding:
    code: str
    location: str
    message: str

    def render(self) -> str:
        return f"{self.code}\t{self.location}\t{self.message}"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _relative_error(actual: float, expected: float) -> float:
    scale = max(abs(expected), 1.0e-15)
    return abs(actual - expected) / scale


def _trapezoid(x: list[float], y: list[float]) -> float:
    return sum(
        0.5 * (y[index] + y[index + 1]) * (x[index + 1] - x[index])
        for index in range(len(x) - 1)
    )


def integrate_alpha2f(
    frequency_mev: Iterable[float],
    alpha2f: Iterable[float],
) -> tuple[float, float]:
    frequency = [float(value) for value in frequency_mev]
    spectral = [float(value) for value in alpha2f]
    if len(frequency) != len(spectral) or len(frequency) < 3:
        raise ValueError("frequency and alpha2F arrays must have the same length >= 3")
    if any(value <= 0 for value in frequency):
        raise ValueError("frequency grid must be strictly positive")
    if any(right <= left for left, right in zip(frequency, frequency[1:])):
        raise ValueError("frequency grid must be strictly increasing")
    if any(value < 0 for value in spectral):
        raise ValueError("alpha2F values must be nonnegative")
    kernel = [value / omega for omega, value in zip(frequency, spectral)]
    coupling = 2.0 * _trapezoid(frequency, kernel)
    if coupling <= 0:
        raise ValueError("integrated lambda must be positive")
    logarithmic_kernel = [
        value * math.log(omega) for omega, value in zip(frequency, kernel)
    ]
    omega_log = math.exp(2.0 * _trapezoid(frequency, logarithmic_kernel) / coupling)
    return coupling, omega_log


def allen_dynes_tc(lambda_ep: float, omega_log_mev: float, mu_star: float) -> float:
    denominator = lambda_ep - mu_star * (1.0 + 0.62 * lambda_ep)
    if denominator <= 0:
        raise ValueError("Allen-Dynes denominator is nonpositive")
    exponent = -1.04 * (1.0 + lambda_ep) / denominator
    return omega_log_mev * MEV_TO_KELVIN / 1.2 * math.exp(exponent)


def pseudopotential_set_sha256(pseudopotentials: list[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    digest.update(b"vibe-dft-qe-pseudopotential-set-v1\0")
    for item in sorted(
        pseudopotentials,
        key=lambda value: (str(value.get("element")), str(value.get("sha256"))),
    ):
        element = str(item.get("element")).encode("utf-8")
        sha256 = str(item.get("sha256")).encode("ascii")
        digest.update(len(element).to_bytes(4, "big") + element)
        digest.update(len(sha256).to_bytes(4, "big") + sha256)
    return digest.hexdigest()


def _claim_finding(data: dict[str, Any]) -> Finding | None:
    evidence_class = data.get("evidence_class")
    declared = data.get("claim_ceiling")
    maximum = (
        "technical_run_gates_only"
        if evidence_class == "synthetic"
        else "numerical_candidate_only"
    )
    if declared not in CLAIM_ORDER or CLAIM_ORDER[str(declared)] > CLAIM_ORDER[maximum]:
        return Finding(
            "QE_EPC_CLAIM_CEILING_OVERSTATED",
            "claim_ceiling",
            f"{evidence_class} evidence is capped at {maximum}",
        )
    return None


def _stage_findings(data: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    system = data.get("system")
    pseudopotentials = data.get("pseudopotentials")
    stages = data.get("stage_identity")
    if not isinstance(system, dict) or not isinstance(pseudopotentials, list) or not isinstance(stages, list):
        return findings
    expected_pseudo = pseudopotential_set_sha256(
        [item for item in pseudopotentials if isinstance(item, dict)]
    )
    stage_map: dict[str, dict[str, Any]] = {}
    record_ids: set[str] = set()
    for index, stage in enumerate(stages):
        if not isinstance(stage, dict):
            continue
        stage_id = stage.get("stage")
        record_id = stage.get("record_id")
        if not isinstance(stage_id, str) or stage_id in stage_map:
            findings.append(
                Finding(
                    "QE_EPC_STAGE_DUPLICATE_OR_INVALID",
                    f"stage_identity/{index}",
                    str(stage_id),
                )
            )
            continue
        stage_map[stage_id] = stage
        if not isinstance(record_id, str) or record_id in record_ids:
            findings.append(
                Finding(
                    "QE_EPC_STAGE_RECORD_ID_INVALID",
                    f"stage_identity/{index}/record_id",
                    str(record_id),
                )
            )
        elif isinstance(record_id, str):
            record_ids.add(record_id)
        expected = {
            "structure_fingerprint": system.get("structure_fingerprint"),
            "pseudopotential_set_sha256": expected_pseudo,
            "spin_mode": system.get("spin_mode"),
            "soc": system.get("soc"),
        }
        for field, value in expected.items():
            if stage.get(field) != value:
                findings.append(
                    Finding(
                        "QE_EPC_STAGE_IDENTITY_MISMATCH",
                        f"stage_identity/{index}/{field}",
                        f"expected {value!r}",
                    )
                )
    if set(stage_map) != REQUIRED_STAGES:
        findings.append(
            Finding(
                "QE_EPC_STAGE_SET_INCOMPLETE",
                "stage_identity",
                f"expected {sorted(REQUIRED_STAGES)}, got {sorted(stage_map)}",
            )
        )
        return findings
    parent_expectations = {
        "scf": None,
        "nscf": stage_map["scf"].get("record_id"),
        "phonon": stage_map["scf"].get("record_id"),
        "epc": stage_map["phonon"].get("record_id"),
    }
    for stage_id, parent in parent_expectations.items():
        if stage_map[stage_id].get("parent_record_id") != parent:
            findings.append(
                Finding(
                    "QE_EPC_STAGE_PARENT_MISMATCH",
                    f"stage_identity/{stage_id}/parent_record_id",
                    f"expected {parent!r}",
                )
            )
    if system.get("soc") is True and any(
        item.get("relativity") != "fully-relativistic"
        for item in pseudopotentials
        if isinstance(item, dict)
    ):
        findings.append(
            Finding(
                "QE_EPC_SOC_PSEUDOPOTENTIAL_MISMATCH",
                "pseudopotentials",
                "SOC requires fully-relativistic pseudopotentials for every element",
            )
        )
    return findings


def _convergence_findings(data: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    convergence = data.get("convergence")
    if not isinstance(convergence, list):
        return findings
    dimensions: set[str] = set()
    for index, item in enumerate(convergence):
        if not isinstance(item, dict):
            continue
        dimension = item.get("dimension")
        if not isinstance(dimension, str) or dimension in dimensions:
            findings.append(
                Finding(
                    "QE_EPC_CONVERGENCE_DIMENSION_DUPLICATE",
                    f"convergence/{index}/dimension",
                    str(dimension),
                )
            )
        elif isinstance(dimension, str):
            dimensions.add(dimension)
        if item.get("accepted") is not True:
            findings.append(
                Finding(
                    "QE_EPC_CONVERGENCE_NOT_ACCEPTED",
                    f"convergence/{index}",
                    str(dimension),
                )
            )
        observed = item.get("observed_change")
        tolerance = item.get("tolerance")
        if isinstance(observed, (int, float)) and isinstance(tolerance, (int, float)):
            if float(observed) > float(tolerance):
                findings.append(
                    Finding(
                        "QE_EPC_CONVERGENCE_TOLERANCE_EXCEEDED",
                        f"convergence/{index}",
                        f"observed {observed} > tolerance {tolerance}",
                    )
                )
    if dimensions != REQUIRED_CONVERGENCE:
        findings.append(
            Finding(
                "QE_EPC_CONVERGENCE_SET_INCOMPLETE",
                "convergence",
                f"expected {sorted(REQUIRED_CONVERGENCE)}, got {sorted(dimensions)}",
            )
        )
    system = data.get("system")
    if isinstance(system, dict):
        vacuum = system.get("vacuum_angstrom")
        if isinstance(vacuum, (int, float)) and float(vacuum) < 12.0:
            findings.append(
                Finding(
                    "QE_EPC_VACUUM_TOO_SMALL_FOR_REVIEW",
                    "system/vacuum_angstrom",
                    "vacuum below 12 angstrom cannot support the 2D validation route",
                )
            )
    protocol = data.get("protocol")
    if isinstance(protocol, dict):
        ecutwfc = protocol.get("ecutwfc_ry")
        ecutrho = protocol.get("ecutrho_ry")
        if isinstance(ecutwfc, (int, float)) and isinstance(ecutrho, (int, float)):
            if float(ecutrho) < float(ecutwfc):
                findings.append(
                    Finding(
                        "QE_EPC_CUTOFF_RATIO_INVALID",
                        "protocol/ecutrho_ry",
                        "charge-density cutoff is below wavefunction cutoff",
                    )
                )
    return findings


def _phonon_and_epc_findings(
    data: dict[str, Any],
) -> tuple[list[Finding], dict[str, float]]:
    findings: list[Finding] = []
    computed: dict[str, float] = {}
    phonons = data.get("phonons")
    epc = data.get("epc")
    tolerances = data.get("tolerances")
    if not isinstance(phonons, dict) or not isinstance(epc, dict) or not isinstance(tolerances, dict):
        return findings, computed

    q_points = phonons.get("q_points")
    q_lambda = epc.get("q_lambda")
    if isinstance(q_points, list):
        q_weight = sum(
            float(item.get("weight", 0.0))
            for item in q_points
            if isinstance(item, dict)
        )
        computed["q_weight_sum"] = q_weight
        tolerance = float(tolerances.get("q_weight_absolute", 0.0))
        if abs(q_weight - 1.0) > tolerance:
            findings.append(
                Finding(
                    "QE_EPC_Q_WEIGHT_NOT_CLOSED",
                    "phonons/q_points",
                    f"sum={q_weight:.16g}",
                )
            )
    else:
        q_points = []
    if phonons.get("acoustic_sum_rule") != "applied-and-reviewed":
        findings.append(
            Finding(
                "QE_EPC_ACOUSTIC_SUM_RULE_UNRESOLVED",
                "phonons/acoustic_sum_rule",
                "acoustic sum rule must be applied and reviewed",
            )
        )
    if phonons.get("za_mode_reviewed") is not True:
        findings.append(
            Finding(
                "QE_EPC_ZA_MODE_UNREVIEWED",
                "phonons/za_mode_reviewed",
                "two-dimensional ZA behavior requires explicit review",
            )
        )
    if phonons.get("unresolved_imaginary_modes") is True:
        findings.append(
            Finding(
                "QE_EPC_IMAGINARY_MODES_UNRESOLVED",
                "phonons/unresolved_imaginary_modes",
                "unresolved imaginary modes block the route",
            )
        )
    imaginary = phonons.get("imaginary_modes_mev")
    threshold = phonons.get("imaginary_mode_tolerance_mev")
    if isinstance(imaginary, list) and isinstance(threshold, (int, float)):
        if any(abs(float(value)) > float(threshold) for value in imaginary):
            findings.append(
                Finding(
                    "QE_EPC_IMAGINARY_MODE_TOLERANCE_EXCEEDED",
                    "phonons/imaginary_modes_mev",
                    f"tolerance={threshold}",
                )
            )

    try:
        coupling, omega_log = integrate_alpha2f(
            epc.get("frequency_mev", []), epc.get("alpha2f", [])
        )
    except (TypeError, ValueError) as exc:
        findings.append(
            Finding("QE_EPC_ALPHA2F_INVALID", "epc", str(exc))
        )
        return findings, computed
    computed["lambda_integrated"] = coupling
    computed["omega_log_mev_integrated"] = omega_log
    lambda_reported = float(epc.get("lambda_reported", 0.0))
    omega_reported = float(epc.get("omega_log_mev_reported", 0.0))
    if _relative_error(coupling, lambda_reported) > float(
        tolerances.get("lambda_relative", 0.0)
    ):
        findings.append(
            Finding(
                "QE_EPC_ALPHA2F_LAMBDA_MISMATCH",
                "epc/lambda_reported",
                f"reported={lambda_reported:.16g}, integrated={coupling:.16g}",
            )
        )
    if _relative_error(omega_log, omega_reported) > float(
        tolerances.get("omega_log_relative", 0.0)
    ):
        findings.append(
            Finding(
                "QE_EPC_ALPHA2F_OMEGA_LOG_MISMATCH",
                "epc/omega_log_mev_reported",
                f"reported={omega_reported:.16g}, integrated={omega_log:.16g}",
            )
        )

    if isinstance(q_lambda, list):
        q_sum = sum(
            float(item.get("weight", 0.0)) * float(item.get("lambda_unweighted", 0.0))
            for item in q_lambda
            if isinstance(item, dict)
        )
        computed["q_weighted_lambda_sum"] = q_sum
        if _relative_error(q_sum, lambda_reported) > float(
            tolerances.get("decomposition_relative", 0.0)
        ):
            findings.append(
                Finding(
                    "QE_EPC_Q_LAMBDA_NOT_CLOSED",
                    "epc/q_lambda",
                    f"sum={q_sum:.16g}, reported={lambda_reported:.16g}",
                )
            )
        q_ids = {
            item.get("q_id")
            for item in q_points
            if isinstance(item, dict)
        }
        q_lambda_ids = {
            item.get("q_id")
            for item in q_lambda
            if isinstance(item, dict)
        }
        if q_ids != q_lambda_ids:
            findings.append(
                Finding(
                    "QE_EPC_Q_ID_SET_MISMATCH",
                    "epc/q_lambda",
                    f"phonon={sorted(str(item) for item in q_ids)}, epc={sorted(str(item) for item in q_lambda_ids)}",
                )
            )
    modes = epc.get("mode_weighted_lambda")
    if isinstance(modes, list):
        mode_sum = sum(float(value) for value in modes)
        computed["mode_weighted_lambda_sum"] = mode_sum
        if _relative_error(mode_sum, lambda_reported) > float(
            tolerances.get("decomposition_relative", 0.0)
        ):
            findings.append(
                Finding(
                    "QE_EPC_MODE_LAMBDA_NOT_CLOSED",
                    "epc/mode_weighted_lambda",
                    f"sum={mode_sum:.16g}, reported={lambda_reported:.16g}",
                )
            )
    return findings, computed


def _tc_findings(data: dict[str, Any], computed: dict[str, float]) -> list[Finding]:
    findings: list[Finding] = []
    tc = data.get("tc")
    epc = data.get("epc")
    tolerances = data.get("tolerances")
    if not isinstance(tc, dict) or not isinstance(epc, dict) or not isinstance(tolerances, dict):
        return findings
    if tc.get("mu_star_source") != "external-assumption":
        findings.append(
            Finding(
                "QE_EPC_MU_STAR_NOT_EXTERNAL_ASSUMPTION",
                "tc/mu_star_source",
                "mu* must remain an explicit external assumption",
            )
        )
    try:
        recomputed = allen_dynes_tc(
            float(epc.get("lambda_reported")),
            float(epc.get("omega_log_mev_reported")),
            float(tc.get("mu_star")),
        )
    except (TypeError, ValueError) as exc:
        findings.append(Finding("QE_EPC_TC_INPUT_INVALID", "tc", str(exc)))
        return findings
    computed["tc_kelvin_recomputed"] = recomputed
    reported = float(tc.get("reported_kelvin", 0.0))
    if _relative_error(recomputed, reported) > float(tolerances.get("tc_relative", 0.0)):
        findings.append(
            Finding(
                "QE_EPC_TC_RECOMPUTATION_MISMATCH",
                "tc/reported_kelvin",
                f"reported={reported:.16g}, recomputed={recomputed:.16g}",
            )
        )
    return findings


def validate_evidence(
    path: Path,
    *,
    contracts_dir: Path | None = None,
) -> tuple[list[Finding], dict[str, Any]]:
    selected_contracts = contracts_dir or repo_root() / "contracts"
    try:
        raw = path.read_bytes()
        data = strict_json.loads_object(raw, path.name)
    except (OSError, strict_json.StrictJSONError) as exc:
        return [Finding("QE_EPC_INPUT_INVALID", str(path), str(exc))], {}
    findings = [
        Finding("QE_EPC_SCHEMA_INVALID", "<schema>", error)
        for error in validate_contract.validation_errors(
            "qe-2d-epc-evidence@1.0", data, selected_contracts
        )
    ]
    claim_finding = _claim_finding(data)
    if claim_finding is not None:
        findings.append(claim_finding)
    findings.extend(_stage_findings(data))
    findings.extend(_convergence_findings(data))
    spectral_findings, computed = _phonon_and_epc_findings(data)
    findings.extend(spectral_findings)
    findings.extend(_tc_findings(data, computed))
    findings = sorted(set(findings))
    evidence_class = data.get("evidence_class")
    maximum_claim = (
        "technical_run_gates_only"
        if evidence_class == "synthetic"
        else "numerical_candidate_only"
    )
    report = {
        "schema_version": "1.0",
        "validator": "qe-2d-epc-validator",
        "record_id": data.get("record_id"),
        "evidence_class": evidence_class,
        "status": "pass" if not findings else "fail",
        "maximum_claim": maximum_claim,
        "native_execution_established": False,
        "scientific_acceptance_established": False,
        "eligible_for_expert_review": False,
        "computed": computed,
        "finding_count": len(findings),
        "findings": [
            {"code": item.code, "location": item.location, "message": item.message}
            for item in findings
        ],
    }
    return findings, report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--contracts-dir", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    findings, report = validate_evidence(
        args.evidence,
        contracts_dir=args.contracts_dir,
    )
    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    if findings:
        for finding in findings:
            print(finding.render(), file=sys.stderr)
        return 2
    print(
        "PASS: QE 2D EPC evidence is internally closed at "
        f"{report['maximum_claim']}; native and scientific acceptance remain false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
