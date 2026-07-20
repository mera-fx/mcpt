from __future__ import annotations

import unittest

from close_exp013_review import replace_exp013_block
from experiment_lifecycle import get_experiment_lifecycle


class Exp013LifecycleTests(unittest.TestCase):
    def test_exp013_is_closed_to_review(self) -> None:
        record = get_experiment_lifecycle("EXP-013")
        self.assertEqual(record.stage, "REVIEW")
        self.assertEqual(
            record.strategy_name,
            "extended_context_finalist_validation",
        )
        self.assertIn("24-candidate", record.hypothesis.lower())
        self.assertIn(
            "strong historical evidence",
            record.stage_reason.lower(),
        )
        self.assertIn(
            "not independent confirmation",
            record.next_action.lower(),
        )

    def test_exp012_and_prior_experiments_remain_frozen(self) -> None:
        expected = {
            "EXP-005": "ACCEPTED_FOR_PAPER_TESTING",
            "EXP-006": "REJECTED",
            "EXP-007": "REJECTED",
            "EXP-008": "REJECTED",
            "EXP-009": "REVIEW",
            "EXP-010": "REVIEW",
            "EXP-011": "REVIEW",
            "EXP-012": "REVIEW",
        }
        for experiment_id, stage in expected.items():
            self.assertEqual(
                get_experiment_lifecycle(experiment_id).stage,
                stage,
            )

    def test_review_closure_is_idempotent_when_present(self) -> None:
        from pathlib import Path

        source = Path("experiment_lifecycle.py").read_text(
            encoding="utf-8"
        )
        self.assertEqual(replace_exp013_block(source), source)


if __name__ == "__main__":
    unittest.main()
