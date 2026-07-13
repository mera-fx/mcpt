from __future__ import annotations

from copy import deepcopy
from typing import Any


EXP004_QUICK_SCREEN_RECORD: dict[str, Any] = {
    "schema_version": 1,
    "experiment_id": "EXP-004",
    "recorded_date": "2026-07-13",
    "implementation_commit": "cd887db",
    "decision": "REJECT",
    "lifecycle_stage": "REJECTED",
    "out_of_sample_disclosure": "BLOCKED",
    "out_of_sample_period_viewed": False,
    "data": {
        "market": "QQQ",
        "timeframe": "5 minutes",
        "feed": "SIP",
        "adjustment": "split",
        "in_sample_start": "2019-01-02",
        "in_sample_end": "2022-12-30",
        "included_sessions": 997,
        "included_rows": 77766,
        "early_close_sessions_excluded": 7,
        "incomplete_sessions_excluded": 4,
        "included_invalid_sessions": 0,
    },
    "mcpt": {
        "method": (
            "time-of-day-stratified session permutation"
        ),
        "permutations": 25,
        "workers": 8,
        "p_value": 0.3076923076923077,
    },
    "observed": {
        "best_in_sample_trade_pf": (
            1.0463260050583139
        ),
        "fixed_in_sample_trade_pf": (
            1.02106173584336
        ),
        "parameter_combinations_pf_ge_1": 3,
        "fixed_in_sample_completed_trades": 973,
        "fixed_in_sample_long_trades": 508,
        "fixed_in_sample_short_trades": 465,
        "included_invalid_sessions": 0,
    },
    "gates": {
        "best_in_sample_trade_pf": {
            "actual": 1.0463260050583139,
            "operator": ">",
            "threshold": 1.10,
            "passed": False,
        },
        "fixed_in_sample_trade_pf": {
            "actual": 1.02106173584336,
            "operator": ">",
            "threshold": 1.05,
            "passed": False,
        },
        "parameter_combinations_pf_ge_1": {
            "actual": 3,
            "operator": ">=",
            "threshold": 3,
            "passed": True,
        },
        "quick_mcpt_p_value": {
            "actual": 0.3076923076923077,
            "operator": "<=",
            "threshold": 0.20,
            "passed": False,
        },
        "fixed_in_sample_completed_trades": {
            "actual": 973,
            "operator": ">=",
            "threshold": 250,
            "passed": True,
        },
        "fixed_in_sample_long_trades": {
            "actual": 508,
            "operator": ">=",
            "threshold": 50,
            "passed": True,
        },
        "fixed_in_sample_short_trades": {
            "actual": 465,
            "operator": ">=",
            "threshold": 50,
            "passed": True,
        },
        "included_invalid_sessions": {
            "actual": 0,
            "operator": "<=",
            "threshold": 0,
            "passed": True,
        },
    },
    "failed_gates": [
        "best_in_sample_trade_pf",
        "fixed_in_sample_trade_pf",
        "quick_mcpt_p_value",
    ],
    "protected_outputs": {
        "decision_file": (
            "results/EXP-004/quick_screen/"
            "quick_screen_decision.json"
        ),
        "report": (
            "reports/EXP-004-quick-screen/"
            "report.html"
        ),
    },
    "conclusion": (
        "The exact basic QQQ ORB specification did not "
        "demonstrate sufficient in-sample strength or "
        "session-aware statistical evidence after costs. "
        "This conclusion does not test more structured ORB "
        "variants, which require separate preregistration."
    ),
}


def get_exp004_quick_screen_record(
) -> dict[str, Any]:
    return deepcopy(
        EXP004_QUICK_SCREEN_RECORD
    )


def validate_exp004_quick_screen_record(
    record: dict[str, Any] | None = None,
) -> None:
    current = (
        EXP004_QUICK_SCREEN_RECORD
        if record is None
        else record
    )

    if current.get(
        "experiment_id"
    ) != "EXP-004":
        raise ValueError(
            "Quick-screen record must belong to EXP-004."
        )

    if current.get(
        "decision"
    ) != "REJECT":
        raise ValueError(
            "EXP-004 quick-screen decision must remain REJECT."
        )

    if current.get(
        "lifecycle_stage"
    ) != "REJECTED":
        raise ValueError(
            "EXP-004 lifecycle must remain REJECTED."
        )

    if current.get(
        "out_of_sample_disclosure"
    ) != "BLOCKED":
        raise ValueError(
            "EXP-004 OOS disclosure must remain blocked."
        )

    if current.get(
        "out_of_sample_period_viewed"
    ) is not False:
        raise ValueError(
            "EXP-004 cannot record viewed OOS results."
        )

    gates = current.get(
        "gates",
        {},
    )

    if len(gates) != 8:
        raise ValueError(
            "EXP-004 must preserve all eight quick gates."
        )

    failed = sorted(
        name
        for name, gate in gates.items()
        if not bool(gate.get("passed"))
    )

    expected_failed = sorted(
        current.get(
            "failed_gates",
            [],
        )
    )

    if failed != expected_failed:
        raise ValueError(
            "EXP-004 failed-gate list is inconsistent."
        )

    if expected_failed != sorted(
        [
            "best_in_sample_trade_pf",
            "fixed_in_sample_trade_pf",
            "quick_mcpt_p_value",
        ]
    ):
        raise ValueError(
            "EXP-004 failed gates cannot be changed."
        )

    data = current.get(
        "data",
        {},
    )

    if data.get(
        "included_invalid_sessions"
    ) != 0:
        raise ValueError(
            "EXP-004 included invalid sessions."
        )

    if data.get(
        "included_sessions"
    ) != 997:
        raise ValueError(
            "EXP-004 session count changed."
        )

    if data.get(
        "included_rows"
    ) != 77766:
        raise ValueError(
            "EXP-004 row count changed."
        )

    if current[
        "mcpt"
    ]["permutations"] != 25:
        raise ValueError(
            "EXP-004 quick MCPT count changed."
        )


if __name__ == "__main__":
    validate_exp004_quick_screen_record()

    print(
        "EXP-004 quick-screen rejection record is valid."
    )
