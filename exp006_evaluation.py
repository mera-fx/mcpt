from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from exp006_candidate_scoring import BASELINE
from exp006_orb import OrbParameters
from exp006_walk_forward import WalkForwardResult


@dataclass(frozen=True)
class Exp006Evaluation:
    decision: str
    passed: bool
    gates: dict[str, dict[str, Any]]
    failed_gates: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "passed": self.passed,
            "gates": self.gates,
            "failed_gates": list(
                self.failed_gates
            ),
        }


def evaluate_exp006(
    *,
    selected_parameters: OrbParameters | None,
    selected_row: pd.Series | None,
    baseline_row: pd.Series,
    walk_forward: WalkForwardResult,
    selection_mcpt_p_value: float,
) -> Exp006Evaluation:
    gates: dict[str, dict[str, Any]] = {}

    def add(
        name: str,
        *,
        actual: Any,
        operator: str,
        threshold: Any,
        passed: bool,
    ) -> None:
        gates[name] = {
            "actual": actual,
            "operator": operator,
            "threshold": threshold,
            "passed": bool(passed),
        }

    has_candidate = (
        selected_parameters is not None
        and selected_row is not None
    )
    add(
        "selected_candidate_exists",
        actual=bool(has_candidate),
        operator="==",
        threshold=True,
        passed=has_candidate,
    )

    differs = (
        has_candidate
        and selected_parameters != BASELINE
    )
    add(
        "selected_candidate_differs_from_exp005",
        actual=(
            selected_parameters.to_dict()
            if selected_parameters is not None
            else None
        ),
        operator="!=",
        threshold=BASELINE.to_dict(),
        passed=bool(differs),
    )

    eligible = bool(
        selected_row["eligible"]
        if has_candidate
        else False
    )
    stable = bool(
        selected_row["neighbor_stable"]
        if has_candidate
        else False
    )
    add(
        "selected_candidate_eligible",
        actual=eligible,
        operator="==",
        threshold=True,
        passed=eligible,
    )
    add(
        "neighbor_stability",
        actual=(
            float(
                selected_row[
                    "profitable_neighbor_share"
                ]
            )
            if has_candidate
            else None
        ),
        operator=">=",
        threshold=0.50,
        passed=stable,
    )

    profitable_folds = int(
        walk_forward.profitable_nq_test_folds
    )
    add(
        "profitable_walk_forward_nq_folds",
        actual=profitable_folds,
        operator=">=",
        threshold=3,
        passed=profitable_folds >= 3,
    )
    add(
        "walk_forward_nq_net_profit_usd",
        actual=float(
            walk_forward.total_nq_net_profit_usd
        ),
        operator=">",
        threshold=0.0,
        passed=(
            walk_forward.total_nq_net_profit_usd
            > 0.0
        ),
    )
    add(
        "walk_forward_mnq_net_profit_usd",
        actual=float(
            walk_forward.total_mnq_net_profit_usd
        ),
        operator=">",
        threshold=0.0,
        passed=(
            walk_forward.total_mnq_net_profit_usd
            > 0.0
        ),
    )

    add(
        "selection_aware_mcpt_p_value",
        actual=float(selection_mcpt_p_value),
        operator="<=",
        threshold=0.05,
        passed=float(selection_mcpt_p_value)
        <= 0.05,
    )

    selected_pf = (
        float(
            selected_row[
                "nq_trade_profit_factor"
            ]
        )
        if has_candidate
        else float("nan")
    )
    baseline_pf = float(
        baseline_row["nq_trade_profit_factor"]
    )
    pf_improvement = selected_pf - baseline_pf
    add(
        "nq_profit_factor_improvement",
        actual=pf_improvement,
        operator=">=",
        threshold=0.02,
        passed=np.isfinite(pf_improvement)
        and pf_improvement >= 0.02,
    )

    selected_drawdown = (
        abs(
            float(
                selected_row[
                    "nq_maximum_drawdown_usd"
                ]
            )
        )
        if has_candidate
        else float("inf")
    )
    baseline_drawdown = abs(
        float(
            baseline_row[
                "nq_maximum_drawdown_usd"
            ]
        )
    )
    drawdown_ratio = (
        selected_drawdown / baseline_drawdown
        if baseline_drawdown > 0
        else float("inf")
    )
    add(
        "nq_drawdown_increase_fraction",
        actual=drawdown_ratio - 1.0,
        operator="<=",
        threshold=0.20,
        passed=drawdown_ratio <= 1.20,
    )

    mnq_pf = (
        float(
            selected_row[
                "mnq_trade_profit_factor"
            ]
        )
        if has_candidate
        else float("nan")
    )
    add(
        "mnq_trade_profit_factor",
        actual=mnq_pf,
        operator=">",
        threshold=1.0,
        passed=np.isfinite(mnq_pf)
        and mnq_pf > 1.0,
    )

    failed = tuple(
        name
        for name, gate in gates.items()
        if not gate["passed"]
    )
    passed = not failed
    return Exp006Evaluation(
        decision=(
            "LOCK_CANDIDATE_FOR_FORWARD_PAPER_COMPARISON"
            if passed
            else "REJECT_EXP006_KEEP_EXP005_CONTROL"
        ),
        passed=passed,
        gates=gates,
        failed_gates=failed,
    )
