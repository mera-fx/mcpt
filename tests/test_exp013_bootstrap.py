from __future__ import annotations

import unittest

import pandas as pd

from exp013_bootstrap import bootstrap_exp013_trade_metrics


class Exp013BootstrapTests(unittest.TestCase):
    def setUp(self) -> None:
        self.trades = pd.DataFrame(
            {"net_pnl_usd": [100.0, -50.0, 75.0, -25.0, 40.0]}
        )

    def test_bootstrap_is_deterministic_and_report_only(self) -> None:
        first = bootstrap_exp013_trade_metrics(
            self.trades, candidate_id="candidate"
        )
        second = bootstrap_exp013_trade_metrics(
            self.trades, candidate_id="candidate"
        )
        self.assertEqual(first, second)
        self.assertEqual(first["resamples"], 10000)
        self.assertEqual(first["random_seed"], 5301)
        self.assertFalse(first["decision_gate"])

    def test_mutated_seed_and_count_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "5301"):
            bootstrap_exp013_trade_metrics(
                self.trades,
                candidate_id="candidate",
                random_seed=1,
            )
        with self.assertRaisesRegex(ValueError, "10,000"):
            bootstrap_exp013_trade_metrics(
                self.trades,
                candidate_id="candidate",
                resamples=100,
            )


if __name__ == "__main__":
    unittest.main()
