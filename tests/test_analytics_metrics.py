from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import unittest

import numpy as np
import pandas as pd

from analytics_evidence_registry import (
    AnalyticsSeriesSpec,
    BenchmarkSchema,
    EquitySchema,
    MetricFamily,
    NOT_AVAILABLE_MESSAGE,
    TradeSchema,
)
from analytics_metrics import (
    ANALYTICS_SCHEMA_VERSION,
    compute_series_analytics,
    summary_row,
)


def series_spec() -> AnalyticsSeriesSpec:
    return AnalyticsSeriesSpec(
        series_id="EXP-999:test:NQ",
        experiment_id="EXP-999",
        display_name="Synthetic test series",
        market="NQ",
        variant_id="test",
        candidate_id="candidate",
        family_id="family",
        trades_path=Path("results/EXP-999/trades.csv"),
        equity_path=Path("results/EXP-999/equity.csv"),
        trade_schema=TradeSchema.FUTURES_CANDIDATE,
        equity_schema=EquitySchema.CANDIDATE_EQUITY,
        benchmark_schema=BenchmarkSchema.NORMALIZED_COMPARISON,
        benchmark_paths=(
            Path("results/EXP-999/benchmark.csv"),
        ),
        benchmark_column="benchmark",
    )


def canonical_frames() -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:
    dates = pd.date_range(
        "2024-01-02",
        periods=4,
        freq="D",
        tz="UTC",
    )
    entry = dates + pd.Timedelta(hours=15)
    exit_ = entry + pd.Timedelta(minutes=30)
    pnl = pd.Series([100.0, -50.0, 200.0, -25.0])
    trades = pd.DataFrame(
        {
            "series_id": "EXP-999:test:NQ",
            "session_date": dates.tz_localize(None),
            "direction": ["long", "long", "short", "short"],
            "entry_time": entry,
            "exit_time": exit_,
            "holding_minutes": 30.0,
            "gross_pnl_usd": pnl + 5.0,
            "transaction_cost_usd": 5.0,
            "net_pnl_usd": pnl,
            "contracts": [1.0, 2.0, 3.0, 4.0],
            "exit_reason": ["target", "stop", "target", "stop"],
            "mae_usd": np.nan,
            "mfe_usd": np.nan,
            "captured_fraction_of_mfe": np.nan,
        }
    )
    equity_values = 100_000.0 + pnl.cumsum()
    equity = pd.DataFrame(
        {
            "series_id": "EXP-999:test:NQ",
            "period_end": dates,
            "equity_usd": equity_values,
        }
    )
    benchmark = pd.DataFrame(
        {
            "series_id": "EXP-999:test:NQ",
            "period_end": dates,
            "benchmark_equity_usd": [
                100_000.0,
                100_020.0,
                100_010.0,
                100_060.0,
            ],
        }
    )
    return trades, equity, benchmark


