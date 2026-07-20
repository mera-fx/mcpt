from __future__ import annotations

from copy import deepcopy
import unittest

from exp011_implementation import (
    get_exp011_implementation,
    validate_exp011_implementation,
)


class Exp011ImplementationTests(unittest.TestCase):
    def test_implementation_is_valid_and_result_free(self) -> None:
        validate_exp011_implementation()
        record = get_exp011_implementation()
        self.assertEqual(
            record["implementation_status"], "IMPLEMENTED_NOT_RUN"
        )
        self.assertEqual(record["results_viewed"], "NONE")
        self.assertEqual(record["measurement_row_count"], 6)

    def test_calibration_and_evaluation_are_separated(self) -> None:
        record = get_exp011_implementation()
        self.assertEqual(record["calibration"]["end"], "2020-12-31")
        self.assertEqual(record["evaluation"]["start"], "2021-01-04")
        self.assertTrue(
            record["calibration"]["evaluation_data_excluded"]
        )

    def test_no_winner_mcpt_or_trading_authorization(self) -> None:
        record = get_exp011_implementation()
        self.assertFalse(record["evaluation"]["automatic_winner"])
        self.assertFalse(record["evaluation"]["pass_fail_gate"])
        self.assertFalse(record["protections"]["new_mcpt"])
        self.assertFalse(
            record["protections"]["paper_trading_authorized"]
        )
        self.assertFalse(
            record["protections"]["live_trading_authorized"]
        )

    def test_mutation_is_rejected(self) -> None:
        changed = deepcopy(get_exp011_implementation())
        changed["sizing"]["integer_mnq_cap"] = 30
        with self.assertRaisesRegex(ValueError, "sizing"):
            validate_exp011_implementation(
                changed, require_files=False
            )


if __name__ == "__main__":
    unittest.main()
