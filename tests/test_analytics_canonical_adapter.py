from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import tempfile
import unittest

import numpy as np
import pandas as pd

from analytics_canonical_adapter import (
    AnalyticsEvidenceUnavailable,
    canonicalize_equity,
    canonicalize_trades,
    load_canonical_benchmark,
)
from analytics_evidence_registry import (
    AnalyticsSeriesSpec,
    BenchmarkSchema,
    EquitySchema,
    TradeSchema,
)


def spec(
    *,
    trade_schema: TradeSchema,
    equity_schema: EquitySchema = EquitySchema.SESSION_EQUITY,
    benchmark_schema: BenchmarkSchema = BenchmarkSchema.NONE,
    benchmark_paths: tuple[Path, ...] = (),
    benchmark_column: str | None = None,
    equity_value_column: str | None = None,
    supports_mae_mfe: bool = False,
) -> AnalyticsSeriesSpec:
    return AnalyticsSeriesSpec(
        series_id="EXP-999:test:NQ",
        experiment_id="EXP-999",
        display_name="Test",
        market="NQ",
        variant_id="test",
        candidate_id="test_candidate",
        family_id="test_family",
        trades_path=Path("trades.csv"),
        equity_path=Path("equity.csv"),
        trade_schema=trade_schema,
        equity_schema=equity_schema,
        benchmark_schema=benchmark_schema,
        benchmark_paths=benchmark_paths,
        benchmark_column=benchmark_column,
        equity_value_column=equity_value_column,
        supports_mae_mfe=supports_mae_mfe,
    )


