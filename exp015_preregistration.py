from __future__ import annotations

from copy import deepcopy
from typing import Any


FIXED_SAMPLE_WINDOWS: tuple[dict[str, str], ...] = (
    {
        "window_id": "2020_march_dst_roll_volatility",
        "start": "2020-03-06",
        "end": "2020-03-20",
        "purpose": "DST transition, March futures roll and extreme volatility.",
    },
    {
        "window_id": "2021_thanksgiving",
        "start": "2021-11-19",
        "end": "2021-12-03",
        "purpose": "Thanksgiving holiday and shortened-session behaviour.",
    },
    {
        "window_id": "2022_june_roll",
        "start": "2022-06-03",
        "end": "2022-06-17",
        "purpose": "June futures roll and ordinary extended sessions.",
    },
    {
        "window_id": "2023_march_dst_roll",
        "start": "2023-03-03",
        "end": "2023-03-17",
        "purpose": "DST transition and March futures roll.",
    },
    {
        "window_id": "2024_thanksgiving",
        "start": "2024-11-22",
        "end": "2024-12-06",
        "purpose": "Thanksgiving holiday and shortened-session behaviour.",
    },
    {
        "window_id": "2025_march_dst_roll",
        "start": "2025-03-07",
        "end": "2025-03-21",
        "purpose": "DST transition and March futures roll.",
    },
)

QUALIFICATION_LEVELS: tuple[str, ...] = (
    "CATALOG_UNAVAILABLE",
    "IDENTITY_UNRESOLVED",
    "SUPPLEMENTARY_ONLY",
    "QUALIFIED_FOR_NEW_NQ_MNQ_HISTORICAL_RESEARCH",
)

OFFICIAL_SOURCE_SNAPSHOT: dict[str, Any] = {
    "snapshot_date": "2026-07-21",
    "website": "https://londonstrategicedge.com/data/",
    "api_docs": "https://londonstrategicedge.com/docs/api/",
    "python_package": "https://pypi.org/project/lse-data/",
    "python_distribution": "lse-data",
    "observed_package_version": "0.14.0",
    "observed_package_release_date": "2026-07-07",
    "observed_package_status": "Beta",
    "observed_requires_python": ">=3.8",
    "observed_classifiers_through": "Python 3.13",
    "package_wheel_sha256": (
        "b1e2f34af882ace2d8dab6fb5fe2b45d0bd6b1f1f39d95d71c3aeb4a56aac1a0"
    ),
    "api_key_environment_variable": "LSE_API_KEY",
    "catalog_method": "client.catalog('futures')",
    "interactive_history_method": "client.candles(...)",
    "bulk_history_method": "client.history(...)",
    "claimed_futures_dataset_count": 54,
    "claimed_candle_resolution_count": 14,
    "claimed_max_rows_per_databank_download": 1_000_000,
    "claimed_databank_downloads_per_hour": 10,
    "claims_are_vendor_statements_not_yet_verified": True,
}


