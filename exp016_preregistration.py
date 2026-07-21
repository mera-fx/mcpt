from __future__ import annotations
from copy import deepcopy
from typing import Any

FIXED_SAMPLE_WINDOWS = (
    {"window_id":"2020_march_dst_roll_volatility","start":"2020-03-06","end":"2020-03-20"},
    {"window_id":"2021_thanksgiving","start":"2021-11-19","end":"2021-12-03"},
    {"window_id":"2022_june_roll","start":"2022-06-03","end":"2022-06-17"},
    {"window_id":"2023_march_dst_roll","start":"2023-03-03","end":"2023-03-17"},
    {"window_id":"2024_thanksgiving","start":"2024-11-22","end":"2024-12-06"},
    {"window_id":"2025_march_dst_roll","start":"2025-03-07","end":"2025-03-21"},
)

EXP015_FROZEN_EVIDENCE = {
    "final_commit":"bd877443f637d8041c3de935c1c8c872f5abcf72",
    "catalog_result_json_sha256":"ba9595726de4018f4b283436c447e5aabd5dfa2109b5296c0a8e41159b3028e5",
    "catalog_rows_csv_sha256":"e191b695ae833984f781236e93551f102218937e5b10f2adb85358f996a5980a",
    "catalog_canonical_sha256":"55d5b8057c8b0b50e416d2a4f1601c86296992e334020d239114ade8dd45fceb",
    "futures_catalog_rows":69,
    "nq_symbol":"NQ.F",
    "mnq_candidate_count":0,
    "classification":"IDENTITY_UNRESOLVED",
}

EXP016_PREREGISTRATION: dict[str, Any] = {
    "schema_version":1,
    "experiment_id":"EXP-016",
    "title":"NQ.F Structural and Cross-Source Sample Audit",
    "locked_date":"2026-07-21",
    "research_status":"PRE_REGISTERED",
    "implementation_status":"NOT_RUN",
    "results_viewed":"NONE",
    "scope":{
        "market":"NQ only","vendor_symbol":"NQ.F","timeframe":"1m",
        "sample_audit_only":True,"full_history_download_prohibited":True,
        "mnq_out_of_scope":True,"primary_source_replacement_prohibited":True,
        "strategy_replay_prohibited":True,"strategy_optimization_prohibited":True,
        "paper_trading_authorized":False,"live_trading_authorized":False,
    },
    "prior_research":{
        "required_exp015_stage":"REVIEW","exp015_frozen_evidence":EXP015_FROZEN_EVIDENCE,
        "exp015_result_must_verify_locally":True,"exp005_through_exp015_must_remain_frozen":True,
        "quantower_reference_is_read_only":True,"existing_data_hashes_must_not_change":True,
        "existing_strategy_results_must_not_change":True,
    },
    "access_safety":{
        "official_client_only":True,"client_distribution":"lse-data","client_version":"0.14.0",
        "isolated_environment_only":True,"main_project_venv_install_prohibited":True,
        "api_key_environment_variable":"LSE_API_KEY","api_key_must_not_be_printed":True,
        "api_key_must_not_be_written":True,"website_scraping_prohibited":True,
        "raw_downloads_local_and_gitignored":True,"maximum_remote_history_requests_per_run":6,
        "one_request_per_window":True,"catalog_rerun_prohibited":True,
    },
    "methodology_boundary":{
        "nq_f_is_candidate_not_resolved_identity":True,"contract_type":"UNRESOLVED",
        "continuous_series_method":"UNRESOLVED","roll_method":"UNRESOLVED",
        "price_adjustment":"UNRESOLVED","timestamp_timezone":"UNRESOLVED",
        "volume_semantics":"UNRESOLVED","missing_methodology_must_remain_visible":True,
        "no_inference_from_symbol_suffix":True,
    },
    "sample_plan":{
        "sample_windows":FIXED_SAMPLE_WINDOWS,"sample_window_count":6,
        "windows_locked_before_history_access":True,"window_changes_after_results_prohibited":True,
        "requested_resolution":"1m","vendor_symbol":"NQ.F","reference_market":"Frozen Quantower NQ",
        "full_2020_2025_vendor_download_prohibited":True,"raw_response_hash_required":True,
        "normalized_sample_hash_required":True,"normalization_must_not_fill_delete_or_repair_bars":True,
    },
    "measurements":{
        "timestamp_order_uniqueness_timezone":True,"ohlcv_numeric_finite":True,
        "ohlc_invariants":True,"negative_volume":True,"expected_missing_unexpected_minutes":True,
        "session_completeness":True,"dst_holiday_roll_diagnostics":True,
        "match_on_utc_minute":True,"matched_vendor_only_quantower_only_counts":True,
        "ohlc_absolute_differences":True,"difference_buckets_points":[0.0,0.25,1.0,"infinity"],
        "close_within_one_tick_share":True,"volume_difference_descriptive_only":True,
        "largest_discrepancy_rows":100,"roll_windows_separate":True,
        "no_silent_row_exclusion":True,"no_automatic_price_offset":True,
    },
    "interpretation":{
        "classifications":["ACCESS_UNAVAILABLE","STRUCTURE_UNRESOLVED","NOT_QUALIFIED","SUPPLEMENTARY_ONLY","QUALIFIED_AS_SUPPLEMENTARY_NQ_SOURCE"],
        "highest_possible_classification":"QUALIFIED_AS_SUPPLEMENTARY_NQ_SOURCE",
        "cannot_qualify_primary_source":True,"cannot_qualify_mnq":True,"cannot_qualify_other_assets":True,
        "requirements":{
            "all_six_windows_downloaded":True,"timestamp_semantics_resolved":True,
            "duplicate_timestamps":0,"invalid_ohlc_rows":0,"negative_volume_rows":0,
            "minimum_expected_minute_completeness":0.999,
            "minimum_matched_timestamp_share":0.999,
            "minimum_close_within_one_tick_share_outside_roll_windows":0.995,
        },
        "methodology_unresolved_forces_at_most":"SUPPLEMENTARY_ONLY",
        "expected_lifecycle_after_measurement":"REVIEW",
        "paper_trading_authorized":False,"live_trading_authorized":False,
    },
}

