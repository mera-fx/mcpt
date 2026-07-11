from __future__ import annotations

import math
import unittest
from types import SimpleNamespace

import numpy as np
import pandas as pd

from run_research_lab import run_standard_benchmarks
from trade_engine import (
    CostModel,
    backtest_signal_strategy,
    signal_to_target_position,
)


def sample_data(
    opens: list[float],
    closes: list[float] | None = None,
) -> pd.DataFrame:
    if closes is None:
        closes = opens

    index = pd.date_range(
        "2024-01-01",
        periods=len(opens),
        freq="h",
    )

    return pd.DataFrame(
        {
            "open": opens,
            "high": [
                max(open_price, close_price)
                for open_price, close_price
                in zip(opens, closes)
            ],
            "low": [
                min(open_price, close_price)
                for open_price, close_price
                in zip(opens, closes)
            ],
            "close": closes,
        },
        index=index,
    )


class SignalTimingTests(unittest.TestCase):
    def test_signal_is_executed_one_bar_later(self) -> None:
        data = sample_data(
            [100, 101, 102, 103, 104]
        )

        signal = pd.Series(
            [0, 1, 1, 0, 0],
            index=data.index,
            dtype=float,
        )

        target = signal_to_target_position(
            signal,
            execution_lag_bars=1,
        )

        self.assertEqual(
            target.tolist(),
            [0.0, 0.0, 1.0, 1.0, 0.0],
        )

        result = backtest_signal_strategy(
            data,
            target,
            cost_model=CostModel(),
        )

        trade = result.trades.iloc[0]

        self.assertEqual(
            trade["entry_time"],
            data.index[2],
        )

        self.assertEqual(
            trade["entry_price"],
            102,
        )

        self.assertEqual(
            trade["exit_time"],
            data.index[4],
        )

        self.assertEqual(
            trade["exit_price"],
            104,
        )

    def test_future_signal_changes_do_not_change_past_positions(
        self,
    ) -> None:
        index = pd.date_range(
            "2024-01-01",
            periods=6,
            freq="h",
        )

        original = pd.Series(
            [0, 1, 1, 0, 0, 0],
            index=index,
            dtype=float,
        )

        changed_future = original.copy()
        changed_future.iloc[-1] = -1

        original_target = signal_to_target_position(
            original,
            execution_lag_bars=1,
        )

        changed_target = signal_to_target_position(
            changed_future,
            execution_lag_bars=1,
        )

        pd.testing.assert_series_equal(
            original_target.iloc[:-1],
            changed_target.iloc[:-1],
        )


class CostAccountingTests(unittest.TestCase):
    def test_round_trip_cost_is_charged_on_entry_and_exit(
        self,
    ) -> None:
        data = sample_data(
            [100, 100, 100, 100]
        )

        target = pd.Series(
            [0, 1, 1, 0],
            index=data.index,
            dtype=float,
        )

        result = backtest_signal_strategy(
            data,
            target,
            cost_model=CostModel(
                commission_bps_per_side=5,
                slippage_bps_per_side=2,
            ),
            starting_capital=100_000,
        )

        trade = result.trades.iloc[0]

        self.assertEqual(
            trade["commission_bps_round_trip"],
            10,
        )

        self.assertEqual(
            trade["slippage_bps_round_trip"],
            4,
        )

        expected_return = (
            math.exp(-0.0014) - 1
        ) * 100

        self.assertAlmostEqual(
            trade["net_return_percent"],
            expected_return,
            places=10,
        )

        self.assertAlmostEqual(
            result.equity_curve[
                "transaction_sides"
            ].sum(),
            2.0,
            places=10,
        )

    def test_reversal_charges_two_transaction_sides(
        self,
    ) -> None:
        data = sample_data(
            [100, 100, 100]
        )

        target = pd.Series(
            [1, -1, 0],
            index=data.index,
            dtype=float,
        )

        result = backtest_signal_strategy(
            data,
            target,
            cost_model=CostModel(
                commission_bps_per_side=1,
            ),
        )

        self.assertEqual(
            len(result.trades),
            2,
        )

        self.assertAlmostEqual(
            result.equity_curve[
                "transaction_sides"
            ].sum(),
            4.0,
            places=10,
        )


class TradeLedgerTests(unittest.TestCase):
    def test_open_trade_is_closed_at_final_close(
        self,
    ) -> None:
        data = sample_data(
            [100, 100, 100],
            [100, 100, 110],
        )

        target = pd.Series(
            [0, 1, 1],
            index=data.index,
            dtype=float,
        )

        result = backtest_signal_strategy(
            data,
            target,
            cost_model=CostModel(),
        )

        trade = result.trades.iloc[0]

        self.assertEqual(
            trade["exit_time"],
            data.index[-1],
        )

        self.assertEqual(
            trade["exit_price"],
            110,
        )

        self.assertEqual(
            trade["exit_reason"],
            "end_of_data",
        )

        self.assertAlmostEqual(
            trade["net_return_percent"],
            10.0,
            places=10,
        )

    def test_trade_ledger_matches_final_equity(
        self,
    ) -> None:
        data = sample_data(
            [100, 105, 103, 110, 108],
            [101, 104, 104, 109, 112],
        )

        target = pd.Series(
            [0, 1, 1, -1, 0],
            index=data.index,
            dtype=float,
        )

        result = backtest_signal_strategy(
            data,
            target,
            cost_model=CostModel(
                commission_bps_per_side=2,
                slippage_bps_per_side=1,
            ),
            starting_capital=100_000,
        )

        ledger_ending_equity = float(
            result.trades["equity_after"].iloc[-1]
        )

        curve_ending_equity = float(
            result.equity_curve["equity"].iloc[-1]
        )

        self.assertAlmostEqual(
            ledger_ending_equity,
            curve_ending_equity,
            places=8,
        )


class BenchmarkTests(unittest.TestCase):
    def test_standard_benchmarks_use_same_period(
        self,
    ) -> None:
        data = sample_data(
            [100, 105, 110],
            [101, 106, 120],
        )

        config = SimpleNamespace(
            commission_bps_per_side=0.0,
            slippage_bps_per_side=0.0,
            starting_capital=100_000.0,
        )

        benchmarks = run_standard_benchmarks(
            data,
            config,
        )

        self.assertEqual(
            set(benchmarks),
            {"Buy and Hold", "Cash"},
        )

        buy_hold = benchmarks[
            "Buy and Hold"
        ]

        cash = benchmarks["Cash"]

        self.assertEqual(
            len(buy_hold.trades),
            1,
        )

        self.assertEqual(
            buy_hold.trades.iloc[0]["entry_time"],
            data.index[0],
        )

        self.assertEqual(
            buy_hold.trades.iloc[0]["exit_time"],
            data.index[-1],
        )

        self.assertAlmostEqual(
            buy_hold.summary[
                "total_return_percent"
            ],
            20.0,
            places=10,
        )

        self.assertEqual(
            cash.summary["total_trades"],
            0,
        )

        self.assertAlmostEqual(
            cash.summary["total_return_percent"],
            0.0,
            places=10,
        )

        self.assertTrue(
            np.allclose(
                cash.equity_curve["equity"],
                100_000.0,
            )
        )


if __name__ == "__main__":
    unittest.main()