EXP015_PREREGISTRATION: dict[str, Any] = {
    "schema_version": 1,
    "experiment_id": "EXP-015",
    "title": "London Strategic Edge NQ/MNQ Data-Source Qualification",
    "locked_date": "2026-07-21",
    "research_status": "PRE_REGISTERED",
    "implementation_status": "NOT_RUN",
    "results_viewed": "NONE",
    "purpose": (
        "Measure whether London Strategic Edge can serve as a reliable source "
        "of one-minute NQ and MNQ historical data for new research."
    ),
    "research_question": (
        "Does the vendor catalog expose identifiable NQ and MNQ datasets with "
        "clear timestamp and contract methodology, and do fixed historical "
        "samples agree closely enough with the frozen Quantower reference to "
        "support new NQ/MNQ research?"
    ),
    "scope_boundary": {
        "qualified_scope_if_successful": (
            "New NQ/MNQ one-minute historical research from EXP-016 onward."
        ),
        "does_not_qualify_all_vendor_asset_classes": True,
        "does_not_replace_frozen_exp005_through_exp014_data": True,
        "does_not_reopen_prior_results": True,
        "does_not_validate_live_streaming": True,
        "does_not_validate_execution_or_order_routing": True,
        "does_not_authorize_paper_or_live_trading": True,
    },
    "relationship_to_prior_research": {
        "required_exp014_stage": "REVIEW",
        "exp014_result_must_match_frozen_hashes": True,
        "quantower_reference_is_read_only": True,
        "existing_data_hashes_must_not_change": True,
        "existing_strategy_results_must_not_change": True,
        "new_strategy_search": False,
        "new_parameter_search": False,
    },
    "official_source_snapshot": OFFICIAL_SOURCE_SNAPSHOT,
    "credential_and_access_safety": {
        "api_key_source": "LSE_API_KEY environment variable only",
        "api_key_must_not_be_written_to_disk": True,
        "api_key_must_not_be_printed": True,
        "api_key_must_not_be_committed": True,
        "website_scraping_prohibited": True,
        "official_api_or_official_client_only": True,
        "raw_downloads_local_and_gitignored": True,
        "tracked_outputs_are_manifests_hashes_and_measurements_only": True,
        "maximum_bulk_exports_per_hour": 8,
        "minimum_seconds_between_bulk_exports": 450,
    },
    "environment_qualification": {
        "current_project_python": "3.14.6",
        "official_package_classifiers_include_python_3_14": False,
        "main_venv_install_before_compatibility_test_prohibited": True,
        "isolated_import_probe_required": True,
        "package_version_and_distribution_hash_recorded": True,
        "direct_http_fallback_without_documented_endpoint_prohibited": True,
    },
    "catalog_phase": {
        "must_run_before_any_history_download": True,
        "category": "futures",
        "catalog_snapshot_saved": True,
        "exact_nq_and_mnq_identity_required": True,
        "symbol_guessing_prohibited": True,
        "required_metadata": [
            "symbol",
            "name",
            "category",
            "history_start",
            "history_end",
            "tick_count",
        ],
        "contract_type_recorded": [
            "individual_contract",
            "continuous_contract",
            "other_or_unknown",
        ],
        "roll_method_recorded": True,
        "price_adjustment_method_recorded": True,
        "upstream_source_recorded_when_available": True,
        "unresolved_identity_stops_history_phase": True,
    },
    "fixed_history_phase": {
        "markets": ["NQ", "MNQ"],
        "timeframe": "1m",
        "reference_timezone": "UTC",
        "research_timezone": "America/New_York",
        "sample_windows": FIXED_SAMPLE_WINDOWS,
        "sample_window_count": 6,
        "window_changes_after_catalog_view_prohibited": True,
        "full_2020_2025_download_before_sample_review_prohibited": True,
        "raw_response_hash_required": True,
        "normalized_file_hash_required": True,
        "normalization_must_not_fill_or_delete_bars": True,
    },
    "structural_measurements": {
        "timestamp_monotonicity": True,
        "duplicate_timestamp_count": True,
        "timezone_awareness": True,
        "ohlc_numeric_and_finite": True,
        "ohlc_invariants": True,
        "negative_volume_count": True,
        "expected_extended_session_minutes": True,
        "missing_expected_minutes": True,
        "unexpected_minutes": True,
        "session_completeness": True,
        "dst_transition_diagnostics": True,
        "holiday_and_shortened_session_diagnostics": True,
        "roll_window_diagnostics": True,
    },
    "cross_source_measurements": {
        "reference": "Frozen Quantower NQ/MNQ one-minute data",
        "matched_timestamp_count": True,
        "left_only_and_right_only_timestamp_counts": True,
        "open_high_low_close_absolute_differences": True,
        "difference_buckets_points": [0.0, 0.25, 1.0, "infinity"],
        "volume_difference_is_descriptive_not_exact_gate": True,
        "session_ohlc_comparison": True,
        "largest_discrepancy_rows_retained": 100,
        "roll_windows_reported_separately": True,
        "no_silent_tolerance_or_row_exclusion": True,
    },
    "frozen_strategy_replay_diagnostic": {
        "required_only_after_catalog_and_sample_structure_pass": True,
        "candidate_ids": [
            "gap_fade_0p50_1r",
            "premarket_continuation_0p50_time",
            "premarket_continuation_0p75_time",
        ],
        "exact_existing_rules_and_costs": True,
        "no_candidate_selection": True,
        "no_parameter_change": True,
        "no_optimization": True,
        "compare_trade_count": True,
        "compare_entry_exit_timestamps": True,
        "compare_direction": True,
        "compare_net_profit_and_drawdown": True,
        "diagnostic_only_not_new_edge_test": True,
    },
    "qualification_interpretation": {
        "levels": QUALIFICATION_LEVELS,
        "classification_is_per_use_case_not_global": True,
        "catalog_unavailable_when_api_or_futures_catalog_cannot_be_read": True,
        "identity_unresolved_when_nq_or_mnq_mapping_is_ambiguous": True,
        "supplementary_only_when_structural_or_cross_source_material_issues_exist": True,
        "primary_historical_qualification_requires": {
            "both_markets_identified": True,
            "timestamp_semantics_resolved": True,
            "contract_and_roll_method_resolved": True,
            "duplicate_timestamps": 0,
            "invalid_ohlc_rows": 0,
            "negative_volume_rows": 0,
            "minimum_expected_minute_completeness": 0.999,
            "minimum_matched_timestamp_share": 0.999,
            "minimum_close_within_one_tick_share_outside_documented_rolls": 0.995,
            "minimum_frozen_replay_entry_direction_agreement": 0.99,
            "maximum_frozen_replay_trade_count_relative_difference": 0.01,
        },
        "automatic_all_data_claim_prohibited": True,
        "expected_lifecycle_after_measurement": "REVIEW",
        "paper_trading_authorized": False,
        "live_trading_authorized": False,
    },
    "reporting_requirements": {
        "vertical_single_column_report": True,
        "plain_english_source_and_methodology": True,
        "catalog_identity_table": True,
        "environment_compatibility_table": True,
        "sample_window_completeness_table": True,
        "timestamp_and_ohlc_integrity_table": True,
        "cross_source_difference_table": True,
        "dst_holiday_and_roll_sections": True,
        "frozen_strategy_replay_comparison": True,
        "all_adverse_findings_visible": True,
        "positive_numbers_use_neutral_text": True,
        "adverse_numbers_use_red_text": True,
        "green_reserved_for_status_words": True,
        "charts_use_solid_opaque_white_canvas": True,
    },
    "prohibited_actions": [
        "Replacing any frozen EXP-005 through EXP-014 source file.",
        "Guessing NQ or MNQ symbols from names without catalog evidence.",
        "Downloading history before the catalog identity phase passes.",
        "Changing fixed sample windows after viewing catalog or bar results.",
        "Silently filling, deleting, resampling or repairing vendor bars.",
        "Installing an untested beta client into the main environment.",
        "Printing, saving or committing the API key.",
        "Scraping the website instead of using documented official access.",
        "Optimizing a strategy or parameter during the data audit.",
        "Claiming the audit qualifies every London Strategic Edge dataset.",
        "Authorizing paper or live trading.",
    ],
}


