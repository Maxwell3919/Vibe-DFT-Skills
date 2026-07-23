from __future__ import annotations

import hashlib,json
from pathlib import Path
import sys,tempfile,unittest

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"tools"))
import migrate_contract,validate_contract
CHECK_IDS=["identity-and-routing","primary-source-provenance","capability-boundary","deterministic-gates","lineage-and-hashes","scientific-gate-separation","shared-interfaces","side-effect-boundary","idempotency-recovery-cancel","validation-evidence","privacy-and-license","portability-and-environment","maintenance-and-forward-test"]

def source_record():
    digest=hashlib.sha256(b"synthetic migration evidence\n").hexdigest();checks=[]
    for i,cid in enumerate(CHECK_IDS):
        checks.append({"check_id":cid,"status":"pass","evidence":[{"evidence_id":f"migration-evidence-{i:02d}","kind":"test-report","path":"skills/example-skill/validation/evidence.txt","sha256":digest}],"reviewer":{"reviewer_id":f"migration-reviewer-{i:02d}","role":"independent-technical-reviewer","independent_of_implementation":True},"validated_utc":"2026-07-21T00:00:00Z","not_applicable_reason":None,"limitations":[]})
    return {"schema_version":"1.0","contract_name":"activation-checklist","checklist_id":"migration-source-checklist","subject":{"skill_id":"example-skill","software_ids":[],"candidate_commit":"a"*40},"profile_ids":["example-profile"],"checks":checks,"summary":{"decision":"eligible","blocker_check_ids":[],"limitations":["Synthetic contract-migration fixture only"]},"provenance":{"producer":"contract-migration-test","producer_version":"1.0","generated_utc":"2026-07-21T00:00:00Z"}}
def plan(operations=None):
    return {"schema_version":"1.0","contract_name":"contract-migration-plan","plan_id":"activation-1.0-to-1.1","source_contract":{"name":"activation-checklist","version":"1.0"},"target_contract":{"name":"activation-checklist","version":"1.1"},"source_path":"records/source.json","output_path":"records/target.json","migration_record_path":"records/migration.json","target_record_id":"migration-target-checklist","operations":operations or [],"provenance":{"producer":"contract-migration-test","producer_version":"1.0","generated_utc":"2026-07-21T00:00:00Z"}}

class ContractMigrationTests(unittest.TestCase):
    def setup_repo(self,root:Path,p=None):
        (root/"records").mkdir();(root/"plans").mkdir();(root/"records/source.json").write_text(json.dumps(source_record(),indent=2,sort_keys=True)+"\n",encoding="utf-8");path=root/"plans/migration.json";path.write_text(json.dumps(p or plan(),indent=2,sort_keys=True)+"\n",encoding="utf-8");return path
    def run_migration(self,root,path,write=True):return migrate_contract.migrate(root,path,contracts_dir=ROOT/"contracts",write=write)
    def test_valid_migration(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);path=self.setup_repo(root);findings,record,target=self.run_migration(root,path)
            self.assertEqual(findings,[]);self.assertEqual(target["schema_version"],"1.1");self.assertEqual(target["checklist_id"],"migration-target-checklist");self.assertFalse(record["evidence_boundary"]["scientific_values_synthesized"])
            target_data=json.loads((root/"records/target.json").read_text());record_data=json.loads((root/"records/migration.json").read_text())
            self.assertEqual(validate_contract.validation_errors("activation-checklist@1.1",target_data,ROOT/"contracts"),[]);self.assertEqual(validate_contract.validation_errors("contract-migration-record@1.0",record_data,ROOT/"contracts"),[])
    def test_dry_run_no_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);path=self.setup_repo(root);findings,_,target=self.run_migration(root,path,False);self.assertEqual(findings,[]);self.assertIsNotNone(target);self.assertFalse((root/"records/target.json").exists())
    def test_protected_summary_removal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);path=self.setup_repo(root,plan([{"op":"remove","from":"/summary"}]));findings,_,_=self.run_migration(root,path);self.assertIn("MIGRATION_PROTECTED_FIELD_CHANGED",{f.code for f in findings});self.assertFalse((root/"records/target.json").exists())
    def test_required_field_removal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);path=self.setup_repo(root,plan([{"op":"remove","from":"/profile_ids"}]));findings,_,_=self.run_migration(root,path);self.assertIn("MIGRATION_SCHEMA_INVALID",{f.code for f in findings});self.assertFalse((root/"records/target.json").exists())
    def test_existing_output_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);path=self.setup_repo(root);out=root/"records/target.json";out.write_text("keep\n");findings,_,_=self.run_migration(root,path);self.assertIn("MIGRATION_OUTPUT_EXISTS",{f.code for f in findings});self.assertEqual(out.read_text(),"keep\n")
    def test_same_version_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);p=plan();p["target_contract"]={"name":"activation-checklist","version":"1.0"};path=self.setup_repo(root,p);findings,_,_=self.run_migration(root,path);self.assertIn("MIGRATION_VERSION_UNCHANGED",{f.code for f in findings})

if __name__=="__main__":unittest.main()
