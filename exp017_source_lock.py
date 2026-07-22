from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

LOCKED_CONTRACTS = (
    "NQH24", "NQM24", "NQU24", "NQZ24", "NQH25", "NQM25",
)

EXP017_SOURCE_SET_LOCK: dict[str, Any] = {
    "schema_version": 1,
    "experiment_id": "EXP-017",
    "record_type": "PRICE_FREE_SOURCE_SET_LOCK",
    "locked_date": "2026-07-22",
    "lock_status": "SOURCE_SET_LOCKED_METADATA_PENDING",
    "benchmark_bar_values_viewed": "NONE",
    "remote_market_data_request_performed": False,
    "benchmark_bar_access_authorized": False,
    "locked_contracts": LOCKED_CONTRACTS,
    "source_roles": {
        "execution_feed_context": {
            "source_id": "lucid_rithmic_quantower",
            "platform": "Quantower",
            "account_provider": "Lucid Trading",
            "connection_technology": "Rithmic",
            "account_context": "evaluation account",
            "existing_export_symbols": ("NQ", "MNQ"),
            "existing_export_character": "generic front-month multi-contract series",
            "front_month_label_observed": True,
            "locked_expired_contract_search_names": (
                "NQH4", "NQM4", "NQU4", "NQZ4", "NQH5", "NQM5",
            ),
            "locked_expired_contracts_found": False,
            "exact_contract_benchmark_eligible": False,
            "execution_feed_alignment_context": True,
            "ground_truth_assumed": False,
            "existing_research_files_frozen": True,
        },
        "historical_exact_contract_candidate": {
            "source_id": "databento_glbx_mdp3",
            "provider": "Databento",
            "dataset": "GLBX.MDP3",
            "exchange_origin": "CME Globex MDP 3.0",
            "historical_coverage_documented_from": "2010-06",
            "exact_child_contract_capability_documented": True,
            "parent_symbol_for_discovery": "NQ.FUT",
            "definition_schema_required": True,
            "api_required_for_individual_child_contracts": True,
            "source_specific_aliases_resolved": False,
            "contract_expiry_identity_resolved": False,
            "timestamp_and_bar_semantics_resolved": False,
            "account_available": "UNVERIFIED",
            "entitlement_available": "UNVERIFIED",
            "license_review": "PENDING",
            "quoted_cost": "PENDING_METADATA_ESTIMATE",
            "bar_values_accessed": False,
            "eligibility": "PENDING_METADATA_CONFIRMATION",
        },
        "exchange_native_reference_candidate": {
            "source_id": "cme_datamine",
            "provider": "CME Group",
            "service": "CME DataMine",
            "source_character": "exchange-native historical data service",
            "historical_futures_and_options_supported": True,
            "delivery_methods": ("API", "SFTP", "S3", "Email"),
            "purchase_or_entitlement_required": True,
            "license_required": True,
            "exact_nq_one_minute_product_confirmed": False,
            "source_specific_aliases_resolved": False,
            "contract_expiry_identity_resolved": False,
            "timestamp_and_bar_semantics_resolved": False,
            "account_available": "UNVERIFIED",
            "entitlement_available": "UNVERIFIED",
            "quoted_cost": "PENDING_CATALOG_OR_SALES_CONFIRMATION",
            "bar_values_accessed": False,
            "eligibility": "PENDING_COMMERCIAL_AND_METADATA_CONFIRMATION",
        },
    },
    "excluded_sources": {
        "london_strategic_edge_nq_f": {
            "reason": (
                "EXP-015 identified only the unresolved NQ.F candidate and "
                "did not identify exact expired NQ contracts."
            ),
            "continuous_candidate_only": True,
            "exact_contract_identity_resolved": False,
            "included_in_exp017_benchmark": False,
            "reentry_after_this_lock": False,
        },
    },
    "truth_boundary": {
        "quantower_assumed_ground_truth": False,
        "lucid_rithmic_assumed_ground_truth": False,
        "databento_assumed_ground_truth": False,
        "cme_datamine_reference_preferred": True,
        "two_disagreeing_nonexchange_sources_can_select_winner": False,
        "exchange_reference_required_for_absolute_accuracy_language": True,
        "best_available_without_exchange_reference_is_relative_only": True,
    },
    "next_metadata_only_stage": {
        "databento_definition_resolution_authorized": True,
        "databento_cost_estimate_authorized": True,
        "databento_ohlcv_request_authorized": False,
        "cme_datamine_catalog_or_sales_confirmation_authorized": True,
        "cme_datamine_file_download_authorized": False,
        "final_source_eligibility_lock_required_before_bars": True,
        "source_substitution_after_bar_access_prohibited": True,
    },
    "research_boundary": {
        "exp005_through_exp016_frozen": True,
        "existing_quantower_files_changed": False,
        "existing_strategy_results_changed": False,
        "full_history_download_authorized": False,
        "continuous_series_construction_authorized": False,
        "strategy_replay_authorized": False,
        "strategy_optimization_authorized": False,
        "paper_trading_authorized": False,
        "live_trading_authorized": False,
    },
}


