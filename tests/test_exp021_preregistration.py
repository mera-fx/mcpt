from __future__ import annotations

import unittest

from exp021_preregistration import (
    EXPECTED_EXP020_CLOSURE_SHA256,
    EXP020_CLOSURE_COMMIT,
    get_exp021_preregistration,
    validate_exp021_preregistration,
)

class Exp021PreregistrationTests(unittest.TestCase):
    def test_preregistration_is_valid(self):
        validate_exp021_preregistration()

    def test_identity_is_locked(self):
        record = get_exp021_preregistration()
        self.assertEqual(record["experiment_id"], "EXP-021")
        self.assertEqual(record["research_status"], "PRE_REGISTERED")
        self.assertEqual(record["implementation_status"], "NOT_IMPLEMENTED")
        self.assertEqual(record["execution_status"], "NOT_RUN")

    def test_exp020_closure_is_frozen(self):
        frozen = get_exp021_preregistration()["frozen_inputs"]
        self.assertEqual(frozen["exp020_closure_commit"], EXP020_CLOSURE_COMMIT)
        self.assertEqual(
            frozen["exp020_closure_record_sha256"],
            EXPECTED_EXP020_CLOSURE_SHA256,
        )
        self.assertTrue(frozen["source_archive_read_only"])
        self.assertTrue(frozen["exp020_outputs_read_only"])
        self.assertEqual(frozen["databento_api_calls"], 0)

    def test_known_exp020_result_is_disclosed(self):
        disclosure = get_exp021_preregistration()["prior_result_disclosure"]
        known = disclosure["known_exp020_result"]
        self.assertTrue(disclosure["exp020_results_viewed_before_lock"])
        self.assertFalse(
            disclosure["candidate_diagnostic_results_viewed_before_lock"]
        )
        self.assertEqual(known["volume_crossovers_selected"], 0)
        self.assertEqual(known["calendar_fallbacks"], 65)
        self.assertEqual(known["fallbacks_without_provider_warnings"], 42)

    def test_candidate_matrix_is_exact(self):
        record = get_exp021_preregistration()
        methods = record["candidate_methods"]
        self.assertEqual(record["candidate_count"], 8)
        self.assertEqual(len(methods), 8)
        self.assertEqual(
            tuple(method["method_id"] for method in methods),
            tuple(record["fixed_selection_order"]),
        )
        self.assertEqual(
            {method["required_consecutive_sessions"] for method in methods},
            {1, 2},
        )
        self.assertEqual(
            {
                method["maximum_effective_common_sessions_after_calendar"]
                for method in methods
            },
            {0, 1, 2, 3},
        )

    def test_original_exp020_rule_is_control(self):
        methods = get_exp021_preregistration()["candidate_methods"]
        controls = [m for m in methods if m["control_method"]]
        self.assertEqual(len(controls), 1)
        self.assertEqual(controls[0]["method_id"], "VOL_GT_OUT_2S_E0")

    def test_diagnostic_window_is_locked(self):
        window = get_exp021_preregistration()["diagnostic_window"]
        self.assertEqual(window["start_common_sessions_before_calendar"], 10)
        self.assertEqual(window["maximum_common_sessions_after_calendar"], 3)
        self.assertTrue(
            window["trigger_sessions_must_be_consecutive_common_sessions"]
        )
        self.assertTrue(window["no_post_expiry_effective_boundary"])

    def test_warning_policy_is_conservative(self):
        policy = get_exp021_preregistration()["provider_warning_policy"]
        self.assertEqual(policy["warning_transition_count_expected"], 23)
        self.assertTrue(
            policy["warning_transitions_forced_to_calendar_fallback"]
        )
        self.assertFalse(policy["warning_volume_may_select_candidate_boundary"])

    def test_selection_gates_and_order_are_locked(self):
        record = get_exp021_preregistration()
        gates = record["selection_gates"]
        self.assertEqual(gates["clean_transition_count"], 42)
        self.assertEqual(gates["minimum_clean_volume_trigger_count"], 34)
        self.assertEqual(gates["minimum_noncalendar_roll_date_count"], 20)
        self.assertFalse(gates["selection_uses_strategy_returns"])
        self.assertTrue(
            record["fixed_selection_order"][0].startswith("VOL_GT_OUT_2S")
        )

    def test_no_strategy_construction_or_trading_permission(self):
        record = get_exp021_preregistration()
        for key in (
            "rerun_exp019", "rerun_exp020", "construct_continuous_series",
            "strategy_replay", "strategy_optimization", "mcpt", "bootstrap",
            "walk_forward", "paper_trading", "live_trading",
        ):
            with self.subTest(key=key):
                self.assertTrue(record["prohibited_actions"][key])
        self.assertFalse(
            record["classification"]["selected_method_authorizes_construction"]
        )
        self.assertFalse(
            record["classification"]["selected_method_authorizes_strategy_use"]
        )

    def test_all_candidate_data_must_be_retained(self):
        interpretation = get_exp021_preregistration()["interpretation"]
        self.assertTrue(
            interpretation["all_candidate_results_must_be_reported"]
        )
        self.assertTrue(
            interpretation["no_pass_fail_result_may_delete_candidate_data"]
        )

    def test_mutation_is_rejected(self):
        record = get_exp021_preregistration()
        record["selection_gates"]["minimum_clean_volume_trigger_count"] = 1
        with self.assertRaisesRegex(
            ValueError,
            "preregistration record changed",
        ):
            validate_exp021_preregistration(record)

if __name__ == "__main__":
    unittest.main()
