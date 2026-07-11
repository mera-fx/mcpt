from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from exp003_preregistration import (
    get_exp003_preregistration,
)


@dataclass(frozen=True)
class FullValidationEvaluation:
    decision: str
    passed: bool
    gates: dict[str, dict[str, Any]]
    failed_gates: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "passed": self.passed,
            "gates": self.gates,
            "failed_gates": self.failed_gates,
        }


def calculate_profitable_calendar_years(
    equity_curve: pd.DataFrame,
    *,
    starting_capital: float,
) -> tuple[int, pd.DataFrame]:
    """
    Count profitable calendar years using year-end equity.

    The first partial OOS year is measured from starting capital.
    Each later year is measured from the prior calendar year's final
    equity. This rule is locked before EXP-003 OOS results are viewed.
    """

    if "equity" not in equity_curve.columns:
        raise ValueError(
            "Equity curve must contain an 'equity' column."
        )

    if not isinstance(
        equity_curve.index,
        pd.DatetimeIndex,
    ):
        raise TypeError(
            "Equity curve index must be a DatetimeIndex."
        )

    clean = equity_curve[
        ["equity"]
    ].dropna().sort_index()

    if clean.empty:
        return 0, pd.DataFrame(
            columns=[
                "year",
                "starting_equity",
                "ending_equity",
                "return_percent",
                "profitable",
            ]
        )

    rows: list[dict[str, Any]] = []
    prior_ending_equity = float(
        starting_capital
    )

    for year, group in clean.groupby(
        clean.index.year
    ):
        ending_equity = float(
            group["equity"].iloc[-1]
        )

        return_percent = (
            ending_equity
            / prior_ending_equity
            - 1.0
        ) * 100.0

        rows.append(
            {
                "year": int(year),
                "starting_equity": (
                    prior_ending_equity
                ),
                "ending_equity": ending_equity,
                "return_percent": (
                    return_percent
                ),
                "profitable": bool(
                    return_percent > 0.0
                ),
            }
        )

        prior_ending_equity = ending_equity

    table = pd.DataFrame(rows)

    count = int(
        table["profitable"].sum()
    )

    return count, table


