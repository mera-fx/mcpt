from __future__ import annotations

import unittest

from exp007_orb import run_exp007_orb
from tests.exp007_test_data import make_exp007_one_minute_data


class Exp007OrbTests(unittest.TestCase):
    def test_target_fills_at_one_r(self) -> None:
        data = make_exp007_one_minute_data(
            ["2024-01-03"], outcomes=["target"]
        )
        result = run_exp007_orb(data, symbol="NQ")
        trade = result.trades.iloc[0]
        self.assertEqual(trade["exit_reason"], "one_r_target")
        self.assertAlmostEqual(trade["gross_r_multiple"], 1.0)
        self.assertAlmostEqual(trade["gross_pnl_usd"], 50.0)
        self.assertAlmostEqual(trade["net_pnl_usd"], 35.0)

    def test_same_minute_stop_and_target_uses_stop(self) -> None:
        data = make_exp007_one_minute_data(
            ["2024-01-03"], outcomes=["both"]
        )
        result = run_exp007_orb(data, symbol="NQ")
        self.assertEqual(
            result.trades.iloc[0]["exit_reason"],
            "opening_range_stop",
        )
        self.assertLess(result.trades.iloc[0]["net_pnl_usd"], 0.0)

    def test_gap_through_stop_uses_open(self) -> None:
        data = make_exp007_one_minute_data(
            ["2024-01-03"], outcomes=["gap_stop"]
        )
        result = run_exp007_orb(data, symbol="NQ")
        trade = result.trades.iloc[0]
        self.assertEqual(
            trade["exit_reason"],
            "gap_through_opening_range_stop",
        )
        self.assertAlmostEqual(trade["exit_price"], 98.5)

    def test_time_exit_uses_1400_open(self) -> None:
        data = make_exp007_one_minute_data(
            ["2024-01-03"], outcomes=["time"]
        )
        result = run_exp007_orb(data, symbol="NQ")
        trade = result.trades.iloc[0]
        self.assertEqual(trade["exit_reason"], "forced_flat_1400")
        self.assertAlmostEqual(trade["exit_price"], 102.0)

    def test_no_short_trades_are_created(self) -> None:
        data = make_exp007_one_minute_data(
            ["2024-01-03", "2024-01-04"],
            outcomes=["target", "stop"],
        )
        result = run_exp007_orb(data, symbol="NQ")
        self.assertEqual(result.summary["short_trades"], 0)
        self.assertTrue((result.trades["direction"] == "long").all())

    def test_no_signal_means_no_trade(self) -> None:
        data = make_exp007_one_minute_data(
            ["2024-01-03"], outcomes=["no_signal"]
        )
        result = run_exp007_orb(data, symbol="NQ")
        self.assertEqual(result.summary["completed_trades"], 0)
        self.assertTrue(result.trades.empty)

    def test_two_tick_stress_has_lower_net_profit(self) -> None:
        data = make_exp007_one_minute_data(
            ["2024-01-03"], outcomes=["target"]
        )
        base = run_exp007_orb(
            data, symbol="NQ", slippage_ticks_per_side=1.0
        )
        stress = run_exp007_orb(
            data, symbol="NQ", slippage_ticks_per_side=2.0
        )
        self.assertAlmostEqual(
            base.summary["net_profit_usd"]
            - stress.summary["net_profit_usd"],
            10.0,
        )

    def test_yearly_results_are_complete(self) -> None:
        data = make_exp007_one_minute_data(
            ["2023-01-03", "2024-01-03"],
            outcomes=["target", "stop"],
        )
        result = run_exp007_orb(data, symbol="MNQ")
        self.assertEqual(result.yearly_results["year"].tolist(), [2023, 2024])


if __name__ == "__main__":
    unittest.main()
