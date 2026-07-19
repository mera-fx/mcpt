from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import numpy as np
import pandas as pd

from strategy_measurement_report import (
    _repair_timestamp_series,
    _table,
    comparison_timeseries,
    measurement_specs,
    normalized_benchmark,
    performance_table,
)


class StrategyMeasurementReportTests(unittest.TestCase):
    def sample_trades(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "session_date": [
                    "2024-01-02",
                    "2024-01-03",
                    "2024-01-04",
                    "2024-01-05",
                ],
                "direction": ["long", "long", "short", "short"],
                "net_pnl_usd": [100.0, -50.0, 80.0, -20.0],
                "transaction_cost_usd": [10.0, 10.0, 10.0, 10.0],
                "minutes_held": [30, 60, 45, 15],
            }
        )

    def test_exp007_uses_fixed_replication_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            specs = {
                spec.experiment_id: spec
                for spec in measurement_specs(Path(temp))
            }

        exp007 = specs["EXP-007"]
        self.assertEqual(
            exp007.result_directory.name,
            "fixed_replication",
        )
        self.assertEqual(
            exp007.decision_file.parent.name,
            "fixed_replication",
        )
        self.assertEqual(
            exp007.nq_trades_file.parent.name,
            "fixed_replication",
        )

    def test_green_is_reserved_for_status_text(self) -> None:
        numeric_markup = _table(
            pd.DataFrame(
                [
                    {"Metric": "Net profit", "All trades": "$1,000.00"},
                    {"Metric": "Maximum drawdown", "All trades": "−$250.00"},
                    {"Metric": "Profit Factor", "All trades": "1.250"},
                    {"Metric": "MCPT p-value", "All trades": "0.1400"},
                ]
            )
        )
        status_markup = _table(
            pd.DataFrame(
                [
                    {"Gate": "Example", "Result": "Pass"},
                    {"Gate": "Example two", "Result": "Fail"},
                ]
            )
        )
        self.assertNotIn('class="value-positive"', numeric_markup)
        self.assertIn('class="value-negative"', numeric_markup)
        self.assertIn('class="value-positive"', status_markup)
        self.assertIn('class="value-negative"', status_markup)

    def test_performance_table_has_all_long_short_columns(self) -> None:
        table = performance_table(self.sample_trades())
        self.assertEqual(
            list(table.columns),
            ["Metric", "All trades", "Long trades", "Short trades"],
        )
        trades_row = table.loc[table["Metric"].eq("Completed trades")].iloc[0]
        self.assertEqual(trades_row["All trades"], "4")
        self.assertEqual(trades_row["Long trades"], "2")
        self.assertEqual(trades_row["Short trades"], "2")

    def test_normalized_benchmark_uses_same_period(self) -> None:
        rows = []
        for date, close in (("2024-01-02", 100.0), ("2024-01-03", 110.0)):
            for minute_slot in range(2):
                rows.append(
                    {
                        "session_date": date,
                        "minute_slot": minute_slot,
                        "close": close + minute_slot,
                    }
                )
        benchmark = normalized_benchmark(
            pd.DataFrame(rows),
            start_date="2024-01-02",
            end_date="2024-01-03",
            reference_capital=100_000.0,
        )
        self.assertEqual(len(benchmark), 2)
        self.assertAlmostEqual(benchmark["benchmark_equity"].iloc[0], 100_000.0)
        self.assertGreater(benchmark["benchmark_equity"].iloc[-1], 100_000.0)

    def test_comparison_timeseries_contains_strategy_benchmark_cash(self) -> None:
        equity = pd.DataFrame(
            {
                "session_date": ["2024-01-02", "2024-01-03"],
                "session_net_pnl_usd": [100.0, -20.0],
                "cumulative_net_pnl_usd": [100.0, 80.0],
            }
        )
        benchmark = pd.DataFrame(
            {
                "session_date": pd.to_datetime(["2024-01-02", "2024-01-03"]),
                "benchmark_close": [100.0, 101.0],
                "benchmark_equity": [100_000.0, 101_000.0],
                "benchmark_drawdown_percent": [0.0, 0.0],
            }
        )
        result = comparison_timeseries(equity, benchmark, reference_capital=100_000.0)
        self.assertIn("strategy_equity", result)
        self.assertIn("benchmark_equity", result)
        self.assertIn("cash_equity", result)
        self.assertAlmostEqual(result["strategy_equity"].iloc[-1], 100_080.0)

    def test_legacy_1970_trade_timestamp_is_repaired(self) -> None:
        source = pd.Series(["1970-01-19T00:35:27.600000+00:00"])
        repaired = _repair_timestamp_series(source)
        self.assertEqual(int(repaired.dt.year.iloc[0]), 2019)
        self.assertEqual(repaired.dt.strftime("%H:%M").iloc[0], "11:00")


if __name__ == "__main__":
    unittest.main()
