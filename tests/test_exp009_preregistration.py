from __future__ import annotations

import unittest

from exp009_preregistration import (
    FAMILY_CANDIDATES,
    get_exp009_preregistration,
    validate_exp009_preregistration,
)


class Exp009PreregistrationTests(unittest.TestCase):
    def test_preregistration_is_valid(self) -> None:
        validate_exp009_preregistration()

    def test_six_families_have_four_candidates_each(self) -> None:
        self.assertEqual(len(FAMILY_CANDIDATES), 6)
        self.assertTrue(
            all(len(candidates) == 4 for candidates in FAMILY_CANDIDATES.values())
        )

    def test_candidate_budget_is_24_unique_candidates(self) -> None:
        budget = get_exp009_preregistration()["candidate_budget"]
        candidate_ids = [
            item["candidate_id"] for item in budget["candidates"]
        ]
        self.assertEqual(budget["total_candidates"], 24)
        self.assertEqual(len(candidate_ids), 24)
        self.assertEqual(len(set(candidate_ids)), 24)

    def test_unavailable_gap_and_delta_families_are_excluded(self) -> None:
        record = get_exp009_preregistration()
        self.assertFalse(record["market_and_data"]["overnight_data_available"])
        self.assertIn(
            "overnight_gap_continuation",
            record["excluded_families"],
        )
        self.assertIn("overnight_gap_fade", record["excluded_families"])
        self.assertIn("order_flow_delta", record["excluded_families"])

    def test_common_execution_is_conservative(self) -> None:
        execution = get_exp009_preregistration()[
            "shared_execution_and_risk_rules"
        ]
        self.assertTrue(
            execution["completed_five_minute_signal_bars_only"]
        )
        self.assertEqual(execution["execution_resolution"], "1 minute")
        self.assertEqual(
            execution["same_minute_stop_and_target_rule"],
            "STOP_FIRST_CONSERVATIVE",
        )
        self.assertFalse(execution["overnight_positions"])

    def test_sizing_is_fixed_and_costs_are_shared(self) -> None:
        record = get_exp009_preregistration()
        sizing = record["position_sizing"]
        self.assertEqual(sizing["method"], "FIXED_ONE_CONTRACT")
        self.assertFalse(sizing["volatility_targeting_enabled"])
        self.assertEqual(
            record["contract_and_cost_model"][
                "nq_cost_sensitivity_ticks_per_side"
            ],
            [0, 1, 2],
        )

    def test_measurement_precedes_any_pass_fail_claim(self) -> None:
        review = get_exp009_preregistration()[
            "comparison_and_review"
        ]
        self.assertFalse(review["formal_accept_reject_gates"])
        self.assertFalse(review["single_composite_score"])
        self.assertFalse(review["automatic_strategy_winner"])
        self.assertEqual(review["finalist_count_maximum"], 3)

    def test_expensive_tests_are_deferred(self) -> None:
        deferred = get_exp009_preregistration()[
            "deferred_expensive_tests"
        ]
        self.assertFalse(deferred["mcpt_run_in_exp009"])
        self.assertFalse(deferred["bootstrap_run_in_exp009"])
        self.assertFalse(deferred["family_optimization_run_in_exp009"])

    def test_reporting_keeps_current_colour_standard(self) -> None:
        reporting = get_exp009_preregistration()[
            "reporting_requirements"
        ]
        self.assertTrue(reporting["positive_numbers_use_neutral_text"])
        self.assertTrue(reporting["adverse_numbers_use_red_text"])
        self.assertTrue(reporting["green_reserved_for_status_words"])

    def test_candidate_mutation_is_rejected(self) -> None:
        changed = get_exp009_preregistration()
        changed["candidate_budget"]["candidates"].pop()
        with self.assertRaisesRegex(ValueError, "candidate budget changed"):
            validate_exp009_preregistration(changed)

    def test_automatic_winner_mutation_is_rejected(self) -> None:
        changed = get_exp009_preregistration()
        changed["comparison_and_review"]["automatic_strategy_winner"] = True
        with self.assertRaisesRegex(
            ValueError,
            "comparison/review procedure changed",
        ):
            validate_exp009_preregistration(changed)


if __name__ == "__main__":
    unittest.main()

