from __future__ import annotations

from collections import Counter
import math
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd

from analytics_evidence_registry import (
    AnalyticsSeriesSpec,
    AvailabilityStatus,
    MetricFamily,
    NOT_AVAILABLE_MESSAGE,
)


ANALYTICS_SCHEMA_VERSION = "frozen_evidence_analytics_v1"
AVAILABLE_MESSAGE = "Calculated from registered frozen evidence."
FAMILY_LABELS = {
    MetricFamily.PERFORMANCE_SUMMARY: "Performance summary",
    MetricFamily.TOTAL_TRADE_ANALYSIS: "Total trade analysis",
    MetricFamily.PERFORMANCE_RATIOS: "Performance ratios",
    MetricFamily.TIME_AND_EXPOSURE: "Time and market exposure",
    MetricFamily.EQUITY_AND_DRAWDOWN: "Equity and drawdown",
    MetricFamily.WIN_LOSS_DISTRIBUTIONS: (
        "Winning and losing trade distributions"
    ),
    MetricFamily.STREAK_AND_TRADE_SERIES: (
        "Streak and trade-series analysis"
    ),
    MetricFamily.OUTLIER_ANALYSIS: "Outlier and concentration analysis",
    MetricFamily.MAE_AND_MFE: "MAE and MFE",
    MetricFamily.MONTHLY_AND_ANNUAL: "Monthly and annual analysis",
    MetricFamily.BENCHMARK_AND_VALUE_ADDED: (
        "Benchmark and value-added analysis"
    ),
    MetricFamily.EXISTING_ROBUSTNESS: (
        "Existing frozen robustness evidence"
    ),
}


def json_safe(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer, int)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return number if math.isfinite(number) else None
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, Mapping):
        return {
            str(key): json_safe(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple, set)):
        return [json_safe(item) for item in value]
    return value


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return [
        json_safe(record)
        for record in frame.to_dict(orient="records")
    ]


def _safe_ratio(
    numerator: float,
    denominator: float,
) -> float:
    if not math.isfinite(float(numerator)):
        return float("nan")
    if not math.isfinite(float(denominator)) or denominator == 0:
        return float("nan")
    return float(numerator / denominator)


def _sample_std(values: pd.Series) -> float:
    clean = pd.to_numeric(values, errors="coerce").dropna()
    return (
        float(clean.std(ddof=1))
        if len(clean) > 1
        else float("nan")
    )


def _profit_factor(values: pd.Series) -> float:
    pnl = pd.to_numeric(values, errors="coerce").dropna()
    profit = float(pnl.loc[pnl > 0].sum())
    loss = float(-pnl.loc[pnl < 0].sum())
    if loss > 0:
        return profit / loss
    return float("inf") if profit > 0 else float("nan")


def _trade_drawdown(values: pd.Series) -> float:
    pnl = pd.to_numeric(values, errors="coerce").fillna(0.0)
    cumulative = pnl.cumsum().to_numpy(dtype=float)
    if not len(cumulative):
        return 0.0
    peaks = np.maximum.accumulate(
        np.concatenate(([0.0], cumulative))
    )[1:]
    return float(np.min(cumulative - peaks))


def _maximum_contracts_held(trades: pd.DataFrame) -> float:
    contracts = pd.to_numeric(
        trades.get(
            "contracts",
            pd.Series(1.0, index=trades.index),
        ),
        errors="coerce",
    ).abs().fillna(0.0)
    if contracts.empty:
        return 0.0

    entries = pd.to_datetime(
        trades.get(
            "entry_time",
            pd.Series(pd.NaT, index=trades.index),
        ),
        errors="coerce",
        utc=True,
    )
    exits = pd.to_datetime(
        trades.get(
            "exit_time",
            pd.Series(pd.NaT, index=trades.index),
        ),
        errors="coerce",
        utc=True,
    )
    events: dict[pd.Timestamp, dict[str, float]] = {}
    for entry, exit_, quantity in zip(entries, exits, contracts):
        amount = float(quantity)
        if amount <= 0 or pd.isna(entry) or pd.isna(exit_):
            continue
        if exit_ <= entry:
            continue
        events.setdefault(
            pd.Timestamp(entry),
            {"entries": 0.0, "exits": 0.0},
        )["entries"] += amount
        events.setdefault(
            pd.Timestamp(exit_),
            {"entries": 0.0, "exits": 0.0},
        )["exits"] += amount

    maximum = float(contracts.max())
    active = 0.0
    for timestamp in sorted(events):
        event = events[timestamp]
        active = max(0.0, active - event["exits"])
        active += event["entries"]
        maximum = max(maximum, active)
    return maximum


def _run_rows(values: pd.Series) -> list[dict[str, Any]]:
    pnl = pd.to_numeric(values, errors="coerce").fillna(0.0)
    rows: list[dict[str, Any]] = []
    active_sign = 0
    active_start = 0
    active_values: list[float] = []

    def finish(end_index: int) -> None:
        nonlocal active_sign, active_start, active_values
        if not active_values:
            return
        rows.append(
            {
                "outcome": "win" if active_sign > 0 else "loss",
                "start_trade": active_start + 1,
                "end_trade": end_index,
                "length": len(active_values),
                "net_pnl_usd": float(sum(active_values)),
            }
        )
        active_values = []

    for index, value in enumerate(pnl.to_numpy(dtype=float)):
        sign = 1 if value > 0 else -1 if value < 0 else 0
        if sign == 0:
            finish(index)
            active_sign = 0
            continue
        if sign != active_sign:
            finish(index)
            active_sign = sign
            active_start = index
        active_values.append(float(value))
    finish(len(pnl))
    return rows


def _segment_metrics(trades: pd.DataFrame) -> dict[str, Any]:
    pnl = pd.to_numeric(
        trades.get("net_pnl_usd", pd.Series(dtype=float)),
        errors="coerce",
    ).dropna()
    costs = pd.to_numeric(
        trades.get(
            "transaction_cost_usd",
            pd.Series(0.0, index=trades.index),
        ),
        errors="coerce",
    ).fillna(0.0)
    holding = pd.to_numeric(
        trades.get(
            "holding_minutes",
            pd.Series(np.nan, index=trades.index),
        ),
        errors="coerce",
    ).dropna()
    winners = pnl.loc[pnl > 0]
    losers = pnl.loc[pnl < 0]
    breakeven = pnl.loc[pnl == 0]
    gross_profit = float(winners.sum())
    gross_loss = float(-losers.sum())
    average_winner = (
        float(winners.mean())
        if len(winners)
        else float("nan")
    )
    average_loser = (
        float(losers.mean())
        if len(losers)
        else float("nan")
    )
    drawdown = _trade_drawdown(pnl)
    runs = _run_rows(pnl)
    win_runs = [
        int(row["length"])
        for row in runs
        if row["outcome"] == "win"
    ]
    loss_runs = [
        int(row["length"])
        for row in runs
        if row["outcome"] == "loss"
    ]
    average_cost = (
        float(costs.sum()) / len(pnl)
        if len(pnl)
        else float("nan")
    )
    return {
        "completed_trades": len(pnl),
        "winning_trades": len(winners),
        "losing_trades": len(losers),
        "breakeven_trades": len(breakeven),
        "net_profit_usd": float(pnl.sum()),
        "gross_profit_usd": gross_profit,
        "gross_loss_usd": gross_loss,
        "profit_factor": _profit_factor(pnl),
        "win_rate_percent": (
            float((pnl > 0).mean() * 100.0)
            if len(pnl)
            else float("nan")
        ),
        "loss_rate_percent": (
            float((pnl < 0).mean() * 100.0)
            if len(pnl)
            else float("nan")
        ),
        "average_trade_usd": (
            float(pnl.mean())
            if len(pnl)
            else float("nan")
        ),
        "median_trade_usd": (
            float(pnl.median())
            if len(pnl)
            else float("nan")
        ),
        "trade_standard_deviation_usd": _sample_std(pnl),
        "average_winner_usd": average_winner,
        "median_winner_usd": (
            float(winners.median())
            if len(winners)
            else float("nan")
        ),
        "average_loser_usd": average_loser,
        "median_loser_usd": (
            float(losers.median())
            if len(losers)
            else float("nan")
        ),
        "payoff_ratio": _safe_ratio(
            average_winner,
            abs(average_loser),
        ),
        "largest_winner_usd": (
            float(winners.max())
            if len(winners)
            else float("nan")
        ),
        "largest_loser_usd": (
            float(losers.min())
            if len(losers)
            else float("nan")
        ),
        "trade_series_maximum_drawdown_usd": drawdown,
        "net_profit_to_trade_drawdown": _safe_ratio(
            float(pnl.sum()),
            abs(drawdown),
        ),
        "total_transaction_cost_usd": float(costs.sum()),
        "average_transaction_cost_usd": average_cost,
        "average_trade_to_average_cost": _safe_ratio(
            float(pnl.mean()) if len(pnl) else float("nan"),
            average_cost,
        ),
        "maximum_consecutive_wins": max(win_runs, default=0),
        "maximum_consecutive_losses": max(loss_runs, default=0),
        "average_holding_minutes": (
            float(holding.mean())
            if len(holding)
            else float("nan")
        ),
        "median_holding_minutes": (
            float(holding.median())
            if len(holding)
            else float("nan")
        ),
    }


