from __future__ import annotations

import copy,json,math
from pathlib import Path
import sys,tempfile,unittest

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"tools"))
import validate_qe_2d_epc as validator
GOLDEN=ROOT/"golden-bundles"/"qe-2d-epc-v1"/"evidence.json"

class QE2DEPCValidationTests(unittest.TestCase):
    def data(self):return json.loads(GOLDEN.read_text(encoding="utf-8"))
    def mutate(self,fn):
        data=copy.deepcopy(self.data());fn(data)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"evidence.json";path.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n",encoding="utf-8")
            findings,report=validator.validate_evidence(path,contracts_dir=ROOT/"contracts")
        return {f.code for f in findings},report
    def test_golden_passes(self):
        findings,report=validator.validate_evidence(GOLDEN,contracts_dir=ROOT/"contracts")
        self.assertEqual(findings,[]);self.assertEqual(report["maximum_claim"],"technical_run_gates_only");self.assertFalse(report["native_execution_established"]);self.assertFalse(report["scientific_acceptance_established"])
        self.assertTrue(math.isclose(report["computed"]["lambda_integrated"],0.8632857142857143,rel_tol=1e-14))
        self.assertTrue(math.isclose(report["computed"]["omega_log_mev_integrated"],17.071652491805146,rel_tol=1e-14))
        self.assertTrue(math.isclose(report["computed"]["tc_kelvin_recomputed"],10.764537564017099,rel_tol=1e-14))
    def test_alpha2f_lambda_mismatch(self):
        codes,_=self.mutate(lambda d:d["epc"].__setitem__("lambda_reported",1.2));self.assertIn("QE_EPC_ALPHA2F_LAMBDA_MISMATCH",codes)
    def test_q_weight_mismatch(self):
        codes,_=self.mutate(lambda d:d["phonons"]["q_points"][0].__setitem__("weight",0.2));self.assertIn("QE_EPC_Q_WEIGHT_NOT_CLOSED",codes)
    def test_imaginary_modes_block(self):
        def change(d):d["phonons"]["imaginary_modes_mev"]=[-2.0];d["phonons"]["unresolved_imaginary_modes"]=True
        codes,_=self.mutate(change);self.assertIn("QE_EPC_IMAGINARY_MODES_UNRESOLVED",codes);self.assertIn("QE_EPC_IMAGINARY_MODE_TOLERANCE_EXCEEDED",codes)
    def test_stage_identity_mismatch(self):
        codes,_=self.mutate(lambda d:d["stage_identity"][2].__setitem__("pseudopotential_set_sha256","0"*64));self.assertIn("QE_EPC_STAGE_IDENTITY_MISMATCH",codes)
    def test_synthetic_claim_overstatement(self):
        codes,_=self.mutate(lambda d:d.__setitem__("claim_ceiling","eligible_for_expert_review"));self.assertIn("QE_EPC_CLAIM_CEILING_OVERSTATED",codes)
    def test_invalid_frequency_grid(self):
        with self.assertRaises(ValueError):validator.integrate_alpha2f([5,5,10],[.1,.2,.3])

if __name__=="__main__":unittest.main()
