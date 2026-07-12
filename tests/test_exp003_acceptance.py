from __future__ import annotations

import unittest
from pathlib import Path

from experiment_lifecycle import (
    get_experiment_lifecycle,
)
from paper_testing_plan import (
    get_exp003_paper_testing_plan,
    validate_exp003_paper_testing_plan,
)


class Exp003AcceptanceTests(
    unittest.TestCase
):
    def test_lifecycle_is_accepted(
        self,
    ) -> None:
        lifecycle = get_experiment_lifecycle(
            "EXP-003"
        )

        self.assertEqual(
            lifecycle.stage,
            "ACCEPTED_FOR_PAPER_TESTING",
        )

        self.assertIn(
            "research outputs frozen",
            lifecycle.next_action.lower(),
        )

    def test_review_v2_record_exists(
        self,
    ) -> None:
        root = Path(
            __file__
        ).resolve().parents[1]

        record = (
            root
            / "research"
            / "EXP-003_review_v2_decision.md"
        )

        self.assertTrue(record.exists())

        text = record.read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "ACCEPTED_FOR_PAPER_TESTING",
            text,
        )

        self.assertIn(
            "Research rerun:** No",
            text,
        )

    def test_paper_plan_is_valid(
        self,
    ) -> None:
        validate_exp003_paper_testing_plan()

        plan = get_exp003_paper_testing_plan()

        self.assertEqual(
            plan["mode"],
            "paper_only",
        )

        self.assertEqual(
            plan[
                "minimum_observation"
            ]["calendar_weeks"],
            12,
        )

        self.assertEqual(
            plan[
                "minimum_observation"
            ]["completed_trades"],
            20,
        )

    def test_fixed_parameters_remain_locked(
        self,
    ) -> None:
        plan = get_exp003_paper_testing_plan()

        self.assertEqual(
            plan["fixed_parameters"],
            {
                "vol_lookback": 48,
                "compression_quantile": 0.20,
                "breakout_lookback": 48,
            },
        )


if __name__ == "__main__":
    unittest.main()