def get_exp015_preregistration() -> dict[str, Any]:
    return deepcopy(EXP015_PREREGISTRATION)


def validate_exp015_preregistration(
    record: dict[str, Any] | None = None,
) -> None:
    current = EXP015_PREREGISTRATION if record is None else record

    if (
        current.get("schema_version") != 1
        or current.get("experiment_id") != "EXP-015"
        or current.get("research_status") != "PRE_REGISTERED"
        or current.get("implementation_status") != "NOT_RUN"
        or current.get("results_viewed") != "NONE"
    ):
        raise ValueError("EXP-015 identity or pre-result state changed.")

    scope = current["scope_boundary"]
    if (
        scope["does_not_qualify_all_vendor_asset_classes"] is not True
        or scope["does_not_replace_frozen_exp005_through_exp014_data"] is not True
        or scope["does_not_reopen_prior_results"] is not True
        or scope["does_not_validate_live_streaming"] is not True
        or scope["does_not_authorize_paper_or_live_trading"] is not True
    ):
        raise ValueError("EXP-015 scope boundary changed.")

    relationship = current["relationship_to_prior_research"]
    if (
        relationship["required_exp014_stage"] != "REVIEW"
        or relationship["exp014_result_must_match_frozen_hashes"] is not True
        or relationship["quantower_reference_is_read_only"] is not True
        or relationship["existing_data_hashes_must_not_change"] is not True
        or relationship["existing_strategy_results_must_not_change"] is not True
        or relationship["new_strategy_search"] is not False
        or relationship["new_parameter_search"] is not False
    ):
        raise ValueError("EXP-015 prior-research protection changed.")

    source = current["official_source_snapshot"]
    if (
        source["snapshot_date"] != "2026-07-21"
        or source["python_distribution"] != "lse-data"
        or source["observed_package_version"] != "0.14.0"
        or source["api_key_environment_variable"] != "LSE_API_KEY"
        or source["claims_are_vendor_statements_not_yet_verified"] is not True
    ):
        raise ValueError("EXP-015 official-source snapshot changed.")

    safety = current["credential_and_access_safety"]
    if (
        safety["api_key_source"] != "LSE_API_KEY environment variable only"
        or safety["api_key_must_not_be_written_to_disk"] is not True
        or safety["api_key_must_not_be_printed"] is not True
        or safety["website_scraping_prohibited"] is not True
        or safety["official_api_or_official_client_only"] is not True
        or safety["maximum_bulk_exports_per_hour"] != 8
        or safety["minimum_seconds_between_bulk_exports"] != 450
    ):
        raise ValueError("EXP-015 credential or access safety changed.")

    environment = current["environment_qualification"]
    if (
        environment["current_project_python"] != "3.14.6"
        or environment["official_package_classifiers_include_python_3_14"]
        is not False
        or environment["main_venv_install_before_compatibility_test_prohibited"]
        is not True
        or environment["isolated_import_probe_required"] is not True
    ):
        raise ValueError("EXP-015 environment qualification changed.")

    catalog = current["catalog_phase"]
    if (
        catalog["must_run_before_any_history_download"] is not True
        or catalog["category"] != "futures"
        or catalog["exact_nq_and_mnq_identity_required"] is not True
        or catalog["symbol_guessing_prohibited"] is not True
        or catalog["unresolved_identity_stops_history_phase"] is not True
    ):
        raise ValueError("EXP-015 catalog phase changed.")

    history = current["fixed_history_phase"]
    if (
        history["markets"] != ["NQ", "MNQ"]
        or history["timeframe"] != "1m"
        or tuple(history["sample_windows"]) != FIXED_SAMPLE_WINDOWS
        or history["sample_window_count"] != 6
        or history["window_changes_after_catalog_view_prohibited"] is not True
        or history["full_2020_2025_download_before_sample_review_prohibited"]
        is not True
        or history["normalization_must_not_fill_or_delete_bars"] is not True
    ):
        raise ValueError("EXP-015 fixed-history phase changed.")

    replay = current["frozen_strategy_replay_diagnostic"]
    if (
        replay["candidate_ids"]
        != [
            "gap_fade_0p50_1r",
            "premarket_continuation_0p50_time",
            "premarket_continuation_0p75_time",
        ]
        or replay["exact_existing_rules_and_costs"] is not True
        or replay["no_candidate_selection"] is not True
        or replay["no_parameter_change"] is not True
        or replay["no_optimization"] is not True
        or replay["diagnostic_only_not_new_edge_test"] is not True
    ):
        raise ValueError("EXP-015 frozen replay boundary changed.")

    interpretation = current["qualification_interpretation"]
    requirements = interpretation["primary_historical_qualification_requires"]
    if (
        tuple(interpretation["levels"]) != QUALIFICATION_LEVELS
        or interpretation["classification_is_per_use_case_not_global"] is not True
        or interpretation["automatic_all_data_claim_prohibited"] is not True
        or interpretation["expected_lifecycle_after_measurement"] != "REVIEW"
        or interpretation["paper_trading_authorized"] is not False
        or interpretation["live_trading_authorized"] is not False
        or requirements["duplicate_timestamps"] != 0
        or requirements["invalid_ohlc_rows"] != 0
        or requirements["minimum_expected_minute_completeness"] != 0.999
        or requirements["minimum_matched_timestamp_share"] != 0.999
        or requirements[
            "minimum_close_within_one_tick_share_outside_documented_rolls"
        ]
        != 0.995
        or requirements["minimum_frozen_replay_entry_direction_agreement"]
        != 0.99
        or requirements[
            "maximum_frozen_replay_trade_count_relative_difference"
        ]
        != 0.01
    ):
        raise ValueError("EXP-015 qualification interpretation changed.")

    reporting = current["reporting_requirements"]
    if (
        reporting["vertical_single_column_report"] is not True
        or reporting["catalog_identity_table"] is not True
        or reporting["cross_source_difference_table"] is not True
        or reporting["frozen_strategy_replay_comparison"] is not True
        or reporting["positive_numbers_use_neutral_text"] is not True
        or reporting["adverse_numbers_use_red_text"] is not True
        or reporting["green_reserved_for_status_words"] is not True
        or reporting["charts_use_solid_opaque_white_canvas"] is not True
    ):
        raise ValueError("EXP-015 reporting standard changed.")
