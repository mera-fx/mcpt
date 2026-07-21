from __future__ import annotations
from copy import deepcopy
from typing import Any, Mapping

EXACT_CONTRACT_WINDOWS = (
    {"window_id":"nqh24_february_ordinary","canonical_contract":"NQH24","start":"2024-02-05","end":"2024-02-16","context":"ordinary_active_contract"},
    {"window_id":"nqm24_may_ordinary","canonical_contract":"NQM24","start":"2024-05-06","end":"2024-05-17","context":"ordinary_active_contract"},
    {"window_id":"nqu24_august_volatility","canonical_contract":"NQU24","start":"2024-08-05","end":"2024-08-16","context":"high_volatility"},
    {"window_id":"nqz24_thanksgiving","canonical_contract":"NQZ24","start":"2024-11-22","end":"2024-12-06","context":"holiday_and_early_close"},
    {"window_id":"nqh25_march_dst","canonical_contract":"NQH25","start":"2025-03-07","end":"2025-03-14","context":"daylight_saving_transition"},
    {"window_id":"nqm25_may_ordinary","canonical_contract":"NQM25","start":"2025-05-12","end":"2025-05-23","context":"ordinary_active_contract"},
)
REPEATABILITY_WINDOW_IDS=("nqz24_thanksgiving","nqh25_march_dst")
SOURCE_ROLE_IDS=("quantower_exact_contract_export","london_exact_contract_candidate","independent_exchange_reference_candidate")

