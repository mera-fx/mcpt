from __future__ import annotations

from typing import Any

from exp009_engine import Exp009Result
from exp009_measurements import (
    add_pareto_context,
    calculate_candidate_measurements,
    family_measurement_summary,
    rolling_trade_measurements,
)


CONTEXT_FIELDS = (
    "context_value_name",
    "feature_eligible_sessions",
    "feature_eligible_rate",
    "signal_confirmed_sessions",
    "signal_confirmation_rate",
    "context_value_mean",
    "context_value_median",
    "context_long_trades",
    "context_short_trades",
)


def calculate_exp012_candidate_measurements(
    nq_result: Exp009Result,
    mnq_result: Exp009Result,
    *,
    nq_zero_tick_result: Exp009Result,
    nq_two_tick_result: Exp009Result,
    included_session_count: int,
) -> dict[str, Any]:
    record = calculate_candidate_measurements(
        nq_result,
        mnq_result,
        nq_zero_tick_result=nq_zero_tick_result,
        nq_two_tick_result=nq_two_tick_result,
        included_session_count=included_session_count,
    )
    for field in CONTEXT_FIELDS:
        record[field] = nq_result.summary[field]
    record["research_status"] = "MEASURED_NOT_VALIDATED"
    return record


__all__ = [
    "add_pareto_context",
    "calculate_exp012_candidate_measurements",
    "family_measurement_summary",
    "rolling_trade_measurements",
]
