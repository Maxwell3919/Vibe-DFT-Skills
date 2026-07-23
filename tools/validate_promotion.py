#!/usr/bin/env python3
"""Validate a two-phase development-to-active promotion against immutable Git objects."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
from typing import Any, Iterable, Iterator, Sequence

from registry_yaml import RegistryYAMLError, loads_yaml_strict
import strict_json
import validate_contract
from skill_registry import TREE_HASH_DOMAIN

MAX_BYTES=16*1024*1024
ROUTING_REGISTRIES=("registry/skill-registry.yaml","registry/interface-registry.yaml","registry/operation-routes.yaml","registry/software-registry.yaml","registry/environment-profiles.yaml")
MATURITY_ORDER={"design-only":0,"synthetic-validated":1,"format-fixture-validated":2,"real-artifact-validated":3,"tool-integration-validated":4}
CLAIM_ORDER={"no_positive_claim":0,"documented_behavior_only":1,"input_gates_only":2,"technical_run_gates_only":3,"numerical_candidate_only":4,"eligible_for_expert_review":5}
MAX_CLAIM={"design-only":"no_positive_claim","synthetic-validated":"documented_behavior_only","format-fixture-validated":"input_gates_only","real-artifact-validated":"numerical_candidate_only","tool-integration-validated":"eligible_for_expert_review"}

@dataclass(frozen=True,order=True)
class Finding:
    code:str; location:str; message:str
    def render(self)->str:return f"{self.code}\t{self.location}\t{self.message}"
@dataclass(frozen=True)
class GitFile:
    path:str; raw:bytes
    @property
    def sha256(self)->str:return hashlib.sha256(self.raw).hexdigest()
class GitError(ValueError):pass

def _safe_path(value:object)->str|None:
    if not isinstance(value,str) or not value or "\\" in value or "\x00" in value:return None
    path=PurePosixPath(value)
    if path.is_absolute() or any(p in {"",".",".."} for p in path.parts):return None
    return path.as_posix()

def _pointer(parts:Iterable[object])->str:
    values=tuple(parts);return "<root>" if not values else "/"+"/".join(str(v) for v in values)

def _dicts(value:object,path:tuple[object,...]=())->Iterator[tuple[tuple[object,...],dict[str,Any]]]:
    if isinstance(value,dict):
        yield path,value
        for key,child in value.items():yield from _dicts(child,(*path,key))
    elif isinstance(value,list):
        for i,child in enumerate(value):yield from _dicts(child,(*path,i))

class GitRepo:
    def __init__(self,root:Path):
        self.root=root.resolve()
        if self._run(["rev-parse","--git-dir"]).returncode!=0:raise GitError("not a Git work tree")
    def _run(self,args:Sequence[str])->subprocess.CompletedProcess[bytes]:
        return subprocess.run(["git","-C",str(self.root),*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
    def head(self)->str:
        result=self._run(["rev-parse","HEAD^{commit}"])
        if result.returncode:raise GitError("HEAD does not resolve")
        return result.stdout.decode().strip()
    def commit(self,value:object,label:str)->str:
        if not isinstance(value,str) or len(value) not in (40,64):raise GitError(f"{label}: noncanonical commit")
        result=self._run(["rev-parse","--verify",f"{value}^{{commit}}"])
        if result.returncode or result.stdout.decode().strip()!=value:raise GitError(f"{label}: commit does not resolve exactly")
        return value
    def ancestor(self,a:str,b:str)->bool:return self._run(["merge-base","--is-ancestor",a,b]).returncode==0
    def file(self,commit:str,path_value:object)->GitFile:
        path=_safe_path(path_value)
        if path is None:raise GitError(f"unsafe path {path_value!r}")
        result=self._run(["show",f"{commit}:{path}"])
        if result.returncode:raise GitError(f"{path}: absent at {commit}")
        if len(result.stdout)>MAX_BYTES:raise GitError(f"{path}: exceeds size limit")
        return GitFile(path,result.stdout)
    def json(self,commit:str,path:object)->tuple[GitFile,dict[str,Any]]:
        item=self.file(commit,path)
        try:value=strict_json.loads_object(item.raw,item.path,max_bytes=MAX_BYTES)
        except strict_json.StrictJSONError as exc:raise GitError(f"{item.path}: {exc}") from exc
        return item,value
    def yaml(self,commit:str,path:object)->tuple[GitFile,dict[str,Any]]:
        item=self.file(commit,path)
        try:value=loads_yaml_strict(item.raw.decode(),item.path)
        except (UnicodeDecodeError,RegistryYAMLError) as exc:raise GitError(f"{item.path}: {exc}") from exc
        return item,value
    def diff(self,a:str,b:str)->set[str]:
        result=self._run(["diff","--name-only","-z","--diff-filter=ACMRT",a,b,"--"])
        if result.returncode:raise GitError("cannot enumerate diff")
        paths=set()
        for raw in result.stdout.split(b"\0"):
            if raw:
                path=_safe_path(raw.decode())
                if path is None:raise GitError("unsafe diff path")
                paths.add(path)
        return paths
    def tree_hash(self,commit:str,prefix:str)->str:
        result=self._run(["ls-tree","-r","--name-only","-z",commit,"--",prefix])
        if result.returncode:raise GitError("cannot list source tree")
        items=[];base=PurePosixPath(prefix)
        for raw_path in result.stdout.split(b"\0"):
            if not raw_path:continue
            full=raw_path.decode();relative=PurePosixPath(full).relative_to(base).as_posix();p=PurePosixPath(relative)
            if any(x in {"__pycache__",".mypy_cache",".pytest_cache",".ruff_cache"} for x in p.parts) or p.name in {".coverage",".DS_Store"} or p.suffix.lower() in {".pyc",".pyo",".pyd"}:continue
            items.append((relative,self.file(commit,full).raw))
        if not items:raise GitError("empty source tree")
        digest=hashlib.sha256();digest.update(TREE_HASH_DOMAIN)
        for path,raw in sorted(items):
            encoded=path.encode();digest.update(len(encoded).to_bytes(8,"big")+encoded);digest.update(len(raw).to_bytes(8,"big")+raw)
        return digest.hexdigest()

def _schema(selector:str,data:dict[str,Any],contracts:Path,location:str)->list[Finding]:
    return [Finding("PROMOTION_SCHEMA_INVALID",location,e) for e in validate_contract.validation_errors(selector,data,contracts)]
def _active(registry:dict[str,Any])->set[str]:
    skills=registry.get("skills",{});return {n for n,v in skills.items() if isinstance(n,str) and isinstance(v,dict) and v.get("lifecycle")=="active"} if isinstance(skills,dict) else set()
def _skill(registry:dict[str,Any],name:str)->dict[str,Any]|None:
    value=registry.get("skills",{}).get(name) if isinstance(registry.get("skills"),dict) else None;return value if isinstance(value,dict) else None

def _ref(repo:GitRepo,commit:str,reference:object,location:str,prefix:str)->tuple[GitFile|None,list[Finding]]:
    if not isinstance(reference,dict):return None,[Finding(prefix+"_REF_INVALID",location,"reference must be object")]
    try:item=repo.file(commit,reference.get("path"))
    except GitError as exc:return None,[Finding(prefix+"_REF_MISSING",location,str(exc))]
    if reference.get("sha256")!=item.sha256:return item,[Finding(prefix+"_REF_HASH_MISMATCH",location,item.path)]
    return item,[]

def _activation_findings(repo:GitRepo,candidate:str,data:dict[str,Any],skill_id:str,decision:object)->list[Finding]:
    findings=[];subject=data.get("subject",{});summary=data.get("summary",{})
    if subject.get("skill_id")!=skill_id or subject.get("candidate_commit")!=candidate:findings.append(Finding("PROMOTION_ACTIVATION_SUBJECT_MISMATCH","activation/subject","skill or commit differs"))
    if summary.get("decision")!=decision:findings.append(Finding("PROMOTION_DECISION_MISMATCH","activation/summary","decision differs"))
    for path,node in _dicts(data):
        if {"path","sha256"}.issubset(node):
            value=node.get("path")
            if not isinstance(value,str) or not value.startswith(f"skills/{skill_id}/"):findings.append(Finding("PROMOTION_ACTIVATION_EVIDENCE_OUTSIDE_SKILL",_pointer(path),str(value)))
            else:findings+=_ref(repo,candidate,node,_pointer(path),"PROMOTION_CANDIDATE_EVIDENCE")[1]
    return findings

def _maturity_findings(repo:GitRepo,candidate:str,data:dict[str,Any],skill_id:str,decision:object)->list[Finding]:
    findings=[]
    if data.get("skill_id")!=skill_id:findings.append(Finding("PROMOTION_MATURITY_SKILL_MISMATCH","maturity/skill_id","skill differs"))
    routes=data.get("routes",[]);route_map={};eligible=0
    for i,route in enumerate(routes):
        if not isinstance(route,dict) or not isinstance(route.get("route_id"),str):continue
        rid=route["route_id"]
        if rid in route_map:findings.append(Finding("PROMOTION_MATURITY_ROUTE_DUPLICATE",f"routes/{i}",rid))
        route_map[rid]=route;axes=[route.get("invocation_maturity"),route.get("parser_maturity"),route.get("scientific_validation_maturity")]
        if all(a in MATURITY_ORDER for a in axes):
            computed=min(axes,key=lambda a:MATURITY_ORDER[str(a)]);overall=route.get("overall_maturity",{})
            if overall.get("declared")!=computed or overall.get("computed")!=computed:findings.append(Finding("PROMOTION_MATURITY_COMPUTED_MISMATCH",f"routes/{i}",str(computed)))
            ceiling=route.get("claim_ceiling")
            if ceiling in CLAIM_ORDER and CLAIM_ORDER[str(ceiling)]>CLAIM_ORDER[MAX_CLAIM[str(computed)]]:findings.append(Finding("PROMOTION_MATURITY_CLAIM_OVERSTATED",f"routes/{i}",str(ceiling)))
        if route.get("provider_lifecycle")=="active" and route.get("implementation")=="implemented" and route.get("advertised") is True and route.get("overall_maturity",{}).get("computed") in {"real-artifact-validated","tool-integration-validated"}:eligible+=1
        evidence_axes=set()
        for j,evidence in enumerate(route.get("evidence",[])):
            if not isinstance(evidence,dict):continue
            if isinstance(evidence.get("axis"),str):evidence_axes.add(evidence["axis"])
            if evidence.get("source")=="skill-local":
                path=evidence.get("path")
                if not isinstance(path,str) or not path.startswith(f"skills/{skill_id}/"):findings.append(Finding("PROMOTION_MATURITY_EVIDENCE_OUTSIDE_SKILL",f"routes/{i}/evidence/{j}",str(path)))
                else:findings+=_ref(repo,candidate,evidence,f"routes/{i}/evidence/{j}","PROMOTION_CANDIDATE_EVIDENCE")[1]
        for field,axis in (("invocation_maturity","invocation"),("parser_maturity","parser"),("scientific_validation_maturity","scientific_validation")):
            if route.get(field)!="design-only" and axis not in evidence_axes:findings.append(Finding("PROMOTION_MATURITY_AXIS_EVIDENCE_MISSING",f"routes/{i}/{field}",axis))
    if decision=="eligible" and not eligible:findings.append(Finding("PROMOTION_NO_ELIGIBLE_ROUTE","maturity/routes","no eligible route"))
    graph={rid:(r.get("parent_route",{}).get("route_id") if isinstance(r.get("parent_route"),dict) and r["parent_route"].get("scope")=="catalog" else None) for rid,r in route_map.items()}
    for rid,parent in graph.items():
        if parent is not None and parent not in graph:findings.append(Finding("PROMOTION_MATURITY_PARENT_MISSING",rid,str(parent)))
        seen=set();current=rid
        while current is not None:
            if current in seen:findings.append(Finding("PROMOTION_MATURITY_PARENT_CYCLE",rid,current));break
            seen.add(current);current=graph.get(current)
    return findings

def validate_promotion(root:Path,promotion_path:Path,*,review_commit:str|None=None,contracts_dir:Path|None=None)->tuple[list[Finding],dict[str,Any]]:
    root=root.resolve();contracts=(contracts_dir or root/"contracts").resolve();findings=[]
    try:raw=promotion_path.read_bytes();promotion=strict_json.loads_object(raw,promotion_path.name,max_bytes=MAX_BYTES)
    except (OSError,strict_json.StrictJSONError) as exc:return [Finding("PROMOTION_INPUT_INVALID",str(promotion_path),str(exc))],{}
    findings+=_schema("promotion-delta@1.1",promotion,contracts,"promotion")
    try:
        repo=GitRepo(root);base=repo.commit(promotion.get("base_commit"),"base");candidate=repo.commit(promotion.get("candidate_commit"),"candidate");review=repo.commit(review_commit,"review") if review_commit else repo.head()
    except GitError as exc:return sorted(set(findings+[Finding("PROMOTION_COMMIT_INVALID","commits",str(exc))])),{}
    if base==candidate or not repo.ancestor(base,candidate):findings.append(Finding("PROMOTION_CANDIDATE_ORDER_INVALID","commits","base must precede candidate"))
    if candidate==review or not repo.ancestor(candidate,review):findings.append(Finding("PROMOTION_REVIEW_ORDER_INVALID","commits","candidate must precede review"))
    skill_id=promotion.get("skill_id")
    if not isinstance(skill_id,str):return sorted(set(findings)),{}
    source=f"skills/{skill_id}";review_root=f"evidence/promotions/{skill_id}"
    if promotion.get("review_artifact_root")!=review_root:findings.append(Finding("PROMOTION_REVIEW_ROOT_INVALID","review_artifact_root",review_root))
    try:relative=promotion_path.resolve().relative_to(root).as_posix();committed=repo.file(review,relative);findings += [] if committed.raw==raw else [Finding("PROMOTION_RECORD_BYTES_MISMATCH",relative,"bytes differ")]
    except (ValueError,GitError) as exc:findings.append(Finding("PROMOTION_RECORD_NOT_COMMITTED",str(promotion_path),str(exc)))
    try:base_file,base_registry=repo.yaml(base,"registry/skill-registry.yaml");_,candidate_registry=repo.yaml(candidate,"registry/skill-registry.yaml")
    except GitError as exc:return sorted(set(findings+[Finding("PROMOTION_SKILL_REGISTRY_INVALID","registry",str(exc))])),{}
    if promotion.get("base_registry_sha256")!=base_file.sha256:findings.append(Finding("PROMOTION_BASE_REGISTRY_HASH_MISMATCH","base_registry_sha256","mismatch"))
    if not _skill(base_registry,skill_id) or _skill(base_registry,skill_id).get("lifecycle")!="development":findings.append(Finding("PROMOTION_BASE_LIFECYCLE_INVALID",skill_id,"expected development"))
    candidate_skill=_skill(candidate_registry,skill_id)
    if not candidate_skill or candidate_skill.get("lifecycle")!="active":findings.append(Finding("PROMOTION_CANDIDATE_LIFECYCLE_INVALID",skill_id,"expected active"))
    transition=promotion.get("path_transition",{})
    try:tree_hash=repo.tree_hash(candidate,source)
    except GitError as exc:findings.append(Finding("PROMOTION_SOURCE_TREE_INVALID",source,str(exc)));tree_hash=None
    if tree_hash and (transition.get("source_tree_sha256")!=tree_hash or candidate_skill.get("source_tree_sha256")!=tree_hash):findings.append(Finding("PROMOTION_SOURCE_TREE_HASH_MISMATCH",source,"mismatch"))
    try:candidate_diff=repo.diff(base,candidate);review_diff=repo.diff(candidate,review)
    except GitError as exc:findings.append(Finding("PROMOTION_DIFF_INVALID","diff",str(exc)));candidate_diff=set();review_diff=set()
    declared=set(promotion.get("domain_owned_files_changed",[]))|set(promotion.get("shared_files_changed",[]))
    if candidate_diff!=declared:findings.append(Finding("PROMOTION_CANDIDATE_DIFF_MISMATCH","changed_files",f"actual-only={sorted(candidate_diff-declared)} declared-only={sorted(declared-candidate_diff)}"))
    illegal=sorted(p for p in review_diff if not p.startswith(review_root+"/"))
    if illegal:findings.append(Finding("PROMOTION_REVIEW_DIFF_ESCAPES_ARTIFACT_ROOT","review_diff",str(illegal)))
    for location,reference in [("task_maturity_catalog",promotion.get("task_maturity_catalog"))]:findings+=_ref(repo,candidate,reference,location,"PROMOTION_CANDIDATE")[1]
    for location,reference in [("activation_checklist",promotion.get("activation_checklist")),("reports/privacy_license",promotion.get("reports",{}).get("privacy_license"))]+[(f"reports/forward_tests/{i}",r) for i,r in enumerate(promotion.get("reports",{}).get("forward_tests",[]))]:findings+=_ref(repo,review,reference,location,"PROMOTION_REVIEW")[1]
    try:_,activation=repo.json(review,promotion.get("activation_checklist",{}).get("path"));findings+=_schema("activation-checklist@1.1",activation,contracts,"activation")+_activation_findings(repo,candidate,activation,skill_id,promotion.get("decision"))
    except GitError as exc:findings.append(Finding("PROMOTION_ACTIVATION_RECORD_INVALID","activation",str(exc)))
    try:_,maturity=repo.json(candidate,promotion.get("task_maturity_catalog",{}).get("path"));findings+=_schema("task-maturity@1.1",maturity,contracts,"maturity")+_maturity_findings(repo,candidate,maturity,skill_id,promotion.get("decision"))
    except GitError as exc:findings.append(Finding("PROMOTION_MATURITY_RECORD_INVALID","maturity",str(exc)))
    before=_active(base_registry);after=_active(candidate_registry);expected={"before":sorted(before),"after":sorted(after),"added":sorted(after-before),"removed":sorted(before-after)};installer=promotion.get("installer_set",{})
    for field,value in expected.items():
        if sorted(installer.get(field,[]))!=value:findings.append(Finding("PROMOTION_INSTALLER_SET_MISMATCH",f"installer/{field}",str(value)))
    if after-before!={skill_id} or before-after:findings.append(Finding("PROMOTION_ACTIVE_DELTA_INVALID","installer","one addition required"))
    try:
        _,operations=repo.yaml(candidate,"registry/operation-routes.yaml");route=operations.get("routes",{}).get(skill_id)
        if not isinstance(route,dict) or route.get("lifecycle")!="active" or route.get("routable") is not True:findings.append(Finding("PROMOTION_OPERATION_ROUTE_INACTIVE","registry/operation-routes.yaml",skill_id))
        for path in ROUTING_REGISTRIES:
            if repo.file(candidate,path).raw!=repo.file(review,path).raw:findings.append(Finding("PROMOTION_REVIEW_REGISTRY_CHANGED",path,"review changed registry"))
    except GitError as exc:findings.append(Finding("PROMOTION_SHARED_REGISTRY_INVALID","registry",str(exc)))
    findings=sorted(set(findings));report={"schema_version":"1.0","validator":"two-phase-promotion-validator","promotion_id":promotion.get("promotion_id"),"skill_id":skill_id,"base_commit":base,"candidate_commit":candidate,"review_commit":review,"status":"pass" if not findings else "fail","eligible":not findings and promotion.get("decision")=="eligible","finding_count":len(findings),"findings":[{"code":f.code,"location":f.location,"message":f.message} for f in findings]}
    return findings,report

def main(argv:Sequence[str]|None=None)->int:
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("promotion_delta",type=Path);parser.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1]);parser.add_argument("--review-commit");parser.add_argument("--contracts-dir",type=Path);parser.add_argument("--report",type=Path);args=parser.parse_args(argv)
    findings,report=validate_promotion(args.root,args.promotion_delta,review_commit=args.review_commit,contracts_dir=args.contracts_dir)
    if args.report:args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    if findings:
        for finding in findings:print(finding.render(),file=sys.stderr)
        return 2
    if not report.get("eligible"):print("BLOCKED: promotion evidence valid but decision blocked");return 3
    print("PASS: two-phase promotion is commit-bound, hash-closed, registry-consistent, and eligible");return 0
if __name__=="__main__":raise SystemExit(main())
