from __future__ import annotations

from copy import deepcopy
import unittest

from exp009_implementation import (
    get_exp009_implementation,
    validate_exp009_implementation,
)


class Exp009ImplementationTests(unittest.TestCase):
    def test_implementation_is_complete_and_result_free(self) -> None:
        record = get_exp009_implementation()
        validate_exp009_implementation(record)
        self.assertEqual(record["candidate_count"], 24)
        self.assertEqual(record["strategy_family_count"], 6)
        self.assertEqual(record["results_viewed"], "NONE")

    def test_automatic_winner_cannot_be_enabled(self) -> None:
        record = deepcopy(get_exp009_implementation())
        record["comparison"]["automatic_winner"] = True
        with self.assertRaises(ValueError):
            validate_exp009_implementation(record, require_files=False)

    def test_expensive_tests_remain_deferred(self) -> None:
        record = deepcopy(get_exp009_implementation())
        record["deferred"]["mcpt"] = False
        with self.assertRaises(ValueError):
            validate_exp009_implementation(record, require_files=False)

    def test_prior_experiments_are_protected(self) -> None:
        record = deepcopy(get_exp009_implementation())
        record["protections"]["exp008_changed"] = True
        with self.assertRaises(ValueError):
            validate_exp009_implementation(record, require_files=False)


if __name__ == "__main__":
    unittest.main()
