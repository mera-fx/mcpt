from __future__ import annotations
from copy import deepcopy

CONTRACTS = (
    ("NQH24", "NQH4", 750, "2024-03-15T13:30:00+00:00", 0.050133),
    ("NQM24", "NQM4", 13743, "2024-06-21T13:30:00+00:00", 0.049921),
    ("NQU24", "NQU4", 4358, "2024-09-20T13:30:00+00:00", 0.049943),
    ("NQZ24", "NQZ4", 106364, "2024-12-20T14:30:00+00:00", 0.053499),
    ("NQH25", "NQH5", 42288528, "2025-03-21T13:30:00+00:00", 0.030009),
    ("NQM25", "NQM5", 42005804, "2025-06-20T13:30:00+00:00", 0.049943),
)

EXP017_CLOSURE = {
    "schema_version": 1,
    "experiment_id": "EXP-017",
    "closed_date": "2026-07-22",
    "research_status": "REVIEW",
    "classification": "ACCESS_INCOMPLETE",
    "benchmark_bar_values_viewed": "NONE",
    "ohlcv_requested": False,
    "ohlcv_downloaded": False,
    "reason": (
        "The locked benchmark required two accessible exact-contract sources. "
        "Databento passed metadata and identity checks, but no second affordable "
        "source was available."
    ),
    "databento": {
        "client_version": "0.81.0",
        "dataset": "GLBX.MDP3",
        "contracts": CONTRACTS,
        "combined_bar_cost_estimate_usd": 0.283447,
        "combined_definition_cost_estimate_usd": 0.000003420,
        "definitions_confirmed": True,
        "exchange": "XCME",
        "asset": "NQ",
        "security_type": "FUT",
        "tick_points": 0.25,
        "point_value_usd": 20.0,
        "tick_value_usd": 5.0,
        "price_accuracy_verified": False,
    },
    "cme_datamine": {
        "dataset_code": "MD_XCME_NQ_FUT_0",
        "exchange_native": True,
        "prebuilt_one_minute_ohlcv_confirmed": False,
        "complete_history_price_usd": 18558.0,
        "annual_subscription_price_usd": 4257.0,
        "user_budget_accessible": False,
        "ordered": False,
        "sample_downloaded": False,
        "benchmark_eligible": False,
    },
    "other_sources": {
        "lucid_rithmic_exact_expired_contracts_available": False,
        "london_exact_expired_contracts_identified": False,
        "website_scraping_used": False,
    },
    "requirement_result": {
        "minimum_sources_required": 2,
        "accessible_sources_confirmed": 1,
        "minimum_met": False,
        "comparison_performed": False,
        "winner_selected": False,
    },
    "interpretation": {
        "databento_structure_untested": True,
        "databento_repeatability_untested": True,
        "exchange_accuracy_not_established": True,
        "prior_experiments_frozen": True,
        "paper_trading_authorized": False,
        "live_trading_authorized": False,
    },
}

def get_exp017_closure():
    return deepcopy(EXP017_CLOSURE)

def validate_exp017_closure(record=None):
    r = EXP017_CLOSURE if record is None else record
    if (
        r["experiment_id"] != "EXP-017"
        or r["research_status"] != "REVIEW"
        or r["classification"] != "ACCESS_INCOMPLETE"
        or r["benchmark_bar_values_viewed"] != "NONE"
        or r["ohlcv_requested"]
        or r["ohlcv_downloaded"]
    ):
        raise ValueError("EXP-017 closure identity changed.")
    if len(r["databento"]["contracts"]) != 6:
        raise ValueError("EXP-017 contract evidence changed.")
    if r["databento"]["combined_bar_cost_estimate_usd"] != 0.283447:
        raise ValueError("EXP-017 Databento estimate changed.")
    if r["cme_datamine"]["user_budget_accessible"]:
        raise ValueError("EXP-017 CME access finding changed.")
    result = r["requirement_result"]
    if (
        result["minimum_sources_required"] != 2
        or result["accessible_sources_confirmed"] != 1
        or result["minimum_met"]
        or result["comparison_performed"]
        or result["winner_selected"]
    ):
        raise ValueError("EXP-017 requirement result changed.")
    if not r["interpretation"]["exchange_accuracy_not_established"]:
        raise ValueError("EXP-017 interpretation changed.")
