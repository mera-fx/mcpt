from __future__ import annotations

import unittest

from experiment_lifecycle import get_experiment_lifecycle
from register_exp014 import add_exp014_lifecycle


class Exp014LifecycleTests(unittest.TestCase):
    def test_exp014_is_preregistered(self) -> None:
        record = get_experiment_lifecycle("EXP-014")
        self.assertEqual(record.stage, "PRE_REGISTERED")
        self.assertEqual(
            record.strategy_name,
            "finalist_behaviour_and_complementarity",
        )
        self.assertIn("complementary", record.hypothesis.lower())
        self.assertIn("no rule", record.next_action.lower())

    def test_exp013_and_prior_experiments_remain_frozen(self) -> None:
        expected = {
            "EXP-005": "ACCEPTED_FOR_PAPER_TESTING",
            "EXP-006": "REJECTED",
            "EXP-007": "REJECTED",
            "EXP-008": "REJECTED",
            "EXP-009": "REVIEW",
            "EXP-010": "REVIEW",
            "EXP-011": "REVIEW",
            "EXP-012": "REVIEW",
            "EXP-013": "REVIEW",
        }
        for experiment_id, stage in expected.items():
            self.assertEqual(
                get_experiment_lifecycle(experiment_id).stage,
                stage,
            )

    def test_registration_is_idempotent_when_present(self) -> None:
        source = '"EXP-014": ExperimentLifecycle(\n'
        self.assertEqual(add_exp014_lifecycle(source), source)


if __name__ == "__main__":
    unittest.main()
