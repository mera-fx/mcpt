from __future__ import annotations

from copy import deepcopy
import unittest

from exp008_implementation import (
    get_exp008_implementation,
    validate_exp008_implementation,
)


class Exp008ImplementationTests(
    unittest.TestCase
):
    def test_implementation_is_valid_and_pre_result(
        self,
    ) -> None:
        validate_exp008_implementation()
        record = (
            get_exp008_implementation()
        )
        self.assertEqual(
            record[
                "implementation_status"
            ],
            "IMPLEMENTED_NOT_RUN",
        )
        self.assertEqual(
            record["results_viewed"],
            "NONE",
        )

    def test_grid_has_27_locked_combinations(
        self,
    ) -> None:
        record = (
            get_exp008_implementation()
        )
        self.assertEqual(
            record[
                "parameter_combinations"
            ],
            27,
        )
        self.assertTrue(
            record[
                "optimization_enabled"
            ]
        )

    def test_mcpt_reselects_all_candidates(
        self,
    ) -> None:
        analysis = (
            get_exp008_implementation()[
                "analysis"
            ]
        )
        self.assertTrue(
            analysis[
                "all_27_candidates_inside_mcpt"
            ]
        )
        self.assertTrue(
            analysis[
                "selection_inside_mcpt"
            ]
        )
        self.assertEqual(
            analysis[
                "mcpt_permutations"
            ],
            1000,
        )
        self.assertEqual(
            analysis["mcpt_seed"],
            48,
        )

    def test_mutation_is_rejected(
        self,
    ) -> None:
        changed = deepcopy(
            get_exp008_implementation()
        )
        changed["grid"][
            "reward_to_risk"
        ] = [
            0.5,
            1.0,
            2.0,
        ]

        with self.assertRaisesRegex(
            ValueError,
            "grid changed",
        ):
            validate_exp008_implementation(
                changed,
                require_files=False,
            )

    def test_prior_experiments_are_protected(
        self,
    ) -> None:
        protections = (
            get_exp008_implementation()[
                "protections"
            ]
        )
        self.assertFalse(
            protections[
                "exp005_changed"
            ]
        )
        self.assertFalse(
            protections[
                "exp006_changed"
            ]
        )
        self.assertFalse(
            protections[
                "exp007_changed"
            ]
        )
        self.assertFalse(
            protections[
                "result_calculated_during_implementation"
            ]
        )


if __name__ == "__main__":
    unittest.main()
