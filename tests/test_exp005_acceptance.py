from __future__ import annotations

import unittest

from exp005_paper_testing_plan import validate_exp005_paper_testing_plan
from exp005_review_result import load_tracked_review_result
from experiment_lifecycle import get_experiment_lifecycle


class Exp005AcceptanceTests(unittest.TestCase):
    def test_review_authorizes_paper_testing(self) -> None:
        result = load_tracked_review_result()
        self.assertEqual(
            result["evaluation"]["decision"],
            "ACCEPT_FOR_PAPER_TESTING",
        )

    def test_lifecycle_is_accepted(self) -> None:
        lifecycle = get_experiment_lifecycle("EXP-005")
        self.assertEqual(
            lifecycle.stage,
            "ACCEPTED_FOR_PAPER_TESTING",
        )
        self.assertIn("paper-only", lifecycle.next_action.lower())

    def test_paper_plan_is_locked(self) -> None:
        validate_exp005_paper_testing_plan()


if __name__ == "__main__":
    unittest.main()
