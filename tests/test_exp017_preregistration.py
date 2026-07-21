from __future__ import annotations
import unittest
from exp017_preregistration import EXACT_CONTRACT_WINDOWS, REPEATABILITY_WINDOW_IDS, SOURCE_ROLE_IDS, get_exp017_preregistration, validate_exp017_preregistration

class Exp017PreregistrationTests(unittest.TestCase):
    def test_preregistration_is_valid(self): validate_exp017_preregistration()
    def test_six_exact_contracts(self):
        self.assertEqual(tuple(x["canonical_contract"] for x in EXACT_CONTRACT_WINDOWS),("NQH24","NQM24","NQU24","NQZ24","NQH25","NQM25"))
    def test_no_continuous_series(self):
        s=get_exp017_preregistration()["scope"]
        self.assertTrue(s["exact_quarterly_contracts_only"]); self.assertTrue(s["continuous_symbols_prohibited"]); self.assertTrue(s["back_adjusted_series_prohibited"])
    def test_source_lock_precedes_bars(self):
        x=get_exp017_preregistration()["source_lock_stage"]
        self.assertTrue(x["required_before_any_benchmark_bars"]); self.assertTrue(x["bar_value_access_before_source_lock_prohibited"]); self.assertEqual(tuple(x["source_roles"]),SOURCE_ROLE_IDS)
    def test_two_sources_cannot_identify_truth(self):
        r=get_exp017_preregistration()
        self.assertTrue(r["source_lock_stage"]["two_source_disagreement_cannot_select_winner"])
        self.assertTrue(r["reference_logic"]["two_sources_only_means_disagreement_unresolved"])
        self.assertTrue(r["source_lock_stage"]["quantower_not_assumed_ground_truth"])
        self.assertTrue(r["source_lock_stage"]["london_not_assumed_inaccurate"])
    def test_repeatability_locked(self): self.assertEqual(REPEATABILITY_WINDOW_IDS,("nqz24_thanksgiving","nqh25_march_dst"))
    def test_quality_precedes_cost(self):
        r=get_exp017_preregistration()
        self.assertTrue(r["objective"]["data_quality_precedes_cost"]); self.assertTrue(r["selection_rule"]["cost_cannot_rescue_weaker_data_quality"])
    def test_no_trading_authority(self):
        r=get_exp017_preregistration()
        self.assertFalse(r["scope"]["paper_trading_authorized"]); self.assertFalse(r["scope"]["live_trading_authorized"])
        self.assertTrue(r["interpretation"]["next_experiment_required_for_full_history_and_roll_build"])
    def test_mutation_rejected(self):
        r=get_exp017_preregistration(); r["scope"]["continuous_symbols_prohibited"]=False
        with self.assertRaisesRegex(ValueError,"scope"): validate_exp017_preregistration(r)

if __name__=="__main__": unittest.main()