EXP017_PREREGISTRATION: dict[str, Any] = {
    "schema_version":1,
    "experiment_id":"EXP-017",
    "title":"Exact NQ Contract Data Benchmark",
    "locked_date":"2026-07-21",
    "research_status":"PRE_REGISTERED",
    "implementation_status":"NOT_IMPLEMENTED",
    "benchmark_bar_values_viewed":"NONE",
    "objective":{
        "primary_question":"Which accessible exact-contract one-minute NQ source provides the strongest evidence of price accuracy, completeness and historical reproducibility for new strategy research?",
        "separate_decisions":("primary_historical_research_source","secondary_audit_source","execution_feed_alignment_source"),
        "weighted_composite_score_prohibited":True,
        "data_quality_precedes_cost":True,
        "cost_is_tie_break_only":True,
    },
    "prior_research":{
        "exp016_required_stage":"REVIEW",
        "exp016_required_classification":"NOT_QUALIFIED",
        "exp016_freeze_must_verify":True,
        "exp005_through_exp016_must_remain_frozen":True,
        "existing_quantower_data_read_only":True,
        "existing_strategy_results_read_only":True,
        "retroactive_result_replacement_prohibited":True,
    },
    "scope":{
        "market":"NQ futures only",
        "timeframe":"one-minute OHLCV",
        "exact_quarterly_contracts_only":True,
        "continuous_symbols_prohibited":True,
        "back_adjusted_series_prohibited":True,
        "synthetic_roll_series_prohibited":True,
        "mnq_out_of_scope":True,
        "sample_benchmark_only":True,
        "full_history_download_prohibited":True,
        "strategy_replay_prohibited":True,
        "strategy_optimization_prohibited":True,
        "paper_trading_authorized":False,
        "live_trading_authorized":False,
    },
    "source_lock_stage":{
        "required_before_any_benchmark_bars":True,
        "source_roles":SOURCE_ROLE_IDS,
        "minimum_exact_contract_sources":2,
        "target_exact_contract_sources":3,
        "absolute_primary_claim_requires_exchange_reference":True,
        "consensus_fallback_requires_independent_sources":3,
        "two_source_disagreement_cannot_select_winner":True,
        "quantower_not_assumed_ground_truth":True,
        "london_not_assumed_inaccurate":True,
        "source_specific_symbol_mapping_required":True,
        "contract_expiry_identity_verification_required":True,
        "source_version_and_provider_required":True,
        "session_and_bar_timestamp_semantics_required":True,
        "official_documentation_or_catalog_only_before_lock":True,
        "bar_value_access_before_source_lock_prohibited":True,
        "source_substitution_after_bar_access_prohibited":True,
        "london_excluded_if_exact_contract_identity_unavailable":True,
        "selection_inputs":("exact_contract_capability","exchange_provenance","timestamp_and_bar_documentation","licensing_and_permitted_research_use","historical_depth","access_method","quoted_cost"),
        "selection_inputs_must_exclude":("observed_ohlcv_values","observed_strategy_performance","post_download_source_quality_results"),
    },
    "access_safety":{
        "official_api_or_user_export_only":True,
        "website_scraping_prohibited":True,
        "credentials_environment_only":True,
        "credentials_must_not_be_printed":True,
        "credentials_must_not_be_written":True,
        "raw_files_local_and_gitignored":True,
        "vendor_data_redistribution_prohibited":True,
        "aggregate_measurements_and_hashes_only_tracked":True,
        "legal_and_license_review_required":True,
    },
    "sample_plan":{
        "windows":EXACT_CONTRACT_WINDOWS,
        "window_count":6,
        "canonical_contract_count":6,
        "windows_locked_before_source_lock":True,
        "source_aliases_may_differ_but_identity_must_match":True,
        "requested_resolution":"1m",
        "canonical_timezone":"UTC",
        "price_tick_points":0.25,
        "regular_and_extended_sessions_measured_separately":True,
        "project_cme_calendar_used_for_schedule_only":True,
        "quantower_prices_not_used_as_automatic_truth":True,
        "no_bar_fill_delete_repair_or_price_offset":True,
        "raw_file_hash_required":True,
        "canonical_row_hash_required":True,
    },
    "measurements":{
        "contract_identity_and_symbol_mapping":True,
        "timestamp_field_timezone_and_bar_label":True,
        "timestamp_order_and_duplicates":True,
        "ohlcv_numeric_and_finite":True,
        "ohlc_invariants":True,
        "negative_volume":True,
        "expected_regular_session_completeness":True,
        "expected_extended_session_completeness":True,
        "source_only_and_reference_only_minutes":True,
        "pairwise_matched_timestamp_share":True,
        "open_high_low_close_absolute_differences":True,
        "difference_buckets_points":(0.0,0.25,0.5,1.0,"infinity"),
        "ohlc_within_one_tick_shares":True,
        "volume_absolute_and_relative_difference":True,
        "volume_is_descriptive_not_primary_accuracy_gate":True,
        "session_first_and_last_timestamp":True,
        "regular_session_and_extended_session_tables":True,
        "largest_discrepancies_local_only":True,
        "no_silent_row_exclusion":True,
    },
    "repeatability":{
        "window_ids":REPEATABILITY_WINDOW_IDS,
        "second_download_minimum_delay_hours":24,
        "raw_hash_compared":True,
        "canonical_row_hash_compared":True,
        "metadata_only_file_difference_separated":True,
        "historical_row_revision_counted":True,
        "primary_candidate_requires_identical_canonical_rows":True,
    },
    "reference_logic":{
        "exchange_native_or_exchange_licensed_reference_preferred":True,
        "reference_must_be_exact_same_contract":True,
        "reference_must_not_be_continuous_symbol":True,
        "exchange_reference_enables_accuracy_language":True,
        "three_source_consensus_is_fallback_only":True,
        "consensus_rule":"two_of_three_within_one_tick",
        "consensus_cannot_prove_absolute_accuracy":True,
        "two_sources_only_means_disagreement_unresolved":True,
        "pairwise_results_all_visible":True,
    },
    "eligibility_gates":{
        "all_locked_windows_present":True,
        "exact_contract_identity_resolved":True,
        "timestamp_semantics_resolved":True,
        "duplicate_timestamps":0,
        "invalid_ohlc_rows":0,
        "negative_volume_rows":0,
        "nonfinite_ohlcv_rows":0,
        "minimum_regular_session_completeness":0.9999,
        "minimum_extended_session_completeness":0.999,
        "minimum_exchange_reference_close_within_one_tick_share":0.9995,
        "minimum_exchange_reference_each_ohlc_within_one_tick_share":0.999,
        "repeatability_canonical_hash_exact_for_primary":True,
        "volume_not_hard_gate":True,
    },
    "selection_rule":{
        "method":"lexicographic_not_weighted",
        "ordered_priorities":("exchange_referenced_ohlc_accuracy","regular_and_extended_session_completeness","canonical_repeatability","execution_feed_similarity","historical_depth_and_operational_reliability","cost_and_license_constraints"),
        "cost_cannot_rescue_weaker_data_quality":True,
        "all_source_measurements_remain_visible":True,
        "ties_may_create_coqualified_sources":True,
        "manual_winner_override_prohibited":True,
    },
    "interpretation":{
        "classifications":("ACCESS_INCOMPLETE","SOURCE_LOCK_INCOMPLETE","IDENTITY_UNRESOLVED","STRUCTURE_FAILED","COMPARISON_UNRESOLVED","NO_QUALIFIED_SOURCE","QUALIFIED_SECONDARY_SOURCE","BEST_AVAILABLE_AMONG_TESTED","EXCHANGE_REFERENCED_PRIMARY_CANDIDATE"),
        "highest_with_exchange_reference":"EXCHANGE_REFERENCED_PRIMARY_CANDIDATE",
        "highest_without_exchange_reference":"BEST_AVAILABLE_AMONG_TESTED",
        "best_available_is_not_absolute_accuracy_claim":True,
        "new_research_only":True,
        "automatic_full_history_migration_prohibited":True,
        "automatic_continuous_series_construction_prohibited":True,
        "next_experiment_required_for_full_history_and_roll_build":True,
        "expected_lifecycle_after_measurement":"REVIEW",
        "paper_trading_authorized":False,
        "live_trading_authorized":False,
    },
}

