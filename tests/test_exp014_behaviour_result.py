from __future__ import annotations

from copy import deepcopy
import unittest

from exp014_behaviour_result import (
    EXPECTED_CANONICAL_SHA256,
    EXPECTED_IMPLEMENTATION_COMMIT,
    canonical_dataframe_sha256,
    canonical_object_sha256,
    load_behaviour_breakdowns,
    load_concentration_measurements,
    load_drawdown_diagnostics,
    load_enriched_ledger,
    load_monthly_measurements,
    load_overlap_measurements,
    load_pair_session_pnl,
    load_period_comparison,
    load_regime_context,
    load_rolling_measurements,
    load_session_pnl,
    load_sleeve_pair_measurements,
    load_standalone_measurements,
    load_study_result,
    validate_exp014_behaviour_result,
    verify_local_exp014_behaviour_result,
)


class Exp014BehaviourResultTests(unittest.TestCase):
    def test_local_result_is_frozen_and_valid(self) -> None:
        result = verify_local_exp014_behaviour_result()
        self.assertEqual(
            result["git"]["commit"],
            EXPECTED_IMPLEMENTATION_COMMIT,
        )
        self.assertEqual(
            result["interpretation"][
                "expected_lifecycle_after_measurement"
            ],
            "REVIEW",
        )

    def test_all_result_hashes_are_frozen(self) -> None:
        actual = {
            "study_result": canonical_object_sha256(
                load_study_result()
            ),
            "standalone": canonical_dataframe_sha256(
                load_standalone_measurements()
            ),
            "period": canonical_dataframe_sha256(
                load_period_comparison()
            ),
            "behaviour": canonical_dataframe_sha256(
                load_behaviour_breakdowns()
            ),
            "concentration": canonical_dataframe_sha256(
                load_concentration_measurements()
            ),
            "drawdown": canonical_dataframe_sha256(
                load_drawdown_diagnostics()
            ),
            "monthly": canonical_dataframe_sha256(
                load_monthly_measurements()
            ),
            "overlap": canonical_dataframe_sha256(
                load_overlap_measurements()
            ),
            "pair_session": canonical_dataframe_sha256(
                load_pair_session_pnl()
            ),
            "regime": canonical_dataframe_sha256(
                load_regime_context()
            ),
            "rolling": canonical_dataframe_sha256(
                load_rolling_measurements()
            ),
            "session": canonical_dataframe_sha256(
                load_session_pnl()
            ),
            "pairs": canonical_dataframe_sha256(
                load_sleeve_pair_measurements()
            ),
        }
        for candidate_id in (
            "gap_fade_0p50_1r",
            "premarket_continuation_0p50_time",
            "premarket_continuation_0p75_time",
        ):
            actual[f"ledger_{candidate_id}"] = (
                canonical_dataframe_sha256(
                    load_enriched_ledger(candidate_id)
                )
            )
        self.assertEqual(actual, EXPECTED_CANONICAL_SHA256)

    def test_annual_measurement_correction_is_preserved(self) -> None:
        pairs = load_sleeve_pair_measurements().set_index("pair_id")
        first = pairs.loc["gap_fade_plus_premarket_0p50"]
        second = pairs.loc["gap_fade_plus_premarket_0p75"]

        self.assertEqual(int(first["profitable_years"]), 5)
        self.assertEqual(int(first["total_years"]), 6)
        self.assertAlmostEqual(float(first["worst_year_usd"]), -1915.0)

        self.assertEqual(int(second["profitable_years"]), 6)
        self.assertEqual(int(second["total_years"]), 6)
        self.assertAlmostEqual(float(second["worst_year_usd"]), 1750.0)

    def test_2025_weakness_and_low_sample_warning_remain_visible(
        self,
    ) -> None:
        period = load_period_comparison()
        rows = period[period["period"] == "2025"].set_index(
            "candidate_id"
        )
        self.assertAlmostEqual(
            float(
                rows.loc[
                    "premarket_continuation_0p75_time",
                    "net_profit_usd",
                ]
            ),
            -2890.0,
        )
        standalone = load_standalone_measurements().set_index(
            "candidate_id"
        )
        self.assertTrue(
            bool(
                standalone.loc[
                    "premarket_continuation_0p75_time",
                    "low_sample",
                ]
            )
        )

    def test_overlap_and_pairs_do_not_create_portfolio_claim(
        self,
    ) -> None:
        overlap = load_overlap_measurements().set_index(
            ["left_candidate_id", "right_candidate_id"]
        )
        self.assertAlmostEqual(
            float(
                overlap.loc[
                    (
                        "gap_fade_0p50_1r",
                        "premarket_continuation_0p75_time",
                    ),
                    "all_session_pnl_correlation",
                ]
            ),
            0.02053197807929911,
        )
        pairs = load_sleeve_pair_measurements()
        self.assertTrue(
            bool(
                pairs[
                    "diagnostic_not_executable_portfolio"
                ].all()
            )
        )

        result = verify_local_exp014_behaviour_result()
        self.assertTrue(
            result["interpretation"][
                "arithmetic_pairs_not_executable_portfolios"
            ]
        )
        self.assertFalse(
            result["interpretation"]["paper_trading_authorized"]
        )
        self.assertFalse(
            result["interpretation"]["live_trading_authorized"]
        )

    def test_mutated_corrected_pair_value_is_rejected(self) -> None:
        record = deepcopy(load_study_result())
        standalone = load_standalone_measurements()
        period = load_period_comparison()
        behaviour = load_behaviour_breakdowns()
        concentration = load_concentration_measurements()
        drawdown = load_drawdown_diagnostics()
        monthly = load_monthly_measurements()
        overlap = load_overlap_measurements()
        pair_session = load_pair_session_pnl()
        regime = load_regime_context()
        rolling = load_rolling_measurements()
        session = load_session_pnl()
        pairs = load_sleeve_pair_measurements()
        pairs.loc[
            pairs["pair_id"]
            == "gap_fade_plus_premarket_0p75",
            "profitable_years",
        ] = 0

        with self.assertRaisesRegex(
            ValueError,
            "profitable_years changed",
        ):
            validate_exp014_behaviour_result(
                record=record,
                standalone=standalone,
                period=period,
                behaviour=behaviour,
                concentration=concentration,
                drawdown=drawdown,
                monthly=monthly,
                overlap=overlap,
                pair_session=pair_session,
                regime=regime,
                rolling=rolling,
                session=session,
                pairs=pairs,
                verify_hashes=False,
                verify_report=False,
            )


if __name__ == "__main__":
    unittest.main()