def _period_frame(
    equity: pd.DataFrame,
    reference_capital_usd: float,
) -> pd.DataFrame:
    working = equity.loc[
        :,
        ["period_end", "equity_usd"],
    ].copy()
    working["analysis_date"] = pd.to_datetime(
        working["period_end"],
        errors="coerce",
        utc=True,
    ).dt.normalize()
    working["equity_usd"] = pd.to_numeric(
        working["equity_usd"],
        errors="coerce",
    )
    working = working.dropna().sort_values("analysis_date")
    periods = (
        working.groupby("analysis_date", as_index=False)
        .last()
        .sort_values("analysis_date")
        .reset_index(drop=True)
    )
    periods["net_pnl_usd"] = periods["equity_usd"].diff()
    periods["return"] = periods["equity_usd"].pct_change()
    if len(periods):
        periods.loc[0, "net_pnl_usd"] = (
            periods.loc[0, "equity_usd"]
            - reference_capital_usd
        )
        periods.loc[0, "return"] = (
            periods.loc[0, "equity_usd"]
            / reference_capital_usd
            - 1.0
        )
    return periods


def _benchmark_period_frame(
    benchmark: pd.DataFrame,
    reference_capital_usd: float,
) -> pd.DataFrame:
    working = benchmark.loc[
        :,
        ["period_end", "benchmark_equity_usd"],
    ].copy()
    working["analysis_date"] = pd.to_datetime(
        working["period_end"],
        errors="coerce",
        utc=True,
    ).dt.normalize()
    working["benchmark_equity_usd"] = pd.to_numeric(
        working["benchmark_equity_usd"],
        errors="coerce",
    )
    working = working.dropna().sort_values("analysis_date")
    periods = (
        working.groupby("analysis_date", as_index=False)
        .last()
        .sort_values("analysis_date")
        .reset_index(drop=True)
    )
    periods["benchmark_return"] = periods[
        "benchmark_equity_usd"
    ].pct_change()
    if len(periods):
        periods.loc[0, "benchmark_return"] = (
            periods.loc[0, "benchmark_equity_usd"]
            / reference_capital_usd
            - 1.0
        )
    return periods


def _elapsed_years(periods: pd.DataFrame, annualization: int) -> float:
    if len(periods) < 2:
        return (
            len(periods) / annualization
            if annualization > 0
            else float("nan")
        )
    days = (
        periods["analysis_date"].iloc[-1]
        - periods["analysis_date"].iloc[0]
    ).days
    if days > 0:
        return days / 365.2425
    return len(periods) / annualization


def _cagr(
    ending_equity: float,
    reference_capital_usd: float,
    elapsed_years: float,
) -> float:
    if (
        ending_equity <= 0
        or reference_capital_usd <= 0
        or elapsed_years <= 0
    ):
        return float("nan")
    return (
        (ending_equity / reference_capital_usd)
        ** (1.0 / elapsed_years)
        - 1.0
    )


def _equivalent_monthly_rate(annual_rate: float) -> float:
    if not math.isfinite(annual_rate) or annual_rate <= -1.0:
        return float("nan")
    return (1.0 + annual_rate) ** (1.0 / 12.0) - 1.0


def _drawdown_arrays(
    values: pd.Series,
    reference_capital_usd: float,
) -> tuple[np.ndarray, np.ndarray]:
    equity = pd.to_numeric(
        values,
        errors="coerce",
    ).to_numpy(dtype=float)
    if not len(equity):
        return np.asarray([], dtype=float), np.asarray([], dtype=float)
    peaks = np.maximum.accumulate(
        np.concatenate(([reference_capital_usd], equity))
    )[1:]
    cash = equity - peaks
    percent = np.divide(
        cash,
        peaks,
        out=np.full_like(cash, np.nan),
        where=peaks != 0,
    )
    return cash, percent


def _drawdown_episodes(
    periods: pd.DataFrame,
    reference_capital_usd: float,
) -> list[dict[str, Any]]:
    if periods.empty:
        return []
    dates = list(periods["analysis_date"])
    values = periods["equity_usd"].to_numpy(dtype=float)
    peak_value = float(reference_capital_usd)
    peak_date = dates[0]
    peak_index = 0
    active: dict[str, Any] | None = None
    episodes: list[dict[str, Any]] = []

    for index, (date, value) in enumerate(zip(dates, values)):
        if value >= peak_value:
            if active is not None:
                active["recovery_date"] = date
                active["underwater_periods"] = (
                    index - int(active["peak_index"])
                )
                active["calendar_days_to_recovery"] = (
                    date - active["peak_date"]
                ).days
                episodes.append(active)
                active = None
            peak_value = float(value)
            peak_date = date
            peak_index = index
            continue

        if active is None:
            active = {
                "peak_date": peak_date,
                "peak_index": peak_index,
                "peak_equity_usd": peak_value,
                "trough_date": date,
                "trough_equity_usd": float(value),
                "recovery_date": None,
            }
        if value < float(active["trough_equity_usd"]):
            active["trough_date"] = date
            active["trough_equity_usd"] = float(value)

    if active is not None:
        active["underwater_periods"] = (
            len(periods) - int(active["peak_index"])
        )
        active["calendar_days_to_recovery"] = None
        episodes.append(active)

    for episode in episodes:
        peak = float(episode["peak_equity_usd"])
        trough = float(episode["trough_equity_usd"])
        episode["drawdown_usd"] = trough - peak
        episode["drawdown_percent"] = (
            (trough / peak - 1.0) * 100.0
            if peak != 0
            else float("nan")
        )
        episode.pop("peak_index", None)
    return episodes


def _available_family(
    family: MetricFamily,
    metrics: Mapping[str, Any],
    *,
    tables: Mapping[str, Any] | None = None,
    assumptions: Mapping[str, Any] | None = None,
    evidence_paths: Iterable[str] = (),
) -> dict[str, Any]:
    return {
        "family": family.value,
        "label": FAMILY_LABELS[family],
        "status": AvailabilityStatus.AVAILABLE.value,
        "message": AVAILABLE_MESSAGE,
        "metrics": dict(metrics),
        "tables": dict(tables or {}),
        "assumptions": dict(assumptions or {}),
        "evidence_paths": list(evidence_paths),
    }


def _unavailable_family(
    family: MetricFamily,
) -> dict[str, Any]:
    return {
        "family": family.value,
        "label": FAMILY_LABELS[family],
        "status": AvailabilityStatus.NOT_AVAILABLE.value,
        "message": NOT_AVAILABLE_MESSAGE,
        "metrics": {},
        "tables": {},
        "assumptions": {},
        "evidence_paths": [],
    }


