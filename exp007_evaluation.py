from __future__ import annotations

from typing import Any

import pandas as pd


PASS_DECISION = (
    "LOCK_FIXED_EXP007_CANDIDATE_FOR_FORWARD_PAPER_COMPARISON"
)
FAIL_DECISION = "REJECT_EXP007_PRESERVE_AS_NEGATIVE_RESULT"


def _gate(
    actual: Any,
    operator: str,
    threshold: Any,
    passed: bool,
) -> dict[str, Any]:
    return {
        "actual": actual,
        "operator": operator,
        "threshold": threshold,
        "passed": bool(passed),
    }


def evaluate_exp007(
    *,
    nq_summary: dict[str, Any],
    mnq_summary: dict[str, Any],
    nq_yearly_results: pd.DataFrame,
    nq_two_tick_summary: dict[str, Any],
    mcpt_p_value: float,
) -> dict[str, Any]:
    annual = nq_yearly_results[
        nq_yearly_results["year"].between(2021, 2025)
    ].copy()
    if len(annual) != 5:
        raise ValueError(
            "EXP-007 requires all five annual evaluation blocks."
        )

    profitable_blocks = int((annual["net_profit_usd"] > 0.0).sum())
    combined_annual_net = float(annual["net_profit_usd"].sum())

    gates = {
        "nq_trade_profit_factor": _gate(
            float(nq_summary["trade_profit_factor"]),
            ">",
            1.0,
            float(nq_summary["trade_profit_factor"]) > 1.0,
        ),
        "nq_net_profit_usd": _gate(
            float(nq_summary["net_profit_usd"]),
            ">",
            0.0,
            float(nq_summary["net_profit_usd"]) > 0.0,
        ),
        "nq_average_trade_usd": _gate(
            float(nq_summary["average_trade_usd"]),
            ">",
            0.0,
            float(nq_summary["average_trade_usd"]) > 0.0,
        ),
        "nq_completed_trades": _gate(
            int(nq_summary["completed_trades"]),
            ">=",
            500,
            int(nq_summary["completed_trades"]) >= 500,
        ),
        "profitable_nq_annual_blocks": _gate(
            profitable_blocks,
            ">=",
            3,
            profitable_blocks >= 3,
        ),
        "combined_2021_2025_nq_net_profit_usd": _gate(
            combined_annual_net,
            ">",
            0.0,
            combined_annual_net > 0.0,
        ),
        "nq_session_aware_mcpt_p_value": _gate(
            float(mcpt_p_value),
            "<=",
            0.05,
            float(mcpt_p_value) <= 0.05,
        ),
        "nq_two_tick_stress_net_profit_usd": _gate(
            float(nq_two_tick_summary["net_profit_usd"]),
            ">",
            0.0,
            float(nq_two_tick_summary["net_profit_usd"]) > 0.0,
        ),
        "mnq_trade_profit_factor": _gate(
            float(mnq_summary["trade_profit_factor"]),
            ">",
            1.0,
            float(mnq_summary["trade_profit_factor"]) > 1.0,
        ),
        "mnq_net_profit_usd": _gate(
            float(mnq_summary["net_profit_usd"]),
            ">",
            0.0,
            float(mnq_summary["net_profit_usd"]) > 0.0,
        ),
    }

    failed = [name for name, gate in gates.items() if not gate["passed"]]
    passed = not failed
    return {
        "decision": PASS_DECISION if passed else FAIL_DECISION,
        "passed": passed,
        "failed_gates": failed,
        "gates": gates,
        "profitable_nq_annual_blocks": profitable_blocks,
        "combined_2021_2025_nq_net_profit_usd": combined_annual_net,
        "profit_factor_improvement_vs_exp005_required": False,
        "live_trading_authorized": False,
    }
