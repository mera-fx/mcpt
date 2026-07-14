from __future__ import annotations

from copy import deepcopy
import unittest

from exp005_review_result import (
    EXPECTED_FILE_SHA256,
    get_exp005_review_result,
    load_tracked_review_result,
    validate_exp005_review_result,
)


class Exp005ReviewResultTests(unittest.TestCase):
    def test_tracked_result_is_valid(self) -> None:
        result = load_tracked_review_result()
        self.assertEqual(
            result["evaluation"]["decision"],
            "ACCEPT_FOR_PAPER_TESTING",
        )

    def test_all_twelve_checks_pass(self) -> None:
        checks = get_exp005_review_result()["evaluation"]["checks"]
        self.assertEqual(len(checks), 12)
        self.assertTrue(all(item["passed"] for item in checks.values()))

    def test_no_research_workflow_was_rerun(self) -> None:
        result = get_exp005_review_result()
        self.assertFalse(result["strategy_rerun"])
        self.assertFalse(result["mcpt_rerun"])
        self.assertFalse(result["data_change"])

    def test_changed_decision_is_rejected(self) -> None:
        changed = deepcopy(get_exp005_review_result())
        changed["evaluation"]["decision"] = "REJECT"
        with self.assertRaisesRegex(ValueError, "acceptance changed"):
            validate_exp005_review_result(changed)

    def test_hash_is_frozen(self) -> None:
        self.assertEqual(
            EXPECTED_FILE_SHA256,
            "3ac6538b1645f674174bb2716a893eb3ec8e1a131c64d05de438db5d12829751",
        )


if __name__ == "__main__":
    unittest.main()