def get_exp017_preregistration():
    return deepcopy(EXP017_PREREGISTRATION)

def validate_exp017_preregistration(record: Mapping[str, Any] | None=None):
    r=EXP017_PREREGISTRATION if record is None else dict(record)
    if (r.get("schema_version")!=1 or r.get("experiment_id")!="EXP-017" or r.get("research_status")!="PRE_REGISTERED" or r.get("implementation_status")!="NOT_IMPLEMENTED" or r.get("benchmark_bar_values_viewed")!="NONE"):
        raise ValueError("EXP-017 identity changed.")
    o=r["objective"]
    if not (o["weighted_composite_score_prohibited"] is True and o["data_quality_precedes_cost"] is True and o["cost_is_tie_break_only"] is True):
        raise ValueError("EXP-017 objective changed.")
    s=r["scope"]
    if not (s["exact_quarterly_contracts_only"] is True and s["continuous_symbols_prohibited"] is True and s["back_adjusted_series_prohibited"] is True and s["synthetic_roll_series_prohibited"] is True and s["full_history_download_prohibited"] is True and s["strategy_replay_prohibited"] is True and s["strategy_optimization_prohibited"] is True and s["paper_trading_authorized"] is False and s["live_trading_authorized"] is False):
        raise ValueError("EXP-017 scope changed.")
    lock=r["source_lock_stage"]
    if not (lock["required_before_any_benchmark_bars"] is True and tuple(lock["source_roles"])==SOURCE_ROLE_IDS and lock["minimum_exact_contract_sources"]==2 and lock["target_exact_contract_sources"]==3 and lock["absolute_primary_claim_requires_exchange_reference"] is True and lock["consensus_fallback_requires_independent_sources"]==3 and lock["two_source_disagreement_cannot_select_winner"] is True and lock["quantower_not_assumed_ground_truth"] is True and lock["london_not_assumed_inaccurate"] is True and lock["bar_value_access_before_source_lock_prohibited"] is True and lock["source_substitution_after_bar_access_prohibited"] is True):
        raise ValueError("EXP-017 source-lock boundary changed.")
    sample=r["sample_plan"]
    if not (tuple(sample["windows"])==EXACT_CONTRACT_WINDOWS and sample["window_count"]==6 and sample["canonical_contract_count"]==6 and sample["requested_resolution"]=="1m" and sample["canonical_timezone"]=="UTC" and sample["price_tick_points"]==0.25 and sample["quantower_prices_not_used_as_automatic_truth"] is True and sample["no_bar_fill_delete_repair_or_price_offset"] is True):
        raise ValueError("EXP-017 sample plan changed.")
    ref=r["reference_logic"]
    if not (ref["reference_must_be_exact_same_contract"] is True and ref["reference_must_not_be_continuous_symbol"] is True and ref["three_source_consensus_is_fallback_only"] is True and ref["consensus_rule"]=="two_of_three_within_one_tick" and ref["consensus_cannot_prove_absolute_accuracy"] is True and ref["two_sources_only_means_disagreement_unresolved"] is True):
        raise ValueError("EXP-017 reference logic changed.")
    g=r["eligibility_gates"]
    if not (g["duplicate_timestamps"]==0 and g["invalid_ohlc_rows"]==0 and g["negative_volume_rows"]==0 and g["nonfinite_ohlcv_rows"]==0 and g["minimum_regular_session_completeness"]==0.9999 and g["minimum_extended_session_completeness"]==0.999 and g["minimum_exchange_reference_close_within_one_tick_share"]==0.9995 and g["minimum_exchange_reference_each_ohlc_within_one_tick_share"]==0.999 and g["repeatability_canonical_hash_exact_for_primary"] is True and g["volume_not_hard_gate"] is True):
        raise ValueError("EXP-017 eligibility gates changed.")
    sel=r["selection_rule"]
    if not (sel["method"]=="lexicographic_not_weighted" and sel["cost_cannot_rescue_weaker_data_quality"] is True and sel["all_source_measurements_remain_visible"] is True and sel["manual_winner_override_prohibited"] is True):
        raise ValueError("EXP-017 selection rule changed.")
    i=r["interpretation"]
    if not (i["highest_with_exchange_reference"]=="EXCHANGE_REFERENCED_PRIMARY_CANDIDATE" and i["highest_without_exchange_reference"]=="BEST_AVAILABLE_AMONG_TESTED" and i["best_available_is_not_absolute_accuracy_claim"] is True and i["automatic_full_history_migration_prohibited"] is True and i["automatic_continuous_series_construction_prohibited"] is True and i["next_experiment_required_for_full_history_and_roll_build"] is True and i["paper_trading_authorized"] is False and i["live_trading_authorized"] is False):
        raise ValueError("EXP-017 interpretation changed.")
