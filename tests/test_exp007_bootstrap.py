from __future__ import annotations

import unittest

import pandas as pd

from exp007_bootstrap import bootstrap_trade_metrics


class Exp007BootstrapTests(unittest.TestCase):
    def test_bootstrap_is_deterministic(self) -> None:
        trades = pd.DataFrame(
            {"net_pnl_usd": [10.0, -5.0, 20.0, -3.0, 8.0] * 20}
        )
        first = bootstrap_trade_metrics(trades)
        second = bootstrap_trade_metrics(trades)
        self.assertEqual(first, second)

    def test_bootstrap_is_report_only(self) -> None:
        trades = pd.DataFrame(
            {"net_pnl_usd": [10.0, -5.0, 20.0, -3.0] * 30}
        )
        result = bootstrap_trade_metrics(trades)
        self.assertFalse(result["decision_gate"])
        self.assertEqual(result["resamples"], 10000)

    def test_mutated_resample_count_is_rejected(self) -> None:
        trades = pd.DataFrame({"net_pnl_usd": [1.0, -1.0]})
        with self.assertRaisesRegex(ValueError, "10,000"):
            bootstrap_trade_metrics(trades, resamples=100)


if __name__ == "__main__":
    unittest.main()