def _performance_summary(
    trades: pd.DataFrame,
    periods: pd.DataFrame,
    spec: AnalyticsSeriesSpec,
    benchmark_family: Mapping[str, Any],
) -> dict[str, Any]:
    direction = trades["direction"].astype(str).str.lower()
    segments = {
        "all": trades,
        "long": trades.loc[direction.eq("long")],
        "short": trades.loc[direction.eq("short")],
    }
    elapsed_years = _elapsed_years(
        periods,
        spec.annualization_periods,
    )
    benchmark_metrics = benchmark_family.get("metrics", {})
    buy_and_hold_return_usd = None
    buy_and_hold_return_percent = None
    if benchmark_family.get("status") == (
        AvailabilityStatus.AVAILABLE.value
    ):
        benchmark_ending = benchmark_metrics.get(
            "benchmark_ending_equity_usd"
        )
        if benchmark_ending is not None:
            buy_and_hold_return_usd = (
                float(benchmark_ending)
                - spec.reference_capital_usd
            )
        buy_and_hold_return_percent = benchmark_metrics.get(
            "benchmark_total_return_percent"
        )

    metrics: dict[str, dict[str, Any]] = {}
    for name, frame in segments.items():
        segment = _segment_metrics(frame)
        if name == "all":
            path_values = periods["equity_usd"]
            ending_equity = (
                float(path_values.iloc[-1])
                if len(path_values)
                else spec.reference_capital_usd
            )
        else:
            pnl = pd.to_numeric(
                frame.get(
                    "net_pnl_usd",
                    pd.Series(dtype=float),
                ),
                errors="coerce",
            ).fillna(0.0)
            path_values = (
                spec.reference_capital_usd + pnl.cumsum()
            )
            ending_equity = (
                float(path_values.iloc[-1])
                if len(path_values)
                else spec.reference_capital_usd
            )
        cash_drawdown, percent_drawdown = _drawdown_arrays(
            path_values,
            spec.reference_capital_usd,
        )
        maximum_drawdown_usd = (
            float(np.nanmin(cash_drawdown))
            if len(cash_drawdown)
            else 0.0
        )
        maximum_drawdown_percent = (
            float(np.nanmin(percent_drawdown)) * 100.0
            if len(percent_drawdown)
            else 0.0
        )
        annual_rate = _cagr(
            ending_equity,
            spec.reference_capital_usd,
            elapsed_years,
        )
        segment.update(
            {
                "return_on_initial_capital_percent": (
                    (
                        ending_equity
                        / spec.reference_capital_usd
                        - 1.0
                    )
                    * 100.0
                ),
                "maximum_strategy_drawdown_usd": (
                    maximum_drawdown_usd
                ),
                "maximum_strategy_drawdown_percent": (
                    maximum_drawdown_percent
                ),
                "return_on_maximum_strategy_drawdown": (
                    _safe_ratio(
                        segment["net_profit_usd"],
                        abs(maximum_drawdown_usd),
                    )
                ),
                "maximum_contracts_held": (
                    _maximum_contracts_held(frame)
                ),
                "annual_rate_of_return_percent": (
                    annual_rate * 100.0
                ),
                "monthly_rate_of_return_percent": (
                    _equivalent_monthly_rate(annual_rate)
                    * 100.0
                ),
                "buy_and_hold_return_usd": (
                    buy_and_hold_return_usd
                    if name == "all"
                    else None
                ),
                "buy_and_hold_return_percent": (
                    buy_and_hold_return_percent
                    if name == "all"
                    else None
                ),
            }
        )
        metrics[name] = segment

    evidence_paths = [
        spec.trades_path.as_posix(),
        spec.equity_path.as_posix(),
    ]
    if benchmark_family.get("status") == (
        AvailabilityStatus.AVAILABLE.value
    ):
        evidence_paths.extend(
            path.as_posix()
            for path in spec.benchmark_paths
        )
    return _available_family(
        MetricFamily.PERFORMANCE_SUMMARY,
        metrics,
        assumptions={
            "profit_factor_basis": (
                "Net trade P&L after frozen transaction costs"
            ),
            "all_strategy_drawdown_basis": (
                "Registered frozen equity path"
            ),
            "long_short_drawdown_basis": (
                "Direction-only ordered closed-trade P&L paths, "
                "each normalized to the registered reference capital"
            ),
            "return_on_maximum_strategy_drawdown_formula": (
                "Net profit divided by the absolute maximum cash "
                "drawdown"
            ),
            "annual_rate_of_return_formula": (
                "Compound annual growth rate over the registered "
                "analysis span"
            ),
            "monthly_rate_of_return_formula": (
                "Monthly rate equivalent to the compound annual "
                "growth rate: (1 + annual rate)^(1/12) - 1"
            ),
            "maximum_contracts_held_basis": (
                "Maximum simultaneous absolute contracts from frozen "
                "entry, exit, and contracts fields"
            ),
            "buy_and_hold_basis": (
                "Aligned normalized underlying benchmark; not a "
                "literal one-contract futures portfolio"
            ),
        },
        evidence_paths=tuple(dict.fromkeys(evidence_paths)),
    )


def _total_trade_analysis(
    trades: pd.DataFrame,
    trade_path: str,
) -> dict[str, Any]:
    metrics = _segment_metrics(trades)
    gross = pd.to_numeric(
        trades["gross_pnl_usd"],
        errors="coerce",
    ).fillna(0.0)
    net = pd.to_numeric(
        trades["net_pnl_usd"],
        errors="coerce",
    ).fillna(0.0)
    direction_rows = []
    for direction, frame in trades.groupby("direction", sort=True):
        direction_rows.append(
            {
                "direction": str(direction),
                **_segment_metrics(frame),
            }
        )
    exit_rows = []
    for reason, frame in trades.groupby("exit_reason", sort=True):
        exit_rows.append(
            {
                "exit_reason": str(reason) or "unspecified",
                **_segment_metrics(frame),
            }
        )
    metrics.update(
        {
            "gross_pnl_before_costs_usd": float(gross.sum()),
            "net_pnl_after_costs_usd": float(net.sum()),
            "cost_drag_usd": float(gross.sum() - net.sum()),
            "cost_drag_as_percent_of_gross_profit": (
                _safe_ratio(
                    float(gross.sum() - net.sum()),
                    float(net.loc[net > 0].sum()),
                )
                * 100.0
            ),
            "distinct_trading_sessions": int(
                pd.to_datetime(
                    trades["session_date"],
                    errors="coerce",
                ).nunique()
            ),
        }
    )
    return _available_family(
        MetricFamily.TOTAL_TRADE_ANALYSIS,
        metrics,
        tables={
            "by_direction": direction_rows,
            "by_exit_reason": exit_rows,
        },
        evidence_paths=(trade_path,),
    )


def _performance_ratios(
    trades: pd.DataFrame,
    periods: pd.DataFrame,
    spec: AnalyticsSeriesSpec,
) -> dict[str, Any]:
    returns = periods["return"].dropna()
    ending = (
        float(periods["equity_usd"].iloc[-1])
        if len(periods)
        else spec.reference_capital_usd
    )
    years = _elapsed_years(periods, spec.annualization_periods)
    cagr = _cagr(
        ending,
        spec.reference_capital_usd,
        years,
    )
    cash_drawdown, percent_drawdown = _drawdown_arrays(
        periods["equity_usd"],
        spec.reference_capital_usd,
    )
    max_drawdown_cash = (
        float(np.nanmin(cash_drawdown))
        if len(cash_drawdown)
        else 0.0
    )
    max_drawdown = (
        float(np.nanmin(percent_drawdown))
        if len(percent_drawdown)
        else 0.0
    )
    mean_return = (
        float(returns.mean())
        if len(returns)
        else float("nan")
    )
    volatility = _sample_std(returns)
    downside = np.minimum(
        returns.to_numpy(dtype=float),
        0.0,
    )
    downside_period = (
        float(np.sqrt(np.mean(np.square(downside))))
        if len(downside)
        else float("nan")
    )
    annualization_root = math.sqrt(spec.annualization_periods)
    pnl = pd.to_numeric(
        trades["net_pnl_usd"],
        errors="coerce",
    ).dropna()
    pnl_std = _sample_std(pnl)
    segment = _segment_metrics(trades)
    return _available_family(
        MetricFamily.PERFORMANCE_RATIOS,
        {
            "normalized_total_return_percent": (
                (ending / spec.reference_capital_usd - 1.0)
                * 100.0
            ),
            "normalized_cagr_percent": cagr * 100.0,
            "annualized_volatility_percent": (
                volatility * annualization_root * 100.0
            ),
            "sharpe_ratio_zero_risk_free": (
                _safe_ratio(mean_return, volatility)
                * annualization_root
            ),
            "annualized_downside_deviation_percent": (
                downside_period * annualization_root * 100.0
            ),
            "sortino_ratio_zero_target": (
                _safe_ratio(mean_return, downside_period)
                * annualization_root
            ),
            "calmar_ratio": _safe_ratio(cagr, abs(max_drawdown)),
            "recovery_factor": _safe_ratio(
                ending - spec.reference_capital_usd,
                abs(max_drawdown_cash),
            ),
            "profit_factor": segment["profit_factor"],
            "payoff_ratio": segment["payoff_ratio"],
            "expectancy_usd_per_trade": segment[
                "average_trade_usd"
            ],
            "sqn_trade_series": (
                _safe_ratio(float(pnl.mean()), pnl_std)
                * math.sqrt(len(pnl))
                if len(pnl)
                else float("nan")
            ),
            "omega_ratio_zero_threshold": _safe_ratio(
                float(returns.loc[returns > 0].sum()),
                float(-returns.loc[returns < 0].sum()),
            ),
        },
        assumptions={
            "reference_capital_usd": spec.reference_capital_usd,
            "return_frequency": (
                "UTC calendar day"
                if spec.annualization_periods == 365
                else "exchange session"
            ),
            "annualization_periods": spec.annualization_periods,
            "risk_free_rate_percent": 0.0,
            "sortino_target_return_percent": 0.0,
            "sqn_label": "Trade-series measurement",
        },
        evidence_paths=(
            spec.trades_path.as_posix(),
            spec.equity_path.as_posix(),
        ),
    )


