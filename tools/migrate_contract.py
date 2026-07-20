#!/usr/bin/env python3
"""Migrate one record between contract versions without synthesizing scientific evidence."""

from __future__ import annotations

import argparse, copy, hashlib, json, os, tempfile, sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Sequence

import strict_json
import validate_contract

MAX_BYTES=16*1024*1024
CLAIM_ORDER={"no_positive_claim":0,"documented_behavior_only":1,"input_gates_only":2,"technical_run_gates_only":3,"numerical_candidate_only":4,"eligible_for_expert_review":5}
CLAIM_KEYS={"claim_ceiling","maximum_claim"}
PROTECTED_KEYS={"claim_ceiling","maximum_claim","status","decision","evidence","validation","scientific_acceptance","physical_validity","numerical_convergence","execution_status","reviewer","sha256","source_tree_sha256"}

@dataclass(frozen=True,order=True)
class Finding:
    code:str;location:str;message:str
    def render(self)->str:return f"{self.code}\t{self.location}\t{self.message}"
class MigrationError(ValueError):
    def __init__(self,code:str,location:str,message:str):super().__init__(message);self.code=code;self.location=location;self.message=message
    def finding(self)->Finding:return Finding(self.code,self.location,self.message)

def repo_root()->Path:return Path(__file__).resolve().parents[1]
def _sha(raw:bytes)->str:return hashlib.sha256(raw).hexdigest()
def _safe(value:object)->PurePosixPath|None:
    if not isinstance(value,str) or not value or "\\" in value or "\x00" in value:return None
    path=PurePosixPath(value)
    return None if path.is_absolute() or any(p in {"",".",".."} for p in path.parts) else path
def _resolve(root:Path,value:object,label:str)->Path:
    relative=_safe(value)
    if relative is None:raise MigrationError("MIGRATION_PATH_INVALID",label,str(value))
    target=root.joinpath(*relative.parts)
    try:target.resolve(strict=False).relative_to(root.resolve())
    except ValueError as exc:raise MigrationError("MIGRATION_PATH_ESCAPE",label,str(value)) from exc
    return target

def _decode(pointer:object)->tuple[str,...]:
    if not isinstance(pointer,str) or not pointer.startswith("/"):raise MigrationError("MIGRATION_POINTER_INVALID",str(pointer),"must start with /")
    result=[]
    for raw in pointer[1:].split("/"):
        if not raw:raise MigrationError("MIGRATION_POINTER_INVALID",pointer,"empty segment")
        out="";i=0
        while i<len(raw):
            if raw[i]!="~":out+=raw[i];i+=1
            elif i+1<len(raw) and raw[i+1] in "01":out+=("~" if raw[i+1]=="0" else "/");i+=2
            else:raise MigrationError("MIGRATION_POINTER_INVALID",pointer,"bad escape")
        result.append(out)
    return tuple(result)
def _encode(parts:Iterable[object])->str:return "/"+"/".join(str(p).replace("~","~0").replace("/","~1") for p in parts)
def _get(value:object,parts:Sequence[str],pointer:str)->object:
    current=value
    for part in parts:
        if isinstance(current,dict) and part in current:current=current[part]
        elif isinstance(current,list) and part.isdigit() and int(part)<len(current):current=current[int(part)]
        else:raise MigrationError("MIGRATION_SOURCE_POINTER_MISSING",pointer,"field absent")
    return current
def _parent(value:object,parts:Sequence[str],pointer:str,create:bool)->tuple[object,str]:
    current=value
    for part in parts[:-1]:
        if isinstance(current,dict):
            if part not in current:
                if not create:raise MigrationError("MIGRATION_TARGET_PARENT_MISSING",pointer,"parent absent")
                current[part]={}
            current=current[part]
        elif isinstance(current,list) and part.isdigit() and int(part)<len(current):current=current[int(part)]
        else:raise MigrationError("MIGRATION_TARGET_PARENT_INVALID",pointer,"parent invalid")
        if not isinstance(current,(dict,list)):raise MigrationError("MIGRATION_TARGET_PARENT_INVALID",pointer,"crosses scalar")
    return current,parts[-1]
def _set(value:object,pointer:str,item:object)->None:
    parent,key=_parent(value,_decode(pointer),pointer,True)
    if isinstance(parent,dict):
        if key in parent:raise MigrationError("MIGRATION_TARGET_EXISTS",pointer,"target exists")
        parent[key]=item
    elif isinstance(parent,list) and key.isdigit() and int(key)==len(parent):parent.append(item)
    else:raise MigrationError("MIGRATION_TARGET_INDEX_INVALID",pointer,"invalid target")
