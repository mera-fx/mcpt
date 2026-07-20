from __future__ import annotations

import unittest

from experiment_lifecycle import get_experiment_lifecycle


class Exp011LifecycleTests(unittest.TestCase):
    def test_exp011_is_closed_to_review(self) -> None:
        record = get_experiment_lifecycle("EXP-011")
        self.assertEqual(record.stage, "REVIEW")
        self.assertEqual(
            record.strategy_name,
            "opening_drive_position_sizing_study",
        )
        self.assertIn("equal-dollar-risk", record.hypothesis.lower())
        self.assertIn("automatic winner", record.next_action.lower())

    def test_exp010_remains_in_review(self) -> None:
        record = get_experiment_lifecycle("EXP-010")
        self.assertEqual(record.stage, "REVIEW")
        self.assertEqual(
            record.strategy_name,
            "opening_drive_deep_validation",
        )

    def test_prior_experiments_remain_frozen(self) -> None:
        expected = {
            "EXP-005": "ACCEPTED_FOR_PAPER_TESTING",
            "EXP-006": "REJECTED",
            "EXP-007": "REJECTED",
            "EXP-008": "REJECTED",
            "EXP-009": "REVIEW",
        }
        for experiment_id, stage in expected.items():
            self.assertEqual(
                get_experiment_lifecycle(experiment_id).stage,
                stage,
            )


if __name__ == "__main__":
    unittest.main()
