from __future__ import annotations

from copy import deepcopy
import unittest

from exp013_validation_result import (
    EXPECTED_BOOTSTRAP_CANONICAL_SHA256,
    EXPECTED_CANDIDATE_CANONICAL_SHA256,
    EXPECTED_COST_CANONICAL_SHA256,
    EXPECTED_MCPT_CANONICAL_SHA256,
    EXPECTED_VALIDATION_CANONICAL_SHA256,
    EXPECTED_WALK_FORWARD_CANONICAL_SHA256,
    canonical_dataframe_sha256,
    canonical_object_sha256,
    load_bootstrap,
    load_candidate_measurements,
    load_cost_sensitivity,
    load_mcpt,
    load_validation_result,
    load_walk_forward,
    validate_exp013_validation_result,
    verify_local_exp013_validation_result,
)


class Exp013ValidationResultTests(unittest.TestCase):
    def test_local_result_is_valid(self) -> None:
        result = verify_local_exp013_validation_result()
        self.assertEqual(
            result["evaluation"]["classification"],
            "STRONG_HISTORICAL_EVIDENCE",
        )

    def test_all_result_hashes_are_frozen(self) -> None:
        self.assertEqual(
            canonical_object_sha256(load_validation_result()),
            EXPECTED_VALIDATION_CANONICAL_SHA256,
        )
        self.assertEqual(
            canonical_dataframe_sha256(load_candidate_measurements()),
            EXPECTED_CANDIDATE_CANONICAL_SHA256,
        )
        self.assertEqual(
            canonical_dataframe_sha256(load_walk_forward()),
            EXPECTED_WALK_FORWARD_CANONICAL_SHA256,
        )
        self.assertEqual(
            canonical_object_sha256(load_bootstrap()),
            EXPECTED_BOOTSTRAP_CANONICAL_SHA256,
        )
        self.assertEqual(
            canonical_dataframe_sha256(load_cost_sensitivity()),
            EXPECTED_COST_CANONICAL_SHA256,
        )
        self.assertEqual(
            canonical_dataframe_sha256(load_mcpt()),
            EXPECTED_MCPT_CANONICAL_SHA256,
        )

    def test_three_finalists_remain_visible(self) -> None:
        candidates = load_candidate_measurements()
        self.assertEqual(
            set(candidates["candidate_id"]),
            {
                "gap_fade_0p50_1r",
                "premarket_continuation_0p50_time",
                "premarket_continuation_0p75_time",
            },
        )
        self.assertEqual(len(candidates), 3)

    def test_measurement_leader_and_low_sample_warning_are_preserved(
        self,
    ) -> None:
        result = verify_local_exp013_validation_result()
        self.assertEqual(
            result["selection"]["measurement_leader_id"],
            "premarket_continuation_0p75_time",
        )
        self.assertTrue(
            result["selection"]["measurement_leader_row"]["low_sample"]
        )
        self.assertFalse(
            result["selection"]["automatic_trading_winner"]
        )

    def test_walk_forward_and_discovery_wide_mcpt_are_exact(self) -> None:
        result = verify_local_exp013_validation_result()
        self.assertEqual(
            result["walk_forward"]["profitable_test_folds"], 3
        )
        self.assertAlmostEqual(
            result["walk_forward"]["combined_test_net_profit_usd"],
            26295.0,
        )
        self.assertEqual(
            result["mcpt"]["permutations_at_least_real"], 3
        )
        self.assertAlmostEqual(
            result["mcpt"]["discovery_wide_p_value"],
            4 / 1001,
            places=12,
        )

    def test_all_bootstrap_intervals_support_positive_context(
        self,
    ) -> None:
        result = verify_local_exp013_validation_result()
        self.assertEqual(len(result["bootstrap"]), 3)
        for diagnostic in result["bootstrap"]:
            self.assertGreater(
                diagnostic[
                    "average_trade_usd_95_percentile_interval"
                ][0],
                0.0,
            )
            self.assertGreater(
                diagnostic[
                    "trade_profit_factor_95_percentile_interval"
                ][0],
                1.0,
            )

    def test_post_selection_limit_and_no_authorization_are_preserved(
        self,
    ) -> None:
        result = verify_local_exp013_validation_result()
        self.assertFalse(result["independent_confirmation"])
        self.assertFalse(result["paper_trading_authorized"])
        self.assertFalse(result["live_trading_authorized"])
        self.assertTrue(
            result["mcpt"][
                "does_not_erase_post_result_human_selection"
            ]
        )

    def test_result_mutation_is_rejected(self) -> None:
        changed = deepcopy(load_validation_result())
        changed["mcpt"]["discovery_wide_p_value"] = 0.05
        with self.assertRaisesRegex(
            ValueError,
            "discovery-wide MCPT p-value changed",
        ):
            validate_exp013_validation_result(
                changed,
                verify_hashes=False,
            )


if __name__ == "__main__":
    unittest.main()
