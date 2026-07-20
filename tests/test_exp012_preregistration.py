from __future__ import annotations

import unittest

from exp012_preregistration import (
    EXP012_CANDIDATES,
    FAMILY_CANDIDATES,
    get_exp012_preregistration,
    validate_exp012_preregistration,
)


class Exp012PreregistrationTests(unittest.TestCase):
    def test_preregistration_is_valid(self) -> None:
        validate_exp012_preregistration()

    def test_six_families_and_24_candidates_are_locked(self) -> None:
        record = get_exp012_preregistration()
        budget = record["candidate_budget"]
        self.assertEqual(budget["family_count"], 6)
        self.assertEqual(budget["candidates_per_family"], 4)
        self.assertEqual(budget["total_candidates"], 24)
        self.assertEqual(budget["candidates"], EXP012_CANDIDATES)
        self.assertEqual(len(FAMILY_CANDIDATES), 6)
        self.assertEqual(
            len({item["candidate_id"] for item in EXP012_CANDIDATES}),
            24,
        )

    def test_only_2020_through_2025_are_included(self) -> None:
        data = get_exp012_preregistration()["market_and_data"]
        self.assertEqual(
            data["included_years"],
            [2020, 2021, 2022, 2023, 2024, 2025],
        )
        self.assertEqual(data["expected_complete_aligned_sessions"], 1331)
        self.assertTrue(data["exclude_2019_due_to_limited_aligned_coverage"])
        self.assertTrue(data["use_only_complete_aligned_nq_mnq_sessions"])

    def test_extended_context_does_not_authorize_overnight_entries(
        self,
    ) -> None:
        record = get_exp012_preregistration()
        execution = record["shared_execution_and_risk_rules"]
        costs = record["contract_and_cost_model"]
        self.assertTrue(execution["entries_during_cash_session_only"])
        self.assertFalse(execution["overnight_positions"])
        self.assertFalse(costs["overnight_execution_cost_model_claimed"])

    def test_gap_predecessor_rule_is_explicit(self) -> None:
        features = get_exp012_preregistration()["feature_definitions"]
        self.assertIn(
            "immediately preceding exchange trade date",
            features["previous_cash_close"],
        )
        self.assertIn(
            "complete aligned included session",
            features["previous_cash_close"],
        )

    def test_all_families_have_plain_english_explanations(self) -> None:
        families = get_exp012_preregistration()["family_definitions"]
        self.assertEqual(set(families), set(FAMILY_CANDIDATES))
        for family in families.values():
            self.assertTrue(family["plain_english"].strip())

    def test_discovery_has_no_automatic_decision(self) -> None:
        record = get_exp012_preregistration()
        interpretation = record["interpretation"]
        review = record["comparison_and_review"]
        self.assertTrue(interpretation["measurement_first"])
        self.assertTrue(interpretation["no_single_pass_fail_decision"])
        self.assertTrue(interpretation["no_automatic_winner"])
        self.assertFalse(review["formal_accept_reject_gates"])
        self.assertFalse(review["single_composite_score"])
        self.assertTrue(review["all_candidates_remain_visible"])

    def test_expensive_tests_are_deferred(self) -> None:
        deferred = get_exp012_preregistration()["deferred_expensive_tests"]
        self.assertFalse(deferred["mcpt_run_in_exp012"])
        self.assertFalse(deferred["bootstrap_run_in_exp012"])
        self.assertFalse(deferred["walk_forward_run_in_exp012"])
        self.assertFalse(deferred["family_optimization_run_in_exp012"])

    def test_reporting_standard_includes_context_and_readability(
        self,
    ) -> None:
        reporting = get_exp012_preregistration()["reporting_requirements"]
        self.assertTrue(
            reporting["plain_english_strategy_explanation_for_every_family"]
        )
        self.assertTrue(reporting["extended_context_visuals"])
        self.assertTrue(reporting["chart_canvas_is_solid_opaque_white"])
        self.assertTrue(reporting["positive_numbers_use_neutral_text"])
        self.assertTrue(reporting["adverse_numbers_use_red_text"])
        self.assertTrue(reporting["green_reserved_for_status_words"])

    def test_candidate_mutation_is_rejected(self) -> None:
        changed = get_exp012_preregistration()
        changed["candidate_budget"]["candidates"][0][
            "minimum_gap_fraction"
        ] = 0.10
        with self.assertRaisesRegex(ValueError, "candidate budget"):
            validate_exp012_preregistration(changed)

    def test_data_mutation_is_rejected(self) -> None:
        changed = get_exp012_preregistration()
        changed["market_and_data"]["expected_complete_aligned_sessions"] = 1344
        with self.assertRaisesRegex(ValueError, "market/data lock"):
            validate_exp012_preregistration(changed)

    def test_overnight_entry_mutation_is_rejected(self) -> None:
        changed = get_exp012_preregistration()
        changed["shared_execution_and_risk_rules"][
            "entries_during_cash_session_only"
        ] = False
        with self.assertRaisesRegex(ValueError, "execution rules"):
            validate_exp012_preregistration(changed)

    def test_trading_authorization_is_prohibited(self) -> None:
        interpretation = get_exp012_preregistration()["interpretation"]
        self.assertFalse(interpretation["paper_trading_authorized"])
        self.assertFalse(interpretation["live_trading_authorized"])
        self.assertTrue(
            interpretation["future_deep_validation_requires_new_experiment_id"]
        )


if __name__ == "__main__":
    unittest.main()
