from __future__ import annotations

from typing import Any, Iterable

import numpy as np
import pandas as pd

from exp009_engine import Exp009Result, profit_factor


def _safe_ratio(numerator: float, denominator: float) -> float:
    if not np.isfinite(denominator) or denominator == 0:
        return 0.0
    return float(numerator / denominator)


def _maximum_losing_streak(values: np.ndarray) -> int:
    longest = 0
    current = 0
    for value in values:
        if value < 0:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def _worst_rolling_sum(values: np.ndarray, window: int) -> float:
    if len(values) < window:
        return float("nan")
    return float(
        pd.Series(values).rolling(window).sum().dropna().min()
    )


def _drawdown_durations(values: np.ndarray) -> tuple[int, int]:
    equity = np.cumsum(values)
    peak = 0.0
    underwater_start: int | None = None
    longest_underwater = 0
    longest_recovery = 0
    trough_index = 0

    for index, value in enumerate(equity):
        if value >= peak:
            if underwater_start is not None:
                duration = index - underwater_start
                longest_underwater = max(longest_underwater, duration)
                longest_recovery = max(
                    longest_recovery, index - trough_index
                )
            peak = value
            underwater_start = None
            trough_index = index
        else:
            if underwater_start is None:
                underwater_start = index
                trough_index = index
            elif value < equity[trough_index]:
                trough_index = index

    if underwater_start is not None and len(equity):
        longest_underwater = max(
            longest_underwater, len(equity) - underwater_start
        )
        longest_recovery = max(
            longest_recovery, len(equity) - 1 - trough_index
        )
    return longest_underwater, longest_recovery


