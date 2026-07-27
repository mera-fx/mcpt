from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any


EXP024_CLOSURE_COMMIT = "1b3673af14e6a1b71948928a6e4af1bc1d1e98d2"
EXPECTED_EXP024_CLOSURE_SHA256 = "f11d3dc899d6ffcb1e24be6113715240da7ab7af109b1ab45daac64f5aadf183"
EXPECTED_EXP019_EXACT_CONTRACT_ARCHIVE_SHA256 = "225a64dc06cb6bb303fd83d186f2e7d81e2a8a8bec44382380c8ccc1b0b6baa3"

EXP025_PREREGISTRATION: dict[str, Any] = {'schema_version': 1, 'experiment_id': 'EXP-025', 'title': 'NQ Gap-Fade Exact-Contract Decision-Engine Qualification', 'locked_date': '2026-07-27', 'research_status': 'PRE_REGISTERED', 'implementation_status': 'NOT_IMPLEMENTED', 'execution_status': 'NOT_RUN', 'purpose': 'Determine whether the 43 unresolved EXP-024 gap-fade decision mismatches arise from exact-contract source bars, provider-managed continuous-series semantics, or the decision-engine implementation.', 'research_question': 'When the identical explicit quarterly NQ contract is compared on Quantower/Lucid-Rithmic and the frozen Databento exact-contract archive, do permitted bars, decision components and two independently implemented frozen gap-fade engines agree on all 43 sessions?', 'prior_result_disclosure': {'exp024_results_viewed_before_lock': True, 'known_exp024_classification': 'ATTRIBUTION_DIAGNOSTIC_NOT_QUALIFIED', 'known_candidate_session_rows': 51, 'known_unresolved_rows': 43, 'known_unresolved_candidate': 'gap_fade_0p50_1r', 'known_reference_rebuild_matches': 8, 'known_reference_rebuild_failures': 43, 'known_transfer_rebuild_matches': 51, 'cannot_claim_blind_diagnostic': True, 'cannot_claim_independent_edge_confirmation': True}, 'objective': {'exact_contract_source_comparison': True, 'decision_engine_qualification': True, 'continuous_series_context_comparison': True, 'all_43_unresolved_rows_required': True, 'strategy_replay': False, 'exit_simulation': False, 'profitability_measurement': False, 'candidate_selection': False, 'source_winner_selection': False, 'parameter_search': False, 'optimization': False, 'mcpt': False, 'bootstrap': False, 'walk_forward': False, 'protected_history_validation': False, 'paper_or_live_trading': False}, 'frozen_inputs': {'exp024_closure_commit': '1b3673af14e6a1b71948928a6e4af1bc1d1e98d2', 'exp024_closure_record_sha256': 'f11d3dc899d6ffcb1e24be6113715240da7ab7af109b1ab45daac64f5aadf183', 'exp024_classification': 'ATTRIBUTION_DIAGNOSTIC_NOT_QUALIFIED', 'exp024_outputs': {'mismatch_attribution.csv': {'size_bytes': 6797, 'sha256': '1f762b2cbb2d53c0cd979171a584a42fb3e8742040b2c3bb9494155e7d55dbae'}, 'feature_comparison.csv': {'size_bytes': 38064, 'sha256': 'd10a5ffb4e01ee0b7ab65d65f721ab5beca0a4b9cfac6eca4fdacc82c9bd595c'}, 'roll_context.csv': {'size_bytes': 8791, 'sha256': '35ec1eba30a6eeea59ab369b89a575b0cad44cf23b6b3ca89d494a8ef6428ffc'}, 'attribution_summary.json': {'size_bytes': 5210, 'sha256': '86cf29b0b15488ec534b69adb67529833b1031333c298030862bbcc6301eac3e'}, 'output_hashes.json': {'size_bytes': 1818, 'sha256': '93803c61ef670193556b2c7f1acb43a3cef9d4d6a692ead3afcf22baa1601cad'}, 'ATTRIBUTION_DIAGNOSTIC_COMPLETE.json': {'size_bytes': 841, 'sha256': 'b594f9177bafb3b5081ffdc37708b74c6da9294ec212885d0d3f99530ff63601'}}, 'exp019_exact_contract_archive': {'provider': 'Databento', 'dataset': 'GLBX.MDP3', 'schema': 'ohlcv-1m', 'market': 'Exact quarterly NQ futures contracts', 'contract_count': 66, 'first_date': '2010-06-06', 'end_exclusive': '2026-07-24', 'archive_sha256': '225a64dc06cb6bb303fd83d186f2e7d81e2a8a8bec44382380c8ccc1b0b6baa3', 'qualified_with_known_provider_conditions': True, 'new_databento_download_authorized': False, 'databento_api_calls': 0}, 'all_frozen_inputs_read_only': True}, 'population': {'selector': 'Frozen EXP-024 mismatch rows where candidate_id is gap_fade_0p50_1r, attribution_category is UNRESOLVED_WITH_LOCKED_FEATURES, and the locked reference decision reconstruction failed.', 'candidate_id': 'gap_fade_0p50_1r', 'candidate_session_row_count': 43, 'unique_session_count': 43, 'all_43_rows_must_be_retained': True, 'sampling_prohibited': True, 'row_addition_or_removal_prohibited': True}, 'contract_identity_rule': {'databento_contract': 'Use the exact quarterly contract already recorded for each session by frozen EXP-022/EXP-024 roll context.', 'quantower_contract': 'A later manual Quantower/Lucid-Rithmic export must name and contain the identical outright quarterly NQ contract.', 'same_contract_required_across_sources': True, 'explicit_contract_symbol_required': True, 'outright_quarterly_contracts_only': True, 'continuous_symbols_prohibited_as_exact_contract_evidence': True, 'ambiguous_or_missing_identity_is_hard_failure': True, 'contract_reselection_prohibited': True}, 'quantower_export_boundary': {'exports_present_at_preregistration': False, 'implementation_status': 'NOT_IMPLEMENTED', 'manual_export_authorized_by_preregistration': False, 'separate_result_free_implementation_required': True, 'separate_preflight_required': True, 'separate_execution_authorization_required': True, 'source': 'Lucid/Rithmic via Quantower History Exporter', 'resolution': '1 minute', 'required_fields': ('timestamp', 'open', 'high', 'low', 'close', 'volume', 'explicit_contract_symbol'), 'timezone_must_be_declared': True, 'raw_exports_local_and_gitignored': True, 'raw_export_hash_manifest_required': True, 'order_api_connection_prohibited': True}, 'data_access_boundary': {'research_timezone': 'America/New_York', 'allowed_session_date_start': '2020-01-03', 'allowed_session_date_end': '2025-12-31', 'allowed_candidate_sessions': 'Only the 43 frozen unresolved sessions.', 'allowed_previous_sessions': 'Only the immediately prior frozen cash session needed for each row.', 'allowed_previous_cash_window_new_york': '09:30:00 through 15:59:59', 'allowed_current_window_new_york': '09:30:00 through the 09:35:00 one-minute bar only', 'current_post_0935_ohlcv_access_prohibited': True, 'out_of_population_session_access_prohibited': True, 'out_of_overlap_ohlcv_access_prohibited': True, 'row_filter_before_materialization_required': True, 'column_projection_before_materialization_required': True, 'missing_minutes_filled': False, 'synthetic_bars_created': False, 'new_databento_download': False, 'network_access': False}, 'bar_comparison': {'source_resolution': '1 minute', 'signal_resolution': '5 minutes', 'nq_tick_size_points': 0.25, 'timestamps_must_be_unique': True, 'timestamp_alignment_required': True, 'one_minute_ohlc_compared': True, 'volume_descriptive_only': True, 'ohlc_match_definition': 'Equal timestamps and equal tick-normalized OHLC values with no tolerance beyond canonical NQ tick representation.', 'missing_bar_is_difference': True, 'five_minute_bars_use_observed_minutes_only': True, 'no_bar_repair': True, 'no_forward_fill': True, 'no_backfill': True, 'per_field_difference_ticks_required': True}, 'decision_engine_comparison': {'frozen_rule': 'gap_fade_0p50_1r', 'gap_threshold': 0.5, 'threshold_operator': '>=', 'canonical_engine': 'Existing frozen gap-fade rule path, unchanged.', 'independent_engine': 'Separately coded minimal rebuild that does not call the canonical decision function.', 'both_engines_run_on_quantower_exact_contract_bars': True, 'both_engines_run_on_databento_exact_contract_bars': True, 'same_input_bar_hash_required_for_engine_pair': True, 'candidate_rule_change_prohibited': True, 'no_stop_target_or_exit_evaluation': True, 'no_trade_pnl_return_equity_or_drawdown': True}, 'comparison_to_prior_continuous_decisions': {'frozen_quantower_reference_decision_reported': True, 'frozen_databento_transfer_decision_reported': True, 'exact_contract_decision_reported_for_each_source': True, 'comparison_is_diagnostic_not_ground_truth': True, 'continuous_series_semantics_may_be_supported_not_proven': True, 'quantower_roll_trigger_remains_unknown': True, 'quantower_adjustment_method_remains_unknown': True, 'no_vendor_winner_selected': True}, 'classification': {'complete_equivalent': 'EXACT_CONTRACT_DIAGNOSTIC_COMPLETE_EQUIVALENT', 'complete_source_differences': 'EXACT_CONTRACT_DIAGNOSTIC_COMPLETE_SOURCE_DIFFERENCES', 'complete_engine_differences': 'EXACT_CONTRACT_DIAGNOSTIC_COMPLETE_ENGINE_DIFFERENCES', 'complete_mixed_differences': 'EXACT_CONTRACT_DIAGNOSTIC_COMPLETE_MIXED_DIFFERENCES', 'hard_failure': 'EXACT_CONTRACT_DIAGNOSTIC_NOT_QUALIFIED', 'equivalent_rule': 'All integrity checks pass, both engines agree within each source for all 43 sessions, and exact-contract OHLC plus final decisions agree across sources for all 43 sessions.', 'source_difference_rule': 'Integrity checks pass, both engines agree within each source, and one or more exact-contract OHLC or cross-source decisions differ.', 'engine_difference_rule': 'Evidence and identity checks pass, exact-contract OHLC agree for affected rows, and the engines disagree on identical input hashes.', 'mixed_difference_rule': 'Evidence and identity checks pass and both source-bar and same-input engine differences are present.', 'hard_failure_rule': 'An evidence, identity, access, rebuild, output or no-performance hard check fails.', 'no_classification_proves_vendor_superiority': True, 'no_classification_validates_strategy_edge': True, 'no_classification_unlocks_protected_history': True, 'no_classification_authorizes_paper_or_live_trading': True}, 'hard_checks': ('exp024_closure_commit_and_hash_match', 'exp024_output_byte_hashes_match', 'exp019_exact_contract_archive_hash_matches', 'unresolved_population_selector_is_exact', 'exactly_43_candidate_session_rows_are_retained', 'quantower_export_manifest_is_complete_and_hash_locked', 'explicit_contract_identity_exists_for_every_source_session', 'same_exact_contract_is_used_across_sources', 'only_outright_quarterly_nq_contracts_are_used', 'all_source_and_result_inputs_remain_read_only', 'only_allowed_sessions_windows_and_columns_are_materialized', 'current_post_0935_and_out_of_population_values_are_not_materialized', 'missing_minutes_are_not_filled_or_repaired', 'timestamps_are_unique_and_timezone_normalized', 'all_prices_are_valid_nq_ticks', 'one_minute_and_five_minute_component_tables_are_complete', 'canonical_gap_fade_rule_is_unchanged', 'independent_engine_does_not_call_canonical_decision_function', 'same_input_hash_is_used_for_each_engine_pair', 'all_43_rows_receive_exactly_one_classification', 'continuous_context_is_not_treated_as_ground_truth', 'no_exit_pnl_return_equity_drawdown_or_performance_is_computed', 'independent_rebuild_hashes_match', 'required_outputs_and_hashes_are_complete', 'no_api_network_optimization_or_trading_action_occurs'), 'hard_check_count': 25, 'required_outputs': ('exp025_summary.json', 'session_contract_map.csv', 'one_minute_bar_comparison.csv', 'five_minute_component_comparison.csv', 'decision_engine_comparison.csv', 'source_difference_summary.csv', 'output_hashes.json', 'report.md', 'report.html', 'EXACT_CONTRACT_DIAGNOSTIC_COMPLETE.json', 'assets/exact_contract_bar_match.png', 'assets/decision_comparison.png', 'assets/component_difference_ticks.png', 'assets/prior_vs_exact_decisions.png'), 'reporting_requirements': {'all_43_sessions_visible': True, 'per_session_contract_identity_visible': True, 'one_minute_ohlc_differences_visible': True, 'five_minute_decision_components_visible': True, 'both_engine_decisions_visible': True, 'prior_continuous_decisions_visible': True, 'no_candidate_ranking': True, 'no_profitability_or_equity_table': True, 'charts_use_opaque_white_canvas': True}, 'execution_boundary': {'separate_result_free_implementation_commit_required': True, 'implementation_preflight_required': True, 'separate_execution_authorization_commit_required': True, 'authorized_preflight_required': True, 'one_authorized_diagnostic_run': True, 'independent_rebuild_required': True, 'rerun_after_completion': False, 'databento_api_calls': 0, 'credentials_required': False, 'external_network_access': False, 'results_calculated_by_preregistration': False}, 'prohibited_actions': {'rerun_any_exp024_mode': True, 'modify_exp024_outputs': True, 'modify_exp019_archive': True, 'reselect_contract_or_roll_rule': True, 'use_continuous_symbol_as_exact_contract_evidence': True, 'read_out_of_population_ohlcv_values': True, 'read_current_post_0935_ohlcv_values': True, 'fill_or_repair_missing_bars': True, 'calculate_trade_exits': True, 'calculate_profit_or_loss': True, 'calculate_return_equity_or_drawdown': True, 'change_strategy_rule_or_threshold': True, 'add_remove_or_sample_sessions': True, 'select_best_source_vendor_or_candidate': True, 'databento_api_request': True, 'new_databento_market_data_download': True, 'strategy_optimization': True, 'mcpt': True, 'bootstrap': True, 'walk_forward': True, 'protected_history_validation': True, 'paper_trading': True, 'live_trading': True}, 'interpretation': {'exact_contract_engine_diagnostic_only': True, 'strategy_specific_not_generic_vendor_qualification': True, 'not_new_edge_evidence': True, 'not_independent_edge_confirmation': True, 'no_strategy_winner_selected': True, 'no_source_winner_selected': True, 'quantower_not_assumed_ground_truth': True, 'databento_not_assumed_ground_truth': True, 'continuous_series_semantics_may_be_localized_not_proven': True, 'separate_future_strategy_experiment_required': True, 'paper_or_live_trading_authorized': False}}

