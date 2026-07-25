from __future__ import annotations

from copy import deepcopy


EXP019_CLOSURE_COMMIT = (
    "e86a9074385ad8d2c1b61711b5739910882c2b18"
)

EXP019_EVIDENCE_HASHES = {
    "acquisition_manifest_sha256": (
        "f8fbac395bbe7f9cdafd0187a00c3d77"
        "ee8f6ded31d7ba6870d6ed3c8e3007b3"
    ),
    "acquisition_completion_sha256": (
        "ef8ad499e62284d872edfd480e7aa635"
        "a26340e85ba1d74d98a51ed80f71f935"
    ),
    "audit_summary_sha256": (
        "e02b3e6d67715fbdfa2c42677225ce74"
        "cdf444b8d14cbf93a80e897fbca18287"
    ),
    "audit_contracts_sha256": (
        "540008d208cf1d4f35d3b2cdbdb1eda7"
        "1f25b18bb931c9c4091cfdad29548b11"
    ),
    "audit_overlaps_sha256": (
        "e07d8cd41a0ae2544d1adb786fa50680"
        "a595f5c479ca699ff044d29991d26e7f"
    ),
    "audit_report_sha256": (
        "172719fee061f133dce5a4755caa29e2"
        "9b48d8984065cb43df4c6ab93eb043da"
    ),
    "audit_completion_sha256": (
        "4f4f224531d3de440e20d9da600e93c"
        "6a0427ddec04b70e507005aecf67075b8"
    ),
}

HARD_CHECKS = (
    "frozen_exp019_evidence_hashes_match",
    "exactly_66_source_contract_files",
    "all_source_files_remain_read_only",
    "all_65_adjacent_transitions_resolved",
    "roll_boundaries_within_locked_overlap",
    "one_ordered_roll_per_adjacent_pair",
    "common_adjustment_reference_exists",
    "constructed_series_is_nonempty",
    "timestamps_are_strictly_increasing",
    "constructed_timestamps_are_unique",
    "source_contract_identity_is_complete",
    "unadjusted_rows_match_source_ohlcv",
    "all_ohlcv_values_are_finite",
    "unadjusted_ohlc_invariants_hold",
    "adjusted_ohlc_invariants_hold",
    "volume_is_nonnegative",
    "unadjusted_prices_are_quarter_tick_aligned",
    "adjustments_are_quarter_tick_aligned",
    "adjustment_ledger_reconciles_exactly",
    "independent_rebuild_hashes_match",
)

