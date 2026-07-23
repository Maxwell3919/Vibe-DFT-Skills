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
CLAIM_ORDER = {"no_positive_claim":0,"documented_behavior_only":1,"input_gates_only":2,"technical_run_gates_only":3,"numerical_candidate_only":4,"eligible_for_expert_review":5}
REQUIRED_CONVERGENCE = {"ecutwfc","k-mesh","q-mesh","smearing","vacuum"}
REQUIRED_STAGES = {"scf","nscf","phonon","epc"}

@dataclass(frozen=True, order=True)
class Finding:
    code: str
    location: str
    message: str
    def render(self) -> str:
        return f"{self.code}\t{self.location}\t{self.message}"

def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]

def _rel(actual: float, expected: float) -> float:
    return abs(actual-expected)/max(abs(expected),1e-15)

def _trap(x:list[float], y:list[float]) -> float:
    return sum(0.5*(y[i]+y[i+1])*(x[i+1]-x[i]) for i in range(len(x)-1))

def integrate_alpha2f(frequency_mev:Iterable[float], alpha2f:Iterable[float]) -> tuple[float,float]:
    x=[float(v) for v in frequency_mev]; y=[float(v) for v in alpha2f]
    if len(x)!=len(y) or len(x)<3: raise ValueError("frequency and alpha2F arrays must have equal length >= 3")
    if any(v<=0 for v in x) or any(b<=a for a,b in zip(x,x[1:])): raise ValueError("frequency grid must be strictly positive and increasing")
    if any(v<0 for v in y): raise ValueError("alpha2F must be nonnegative")
    kernel=[a/w for w,a in zip(x,y)]
    coupling=2*_trap(x,kernel)
    if coupling<=0: raise ValueError("integrated lambda must be positive")
    omega_log=math.exp(2*_trap(x,[k*math.log(w) for w,k in zip(x,kernel)])/coupling)
    return coupling,omega_log

def allen_dynes_tc(lambda_ep:float, omega_log_mev:float, mu_star:float) -> float:
    denominator=lambda_ep-mu_star*(1+0.62*lambda_ep)
    if denominator<=0: raise ValueError("Allen-Dynes denominator is nonpositive")
    return omega_log_mev*MEV_TO_KELVIN/1.2*math.exp(-1.04*(1+lambda_ep)/denominator)

def pseudopotential_set_sha256(items:list[dict[str,Any]]) -> str:
    digest=hashlib.sha256(); digest.update(b"vibe-dft-qe-pseudopotential-set-v1\0")
    for item in sorted(items,key=lambda v:(str(v.get("element")),str(v.get("sha256")))):
        for raw in (str(item.get("element")).encode(),str(item.get("sha256")).encode()): digest.update(len(raw).to_bytes(4,"big")+raw)
    return digest.hexdigest()

def _stage_findings(data:dict[str,Any]) -> list[Finding]:
    findings=[]; system=data.get("system",{}); pseudo=data.get("pseudopotentials",[]); stages=data.get("stage_identity",[])
    expected_pseudo=pseudopotential_set_sha256([v for v in pseudo if isinstance(v,dict)])
    stage_map={}
    for i,stage in enumerate(stages):
        if not isinstance(stage,dict) or stage.get("stage") in stage_map:
            findings.append(Finding("QE_EPC_STAGE_DUPLICATE_OR_INVALID",f"stage_identity/{i}",str(stage.get("stage") if isinstance(stage,dict) else None))); continue
        stage_map[stage["stage"]]=stage
        for field,expected in {"structure_fingerprint":system.get("structure_fingerprint"),"pseudopotential_set_sha256":expected_pseudo,"spin_mode":system.get("spin_mode"),"soc":system.get("soc")}.items():
            if stage.get(field)!=expected: findings.append(Finding("QE_EPC_STAGE_IDENTITY_MISMATCH",f"stage_identity/{i}/{field}",f"expected {expected!r}"))
    if set(stage_map)!=REQUIRED_STAGES:
        findings.append(Finding("QE_EPC_STAGE_SET_INCOMPLETE","stage_identity",str(sorted(stage_map)))); return findings
    parents={"scf":None,"nscf":stage_map["scf"].get("record_id"),"phonon":stage_map["scf"].get("record_id"),"epc":stage_map["phonon"].get("record_id")}
    for stage,parent in parents.items():
        if stage_map[stage].get("parent_record_id")!=parent: findings.append(Finding("QE_EPC_STAGE_PARENT_MISMATCH",stage,f"expected {parent!r}"))
    if system.get("soc") is True and any(v.get("relativity")!="fully-relativistic" for v in pseudo if isinstance(v,dict)):
        findings.append(Finding("QE_EPC_SOC_PSEUDOPOTENTIAL_MISMATCH","pseudopotentials","SOC requires fully-relativistic pseudopotentials"))
    return findings

