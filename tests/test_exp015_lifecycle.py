from __future__ import annotations

import unittest

from close_exp015_review import replace_exp015_block
from experiment_lifecycle import get_experiment_lifecycle


class Exp015LifecycleTests(unittest.TestCase):
    def test_exp015_is_closed_to_review(self) -> None:
        record = get_experiment_lifecycle("EXP-015")
        self.assertEqual(record.stage, "REVIEW")
        self.assertEqual(
            record.strategy_name,
            "london_strategic_edge_data_qualification",
        )
        self.assertIn("identity_unresolved", record.stage_reason.lower())
        self.assertIn("no mnq", record.stage_reason.lower())
        self.assertIn(
            "not qualified as the primary",
            record.next_action.lower(),
        )
        self.assertIn(
            "no paper or live trading",
            record.next_action.lower(),
        )

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

    def test_review_closure_is_idempotent_when_present(self) -> None:
        source = (
            '"EXP-015": ExperimentLifecycle(\n'
            '    stage="REVIEW",\n'
            '    stage_reason="IDENTITY_UNRESOLVED",\n'
            '    next_action="No paper or live trading",\n'
            ")\n"
            "}\n"
            "\ndef normalize_experiment_id(value):\n"
            "    return value\n"
        )
        self.assertEqual(replace_exp015_block(source), source)


if __name__ == "__main__":
    unittest.main()