def get_exp017_source_set_lock() -> dict[str, Any]:
    return deepcopy(EXP017_SOURCE_SET_LOCK)


def validate_exp017_source_set_lock(
    record: Mapping[str, Any] | None = None,
) -> None:
    current = EXP017_SOURCE_SET_LOCK if record is None else dict(record)
    if (
        current.get("schema_version") != 1
        or current.get("experiment_id") != "EXP-017"
        or current.get("record_type") != "PRICE_FREE_SOURCE_SET_LOCK"
        or current.get("lock_status") != "SOURCE_SET_LOCKED_METADATA_PENDING"
        or current.get("benchmark_bar_values_viewed") != "NONE"
        or current.get("remote_market_data_request_performed") is not False
        or current.get("benchmark_bar_access_authorized") is not False
        or tuple(current.get("locked_contracts", ())) != LOCKED_CONTRACTS
    ):
        raise ValueError("EXP-017 source-set lock identity changed.")

    roles = current["source_roles"]
    execution = roles["execution_feed_context"]
    if (
        execution["platform"] != "Quantower"
        or execution["account_provider"] != "Lucid Trading"
        or execution["connection_technology"] != "Rithmic"
        or execution["account_context"] != "evaluation account"
        or tuple(execution["existing_export_symbols"]) != ("NQ", "MNQ")
        or execution["locked_expired_contracts_found"] is not False
        or execution["exact_contract_benchmark_eligible"] is not False
        or execution["execution_feed_alignment_context"] is not True
        or execution["ground_truth_assumed"] is not False
    ):
        raise ValueError("EXP-017 execution context changed.")

    databento = roles["historical_exact_contract_candidate"]
    if (
        databento["dataset"] != "GLBX.MDP3"
        or databento["parent_symbol_for_discovery"] != "NQ.FUT"
        or databento["exact_child_contract_capability_documented"] is not True
        or databento["api_required_for_individual_child_contracts"] is not True
        or databento["source_specific_aliases_resolved"] is not False
        or databento["bar_values_accessed"] is not False
        or databento["eligibility"] != "PENDING_METADATA_CONFIRMATION"
    ):
        raise ValueError("EXP-017 Databento candidate changed.")

    cme = roles["exchange_native_reference_candidate"]
    if (
        cme["service"] != "CME DataMine"
        or cme["exact_nq_one_minute_product_confirmed"] is not False
        or cme["bar_values_accessed"] is not False
        or cme["eligibility"] != "PENDING_COMMERCIAL_AND_METADATA_CONFIRMATION"
    ):
        raise ValueError("EXP-017 CME candidate changed.")

    excluded = current["excluded_sources"]["london_strategic_edge_nq_f"]
    if (
        excluded["continuous_candidate_only"] is not True
        or excluded["exact_contract_identity_resolved"] is not False
        or excluded["included_in_exp017_benchmark"] is not False
        or excluded["reentry_after_this_lock"] is not False
    ):
        raise ValueError("EXP-017 excluded-source boundary changed.")

    next_stage = current["next_metadata_only_stage"]
    if (
        next_stage["databento_definition_resolution_authorized"] is not True
        or next_stage["databento_cost_estimate_authorized"] is not True
        or next_stage["databento_ohlcv_request_authorized"] is not False
        or next_stage["cme_datamine_catalog_or_sales_confirmation_authorized"] is not True
        or next_stage["cme_datamine_file_download_authorized"] is not False
        or next_stage["final_source_eligibility_lock_required_before_bars"] is not True
    ):
        raise ValueError("EXP-017 metadata-only boundary changed.")

    research = current["research_boundary"]
    prohibited = (
        "existing_quantower_files_changed",
        "existing_strategy_results_changed",
        "full_history_download_authorized",
        "continuous_series_construction_authorized",
        "strategy_replay_authorized",
        "strategy_optimization_authorized",
        "paper_trading_authorized",
        "live_trading_authorized",
    )
    if any(research[key] is not False for key in prohibited):
        raise ValueError("EXP-017 research boundary changed.")
