from __future__ import annotations

from copy import deepcopy
import unittest

import numpy as np
import pandas as pd

from exp026_core import (
    ALL_CANDIDATE_IDS,
    CANDIDATE_SPECS,
    CONTROL_CANDIDATE_IDS,
    DECISION_COLUMNS,
    DEVELOPMENT_CANDIDATE_IDS,
    DIRECTION_ALL,
    DIRECTION_LONG,
    DIRECTION_SHORT,
    METRIC_COLUMNS,
    SOURCE_COLUMNS,
    TRADE_COLUMNS,
    aggregate_observed_five_minute,
    annual_results,
    candidate_metrics,
    candidate_registry_frame,
    canonical_dataframe_sha256,
    cost_sensitivity,
    mirrored_trade_outcomes,
    normalise_source_frame,
    parameter_stability,
    replay_candidates,
    select_phase_a_survivors,
    select_phase_b_finalists,
    validate_candidate_specs,
)
from exp026_statistics import (
    anchored_walk_forward,
    bootstrap_session_blocks,
    build_session_outcome_matrices,
    selection_aware_market_mcpt,
)


TEST_DATES = (
    "2016-01-04",
    "2016-01-05",
    "2016-01-06",
)


def _timestamp(
    session_date: str,
    session_minute: int,
) -> pd.Timestamp:
    if session_minute < 360:
        local_date = (
            pd.Timestamp(session_date)
            - pd.Timedelta(days=1)
        )
        clock_minute = 18 * 60 + session_minute
    else:
        local_date = pd.Timestamp(session_date)
        clock_minute = session_minute - 360
    local = pd.Timestamp(
        (
            f"{local_date.date().isoformat()} "
            f"{clock_minute // 60:02d}:"
            f"{clock_minute % 60:02d}:00"
        ),
        tz="America/New_York",
    )
    return local.tz_convert("UTC")


def make_source_frame() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for session_date in TEST_DATES:
        for session_minute in range(840, 1320):
            opening = 100.0
            closing = 100.0
            high = 100.25
            low = 99.75

            if session_date == TEST_DATES[0]:
                if session_minute >= 930:
                    opening = 100.0
                    closing = 100.0
                    high = 102.0
                    low = 98.0

            elif session_date == TEST_DATES[1]:
                if session_minute == 840:
                    opening = 99.0
                    closing = 99.0
                    high = 99.25
                    low = 98.0
                elif 841 <= session_minute <= 928:
                    opening = 100.0
                    closing = 100.0
                    high = 102.0
                    low = 98.0
                elif session_minute == 929:
                    opening = 101.75
                    closing = 102.0
                    high = 102.0
                    low = 101.5
                elif session_minute == 930:
                    opening = 103.0
                    closing = 102.75
                    high = 104.0
                    low = 102.5
                elif 931 <= session_minute <= 934:
                    opening = 102.75
                    closing = 102.0
                    high = 103.0
                    low = 101.75
                elif session_minute == 935:
                    opening = 102.0
                    closing = 101.0
                    high = 102.25
                    low = 99.5
                elif 936 <= session_minute < 1315:
                    opening = 100.0
                    closing = 100.0
                    high = 100.5
                    low = 99.5
                elif session_minute == 1315:
                    opening = 100.5
                    closing = 100.5
                    high = 100.75
                    low = 100.25

            else:
                if session_minute == 840:
                    opening = 99.0
                    closing = 99.0
                    high = 99.25
                    low = 98.0
                elif 841 <= session_minute <= 928:
                    opening = 100.0
                    closing = 100.0
                    high = 102.0
                    low = 98.0
                elif session_minute == 929:
                    opening = 101.75
                    closing = 102.0
                    high = 102.0
                    low = 101.5
                elif session_minute == 930:
                    opening = 102.0
                    closing = 102.25
                    high = 102.5
                    low = 101.5
                elif 931 <= session_minute <= 934:
                    opening = 102.25
                    closing = 102.5
                    high = 103.0
                    low = 102.0
                elif 935 <= session_minute <= 959:
                    opening = 102.5
                    closing = 104.0
                    high = 104.5
                    low = 102.0
                elif session_minute == 960:
                    opening = 104.0
                    closing = 104.25
                    high = 104.5
                    low = 103.75
                elif 961 <= session_minute < 1315:
                    opening = 105.0
                    closing = 105.0
                    high = 106.0
                    low = 104.0
                elif session_minute == 1315:
                    opening = 105.0
                    closing = 105.0
                    high = 105.25
                    low = 104.75

            rows.append(
                {
                    "ts_event": _timestamp(
                        session_date,
                        session_minute,
                    ),
                    "open": opening,
                    "high": high,
                    "low": low,
                    "close": closing,
                    "volume": 10,
                    "trading_date": pd.Timestamp(
                        session_date
                    ).date(),
                }
            )

    return pd.DataFrame(rows).sort_values(
        "ts_event",
        kind="stable",
    ).reset_index(drop=True)