def evaluate_exp003_full_validation(
    *,
    summary: pd.DataFrame,
    mcpt_p_value: float,
    mcpt_permutations: int,
    mcpt_source: str,
    profitable_calendar_years: int,
) -> FullValidationEvaluation:
    preregistration = (
        get_exp003_preregistration()
    )

    thresholds = preregistration[
        "full_validation"
    ]["gates"]

    required_rows = {
        "Fixed parameters",
        "Walk-forward",
    }

    missing_rows = required_rows.difference(
        summary.index
    )

    if missing_rows:
        raise ValueError(
            "Full-validation summary is missing rows: "
            f"{sorted(missing_rows)}"
        )

    fixed = summary.loc[
        "Fixed parameters"
    ]

    walkforward = summary.loc[
        "Walk-forward"
    ]

    raw_gates = {
        "full_mcpt_p_value": {
            "actual": float(mcpt_p_value),
            "operator": "<=",
            "threshold": float(
                thresholds[
                    "maximum_full_mcpt_p_value"
                ]
            ),
            "passed": bool(
                mcpt_p_value
                <= thresholds[
                    "maximum_full_mcpt_p_value"
                ]
            ),
        },
        "full_mcpt_permutations": {
            "actual": int(mcpt_permutations),
            "operator": ">=",
            "threshold": int(
                preregistration[
                    "statistical_plan"
                ]["full_mcpt_permutations"]
            ),
            "passed": bool(
                mcpt_permutations
                >= preregistration[
                    "statistical_plan"
                ]["full_mcpt_permutations"]
            ),
        },
        "full_mcpt_source": {
            "actual": str(mcpt_source),
            "operator": "==",
            "threshold": "full_run",
            "passed": bool(
                mcpt_source == "full_run"
            ),
        },
        "fixed_oos_total_return_percent": {
            "actual": float(
                fixed[
                    "total_return_percent"
                ]
            ),
            "operator": ">",
            "threshold": float(
                thresholds[
                    "minimum_fixed_oos_total_return_percent"
                ]
            ),
            "passed": bool(
                fixed[
                    "total_return_percent"
                ]
                > thresholds[
                    "minimum_fixed_oos_total_return_percent"
                ]
            ),
        },
        "fixed_oos_trade_profit_factor": {
            "actual": float(
                fixed[
                    "trade_profit_factor"
                ]
            ),
            "operator": ">",
            "threshold": float(
                thresholds[
                    "minimum_fixed_oos_trade_profit_factor"
                ]
            ),
            "passed": bool(
                fixed[
                    "trade_profit_factor"
                ]
                > thresholds[
                    "minimum_fixed_oos_trade_profit_factor"
                ]
            ),
        },
        "fixed_oos_completed_trades": {
            "actual": int(
                fixed["total_trades"]
            ),
            "operator": ">=",
            "threshold": int(
                thresholds[
                    "minimum_fixed_oos_completed_trades"
                ]
            ),
            "passed": bool(
                fixed["total_trades"]
                >= thresholds[
                    "minimum_fixed_oos_completed_trades"
                ]
            ),
        },
        "walkforward_total_return_percent": {
            "actual": float(
                walkforward[
                    "total_return_percent"
                ]
            ),
            "operator": ">",
            "threshold": float(
                thresholds[
                    "minimum_walkforward_total_return_percent"
                ]
            ),
            "passed": bool(
                walkforward[
                    "total_return_percent"
                ]
                > thresholds[
                    "minimum_walkforward_total_return_percent"
                ]
            ),
        },
        "walkforward_trade_profit_factor": {
            "actual": float(
                walkforward[
                    "trade_profit_factor"
                ]
            ),
            "operator": ">",
            "threshold": float(
                thresholds[
                    "minimum_walkforward_trade_profit_factor"
                ]
            ),
            "passed": bool(
                walkforward[
                    "trade_profit_factor"
                ]
                > thresholds[
                    "minimum_walkforward_trade_profit_factor"
                ]
            ),
        },
        "walkforward_completed_trades": {
            "actual": int(
                walkforward["total_trades"]
            ),
            "operator": ">=",
            "threshold": int(
                thresholds[
                    "minimum_walkforward_completed_trades"
                ]
            ),
            "passed": bool(
                walkforward["total_trades"]
                >= thresholds[
                    "minimum_walkforward_completed_trades"
                ]
            ),
        },
        "fixed_oos_absolute_max_drawdown_percent": {
            "actual": abs(
                float(
                    fixed[
                        "max_drawdown_percent"
                    ]
                )
            ),
            "operator": "<=",
            "threshold": float(
                thresholds[
                    "maximum_absolute_fixed_oos_drawdown_percent"
                ]
            ),
            "passed": bool(
                abs(
                    fixed[
                        "max_drawdown_percent"
                    ]
                )
                <= thresholds[
                    "maximum_absolute_fixed_oos_drawdown_percent"
                ]
            ),
        },
        "profitable_oos_calendar_years": {
            "actual": int(
                profitable_calendar_years
            ),
            "operator": ">=",
            "threshold": int(
                thresholds[
                    "minimum_profitable_oos_calendar_years"
                ]
            ),
            "passed": bool(
                profitable_calendar_years
                >= thresholds[
                    "minimum_profitable_oos_calendar_years"
                ]
            ),
        },
    }

    failed = [
        gate_name
        for gate_name, gate
        in raw_gates.items()
        if not gate["passed"]
    ]

    passed = not failed

    decision = (
        "PASS_TO_REVIEW"
        if passed
        else "REJECT"
    )

    return FullValidationEvaluation(
        decision=decision,
        passed=passed,
        gates=raw_gates,
        failed_gates=failed,
    )
