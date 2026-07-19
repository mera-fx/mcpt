from __future__ import annotations

from copy import deepcopy
import unittest

from exp010_validation_result import (
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
    validate_exp010_validation_result,
    verify_local_exp010_validation_result,
)


class Exp010ValidationResultTests(unittest.TestCase):
    def test_local_result_is_valid(self) -> None:
        result = verify_local_exp010_validation_result()
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

    def test_measurement_leader_and_user_reference_remain_distinct(
        self,
    ) -> None:
        result = verify_local_exp010_validation_result()
        selection = result["selection"]
        self.assertEqual(
            selection["selected_candidate_id"],
            "opening_drive_0p5_time",
        )
        self.assertEqual(
            selection["user_reference_candidate_id"],
            "opening_drive_0p5_1p5r",
        )
        self.assertFalse(selection["automatic_trading_winner"])

    def test_walk_forward_and_mcpt_are_exact(self) -> None:
        result = verify_local_exp010_validation_result()
        self.assertEqual(
            result["walk_forward"]["profitable_test_folds"], 4
        )
        self.assertAlmostEqual(
            result["walk_forward"]["combined_test_net_profit_usd"],
            114695.0,
        )
        self.assertEqual(
            result["mcpt"]["selected_permutations_at_least_real"], 25
        )
        self.assertAlmostEqual(
            result["mcpt"]["selection_aware_p_value"],
            26 / 1001,
            places=12,
        )

    def test_prior_family_selection_limit_is_preserved(self) -> None:
        result = verify_local_exp010_validation_result()
        self.assertFalse(
            result["mcpt"]["prior_six_family_selection_corrected"]
        )
        self.assertFalse(result["independent_confirmation"])
        self.assertIn(
            "ALREADY_VIEWED",
            result["historical_status"],
        )

    def test_no_paper_or_live_authorization(self) -> None:
        result = verify_local_exp010_validation_result()
        self.assertFalse(result["paper_trading_authorized"])
        self.assertFalse(result["live_trading_authorized"])
        self.assertIsNone(
            result["evaluation"]["lifecycle_accept_reject_decision"]
        )

    def test_result_mutation_is_rejected(self) -> None:
        changed = deepcopy(load_validation_result())
        changed["mcpt"]["selection_aware_p_value"] = 0.01
        with self.assertRaisesRegex(
            ValueError,
            "selection-aware MCPT p-value changed",
        ):
            validate_exp010_validation_result(
                changed,
                verify_hashes=False,
            )


if __name__ == "__main__":
    unittest.main()