class AnalyticsCanonicalAdapterTests(unittest.TestCase):
    def test_btc_trade_schema_maps_cash_and_costs(self) -> None:
        frame = pd.DataFrame(
            {
                "trade_id": [1],
                "side": ["Short"],
                "entry_time": ["2022-01-05 01:00:00"],
                "exit_time": ["2022-01-05 03:00:00"],
                "entry_price": [100.0],
                "exit_price": [95.0],
                "hours_held": [2.0],
                "gross_return_percent": [5.0],
                "net_return_percent": [4.8],
                "equity_before": [100_000.0],
                "pnl_cash": [4_800.0],
                "exit_reason": ["signal_change"],
            }
        )
        result = canonicalize_trades(
            frame,
            spec(trade_schema=TradeSchema.BTC_HOURLY),
        )
        self.assertEqual(result.loc[0, "direction"], "short")
        self.assertEqual(result.loc[0, "holding_minutes"], 120.0)
        self.assertEqual(result.loc[0, "gross_pnl_usd"], 5_000.0)
        self.assertEqual(
            result.loc[0, "transaction_cost_usd"],
            200.0,
        )
        self.assertEqual(result.loc[0, "net_pnl_usd"], 4_800.0)

    def test_candidate_slots_become_real_timestamps(self) -> None:
        frame = pd.DataFrame(
            {
                "session_date": ["2024-07-01"],
                "direction": ["long"],
                "entry_minute_slot": [30],
                "exit_minute_slot": [385],
                "holding_minutes": [355],
                "entry_price": [20_000.0],
                "exit_price": [20_100.0],
                "gross_pnl_usd": [2_000.0],
                "transaction_cost_usd": [15.0],
                "net_pnl_usd": [1_985.0],
                "exit_reason": ["forced_flat_1555"],
            }
        )
        result = canonicalize_trades(
            frame,
            spec(
                trade_schema=TradeSchema.FUTURES_CANDIDATE,
            ),
        )
        self.assertEqual(
            result.loc[0, "entry_time"].tz_convert(
                "America/New_York"
            ).strftime("%H:%M"),
            "10:00",
        )
        self.assertEqual(
            result.loc[0, "exit_time"].tz_convert(
                "America/New_York"
            ).strftime("%H:%M"),
            "15:55",
        )

    def test_legacy_1970_timestamp_is_repaired(self) -> None:
        real = pd.Timestamp("2019-05-08 14:00:00", tz="UTC")
        broken = pd.Timestamp(real.value // 1000, tz="UTC")
        frame = pd.DataFrame(
            {
                "session_date": ["2019-05-08"],
                "direction": ["long"],
                "entry_time": [broken.isoformat()],
                "exit_time": [broken.isoformat()],
                "minutes_held": [10],
                "entry_price": [1.0],
                "exit_price": [1.0],
                "gross_pnl_usd": [0.0],
                "transaction_cost_usd": [15.0],
                "net_pnl_usd": [-15.0],
                "exit_reason": ["time"],
            }
        )
        result = canonicalize_trades(
            frame,
            spec(trade_schema=TradeSchema.FUTURES_ORB),
        )
        self.assertEqual(
            result.loc[0, "entry_time"],
            real,
        )

    def test_mae_mfe_remain_missing_when_not_supported(self) -> None:
        frame = pd.DataFrame(
            {
                "session_date": ["2024-01-02"],
                "direction": ["long"],
                "entry_minute_slot": [5],
                "exit_minute_slot": [20],
                "holding_minutes": [15],
                "entry_price": [1.0],
                "exit_price": [2.0],
                "gross_pnl_usd": [20.0],
                "transaction_cost_usd": [5.0],
                "net_pnl_usd": [15.0],
                "exit_reason": ["target"],
            }
        )
        result = canonicalize_trades(
            frame,
            spec(
                trade_schema=TradeSchema.FUTURES_CANDIDATE,
            ),
        )
        self.assertTrue(result["mae_usd"].isna().all())
        self.assertTrue(result["mfe_usd"].isna().all())

    def test_enriched_trade_preserves_mae_mfe(self) -> None:
        frame = pd.DataFrame(
            {
                "session_date": ["2024-01-02"],
                "direction": ["long"],
                "entry_time": ["09:35"],
                "exit_time": ["10:00"],
                "holding_minutes": [25],
                "entry_price": [20_000.0],
                "exit_price": [20_020.0],
                "gross_pnl_usd": [400.0],
                "transaction_cost_usd": [15.0],
                "net_pnl_usd": [385.0],
                "exit_reason": ["time"],
                "pre_exit_mae_usd": [-120.0],
                "pre_exit_mfe_usd": [500.0],
                "captured_fraction_of_mfe": [0.8],
            }
        )
        result = canonicalize_trades(
            frame,
            spec(
                trade_schema=TradeSchema.FUTURES_ENRICHED,
                supports_mae_mfe=True,
            ),
        )
        self.assertEqual(result.loc[0, "mae_usd"], -120.0)
        self.assertEqual(result.loc[0, "mfe_usd"], 500.0)
        self.assertEqual(
            result.loc[0, "captured_fraction_of_mfe"],
            0.8,
        )

    def test_equity_is_recomputed_from_cumulative_pnl(self) -> None:
        frame = pd.DataFrame(
            {
                "session_date": ["2024-01-02", "2024-01-03"],
                "cumulative_net_pnl_usd": [100.0, 50.0],
                "had_trade": [True, True],
            }
        )
        result = canonicalize_equity(
            frame,
            spec(trade_schema=TradeSchema.FUTURES_ORB),
        )
        self.assertEqual(
            result["equity_usd"].tolist(),
            [100_100.0, 100_050.0],
        )
        self.assertEqual(
            result["net_pnl_usd"].tolist(),
            [100.0, -50.0],
        )
        self.assertEqual(result.loc[1, "drawdown_usd"], -50.0)

    def test_session_pnl_matrix_uses_only_selected_column(self) -> None:
        frame = pd.DataFrame(
            {
                "session_date": ["2024-01-02", "2024-01-03"],
                "candidate_a": [10.0, -5.0],
                "candidate_b": [1_000.0, 1_000.0],
            }
        )
        result = canonicalize_equity(
            frame,
            spec(
                trade_schema=TradeSchema.FUTURES_ENRICHED,
                equity_schema=EquitySchema.SESSION_PNL_MATRIX,
                equity_value_column="candidate_a",
                supports_mae_mfe=True,
            ),
        )
        self.assertEqual(
            result["equity_usd"].tolist(),
            [100_010.0, 100_005.0],
        )

    def test_normalized_comparison_benchmark(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            path = project / "benchmark.csv"
            pd.DataFrame(
                {
                    "session_date": [
                        "2024-01-02",
                        "2024-01-03",
                    ],
                    "market": [200.0, 220.0],
                }
            ).to_csv(path, index=False)
            current = spec(
                trade_schema=TradeSchema.FUTURES_CANDIDATE,
                benchmark_schema=(
                    BenchmarkSchema.NORMALIZED_COMPARISON
                ),
                benchmark_paths=(Path("benchmark.csv"),),
                benchmark_column="market",
            )
            result = load_canonical_benchmark(project, current)
            self.assertAlmostEqual(
                result.loc[0, "benchmark_equity_usd"],
                100_000.0,
            )
            self.assertAlmostEqual(
                result.loc[1, "benchmark_equity_usd"],
                110_000.0,
            )
            self.assertAlmostEqual(
                result.loc[1, "benchmark_return"],
                0.1,
            )

    def test_missing_benchmark_raises_explicit_error(self) -> None:
        current = spec(
            trade_schema=TradeSchema.QQQ_QUICK_SCREEN,
        )
        with self.assertRaisesRegex(
            AnalyticsEvidenceUnavailable,
            "not available",
        ):
            load_canonical_benchmark(Path("."), current)

    def test_unsupported_mae_fields_cannot_sneak_in(self) -> None:
        frame = pd.DataFrame(
            {
                "session_date": ["2024-01-02"],
                "direction": ["long"],
                "entry_minute_slot": [5],
                "exit_minute_slot": [20],
                "holding_minutes": [15],
                "entry_price": [1.0],
                "exit_price": [2.0],
                "gross_pnl_usd": [20.0],
                "transaction_cost_usd": [5.0],
                "net_pnl_usd": [15.0],
                "exit_reason": ["target"],
                "pre_exit_mae_usd": [-10.0],
                "pre_exit_mfe_usd": [30.0],
            }
        )
        with self.assertRaisesRegex(
            ValueError,
            "does not support",
        ):
            canonicalize_trades(
                frame,
                spec(
                    trade_schema=TradeSchema.FUTURES_CANDIDATE,
                ),
            )

    def test_clipped_benchmark_is_rebased_to_reference_capital(
        self,
    ) -> None:
        current = replace(
            spec(
                trade_schema=TradeSchema.FUTURES_CANDIDATE,
                benchmark_schema=(
                    BenchmarkSchema.NORMALIZED_COMPARISON
                ),
                benchmark_paths=(Path("benchmark.csv"),),
                benchmark_column="benchmark",
            ),
            analysis_start="2024-01-02",
            analysis_end="2024-01-03",
        )
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            pd.DataFrame(
                {
                    "session_date": [
                        "2024-01-01",
                        "2024-01-02",
                        "2024-01-03",
                    ],
                    "benchmark": [100.0, 110.0, 121.0],
                }
            ).to_csv(project / "benchmark.csv", index=False)
            result = load_canonical_benchmark(project, current)

        self.assertEqual(len(result), 2)
        self.assertAlmostEqual(
            result.loc[0, "benchmark_equity_usd"],
            current.reference_capital_usd,
        )
        self.assertAlmostEqual(
            result.loc[1, "benchmark_equity_usd"],
            current.reference_capital_usd * 1.1,
        )


if __name__ == "__main__":
    unittest.main()
