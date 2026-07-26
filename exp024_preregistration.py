from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any


EXP023_CLOSURE_COMMIT = (
    "d9843656d764c3146c87220489a762a6e89eb37c"
)
EXPECTED_EXP023_CLOSURE_SHA256 = (
    "e3addce87c97b3cbaf1b5bddee0c9be2"
    "be0c75fedb45d3267ae293556e2f2c11"
)
EXP022_CLOSURE_COMMIT = (
    "9d157c8e7a6ba584a96cb5d37086672ad5b64ea1"
)
EXPECTED_EXP022_CLOSURE_SHA256 = (
    "1cc01baddeeae3acf81b0785923b581fa"
    "d6aac0b6e36071d07d0d83d35bf588d"
)

CANDIDATE_IDS = (
    "gap_fade_0p50_1r",
    "premarket_continuation_0p50_time",
    "premarket_continuation_0p75_time",
)

ATTRIBUTION_CATEGORIES = (
    "ELIGIBILITY_DIFFERENCE",
    "NORMALIZED_CONTEXT_THRESHOLD_CROSSING",
    "CONTEXT_DIRECTION_DIFFERENCE",
    "FIRST_CASH_BAR_CONFIRMATION_DIFFERENCE",
    "ENTRY_RISK_VALIDITY_DIFFERENCE",
    "MULTIPLE_DECISION_COMPONENT_DIFFERENCES",
    "UNRESOLVED_WITH_LOCKED_FEATURES",
)

