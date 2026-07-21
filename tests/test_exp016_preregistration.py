from __future__ import annotations
import unittest
from exp016_preregistration import EXP015_FROZEN_EVIDENCE,FIXED_SAMPLE_WINDOWS,get_exp016_preregistration,validate_exp016_preregistration

class Exp016PreregistrationTests(unittest.TestCase):
    def test_preregistration_is_valid(self):
        validate_exp016_preregistration()
    def test_scope_is_nq_f_sample_only(self):
        s=get_exp016_preregistration()["scope"]
        self.assertEqual((s["market"],s["vendor_symbol"],s["timeframe"]),("NQ only","NQ.F","1m"))
        self.assertTrue(s["sample_audit_only"])
        self.assertTrue(s["full_history_download_prohibited"])
        self.assertTrue(s["mnq_out_of_scope"])
        self.assertTrue(s["primary_source_replacement_prohibited"])
        self.assertTrue(s["strategy_replay_prohibited"])
        self.assertTrue(s["strategy_optimization_prohibited"])
    def test_exp015_evidence_is_frozen(self):
        p=get_exp016_preregistration()["prior_research"]
        self.assertEqual(p["exp015_frozen_evidence"],EXP015_FROZEN_EVIDENCE)
        self.assertEqual(EXP015_FROZEN_EVIDENCE["final_commit"][:7],"bd87744")
        self.assertEqual(EXP015_FROZEN_EVIDENCE["nq_symbol"],"NQ.F")
        self.assertEqual(EXP015_FROZEN_EVIDENCE["mnq_candidate_count"],0)
    def test_access_is_six_requests_and_no_catalog_rerun(self):
        a=get_exp016_preregistration()["access_safety"]
        self.assertEqual(a["maximum_remote_history_requests_per_run"],6)
        self.assertTrue(a["one_request_per_window"])
        self.assertTrue(a["catalog_rerun_prohibited"])
        self.assertTrue(a["api_key_must_not_be_printed"])
        self.assertTrue(a["api_key_must_not_be_written"])
    def test_six_windows_are_locked(self):
        s=get_exp016_preregistration()["sample_plan"]
        self.assertEqual(tuple(s["sample_windows"]),FIXED_SAMPLE_WINDOWS)
        self.assertEqual(s["sample_window_count"],6)
        self.assertTrue(s["windows_locked_before_history_access"])
        self.assertTrue(s["window_changes_after_results_prohibited"])
        self.assertTrue(s["full_2020_2025_vendor_download_prohibited"])
    def test_methodology_starts_unresolved(self):
        m=get_exp016_preregistration()["methodology_boundary"]
        self.assertEqual(m["contract_type"],"UNRESOLVED")
        self.assertEqual(m["roll_method"],"UNRESOLVED")
        self.assertEqual(m["price_adjustment"],"UNRESOLVED")
        self.assertTrue(m["no_inference_from_symbol_suffix"])
    def test_highest_result_is_supplementary(self):
        q=get_exp016_preregistration()["interpretation"]
        self.assertEqual(q["highest_possible_classification"],"QUALIFIED_AS_SUPPLEMENTARY_NQ_SOURCE")
        self.assertTrue(q["cannot_qualify_primary_source"])
        self.assertTrue(q["cannot_qualify_mnq"])
        self.assertFalse(q["paper_trading_authorized"])
        self.assertFalse(q["live_trading_authorized"])
    def test_scope_mutation_is_rejected(self):
        r=get_exp016_preregistration(); r["scope"]["full_history_download_prohibited"]=False
        with self.assertRaisesRegex(ValueError,'scope'):
            validate_exp016_preregistration(r)
    def test_window_mutation_is_rejected(self):
        r=get_exp016_preregistration(); r["sample_plan"]["sample_windows"]=list(FIXED_SAMPLE_WINDOWS[:-1])
        with self.assertRaisesRegex(ValueError,'sample plan'):
            validate_exp016_preregistration(r)
    def test_primary_claim_is_rejected(self):
        r=get_exp016_preregistration(); r["interpretation"]["cannot_qualify_primary_source"]=False
        with self.assertRaisesRegex(ValueError,'interpretation'):
            validate_exp016_preregistration(r)

if __name__=='__main__':
    unittest.main()