EXP020_PREREGISTRATION = {
    "schema_version": 1,
    "experiment_id": "EXP-020",
    "title": (
        "NQ Exact-Contract Continuous-Series Construction"
    ),
    "locked_date": "2026-07-25",
    "research_status": "PRE_REGISTERED",
    "implementation_status": "NOT_IMPLEMENTED",
    "roll_trigger_values_viewed_before_lock": False,
    "objective": {
        "construct_continuous_series": True,
        "compare_locked_roll_methods": True,
        "produce_unadjusted_series": True,
        "produce_backward_adjusted_series": True,
        "select_method_using_strategy_results": False,
        "strategy_performance_question": False,
        "market_data_download": False,
    },
    "frozen_input": {
        "source_experiment": "EXP-019",
        "closure_commit": EXP019_CLOSURE_COMMIT,
        "classification": (
            "QUALIFIED_WITH_KNOWN_PROVIDER_CONDITIONS"
        ),
        "provider": "Databento",
        "dataset": "GLBX.MDP3",
        "schema": "ohlcv-1m",
        "first_date": "2010-06-06",
        "end_exclusive": "2026-07-24",
        "contract_count": 66,
        "record_count": 6_276_486,
        "compressed_total_bytes": 104_491_346,
        "known_provider_warning_windows": 16,
        "hard_failure_count": 0,
        "archive_sha256": (
            "225a64dc06cb6bb303fd83d186f2e7d8"
            "1e2a8a8bec44382380c8ccc1b0b6baa3"
        ),
        "evidence_hashes": EXP019_EVIDENCE_HASHES,
        "source_archive_read_only": True,
    },
    "session_definition": {
        "timezone": "America/New_York",
        "session_start_local": "18:00:00",
        "session_end_local_exclusive": (
            "18:00:00 next calendar day"
        ),
        "trading_date_rule": (
            "Timestamps at or after 18:00 New York belong "
            "to the following trading date; earlier "
            "timestamps belong to the local date."
        ),
        "daylight_saving_time_aware": True,
        "missing_no_trade_minutes_not_filled": True,
        "synthetic_bars_prohibited": True,
    },
    "construction_scope": {
        "primary_method": (
            "VOLUME_CROSSOVER_2_SESSION_"
            "WITH_CALENDAR_FALLBACK"
        ),
        "benchmark_method": (
            "CALENDAR_THURSDAY_8_DAYS_BEFORE_EXPIRY"
        ),
        "primary_method_fixed_before_values": True,
        "dynamic_method_selection_prohibited": True,
        "open_interest_method_in_scope": False,
        "quarterly_contracts_only": True,
        "expected_contract_transitions": 65,
        "output_frequency": "1 minute",
        "output_timestamp_timezone": "UTC",
    },
    "volume_roll_rule": {
        "daily_measure": (
            "Sum observed one-minute volume by contract "
            "and New York trading date."
        ),
        "comparison": (
            "Incoming-contract daily volume must be "
            "strictly greater than outgoing-contract "
            "daily volume."
        ),
        "required_consecutive_sessions": 2,
        "both_contracts_required": True,
        "known_warning_sessions_excluded_from_trigger": True,
        "effective_boundary": (
            "Trading session immediately following the "
            "second consecutive qualifying session."
        ),
        "latest_allowed_boundary": (
            "Locked calendar-roll effective boundary."
        ),
        "fallback": (
            "Use the locked calendar-roll boundary when "
            "no valid crossover occurs first."
        ),
        "fallbacks_must_be_disclosed": True,
        "intraday_roll_prohibited": True,
    },
    "calendar_roll_rule": {
        "method_id": (
            "CALENDAR_THURSDAY_8_DAYS_BEFORE_EXPIRY"
        ),
        "expiry_reference": (
            "Locked EXP-019 planning expiry date."
        ),
        "trigger_calendar_days_before_expiry": 8,
        "trigger_weekday": "Thursday",
        "effective_boundary": (
            "First complete trading session beginning "
            "after the trigger date."
        ),
        "intraday_roll_prohibited": True,
        "missing_boundary_rule": (
            "Use the first later common trading session "
            "within the locked overlap window; otherwise "
            "the transition hard-fails."
        ),
    },
    "stitching_rule": {
        "boundary_unit": "New York trading date",
        "old_contract_rows": (
            "Include rows with trading date before the "
            "effective roll trading date."
        ),
        "new_contract_rows": (
            "Include rows with trading date on or after "
            "the effective roll trading date."
        ),
        "duplicate_timestamp_resolution": (
            "Use the contract-selection rule only; "
            "arbitrary first-row or last-row "
            "deduplication is prohibited."
        ),
        "source_contract_column_required": True,
        "roll_method_column_required": True,
        "adjustment_column_required": True,
    },
    "adjustment_rule": {
        "method": "BACKWARD_DIFFERENCE",
        "reference_timestamp": (
            "Latest timestamp shared by outgoing and "
            "incoming contracts before the roll boundary."
        ),
        "reference_price": "close",
        "roll_difference_formula": (
            "incoming_close - outgoing_close"
        ),
        "historical_adjustment": (
            "Add each roll difference cumulatively to all "
            "earlier OHLC values."
        ),
        "volume_adjusted": False,
        "timestamps_adjusted": False,
        "unadjusted_series_preserved": True,
        "forward_adjustment_prohibited": True,
        "ratio_adjustment_prohibited": True,
    },
    "required_series": (
        "volume_roll_unadjusted",
        "volume_roll_backward_adjusted",
        "calendar_roll_unadjusted",
        "calendar_roll_backward_adjusted",
    ),
    "required_outputs": (
        "construction_summary.json",
        "roll_ledger.csv",
        "contract_contribution.csv",
        "method_comparison.csv",
        "volume_roll_unadjusted.parquet",
        "volume_roll_backward_adjusted.parquet",
        "calendar_roll_unadjusted.parquet",
        "calendar_roll_backward_adjusted.parquet",
        "output_hashes.json",
        "report.md",
        "CONSTRUCTION_COMPLETE.json",
    ),
    "hard_checks": HARD_CHECKS,
    "classification": {
        "hard_failure_result": "NOT_QUALIFIED",
        "all_checks_zero_fallbacks": (
            "QUALIFIED_VOLUME_CROSSOVER_"
            "CONTINUOUS_SERIES"
        ),
        "all_checks_with_fallbacks": (
            "QUALIFIED_WITH_DISCLOSED_"
            "CALENDAR_FALLBACKS"
        ),
        "canonical_candidate": (
            "Volume-crossover series only; calendar "
            "series remains a benchmark."
        ),
        "strategy_use_authorized": False,
    },
    "execution_boundary": {
        "implementation_requires_locked_commit": True,
        "protected_preflight_required": True,
        "databento_api_calls": 0,
        "credentials_required": False,
        "source_archive_modifications": False,
        "temporary_independent_rebuild_required": True,
        "construction_rerun_after_completion": False,
    },
    "prohibited_actions": {
        "databento_api_request": True,
        "new_market_data_download": True,
        "modify_exp019_archive": True,
        "overwrite_exp019_outputs": True,
        "inspect_strategy_performance": True,
        "strategy_replay": True,
        "strategy_optimization": True,
        "mcpt": True,
        "bootstrap": True,
        "walk_forward": True,
        "paper_trading": True,
        "live_trading": True,
        "change_prior_experiments": True,
    },
    "interpretation": {
        "data_engineering_experiment_only": True,
        "continuous_series_not_yet_created": True,
        "roll_method_not_validated_by_strategy": True,
        "exchange_accuracy_not_claimed": True,
        "best_vendor_not_claimed": True,
        "strategy_edge_not_claimed": True,
        "separate_strategy_experiment_required": True,
    },
}