EXP024_PREREGISTRATION: dict[str, Any] = {
    "schema_version": 1,
    "experiment_id": "EXP-024",
    "title": (
        "NQ Cross-Source Signal-Disagreement Attribution"
    ),
    "locked_date": "2026-07-26",
    "research_status": "PRE_REGISTERED",
    "implementation_status": "NOT_IMPLEMENTED",
    "execution_status": "NOT_RUN",
    "purpose": (
        "Attribute the 51 frozen primary candidate-session decision "
        "mismatches from EXP-023 to prespecified entry-decision components "
        "using only the already-known 2020-2025 overlap."
    ),
    "research_question": (
        "Which eligibility, normalized-context, direction-confirmation or "
        "entry-risk component differs between the frozen Quantower reference "
        "and the frozen Databento-derived series on each EXP-023 mismatch?"
    ),
    "prior_result_disclosure": {
        "exp018_results_viewed_before_lock": True,
        "exp019_results_viewed_before_lock": True,
        "exp020_results_viewed_before_lock": True,
        "exp021_results_viewed_before_lock": True,
        "exp022_results_viewed_before_lock": True,
        "exp023_results_viewed_before_lock": True,
        "some_exp023_mismatch_dates_viewed_before_lock": True,
        "some_transfer_context_values_viewed_before_lock": True,
        "complete_cross_source_feature_attribution_viewed_before_lock": (
            False
        ),
        "exp024_results_viewed_before_lock": False,
        "cannot_claim_blind_attribution": True,
        "cannot_claim_independent_edge_confirmation": True,
        "known_source_context": {
            "quantower_provider": "Lucid/Rithmic via Quantower",
            "quantower_series": "provider-managed front month",
            "quantower_roll_trigger": "NOT_EXPOSED",
            "quantower_adjustment_method": "UNKNOWN_PROVIDER_DEFINED",
            "databento_dataset": "GLBX.MDP3",
            "databento_source": "exact quarterly NQ contracts",
            "databento_selected_roll_method": "VOL_GT_OUT_2S_E3",
            "databento_volume_driven_transitions": 40,
            "databento_calendar_fallbacks": 25,
            "databento_warning_calendar_fallbacks": 23,
        },
        "known_exp023_result": {
            "classification": (
                "TRANSFER_DIAGNOSTIC_COMPLETE_WITH_MATERIAL_DIFFERENCES"
            ),
            "hard_checks": 20,
            "hard_failure_count": 0,
            "primary_representation": "BACKWARD_ADJUSTED",
            "primary_candidate_gate_outcomes": (
                {
                    "candidate_id": "gap_fade_0p50_1r",
                    "all_transfer_gates_pass": False,
                    "reference_trade_count": 186,
                    "transfer_trade_count": 230,
                    "common_trade_count": 184,
                },
                {
                    "candidate_id": (
                        "premarket_continuation_0p50_time"
                    ),
                    "all_transfer_gates_pass": True,
                    "reference_trade_count": 291,
                    "transfer_trade_count": 289,
                    "common_trade_count": 289,
                },
                {
                    "candidate_id": (
                        "premarket_continuation_0p75_time"
                    ),
                    "all_transfer_gates_pass": False,
                    "reference_trade_count": 88,
                    "transfer_trade_count": 87,
                    "common_trade_count": 87,
                },
            ),
        },
    },
    "objective": {
        "cross_source_entry_decision_attribution": True,
        "known_overlap_only": True,
        "frozen_mismatch_rows_only": True,
        "entry_decision_features_only": True,
        "roll_context_measurement": True,
        "data_quality_winner_selection": False,
        "generic_vendor_qualification": False,
        "strategy_replay": False,
        "exit_simulation": False,
        "profitability_measurement": False,
        "candidate_selection": False,
        "parameter_search": False,
        "threshold_change": False,
        "optimization": False,
        "mcpt": False,
        "bootstrap": False,
        "walk_forward": False,
        "protected_history_validation": False,
        "paper_or_live_trading": False,
    },
    "frozen_inputs": {
        "exp023_closure_commit": EXP023_CLOSURE_COMMIT,
        "exp023_closure_record_sha256": (
            EXPECTED_EXP023_CLOSURE_SHA256
        ),
        "exp023_classification": (
            "TRANSFER_DIAGNOSTIC_COMPLETE_WITH_MATERIAL_DIFFERENCES"
        ),
        "exp023_outputs": (
            {
                "role": "MISMATCH_POPULATION",
                "path": (
                    "results/EXP-023/transfer_qualification/"
                    "trade_alignment.csv"
                ),
                "size_bytes": 981_790,
                "sha256": (
                    "715ada134530a9c71238025afd0275fba"
                    "3af31931ba8e56c08e89c18b9779d89"
                ),
            },
            {
                "role": "TRANSFER_FEATURE_REFERENCE",
                "path": (
                    "results/EXP-023/transfer_qualification/"
                    "session_alignment.csv"
                ),
                "size_bytes": 1_001_712,
                "sha256": (
                    "c0a81009b7af49a9714553d54b9045a3"
                    "df60c3a32a876052c9a5987db8f40774"
                ),
            },
            {
                "role": "LOCKED_METRICS",
                "path": (
                    "results/EXP-023/transfer_qualification/"
                    "candidate_transfer_metrics.csv"
                ),
                "size_bytes": 2_103,
                "sha256": (
                    "24e9d5f53faaafee4a09762f8525c089"
                    "750ec38874bea3fdfff5affcaf9b97fb"
                ),
            },
            {
                "role": "LOCKED_SUMMARY",
                "path": (
                    "results/EXP-023/transfer_qualification/"
                    "transfer_summary.json"
                ),
                "size_bytes": 10_551,
                "sha256": (
                    "8980bbac1f85ff1afc965430d5cae047"
                    "901681bb0279109f8f251a4b8ee0fac4"
                ),
            },
            {
                "role": "OUTPUT_MANIFEST",
                "path": (
                    "results/EXP-023/transfer_qualification/"
                    "output_hashes.json"
                ),
                "size_bytes": 2_773,
                "sha256": (
                    "05731ab19c85eff57750dc126da9b2227"
                    "937094b8bbb1d7da31c38847392194b"
                ),
            },
            {
                "role": "COMPLETION_MARKER",
                "path": (
                    "results/EXP-023/transfer_qualification/"
                    "TRANSFER_DIAGNOSTIC_COMPLETE.json"
                ),
                "size_bytes": 363,
                "sha256": (
                    "aac79a622ee09618d304a0c7b5cf41d6"
                    "f810c1fcf7ffb58b63f16fc2cf78e150"
                ),
            },
        ),
        "exp022_closure_commit": EXP022_CLOSURE_COMMIT,
        "exp022_closure_record_sha256": (
            EXPECTED_EXP022_CLOSURE_SHA256
        ),
        "databento_series": (
            {
                "representation_id": "BACKWARD_ADJUSTED",
                "role": "PRIMARY_ATTRIBUTION_SERIES",
                "path": (
                    "results/EXP-022/selected_continuous_series/"
                    "selected_roll_backward_adjusted.parquet"
                ),
                "rows": 5_457_606,
                "size_bytes": 71_964_074,
                "sha256": (
                    "61ccb3621b53fa313147a866948ec1f2c"
                    "7a6b36956d2ba26090162b518c30c84"
                ),
                "semantic_sha256": (
                    "3c6fa83821183ca54bc547c555834ceb1"
                    "6a126be50f90d8c6db5684220929951"
                ),
            },
            {
                "representation_id": "UNADJUSTED",
                "role": "SECONDARY_ADJUSTMENT_SENSITIVITY",
                "path": (
                    "results/EXP-022/selected_continuous_series/"
                    "selected_roll_unadjusted.parquet"
                ),
                "rows": 5_457_606,
                "size_bytes": 73_760_121,
                "sha256": (
                    "606a69bbba4f4a5db3e0356d7b2849f9"
                    "481e4555dc24cae4c6b9d1d12f673ab1"
                ),
                "semantic_sha256": (
                    "29daf3f20b022fb69967349095eb9663b"
                    "d04276cbc5743a65b1ecabc33113640"
                ),
            },
        ),
        "roll_ledger": {
            "path": (
                "results/EXP-022/selected_continuous_series/"
                "roll_ledger.csv"
            ),
            "size_bytes": 15_343,
            "sha256": (
                "74dbd346f27ea980e3d66e81acf99c6"
                "e08df80ca573100a7618f52b131d151aa"
            ),
            "semantic_sha256": (
                "c800004230ae0db630a4414db81d1c030"
                "c02976ec06c47731ba4384265069090"
            ),
        },
        "quantower_reference": {
            "source": "Lucid/Rithmic via Quantower History Exporter",
            "series": "provider-managed front-month NQ",
            "roll_trigger": "NOT_EXPOSED",
            "adjustment_method": "UNKNOWN_PROVIDER_DEFINED",
            "nq_one_minute_path": (
                "data/extended_session/processed/"
                "NQ_1m_extended.parquet"
            ),
            "nq_one_minute_rows": 1_849_560,
            "nq_one_minute_size_bytes": 32_064_933,
            "nq_one_minute_sha256": (
                "b1679f833d03c2f2aedeaf4ec442a34a"
                "284edd307942e13918a0488c71a669cc"
            ),
            "nq_five_minute_path": (
                "data/extended_session/processed/"
                "NQ_5m_extended.parquet"
            ),
            "nq_five_minute_rows": 369_912,
            "nq_five_minute_size_bytes": 7_380_444,
            "nq_five_minute_sha256": (
                "06598e2dd4cf2b89cd6777fb85881db7f"
                "eb00faa0a5b4cda435e664a4c3c660a"
            ),
            "session_quality_path": (
                "results/extended_session_data/session_quality.csv"
            ),
            "session_quality_size_bytes": 78_768,
            "session_quality_sha256": (
                "6b55077783ad2c1cd8ef99f10d50ed7d"
                "691aad7cafcdb7e8fa37639d90724712"
            ),
            "extended_session_implementation_commit": (
                "73dc3650ad5d3ebffd817fe5b2851729b03fe7d4"
            ),
        },
        "exp019_archive_sha256": (
            "225a64dc06cb6bb303fd83d186f2e7d8"
            "1e2a8a8bec44382380c8ccc1b0b6baa3"
        ),
        "all_inputs_read_only": True,
        "databento_api_calls": 0,
        "credentials_required": False,
    },
    "mismatch_population": {
        "representation_id": "BACKWARD_ADJUSTED",
        "selector": (
            "Rows in frozen trade_alignment.csv where representation_id "
            "equals BACKWARD_ADJUSTED and "
            "trade_indicator_and_direction_match equals False."
        ),
        "candidate_ids": CANDIDATE_IDS,
        "candidate_session_row_count": 51,
        "unique_session_count": 51,
        "candidate_counts": (
            {
                "candidate_id": "gap_fade_0p50_1r",
                "mismatch_rows": 48,
                "eligible_mismatch_rows": 47,
                "ineligible_mismatch_rows": 1,
                "reference_only_trades": 2,
                "transfer_only_trades": 46,
                "direction_mismatches": 0,
            },
            {
                "candidate_id": (
                    "premarket_continuation_0p50_time"
                ),
                "mismatch_rows": 2,
                "eligible_mismatch_rows": 2,
                "ineligible_mismatch_rows": 0,
                "reference_only_trades": 2,
                "transfer_only_trades": 0,
                "direction_mismatches": 0,
            },
            {
                "candidate_id": (
                    "premarket_continuation_0p75_time"
                ),
                "mismatch_rows": 1,
                "eligible_mismatch_rows": 1,
                "ineligible_mismatch_rows": 0,
                "reference_only_trades": 1,
                "transfer_only_trades": 0,
                "direction_mismatches": 0,
            },
        ),
        "all_51_rows_must_be_retained": True,
        "row_addition_or_removal_prohibited": True,
        "unadjusted_role": (
            "Secondary feature-level adjustment sensitivity on the same "
            "51 candidate-session rows only."
        ),
        "no_matched_control_sessions": True,
    },
    "data_access_boundary": {
        "allowed_session_date_start": "2020-01-03",
        "allowed_session_date_end": "2025-12-31",
        "allowed_candidate_sessions": (
            "Only the 51 primary mismatch sessions selected from the "
            "frozen EXP-023 alignment."
        ),
        "allowed_previous_sessions": (
            "Only the immediately prior frozen reference cash session for "
            "gap_fade mismatch rows."
        ),
        "allowed_current_premarket_window_new_york": (
            "08:00:00 through 09:29:59"
        ),
        "allowed_current_first_cash_bar_new_york": (
            "09:30:00 through 09:34:59"
        ),
        "allowed_entry_field": (
            "09:35:00 open price only, for locked positive-risk validation"
        ),
        "allowed_previous_cash_window_new_york": (
            "09:30:00 through 15:59:59"
        ),
        "current_post_entry_ohlcv_access_prohibited": True,
        "out_of_overlap_ohlcv_access_prohibited": True,
        "databento_parquet_filter_before_materialization_required": True,
        "column_projection_before_materialization_required": True,
        "full_file_byte_hash_verification_permitted": True,
        "parquet_metadata_inspection_permitted": True,
        "no_new_market_data_download": True,
        "no_network_access": True,
        "preserved_for_later_experiments": (
            "2010-06-06 through 2019-12-31",
            "2026-01-01 through 2026-07-23",
        ),
    },
    "feature_reconstruction": {
        "research_timezone": "America/New_York",
        "source_resolution": "1 minute",
        "signal_resolution": "5 minutes",
        "five_minute_bars_use_observed_minutes_only": True,
        "missing_minutes_filled": False,
        "synthetic_bars_created": False,
        "quantower_one_to_five_minute_rebuild_required": True,
        "quantower_rebuild_must_match_frozen_five_minute_rows": True,
        "common_components": (
            "session_eligibility",
            "first_cash_bar_open",
            "first_cash_bar_close",
            "first_cash_bar_direction",
            "entry_0935_open",
            "entry_risk_points",
            "entry_risk_positive",
            "setup_passes",
        ),
        "gap_fade_components": (
            "previous_cash_close",
            "previous_cash_high",
            "previous_cash_low",
            "previous_cash_range",
            "current_cash_open",
            "gap_move",
            "gap_direction",
            "normalized_gap",
            "threshold_margin",
            "threshold_passes",
            "fade_direction",
            "first_cash_bar_confirmation",
        ),
        "premarket_components": (
            "premarket_open",
            "premarket_last_close",
            "premarket_high",
            "premarket_low",
            "premarket_range",
            "premarket_move",
            "premarket_direction",
            "normalized_premarket_move",
            "threshold_margin",
            "threshold_passes",
            "continuation_direction",
            "first_cash_bar_confirmation",
        ),
        "thresholds": {
            "gap_fade_0p50_1r": 0.50,
            "premarket_continuation_0p50_time": 0.50,
            "premarket_continuation_0p75_time": 0.75,
        },
        "threshold_operator": ">=",
        "candidate_rules_must_not_change": True,
        "no_stop_target_or_exit_evaluation": True,
        "no_trade_pnl_or_equity_calculation": True,
    },
    "raw_feature_comparison": {
        "price_difference_unit": "NQ ticks",
        "nq_tick_size_points": 0.25,
        "compare_only_strategy_input_fields": True,
        "volume_comparison": False,
        "compare_backward_adjusted_to_quantower": True,
        "compare_unadjusted_to_quantower": True,
        "compare_backward_adjusted_to_unadjusted": True,
        "source_contract_and_instrument_id_reported": True,
        "distance_to_selected_roll_session_reported": True,
        "roll_distance_bands_sessions": (0, 1, 3, "OTHER"),
        "calendar_fallback_status_reported": True,
        "provider_warning_context_reported": True,
        "roll_context_is_descriptive_not_causal": True,
        "quantower_contract_identity_unavailable_is_reported": True,
    },
    "attribution_rule": {
        "candidate_decision_vectors_rebuilt_for_both_sources": True,
        "reference_rebuild_must_match_frozen_reference_decision": True,
        "transfer_rebuild_must_match_frozen_transfer_decision": True,
        "differing_decision_components_are_recorded_as_a_set": True,
        "single_component_maps_to_its_exact_category": True,
        "multiple_components_map_to": (
            "MULTIPLE_DECISION_COMPONENT_DIFFERENCES"
        ),
        "zero_differing_components_with_decision_mismatch_maps_to": (
            "UNRESOLVED_WITH_LOCKED_FEATURES"
        ),
        "categories": ATTRIBUTION_CATEGORIES,
        "exactly_one_primary_category_per_candidate_session": True,
        "manual_relabeling_prohibited": True,
        "statistical_model_prohibited": True,
        "source_quality_winner_selection_prohibited": True,
    },
    "descriptive_metrics": (
        "mismatch_count_by_candidate",
        "mismatch_count_by_attribution_category",
        "single_vs_multiple_component_count",
        "unresolved_count",
        "eligibility_difference_count",
        "threshold_crossing_count",
        "direction_difference_count",
        "confirmation_difference_count",
        "risk_validity_difference_count",
        "component_price_difference_ticks",
        "threshold_margin_by_source",
        "roll_distance_band_count",
        "calendar_fallback_context_count",
        "provider_warning_context_count",
        "backward_adjusted_vs_unadjusted_component_agreement",
    ),
    "classification": {
        "complete_identified": (
            "ATTRIBUTION_COMPLETE_WITH_IDENTIFIED_COMPONENTS"
        ),
        "complete_with_unresolved": (
            "ATTRIBUTION_COMPLETE_WITH_UNRESOLVED_CASES"
        ),
        "hard_failure": "ATTRIBUTION_DIAGNOSTIC_NOT_QUALIFIED",
        "complete_identified_rule": (
            "All hard checks pass and unresolved_count equals zero."
        ),
        "complete_with_unresolved_rule": (
            "All hard checks pass and unresolved_count is greater than zero."
        ),
        "hard_failure_rule": "One or more hard checks fail.",
        "no_classification_qualifies_a_vendor_as_best": True,
        "no_classification_validates_strategy_edge": True,
        "no_classification_authorizes_protected_history": True,
        "no_classification_authorizes_paper_or_live_trading": True,
    },
    "decision_policy_after_result": {
        "reconstruction_hard_failure": (
            "Stop. A new data or engine qualification experiment is "
            "required before strategy validation."
        ),
        "all_cases_attributed_without_structural_failure": (
            "Databento may remain eligible only as a source for a separately "
            "preregistered Databento-native experiment. Quantower equivalence "
            "must not be claimed."
        ),
        "unresolved_cases_remain": (
            "Do not unlock protected history. A new exact-contract benchmark "
            "or separately preregistered diagnostic is required."
        ),
        "automatic_candidate_selection": False,
        "automatic_source_replacement": False,
        "automatic_protected_validation": False,
    },
    "required_outputs": (
        "attribution_summary.json",
        "mismatch_attribution.csv",
        "feature_comparison.csv",
        "raw_component_differences.csv",
        "roll_context.csv",
        "aggregation_check.csv",
        "output_hashes.json",
        "report.md",
        "report.html",
        "ATTRIBUTION_DIAGNOSTIC_COMPLETE.json",
    ),
    "reporting_requirements": {
        "all_51_candidate_session_rows_visible": True,
        "all_three_candidates_remain_separate": True,
        "no_candidate_ranking": True,
        "no_profitability_or_equity_table": True,
        "decision_component_attribution_chart": True,
        "threshold_margin_pair_chart": True,
        "raw_component_tick_difference_chart": True,
        "roll_context_chart": True,
        "unresolved_cases_list_required": True,
        "roll_context_causality_warning_required": True,
        "quantower_roll_identity_limitation_required": True,
        "charts_use_opaque_white_canvas": True,
        "positive_numbers_use_neutral_text": True,
        "adverse_numbers_use_red_text": True,
        "green_reserved_for_status_words": True,
    },
    "hard_checks": (
        "exp023_closure_commit_and_hash_match",
        "exp023_output_byte_hashes_match",
        "exp022_closure_commit_and_hash_match",
        "exp022_series_byte_and_semantic_hashes_match",
        "exp022_roll_ledger_byte_and_semantic_hashes_match",
        "quantower_one_and_five_minute_hashes_match",
        "frozen_session_quality_hash_matches",
        "all_source_and_result_inputs_remain_read_only",
        "primary_mismatch_selector_is_exact",
        "exactly_51_candidate_session_rows_are_retained",
        "candidate_mismatch_counts_match_preregistration",
        "primary_and_secondary_representation_roles_are_fixed",
        "only_mismatch_and_required_previous_sessions_are_deserialized",
        "out_of_overlap_ohlcv_values_are_not_deserialized",
        "current_post_entry_ohlcv_values_are_not_deserialized",
        "parquet_row_filter_and_column_projection_precede_materialization",
        "missing_minutes_are_not_filled_or_repaired",
        "quantower_one_minute_aggregation_matches_frozen_five_minute_rows",
        "reference_decision_rebuild_matches_frozen_alignment",
        "transfer_decision_rebuild_matches_frozen_alignment",
        "attribution_categories_are_exhaustive_and_mutually_exclusive",
        "roll_context_is_not_used_as_automatic_causal_attribution",
        "no_exit_pnl_return_equity_or_performance_metric_is_computed",
        "independent_rebuild_hashes_match",
        "required_outputs_and_hashes_are_complete",
        "no_api_network_search_optimization_or_trading_action_occurs",
    ),
    "hard_check_count": 26,
    "execution_boundary": {
        "separate_implementation_commit_required": True,
        "separate_execution_authorization_required": True,
        "protected_preflight_required": True,
        "one_authorized_attribution_run": True,
        "independent_rebuild_required": True,
        "rerun_after_completion": False,
        "databento_api_calls": 0,
        "credentials_required": False,
        "external_network_access": False,
        "strategy_results_calculated_by_preregistration": False,
        "source_feature_attribution_calculated_by_preregistration": False,
        "out_of_overlap_values_accessed_by_preregistration": False,
    },
    "prohibited_actions": {
        "rerun_exp023": True,
        "modify_exp023_outputs": True,
        "modify_exp022_outputs": True,
        "modify_quantower_outputs": True,
        "read_out_of_overlap_ohlcv_values": True,
        "read_non_mismatch_session_ohlcv_values": True,
        "read_current_post_entry_ohlcv_values": True,
        "calculate_trade_exits": True,
        "calculate_profit_or_loss": True,
        "calculate_equity_or_drawdown": True,
        "change_strategy_rule_or_threshold": True,
        "add_remove_or_rank_candidate": True,
        "select_best_source_or_vendor": True,
        "databento_api_request": True,
        "new_market_data_download": True,
        "strategy_optimization": True,
        "mcpt": True,
        "bootstrap": True,
        "walk_forward": True,
        "protected_history_validation": True,
        "paper_trading": True,
        "live_trading": True,
    },
    "interpretation": {
        "known_overlap_root_cause_diagnostic_only": True,
        "strategy_specific_not_generic_data_qualification": True,
        "not_new_edge_evidence": True,
        "not_independent_confirmation": True,
        "all_three_candidate_rows_remain_separate": True,
        "no_strategy_winner_selected": True,
        "no_source_winner_selected": True,
        "databento_not_automatically_rejected": True,
        "quantower_not_assumed_ground_truth": True,
        "roll_proximity_does_not_prove_causation": True,
        "earlier_and_2026_strategy_evidence_preserved": True,
        "separate_future_experiment_required": True,
        "paper_or_live_trading_authorized": False,
    },
}

