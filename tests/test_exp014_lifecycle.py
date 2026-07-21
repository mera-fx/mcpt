from __future__ import annotations

from pathlib import Path
import unittest

from close_exp014_review import replace_exp014_block
from experiment_lifecycle import get_experiment_lifecycle


class Exp014LifecycleTests(unittest.TestCase):
    def test_exp014_is_closed_to_review(self) -> None:
        record = get_experiment_lifecycle("EXP-014")
        self.assertEqual(record.stage, "REVIEW")
        self.assertEqual(
            record.strategy_name,
            "finalist_behaviour_and_complementarity",
        )
        self.assertIn(
            "annual-measurement correction",
            record.stage_reason.lower(),
        )
        self.assertIn(
            "no paper or live trading",
            record.next_action.lower(),
        )

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

    def test_review_closure_is_idempotent_when_present(self) -> None:
        source = Path("experiment_lifecycle.py").read_text(
            encoding="utf-8"
        )
        self.assertEqual(replace_exp014_block(source), source)


if __name__ == "__main__":
    unittest.main()