def _convergence_findings(data:dict[str,Any]) -> list[Finding]:
    findings=[]; dimensions=set()
    for i,item in enumerate(data.get("convergence",[])):
        if not isinstance(item,dict): continue
        d=item.get("dimension")
        if not isinstance(d,str) or d in dimensions: findings.append(Finding("QE_EPC_CONVERGENCE_DIMENSION_DUPLICATE",f"convergence/{i}",str(d)))
        else: dimensions.add(d)
        if item.get("accepted") is not True: findings.append(Finding("QE_EPC_CONVERGENCE_NOT_ACCEPTED",f"convergence/{i}",str(d)))
        if isinstance(item.get("observed_change"),(int,float)) and isinstance(item.get("tolerance"),(int,float)) and item["observed_change"]>item["tolerance"]:
            findings.append(Finding("QE_EPC_CONVERGENCE_TOLERANCE_EXCEEDED",f"convergence/{i}",str(d)))
    if dimensions!=REQUIRED_CONVERGENCE: findings.append(Finding("QE_EPC_CONVERGENCE_SET_INCOMPLETE","convergence",str(sorted(dimensions))))
    system=data.get("system",{}); protocol=data.get("protocol",{})
    if float(system.get("vacuum_angstrom",0))<12: findings.append(Finding("QE_EPC_VACUUM_TOO_SMALL_FOR_REVIEW","system/vacuum_angstrom","below 12 angstrom"))
    if float(protocol.get("ecutrho_ry",0))<float(protocol.get("ecutwfc_ry",0)): findings.append(Finding("QE_EPC_CUTOFF_RATIO_INVALID","protocol/ecutrho_ry","below ecutwfc"))
    return findings

def _spectral_findings(data:dict[str,Any]) -> tuple[list[Finding],dict[str,float]]:
    findings=[]; computed={}; phonons=data.get("phonons",{}); epc=data.get("epc",{}); tol=data.get("tolerances",{})
    q_points=phonons.get("q_points",[]); q_weight=sum(float(v.get("weight",0)) for v in q_points if isinstance(v,dict)); computed["q_weight_sum"]=q_weight
    if abs(q_weight-1)>float(tol.get("q_weight_absolute",0)): findings.append(Finding("QE_EPC_Q_WEIGHT_NOT_CLOSED","phonons/q_points",str(q_weight)))
    if phonons.get("acoustic_sum_rule")!="applied-and-reviewed": findings.append(Finding("QE_EPC_ACOUSTIC_SUM_RULE_UNRESOLVED","phonons/acoustic_sum_rule","blocked"))
    if phonons.get("za_mode_reviewed") is not True: findings.append(Finding("QE_EPC_ZA_MODE_UNREVIEWED","phonons/za_mode_reviewed","blocked"))
    if phonons.get("unresolved_imaginary_modes") is True: findings.append(Finding("QE_EPC_IMAGINARY_MODES_UNRESOLVED","phonons","blocked"))
    if any(abs(float(v))>float(phonons.get("imaginary_mode_tolerance_mev",0)) for v in phonons.get("imaginary_modes_mev",[])): findings.append(Finding("QE_EPC_IMAGINARY_MODE_TOLERANCE_EXCEEDED","phonons/imaginary_modes_mev","blocked"))
    try: coupling,omega=integrate_alpha2f(epc.get("frequency_mev",[]),epc.get("alpha2f",[]))
    except (TypeError,ValueError) as exc: return findings+[Finding("QE_EPC_ALPHA2F_INVALID","epc",str(exc))],computed
    computed.update(lambda_integrated=coupling,omega_log_mev_integrated=omega)
    reported=float(epc.get("lambda_reported",0)); omega_reported=float(epc.get("omega_log_mev_reported",0))
    if _rel(coupling,reported)>float(tol.get("lambda_relative",0)): findings.append(Finding("QE_EPC_ALPHA2F_LAMBDA_MISMATCH","epc/lambda_reported",f"{reported} != {coupling}"))
    if _rel(omega,omega_reported)>float(tol.get("omega_log_relative",0)): findings.append(Finding("QE_EPC_ALPHA2F_OMEGA_LOG_MISMATCH","epc/omega_log_mev_reported",f"{omega_reported} != {omega}"))
    q_lambda=epc.get("q_lambda",[]); q_sum=sum(float(v.get("weight",0))*float(v.get("lambda_unweighted",0)) for v in q_lambda if isinstance(v,dict)); computed["q_weighted_lambda_sum"]=q_sum
    if _rel(q_sum,reported)>float(tol.get("decomposition_relative",0)): findings.append(Finding("QE_EPC_Q_LAMBDA_NOT_CLOSED","epc/q_lambda",str(q_sum)))
    if {v.get("q_id") for v in q_points if isinstance(v,dict)}!={v.get("q_id") for v in q_lambda if isinstance(v,dict)}: findings.append(Finding("QE_EPC_Q_ID_SET_MISMATCH","epc/q_lambda","q IDs differ"))
    mode_sum=sum(float(v) for v in epc.get("mode_weighted_lambda",[])); computed["mode_weighted_lambda_sum"]=mode_sum
    if _rel(mode_sum,reported)>float(tol.get("decomposition_relative",0)): findings.append(Finding("QE_EPC_MODE_LAMBDA_NOT_CLOSED","epc/mode_weighted_lambda",str(mode_sum)))
    return findings,computed