def _merged_interval_minutes(trades: pd.DataFrame) -> float:
    intervals = (
        trades.loc[:, ["entry_time", "exit_time"]]
        .dropna()
        .sort_values("entry_time")
    )
    if intervals.empty:
        return float("nan")
    merged: list[tuple[pd.Timestamp, pd.Timestamp]] = []
    for row in intervals.itertuples(index=False):
        start = pd.Timestamp(row.entry_time)
        end = pd.Timestamp(row.exit_time)
        if end < start:
            continue
        if not merged or start > merged[-1][1]:
            merged.append((start, end))
        else:
            merged[-1] = (
                merged[-1][0],
                max(merged[-1][1], end),
            )
    return float(
        sum(
            (end - start).total_seconds() / 60.0
            for start, end in merged
        )
    )


def _time_and_exposure(
    trades: pd.DataFrame,
    periods: pd.DataFrame,
    spec: AnalyticsSeriesSpec,
) -> dict[str, Any]:
    holding = pd.to_numeric(
        trades["holding_minutes"],
        errors="coerce",
    ).dropna()
    merged_minutes = _merged_interval_minutes(trades)
    if not math.isfinite(merged_minutes):
        merged_minutes = float(holding.sum())
        exposure_method = "Summed frozen holding durations"
    else:
        exposure_method = "Union of frozen entry and exit intervals"

    eligible_minutes_per_period = (
        spec.eligible_minutes_per_session
        if spec.eligible_minutes_per_session is not None
        else 24 * 60
    )
    eligible_minutes = (
        len(periods) * eligible_minutes_per_period
    )
    years = _elapsed_years(periods, spec.annualization_periods)
    months = years * 12.0
    session_dates = pd.to_datetime(
        trades["session_date"],
        errors="coerce",
    )
    sessions_traded = int(session_dates.nunique())

    entries = pd.to_datetime(
        trades["entry_time"],
        errors="coerce",
        utc=True,
    )
    entry_table: list[dict[str, Any]] = []
    if entries.notna().any():
        local_entries = entries.dt.tz_convert(spec.timezone)
        entry_hours = local_entries.dt.hour
        for hour, indexes in entry_hours.dropna().groupby(
            entry_hours.dropna()
        ).groups.items():
            frame = trades.loc[indexes]
            entry_table.append(
                {
                    "entry_hour_local": f"{int(hour):02d}:00",
                    "trades": len(frame),
                    "net_pnl_usd": float(
                        pd.to_numeric(
                            frame["net_pnl_usd"],
                            errors="coerce",
                        ).sum()
                    ),
                }
            )

    return _available_family(
        MetricFamily.TIME_AND_EXPOSURE,
        {
            "analysis_start": (
                periods["analysis_date"].iloc[0]
                if len(periods)
                else None
            ),
            "analysis_end": (
                periods["analysis_date"].iloc[-1]
                if len(periods)
                else None
            ),
            "calendar_days": (
                (
                    periods["analysis_date"].iloc[-1]
                    - periods["analysis_date"].iloc[0]
                ).days
                + 1
                if len(periods)
                else 0
            ),
            "elapsed_years": years,
            "eligible_periods": len(periods),
            "periods_with_trades": sessions_traded,
            "session_participation_percent": (
                _safe_ratio(sessions_traded, len(periods)) * 100.0
            ),
            "completed_trades": len(trades),
            "trades_per_year": _safe_ratio(len(trades), years),
            "trades_per_month": _safe_ratio(len(trades), months),
            "total_holding_minutes": float(holding.sum()),
            "non_overlapping_market_minutes": merged_minutes,
            "market_exposure_percent": (
                _safe_ratio(merged_minutes, eligible_minutes)
                * 100.0
            ),
            "average_holding_minutes": (
                float(holding.mean())
                if len(holding)
                else float("nan")
            ),
            "median_holding_minutes": (
                float(holding.median())
                if len(holding)
                else float("nan")
            ),
            "maximum_holding_minutes": (
                float(holding.max())
                if len(holding)
                else float("nan")
            ),
            "long_holding_minutes": float(
                pd.to_numeric(
                    trades.loc[
                        trades["direction"].eq("long"),
                        "holding_minutes",
                    ],
                    errors="coerce",
                ).sum()
            ),
            "short_holding_minutes": float(
                pd.to_numeric(
                    trades.loc[
                        trades["direction"].eq("short"),
                        "holding_minutes",
                    ],
                    errors="coerce",
                ).sum()
            ),
        },
        tables={"entries_by_local_hour": entry_table},
        assumptions={
            "timezone": spec.timezone,
            "eligible_minutes_per_period": (
                eligible_minutes_per_period
            ),
            "exposure_method": exposure_method,
        },
        evidence_paths=(
            spec.trades_path.as_posix(),
            spec.equity_path.as_posix(),
        ),
    )


def _equity_and_drawdown(
    periods: pd.DataFrame,
    spec: AnalyticsSeriesSpec,
) -> dict[str, Any]:
    cash, percent = _drawdown_arrays(
        periods["equity_usd"],
        spec.reference_capital_usd,
    )
    episodes = _drawdown_episodes(
        periods,
        spec.reference_capital_usd,
    )
    ending = (
        float(periods["equity_usd"].iloc[-1])
        if len(periods)
        else spec.reference_capital_usd
    )
    max_index = (
        int(np.nanargmin(percent))
        if len(percent)
        else 0
    )
    maximum_drawdown = (
        float(percent[max_index])
        if len(percent)
        else 0.0
    )
    maximum_drawdown_cash = (
        float(cash[max_index])
        if len(cash)
        else 0.0
    )
    longest = max(
        (
            int(episode["underwater_periods"])
            for episode in episodes
        ),
        default=0,
    )
    equity_curve = [
        {
            "analysis_date": row.analysis_date,
            "strategy_equity_usd": row.equity_usd,
        }
        for row in periods.itertuples(index=False)
    ]
    return _available_family(
        MetricFamily.EQUITY_AND_DRAWDOWN,
        {
            "reference_capital_usd": spec.reference_capital_usd,
            "ending_equity_usd": ending,
            "net_profit_usd": (
                ending - spec.reference_capital_usd
            ),
            "highest_equity_usd": (
                float(periods["equity_usd"].max())
                if len(periods)
                else spec.reference_capital_usd
            ),
            "lowest_equity_usd": (
                float(periods["equity_usd"].min())
                if len(periods)
                else spec.reference_capital_usd
            ),
            "maximum_drawdown_usd": maximum_drawdown_cash,
            "maximum_drawdown_percent": (
                maximum_drawdown * 100.0
            ),
            "maximum_drawdown_date": (
                periods["analysis_date"].iloc[max_index]
                if len(periods)
                else None
            ),
            "current_drawdown_usd": (
                float(cash[-1])
                if len(cash)
                else 0.0
            ),
            "current_drawdown_percent": (
                float(percent[-1] * 100.0)
                if len(percent)
                else 0.0
            ),
            "ulcer_index_percent": (
                float(
                    np.sqrt(
                        np.nanmean(
                            np.square(percent * 100.0)
                        )
                    )
                )
                if len(percent)
                else 0.0
            ),
            "pain_index_percent": (
                float(np.nanmean(np.abs(percent * 100.0)))
                if len(percent)
                else 0.0
            ),
            "drawdown_episode_count": len(episodes),
            "longest_underwater_periods": longest,
            "unrecovered_drawdown": bool(
                episodes
                and episodes[-1]["recovery_date"] is None
            ),
        },
        tables={
            "equity_curve": equity_curve,
            "drawdown_episodes": episodes,
        },
        assumptions={
            "drawdown_basis": (
                "Normalized equity including the declared starting "
                "reference capital"
            ),
        },
        evidence_paths=(spec.equity_path.as_posix(),),
    )


