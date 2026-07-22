from __future__ import annotations
from copy import deepcopy

WINDOWS = (
    ("nqh24_february_ordinary", "NQH24", "NQH4", 750, "2024-02-05", "2024-02-17"),
    ("nqm24_may_ordinary", "NQM24", "NQM4", 13743, "2024-05-06", "2024-05-18"),
    ("nqu24_august_volatility", "NQU24", "NQU4", 4358, "2024-08-05", "2024-08-17"),
    ("nqz24_thanksgiving", "NQZ24", "NQZ4", 106364, "2024-11-22", "2024-12-07"),
    ("nqh25_march_dst", "NQH25", "NQH5", 42288528, "2025-03-07", "2025-03-15"),
    ("nqm25_may_ordinary", "NQM25", "NQM5", 42005804, "2025-05-12", "2025-05-24"),
)

REPEATABILITY_WINDOW_IDS = (
    "nqz24_thanksgiving",
    "nqh25_march_dst",
)

EXP018_PREREGISTRATION = {
    "schema_version": 1,
    "experiment_id": "EXP-018",
    "title": "Databento Exact-Contract Structural and Repeatability Qualification",
    "locked_date": "2026-07-22",
    "research_status": "PRE_REGISTERED",
    "implementation_status": "NOT_IMPLEMENTED",
    "ohlcv_bar_values_viewed": "NONE",
    "objective": {
        "single_source_qualification_only": True,
        "price_accuracy_comparison": False,
        "exchange_accuracy_claim": False,
        "best_vendor_claim": False,
        "strategy_performance_question": False,
    },
    "source": {
        "provider": "Databento",
        "client_version": "0.81.0",
        "dataset": "GLBX.MDP3",
        "schema": "ohlcv-1m",
        "stype_in": "raw_symbol",
        "estimated_initial_cost_usd": 0.283447,
    },
    "scope": {
        "exact_contracts_only": True,
        "continuous_symbols_prohibited": True,
        "back_adjusted_series_prohibited": True,
        "full_history_download_prohibited": True,
        "strategy_replay_prohibited": True,
        "strategy_optimization_prohibited": True,
        "paper_trading_authorized": False,
        "live_trading_authorized": False,
    },
    "access": {
        "official_api_only": True,
        "website_scraping_prohibited": True,
        "credentials_environment_only": True,
        "raw_files_local_and_gitignored": True,
        "automatic_retry_prohibited": True,
        "failure_requires_stop": True,
        "maximum_total_cost_usd": 1.0,
    },
    "sample_plan": {
        "windows": WINDOWS,
        "first_pass_requests": 6,
        "repeat_requests": 2,
        "maximum_successful_bar_requests": 8,
        "timestamp_field": "ts_event",
        "timestamp_timezone": "UTC",
        "bar_label": "inclusive_minute_start",
        "empty_trade_minutes_omitted_by_source": True,
        "tick_points": 0.25,
    },
    "canonicalization": {
        "sort_keys": ("ts_event", "instrument_id"),
        "timestamp_shift_prohibited": True,
        "ohlc_rounding_prohibited": True,
        "bar_fill_prohibited": True,
        "bar_delete_prohibited": True,
        "price_repair_prohibited": True,
        "duplicates_must_be_reported": True,
        "raw_sha256_required": True,
        "canonical_sha256_required": True,
    },
    "measurements": {
        "identity": True,
        "timestamp_alignment": True,
        "duplicates": True,
        "finite_ohlcv": True,
        "ohlc_invariants": True,
        "negative_volume": True,
        "off_tick_prices": True,
        "regular_trade_minute_coverage": True,
        "extended_trade_minute_coverage": True,
        "missing_minute_runs": True,
        "holiday_and_dst_separate": True,
    },
    "repeatability": {
        "window_ids": REPEATABILITY_WINDOW_IDS,
        "minimum_delay_hours": 24,
        "raw_hash_compared": True,
        "canonical_hash_compared": True,
        "row_count_compared": True,
        "timestamp_set_compared": True,
        "identical_canonical_rows_required": True,
    },
    "gates": {
        "all_initial_windows_required": True,
        "identity_mismatches": 0,
        "duplicate_timestamps": 0,
        "duplicate_full_rows": 0,
        "invalid_ohlc_rows": 0,
        "negative_volume_rows": 0,
        "nonfinite_ohlcv_rows": 0,
        "off_tick_ohlc_values": 0,
        "minimum_regular_trade_minute_coverage": 0.999,
        "minimum_extended_trade_minute_coverage": 0.995,
        "both_repeats_required": True,
        "repeat_delay_required": True,
        "repeat_canonical_hash_exact": True,
    },
    "interpretation": {
        "highest_possible": "QUALIFIED_AS_ACCESSIBLE_EXACT_CONTRACT_SOURCE",
        "not_exchange_accuracy_claim": True,
        "not_best_vendor_claim": True,
        "new_research_only": True,
        "full_history_requires_new_experiment": True,
        "continuous_roll_requires_new_experiment": True,
        "paper_trading_authorized": False,
        "live_trading_authorized": False,
    },
}

def get_exp018_preregistration():
    return deepcopy(EXP018_PREREGISTRATION)

def validate_exp018_preregistration(record=None):
    r = EXP018_PREREGISTRATION if record is None else record
    if (
        r["experiment_id"] != "EXP-018"
        or r["research_status"] != "PRE_REGISTERED"
        or r["implementation_status"] != "NOT_IMPLEMENTED"
        or r["ohlcv_bar_values_viewed"] != "NONE"
    ):
        raise ValueError("EXP-018 identity changed.")
    if len(r["sample_plan"]["windows"]) != 6:
        raise ValueError("EXP-018 sample plan changed.")
    if (
        r["sample_plan"]["first_pass_requests"] != 6
        or r["sample_plan"]["repeat_requests"] != 2
        or r["sample_plan"]["maximum_successful_bar_requests"] != 8
    ):
        raise ValueError("EXP-018 request plan changed.")
    if r["access"]["maximum_total_cost_usd"] != 1.0:
        raise ValueError("EXP-018 cost cap changed.")
    if r["access"]["automatic_retry_prohibited"] is not True:
        raise ValueError("EXP-018 retry boundary changed.")
    if tuple(r["repeatability"]["window_ids"]) != REPEATABILITY_WINDOW_IDS:
        raise ValueError("EXP-018 repeatability changed.")
    if (
        r["gates"]["minimum_regular_trade_minute_coverage"] != 0.999
        or r["gates"]["minimum_extended_trade_minute_coverage"] != 0.995
        or r["gates"]["repeat_canonical_hash_exact"] is not True
    ):
        raise ValueError("EXP-018 gates changed.")
    if (
        r["scope"]["strategy_replay_prohibited"] is not True
        or r["scope"]["strategy_optimization_prohibited"] is not True
        or r["scope"]["paper_trading_authorized"] is not False
        or r["scope"]["live_trading_authorized"] is not False
    ):
        raise ValueError("EXP-018 scope changed.")
