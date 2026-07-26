from __future__ import annotations

import unittest

from exp024_preregistration import (
    ATTRIBUTION_CATEGORIES,
    CANDIDATE_IDS,
    EXPECTED_EXP022_CLOSURE_SHA256,
    EXPECTED_EXP023_CLOSURE_SHA256,
    EXP022_CLOSURE_COMMIT,
    EXP023_CLOSURE_COMMIT,
    get_exp024_preregistration,
    validate_exp024_preregistration,
)


class Exp024PreregistrationTests(unittest.TestCase):
    def test_01_preregistration_is_valid(self) -> None:
        validate_exp024_preregistration()

    def test_02_identity_is_result_free(self) -> None:
        record = get_exp024_preregistration()
        self.assertEqual(record["experiment_id"], "EXP-024")
        self.assertEqual(record["research_status"], "PRE_REGISTERED")
        self.assertEqual(
            record["implementation_status"],
            "NOT_IMPLEMENTED",
        )
        self.assertEqual(record["execution_status"], "NOT_RUN")

    def test_03_prior_result_disclosure_is_honest(self) -> None:
        disclosure = get_exp024_preregistration()[
            "prior_result_disclosure"
        ]
        self.assertTrue(disclosure["exp023_results_viewed_before_lock"])
        self.assertTrue(
            disclosure["some_exp023_mismatch_dates_viewed_before_lock"]
        )
        self.assertTrue(
            disclosure["some_transfer_context_values_viewed_before_lock"]
        )
        self.assertFalse(
            disclosure[
                "complete_cross_source_feature_attribution_viewed_before_lock"
            ]
        )
        self.assertFalse(
            disclosure["exp024_results_viewed_before_lock"]
        )
        self.assertTrue(disclosure["cannot_claim_blind_attribution"])

    def test_04_exp022_and_exp023_are_hash_locked(self) -> None:
        frozen = get_exp024_preregistration()["frozen_inputs"]
        self.assertEqual(
            frozen["exp023_closure_commit"],
            EXP023_CLOSURE_COMMIT,
        )
        self.assertEqual(
            frozen["exp023_closure_record_sha256"],
            EXPECTED_EXP023_CLOSURE_SHA256,
        )
        self.assertEqual(
            frozen["exp022_closure_commit"],
            EXP022_CLOSURE_COMMIT,
        )
        self.assertEqual(
            frozen["exp022_closure_record_sha256"],
            EXPECTED_EXP022_CLOSURE_SHA256,
        )
        self.assertTrue(frozen["all_inputs_read_only"])
        self.assertEqual(frozen["databento_api_calls"], 0)

    def test_05_exp023_input_files_are_exact(self) -> None:
        outputs = get_exp024_preregistration()["frozen_inputs"][
            "exp023_outputs"
        ]
        self.assertEqual(len(outputs), 6)
        self.assertEqual(
            tuple(item["role"] for item in outputs),
            (
                "MISMATCH_POPULATION",
                "TRANSFER_FEATURE_REFERENCE",
                "LOCKED_METRICS",
                "LOCKED_SUMMARY",
                "OUTPUT_MANIFEST",
                "COMPLETION_MARKER",
            ),
        )
        self.assertEqual(
            outputs[0]["sha256"],
            (
                "715ada134530a9c71238025afd0275fba"
                "3af31931ba8e56c08e89c18b9779d89"
            ),
        )

    def test_06_primary_mismatch_population_is_exact(self) -> None:
        population = get_exp024_preregistration()[
            "mismatch_population"
        ]
        self.assertEqual(population["candidate_ids"], CANDIDATE_IDS)
        self.assertEqual(population["candidate_session_row_count"], 51)
        self.assertEqual(population["unique_session_count"], 51)
        counts = population["candidate_counts"]
        self.assertEqual(
            tuple(item["mismatch_rows"] for item in counts),
            (48, 2, 1),
        )
        self.assertEqual(
            tuple(item["reference_only_trades"] for item in counts),
            (2, 2, 1),
        )
        self.assertEqual(
            tuple(item["transfer_only_trades"] for item in counts),
            (46, 0, 0),
        )
        self.assertTrue(population["all_51_rows_must_be_retained"])
        self.assertTrue(population["no_matched_control_sessions"])

    def test_07_data_access_stops_at_entry(self) -> None:
        access = get_exp024_preregistration()[
            "data_access_boundary"
        ]
        self.assertEqual(
            access["allowed_current_premarket_window_new_york"],
            "08:00:00 through 09:29:59",
        )
        self.assertEqual(
            access["allowed_current_first_cash_bar_new_york"],
            "09:30:00 through 09:34:59",
        )
        self.assertIn("09:35:00 open price only", access["allowed_entry_field"])
        self.assertTrue(
            access["current_post_entry_ohlcv_access_prohibited"]
        )
        self.assertTrue(
            access["out_of_overlap_ohlcv_access_prohibited"]
        )
        self.assertTrue(
            access[
                "databento_parquet_filter_before_materialization_required"
            ]
        )
        self.assertTrue(
            access["column_projection_before_materialization_required"]
        )

    def test_08_only_entry_decision_features_are_permitted(self) -> None:
        features = get_exp024_preregistration()[
            "feature_reconstruction"
        ]
        self.assertTrue(
            features["quantower_one_to_five_minute_rebuild_required"]
        )
        self.assertTrue(
            features[
                "quantower_rebuild_must_match_frozen_five_minute_rows"
            ]
        )
        self.assertFalse(features["missing_minutes_filled"])
        self.assertFalse(features["synthetic_bars_created"])
        self.assertTrue(features["no_stop_target_or_exit_evaluation"])
        self.assertTrue(features["no_trade_pnl_or_equity_calculation"])

    def test_09_thresholds_cannot_change(self) -> None:
        features = get_exp024_preregistration()[
            "feature_reconstruction"
        ]
        self.assertEqual(
            features["thresholds"],
            {
                "gap_fade_0p50_1r": 0.50,
                "premarket_continuation_0p50_time": 0.50,
                "premarket_continuation_0p75_time": 0.75,
            },
        )
        self.assertEqual(features["threshold_operator"], ">=")
        self.assertTrue(features["candidate_rules_must_not_change"])

    def test_10_attribution_categories_are_fixed(self) -> None:
        attribution = get_exp024_preregistration()[
            "attribution_rule"
        ]
        self.assertEqual(
            attribution["categories"],
            ATTRIBUTION_CATEGORIES,
        )
        self.assertEqual(len(ATTRIBUTION_CATEGORIES), 7)
        self.assertTrue(
            attribution[
                "exactly_one_primary_category_per_candidate_session"
            ]
        )
        self.assertTrue(attribution["manual_relabeling_prohibited"])
        self.assertTrue(attribution["statistical_model_prohibited"])

    def test_11_roll_context_cannot_be_called_causal(self) -> None:
        comparison = get_exp024_preregistration()[
            "raw_feature_comparison"
        ]
        self.assertTrue(comparison["roll_context_is_descriptive_not_causal"])
        self.assertTrue(
            comparison[
                "quantower_contract_identity_unavailable_is_reported"
            ]
        )
        self.assertFalse(comparison["volume_comparison"])

    def test_12_classification_cannot_select_or_validate(self) -> None:
        classification = get_exp024_preregistration()[
            "classification"
        ]
        for key in (
            "no_classification_qualifies_a_vendor_as_best",
            "no_classification_validates_strategy_edge",
            "no_classification_authorizes_protected_history",
            "no_classification_authorizes_paper_or_live_trading",
        ):
            with self.subTest(key=key):
                self.assertTrue(classification[key])

    def test_13_separate_implementation_and_authorization_required(
        self,
    ) -> None:
        boundary = get_exp024_preregistration()[
            "execution_boundary"
        ]
        self.assertTrue(
            boundary["separate_implementation_commit_required"]
        )
        self.assertTrue(
            boundary["separate_execution_authorization_required"]
        )
        self.assertTrue(boundary["protected_preflight_required"])
        self.assertTrue(boundary["one_authorized_attribution_run"])
        self.assertFalse(
            boundary[
                "source_feature_attribution_calculated_by_preregistration"
            ]
        )

    def test_14_no_performance_search_or_trading_permission(
        self,
    ) -> None:
        prohibited = get_exp024_preregistration()[
            "prohibited_actions"
        ]
        for key in (
            "rerun_exp023",
            "read_out_of_overlap_ohlcv_values",
            "read_non_mismatch_session_ohlcv_values",
            "read_current_post_entry_ohlcv_values",
            "calculate_trade_exits",
            "calculate_profit_or_loss",
            "calculate_equity_or_drawdown",
            "change_strategy_rule_or_threshold",
            "add_remove_or_rank_candidate",
            "select_best_source_or_vendor",
            "databento_api_request",
            "strategy_optimization",
            "mcpt",
            "bootstrap",
            "walk_forward",
            "protected_history_validation",
            "paper_trading",
            "live_trading",
        ):
            with self.subTest(key=key):
                self.assertTrue(prohibited[key])

    def test_15_twenty_six_hard_checks_are_locked(self) -> None:
        record = get_exp024_preregistration()
        self.assertEqual(record["hard_check_count"], 26)
        self.assertEqual(len(record["hard_checks"]), 26)
        self.assertEqual(len(set(record["hard_checks"])), 26)

    def test_16_mutation_is_rejected(self) -> None:
        record = get_exp024_preregistration()
        record["mismatch_population"]["candidate_session_row_count"] = 50
        with self.assertRaisesRegex(
            ValueError,
            "mismatch population changed|preregistration record changed",
        ):
            validate_exp024_preregistration(record)


if __name__ == "__main__":
    unittest.main()
