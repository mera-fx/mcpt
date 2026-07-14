from __future__ import annotations

from copy import deepcopy
import unittest

from exp005_paper_testing_plan import (
    EXP005_PAPER_TESTING_PLAN,
    get_exp005_paper_testing_plan,
    validate_exp005_paper_testing_plan,
)


class Exp005PaperTestingPlanTests(unittest.TestCase):
    def test_plan_is_valid(self) -> None:
        validate_exp005_paper_testing_plan()

    def test_observation_requires_both_minimums(self) -> None:
        observation = EXP005_PAPER_TESTING_PLAN["minimum_observation"]
        self.assertEqual(observation["calendar_weeks"], 12)
        self.assertEqual(observation["completed_nq_trades"], 40)
        self.assertEqual(
            observation["completion_rule"],
            "Both minimums must be met.",
        )

    def test_reference_capital_is_explicit(self) -> None:
        capital = EXP005_PAPER_TESTING_PLAN["analytical_reference_capital"]
        self.assertEqual(capital["NQ_usd"], 100000.0)
        self.assertEqual(capital["MNQ_usd"], 10000.0)
        self.assertTrue(capital["not_a_margin_requirement"])

    def test_rules_and_costs_are_fixed(self) -> None:
        plan = get_exp005_paper_testing_plan()
        self.assertFalse(plan["fixed_strategy_rules"]["optimization"])
        self.assertEqual(plan["cost_model"]["NQ"]["round_trip_cost_usd"], 15.0)
        self.assertEqual(plan["cost_model"]["MNQ"]["round_trip_cost_usd"], 3.0)

    def test_live_orders_are_prohibited(self) -> None:
        prohibited = " ".join(
            EXP005_PAPER_TESTING_PLAN["prohibited_actions"]
        ).lower()
        self.assertIn("no live orders", prohibited)
        self.assertFalse(
            EXP005_PAPER_TESTING_PLAN["data_workflow"][
                "broker_order_connection_allowed"
            ]
        )

    def test_mutated_plan_is_rejected(self) -> None:
        changed = deepcopy(EXP005_PAPER_TESTING_PLAN)
        changed["minimum_observation"]["completed_nq_trades"] = 20
        with self.assertRaisesRegex(
            ValueError,
            "observation requirement changed",
        ):
            validate_exp005_paper_testing_plan(changed)


if __name__ == "__main__":
    unittest.main()