def get_exp016_preregistration():
    return deepcopy(EXP016_PREREGISTRATION)

def validate_exp016_preregistration(record=None):
    r = EXP016_PREREGISTRATION if record is None else record
    if (r.get("schema_version")!=1 or r.get("experiment_id")!="EXP-016" or
        r.get("research_status")!="PRE_REGISTERED" or r.get("implementation_status")!="NOT_RUN" or
        r.get("results_viewed")!="NONE"):
        raise ValueError("EXP-016 identity changed.")
    s=r["scope"]
    if not (s["market"]=="NQ only" and s["vendor_symbol"]=="NQ.F" and s["timeframe"]=="1m" and
            s["sample_audit_only"] is True and s["full_history_download_prohibited"] is True and
            s["mnq_out_of_scope"] is True and s["primary_source_replacement_prohibited"] is True and
            s["strategy_replay_prohibited"] is True and s["strategy_optimization_prohibited"] is True and
            s["paper_trading_authorized"] is False and s["live_trading_authorized"] is False):
        raise ValueError("EXP-016 scope changed.")
    p=r["prior_research"]
    if not (p["required_exp015_stage"]=="REVIEW" and p["exp015_frozen_evidence"]==EXP015_FROZEN_EVIDENCE and
            p["exp015_result_must_verify_locally"] is True and p["exp005_through_exp015_must_remain_frozen"] is True and
            p["quantower_reference_is_read_only"] is True and p["existing_data_hashes_must_not_change"] is True and
            p["existing_strategy_results_must_not_change"] is True):
        raise ValueError("EXP-016 prior research protection changed.")
    a=r["access_safety"]
    if not (a["official_client_only"] is True and a["client_version"]=="0.14.0" and
            a["isolated_environment_only"] is True and a["main_project_venv_install_prohibited"] is True and
            a["api_key_environment_variable"]=="LSE_API_KEY" and a["api_key_must_not_be_printed"] is True and
            a["api_key_must_not_be_written"] is True and a["website_scraping_prohibited"] is True and
            a["maximum_remote_history_requests_per_run"]==6 and a["one_request_per_window"] is True and
            a["catalog_rerun_prohibited"] is True):
        raise ValueError("EXP-016 access safety changed.")
    m=r["methodology_boundary"]
    if not (m["nq_f_is_candidate_not_resolved_identity"] is True and m["contract_type"]=="UNRESOLVED" and
            m["roll_method"]=="UNRESOLVED" and m["price_adjustment"]=="UNRESOLVED" and
            m["missing_methodology_must_remain_visible"] is True and m["no_inference_from_symbol_suffix"] is True):
        raise ValueError("EXP-016 methodology boundary changed.")
    sp=r["sample_plan"]
    if not (tuple(sp["sample_windows"])==FIXED_SAMPLE_WINDOWS and sp["sample_window_count"]==6 and
            sp["windows_locked_before_history_access"] is True and sp["window_changes_after_results_prohibited"] is True and
            sp["requested_resolution"]=="1m" and sp["vendor_symbol"]=="NQ.F" and
            sp["full_2020_2025_vendor_download_prohibited"] is True and
            sp["normalization_must_not_fill_delete_or_repair_bars"] is True):
        raise ValueError("EXP-016 sample plan changed.")
    q=r["interpretation"]; req=q["requirements"]
    if not (q["highest_possible_classification"]=="QUALIFIED_AS_SUPPLEMENTARY_NQ_SOURCE" and
            q["cannot_qualify_primary_source"] is True and q["cannot_qualify_mnq"] is True and
            req["duplicate_timestamps"]==0 and req["invalid_ohlc_rows"]==0 and req["negative_volume_rows"]==0 and
            req["minimum_expected_minute_completeness"]==0.999 and req["minimum_matched_timestamp_share"]==0.999 and
            req["minimum_close_within_one_tick_share_outside_roll_windows"]==0.995 and
            q["methodology_unresolved_forces_at_most"]=="SUPPLEMENTARY_ONLY" and
            q["expected_lifecycle_after_measurement"]=="REVIEW" and
            q["paper_trading_authorized"] is False and q["live_trading_authorized"] is False):
        raise ValueError("EXP-016 interpretation changed.")