def replay_fixture() -> tuple[pd.DataFrame, pd.DataFrame]:
    return replay_candidates(
        make_source_frame(),
        representation_id="BACKWARD_ADJUSTED",
        allowed_session_start=TEST_DATES[0],
        allowed_session_end=TEST_DATES[-1],
    )


class Exp026CoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = make_source_frame()
        cls.decisions, cls.trades = (
            replay_fixture()
        )

    def test_01_candidate_lock_is_exact(self) -> None:
        validate_candidate_specs()
        self.assertEqual(len(CANDIDATE_SPECS), 24)
        self.assertEqual(
            len(DEVELOPMENT_CANDIDATE_IDS),
            22,
        )
        self.assertEqual(
            len(CONTROL_CANDIDATE_IDS),
            2,
        )
        self.assertEqual(
            len(ALL_CANDIDATE_IDS),
            len(set(ALL_CANDIDATE_IDS)),
        )

    def test_02_source_columns_are_exact(self) -> None:
        self.assertEqual(
            SOURCE_COLUMNS,
            (
                "ts_event",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "trading_date",
            ),
        )

    def test_03_source_normalization_is_new_york_aware(
        self,
    ) -> None:
        source = normalise_source_frame(
            self.source,
            representation_id=(
                "BACKWARD_ADJUSTED"
            ),
            allowed_session_start=TEST_DATES[0],
            allowed_session_end=TEST_DATES[-1],
        )
        self.assertEqual(
            int(source.iloc[0]["session_minute"]),
            840,
        )
        self.assertEqual(
            source.iloc[0]["session_date"],
            TEST_DATES[0],
        )

    def test_04_protected_or_out_of_window_date_is_rejected(
        self,
    ) -> None:
        changed = self.source.copy()
        changed.loc[
            changed.index[-1],
            "trading_date",
        ] = pd.Timestamp("2026-01-02").date()
        changed.loc[
            changed.index[-1],
            "ts_event",
        ] = pd.Timestamp(
            "2026-01-02T20:59:00+00:00"
        )
        with self.assertRaisesRegex(
            ValueError,
            "out-of-window",
        ):
            normalise_source_frame(
                changed,
                representation_id=(
                    "BACKWARD_ADJUSTED"
                ),
                allowed_session_start=(
                    TEST_DATES[0]
                ),
                allowed_session_end=(
                    TEST_DATES[-1]
                ),
            )

    def test_05_observed_five_minute_bars_are_not_filled(
        self,
    ) -> None:
        source = normalise_source_frame(
            self.source,
            representation_id=(
                "BACKWARD_ADJUSTED"
            ),
            allowed_session_start=TEST_DATES[0],
            allowed_session_end=TEST_DATES[-1],
        )
        five = aggregate_observed_five_minute(
            source
        )
        self.assertTrue(
            five["observation_count"].eq(5).all()
        )
        self.assertEqual(
            len(five),
            96 * len(TEST_DATES),
        )

    def test_06_every_candidate_session_is_accounted_for(
        self,
    ) -> None:
        self.assertEqual(
            tuple(self.decisions.columns),
            DECISION_COLUMNS,
        )
        self.assertEqual(
            len(self.decisions),
            24 * len(TEST_DATES),
        )
        self.assertFalse(
            self.decisions.duplicated(
                ["candidate_id", "session_date"]
            ).any()
        )

    def test_07_trade_schema_and_one_trade_limit_are_exact(
        self,
    ) -> None:
        self.assertEqual(
            tuple(self.trades.columns),
            TRADE_COLUMNS,
        )
        self.assertFalse(
            self.trades.duplicated(
                ["candidate_id", "session_date"]
            ).any()
        )

    def test_08_first_gap_session_has_no_predecessor(
        self,
    ) -> None:
        first = self.decisions.loc[
            (
                self.decisions["candidate_id"]
                == "gap_fade_0p50_1r"
            )
            & (
                self.decisions["session_date"]
                == TEST_DATES[0]
            )
        ].iloc[0]
        self.assertFalse(bool(first["eligible"]))
        self.assertEqual(
            first["ineligibility_reason"],
            "PREVIOUS_REFERENCE_SESSION_UNAVAILABLE",
        )

    def test_09_gap_fade_thresholds_and_targets_are_exact(
        self,
    ) -> None:
        gap = self.trades.loc[
            self.trades["candidate_id"].str.startswith(
                "gap_fade"
            )
        ]
        self.assertEqual(len(gap), 6)
        self.assertEqual(set(gap["direction"]), {"short"})
        one_r = gap.loc[
            gap["candidate_id"].str.endswith("_1r")
        ]
        self.assertTrue(
            one_r["exit_reason"].eq(
                "profit_target"
            ).all()
        )
        self.assertTrue(
            np.allclose(
                one_r["target_price"],
                100.0,
            )
        )

    def test_10_premarket_requires_same_direction_signal(
        self,
    ) -> None:
        premarket = self.trades.loc[
            self.trades["candidate_id"].str.startswith(
                "premarket_continuation"
            )
        ]
        self.assertTrue(
            premarket["session_date"].eq(
                TEST_DATES[-1]
            ).all()
        )
        self.assertIn(
            "premarket_continuation_0p75_time",
            set(premarket["candidate_id"]),
        )
        self.assertNotIn(
            "premarket_continuation_0p875_time",
            set(premarket["candidate_id"]),
        )

    def test_11_opening_drive_uses_ten_oclock_entry(
        self,
    ) -> None:
        opening = self.trades.loc[
            self.trades["candidate_id"].str.startswith(
                "opening_drive"
            )
        ]
        self.assertFalse(opening.empty)
        self.assertTrue(
            opening["entry_session_minute"].eq(
                960
            ).all()
        )

    def test_12_fixed_controls_are_reported_not_selectable(
        self,
    ) -> None:
        registry = candidate_registry_frame()
        controls = registry.loc[
            registry["candidate_id"].isin(
                CONTROL_CANDIDATE_IDS
            )
        ]
        self.assertTrue(
            controls["candidate_role"].eq(
                "CONTROL"
            ).all()
        )
        self.assertFalse(
            controls["selectable"].any()
        )

    def test_13_missing_entry_minute_is_not_repaired(
        self,
    ) -> None:
        missing_timestamp = _timestamp(
            TEST_DATES[-1],
            935,
        )
        changed = self.source.loc[
            self.source["ts_event"]
            != missing_timestamp
        ]
        decisions, _ = replay_candidates(
            changed,
            representation_id=(
                "BACKWARD_ADJUSTED"
            ),
            allowed_session_start=TEST_DATES[0],
            allowed_session_end=TEST_DATES[-1],
            candidate_ids=(
                "premarket_continuation_0p50_time",
            ),
        )
        last = decisions.loc[
            decisions["session_date"]
            == TEST_DATES[-1]
        ].iloc[0]
        self.assertFalse(bool(last["eligible"]))
        self.assertEqual(
            last["ineligibility_reason"],
            "ENTRY_MINUTE_UNAVAILABLE",
        )

    def test_14_metrics_have_all_long_short_rows(
        self,
    ) -> None:
        metrics = candidate_metrics(
            self.trades,
            candidate_ids=ALL_CANDIDATE_IDS,
            period_start=TEST_DATES[0],
            period_end=TEST_DATES[-1],
        )
        self.assertEqual(
            tuple(metrics.columns),
            METRIC_COLUMNS,
        )
        self.assertEqual(
            set(metrics["segment"]),
            {
                DIRECTION_ALL,
                DIRECTION_LONG,
                DIRECTION_SHORT,
            },
        )
        self.assertEqual(
            len(metrics),
            24 * 3,
        )

    def test_15_cost_sensitivity_worsens_net_profit(
        self,
    ) -> None:
        costs = cost_sensitivity(
            self.trades,
            candidate_ids=(
                "gap_fade_0p50_1r",
            ),
            period_start=TEST_DATES[0],
            period_end=TEST_DATES[-1],
        )
        zero = costs.loc[
            costs["slippage_ticks_per_side"]
            == 0,
            "net_profit_usd",
        ].iloc[0]
        three = costs.loc[
            costs["slippage_ticks_per_side"]
            == 3,
            "net_profit_usd",
        ].iloc[0]
        self.assertGreater(zero, three)

    def test_16_phase_a_selection_excludes_controls(
        self,
    ) -> None:
        metrics = candidate_metrics(
            self.trades,
            period_start=TEST_DATES[0],
            period_end=TEST_DATES[-1],
        )
        survivors = select_phase_a_survivors(
            metrics
        )
        self.assertLessEqual(len(survivors), 6)
        self.assertFalse(
            survivors["candidate_id"].isin(
                CONTROL_CANDIDATE_IDS
            ).any()
        )

    def test_17_phase_b_selects_at_most_one_per_family(
        self,
    ) -> None:
        metrics = candidate_metrics(
            self.trades,
            period_start=TEST_DATES[0],
            period_end=TEST_DATES[-1],
        )
        survivors = select_phase_a_survivors(
            metrics
        )
        annual = annual_results(
            self.trades,
            candidate_ids=(
                DEVELOPMENT_CANDIDATE_IDS
            ),
            start_year=2016,
            end_year=2016,
        )
        finalists = select_phase_b_finalists(
            metrics,
            metrics,
            annual,
            phase_a_candidate_ids=(
                survivors["candidate_id"]
            ),
        )
        counts = finalists.groupby(
            "family_id"
        ).size()
        self.assertTrue((counts <= 1).all())

    def test_18_parameter_neighbours_are_reported(
        self,
    ) -> None:
        metrics = candidate_metrics(
            self.trades,
            candidate_ids=(
                DEVELOPMENT_CANDIDATE_IDS
            ),
            period_start=TEST_DATES[0],
            period_end=TEST_DATES[-1],
        )
        stability = parameter_stability(
            metrics
        )
        self.assertEqual(
            len(stability),
            22,
        )
        self.assertIn(
            "paired_exit_candidate",
            stability.columns,
        )

    def test_19_mirrored_outcomes_are_deterministic(
        self,
    ) -> None:
        first = mirrored_trade_outcomes(
            self.source,
            self.trades,
            representation_id=(
                "BACKWARD_ADJUSTED"
            ),
            allowed_session_start=TEST_DATES[0],
            allowed_session_end=TEST_DATES[-1],
        )
        second = mirrored_trade_outcomes(
            self.source,
            self.trades,
            representation_id=(
                "BACKWARD_ADJUSTED"
            ),
            allowed_session_start=TEST_DATES[0],
            allowed_session_end=TEST_DATES[-1],
        )
        self.assertEqual(
            canonical_dataframe_sha256(first),
            canonical_dataframe_sha256(second),
        )
        self.assertEqual(len(first), len(self.trades))

    def test_20_bootstrap_is_seed_deterministic(
        self,
    ) -> None:
        candidate_ids = (
            "gap_fade_0p50_1r",
            "premarket_continuation_0p50_time",
        )
        first = bootstrap_session_blocks(
            self.trades,
            candidate_ids=candidate_ids,
            session_dates=TEST_DATES,
            resamples=100,
            random_seed=123,
        )
        second = bootstrap_session_blocks(
            self.trades,
            candidate_ids=candidate_ids,
            session_dates=TEST_DATES,
            resamples=100,
            random_seed=123,
        )
        self.assertEqual(
            canonical_dataframe_sha256(first),
            canonical_dataframe_sha256(second),
        )

    def test_21_selection_aware_mcpt_repeats_all_candidates(
        self,
    ) -> None:
        mirrored = mirrored_trade_outcomes(
            self.source,
            self.trades,
            representation_id=(
                "BACKWARD_ADJUSTED"
            ),
            allowed_session_start=TEST_DATES[0],
            allowed_session_end=TEST_DATES[-1],
        )
        matrices = build_session_outcome_matrices(
            self.trades.loc[
                self.trades["candidate_id"].isin(
                    DEVELOPMENT_CANDIDATE_IDS
                )
            ],
            mirrored.loc[
                mirrored["candidate_id"].isin(
                    DEVELOPMENT_CANDIDATE_IDS
                )
            ],
            session_dates=TEST_DATES,
        )
        summary, distribution = (
            selection_aware_market_mcpt(
                matrices,
                phase_a_end=TEST_DATES[0],
                phase_b_start=TEST_DATES[1],
                phase_b_end=TEST_DATES[-1],
                permutations=20,
                random_seed=321,
            )
        )
        self.assertEqual(len(distribution), 20)
        self.assertTrue(
            summary[
                "all_22_candidates_inside_each_permutation"
            ]
        )
        self.assertTrue(
            summary[
                "phase_a_and_phase_b_selection_repeated"
            ]
        )
        self.assertGreater(
            summary["plus_one_p_value"],
            0.0,
        )
        self.assertLessEqual(
            summary["plus_one_p_value"],
            1.0,
        )

    def test_22_walk_forward_uses_prior_years_only(
        self,
    ) -> None:
        # A minimal empty-year check verifies the registered chronology
        # without requiring production data.
        extended = self.trades.copy()
        result = anchored_walk_forward(
            extended,
            test_years=(2019,),
            training_start="2010-06-07",
        )
        self.assertTrue(
            result["development_end"].eq(
                "2016-12-31"
            ).all()
        )
        self.assertTrue(
            result["validation_start"].eq(
                "2017-01-01"
            ).all()
        )
        self.assertTrue(
            result["validation_end"].eq(
                "2018-12-31"
            ).all()
        )


if __name__ == "__main__":
    unittest.main()
