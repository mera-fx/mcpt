from __future__ import annotations

import unittest

from exp023_preregistration import (
    EXPECTED_EXP022_CLOSURE_SHA256,
    EXPECTED_SESSION_QUALITY_SHA256,
    EXP014_FREEZE_COMMIT,
    EXP022_CLOSURE_COMMIT,
    FINALIST_IDS,
    get_exp023_preregistration,
    validate_exp023_preregistration,
)


class Exp023PreregistrationTests(unittest.TestCase):
    def test_01_preregistration_is_valid(self):
        validate_exp023_preregistration()

    def test_02_identity_is_locked(self):
        record = get_exp023_preregistration()
        self.assertEqual(
            record["experiment_id"],
            "EXP-023",
        )
        self.assertEqual(
            record["research_status"],
            "PRE_REGISTERED",
        )
        self.assertEqual(
            record["implementation_status"],
            "NOT_IMPLEMENTED",
        )
        self.assertEqual(
            record["execution_status"],
            "NOT_RUN",
        )

    def test_03_known_prior_results_are_disclosed(self):
        disclosure = get_exp023_preregistration()[
            "prior_result_disclosure"
        ]
        self.assertTrue(
            disclosure[
                "exp014_strategy_results_viewed_before_lock"
            ]
        )
        self.assertTrue(
            disclosure[
                "exp022_construction_results_viewed_before_lock"
            ]
        )
        self.assertFalse(
            disclosure[
                "exp023_transfer_results_viewed_before_lock"
            ]
        )
        self.assertTrue(
            disclosure["cannot_claim_independent_confirmation"]
        )

    def test_04_frozen_evidence_boundary_is_exact(self):
        frozen = get_exp023_preregistration()[
            "frozen_inputs"
        ]
        self.assertEqual(
            frozen["exp022_closure_commit"],
            EXP022_CLOSURE_COMMIT,
        )
        self.assertEqual(
            frozen["exp022_closure_record_sha256"],
            EXPECTED_EXP022_CLOSURE_SHA256,
        )
        self.assertEqual(
            frozen["exp014_freeze_commit"],
            EXP014_FREEZE_COMMIT,
        )
        self.assertEqual(
            frozen["session_quality_sha256"],
            EXPECTED_SESSION_QUALITY_SHA256,
        )
        self.assertEqual(
            frozen["exp014_reference_session_count"],
            1_331,
        )
        self.assertTrue(
            frozen["exp022_outputs_read_only"]
        )

    def test_05_representation_roles_are_selected_in_advance(self):
        series = get_exp023_preregistration()[
            "frozen_inputs"
        ]["series"]
        self.assertEqual(
            tuple(
                item["representation_id"]
                for item in series
            ),
            (
                "BACKWARD_ADJUSTED",
                "UNADJUSTED",
            ),
        )
        self.assertEqual(
            series[0]["role"],
            "PRIMARY_TRANSFER_SERIES",
        )
        self.assertEqual(
            series[1]["role"],
            "SECONDARY_ROLL_SENSITIVITY_SERIES",
        )
        self.assertEqual(
            series[0]["size_bytes"],
            71_964_074,
        )
        self.assertEqual(
            series[1]["size_bytes"],
            73_760_121,
        )

    def test_06_three_frozen_finalists_are_exact(self):
        record = get_exp023_preregistration()
        finalists = record["frozen_finalists"]
        self.assertEqual(
            tuple(
                item["candidate_id"]
                for item in finalists
            ),
            FINALIST_IDS,
        )
        self.assertEqual(
            tuple(
                item["reference_trade_count"]
                for item in finalists
            ),
            (186, 291, 88),
        )
        self.assertEqual(
            len(
                {
                    item[
                        "reference_ledger_canonical_sha256"
                    ]
                    for item in finalists
                }
            ),
            3,
        )

    def test_07_rules_costs_and_execution_are_locked(self):
        rules = get_exp023_preregistration()[
            "strategy_lock"
        ]
        self.assertEqual(
            rules["candidate_ids"],
            FINALIST_IDS,
        )
        self.assertEqual(
            rules["entry_time_new_york"],
            "09:35",
        )
        self.assertEqual(
            rules["forced_flat_time_new_york"],
            "15:55",
        )
        self.assertEqual(
            rules["same_minute_stop_and_target_rule"],
            "STOP_FIRST_CONSERVATIVE",
        )
        self.assertEqual(
            rules["position_size"],
            "FIXED_ONE_NQ_CONTRACT",
        )
        self.assertEqual(
            rules["round_trip_cost_usd"],
            15.0,
        )
        self.assertTrue(
            rules["rule_or_parameter_changes_prohibited"]
        )

    def test_08_only_known_overlap_may_be_read(self):
        access = get_exp023_preregistration()[
            "data_access_boundary"
        ]
        self.assertEqual(
            access["allowed_session_date_start"],
            "2020-01-03",
        )
        self.assertEqual(
            access["allowed_session_date_end"],
            "2025-12-31",
        )
        self.assertTrue(
            access[
                "out_of_window_ohlcv_deserialization_prohibited"
            ]
        )
        self.assertTrue(
            access[
                "out_of_window_strategy_calculation_prohibited"
            ]
        )
        self.assertEqual(
            access["preserved_for_later_experiments"],
            (
                "2010-06-06 through 2019-12-31",
                "2026-01-01 through 2026-07-23",
            ),
        )

    def test_09_missing_bars_cannot_be_filled(self):
        rules = get_exp023_preregistration()[
            "bar_and_session_normalization"
        ]
        self.assertFalse(
            rules["missing_source_minutes_filled"]
        )
        self.assertFalse(
            rules["synthetic_bars_created"]
        )
        self.assertFalse(
            rules["source_ohlcv_modified"]
        )
        self.assertTrue(
            rules[
                "ineligible_sessions_are_logged_not_repaired"
            ]
        )
        self.assertTrue(
            rules[
                "every_reference_session_must_be_accounted_for"
            ]
        )

    def test_10_transfer_gates_are_exact(self):
        gates = get_exp023_preregistration()[
            "qualification_gates"
        ]
        self.assertEqual(
            gates["reference_session_denominator"],
            1_331,
        )
        self.assertEqual(
            gates["common_trade_key"],
            (
                "session_date",
                "direction",
            ),
        )
        self.assertEqual(
            gates[
                "insufficient_or_zero_variance_correlation_action"
            ],
            "FAIL",
        )
        self.assertEqual(
            gates[
                "minimum_required_session_eligibility_share"
            ],
            0.99,
        )
        self.assertEqual(
            gates[
                "minimum_trade_indicator_and_direction_agreement"
            ],
            0.99,
        )
        self.assertEqual(
            gates["maximum_trade_count_relative_difference"],
            0.01,
        )
        self.assertEqual(
            gates["minimum_common_trade_match_share"],
            0.98,
        )
        self.assertEqual(
            gates[
                "minimum_matching_entry_timestamp_agreement"
            ],
            1.0,
        )
        self.assertEqual(
            gates[
                "minimum_common_trade_gross_pnl_correlation"
            ],
            0.98,
        )
        self.assertEqual(
            gates[
                "minimum_common_trade_gross_pnl_sign_agreement"
            ],
            0.95,
        )
        self.assertIsNone(
            gates["profit_factor_threshold"]
        )

    def test_11_profitability_is_not_a_transfer_gate(self):
        comparison = get_exp023_preregistration()[
            "comparison_plan"
        ]
        self.assertTrue(
            comparison[
                "reference_results_are_known_not_holdout_evidence"
            ]
        )
        self.assertTrue(
            comparison[
                "profitability_is_measured_but_not_a_transfer_gate"
            ]
        )
        self.assertTrue(
            comparison["no_strategy_ranking_or_winner_selection"]
        )

    def test_12_separate_implementation_and_authorization_required(
        self,
    ):
        boundary = get_exp023_preregistration()[
            "execution_boundary"
        ]
        self.assertTrue(
            boundary["separate_implementation_commit_required"]
        )
        self.assertTrue(
            boundary[
                "separate_execution_authorization_required"
            ]
        )
        self.assertTrue(
            boundary["protected_preflight_required"]
        )
        self.assertTrue(
            boundary["one_authorized_transfer_run"]
        )
        self.assertFalse(
            boundary[
                "strategy_results_calculated_by_preregistration"
            ]
        )
        self.assertFalse(
            boundary[
                "out_of_overlap_values_accessed_by_preregistration"
            ]
        )

    def test_13_no_search_or_trading_permission(self):
        prohibited = get_exp023_preregistration()[
            "prohibited_actions"
        ]
        for key in (
            "read_out_of_overlap_ohlcv_values",
            "calculate_out_of_overlap_strategy_results",
            "strategy_optimization",
            "mcpt",
            "bootstrap",
            "walk_forward",
            "strategy_ranking",
            "paper_trading",
            "live_trading",
        ):
            with self.subTest(key=key):
                self.assertTrue(
                    prohibited[key]
                )

    def test_14_twenty_hard_checks_are_locked(self):
        record = get_exp023_preregistration()
        self.assertEqual(
            record["hard_check_count"],
            20,
        )
        self.assertEqual(
            len(record["hard_checks"]),
            20,
        )
        self.assertEqual(
            len(set(record["hard_checks"])),
            20,
        )

    def test_15_mutation_is_rejected(self):
        record = get_exp023_preregistration()
        record["qualification_gates"][
            "minimum_trade_indicator_and_direction_agreement"
        ] = 0.95
        with self.assertRaisesRegex(
            ValueError,
            "qualification gates changed|"
            "preregistration record changed",
        ):
            validate_exp023_preregistration(
                record
            )


if __name__ == "__main__":
    unittest.main()
