from __future__ import annotations

from copy import deepcopy
import unittest

from exp005_full_validation_result import (
    EXPECTED_FILE_SHA256,
    EXPECTED_RESULT,
    get_exp005_full_validation_result,
    load_tracked_result,
    validate_exp005_full_validation_result,
)


class Exp005FullValidationResultTests(unittest.TestCase):
    def test_tracked_record_is_valid(self) -> None:
        self.assertEqual(load_tracked_result(), EXPECTED_RESULT)

    def test_decision_passes_to_review(self) -> None:
        result = get_exp005_full_validation_result()
        self.assertEqual(result["evaluation"]["decision"], "PASS_TO_REVIEW")
        self.assertEqual(result["mcpt"]["permutations"], 1000)
        self.assertEqual(result["evaluation"]["failed_gates"], [])

    def test_metric_change_is_rejected(self) -> None:
        changed = deepcopy(EXPECTED_RESULT)
        changed["results"]["NQ"]["net_profit_usd"] += 1.0
        with self.assertRaisesRegex(ValueError, "NQ net_profit_usd changed"):
            validate_exp005_full_validation_result(changed)

    def test_access_change_is_rejected(self) -> None:
        changed = deepcopy(EXPECTED_RESULT)
        changed["quick_transfer_rerun"] = True
        with self.assertRaisesRegex(ValueError, "protection fields changed"):
            validate_exp005_full_validation_result(changed)

    def test_tracked_hash_is_frozen(self) -> None:
        self.assertEqual(
            EXPECTED_FILE_SHA256,
            "7d2a3d1eb8716851fc913482c55809c360959b7a5d9eb3e474389b21131b6987",
        )


if __name__ == "__main__":
    unittest.main()
