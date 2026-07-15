from __future__ import annotations

from copy import deepcopy
import unittest

from exp006_preregistration import (
    BASELINE_PARAMETERS,
    EXP006_PREREGISTRATION,
    build_locked_parameter_grid,
    validate_exp006_preregistration,
)


class Exp006PreregistrationTests(
    unittest.TestCase
):
    def test_preregistration_is_valid(
        self,
    ) -> None:
        validate_exp006_preregistration()

    def test_grid_has_exactly_27_unique_combinations(
        self,
    ) -> None:
        grid = build_locked_parameter_grid()
        keys = {
            (
                item["opening_range_minutes"],
                item[
                    "final_entry_time_new_york"
                ],
                item["direction_mode"],
            )
            for item in grid
        }

        self.assertEqual(len(grid), 27)
        self.assertEqual(len(keys), 27)

    def test_exp005_baseline_is_included_once(
        self,
    ) -> None:
        matches = [
            item
            for item in build_locked_parameter_grid()
            if all(
                item[key] == value
                for key, value
                in BASELINE_PARAMETERS.items()
            )
        ]
        self.assertEqual(len(matches), 1)

    def test_selection_aware_mcpt_optimizes_inside_permutation(
        self,
    ) -> None:
        mcpt = EXP006_PREREGISTRATION[
            "selection_aware_mcpt"
        ]
        self.assertEqual(
            mcpt["permutations"],
            1000,
        )
        self.assertTrue(
            mcpt[
                "optimization_inside_each_permutation"
            ]
        )

    def test_historical_claim_is_exploratory(
        self,
    ) -> None:
        interpretation = (
            EXP006_PREREGISTRATION[
                "interpretation"
            ]
        )
        self.assertEqual(
            interpretation[
                "final_confirmation_source"
            ],
            "NEW_FORWARD_DATA_ONLY",
        )
        self.assertTrue(
            interpretation[
                "historical_result_cannot_authorize_live_trading"
            ]
        )

    def test_mcpt_prohibition_wording_is_locked(
        self,
    ) -> None:
        prohibited = " ".join(
            EXP006_PREREGISTRATION[
                "prohibited_actions"
            ]
        ).lower()
        self.assertIn(
            "during mcpt",
            prohibited,
        )

    def test_grid_mutation_is_rejected(
        self,
    ) -> None:
        changed = deepcopy(
            EXP006_PREREGISTRATION
        )
        changed[
            "locked_parameter_grid"
        ]["opening_range_minutes"].append(60)

        with self.assertRaisesRegex(
            ValueError,
            "27-combination grid changed",
        ):
            validate_exp006_preregistration(
                changed
            )


if __name__ == "__main__":
    unittest.main()
