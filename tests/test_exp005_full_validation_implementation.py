from __future__ import annotations

from pathlib import Path
import unittest

from exp005_full_validation_implementation import (
    get_exp005_full_validation_implementation,
    validate_exp005_full_validation_implementation,
)


class Exp005FullValidationImplementationTests(
    unittest.TestCase
):
    def test_implementation_is_valid_and_pre_result(
        self,
    ) -> None:
        validate_exp005_full_validation_implementation()
        record = (
            get_exp005_full_validation_implementation()
        )
        self.assertFalse(
            record[
                "full_validation_results_viewed"
            ]
        )
        self.assertFalse(
            record["quick_transfer_rerun"]
        )

    def test_confirmation_import_counts_are_locked(
        self,
    ) -> None:
        record = (
            get_exp005_full_validation_implementation()
        )
        imported = record["confirmation_import"]
        self.assertEqual(
            imported["included_sessions"],
            733,
        )
        self.assertEqual(
            imported["NQ_1m_rows"],
            285_870,
        )
        self.assertEqual(
            imported["NQ_5m_rows"],
            57_174,
        )

    def test_mcpt_and_no_optimization_are_locked(
        self,
    ) -> None:
        record = (
            get_exp005_full_validation_implementation()
        )
        self.assertEqual(
            record["mcpt"]["permutations"],
            1000,
        )
        self.assertEqual(
            record["mcpt"]["random_seed"],
            45,
        )
        self.assertFalse(
            record["locked_strategy"][
                "optimization"
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
            get_exp005_full_validation_implementation()
        )
        self.assertTrue(
            Path(record["document"]).exists()
        )


if __name__ == "__main__":
    unittest.main()
