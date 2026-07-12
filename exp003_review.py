from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class ReviewEvaluation:
    decision: str
    passed: bool
    checks: dict[str, dict[str, Any]]
    failed_checks: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "passed": self.passed,
            "checks": self.checks,
            "failed_checks": self.failed_checks,
        }


def _check(
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


def evaluate_exp003_review(
    *,
    full_validation_decision: dict[str, Any],
    summary: pd.DataFrame,
    diagnostics: pd.DataFrame,
    parameter_stability: dict[str, Any],
    profitable_calendar_years: int,
) -> ReviewEvaluation:
    """Evaluate locked, read-only paper-testing review checks."""

    fixed = summary.loc["Fixed parameters"]
    walkforward = summary.loc["Walk-forward"]
    buy_hold = summary.loc["Buy and Hold"]

    fixed_diag = diagnostics.loc["Fixed parameters"]
    walkforward_diag = diagnostics.loc["Walk-forward"]

    fixed_drawdown = abs(float(fixed["max_drawdown_percent"]))
    buy_hold_drawdown = abs(float(buy_hold["max_drawdown_percent"]))
    drawdown_improvement = buy_hold_drawdown - fixed_drawdown

    pf_ge_one = int(
        parameter_stability.get(
            "combinations_at_or_above_one",
            parameter_stability.get("pf_ge_1_count", 0),
        )
    )

    total_combinations = int(
        parameter_stability.get(
            "total_combinations",
            parameter_stability.get("combination_count", 0),
        )
    )

    checks = {
        "full_validation_passed": _check(
            full_validation_decision.get("decision"),
            "==",
            "PASS_TO_REVIEW",
            full_validation_decision.get("decision") == "PASS_TO_REVIEW"
            and bool(full_validation_decision.get("passed")),
        ),
        "fixed_and_walkforward_positive": _check(
            [
                float(fixed["total_return_percent"]),
                float(walkforward["total_return_percent"]),
            ],
            ">",
            0.0,
            float(fixed["total_return_percent"]) > 0.0
            and float(walkforward["total_return_percent"]) > 0.0,
        ),
        "fixed_and_walkforward_pf": _check(
            [
                float(fixed["trade_profit_factor"]),
                float(walkforward["trade_profit_factor"]),
            ],
            ">",
            1.0,
            float(fixed["trade_profit_factor"]) > 1.0
            and float(walkforward["trade_profit_factor"]) > 1.0,
        ),
        "adequate_trade_counts": _check(
            [int(fixed["total_trades"]), int(walkforward["total_trades"])],
            ">=",
            30,
            int(fixed["total_trades"]) >= 30
            and int(walkforward["total_trades"]) >= 30,
        ),
        "payoff_ratio_quality": _check(
            [
                float(fixed_diag["payoff_ratio"]),
                float(walkforward_diag["payoff_ratio"]),
            ],
            ">=",
            1.5,
            float(fixed_diag["payoff_ratio"]) >= 1.5
            and float(walkforward_diag["payoff_ratio"]) >= 1.5,
        ),
        "largest_loss_control": _check(
            [
                float(fixed_diag["largest_loss_percent"]),
                float(walkforward_diag["largest_loss_percent"]),
            ],
            ">=",
            -15.0,
            float(fixed_diag["largest_loss_percent"]) >= -15.0
            and float(walkforward_diag["largest_loss_percent"]) >= -15.0,
        ),
        "tail_loss_concentration": _check(
            [
                float(fixed_diag["top_5_loss_share_percent"]),
                float(walkforward_diag["top_5_loss_share_percent"]),
            ],
            "<=",
            35.0,
            float(fixed_diag["top_5_loss_share_percent"]) <= 35.0
            and float(walkforward_diag["top_5_loss_share_percent"]) <= 35.0,
        ),
        "broad_parameter_support": _check(
            [pf_ge_one, total_combinations],
            ">=",
            [6, 27],
            pf_ge_one >= 6 and total_combinations == 27,
        ),
        "profitable_calendar_years": _check(
            profitable_calendar_years,
            ">=",
            2,
            profitable_calendar_years >= 2,
        ),
        "drawdown_improvement_vs_buy_hold": _check(
            drawdown_improvement,
            ">=",
            20.0,
            drawdown_improvement >= 20.0,
        ),
    }

    failed = [
        name for name, result in checks.items()
        if not result["passed"]
    ]

    passed = not failed

    return ReviewEvaluation(
        decision=(
            "ACCEPT_FOR_PAPER_TESTING"
            if passed
            else "REJECT"
        ),
        passed=passed,
        checks=checks,
        failed_checks=failed,
    )
