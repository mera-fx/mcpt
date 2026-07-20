from __future__ import annotations

import unittest

from exp013_implementation import (
    get_exp013_implementation,
    validate_exp013_implementation,
)


class Exp013ImplementationTests(unittest.TestCase):
    def test_implementation_is_complete_and_result_free(self) -> None:
        validate_exp013_implementation()
        record = get_exp013_implementation()
        self.assertEqual(
            record["implementation_status"], "IMPLEMENTED_NOT_RUN"
        )
        self.assertEqual(len(record["finalist_ids"]), 3)
        self.assertEqual(
            record["source_candidate_count_inside_primary_mcpt"], 24
        )

    def test_analysis_and_safety_locks_are_exact(self) -> None:
        record = get_exp013_implementation()
        self.assertEqual(record["mcpt_seed"], 53)
        self.assertEqual(record["bootstrap_seed"], 5301)
        self.assertEqual(record["mcpt_exact_extended_slots"], 1320)
        self.assertFalse(
            record["protections"]["automatic_trading_winner"]
        )
        self.assertFalse(
            record["protections"]["live_trading_authorized"]
        )

    def test_mutation_is_rejected(self) -> None:
        changed = get_exp013_implementation()
        changed["source_candidate_count_inside_primary_mcpt"] = 3
        with self.assertRaisesRegex(ValueError, "identity"):
            validate_exp013_implementation(
                changed, require_files=False
            )


if __name__ == "__main__":
    unittest.main()
