from __future__ import annotations

import unittest

from exp022_preregistration import (
    EXPECTED_EXP021_CLOSURE_SHA256,
    EXP021_CLOSURE_COMMIT,
    get_exp022_preregistration,
    validate_exp022_preregistration,
)


class Exp022PreregistrationTests(unittest.TestCase):
    def test_01_preregistration_is_valid(self):
        validate_exp022_preregistration()

    def test_02_identity_is_locked(self):
        record = get_exp022_preregistration()
        self.assertEqual(record["experiment_id"], "EXP-022")
        self.assertEqual(record["research_status"], "PRE_REGISTERED")
        self.assertEqual(record["implementation_status"], "NOT_IMPLEMENTED")
        self.assertEqual(record["execution_status"], "NOT_RUN")

    def test_03_exp021_closure_is_frozen(self):
        frozen = get_exp022_preregistration()["frozen_inputs"]
        self.assertEqual(
            frozen["exp021_closure_commit"],
            EXP021_CLOSURE_COMMIT,
        )
        self.assertEqual(
            frozen["exp021_closure_record_sha256"],
            EXPECTED_EXP021_CLOSURE_SHA256,
        )
        self.assertTrue(frozen["exp021_outputs_read_only"])
        self.assertEqual(frozen["databento_api_calls"], 0)

    def test_04_selected_method_is_exact(self):
        rule = get_exp022_preregistration()["selected_roll_rule"]
        self.assertEqual(
            rule["candidate_id"],
            "VOL_GT_OUT_2S_E3",
        )
        self.assertEqual(
            rule["required_consecutive_sessions"],
            2,
        )
        self.assertEqual(
            rule[
                "maximum_effective_common_sessions_after_calendar"
            ],
            3,
        )
        self.assertTrue(
            rule["effective_roll_dates_are_frozen_from_exp021"]
        )
        self.assertFalse(rule["recalculate_roll_dates"])

    def test_05_selected_counts_are_locked(self):
        rule = get_exp022_preregistration()["selected_roll_rule"]
        self.assertEqual(rule["volume_driven_transition_count"], 40)
        self.assertEqual(rule["calendar_fallback_transition_count"], 25)
        self.assertEqual(rule["provider_warning_fallback_count"], 23)
        self.assertEqual(rule["clean_fallback_count"], 2)

    def test_06_two_series_are_locked(self):
        spec = get_exp022_preregistration()["series_specification"]
        self.assertEqual(spec["series_count"], 2)
        self.assertEqual(
            tuple(item["filename"] for item in spec["series"]),
            (
                "selected_roll_unadjusted.parquet",
                "selected_roll_backward_adjusted.parquet",
            ),
        )
        self.assertEqual(
            spec["roll_method_column_value"],
            "VOL_GT_OUT_2S_E3",
        )

    def test_07_stitching_rule_is_locked(self):
        rule = get_exp022_preregistration()["stitching_rule"]
        self.assertIn(
            "outgoing contract",
            rule["before_effective_roll_trading_date"],
        )
        self.assertIn(
            "incoming contract",
            rule["on_or_after_effective_roll_trading_date"],
        )
        self.assertFalse(rule["intraday_rolls"])
        self.assertFalse(rule["missing_source_minutes_filled"])

    def test_08_backward_adjustment_is_locked(self):
        rule = get_exp022_preregistration()["adjustment_rule"]
        self.assertEqual(rule["method"], "BACKWARD_DIFFERENCE")
        self.assertIn(
            "incoming_reference_close - outgoing_reference_close",
            rule["roll_difference_points"],
        )
        self.assertFalse(rule["volume_adjusted"])
        self.assertFalse(rule["source_contract_adjusted"])

    def test_09_twenty_hard_checks_are_locked(self):
        record = get_exp022_preregistration()
        self.assertEqual(record["hard_check_count"], 20)
        self.assertEqual(len(record["hard_checks"]), 20)
        self.assertEqual(
            len(set(record["hard_checks"])),
            20,
        )

    def test_10_separate_implementation_and_authorization_required(self):
        boundary = get_exp022_preregistration()["execution_boundary"]
        self.assertTrue(
            boundary["separate_implementation_commit_required"]
        )
        self.assertTrue(
            boundary["separate_execution_authorization_required"]
        )
        self.assertTrue(boundary["protected_preflight_required"])
        self.assertTrue(boundary["one_authorized_construction_run"])

    def test_11_no_strategy_or_trading_permission(self):
        record = get_exp022_preregistration()
        for key in (
            "strategy_replay",
            "strategy_optimization",
            "mcpt",
            "bootstrap",
            "walk_forward",
            "paper_trading",
            "live_trading",
        ):
            with self.subTest(key=key):
                self.assertTrue(record["prohibited_actions"][key])
        self.assertFalse(
            record["completion_classification"][
                "construction_authorizes_strategy_use"
            ]
        )

    def test_12_mutation_is_rejected(self):
        record = get_exp022_preregistration()
        record["selected_roll_rule"]["candidate_id"] = (
            "VOL_GT_OUT_1S_E3"
        )
        with self.assertRaisesRegex(
            ValueError,
            "preregistration record changed",
        ):
            validate_exp022_preregistration(record)


if __name__ == "__main__":
    unittest.main()