def _distribution(values: pd.Series) -> dict[str, Any]:
    clean = pd.to_numeric(values, errors="coerce").dropna()
    if clean.empty:
        return {
            key: float("nan")
            for key in (
                "mean_usd",
                "median_usd",
                "standard_deviation_usd",
                "minimum_usd",
                "p05_usd",
                "p25_usd",
                "p75_usd",
                "p95_usd",
                "maximum_usd",
                "skewness",
                "excess_kurtosis",
            )
        } | {"count": 0}
    return {
        "count": len(clean),
        "mean_usd": float(clean.mean()),
        "median_usd": float(clean.median()),
        "standard_deviation_usd": _sample_std(clean),
        "minimum_usd": float(clean.min()),
        "p05_usd": float(clean.quantile(0.05)),
        "p25_usd": float(clean.quantile(0.25)),
        "p75_usd": float(clean.quantile(0.75)),
        "p95_usd": float(clean.quantile(0.95)),
        "maximum_usd": float(clean.max()),
        "skewness": (
            float(clean.skew())
            if len(clean) > 2
            else float("nan")
        ),
        "excess_kurtosis": (
            float(clean.kurt())
            if len(clean) > 3
            else float("nan")
        ),
    }


def _win_loss_distributions(
    trades: pd.DataFrame,
    trade_path: str,
) -> dict[str, Any]:
    pnl = pd.to_numeric(
        trades["net_pnl_usd"],
        errors="coerce",
    ).dropna()
    winners = pnl.loc[pnl > 0]
    losers = pnl.loc[pnl < 0]
    return _available_family(
        MetricFamily.WIN_LOSS_DISTRIBUTIONS,
        {
            "all_trades": _distribution(pnl),
            "winning_trades": _distribution(winners),
            "losing_trades": _distribution(losers),
            "payoff_ratio": _safe_ratio(
                float(winners.mean())
                if len(winners)
                else float("nan"),
                abs(float(losers.mean()))
                if len(losers)
                else float("nan"),
            ),
            "median_payoff_ratio": _safe_ratio(
                float(winners.median())
                if len(winners)
                else float("nan"),
                abs(float(losers.median()))
                if len(losers)
                else float("nan"),
            ),
        },
        evidence_paths=(trade_path,),
    )


def _streak_and_trade_series(
    trades: pd.DataFrame,
    trade_path: str,
) -> dict[str, Any]:
    pnl = pd.to_numeric(
        trades["net_pnl_usd"],
        errors="coerce",
    ).dropna()
    runs = _run_rows(pnl)
    wins = [
        int(row["length"])
        for row in runs
        if row["outcome"] == "win"
    ]
    losses = [
        int(row["length"])
        for row in runs
        if row["outcome"] == "loss"
    ]
    signs = np.sign(pnl.to_numpy(dtype=float))
    adjacent = [
        (left, right)
        for left, right in zip(signs[:-1], signs[1:])
        if left != 0 and right != 0
    ]
    sign_changes = sum(
        left != right
        for left, right in adjacent
    )
    pnl_std = _sample_std(pnl)
    return _available_family(
        MetricFamily.STREAK_AND_TRADE_SERIES,
        {
            "winning_streak_count": len(wins),
            "losing_streak_count": len(losses),
            "maximum_winning_streak": max(wins, default=0),
            "maximum_losing_streak": max(losses, default=0),
            "average_winning_streak": (
                float(np.mean(wins))
                if wins
                else float("nan")
            ),
            "average_losing_streak": (
                float(np.mean(losses))
                if losses
                else float("nan")
            ),
            "median_winning_streak": (
                float(np.median(wins))
                if wins
                else float("nan")
            ),
            "median_losing_streak": (
                float(np.median(losses))
                if losses
                else float("nan")
            ),
            "current_streak_outcome": (
                runs[-1]["outcome"]
                if runs
                else None
            ),
            "current_streak_length": (
                runs[-1]["length"]
                if runs
                else 0
            ),
            "lag_one_pnl_autocorrelation": (
                float(pnl.autocorr(lag=1))
                if len(pnl) > 2
                else float("nan")
            ),
            "outcome_sign_change_percent": (
                _safe_ratio(sign_changes, len(adjacent)) * 100.0
            ),
            "sqn_trade_series": (
                _safe_ratio(float(pnl.mean()), pnl_std)
                * math.sqrt(len(pnl))
                if len(pnl)
                else float("nan")
            ),
        },
        tables={"runs": runs},
        assumptions={
            "breakeven_treatment": "Breaks a win or loss streak",
            "sqn_label": "Trade-series measurement",
        },
        evidence_paths=(trade_path,),
    )


def _gini_nonnegative(values: pd.Series) -> float:
    array = np.sort(
        pd.to_numeric(values, errors="coerce")
        .dropna()
        .clip(lower=0.0)
        .to_numpy(dtype=float)
    )
    array = array[array > 0]
    if not len(array) or float(array.sum()) == 0:
        return float("nan")
    index = np.arange(1, len(array) + 1)
    return float(
        (
            2.0 * np.sum(index * array)
            / (len(array) * np.sum(array))
        )
        - (len(array) + 1.0) / len(array)
    )


def _outlier_analysis(
    trades: pd.DataFrame,
    trade_path: str,
) -> dict[str, Any]:
    pnl = pd.to_numeric(
        trades["net_pnl_usd"],
        errors="coerce",
    ).dropna()
    descending = pnl.sort_values(ascending=False)
    ascending = pnl.sort_values()
    total = float(pnl.sum())
    gross_profit = float(pnl.loc[pnl > 0].sum())
    rows: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {}
    for share in (0.01, 0.05, 0.10):
        label = f"{int(share * 100)}pct"
        count = max(1, int(math.ceil(len(pnl) * share)))
        best = float(descending.head(count).sum())
        worst = float(ascending.head(count).sum())
        remaining = float(descending.iloc[count:].sum())
        metrics[f"top_{label}_trade_count"] = count
        metrics[f"top_{label}_pnl_usd"] = best
        metrics[f"bottom_{label}_pnl_usd"] = worst
        metrics[f"net_without_top_{label}_usd"] = remaining
        metrics[f"top_{label}_share_of_net_profit_percent"] = (
            _safe_ratio(best, total) * 100.0
        )
        rows.append(
            {
                "slice": f"Top {int(share * 100)}%",
                "trade_count": count,
                "pnl_usd": best,
                "share_of_net_profit_percent": (
                    _safe_ratio(best, total) * 100.0
                ),
                "net_profit_after_removal_usd": remaining,
            }
        )
        rows.append(
            {
                "slice": f"Bottom {int(share * 100)}%",
                "trade_count": count,
                "pnl_usd": worst,
                "share_of_net_profit_percent": (
                    _safe_ratio(worst, total) * 100.0
                ),
                "net_profit_after_removal_usd": (
                    total - worst
                ),
            }
        )

    winners = pnl.loc[pnl > 0]
    winner_shares = (
        winners / gross_profit
        if gross_profit > 0
        else pd.Series(dtype=float)
    )
    standard_deviation = _sample_std(pnl)
    z_scores = (
        (pnl - float(pnl.mean())) / standard_deviation
        if math.isfinite(standard_deviation)
        and standard_deviation > 0
        else pd.Series(np.nan, index=pnl.index)
    )
    q1 = float(pnl.quantile(0.25)) if len(pnl) else float("nan")
    q3 = float(pnl.quantile(0.75)) if len(pnl) else float("nan")
    iqr = q3 - q1
    metrics.update(
        {
            "largest_trade_share_of_net_profit_percent": (
                _safe_ratio(
                    float(pnl.max())
                    if len(pnl)
                    else float("nan"),
                    total,
                )
                * 100.0
            ),
            "largest_winner_share_of_gross_profit_percent": (
                _safe_ratio(
                    float(winners.max())
                    if len(winners)
                    else float("nan"),
                    gross_profit,
                )
                * 100.0
            ),
            "winner_profit_hhi": (
                float(np.square(winner_shares).sum())
                if len(winner_shares)
                else float("nan")
            ),
            "winner_profit_gini": _gini_nonnegative(winners),
            "absolute_z_score_3_outlier_count": int(
                z_scores.abs().ge(3.0).sum()
            ),
            "iqr_outlier_count": int(
                (
                    (pnl < q1 - 1.5 * iqr)
                    | (pnl > q3 + 1.5 * iqr)
                ).sum()
            )
            if len(pnl)
            else 0,
        }
    )
    return _available_family(
        MetricFamily.OUTLIER_ANALYSIS,
        metrics,
        tables={"concentration_slices": rows},
        evidence_paths=(trade_path,),
    )