EXPECTED_EXP024_PREREGISTRATION_SHA256 = (
    "6bc6b7b493aa5eb4a58699fd8cd2c0af15d6c8cfe5323edf9cb3bba1193e3871"
)


def canonical_record_hash(record: dict[str, Any]) -> str:
    encoded = json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def get_exp024_preregistration() -> dict[str, Any]:
    return deepcopy(EXP024_PREREGISTRATION)


def validate_exp024_preregistration(
    candidate: dict[str, Any] | None = None,
) -> None:
    record = (
        EXP024_PREREGISTRATION
        if candidate is None
        else candidate
    )
    if (
        record["experiment_id"] != "EXP-024"
        or record["locked_date"] != "2026-07-26"
        or record["research_status"] != "PRE_REGISTERED"
        or record["implementation_status"] != "NOT_IMPLEMENTED"
        or record["execution_status"] != "NOT_RUN"
    ):
        raise ValueError("EXP-024 preregistration identity changed.")
    frozen = record["frozen_inputs"]
    if (
        frozen["exp023_closure_commit"]
        != EXP023_CLOSURE_COMMIT
        or frozen["exp023_closure_record_sha256"]
        != EXPECTED_EXP023_CLOSURE_SHA256
        or frozen["exp022_closure_commit"]
        != EXP022_CLOSURE_COMMIT
        or frozen["exp022_closure_record_sha256"]
        != EXPECTED_EXP022_CLOSURE_SHA256
    ):
        raise ValueError("EXP-024 frozen evidence boundary changed.")
    population = record["mismatch_population"]
    if (
        population["candidate_ids"] != CANDIDATE_IDS
        or population["candidate_session_row_count"] != 51
        or population["unique_session_count"] != 51
    ):
        raise ValueError("EXP-024 mismatch population changed.")
    attribution = record["attribution_rule"]
    if (
        attribution["categories"] != ATTRIBUTION_CATEGORIES
        or attribution[
            "exactly_one_primary_category_per_candidate_session"
        ]
        is not True
    ):
        raise ValueError("EXP-024 attribution categories changed.")
    if (
        len(record["hard_checks"])
        != record["hard_check_count"]
    ):
        raise ValueError("EXP-024 hard-check count changed.")
    if (
        canonical_record_hash(record)
        != EXPECTED_EXP024_PREREGISTRATION_SHA256
    ):
        raise ValueError("EXP-024 preregistration record changed.")
