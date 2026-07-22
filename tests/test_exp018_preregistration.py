import unittest
from exp018_preregistration import (
    REPEATABILITY_WINDOW_IDS,
    get_exp018_preregistration,
    validate_exp018_preregistration,
)

class Exp018PreregistrationTests(unittest.TestCase):
    def test_valid(self):
        validate_exp018_preregistration()
    def test_six_locked_windows(self):
        r = get_exp018_preregistration()
        self.assertEqual(len(r["sample_plan"]["windows"]), 6)
        self.assertEqual(r["sample_plan"]["maximum_successful_bar_requests"], 8)
    def test_repeatability(self):
        self.assertEqual(
            REPEATABILITY_WINDOW_IDS,
            ("nqz24_thanksgiving", "nqh25_march_dst"),
        )
        r = get_exp018_preregistration()["repeatability"]
        self.assertEqual(r["minimum_delay_hours"], 24)
        self.assertTrue(r["identical_canonical_rows_required"])
    def test_cost_and_retry_boundary(self):
        r = get_exp018_preregistration()["access"]
        self.assertEqual(r["maximum_total_cost_usd"], 1.0)
        self.assertTrue(r["automatic_retry_prohibited"])
    def test_no_strategy_or_trading_authority(self):
        r = get_exp018_preregistration()["scope"]
        self.assertTrue(r["strategy_replay_prohibited"])
        self.assertTrue(r["strategy_optimization_prohibited"])
        self.assertFalse(r["paper_trading_authorized"])
        self.assertFalse(r["live_trading_authorized"])
    def test_mutation_rejected(self):
        r = get_exp018_preregistration()
        r["access"]["maximum_total_cost_usd"] = 2.0
        with self.assertRaisesRegex(ValueError, "cost"):
            validate_exp018_preregistration(r)

if __name__ == "__main__":
    unittest.main()