EXPECTED_EXP025_PREREGISTRATION_SHA256 = "7534f8ba59a57e79ec98067b3fda3606e5b327a2320c82805cf8001f8c6dd5aa"


def canonical_record_hash(record: dict[str, Any]) -> str:
    encoded = json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def get_exp025_preregistration() -> dict[str, Any]:
    return deepcopy(EXP025_PREREGISTRATION)


def validate_exp025_preregistration(
    candidate: dict[str, Any] | None = None,
) -> None:
    record = (
        EXP025_PREREGISTRATION
        if candidate is None
        else candidate
    )
    if (
        record.get("experiment_id") != "EXP-025"
        or record.get("locked_date") != "2026-07-27"
        or record.get("research_status") != "PRE_REGISTERED"
        or record.get("implementation_status") != "NOT_IMPLEMENTED"
        or record.get("execution_status") != "NOT_RUN"
    ):
        raise ValueError("EXP-025 preregistration identity changed.")

    frozen = record["frozen_inputs"]
    if (
        frozen["exp024_closure_commit"] != EXP024_CLOSURE_COMMIT
        or frozen["exp024_closure_record_sha256"]
        != EXPECTED_EXP024_CLOSURE_SHA256
        or frozen["exp019_exact_contract_archive"]["archive_sha256"]
        != EXPECTED_EXP019_EXACT_CONTRACT_ARCHIVE_SHA256
    ):
        raise ValueError("EXP-025 frozen evidence boundary changed.")

    population = record["population"]
    if (
        population["candidate_id"] != "gap_fade_0p50_1r"
        or population["candidate_session_row_count"] != 43
        or population["unique_session_count"] != 43
        or population["all_43_rows_must_be_retained"] is not True
        or population["sampling_prohibited"] is not True
    ):
        raise ValueError("EXP-025 population boundary changed.")

    if (
        len(record["hard_checks"]) != record["hard_check_count"]
        or len(record["required_outputs"]) != 14
    ):
        raise ValueError("EXP-025 locked check or output count changed.")

    if (
        canonical_record_hash(record)
        != EXPECTED_EXP025_PREREGISTRATION_SHA256
    ):
        raise ValueError("EXP-025 preregistration record changed.")
