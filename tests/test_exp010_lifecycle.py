from __future__ import annotations

import unittest

from experiment_lifecycle import get_experiment_lifecycle


class Exp010LifecycleTests(unittest.TestCase):
    def test_exp010_is_preregistered(self) -> None:
        record = get_experiment_lifecycle("EXP-010")
        self.assertEqual(record.stage, "PRE_REGISTERED")
        self.assertEqual(
            record.strategy_name,
            "opening_drive_deep_validation",
        )
        self.assertIn("all four", record.stage_reason.lower())

    def test_exp009_remains_in_review(self) -> None:
        record = get_experiment_lifecycle("EXP-009")
        self.assertEqual(record.stage, "REVIEW")
        self.assertEqual(
            record.strategy_name,
            "multi_strategy_discovery_tournament",
        )

    def test_prior_experiments_remain_frozen(self) -> None:
        expected = {
            "EXP-005": "ACCEPTED_FOR_PAPER_TESTING",
            "EXP-006": "REJECTED",
            "EXP-007": "REJECTED",
            "EXP-008": "REJECTED",
        }
        for experiment_id, stage in expected.items():
            self.assertEqual(
                get_experiment_lifecycle(experiment_id).stage,
                stage,
            )


if __name__ == "__main__":
    unittest.main()
