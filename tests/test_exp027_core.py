from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from exp026_core import (
    ALL_CANDIDATE_IDS,
    BASE_ROUND_TRIP_COST_USD,
    CONTROL_CANDIDATE_IDS,
    DEVELOPMENT_CANDIDATE_IDS,
    METRIC_SEGMENTS,
    candidate_metrics,
)
from exp027_core import (
    CANONICAL_EQUITY_COLUMNS,
    CANONICAL_TRADE_COLUMNS,
    CONTROL_COHORT_LABEL,
    PRIMARY_COHORT_LABEL,
    SECONDARY_COHORT_LABEL,
    candidate_registry_exp027,
    candidate_series_metrics,
    canonical_trade_ledger,
    cohort_for,
    comparison_timeseries,
    dense_session_equity,
    exp027_candidate_ids,
    exp027_control_ids,
    exp027_reported_ids,
    historical_context,
    primary_cohort_ids,
    representation_sensitivity,
    series_id_for,
    trade_distribution,
    validate_exp027_population,
    validate_result_frames,
)


def sample_decisions() -> pd.DataFrame:
    rows = []
    for candidate_id in exp027_reported_ids():
        for session_date in (
            "2026-01-02",
            "2026-01-05",
        ):
            rows.append(
                {
                    "candidate_id": candidate_id,
                    "session_date": session_date,
                }
            )
    return pd.DataFrame(rows)


def sample_trade() -> pd.DataFrame:
    candidate_id = primary_cohort_ids()[0]
    return pd.DataFrame(
        [
            {
                "candidate_id": candidate_id,
                "family_id": "gap_fade",
                "candidate_role": "DEVELOPMENT",
                "session_date": "2026-01-02",
                "direction": "long",
                "entry_timestamp_utc": (
                    "2026-01-02T14:35:00+00:00"
                ),
                "exit_timestamp_utc": (
                    "2026-01-02T14:40:00+00:00"
                ),
                "entry_session_minute": 935,
                "exit_session_minute": 940,
                "entry_price": 20000.0,
                "stop_price": 19999.0,
                "target_price": 20001.0,
                "exit_price": 20001.0,
                "risk_points": 1.0,
                "gross_pnl_usd": 20.0,
                "transaction_cost_usd": (
                    BASE_ROUND_TRIP_COST_USD
                ),
                "net_pnl_usd": 5.0,
                "exit_reason": "profit_target",
                "context_value": 0.8,
                "threshold": 0.75,
                "exit_mode": "1r_or_time",
                "setup_kind": "gap_fade",
                "representation_id": (
                    "BACKWARD_ADJUSTED"
                ),
                "forced_flat_session_minute": 1315,
            }
        ]
    )