def validate_evidence(path:Path,*,contracts_dir:Path|None=None)->tuple[list[Finding],dict[str,Any]]:
    contracts=contracts_dir or repo_root()/"contracts"
    try: data=strict_json.loads_object(path.read_bytes(),path.name)
    except (OSError,strict_json.StrictJSONError) as exc: return [Finding("QE_EPC_INPUT_INVALID",str(path),str(exc))],{}
    findings=[Finding("QE_EPC_SCHEMA_INVALID","<schema>",e) for e in validate_contract.validation_errors("qe-2d-epc-evidence@1.0",data,contracts)]
    maximum="technical_run_gates_only" if data.get("evidence_class")=="synthetic" else "numerical_candidate_only"
    if data.get("claim_ceiling") not in CLAIM_ORDER or CLAIM_ORDER[str(data.get("claim_ceiling"))]>CLAIM_ORDER[maximum]: findings.append(Finding("QE_EPC_CLAIM_CEILING_OVERSTATED","claim_ceiling",maximum))
    findings+=_stage_findings(data)+_convergence_findings(data)
    spectral,computed=_spectral_findings(data); findings+=spectral
    tc=data.get("tc",{}); epc=data.get("epc",{}); tol=data.get("tolerances",{})
    if tc.get("mu_star_source")!="external-assumption": findings.append(Finding("QE_EPC_MU_STAR_NOT_EXTERNAL_ASSUMPTION","tc/mu_star_source","blocked"))
    try:
        recomputed=allen_dynes_tc(float(epc.get("lambda_reported")),float(epc.get("omega_log_mev_reported")),float(tc.get("mu_star"))); computed["tc_kelvin_recomputed"]=recomputed
        if _rel(recomputed,float(tc.get("reported_kelvin",0)))>float(tol.get("tc_relative",0)): findings.append(Finding("QE_EPC_TC_RECOMPUTATION_MISMATCH","tc/reported_kelvin",str(recomputed)))
    except (TypeError,ValueError) as exc: findings.append(Finding("QE_EPC_TC_INPUT_INVALID","tc",str(exc)))
    findings=sorted(set(findings))
    return findings,{"schema_version":"1.0","validator":"qe-2d-epc-validator","record_id":data.get("record_id"),"evidence_class":data.get("evidence_class"),"status":"pass" if not findings else "fail","maximum_claim":maximum,"native_execution_established":False,"scientific_acceptance_established":False,"eligible_for_expert_review":False,"computed":computed,"finding_count":len(findings),"findings":[{"code":f.code,"location":f.location,"message":f.message} for f in findings]}

def main(argv:Sequence[str]|None=None)->int:
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("evidence",type=Path); parser.add_argument("--contracts-dir",type=Path); parser.add_argument("--report",type=Path); args=parser.parse_args(argv)
    findings,report=validate_evidence(args.evidence,contracts_dir=args.contracts_dir)
    if args.report: args.report.parent.mkdir(parents=True,exist_ok=True); args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    if findings:
        for finding in findings: print(finding.render(),file=sys.stderr)
        return 2
    print(f"PASS: QE 2D EPC evidence is internally closed at {report['maximum_claim']}; native and scientific acceptance remain false"); return 0
if __name__=="__main__": raise SystemExit(main())