class AnalyticsMetricTests(unittest.TestCase):
    def test_all_metric_families_are_explicit_and_json_safe(
        self,
    ) -> None:
        trades, equity, benchmark = canonical_frames()
        result = compute_series_analytics(
            trades,
            equity,
            series_spec(),
            benchmark=benchmark,
            evidence_records=(
                {
                    "path": "results/EXP-999/trades.csv",
                    "sha256": "a" * 64,
                    "size_bytes": 10,
                    "roles": ["trade_ledger"],
                },
            ),
            robustness_records=(
                {
                    "path": "results/EXP-999/decision.json",
                    "sha256": "b" * 64,
                    "size_bytes": 20,
                    "roles": ["existing_robustness"],
                },
            ),
        )

        self.assertEqual(
            result["schema_version"],
            ANALYTICS_SCHEMA_VERSION,
        )
        self.assertEqual(
            set(result["metric_families"]),
            {family.value for family in MetricFamily},
        )
        performance = result["metric_families"][
            MetricFamily.PERFORMANCE_SUMMARY.value
        ]["metrics"]
        self.assertEqual(performance["all"]["completed_trades"], 4)
        self.assertEqual(performance["long"]["completed_trades"], 2)
        self.assertEqual(performance["short"]["completed_trades"], 2)
        self.assertEqual(performance["all"]["net_profit_usd"], 225.0)
        self.assertEqual(
            performance["all"]["maximum_contracts_held"],
            4.0,
        )
        self.assertEqual(
            performance["long"]["maximum_contracts_held"],
            2.0,
        )
        self.assertEqual(
            performance["short"]["maximum_contracts_held"],
            4.0,
        )
        self.assertAlmostEqual(
            performance["all"][
                "maximum_strategy_drawdown_usd"
            ],
            -50.0,
        )
        self.assertAlmostEqual(
            performance["all"][
                "return_on_maximum_strategy_drawdown"
            ],
            4.5,
        )
        self.assertAlmostEqual(
            performance["long"][
                "return_on_maximum_strategy_drawdown"
            ],
            1.0,
        )
        self.assertAlmostEqual(
            performance["short"][
                "return_on_maximum_strategy_drawdown"
            ],
            7.0,
        )
        self.assertAlmostEqual(
            performance["all"]["buy_and_hold_return_usd"],
            60.0,
        )
        self.assertAlmostEqual(
            performance["all"]["buy_and_hold_return_percent"],
            0.06,
        )
        self.assertIsNone(
            performance["long"]["buy_and_hold_return_usd"]
        )
        annual_rate = (
            performance["all"]["annual_rate_of_return_percent"]
            / 100.0
        )
        self.assertAlmostEqual(
            performance["all"]["monthly_rate_of_return_percent"],
            (
                (1.0 + annual_rate) ** (1.0 / 12.0)
                - 1.0
            )
            * 100.0,
        )
        self.assertEqual(
            result["integrity"]["reconciliation_difference_usd"],
            0.0,
        )
        self.assertTrue(
            result["integrity"]["trade_equity_reconciled"]
        )
        self.assertEqual(
            result["metric_families"][
                MetricFamily.MAE_AND_MFE.value
            ]["message"],
            NOT_AVAILABLE_MESSAGE,
        )
        self.assertEqual(
            result["metric_families"][
                MetricFamily.BENCHMARK_AND_VALUE_ADDED.value
            ]["status"],
            "AVAILABLE",
        )
        equity_curve = result["metric_families"][
            MetricFamily.EQUITY_AND_DRAWDOWN.value
        ]["tables"]["equity_curve"]
        self.assertEqual(len(equity_curve), 4)
        self.assertEqual(
            equity_curve[-1]["strategy_equity_usd"],
            100_225.0,
        )
        json.dumps(result, allow_nan=False)

    def test_mae_mfe_is_calculated_only_for_enriched_evidence(
        self,
    ) -> None:
        trades, equity, benchmark = canonical_frames()
        trades["mae_usd"] = [-20.0, -60.0, -10.0, -30.0]
        trades["mfe_usd"] = [120.0, 20.0, 230.0, 10.0]
        trades["captured_fraction_of_mfe"] = [
            0.875,
            -2.25,
            0.891304,
            -2.0,
        ]
        enriched = replace(
            series_spec(),
            trade_schema=TradeSchema.FUTURES_ENRICHED,
            supports_mae_mfe=True,
        )
        result = compute_series_analytics(
            trades,
            equity,
            enriched,
            benchmark=benchmark,
        )
        family = result["metric_families"][
            MetricFamily.MAE_AND_MFE.value
        ]
        self.assertEqual(family["status"], "AVAILABLE")
        self.assertEqual(family["metrics"]["trades_with_mae_mfe"], 4)
        self.assertAlmostEqual(
            family["metrics"]["average_absolute_mae_usd"],
            30.0,
        )
        self.assertEqual(
            len(family["tables"]["by_outcome"]),
            4,
        )

    def test_benchmark_unavailability_is_visible(self) -> None:
        trades, equity, _ = canonical_frames()
        without_benchmark = replace(
            series_spec(),
            benchmark_schema=BenchmarkSchema.NONE,
            benchmark_paths=(),
            benchmark_column=None,
        )
        result = compute_series_analytics(
            trades,
            equity,
            without_benchmark,
        )
        family = result["metric_families"][
            MetricFamily.BENCHMARK_AND_VALUE_ADDED.value
        ]
        self.assertEqual(family["status"], "NOT_AVAILABLE")
        self.assertEqual(family["message"], NOT_AVAILABLE_MESSAGE)
        performance = result["metric_families"][
            MetricFamily.PERFORMANCE_SUMMARY.value
        ]["metrics"]["all"]
        self.assertIsNone(performance["buy_and_hold_return_usd"])
        self.assertIsNone(
            performance["buy_and_hold_return_percent"]
        )
        self.assertIsNone(
            summary_row(result)["excess_total_return_percent"]
        )

    def test_maximum_contracts_counts_overlapping_positions(
        self,
    ) -> None:
        trades, equity, benchmark = canonical_frames()
        first_entry = trades.loc[0, "entry_time"]
        trades.loc[1, "entry_time"] = (
            first_entry + pd.Timedelta(minutes=10)
        )
        trades.loc[1, "exit_time"] = (
            first_entry + pd.Timedelta(minutes=45)
        )
        result = compute_series_analytics(
            trades,
            equity,
            series_spec(),
            benchmark=benchmark,
        )
        performance = result["metric_families"][
            MetricFamily.PERFORMANCE_SUMMARY.value
        ]["metrics"]
        self.assertEqual(
            performance["all"]["maximum_contracts_held"],
            4.0,
        )
        self.assertEqual(
            performance["long"]["maximum_contracts_held"],
            3.0,
        )

    def test_returns_use_period_equity_not_raw_trade_pnl(self) -> None:
        trades, equity, benchmark = canonical_frames()
        result = compute_series_analytics(
            trades,
            equity,
            series_spec(),
            benchmark=benchmark,
        )
        ratios = result["metric_families"][
            MetricFamily.PERFORMANCE_RATIOS.value
        ]["metrics"]
        self.assertAlmostEqual(
            ratios["normalized_total_return_percent"],
            0.225,
        )
        self.assertLess(abs(ratios["sharpe_ratio_zero_risk_free"]), 10)
        exposure = result["metric_families"][
            MetricFamily.TIME_AND_EXPOSURE.value
        ]["metrics"]
        self.assertAlmostEqual(
            exposure["non_overlapping_market_minutes"],
            120.0,
        )


if __name__ == "__main__":
    unittest.main()
