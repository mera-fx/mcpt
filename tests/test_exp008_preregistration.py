from __future__ import annotations

from copy import deepcopy
import unittest

from exp008_preregistration import (
    get_exp008_preregistration,
    validate_exp008_preregistration,
)


class Exp008PreregistrationTests(
    unittest.TestCase
):
    def test_preregistration_is_valid(
        self,
    ) -> None:
        validate_exp008_preregistration()

    def test_grid_has_exactly_27_unique_combinations(
        self,
    ) -> None:
        grid = get_exp008_preregistration()[
            "parameter_grid"
        ]
        keys = [
            item["parameter_key"]
            for item in grid["combinations"]
        ]
        self.assertEqual(
            grid["combination_count"],
            27,
        )
        self.assertEqual(len(keys), 27)
        self.assertEqual(len(set(keys)), 27)

    def test_grid_dimensions_are_exact(
        self,
    ) -> None:
        dimensions = (
            get_exp008_preregistration()[
                "parameter_grid"
            ]["dimensions"]
        )
        self.assertEqual(
            dimensions["opening_range_minutes"],
            [15, 30, 45],
        )
        self.assertEqual(
            dimensions["reward_to_risk"],
            [0.5, 1.0, 1.5],
        )
        self.assertEqual(
            dimensions[
                "forced_flat_time_new_york"
            ],
            ["12:00", "14:00", "15:55"],
        )

    def test_exp007_baseline_is_included_once(
        self,
    ) -> None:
        combinations = (
            get_exp008_preregistration()[
                "parameter_grid"
            ]["combinations"]
        )
        baseline_count = sum(
            item["parameter_key"]
            == "or30_target1p0_flat1400"
            for item in combinations
        )
        self.assertEqual(
            baseline_count,
            1,
        )

    def test_selection_requires_neighbor_stability(
        self,
    ) -> None:
        selection = (
            get_exp008_preregistration()[
                "candidate_selection"
            ]
        )
        self.assertEqual(
            selection[
                "minimum_profitable_neighbor_fraction"
            ],
            0.5,
        )
        self.assertEqual(
            selection[
                "minimum_neighbor_median_profit_factor_strict"
            ],
            1.0,
        )

    def test_five_anchored_folds_are_locked(
        self,
    ) -> None:
        walk_forward = (
            get_exp008_preregistration()[
                "anchored_walk_forward"
            ]
        )
        self.assertEqual(
            walk_forward["fold_count"],
            5,
        )
        self.assertEqual(
            len(walk_forward["folds"]),
            5,
        )
        self.assertTrue(
            walk_forward[
                "selection_repeated_in_each_training_window"
            ]
        )

    def test_mcpt_reselects_all_27_inside_permutation(
        self,
    ) -> None:
        mcpt = (
            get_exp008_preregistration()[
                "selection_aware_mcpt"
            ]
        )
        self.assertEqual(
            mcpt["permutations"],
            1000,
        )
        self.assertEqual(
            mcpt["random_seed"],
            48,
        )
        self.assertTrue(
            mcpt[
                "all_27_candidates_run_inside_each_permutation"
            ]
        )
        self.assertTrue(
            mcpt[
                "candidate_selection_repeated_inside_each_permutation"
            ]
        )

    def test_selected_pf_must_exceed_exp007(
        self,
    ) -> None:
        record = get_exp008_preregistration()
        gate = record[
            "historical_decision_gates"
        ][
            "minimum_selected_nq_trade_profit_factor_strict"
        ]
        baseline = record[
            "experiment_relationships"
        ]["exp007"][
            "baseline_nq_trade_profit_factor"
        ]
        self.assertEqual(gate, baseline)

    def test_sizing_remains_isolated(
        self,
    ) -> None:
        sizing = get_exp008_preregistration()[
            "position_sizing"
        ]
        self.assertEqual(
            sizing["method"],
            "FIXED_ONE_CONTRACT",
        )
        self.assertFalse(
            sizing[
                "volatility_targeting_enabled"
            ]
        )

    def test_historical_claim_is_exploratory(
        self,
    ) -> None:
        interpretation = (
            get_exp008_preregistration()[
                "interpretation"
            ]
        )
        self.assertEqual(
            interpretation[
                "historical_status"
            ],
            "EXPLORATORY_BECAUSE_2019_2025_WAS_ALREADY_VIEWED",
        )
        self.assertTrue(
            interpretation[
                "historical_result_cannot_authorize_live_trading"
            ]
        )

    def test_grid_mutation_is_rejected(
        self,
    ) -> None:
        changed = (
            get_exp008_preregistration()
        )
        changed["parameter_grid"][
            "dimensions"
        ]["reward_to_risk"] = [0.5, 1.0, 2.0]

        with self.assertRaisesRegex(
            ValueError,
            "parameter grid changed",
        ):
            validate_exp008_preregistration(
                changed
            )


if __name__ == "__main__":
    unittest.main()
