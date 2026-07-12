from __future__ import annotations

from copy import deepcopy
from typing import Any


EXP003_PAPER_TESTING_PLAN: dict[str, Any] = {
    "schema_version": 1,
    "experiment_id": "EXP-003",
    "status": "ACCEPTED_FOR_PAPER_TESTING",
    "mode": "paper_only",
    "strategy_name": (
        "volatility_compression_breakout_long"
    ),
    "fixed_parameters": {
        "vol_lookback": 48,
        "compression_quantile": 0.20,
        "breakout_lookback": 48,
    },
    "locked_strategy_rules": {
        "compression_reference_window_bars": 2160,
        "compression_recency_bars": 24,
        "exit_lookback_bars": 24,
        "maximum_holding_bars": 168,
        "execution_lag_bars": 1,
        "direction": "long_only",
        "pyramiding": False,
    },
    "cost_model": {
        "commission_bps_per_side": 5.0,
        "slippage_bps_per_side": 2.0,
        "starting_capital": 100000.0,
    },
    "minimum_observation": {
        "calendar_weeks": 12,
        "completed_trades": 20,
        "completion_rule": (
            "Both minimums must be met."
        ),
    },
    "operational_gates": {
        "closed_candle_only": True,
        "next_open_execution": True,
        "signal_state_match_percent": 100.0,
        "maximum_unresolved_reconciliation_errors": 0,
        "maximum_duplicate_orders": 0,
        "maximum_pyramiding_events": 0,
        "maximum_stale_or_missing_candle_trades": 0,
        "complete_audit_log_required": True,
    },
    "data_safety": {
        "trade_on_incomplete_candle": False,
        "stop_on_missing_hour": True,
        "stop_on_duplicate_timestamp": True,
        "stop_on_non_monotonic_timestamp": True,
        "public_market_data_only_initially": True,
    },
    "acceptance_interpretation": (
        "Paper testing validates implementation fidelity and "
        "operational reliability. Paper profitability is reported "
        "but is not, by itself, a pass or fail criterion."
    ),
    "prohibited_actions": [
        "No live orders.",
        "No exchange trading API keys.",
        "No leverage.",
        "No parameter changes.",
        "No new filters, stops, targets or exits under EXP-003.",
        "No rerun of EXP-003 research to justify paper results.",
    ],
}


def get_exp003_paper_testing_plan(
) -> dict[str, Any]:
    return deepcopy(
        EXP003_PAPER_TESTING_PLAN
    )


def validate_exp003_paper_testing_plan(
    plan: dict[str, Any] | None = None,
) -> None:
    record = (
        EXP003_PAPER_TESTING_PLAN
        if plan is None
        else plan
    )

    if record.get("experiment_id") != "EXP-003":
        raise ValueError(
            "Paper plan must belong to EXP-003."
        )

    if (
        record.get("status")
        != "ACCEPTED_FOR_PAPER_TESTING"
    ):
        raise ValueError(
            "Paper plan status must be "
            "ACCEPTED_FOR_PAPER_TESTING."
        )

    if record.get("mode") != "paper_only":
        raise ValueError(
            "The initial implementation must be paper-only."
        )

    expected_parameters = {
        "vol_lookback": 48,
        "compression_quantile": 0.20,
        "breakout_lookback": 48,
    }

    if (
        record.get("fixed_parameters")
        != expected_parameters
    ):
        raise ValueError(
            "Paper-testing parameters do not match "
            "the preregistered fixed parameters."
        )

    observation = record[
        "minimum_observation"
    ]

    if observation["calendar_weeks"] < 12:
        raise ValueError(
            "Paper testing must run for at least 12 weeks."
        )

    if observation["completed_trades"] < 20:
        raise ValueError(
            "Paper testing requires at least 20 trades."
        )

    gates = record["operational_gates"]

    if (
        gates["signal_state_match_percent"]
        != 100.0
    ):
        raise ValueError(
            "Signal/state reconciliation must be exact."
        )

    for key in (
        "maximum_unresolved_reconciliation_errors",
        "maximum_duplicate_orders",
        "maximum_pyramiding_events",
        "maximum_stale_or_missing_candle_trades",
    ):
        if gates[key] != 0:
            raise ValueError(
                f"{key} must remain zero."
            )

    prohibited = " ".join(
        record["prohibited_actions"]
    ).lower()

    if "no live orders" not in prohibited:
        raise ValueError(
            "The plan must explicitly prohibit live orders."
        )

    if "no parameter changes" not in prohibited:
        raise ValueError(
            "The plan must prohibit parameter changes."
        )


if __name__ == "__main__":
    validate_exp003_paper_testing_plan()

    print(
        "EXP-003 paper-testing plan is valid and locked."
    )