def _remove(value:object,pointer:str)->object:
    parent,key=_parent(value,_decode(pointer),pointer,False)
    if isinstance(parent,dict) and key in parent:return parent.pop(key)
    if isinstance(parent,list) and key.isdigit() and int(key)<len(parent):return parent.pop(int(key))
    raise MigrationError("MIGRATION_SOURCE_POINTER_MISSING",pointer,"field absent")
def _walk(value:object,path:tuple[object,...]=()):
    yield path,value
    if isinstance(value,dict):
        for key,child in value.items():yield from _walk(child,(*path,key))
    elif isinstance(value,list):
        for i,child in enumerate(value):yield from _walk(child,(*path,i))
def _protected(value:object)->dict[str,object]:return {_encode(path):copy.deepcopy(child) for path,child in _walk(value) if path and str(path[-1]).lower() in PROTECTED_KEYS}
def _claim(value:object)->str|None:
    found=[]
    for path,child in _walk(value):
        if path and str(path[-1]).lower() in CLAIM_KEYS and isinstance(child,str):
            if child not in CLAIM_ORDER:raise MigrationError("MIGRATION_CLAIM_CEILING_UNKNOWN",_encode(path),child)
            found.append(child)
    return max(found,key=CLAIM_ORDER.__getitem__) if found else None
def _record_id(data:dict[str,Any],contract:validate_contract.ContractSchema)->str|None:
    field=contract.record_id_field;value=data.get(field) if field else None;return value if isinstance(value,str) else None
def _schema(selector:str,data:dict[str,Any],contracts:Path,prefix:str)->list[Finding]:return [Finding("MIGRATION_SCHEMA_INVALID",prefix,e) for e in validate_contract.validation_errors(selector,data,contracts)]
def _atomic(path:Path,raw:bytes)->None:
    path.parent.mkdir(parents=True,exist_ok=True);fd,name=tempfile.mkstemp(prefix=f".{path.name}.",dir=path.parent);tmp=Path(name)
    try:
        with os.fdopen(fd,"wb") as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
        os.replace(tmp,path)
    except Exception:tmp.unlink(missing_ok=True);raise

