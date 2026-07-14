from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from exp005_preregistration import (
    get_exp005_preregistration,
)


@dataclass(frozen=True)
class Exp005FullEvaluation:
    decision: str
    passed: bool
    gates: dict[str, dict[str, Any]]
    failed_gates: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "passed": self.passed,
            "gates": self.gates,
            "failed_gates": list(self.failed_gates),
        }


def evaluate_exp005_full_validation(
    *,
    nq_trade_profit_factor: float,
    mnq_trade_profit_factor: float,
    nq_net_profit_usd: float,
    mnq_net_profit_usd: float,
    nq_mcpt_p_value: float,
    nq_completed_trades: int,
    profitable_nq_calendar_years: int,
    included_invalid_sessions: int,
    included_roll_switch_sessions: int,
) -> Exp005FullEvaluation:
    thresholds = (
        get_exp005_preregistration()[
            "full_validation"
        ]["gates"]
    )
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

    add(
        "nq_trade_profit_factor",
        actual=float(nq_trade_profit_factor),
        operator=">",
        threshold=thresholds[
            "minimum_nq_trade_profit_factor_strict"
        ],
        passed=(
            float(nq_trade_profit_factor)
            > thresholds[
                "minimum_nq_trade_profit_factor_strict"
            ]
        ),
    )
    add(
        "mnq_trade_profit_factor",
        actual=float(mnq_trade_profit_factor),
        operator=">",
        threshold=thresholds[
            "minimum_mnq_trade_profit_factor_strict"
        ],
        passed=(
            float(mnq_trade_profit_factor)
            > thresholds[
                "minimum_mnq_trade_profit_factor_strict"
            ]
        ),
    )
    add(
        "nq_net_profit_usd",
        actual=float(nq_net_profit_usd),
        operator=">",
        threshold=thresholds[
            "minimum_nq_net_profit_usd_strict"
        ],
        passed=(
            float(nq_net_profit_usd)
            > thresholds[
                "minimum_nq_net_profit_usd_strict"
            ]
        ),
    )
    add(
        "mnq_net_profit_usd",
        actual=float(mnq_net_profit_usd),
        operator=">",
        threshold=thresholds[
            "minimum_mnq_net_profit_usd_strict"
        ],
        passed=(
            float(mnq_net_profit_usd)
            > thresholds[
                "minimum_mnq_net_profit_usd_strict"
            ]
        ),
    )
    add(
        "nq_mcpt_p_value",
        actual=float(nq_mcpt_p_value),
        operator="<=",
        threshold=thresholds[
            "maximum_nq_mcpt_p_value"
        ],
        passed=(
            float(nq_mcpt_p_value)
            <= thresholds[
                "maximum_nq_mcpt_p_value"
            ]
        ),
    )
    add(
        "nq_completed_trades",
        actual=int(nq_completed_trades),
        operator=">=",
        threshold=thresholds[
            "minimum_nq_completed_trades"
        ],
        passed=(
            int(nq_completed_trades)
            >= thresholds[
                "minimum_nq_completed_trades"
            ]
        ),
    )
    add(
        "profitable_nq_calendar_years",
        actual=int(profitable_nq_calendar_years),
        operator=">=",
        threshold=thresholds[
            "minimum_profitable_nq_calendar_years"
        ],
        passed=(
            int(profitable_nq_calendar_years)
            >= thresholds[
                "minimum_profitable_nq_calendar_years"
            ]
        ),
    )
    add(
        "included_invalid_sessions",
        actual=int(included_invalid_sessions),
        operator="<=",
        threshold=thresholds[
            "maximum_included_invalid_sessions"
        ],
        passed=(
            int(included_invalid_sessions)
            <= thresholds[
                "maximum_included_invalid_sessions"
            ]
        ),
    )
    add(
        "included_roll_switch_sessions",
        actual=int(included_roll_switch_sessions),
        operator="<=",
        threshold=thresholds[
            "maximum_included_roll_switch_sessions"
        ],
        passed=(
            int(included_roll_switch_sessions)
            <= thresholds[
                "maximum_included_roll_switch_sessions"
            ]
        ),
    )

    failed = tuple(
        name
        for name, gate in gates.items()
        if not gate["passed"]
    )
    passed = not failed

    return Exp005FullEvaluation(
        decision=(
            "PASS_TO_REVIEW"
            if passed
            else "REJECT"
        ),
        passed=passed,
        gates=gates,
        failed_gates=failed,
    )
