from __future__ import annotations

import unittest

import pandas as pd

from exp010_bootstrap import bootstrap_exp010_trade_metrics


class Exp010BootstrapTests(unittest.TestCase):
    def setUp(self) -> None:
        self.trades = pd.DataFrame(
            {"net_pnl_usd": [100.0, -50.0, 75.0, -25.0, 40.0]}
        )

    def test_bootstrap_is_deterministic(self) -> None:
        first = bootstrap_exp010_trade_metrics(
            self.trades, candidate_id="candidate"
        )
        second = bootstrap_exp010_trade_metrics(
            self.trades, candidate_id="candidate"
        )
        self.assertEqual(first, second)

    def test_bootstrap_is_report_only(self) -> None:
        result = bootstrap_exp010_trade_metrics(
            self.trades, candidate_id="candidate"
        )
        self.assertEqual(result["resamples"], 10000)
        self.assertEqual(result["random_seed"], 5001)
        self.assertFalse(result["decision_gate"])
        self.assertIn("profit_factor_probability_above_one", result)

    def test_mutated_seed_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "5001"):
            bootstrap_exp010_trade_metrics(
                self.trades,
                candidate_id="candidate",
                random_seed=5002,
            )


if __name__ == "__main__":
    unittest.main()
