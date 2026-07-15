from __future__ import annotations

from copy import deepcopy
import unittest

from exp006_implementation import (
    EXP006_IMPLEMENTATION,
    validate_exp006_implementation,
)


class Exp006ImplementationTests(unittest.TestCase):
    def test_implementation_is_valid_and_pre_result(self) -> None:
        validate_exp006_implementation()
        self.assertFalse(
            EXP006_IMPLEMENTATION["results_calculated"]
        )

    def test_all_27_candidates_run_inside_mcpt(self) -> None:
        mcpt = EXP006_IMPLEMENTATION[
            "selection_aware_mcpt"
        ]
        self.assertTrue(
            mcpt[
                "all_27_candidates_inside_each_permutation"
            ]
        )
        self.assertEqual(mcpt["permutations"], 1000)

    def test_exp005_control_is_protected(self) -> None:
        self.assertFalse(
            EXP006_IMPLEMENTATION["protections"][
                "exp005_control_changed"
            ]
        )

    def test_mutation_is_rejected(self) -> None:
        changed = deepcopy(EXP006_IMPLEMENTATION)
        changed["selection_aware_mcpt"][
            "permutations"
        ] = 100
        with self.assertRaisesRegex(
            ValueError,
            "MCPT changed",
        ):
            validate_exp006_implementation(changed)


if __name__ == "__main__":
    unittest.main()