def _mae_and_mfe(
    trades: pd.DataFrame,
    spec: AnalyticsSeriesSpec,
) -> dict[str, Any]:
    if not spec.supports_mae_mfe:
        return _unavailable_family(MetricFamily.MAE_AND_MFE)
    mae = pd.to_numeric(trades["mae_usd"], errors="coerce")
    mfe = pd.to_numeric(trades["mfe_usd"], errors="coerce")
    gross = pd.to_numeric(
        trades["gross_pnl_usd"],
        errors="coerce",
    )
    net = pd.to_numeric(
        trades["net_pnl_usd"],
        errors="coerce",
    )
    capture = pd.to_numeric(
        trades["captured_fraction_of_mfe"],
        errors="coerce",
    )
    valid = mae.notna() & mfe.notna()
    if not valid.any():
        return _unavailable_family(MetricFamily.MAE_AND_MFE)

    efficiency = pd.Series(np.nan, index=trades.index)
    efficiency.loc[mfe > 0] = (
        gross.loc[mfe > 0] / mfe.loc[mfe > 0]
    )
    rows: list[dict[str, Any]] = []
    outcomes = {
        "all": valid,
        "winners": valid & net.gt(0),
        "losers": valid & net.lt(0),
        "breakeven": valid & net.eq(0),
    }
    for outcome, mask in outcomes.items():
        rows.append(
            {
                "outcome": outcome,
                "trades": int(mask.sum()),
                "average_mae_usd": float(mae.loc[mask].mean()),
                "median_mae_usd": float(mae.loc[mask].median()),
                "average_mfe_usd": float(mfe.loc[mask].mean()),
                "median_mfe_usd": float(mfe.loc[mask].median()),
                "average_capture_fraction": float(
                    capture.loc[mask].mean()
                ),
                "median_capture_fraction": float(
                    capture.loc[mask].median()
                ),
            }
        )
    return _available_family(
        MetricFamily.MAE_AND_MFE,
        {
            "trades_with_mae_mfe": int(valid.sum()),
            "average_mae_usd": float(mae.loc[valid].mean()),
            "median_mae_usd": float(mae.loc[valid].median()),
            "worst_mae_usd": float(mae.loc[valid].min()),
            "average_absolute_mae_usd": float(
                mae.loc[valid].abs().mean()
            ),
            "average_mfe_usd": float(mfe.loc[valid].mean()),
            "median_mfe_usd": float(mfe.loc[valid].median()),
            "best_mfe_usd": float(mfe.loc[valid].max()),
            "mfe_to_absolute_mae_edge_ratio": _safe_ratio(
                float(mfe.loc[valid].mean()),
                float(mae.loc[valid].abs().mean()),
            ),
            "average_capture_fraction": float(
                capture.loc[valid].mean()
            ),
            "median_capture_fraction": float(
                capture.loc[valid].median()
            ),
            "average_mfe_realization_efficiency": float(
                efficiency.loc[valid].mean()
            ),
            "median_mfe_realization_efficiency": float(
                efficiency.loc[valid].median()
            ),
            "average_missed_mfe_usd": float(
                (mfe.loc[valid] - gross.loc[valid]).mean()
            ),
            "trades_reaching_positive_mfe_percent": (
                float(mfe.loc[valid].gt(0).mean() * 100.0)
            ),
            "trades_with_adverse_excursion_percent": (
                float(mae.loc[valid].lt(0).mean() * 100.0)
            ),
        },
        tables={"by_outcome": rows},
        assumptions={
            "mae_definition": "Frozen pre-exit adverse excursion",
            "mfe_definition": "Frozen pre-exit favorable excursion",
            "capture_source": (
                "Saved captured_fraction_of_mfe field"
            ),
        },
        evidence_paths=(spec.trades_path.as_posix(),),
    )


def _calendar_analysis(
    trades: pd.DataFrame,
    periods: pd.DataFrame,
    spec: AnalyticsSeriesSpec,
) -> dict[str, Any]:
    working = periods.copy()
    working["month"] = working[
        "analysis_date"
    ].dt.strftime("%Y-%m")
    working["year"] = working["analysis_date"].dt.year
    trade_dates = pd.to_datetime(
        trades["session_date"],
        errors="coerce",
    )
    trade_month = trade_dates.dt.strftime("%Y-%m")
    trade_year = trade_dates.dt.year
    trade_pnl = pd.to_numeric(
        trades["net_pnl_usd"],
        errors="coerce",
    )

    monthly: list[dict[str, Any]] = []
    for month, frame in working.groupby("month", sort=True):
        mask = trade_month.eq(month)
        month_trades = trade_pnl.loc[mask].dropna()
        monthly.append(
            {
                "month": month,
                "net_pnl_usd": float(
                    frame["net_pnl_usd"].sum()
                ),
                "return_percent": (
                    float(
                        (
                            np.prod(1.0 + frame["return"])
                            - 1.0
                        )
                        * 100.0
                    )
                ),
                "ending_equity_usd": float(
                    frame["equity_usd"].iloc[-1]
                ),
                "trades": len(month_trades),
                "win_rate_percent": (
                    float(
                        month_trades.gt(0).mean() * 100.0
                    )
                    if len(month_trades)
                    else float("nan")
                ),
            }
        )

    annual: list[dict[str, Any]] = []
    for year, frame in working.groupby("year", sort=True):
        mask = trade_year.eq(year)
        year_trades = trade_pnl.loc[mask].dropna()
        annual.append(
            {
                "year": int(year),
                "net_pnl_usd": float(
                    frame["net_pnl_usd"].sum()
                ),
                "return_percent": (
                    float(
                        (
                            np.prod(1.0 + frame["return"])
                            - 1.0
                        )
                        * 100.0
                    )
                ),
                "ending_equity_usd": float(
                    frame["equity_usd"].iloc[-1]
                ),
                "trades": len(year_trades),
                "win_rate_percent": (
                    float(
                        year_trades.gt(0).mean() * 100.0
                    )
                    if len(year_trades)
                    else float("nan")
                ),
            }
        )

    monthly_frame = pd.DataFrame(monthly)
    annual_frame = pd.DataFrame(annual)
    matrix: list[dict[str, Any]] = []
    if monthly:
        matrix_source = monthly_frame.copy()
        matrix_source["year"] = matrix_source[
            "month"
        ].str.slice(0, 4).astype(int)
        matrix_source["month_number"] = matrix_source[
            "month"
        ].str.slice(5, 7).astype(int)
        pivot = matrix_source.pivot(
            index="year",
            columns="month_number",
            values="net_pnl_usd",
        )
        for year, row in pivot.iterrows():
            record: dict[str, Any] = {"year": int(year)}
            for month in range(1, 13):
                record[f"month_{month:02d}_net_pnl_usd"] = (
                    float(row.get(month))
                    if pd.notna(row.get(month))
                    else None
                )
            record["annual_net_pnl_usd"] = float(
                np.nansum(
                    [
                        value
                        for key, value in record.items()
                        if key.endswith("_net_pnl_usd")
                        and key != "annual_net_pnl_usd"
                        and value is not None
                    ]
                )
            )
            matrix.append(record)

    best_month = (
        monthly_frame.loc[
            monthly_frame["return_percent"].idxmax()
        ].to_dict()
        if not monthly_frame.empty
        else {}
    )
    worst_month = (
        monthly_frame.loc[
            monthly_frame["return_percent"].idxmin()
        ].to_dict()
        if not monthly_frame.empty
        else {}
    )
    best_year = (
        annual_frame.loc[
            annual_frame["return_percent"].idxmax()
        ].to_dict()
        if not annual_frame.empty
        else {}
    )
    worst_year = (
        annual_frame.loc[
            annual_frame["return_percent"].idxmin()
        ].to_dict()
        if not annual_frame.empty
        else {}
    )
    return _available_family(
        MetricFamily.MONTHLY_AND_ANNUAL,
        {
            "calendar_months": len(monthly),
            "profitable_months": int(
                monthly_frame["net_pnl_usd"].gt(0).sum()
            )
            if not monthly_frame.empty
            else 0,
            "profitable_months_percent": (
                float(
                    monthly_frame["net_pnl_usd"]
                    .gt(0)
                    .mean()
                    * 100.0
                )
                if not monthly_frame.empty
                else float("nan")
            ),
            "average_monthly_return_percent": (
                float(monthly_frame["return_percent"].mean())
                if not monthly_frame.empty
                else float("nan")
            ),
            "monthly_return_standard_deviation_percent": (
                _sample_std(monthly_frame["return_percent"])
                if not monthly_frame.empty
                else float("nan")
            ),
            "best_month": best_month.get("month"),
            "best_month_return_percent": best_month.get(
                "return_percent"
            ),
            "worst_month": worst_month.get("month"),
            "worst_month_return_percent": worst_month.get(
                "return_percent"
            ),
            "calendar_years": len(annual),
            "profitable_years": int(
                annual_frame["net_pnl_usd"].gt(0).sum()
            )
            if not annual_frame.empty
            else 0,
            "profitable_years_percent": (
                float(
                    annual_frame["net_pnl_usd"]
                    .gt(0)
                    .mean()
                    * 100.0
                )
                if not annual_frame.empty
                else float("nan")
            ),
            "best_year": best_year.get("year"),
            "best_year_return_percent": best_year.get(
                "return_percent"
            ),
            "worst_year": worst_year.get("year"),
            "worst_year_return_percent": worst_year.get(
                "return_percent"
            ),
        },
        tables={
            "monthly": monthly,
            "annual": annual,
            "monthly_pnl_matrix": matrix,
        },
        assumptions={
            "return_aggregation": (
                "Compounded aligned daily or exchange-session "
                "normalized returns"
            ),
        },
        evidence_paths=(
            spec.trades_path.as_posix(),
            spec.equity_path.as_posix(),
        ),
    )


