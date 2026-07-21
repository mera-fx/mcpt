from __future__ import annotations

import unittest

from experiment_lifecycle import get_experiment_lifecycle
from register_exp015 import add_exp015_lifecycle


class Exp015LifecycleTests(unittest.TestCase):
    def test_exp015_is_preregistered(self) -> None:
        record = get_experiment_lifecycle("EXP-015")
        self.assertEqual(record.stage, "PRE_REGISTERED")
        self.assertEqual(
            record.strategy_name,
            "london_strategic_edge_data_qualification",
        )
        self.assertIn("data-source", record.experiment_name.lower())
        self.assertIn("catalog", record.next_action.lower())
        self.assertIn("do not download", record.next_action.lower())

    def test_exp014_and_prior_experiments_remain_frozen(self) -> None:
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
            "EXP-014": "REVIEW",
        }
        for experiment_id, stage in expected.items():
            self.assertEqual(
                get_experiment_lifecycle(experiment_id).stage,
                stage,
            )

    def test_registration_is_idempotent_when_present(self) -> None:
        source = '"EXP-015": ExperimentLifecycle(\n'
        self.assertEqual(add_exp015_lifecycle(source), source)


if __name__ == "__main__":
    unittest.main()
