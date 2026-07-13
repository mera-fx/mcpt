from __future__ import annotations

from pathlib import Path
import unittest

from exp005_quick_transfer_implementation import (
    get_exp005_quick_transfer_implementation,
    validate_exp005_quick_transfer_implementation,
)


class Exp005QuickImplementationTests(
    unittest.TestCase
):
    def test_implementation_is_valid_and_pre_result(
        self,
    ) -> None:
        validate_exp005_quick_transfer_implementation()

        record = (
            get_exp005_quick_transfer_implementation()
        )

        self.assertFalse(
            record["results_viewed"]
        )
        self.assertFalse(
            record[
                "confirmation_period_accessed"
            ]
        )

    def test_no_optimization_is_locked(
        self,
    ) -> None:
        record = (
            get_exp005_quick_transfer_implementation()
        )

        self.assertTrue(
            record["safety"][
                "no_parameter_optimization"
            ]
        )
        self.assertFalse(
            record["mcpt"][
                "optimization_inside_permutation"
            ]
        )


    def test_human_implementation_record_exists(
        self,
    ) -> None:
        record = (
            get_exp005_quick_transfer_implementation()
        )

        self.assertTrue(
            Path(
                record["document"]
            ).exists()
        )

    def test_mcpt_is_one_minute_and_25_permutations(
        self,
    ) -> None:
        record = (
            get_exp005_quick_transfer_implementation()
        )

        self.assertEqual(
            record["mcpt"][
                "input_timeframe"
            ],
            "one_minute",
        )
        self.assertEqual(
            record["mcpt"][
                "permutations"
            ],
            25,
        )


if __name__ == "__main__":
    unittest.main()