def _benchmark_analysis(
    periods: pd.DataFrame,
    benchmark: pd.DataFrame | None,
    spec: AnalyticsSeriesSpec,
) -> dict[str, Any]:
    if benchmark is None:
        return _unavailable_family(
            MetricFamily.BENCHMARK_AND_VALUE_ADDED
        )
    benchmark_periods = _benchmark_period_frame(
        benchmark,
        spec.reference_capital_usd,
    )
    aligned = periods.loc[
        :,
        ["analysis_date", "equity_usd"],
    ].merge(
        benchmark_periods.loc[
            :,
            ["analysis_date", "benchmark_equity_usd"],
        ],
        on="analysis_date",
        how="inner",
    )
    if aligned.empty:
        return _unavailable_family(
            MetricFamily.BENCHMARK_AND_VALUE_ADDED
        )

    aligned["strategy_return"] = aligned[
        "equity_usd"
    ].pct_change()
    aligned["benchmark_return"] = aligned[
        "benchmark_equity_usd"
    ].pct_change()
    aligned.loc[0, "strategy_return"] = (
        aligned.loc[0, "equity_usd"]
        / spec.reference_capital_usd
        - 1.0
    )
    aligned.loc[0, "benchmark_return"] = (
        aligned.loc[0, "benchmark_equity_usd"]
        / spec.reference_capital_usd
        - 1.0
    )
    strategy_returns = aligned["strategy_return"]
    benchmark_returns = aligned["benchmark_return"]
    active_returns = strategy_returns - benchmark_returns
    annual_root = math.sqrt(spec.annualization_periods)
    tracking_error = _sample_std(active_returns) * annual_root
    benchmark_variance = float(
        benchmark_returns.var(ddof=1)
    )
    beta = (
        float(
            np.cov(
                strategy_returns,
                benchmark_returns,
                ddof=1,
            )[0, 1]
            / benchmark_variance
        )
        if len(aligned) > 1 and benchmark_variance > 0
        else float("nan")
    )
    alpha = (
        (
            float(strategy_returns.mean())
            - beta * float(benchmark_returns.mean())
        )
        * spec.annualization_periods
        if math.isfinite(beta)
        else float("nan")
    )
    strategy_cash_dd, strategy_percent_dd = _drawdown_arrays(
        aligned["equity_usd"],
        spec.reference_capital_usd,
    )
    benchmark_cash_dd, benchmark_percent_dd = _drawdown_arrays(
        aligned["benchmark_equity_usd"],
        spec.reference_capital_usd,
    )
    years = _elapsed_years(
        aligned.rename(
            columns={"analysis_date": "analysis_date"}
        ),
        spec.annualization_periods,
    )
    strategy_ending = float(aligned["equity_usd"].iloc[-1])
    benchmark_ending = float(
        aligned["benchmark_equity_usd"].iloc[-1]
    )
    strategy_cagr = _cagr(
        strategy_ending,
        spec.reference_capital_usd,
        years,
    )
    benchmark_cagr = _cagr(
        benchmark_ending,
        spec.reference_capital_usd,
        years,
    )
    up = benchmark_returns > 0
    down = benchmark_returns < 0
    comparison_rows = [
        {
            "analysis_date": row.analysis_date,
            "strategy_equity_usd": row.equity_usd,
            "benchmark_equity_usd": row.benchmark_equity_usd,
            "strategy_return_percent": (
                row.strategy_return * 100.0
            ),
            "benchmark_return_percent": (
                row.benchmark_return * 100.0
            ),
            "active_return_percent": (
                (row.strategy_return - row.benchmark_return)
                * 100.0
            ),
        }
        for row in aligned.itertuples(index=False)
    ]
    return _available_family(
        MetricFamily.BENCHMARK_AND_VALUE_ADDED,
        {
            "aligned_periods": len(aligned),
            "strategy_ending_equity_usd": strategy_ending,
            "benchmark_ending_equity_usd": benchmark_ending,
            "value_added_usd": (
                strategy_ending - benchmark_ending
            ),
            "strategy_total_return_percent": (
                (
                    strategy_ending
                    / spec.reference_capital_usd
                    - 1.0
                )
                * 100.0
            ),
            "benchmark_total_return_percent": (
                (
                    benchmark_ending
                    / spec.reference_capital_usd
                    - 1.0
                )
                * 100.0
            ),
            "excess_total_return_percent": (
                (strategy_ending - benchmark_ending)
                / spec.reference_capital_usd
                * 100.0
            ),
            "strategy_cagr_percent": strategy_cagr * 100.0,
            "benchmark_cagr_percent": benchmark_cagr * 100.0,
            "excess_cagr_percent": (
                (strategy_cagr - benchmark_cagr) * 100.0
            ),
            "strategy_maximum_drawdown_usd": (
                float(np.nanmin(strategy_cash_dd))
                if len(strategy_cash_dd)
                else 0.0
            ),
            "benchmark_maximum_drawdown_usd": (
                float(np.nanmin(benchmark_cash_dd))
                if len(benchmark_cash_dd)
                else 0.0
            ),
            "strategy_maximum_drawdown_percent": (
                float(np.nanmin(strategy_percent_dd)) * 100.0
                if len(strategy_percent_dd)
                else 0.0
            ),
            "benchmark_maximum_drawdown_percent": (
                float(np.nanmin(benchmark_percent_dd)) * 100.0
                if len(benchmark_percent_dd)
                else 0.0
            ),
            "return_correlation": (
                float(
                    strategy_returns.corr(benchmark_returns)
                )
                if len(aligned) > 1
                else float("nan")
            ),
            "beta": beta,
            "annualized_alpha_percent": alpha * 100.0,
            "annualized_tracking_error_percent": (
                tracking_error * 100.0
            ),
            "information_ratio": _safe_ratio(
                float(active_returns.mean())
                * spec.annualization_periods,
                tracking_error,
            ),
            "active_period_win_rate_percent": (
                float(active_returns.gt(0).mean() * 100.0)
            ),
            "up_market_capture_percent": (
                _safe_ratio(
                    float(strategy_returns.loc[up].mean()),
                    float(benchmark_returns.loc[up].mean()),
                )
                * 100.0
            ),
            "down_market_capture_percent": (
                _safe_ratio(
                    float(strategy_returns.loc[down].mean()),
                    float(benchmark_returns.loc[down].mean()),
                )
                * 100.0
            ),
        },
        tables={"aligned_periods": comparison_rows},
        assumptions={
            "benchmark_description": (
                "Normalized underlying price path, not a literal "
                "one-contract futures portfolio"
            ),
            "reference_capital_usd": spec.reference_capital_usd,
            "annualization_periods": spec.annualization_periods,
            "risk_free_rate_percent": 0.0,
        },
        evidence_paths=tuple(
            path.as_posix()
            for path in spec.benchmark_paths
        ),
    )