def _monthly_results(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame(
            columns=["month", "completed_trades", "net_profit_usd"]
        )
    dates = pd.to_datetime(trades["session_date"])
    local = trades.assign(month=dates.dt.to_period("M").astype(str))
    return (
        local.groupby("month", as_index=False)
        .agg(
            completed_trades=("net_pnl_usd", "size"),
            net_profit_usd=("net_pnl_usd", "sum"),
        )
        .sort_values("month")
        .reset_index(drop=True)
    )


def calculate_candidate_measurements(
    nq_result: Exp009Result,
    mnq_result: Exp009Result,
    *,
    nq_zero_tick_result: Exp009Result,
    nq_two_tick_result: Exp009Result,
    included_session_count: int,
) -> dict[str, Any]:
    trades = nq_result.trades
    pnl = trades["net_pnl_usd"].to_numpy(dtype=float)
    monthly = _monthly_results(trades)
    yearly = nq_result.yearly_results
    trade_years = (
        int(trades["year"].nunique()) if not trades.empty else 0
    )
    profitable_years = (
        int((yearly["net_profit_usd"] > 0).sum())
        if not yearly.empty
        else 0
    )
    profitable_months = (
        int((monthly["net_profit_usd"] > 0).sum())
        if not monthly.empty
        else 0
    )
    longest_dd, longest_recovery = _drawdown_durations(pnl)
    total_profit = float(pnl.sum())
    positive_pnl = np.sort(pnl[pnl > 0])[::-1]
    top_five = float(positive_pnl[:5].sum())
    best_year = (
        float(yearly["net_profit_usd"].max())
        if not yearly.empty
        else 0.0
    )
    round_trip_cost = float(
        nq_result.summary["round_trip_cost_usd"]
    )

    nq_pf = float(nq_result.summary["trade_profit_factor"])
    mnq_pf = float(mnq_result.summary["trade_profit_factor"])
    flags = {
        "low_sample": int(len(trades)) < 150,
        "concentrated_activity": trade_years < 3,
        "cost_fragile": (
            float(nq_two_tick_result.summary["net_profit_usd"]) <= 0
        ),
        "mnq_divergence": (nq_pf > 1.0) != (mnq_pf > 1.0),
    }

    return {
        **nq_result.summary,
        "mnq_completed_trades": int(
            mnq_result.summary["completed_trades"]
        ),
        "mnq_profit_factor": mnq_pf,
        "mnq_net_profit_usd": float(
            mnq_result.summary["net_profit_usd"]
        ),
        "zero_tick_net_profit_usd": float(
            nq_zero_tick_result.summary["net_profit_usd"]
        ),
        "two_tick_net_profit_usd": float(
            nq_two_tick_result.summary["net_profit_usd"]
        ),
        "cost_resilience_ratio": _safe_ratio(
            float(nq_two_tick_result.summary["net_profit_usd"]),
            float(nq_zero_tick_result.summary["net_profit_usd"]),
        ),
        "trading_years": trade_years,
        "profitable_years": profitable_years,
        "profitable_year_fraction": _safe_ratio(
            profitable_years, trade_years
        ),
        "observed_months": int(len(monthly)),
        "profitable_months": profitable_months,
        "profitable_month_fraction": _safe_ratio(
            profitable_months, len(monthly)
        ),
        "best_year_profit_contribution": _safe_ratio(
            best_year, total_profit
        ),
        "top_5_trade_profit_contribution": _safe_ratio(
            top_five, total_profit
        ),
        "longest_drawdown_duration_trades": int(longest_dd),
        "longest_recovery_duration_trades": int(longest_recovery),
        "maximum_consecutive_losses": _maximum_losing_streak(pnl),
        "worst_20_trade_result_usd": _worst_rolling_sum(pnl, 20),
        "worst_50_trade_result_usd": _worst_rolling_sum(pnl, 50),
        "worst_100_trade_result_usd": _worst_rolling_sum(pnl, 100),
        "trades_per_year": _safe_ratio(len(trades), trade_years),
        "session_participation_rate": _safe_ratio(
            len(trades), included_session_count
        ),
        "average_holding_minutes": (
            float(trades["holding_minutes"].mean())
            if not trades.empty
            else 0.0
        ),
        "median_holding_minutes": (
            float(trades["holding_minutes"].median())
            if not trades.empty
            else 0.0
        ),
        "average_trade_to_round_trip_cost": _safe_ratio(
            float(nq_result.summary["average_trade_usd"]),
            round_trip_cost,
        ),
        "low_sample": bool(flags["low_sample"]),
        "concentrated_activity": bool(
            flags["concentrated_activity"]
        ),
        "cost_fragile": bool(flags["cost_fragile"]),
        "mnq_divergence": bool(flags["mnq_divergence"]),
        "reliability_flag_count": int(sum(flags.values())),
        "research_status": "MEASURED_NOT_VALIDATED",
    }


PARETO_OBJECTIVES: tuple[tuple[str, bool], ...] = (
    ("trade_profit_factor", True),
    ("win_rate", True),
    ("average_trade_to_round_trip_cost", True),
    ("net_profit_to_drawdown", True),
    ("profitable_year_fraction", True),
    ("maximum_drawdown_usd", True),
)


def add_pareto_context(
    table: pd.DataFrame,
    *,
    objectives: Iterable[tuple[str, bool]] = PARETO_OBJECTIVES,
) -> pd.DataFrame:
    result = table.copy().reset_index(drop=True)
    objective_list = list(objectives)
    missing = [
        name for name, _ in objective_list if name not in result.columns
    ]
    if missing:
        raise ValueError(
            "Pareto table is missing objectives: " + ", ".join(missing)
        )

    dominated = np.zeros(len(result), dtype=bool)
    domination_count = np.zeros(len(result), dtype=int)
    values = result[[name for name, _ in objective_list]].to_numpy(
        dtype=float
    )

    for left in range(len(result)):
        if not np.all(np.isfinite(values[left])):
            dominated[left] = True
            continue
        for right in range(len(result)):
            if left == right or not np.all(np.isfinite(values[right])):
                continue
            no_worse = True
            strictly_better = False
            for column, (_, maximize) in enumerate(objective_list):
                right_value = values[right, column]
                left_value = values[left, column]
                if maximize:
                    no_worse &= right_value >= left_value
                    strictly_better |= right_value > left_value
                else:
                    no_worse &= right_value <= left_value
                    strictly_better |= right_value < left_value
            if no_worse and strictly_better:
                dominated[left] = True
                domination_count[left] += 1

    result["pareto_nondominated"] = ~dominated
    result["domination_count"] = domination_count
    return result


def family_measurement_summary(
    candidate_table: pd.DataFrame,
) -> pd.DataFrame:
    if candidate_table.empty:
        return pd.DataFrame()
    records: list[dict[str, Any]] = []
    for family_id, group in candidate_table.groupby(
        "family_id", sort=False
    ):
        records.append(
            {
                "family_id": family_id,
                "candidate_count": int(len(group)),
                "profitable_candidate_count": int(
                    (group["net_profit_usd"] > 0).sum()
                ),
                "median_profit_factor": float(
                    group["trade_profit_factor"].median()
                ),
                "median_win_rate": float(group["win_rate"].median()),
                "median_net_profit_usd": float(
                    group["net_profit_usd"].median()
                ),
                "median_maximum_drawdown_usd": float(
                    group["maximum_drawdown_usd"].median()
                ),
                "nondominated_candidate_count": int(
                    group["pareto_nondominated"].sum()
                ),
                "reliability_flags": int(
                    group["reliability_flag_count"].sum()
                ),
            }
        )
    return pd.DataFrame.from_records(records)


def rolling_trade_measurements(
    trades: pd.DataFrame,
    *,
    window: int = 100,
) -> pd.DataFrame:
    columns = [
        "trade_number",
        "session_date",
        "rolling_profit_factor",
        "rolling_average_trade_usd",
        "rolling_net_profit_usd",
    ]
    if trades.empty:
        return pd.DataFrame(columns=columns)
    pnl = trades["net_pnl_usd"].to_numpy(dtype=float)
    records = []
    for end in range(window, len(pnl) + 1):
        local = pnl[end - window : end]
        records.append(
            {
                "trade_number": end,
                "session_date": trades.iloc[end - 1]["session_date"],
                "rolling_profit_factor": profit_factor(local),
                "rolling_average_trade_usd": float(local.mean()),
                "rolling_net_profit_usd": float(local.sum()),
            }
        )
    return pd.DataFrame.from_records(records, columns=columns)
