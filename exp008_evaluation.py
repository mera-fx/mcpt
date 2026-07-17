from __future__ import annotations

from typing import Any

import pandas as pd


PASS_DECISION = (
    "LOCK_EXP008_EXIT_GEOMETRY_CANDIDATE_FOR_"
    "NEW_FORWARD_PAPER_COMPARISON"
)
FAIL_DECISION = (
    "REJECT_EXP008_PRESERVE_AS_NEGATIVE_RESULT"
)
EXP007_BASELINE_NQ_PF = (
    1.1168167521220216
)


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


def evaluate_exp008(
    *,
    selected_row: dict[str, Any] | None,
    nq_summary: dict[str, Any] | None,
    mnq_summary: dict[str, Any] | None,
    nq_yearly_results: pd.DataFrame,
    walk_forward_results: pd.DataFrame,
    nq_two_tick_summary: dict[str, Any] | None,
    mcpt_p_value: float,
) -> dict[str, Any]:
    annual = nq_yearly_results.loc[
        nq_yearly_results[
            "year"
        ].between(2021, 2025)
    ].copy()

    if len(annual) != 5:
        raise ValueError(
            "EXP-008 requires all five final-"
            "candidate annual evaluation blocks."
        )

    if len(walk_forward_results) != 5:
        raise ValueError(
            "EXP-008 requires all five anchored "
            "walk-forward folds."
        )

    selected_exists = (
        selected_row is not None
        and nq_summary is not None
        and mnq_summary is not None
        and nq_two_tick_summary is not None
    )

    profitable_final_years = int(
        (
            annual[
                "net_profit_usd"
            ] > 0.0
        ).sum()
    )
    combined_final_net = float(
        annual[
            "net_profit_usd"
        ].sum()
    )
    profitable_walk_forward = int(
        (
            walk_forward_results[
                "test_net_profit_usd"
            ] > 0.0
        ).sum()
    )
    combined_walk_forward = float(
        walk_forward_results[
            "test_net_profit_usd"
        ].sum()
    )

    if selected_exists:
        nq_pf = float(
            nq_summary[
                "trade_profit_factor"
            ]
        )
        nq_net = float(
            nq_summary[
                "net_profit_usd"
            ]
        )
        nq_average = float(
            nq_summary[
                "average_trade_usd"
            ]
        )
        nq_trades = int(
            nq_summary[
                "completed_trades"
            ]
        )
        mnq_pf = float(
            mnq_summary[
                "trade_profit_factor"
            ]
        )
        mnq_net = float(
            mnq_summary[
                "net_profit_usd"
            ]
        )
        two_tick_net = float(
            nq_two_tick_summary[
                "net_profit_usd"
            ]
        )
        neighbor_stable = bool(
            selected_row[
                "neighbor_stable"
            ]
        )
    else:
        nq_pf = 0.0
        nq_net = 0.0
        nq_average = 0.0
        nq_trades = 0
        mnq_pf = 0.0
        mnq_net = 0.0
        two_tick_net = 0.0
        neighbor_stable = False

    gates = {
        "selected_candidate_neighbor_stable": _gate(
            neighbor_stable,
            "is",
            True,
            neighbor_stable,
        ),
        "selected_nq_trade_profit_factor": _gate(
            nq_pf,
            ">",
            EXP007_BASELINE_NQ_PF,
            nq_pf > EXP007_BASELINE_NQ_PF,
        ),
        "selected_nq_net_profit_usd": _gate(
            nq_net,
            ">",
            0.0,
            nq_net > 0.0,
        ),
        "selected_nq_average_trade_usd": _gate(
            nq_average,
            ">",
            0.0,
            nq_average > 0.0,
        ),
        "selected_nq_completed_trades": _gate(
            nq_trades,
            ">=",
            500,
            nq_trades >= 500,
        ),
        "profitable_final_candidate_nq_years": _gate(
            profitable_final_years,
            ">=",
            3,
            profitable_final_years >= 3,
        ),
        "combined_2021_2025_final_candidate_nq_net_profit_usd": _gate(
            combined_final_net,
            ">",
            0.0,
            combined_final_net > 0.0,
        ),
        "profitable_anchored_test_folds": _gate(
            profitable_walk_forward,
            ">=",
            3,
            profitable_walk_forward >= 3,
        ),
        "combined_anchored_test_fold_nq_net_profit_usd": _gate(
            combined_walk_forward,
            ">",
            0.0,
            combined_walk_forward > 0.0,
        ),
        "selection_aware_nq_mcpt_p_value": _gate(
            float(mcpt_p_value),
            "<=",
            0.05,
            float(mcpt_p_value) <= 0.05,
        ),
        "selected_nq_two_tick_stress_net_profit_usd": _gate(
            two_tick_net,
            ">",
            0.0,
            two_tick_net > 0.0,
        ),
        "selected_mnq_trade_profit_factor": _gate(
            mnq_pf,
            ">",
            1.0,
            mnq_pf > 1.0,
        ),
        "selected_mnq_net_profit_usd": _gate(
            mnq_net,
            ">",
            0.0,
            mnq_net > 0.0,
        ),
    }

    failed = [
        name
        for name, gate in gates.items()
        if not gate["passed"]
    ]
    passed = not failed

    return {
        "decision": (
            PASS_DECISION
            if passed
            else FAIL_DECISION
        ),
        "passed": passed,
        "failed_gates": failed,
        "gates": gates,
        "selected_candidate_exists": (
            selected_exists
        ),
        "profitable_final_candidate_nq_years": (
            profitable_final_years
        ),
        "combined_2021_2025_final_candidate_nq_net_profit_usd": (
            combined_final_net
        ),
        "profitable_anchored_test_folds": (
            profitable_walk_forward
        ),
        "combined_anchored_test_fold_nq_net_profit_usd": (
            combined_walk_forward
        ),
        "profit_factor_comparison_baseline": (
            "FROZEN_EXP007_NQ_TRADE_PROFIT_FACTOR"
        ),
        "frozen_exp007_nq_trade_profit_factor": (
            EXP007_BASELINE_NQ_PF
        ),
        "live_trading_authorized": False,
    }