def _robustness_family(
    evidence: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    rows = [dict(item) for item in evidence]
    if not rows:
        return _unavailable_family(
            MetricFamily.EXISTING_ROBUSTNESS
        )
    suffix_counts = Counter(
        Path(str(row["path"])).suffix.lower()
        for row in rows
    )
    return _available_family(
        MetricFamily.EXISTING_ROBUSTNESS,
        {
            "artifact_count": len(rows),
            "total_bytes": sum(
                int(row.get("size_bytes", 0))
                for row in rows
            ),
            "csv_artifacts": suffix_counts[".csv"],
            "json_artifacts": suffix_counts[".json"],
            "markdown_artifacts": suffix_counts[".md"],
            "text_artifacts": suffix_counts[".txt"],
        },
        tables={"evidence_files": rows},
        assumptions={
            "treatment": (
                "Existing robustness artifacts are catalogued and "
                "hashed; no MCPT, bootstrap, walk-forward, or "
                "optimization is rerun"
            )
        },
        evidence_paths=tuple(
            str(row["path"])
            for row in rows
        ),
    )


def compute_series_analytics(
    trades: pd.DataFrame,
    equity: pd.DataFrame,
    spec: AnalyticsSeriesSpec,
    *,
    benchmark: pd.DataFrame | None = None,
    evidence_records: Iterable[Mapping[str, Any]] = (),
    robustness_records: Iterable[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    if set(trades["series_id"].astype(str)) != {spec.series_id}:
        raise ValueError("Trade evidence does not match the series ID.")
    if set(equity["series_id"].astype(str)) != {spec.series_id}:
        raise ValueError("Equity evidence does not match the series ID.")
    periods = _period_frame(
        equity,
        spec.reference_capital_usd,
    )
    if periods.empty:
        raise ValueError(
            f"{spec.series_id} has no canonical equity periods."
        )
    trade_total = float(
        pd.to_numeric(
            trades["net_pnl_usd"],
            errors="coerce",
        ).sum()
    )
    equity_total = (
        float(periods["equity_usd"].iloc[-1])
        - spec.reference_capital_usd
    )
    reconciliation_difference = equity_total - trade_total
    reconciliation_tolerance = max(
        0.01,
        abs(trade_total) * 1e-9,
    )

    evidence_rows = [dict(item) for item in evidence_records]
    robustness_rows = [
        dict(item)
        for item in robustness_records
    ]
    benchmark_family = _benchmark_analysis(
        periods,
        benchmark,
        spec,
    )
    families = {
        MetricFamily.PERFORMANCE_SUMMARY.value: (
            _performance_summary(
                trades,
                periods,
                spec,
                benchmark_family,
            )
        ),
        MetricFamily.TOTAL_TRADE_ANALYSIS.value: (
            _total_trade_analysis(
                trades,
                spec.trades_path.as_posix(),
            )
        ),
        MetricFamily.PERFORMANCE_RATIOS.value: (
            _performance_ratios(trades, periods, spec)
        ),
        MetricFamily.TIME_AND_EXPOSURE.value: (
            _time_and_exposure(trades, periods, spec)
        ),
        MetricFamily.EQUITY_AND_DRAWDOWN.value: (
            _equity_and_drawdown(periods, spec)
        ),
        MetricFamily.WIN_LOSS_DISTRIBUTIONS.value: (
            _win_loss_distributions(
                trades,
                spec.trades_path.as_posix(),
            )
        ),
        MetricFamily.STREAK_AND_TRADE_SERIES.value: (
            _streak_and_trade_series(
                trades,
                spec.trades_path.as_posix(),
            )
        ),
        MetricFamily.OUTLIER_ANALYSIS.value: (
            _outlier_analysis(
                trades,
                spec.trades_path.as_posix(),
            )
        ),
        MetricFamily.MAE_AND_MFE.value: (
            _mae_and_mfe(trades, spec)
        ),
        MetricFamily.MONTHLY_AND_ANNUAL.value: (
            _calendar_analysis(trades, periods, spec)
        ),
        MetricFamily.BENCHMARK_AND_VALUE_ADDED.value: (
            benchmark_family
        ),
        MetricFamily.EXISTING_ROBUSTNESS.value: (
            _robustness_family(robustness_rows)
        ),
    }
    result = {
        "schema_version": ANALYTICS_SCHEMA_VERSION,
        "series": {
            "series_id": spec.series_id,
            "experiment_id": spec.experiment_id,
            "display_name": spec.display_name,
            "market": spec.market,
            "variant_id": spec.variant_id,
            "candidate_id": spec.candidate_id,
            "family_id": spec.family_id,
        },
        "analysis_boundary": {
            "mode": "frozen_evidence_reporting_only",
            "strategy_rerun": False,
            "optimization_rerun": False,
            "walk_forward_rerun": False,
            "mcpt_rerun": False,
            "bootstrap_rerun": False,
            "market_data_request": False,
        },
        "reference_model": {
            "reference_capital_usd": (
                spec.reference_capital_usd
            ),
            "annualization_periods": spec.annualization_periods,
            "timezone": spec.timezone,
        },
        "integrity": {
            "trade_count": len(trades),
            "equity_period_count": len(periods),
            "trade_net_pnl_usd": trade_total,
            "equity_net_pnl_usd": equity_total,
            "reconciliation_difference_usd": (
                reconciliation_difference
            ),
            "reconciliation_tolerance_usd": (
                reconciliation_tolerance
            ),
            "trade_equity_reconciled": (
                abs(reconciliation_difference)
                <= reconciliation_tolerance
            ),
        },
        "evidence": evidence_rows,
        "metric_families": families,
    }
    return json_safe(result)


def summary_row(result: Mapping[str, Any]) -> dict[str, Any]:
    series = result["series"]
    families = result["metric_families"]
    performance = families[
        MetricFamily.PERFORMANCE_SUMMARY.value
    ]["metrics"]["all"]
    ratios = families[
        MetricFamily.PERFORMANCE_RATIOS.value
    ]["metrics"]
    equity = families[
        MetricFamily.EQUITY_AND_DRAWDOWN.value
    ]["metrics"]
    calendar = families[
        MetricFamily.MONTHLY_AND_ANNUAL.value
    ]["metrics"]
    benchmark = families[
        MetricFamily.BENCHMARK_AND_VALUE_ADDED.value
    ]
    return json_safe(
        {
            **series,
            "completed_trades": performance["completed_trades"],
            "net_profit_usd": performance["net_profit_usd"],
            "profit_factor": performance["profit_factor"],
            "win_rate_percent": performance[
                "win_rate_percent"
            ],
            "average_trade_usd": performance[
                "average_trade_usd"
            ],
            "normalized_total_return_percent": ratios[
                "normalized_total_return_percent"
            ],
            "normalized_cagr_percent": ratios[
                "normalized_cagr_percent"
            ],
            "return_on_maximum_strategy_drawdown": performance[
                "return_on_maximum_strategy_drawdown"
            ],
            "maximum_contracts_held": performance[
                "maximum_contracts_held"
            ],
            "monthly_rate_of_return_percent": performance[
                "monthly_rate_of_return_percent"
            ],
            "buy_and_hold_return_usd": performance[
                "buy_and_hold_return_usd"
            ],
            "buy_and_hold_return_percent": performance[
                "buy_and_hold_return_percent"
            ],
            "sharpe_ratio": ratios[
                "sharpe_ratio_zero_risk_free"
            ],
            "sortino_ratio": ratios[
                "sortino_ratio_zero_target"
            ],
            "maximum_drawdown_usd": equity[
                "maximum_drawdown_usd"
            ],
            "maximum_drawdown_percent": equity[
                "maximum_drawdown_percent"
            ],
            "profitable_months_percent": calendar[
                "profitable_months_percent"
            ],
            "benchmark_status": benchmark["status"],
            "excess_total_return_percent": benchmark[
                "metrics"
            ].get("excess_total_return_percent"),
            "trade_equity_reconciled": result[
                "integrity"
            ]["trade_equity_reconciled"],
        }
    )
