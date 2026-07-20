from __future__ import annotations

import unittest

from exp012_implementation import (
    get_exp012_implementation,
    validate_exp012_implementation,
)


class Exp012ImplementationTests(unittest.TestCase):
    def test_implementation_is_complete_and_result_free(self) -> None:
        validate_exp012_implementation()
        record = get_exp012_implementation()
        self.assertEqual(
            record["implementation_status"], "IMPLEMENTED_NOT_RUN"
        )
        self.assertEqual(record["candidate_count"], 24)
        self.assertEqual(record["strategy_family_count"], 6)
        self.assertEqual(record["expected_sessions"], 1331)

    def test_entries_remain_in_cash_session(self) -> None:
        record = get_exp012_implementation()
        self.assertTrue(record["entries_during_cash_session_only"])
        self.assertFalse(
            record["protections"]["overnight_execution_claimed"]
        )

    def test_no_winner_or_expensive_validation(self) -> None:
        record = get_exp012_implementation()
        self.assertFalse(record["comparison"]["automatic_winner"])
        self.assertFalse(
            record["comparison"]["formal_accept_reject_gates"]
        )
        self.assertTrue(all(record["deferred"].values()))

    def test_mutation_is_rejected(self) -> None:
        changed = get_exp012_implementation()
        changed["expected_sessions"] = 1344
        with self.assertRaisesRegex(ValueError, "identity"):
            validate_exp012_implementation(
                changed, require_files=False
            )


if __name__ == "__main__":
    unittest.main()
