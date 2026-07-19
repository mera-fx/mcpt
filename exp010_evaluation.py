from __future__ import annotations

from typing import Any, Mapping

import pandas as pd


def _positive(summary: Mapping[str, Any], field: str) -> bool:
    return float(summary[field]) > 0.0


def evaluate_exp010_evidence(
    *,
    nq_summary: Mapping[str, Any],
    mnq_summary: Mapping[str, Any],
    nq_two_tick_summary: Mapping[str, Any],
    walk_forward: pd.DataFrame,
    selection_aware_mcpt_p_value: float,
) -> dict[str, Any]:
    profitable_folds = int(
        (walk_forward["test_net_profit_usd"].astype(float) > 0).sum()
    )
    combined_walk_forward = float(
        walk_forward["test_net_profit_usd"].astype(float).sum()
    )
    common = {
        "combined_walk_forward_net_profit_positive": (
            combined_walk_forward > 0.0
        ),
        "selected_nq_profit_factor_above_one": (
            float(nq_summary["trade_profit_factor"]) > 1.0
        ),
        "two_tick_nq_net_profit_positive": _positive(
            nq_two_tick_summary, "net_profit_usd"
        ),
    }
    strong = {
        **common,
        "selection_aware_mcpt_p_value_at_most_0p05": (
            float(selection_aware_mcpt_p_value) <= 0.05
        ),
        "at_least_four_profitable_walk_forward_folds": (
            profitable_folds >= 4
        ),
        "selected_mnq_profit_factor_above_one": (
            float(mnq_summary["trade_profit_factor"]) > 1.0
        ),
    }
    promising = {
        **common,
        "selection_aware_mcpt_p_value_at_most_0p10": (
            float(selection_aware_mcpt_p_value) <= 0.10
        ),
        "at_least_three_profitable_walk_forward_folds": (
            profitable_folds >= 3
        ),
    }
    if all(strong.values()):
        classification = "STRONG_HISTORICAL_EVIDENCE"
    elif all(promising.values()):
        classification = "PROMISING_BUT_UNCERTAIN"
    else:
        classification = "WEAK_OR_INCONCLUSIVE_HISTORICAL_EVIDENCE"

    return {
        "classification": classification,
        "classification_is_secondary": True,
        "measurement_first": True,
        "strong_context_checks": strong,
        "promising_context_checks": promising,
        "profitable_walk_forward_folds": profitable_folds,
        "combined_walk_forward_net_profit_usd": combined_walk_forward,
        "selection_aware_mcpt_p_value": float(
            selection_aware_mcpt_p_value
        ),
        "lifecycle_accept_reject_decision": None,
        "paper_trading_authorized": False,
        "live_trading_authorized": False,
    }