def migrate(root:Path,plan_path:Path,*,contracts_dir:Path|None=None,write:bool=True)->tuple[list[Finding],dict[str,Any],dict[str,Any]|None]:
    root=root.resolve();contracts=(contracts_dir or root/"contracts").resolve();findings=[]
    try:plan_raw=plan_path.read_bytes();plan=strict_json.loads_object(plan_raw,plan_path.name,max_bytes=MAX_BYTES)
    except (OSError,strict_json.StrictJSONError) as exc:return [Finding("MIGRATION_PLAN_INVALID",str(plan_path),str(exc))],{},None
    findings+=_schema("contract-migration-plan@1.0",plan,contracts,"plan")
    if findings:return sorted(set(findings)),{},None
    source_id=plan["source_contract"];target_id=plan["target_contract"];source_selector=f"{source_id['name']}@{source_id['version']}";target_selector=f"{target_id['name']}@{target_id['version']}"
    if source_id["name"]!=target_id["name"]:findings.append(Finding("MIGRATION_CONTRACT_NAME_CHANGED","target_contract/name","cross-contract migration forbidden"))
    if source_selector==target_selector:findings.append(Finding("MIGRATION_VERSION_UNCHANGED","target_contract/version","versions equal"))
    try:catalog=validate_contract.load_catalog(contracts);source_contract=catalog.resolve(source_selector);target_contract=catalog.resolve(target_selector)
    except Exception as exc:return sorted(set(findings+[Finding("MIGRATION_CONTRACT_UNRESOLVED","contracts",str(exc))])),{},None
    if source_contract.document_kind!="content-addressed-record" or target_contract.document_kind!="content-addressed-record":findings.append(Finding("MIGRATION_RECORD_KIND_UNSUPPORTED","contracts","content-addressed records required"))
    try:source_path=_resolve(root,plan["source_path"],"source_path");output_path=_resolve(root,plan["output_path"],"output_path");record_path=_resolve(root,plan["migration_record_path"],"migration_record_path");plan_relative=plan_path.resolve().relative_to(root).as_posix()
    except (MigrationError,ValueError) as exc:return sorted(set(findings+[(exc.finding() if isinstance(exc,MigrationError) else Finding("MIGRATION_PLAN_PATH_OUTSIDE_ROOT",str(plan_path),str(exc)))])),{},None
    if len({source_path,output_path,record_path,plan_path.resolve()})!=4:findings.append(Finding("MIGRATION_PATH_COLLISION","paths","paths must differ"))
    if output_path.exists() or record_path.exists():findings.append(Finding("MIGRATION_OUTPUT_EXISTS","paths","overwrite forbidden"))
    try:source_raw=source_path.read_bytes();source=strict_json.loads_object(source_raw,source_path.name,max_bytes=MAX_BYTES)
    except (OSError,strict_json.StrictJSONError) as exc:return sorted(set(findings+[Finding("MIGRATION_SOURCE_INVALID",str(source_path),str(exc))])),{},None
    findings+=_schema(source_selector,source,contracts,"source")
    if findings:return sorted(set(findings)),{},None
    before=_protected(source)
    try:claim_before=_claim(source)
    except MigrationError as exc:return [exc.finding()],{},None
    target=copy.deepcopy(source);removed=[]
    try:
        for i,operation in enumerate(plan["operations"]):
            op=operation["op"];pointer=operation["from"];value=copy.deepcopy(_get(target,_decode(pointer),pointer))
            if op=="copy":_set(target,operation["to"],value)
            elif op=="rename":_set(target,operation["to"],value);_remove(target,pointer);removed.append(pointer)
            elif op=="remove":_remove(target,pointer);removed.append(pointer)
            else:raise MigrationError("MIGRATION_OPERATION_INVALID",f"operations/{i}",op)
    except MigrationError as exc:return [exc.finding()],{},None
    target["contract_name"]=target_contract.name;target["schema_version"]=target_contract.version
    if target_contract.record_id_field:target[target_contract.record_id_field]=plan["target_record_id"]
    after=_protected(target)
    for pointer,value in before.items():
        if pointer not in after or after[pointer]!=value:findings.append(Finding("MIGRATION_PROTECTED_FIELD_CHANGED",pointer,"removed or changed"))
    try:claim_after=_claim(target)
    except MigrationError as exc:findings.append(exc.finding());claim_after=None
    if claim_before is not None and (claim_after is None or CLAIM_ORDER[claim_after]>CLAIM_ORDER[claim_before]):findings.append(Finding("MIGRATION_CLAIM_CEILING_INCREASED","claim_ceiling",f"{claim_before}->{claim_after}"))
    findings+=_schema(target_selector,target,contracts,"target")
    if findings:return sorted(set(findings)),{},target
    target_raw=(json.dumps(target,indent=2,sort_keys=True,ensure_ascii=False)+"\n").encode()
    record={"schema_version":"1.0","contract_name":"contract-migration-record","migration_id":f"{plan['plan_id']}-migration","plan_ref":{"path":plan_relative,"sha256":_sha(plan_raw)},"source":{"path":plan["source_path"],"sha256":_sha(source_raw),"contract":source_id,"record_id":_record_id(source,source_contract)},"target":{"path":plan["output_path"],"sha256":_sha(target_raw),"contract":target_id,"record_id":_record_id(target,target_contract)},"operations":plan["operations"],"preserved_protected_pointers":sorted(before),"removed_pointers":sorted(set(removed)),"evidence_boundary":{"scientific_values_synthesized":False,"protected_fields_preserved":True,"claim_ceiling_before":claim_before,"claim_ceiling_after":claim_after},"validation":{"source_schema_valid":True,"target_schema_valid":True},"provenance":plan["provenance"]}
    findings+=_schema("contract-migration-record@1.0",record,contracts,"migration_record")
    if findings:return sorted(set(findings)),record,target
    record_raw=(json.dumps(record,indent=2,sort_keys=True,ensure_ascii=False)+"\n").encode()
    if write:
        try:_atomic(output_path,target_raw);_atomic(record_path,record_raw)
        except OSError as exc:output_path.unlink(missing_ok=True);record_path.unlink(missing_ok=True);return [Finding("MIGRATION_WRITE_FAILED","outputs",str(exc))],record,target
    return [],record,target

def main(argv:Sequence[str]|None=None)->int:
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("plan",type=Path);parser.add_argument("--root",type=Path,default=repo_root());parser.add_argument("--contracts-dir",type=Path);parser.add_argument("--dry-run",action="store_true");parser.add_argument("--report",type=Path);args=parser.parse_args(argv)
    findings,record,_=migrate(args.root,args.plan,contracts_dir=args.contracts_dir,write=not args.dry_run);report={"schema_version":"1.0","status":"pass" if not findings else "fail","migration_id":record.get("migration_id") if record else None,"dry_run":args.dry_run,"findings":[{"code":f.code,"location":f.location,"message":f.message} for f in findings]}
    if args.report:args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    if findings:
        for finding in findings:print(finding.render(),file=sys.stderr)
        return 2
    print("PASS: contract migration completed without synthesizing scientific evidence");return 0
if __name__=="__main__":raise SystemExit(main())
