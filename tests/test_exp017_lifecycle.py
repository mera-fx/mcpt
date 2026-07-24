from __future__ import annotations

import unittest

from experiment_lifecycle import get_experiment_lifecycle


class Exp017LifecycleTests(unittest.TestCase):
    def test_exp017_is_closed_in_review(self) -> None:
        record = get_experiment_lifecycle("EXP-017")
        self.assertEqual(record.stage, "REVIEW")
        self.assertIn("access_incomplete", record.stage_reason.lower())
        self.assertIn("exp-018", record.next_action.lower())

    def test_exp018_is_closed_as_qualified_source(self) -> None:
        record = get_experiment_lifecycle("EXP-018")

        self.assertEqual(record.stage, "REVIEW")
        self.assertEqual(
            record.strategy_name,
            "databento_exact_contract_qualification",
        )
        self.assertIn(
            "qualified_as_accessible_exact_contract_source",
            record.stage_reason.lower(),
        )
        self.assertIn(
            "do not rerun exp-018",
            record.next_action.lower(),
        )
        self.assertIn(
            "separately preregistered",
            record.next_action.lower(),
        )

    def test_exp016_remains_review(self) -> None:
        self.assertEqual(
            get_experiment_lifecycle("EXP-016").stage,
            "REVIEW",
        )


if __name__ == "__main__":
    unittest.main()