class Exp027CoreTests(unittest.TestCase):
    def test_01_population_is_exact(self) -> None:
        validate_exp027_population()
        self.assertEqual(
            exp027_candidate_ids(),
            tuple(DEVELOPMENT_CANDIDATE_IDS),
        )
        self.assertEqual(
            exp027_control_ids(),
            tuple(CONTROL_CANDIDATE_IDS),
        )
        self.assertEqual(
            exp027_reported_ids(),
            tuple(ALL_CANDIDATE_IDS),
        )

    def test_02_cohort_labels_are_locked(self) -> None:
        self.assertEqual(
            cohort_for(primary_cohort_ids()[0]),
            PRIMARY_COHORT_LABEL,
        )
        secondary = next(
            item
            for item in exp027_candidate_ids()
            if item not in primary_cohort_ids()
        )
        self.assertEqual(
            cohort_for(secondary),
            SECONDARY_COHORT_LABEL,
        )
        self.assertEqual(
            cohort_for(exp027_control_ids()[0]),
            CONTROL_COHORT_LABEL,
        )

    def test_03_registry_has_24_nonselectable_rows(
        self,
    ) -> None:
        registry = candidate_registry_exp027()
        self.assertEqual(len(registry), 24)
        self.assertFalse(
            registry[
                "selection_eligible_in_exp027"
            ].any()
        )
        self.assertEqual(
            int(
                registry[
                    "primary_confirmation_cohort"
                ].sum()
            ),
            3,
        )

    def test_04_empty_trade_ledger_has_canonical_header(
        self,
    ) -> None:
        ledger = canonical_trade_ledger(
            pd.DataFrame(),
            candidate_id=exp027_candidate_ids()[0],
        )
        self.assertEqual(
            tuple(ledger.columns),
            CANONICAL_TRADE_COLUMNS,
        )
        self.assertTrue(ledger.empty)

    def test_05_trade_ledger_is_canonical(self) -> None:
        candidate_id = primary_cohort_ids()[0]
        ledger = canonical_trade_ledger(
            sample_trade(),
            candidate_id=candidate_id,
        )
        self.assertEqual(
            tuple(ledger.columns),
            CANONICAL_TRADE_COLUMNS,
        )
        self.assertEqual(len(ledger), 1)
        self.assertEqual(
            ledger.iloc[0]["series_id"],
            series_id_for(candidate_id),
        )
        self.assertEqual(
            float(ledger.iloc[0]["net_pnl_usd"]),
            5.0,
        )
        self.assertEqual(
            float(ledger.iloc[0]["initial_risk_usd"]),
            20.0,
        )

    def test_06_dense_equity_includes_zero_trade_session(
        self,
    ) -> None:
        candidate_id = primary_cohort_ids()[0]
        equity = dense_session_equity(
            sample_decisions(),
            sample_trade(),
            candidate_id=candidate_id,
        )
        self.assertEqual(
            tuple(equity.columns),
            CANONICAL_EQUITY_COLUMNS,
        )
        self.assertEqual(len(equity), 2)
        self.assertEqual(
            tuple(equity["net_pnl_usd"]),
            (5.0, 0.0),
        )
        self.assertEqual(
            float(equity.iloc[-1]["equity_usd"]),
            100005.0,
        )

    def test_07_comparison_timeseries_has_context(
        self,
    ) -> None:
        candidate_id = primary_cohort_ids()[0]
        equity = dense_session_equity(
            sample_decisions(),
            sample_trade(),
            candidate_id=candidate_id,
        )
        result = comparison_timeseries(
            equity,
            candidate_id=candidate_id,
        )
        self.assertEqual(
            set(result["candidate_id"]),
            {candidate_id},
        )
        self.assertEqual(
            set(result["exp027_cohort"]),
            {PRIMARY_COHORT_LABEL},
        )

    def test_08_distribution_keeps_zero_trade_rows(
        self,
    ) -> None:
        result = trade_distribution(sample_trade())
        self.assertEqual(len(result), 24)
        zero_candidate = exp027_control_ids()[0]
        row = result.loc[
            result["candidate_id"] == zero_candidate
        ].iloc[0]
        self.assertEqual(
            int(row["completed_trades"]),
            0,
        )

    def test_09_representation_sensitivity_is_segmented(
        self,
    ) -> None:
        trades = sample_trade()
        primary = candidate_metrics(
            trades,
            candidate_ids=exp027_reported_ids(),
            period_start="2026-01-01",
            period_end="2026-07-23",
        )
        secondary = primary.copy()
        result = representation_sensitivity(
            primary,
            secondary,
        )
        self.assertEqual(len(result), 72)
        self.assertTrue(
            np.allclose(
                result[
                    "completed_trades_difference"
                ],
                0.0,
            )
        )

    def test_10_series_metrics_have_three_segments(
        self,
    ) -> None:
        candidate_id = primary_cohort_ids()[0]
        metrics = candidate_metrics(
            sample_trade(),
            candidate_ids=exp027_reported_ids(),
            period_start="2026-01-01",
            period_end="2026-07-23",
        )
        current = candidate_series_metrics(
            metrics,
            candidate_id=candidate_id,
        )
        self.assertEqual(
            tuple(current["segment"]),
            tuple(METRIC_SEGMENTS),
        )

    def test_11_historical_context_preserves_all_rows(
        self,
    ) -> None:
        phase = pd.DataFrame(
            [
                {
                    "candidate_id": candidate_id,
                    "segment": "ALL_TRADES",
                    "completed_trades": 1,
                    "net_profit_usd": 5.0,
                    "trade_profit_factor": 1.2,
                    "maximum_drawdown_usd": -2.0,
                    "win_rate": 0.5,
                }
                for candidate_id in exp027_reported_ids()
            ]
        )
        result = historical_context(
            phase,
            phase,
            phase,
        )
        self.assertEqual(len(result), 24)
        self.assertTrue(
            result[
                "historical_context_available"
            ].all()
        )

    def test_12_result_validation_requires_72_metrics(
        self,
    ) -> None:
        metrics = candidate_metrics(
            sample_trade(),
            candidate_ids=exp027_reported_ids(),
            period_start="2026-01-01",
            period_end="2026-07-23",
        )
        validate_result_frames(
            decisions=sample_decisions(),
            trades=sample_trade(),
            metrics=metrics,
        )


if __name__ == "__main__":
    unittest.main()