def get_exp020_preregistration():
    return deepcopy(EXP020_PREREGISTRATION)


def validate_exp020_preregistration(candidate=None):
    record = (
        EXP020_PREREGISTRATION
        if candidate is None
        else candidate
    )

    if (
        record["experiment_id"] != "EXP-020"
        or record["locked_date"] != "2026-07-25"
        or record["research_status"] != "PRE_REGISTERED"
        or record["implementation_status"] != "NOT_IMPLEMENTED"
        or record[
            "roll_trigger_values_viewed_before_lock"
        ]
        is not False
    ):
        raise ValueError("EXP-020 identity changed.")

    source = record["frozen_input"]

    if (
        source["source_experiment"] != "EXP-019"
        or source["closure_commit"] != EXP019_CLOSURE_COMMIT
        or source["classification"]
        != "QUALIFIED_WITH_KNOWN_PROVIDER_CONDITIONS"
        or source["contract_count"] != 66
        or source["record_count"] != 6_276_486
        or source["compressed_total_bytes"] != 104_491_346
        or source["known_provider_warning_windows"] != 16
        or source["hard_failure_count"] != 0
        or source["source_archive_read_only"] is not True
        or source["evidence_hashes"] != EXP019_EVIDENCE_HASHES
    ):
        raise ValueError("EXP-020 frozen input changed.")

    scope = record["construction_scope"]

    if (
        scope["primary_method"]
        != (
            "VOLUME_CROSSOVER_2_SESSION_"
            "WITH_CALENDAR_FALLBACK"
        )
        or scope["benchmark_method"]
        != "CALENDAR_THURSDAY_8_DAYS_BEFORE_EXPIRY"
        or scope["primary_method_fixed_before_values"]
        is not True
        or scope["dynamic_method_selection_prohibited"]
        is not True
        or scope["open_interest_method_in_scope"] is not False
        or scope["expected_contract_transitions"] != 65
    ):
        raise ValueError("EXP-020 construction scope changed.")

    session = record["session_definition"]

    if (
        session["timezone"] != "America/New_York"
        or session["session_start_local"] != "18:00:00"
        or session["daylight_saving_time_aware"] is not True
        or session["missing_no_trade_minutes_not_filled"]
        is not True
        or session["synthetic_bars_prohibited"] is not True
    ):
        raise ValueError("EXP-020 session definition changed.")

    volume = record["volume_roll_rule"]

    if (
        volume["required_consecutive_sessions"] != 2
        or volume[
            "known_warning_sessions_excluded_from_trigger"
        ]
        is not True
        or volume["fallbacks_must_be_disclosed"] is not True
        or volume["intraday_roll_prohibited"] is not True
    ):
        raise ValueError("EXP-020 volume-roll rule changed.")

    adjustment = record["adjustment_rule"]

    if (
        adjustment["method"] != "BACKWARD_DIFFERENCE"
        or adjustment["reference_price"] != "close"
        or adjustment["volume_adjusted"] is not False
        or adjustment["timestamps_adjusted"] is not False
        or adjustment["unadjusted_series_preserved"] is not True
        or adjustment["forward_adjustment_prohibited"] is not True
        or adjustment["ratio_adjustment_prohibited"] is not True
    ):
        raise ValueError("EXP-020 adjustment rule changed.")

    checks = tuple(record["hard_checks"])

    if (
        checks != HARD_CHECKS
        or len(checks) != 20
        or len(set(checks)) != 20
    ):
        raise ValueError("EXP-020 hard checks changed.")

    required_series = tuple(record["required_series"])

    if required_series != (
        "volume_roll_unadjusted",
        "volume_roll_backward_adjusted",
        "calendar_roll_unadjusted",
        "calendar_roll_backward_adjusted",
    ):
        raise ValueError("EXP-020 required series changed.")

    classification = record["classification"]

    if (
        classification["hard_failure_result"]
        != "NOT_QUALIFIED"
        or classification["all_checks_zero_fallbacks"]
        != "QUALIFIED_VOLUME_CROSSOVER_CONTINUOUS_SERIES"
        or classification["all_checks_with_fallbacks"]
        != "QUALIFIED_WITH_DISCLOSED_CALENDAR_FALLBACKS"
        or classification["strategy_use_authorized"] is not False
    ):
        raise ValueError("EXP-020 classification changed.")

    if not all(
        value is True
        for value in record["prohibited_actions"].values()
    ):
        raise ValueError("EXP-020 prohibited actions changed.")
