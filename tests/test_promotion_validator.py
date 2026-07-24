from __future__ import annotations

import hashlib,json
from pathlib import Path
import subprocess,sys,tempfile,unittest

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"tools"))
from skill_registry import source_tree_digest
import validate_promotion
CHECK_IDS=["identity-and-routing","primary-source-provenance","capability-boundary","deterministic-gates","lineage-and-hashes","scientific-gate-separation","shared-interfaces","side-effect-boundary","idempotency-recovery-cancel","validation-evidence","privacy-and-license","portability-and-environment","maintenance-and-forward-test"]

class Repo:
    def __init__(self,root):self.root=root;self.git("init","-q");self.git("config","user.email","test@example.invalid");self.git("config","user.name","Promotion Test")
    def git(self,*args):
        result=subprocess.run(["git","-C",str(self.root),*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        if result.returncode:raise AssertionError(result.stderr)
        return result.stdout.strip()
    def write(self,path,content):
        target=self.root/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(content if isinstance(content,bytes) else content.encode())
    def json(self,path,value):raw=(json.dumps(value,indent=2,sort_keys=True)+"\n").encode();self.write(path,raw);return hashlib.sha256(raw).hexdigest()
    def commit(self,msg):self.git("add","-A");self.git("commit","-q","-m",msg);return self.git("rev-parse","HEAD")
    def show(self,commit,path):return subprocess.check_output(["git","-C",str(self.root),"show",f"{commit}:{path}"])
    def diff(self,a,b):return sorted(x for x in self.git("diff","--name-only",a,b,"--").splitlines() if x)

def skill_registry(lifecycle,digest):
    return f'''schema_version: "1.0"\nskills:\n  example-skill:\n    display_name: Example Skill\n    kind: advisory\n    lifecycle: {lifecycle}\n    path: skills/example-skill\n    source_tree_sha256: "{digest}"\n    side_effects: []\n    consumes: []\n    produces: []\n    activation_requirements:\n      software_profiles: []\n      interface_ids: []\n      activation_check_ids: []\n      task_catalog_ids: []\n'''
def operations(lifecycle,routable):
    return f'''schema_version: "1.0"\nroutes:\n  example-skill:\n    lifecycle: {lifecycle}\n    routable: {'true' if routable else 'false'}\n    required_reads: [skills/example-skill/SKILL.md]\n    first_tool: {{}}\n    tool_sequence: {{}}\n    side_effects: []\n    minimum_evidence: []\n    maximum_claim: documented_behavior_only\n'''
def maturity(digest):
    path="skills/example-skill/validation/evidence.txt";e=[]
    for eid,axis,level,kind in [("invoke","invocation","tool-integration-validated","invocation-tool-integration-test"),("parse","parser","real-artifact-validated","parser-real-artifact-test"),("science","scientific_validation","real-artifact-validated","scientific-real-artifact-validation")]:e.append({"evidence_id":eid,"axis":axis,"maturity_level":level,"kind":kind,"provider_version":"1.0","source":"skill-local","path":path,"external_record_ref":None,"sha256":digest})
    return {"schema_version":"1.1","contract_name":"task-maturity","catalog_id":"example-maturity","skill_id":"example-skill","aggregate":False,"routes":[{"route_id":"example/primary","provider_id":"example-provider","provider_lifecycle":"active","task_id":"example-task","parent_route":None,"provider_version":"1.0","implementation":"implemented","invocation_maturity":"tool-integration-validated","parser_maturity":"real-artifact-validated","scientific_validation_maturity":"real-artifact-validated","overall_maturity":{"declared":"real-artifact-validated","computed":"real-artifact-validated"},"claim_ceiling":"numerical_candidate_only","advertised":True,"execution_capability":True,"unknown_version_policy":"block","evidence":e,"limitations":["Synthetic fixture"]}],"provenance":{"producer":"promotion-test","producer_version":"1.0","generated_utc":"2026-07-21T00:00:00Z"}}
def activation(candidate,digest,bad=False):
    checks=[];selected="0"*64 if bad else digest
    for i,cid in enumerate(CHECK_IDS):checks.append({"check_id":cid,"status":"pass","evidence":[{"evidence_id":f"e-{i}","kind":"test-report","path":"skills/example-skill/validation/evidence.txt","sha256":selected}],"reviewer":{"reviewer_id":f"reviewer-{i}","role":"independent-technical-reviewer","independent_of_implementation":True},"validated_utc":"2026-07-21T00:00:00Z","not_applicable_reason":None,"limitations":[]})
    return {"schema_version":"1.1","contract_name":"activation-checklist","checklist_id":"example-activation","subject":{"skill_id":"example-skill","software_ids":[],"candidate_commit":candidate},"profile_ids":["example-profile"],"checks":checks,"summary":{"decision":"eligible","blocker_check_ids":[],"limitations":[]},"provenance":{"producer":"promotion-test","producer_version":"1.0","generated_utc":"2026-07-21T00:00:00Z"}}

class PromotionTests(unittest.TestCase):
    def build(self,root,omit=False,bad_tree=False,bad_evidence=False,escape=False,pack=False):
        r=Repo(root);r.write("skills/example-skill/SKILL.md","development\n");base_hash=source_tree_digest(root/"skills/example-skill").sha256;r.write("registry/skill-registry.yaml",skill_registry("development",base_hash));r.write("registry/interface-registry.yaml",'schema_version: "1.0"\ninterfaces: {}\n');r.write("registry/operation-routes.yaml",operations("development",False));r.write("registry/software-registry.yaml",'schema_version: "1.0"\naggregate_codes: []\nsoftware: {}\nplanned_software: {}\n');r.write("registry/environment-profiles.yaml",'schema_version: "1.0"\nas_of: "2026-07-21"\nsnapshot: {}\nprofiles: {}\n');base=r.commit("base");base_registry_sha=hashlib.sha256(r.show(base,"registry/skill-registry.yaml")).hexdigest()
        raw=b"synthetic promotion evidence\n";digest=hashlib.sha256(raw).hexdigest();r.write("skills/example-skill/SKILL.md","active\n");r.write("skills/example-skill/validation/evidence.txt",raw);maturity_path="skills/example-skill/references/task-maturity.json";maturity_sha=r.json(maturity_path,maturity(digest));
        if pack:r.json("skills/example-skill/references/official-source-pack/bundle.json",{"bound_tree":"0"*64})
        tree=source_tree_digest(root/"skills/example-skill").sha256;recorded="0"*64 if bad_tree else tree;r.write("registry/skill-registry.yaml",skill_registry("active",recorded));r.write("registry/interface-registry.yaml",'# candidate\nschema_version: "1.0"\ninterfaces: {}\n');r.write("registry/operation-routes.yaml",operations("active",True));candidate=r.commit("candidate");diff=r.diff(base,candidate);domain=[p for p in diff if p.startswith("skills/example-skill/")];shared=[p for p in diff if not p.startswith("skills/example-skill/")];domain=domain[1:] if omit else domain
        rootdir="evidence/promotions/example-skill";privacy=f"{rootdir}/privacy.txt";forward=f"{rootdir}/forward.txt";act=f"{rootdir}/activation.json";prom=f"{rootdir}/promotion.json";r.write(privacy,"privacy pass\n");r.write(forward,"forward pass\n");act_sha=r.json(act,activation(candidate,digest,bad_evidence));promotion={"schema_version":"1.1","contract_name":"promotion-delta","promotion_id":"example-promotion","skill_id":"example-skill","skill_kind":"advisory","software_backed":False,"base_commit":base,"candidate_commit":candidate,"base_registry_sha256":base_registry_sha,"review_artifact_root":rootdir,"lifecycle_transition":{"from":"development","to":"active"},"path_transition":{"from":"skills/example-skill","to":"skills/example-skill","source_tree_sha256":recorded},"domain_owned_files_changed":domain,"shared_files_changed":shared,"software_entries_moved":[],"interface_changes":[],"contracts_changed":[],"observable_route_decisions":[],"task_maturity_catalog":{"path":maturity_path,"sha256":maturity_sha},"activation_checklist":{"path":act,"sha256":act_sha},"installer_set":{"before":[],"after":["example-skill"],"added":["example-skill"],"removed":[]},"reports":{"privacy_license":{"report_id":"privacy-report","path":privacy,"sha256":hashlib.sha256(b"privacy pass\n").hexdigest(),"status":"pass","validated_utc":"2026-07-21T00:00:00Z"},"forward_tests":[{"report_id":"forward-report","path":forward,"sha256":hashlib.sha256(b"forward pass\n").hexdigest(),"status":"pass","validated_utc":"2026-07-21T00:00:00Z"}]},"known_limitations":["Synthetic fixture"],"blockers":[],"decision":"eligible","provenance":{"producer":"promotion-test","producer_version":"1.0","generated_utc":"2026-07-21T00:00:00Z"}};r.json(prom,promotion)
        if escape:r.write("outside.txt","forbidden\n")
        return root/prom,r.commit("review")
    def codes(self,root,path,review):
        findings,report=validate_promotion.validate_promotion(root,path,review_commit=review,contracts_dir=ROOT/"contracts");return {f.code for f in findings},report
    def test_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);path,review=self.build(root);codes,report=self.codes(root,path,review);self.assertEqual(codes,set());self.assertTrue(report["eligible"])
    def test_official_source_pack_uses_the_independent_hash_domain(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);path,review=self.build(root,pack=True);codes,report=self.codes(root,path,review);self.assertEqual(codes,set());self.assertTrue(report["eligible"])
    def test_omitted_diff(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);path,review=self.build(root,omit=True);self.assertIn("PROMOTION_CANDIDATE_DIFF_MISMATCH",self.codes(root,path,review)[0])
    def test_tree_tamper(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);path,review=self.build(root,bad_tree=True);self.assertIn("PROMOTION_SOURCE_TREE_HASH_MISMATCH",self.codes(root,path,review)[0])
    def test_review_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);path,review=self.build(root,escape=True);self.assertIn("PROMOTION_REVIEW_DIFF_ESCAPES_ARTIFACT_ROOT",self.codes(root,path,review)[0])
    def test_evidence_tamper(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);path,review=self.build(root,bad_evidence=True);self.assertIn("PROMOTION_CANDIDATE_EVIDENCE_REF_HASH_MISMATCH",self.codes(root,path,review)[0])

if __name__=="__main__":unittest.main()
