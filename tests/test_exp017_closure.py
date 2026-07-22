import unittest
from exp017_closure import get_exp017_closure, validate_exp017_closure

class Exp017ClosureTests(unittest.TestCase):
    def test_valid(self):
        validate_exp017_closure()
    def test_access_incomplete_without_bars(self):
        r = get_exp017_closure()
        self.assertEqual(r["classification"], "ACCESS_INCOMPLETE")
        self.assertEqual(r["benchmark_bar_values_viewed"], "NONE")
        self.assertFalse(r["ohlcv_requested"])
        self.assertFalse(r["ohlcv_downloaded"])
    def test_only_one_accessible_source(self):
        r = get_exp017_closure()["requirement_result"]
        self.assertEqual(r["minimum_sources_required"], 2)
        self.assertEqual(r["accessible_sources_confirmed"], 1)
        self.assertFalse(r["minimum_met"])
        self.assertFalse(r["winner_selected"])
    def test_no_accuracy_claim(self):
        self.assertTrue(
            get_exp017_closure()["interpretation"][
                "exchange_accuracy_not_established"
            ]
        )
    def test_mutation_rejected(self):
        r = get_exp017_closure()
        r["ohlcv_requested"] = True
        with self.assertRaisesRegex(ValueError, "identity"):
            validate_exp017_closure(r)

if __name__ == "__main__":
    unittest.main()
