from __future__ import annotations

import unittest

import pandas as pd

from exp008_bootstrap import (
    bootstrap_exp008_trade_metrics,
)


class Exp008BootstrapTests(
    unittest.TestCase
):
    def setUp(self) -> None:
        self.trades = pd.DataFrame(
            {
                "net_pnl_usd": [
                    100.0,
                    -50.0,
                    75.0,
                    -25.0,
                    125.0,
                    -40.0,
                ]
            }
        )

    def test_bootstrap_is_deterministic(
        self,
    ) -> None:
        first = (
            bootstrap_exp008_trade_metrics(
                self.trades
            )
        )
        second = (
            bootstrap_exp008_trade_metrics(
                self.trades
            )
        )
        self.assertEqual(
            first,
            second,
        )

    def test_bootstrap_is_report_only(
        self,
    ) -> None:
        result = (
            bootstrap_exp008_trade_metrics(
                self.trades
            )
        )
        self.assertFalse(
            result["decision_gate"]
        )
        self.assertEqual(
            result["resamples"],
            10000,
        )
        self.assertEqual(
            result["random_seed"],
            4801,
        )

    def test_mutated_resample_count_is_rejected(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "10,000",
        ):
            bootstrap_exp008_trade_metrics(
                self.trades,
                resamples=1000,
            )


if __name__ == "__main__":
    unittest.main()
