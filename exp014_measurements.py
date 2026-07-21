from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
import pandas as pd

from exp009_engine import Exp009Result, maximum_drawdown, profit_factor
from exp012_engine import Exp012Arrays
from exp014_preregistration import FINALIST_IDS, PAIR_DEFINITIONS


NQ_MULTIPLIER_USD_PER_POINT = 20.0
REFERENCE_CAPITAL_USD = 100_000.0
ROLLING_TRADE_WINDOWS: tuple[int, ...] = (20, 50)


def _safe_correlation(left: np.ndarray, right: np.ndarray) -> float:
    x = np.asarray(left, dtype=float)
    y = np.asarray(right, dtype=float)
    valid = np.isfinite(x) & np.isfinite(y)
    x = x[valid]
    y = y[valid]
    if x.size < 2 or np.std(x) == 0 or np.std(y) == 0:
        return 0.0
    return float(np.corrcoef(x, y)[0, 1])


def session_regime_table(arrays: Exp012Arrays) -> tuple[pd.DataFrame, float]:
    """Build entry-known trend and volatility labels.

    Both measurements end at the prior completed cash session. The volatility
    boundary is calibrated once from 2020-01-03 through 2021-12-31.
    """

    dates = pd.to_datetime(arrays.session_dates)
    closes = pd.Series(
        arrays.cash.close[:, -1].astype(float),
        index=dates,
    )
    returns = closes.pct_change(fill_method=None)
    prior_return = closes.shift(1).div(closes.shift(21)).sub(1.0)
    prior_volatility = returns.shift(1).rolling(20).std()
    calibration = prior_volatility.loc[
        (prior_volatility.index >= pd.Timestamp("2020-01-03"))
        & (prior_volatility.index <= pd.Timestamp("2021-12-31"))
    ].dropna()
    if calibration.empty:
        raise ValueError("EXP-014 volatility calibration is empty.")
    boundary = float(calibration.median())
    trend = np.where(
        prior_return.isna(),
        "UNAVAILABLE",
        np.where(prior_return > 0.0, "UP", "DOWN_OR_FLAT"),
    )
    volatility = np.where(
        prior_volatility.isna(),
        "UNAVAILABLE",
        np.where(prior_volatility <= boundary, "LOW", "HIGH"),
    )
    frame = pd.DataFrame(
        {
            "session_date": dates.strftime("%Y-%m-%d"),
            "prior_20_session_return": prior_return.to_numpy(),
            "prior_20_session_volatility": prior_volatility.to_numpy(),
            "trend_regime": trend,
            "volatility_regime": volatility,
        }
    )
    return frame, boundary


def _clock_label(minute_slot: int) -> str:
    total = 9 * 60 + 30 + int(minute_slot)
    return f"{total // 60:02d}:{total % 60:02d}"


def _context_band(candidate_id: str, value: float) -> str:
    if not np.isfinite(value):
        return "UNAVAILABLE"
    if candidate_id == "gap_fade_0p50_1r":
        if value < 0.75:
            return "0.50-0.75"
        if value < 1.0:
            return "0.75-1.00"
        return "1.00+"
    if value < 0.625:
        return "0.50-0.625"
    if value < 0.75:
        return "0.625-0.75"
    if value < 0.875:
        return "0.75-0.875"
    return "0.875-1.00"


def _holding_band(value: float) -> str:
    if value < 15:
        return "0-14 minutes"
    if value < 60:
        return "15-59 minutes"
    if value < 180:
        return "60-179 minutes"
    return "180+ minutes"


def _trade_excursions(
    arrays: Exp012Arrays,
    trade: Mapping[str, Any],
    *,
    date_to_index: Mapping[str, int],
) -> tuple[float, float]:
    """Return pre-exit MFE and MAE in NQ dollars.

    Complete one-minute bars are included from the entry minute through the
    minute immediately before the exit. The exit minute contributes only the
    actual fill price so post-exit extremes cannot leak into the diagnostic.
    """

    session = date_to_index[str(trade["session_date"])]
    entry_minute = int(trade["entry_minute_slot"])
    exit_minute = int(trade["exit_minute_slot"])
    entry = float(trade["entry_price"])
    exit_price = float(trade["exit_price"])
    direction = 1.0 if str(trade["direction"]).lower() == "long" else -1.0

    realised_points = direction * (exit_price - entry)
    favourable = [0.0, realised_points]
    adverse = [0.0, realised_points]
    for minute in range(entry_minute, max(entry_minute, exit_minute)):
        high = float(arrays.cash.high[session, minute])
        low = float(arrays.cash.low[session, minute])
        if direction > 0:
            favourable.append(high - entry)
            adverse.append(low - entry)
        else:
            favourable.append(entry - low)
            adverse.append(entry - high)
    return (
        max(favourable) * NQ_MULTIPLIER_USD_PER_POINT,
        min(adverse) * NQ_MULTIPLIER_USD_PER_POINT,
    )


def enrich_trade_ledger(
    arrays: Exp012Arrays,
    result: Exp009Result,
    regimes: pd.DataFrame,
) -> pd.DataFrame:
    trades = result.trades.copy()
    if trades.empty:
        return trades
    trades["session_date"] = trades["session_date"].astype(str)
    regime_columns = [
        "session_date",
        "prior_20_session_return",
        "prior_20_session_volatility",
        "trend_regime",
        "volatility_regime",
    ]
    trades = trades.merge(
        regimes[regime_columns],
        on="session_date",
        how="left",
        validate="many_to_one",
    )
    trades["entry_time"] = trades["entry_minute_slot"].map(_clock_label)
    trades["exit_time"] = trades["exit_minute_slot"].map(_clock_label)
    trades["holding_time_band"] = trades["holding_minutes"].map(
        _holding_band
    )
    trades["context_strength_band"] = [
        _context_band(str(candidate_id), float(context_value))
        for candidate_id, context_value in zip(
            trades["candidate_id"], trades["context_value"]
        )
    ]
    date_to_index = {
        str(value): index for index, value in enumerate(arrays.session_dates)
    }
    excursions = [
        _trade_excursions(arrays, row, date_to_index=date_to_index)
        for row in trades.to_dict(orient="records")
    ]
    trades["pre_exit_mfe_usd"] = [value[0] for value in excursions]
    trades["pre_exit_mae_usd"] = [value[1] for value in excursions]
    trades["captured_fraction_of_mfe"] = np.where(
        trades["pre_exit_mfe_usd"] > 0,
        trades["gross_pnl_usd"] / trades["pre_exit_mfe_usd"],
        np.nan,
    )
    trades["month"] = pd.to_datetime(
        trades["session_date"]
    ).dt.to_period("M").astype(str)
    trades = trades.sort_values(
        ["session_date", "entry_minute_slot"], kind="stable"
    ).reset_index(drop=True)
    trades["candidate_trade_number"] = np.arange(1, len(trades) + 1)
    return trades


def _max_losing_streak(values: np.ndarray) -> int:
    longest = 0
    current = 0
    for value in values:
        if value < 0:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def _summary(values: np.ndarray) -> dict[str, float | int]:
    pnl = np.asarray(values, dtype=float)
    wins = pnl[pnl > 0]
    losses = pnl[pnl < 0]
    drawdown = maximum_drawdown(pnl)
    return {
        "completed_trades": int(pnl.size),
        "net_profit_usd": float(pnl.sum()),
        "profit_factor": float(profit_factor(pnl)),
        "win_rate": float(np.mean(pnl > 0)) if pnl.size else 0.0,
        "average_trade_usd": float(pnl.mean()) if pnl.size else 0.0,
        "median_trade_usd": float(np.median(pnl)) if pnl.size else 0.0,
        "average_winner_usd": float(wins.mean()) if wins.size else 0.0,
        "average_loser_usd": float(losses.mean()) if losses.size else 0.0,
        "payoff_ratio": (
            float(wins.mean() / abs(losses.mean()))
            if wins.size and losses.size
            else 0.0
        ),
        "maximum_drawdown_usd": float(drawdown),
        "net_profit_to_drawdown": (
            float(pnl.sum() / abs(drawdown)) if drawdown < 0 else 0.0
        ),
        "maximum_losing_streak": _max_losing_streak(pnl),
    }


def behaviour_breakdowns(
    ledgers: Mapping[str, pd.DataFrame],
) -> pd.DataFrame:
    dimensions = {
        "year": "year",
        "direction": "direction",
        "exit_reason": "exit_reason",
        "holding_time": "holding_time_band",
        "context_strength": "context_strength_band",
        "trend_regime": "trend_regime",
        "volatility_regime": "volatility_regime",
        "entry_time": "entry_time",
        "exit_time": "exit_time",
    }
    rows: list[dict[str, Any]] = []
    for candidate_id in FINALIST_IDS:
        trades = ledgers[candidate_id]
        for dimension, column in dimensions.items():
            for value, group in trades.groupby(column, dropna=False):
                rows.append(
                    {
                        "candidate_id": candidate_id,
                        "dimension": dimension,
                        "value": str(value),
                        **_summary(
                            group["net_pnl_usd"].to_numpy(dtype=float)
                        ),
                    }
                )
    return pd.DataFrame.from_records(rows)


def period_comparison(
    ledgers: Mapping[str, pd.DataFrame],
) -> pd.DataFrame:
    periods = {
        "2020-2024": lambda year: year <= 2024,
        "2022-2024": lambda year: (year >= 2022) & (year <= 2024),
        "2025": lambda year: year == 2025,
    }
    rows: list[dict[str, Any]] = []
    for candidate_id in FINALIST_IDS:
        trades = ledgers[candidate_id]
        years = trades["year"].astype(int)
        for period, selector in periods.items():
            local = trades.loc[selector(years)].copy()
            summary = _summary(
                local["net_pnl_usd"].to_numpy(dtype=float)
            )
            exits = local["exit_reason"].astype(str)
            rows.append(
                {
                    "candidate_id": candidate_id,
                    "period": period,
                    **summary,
                    "long_share": (
                        float(local["direction"].eq("long").mean())
                        if len(local)
                        else 0.0
                    ),
                    "stop_exit_share": (
                        float(
                            exits.isin(
                                ["protective_stop", "gap_through_stop"]
                            ).mean()
                        )
                        if len(local)
                        else 0.0
                    ),
                    "target_exit_share": (
                        float(exits.eq("profit_target").mean())
                        if len(local)
                        else 0.0
                    ),
                    "time_exit_share": (
                        float(exits.eq("forced_flat_1555").mean())
                        if len(local)
                        else 0.0
                    ),
                    "average_holding_minutes": (
                        float(local["holding_minutes"].mean())
                        if len(local)
                        else 0.0
                    ),
                    "average_mfe_usd": (
                        float(local["pre_exit_mfe_usd"].mean())
                        if len(local)
                        else 0.0
                    ),
                    "average_mae_usd": (
                        float(local["pre_exit_mae_usd"].mean())
                        if len(local)
                        else 0.0
                    ),
                }
            )
    return pd.DataFrame.from_records(rows)


def monthly_measurements(
    session_pnl: pd.DataFrame,
    ledgers: Mapping[str, pd.DataFrame],
) -> pd.DataFrame:
    dates = pd.to_datetime(session_pnl["session_date"])
    months = pd.period_range(
        dates.min().to_period("M"),
        dates.max().to_period("M"),
        freq="M",
    )
    rows: list[dict[str, Any]] = []
    for candidate_id in FINALIST_IDS:
        trades = ledgers[candidate_id].copy()
        trade_month = pd.to_datetime(
            trades["session_date"]
        ).dt.to_period("M")
        for month in months:
            local = trades.loc[trade_month.eq(month)]
            rows.append(
                {
                    "candidate_id": candidate_id,
                    "month": str(month),
                    "year": int(month.year),
                    "month_number": int(month.month),
                    **_summary(
                        local["net_pnl_usd"].to_numpy(dtype=float)
                    ),
                }
            )
    return pd.DataFrame.from_records(rows)


def rolling_trade_measurements(
    ledgers: Mapping[str, pd.DataFrame],
    *,
    windows: Sequence[int] = ROLLING_TRADE_WINDOWS,
) -> pd.DataFrame:
    normalized_windows = tuple(sorted({int(value) for value in windows}))
    if not normalized_windows or any(value <= 1 for value in normalized_windows):
        raise ValueError("EXP-014 rolling windows must exceed one trade.")
    rows: list[dict[str, Any]] = []
    for candidate_id in FINALIST_IDS:
        trades = ledgers[candidate_id].sort_values(
            ["session_date", "entry_minute_slot"], kind="stable"
        ).reset_index(drop=True)
        pnl = trades["net_pnl_usd"].to_numpy(dtype=float)
        for window in normalized_windows:
            for end in range(window - 1, len(trades)):
                start = end - window + 1
                local = pnl[start : end + 1]
                rows.append(
                    {
                        "candidate_id": candidate_id,
                        "window_trades": window,
                        "window_start_trade_number": start + 1,
                        "window_end_trade_number": end + 1,
                        "window_start_session_date": str(
                            trades.loc[start, "session_date"]
                        ),
                        "window_end_session_date": str(
                            trades.loc[end, "session_date"]
                        ),
                        **_summary(local),
                    }
                )
    return pd.DataFrame.from_records(rows)


def concentration_measurements(
    ledgers: Mapping[str, pd.DataFrame],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for candidate_id in FINALIST_IDS:
        trades = ledgers[candidate_id]
        pnl = trades["net_pnl_usd"].to_numpy(dtype=float)
        sorted_desc = np.sort(pnl)[::-1]
        total = float(pnl.sum())
        row: dict[str, Any] = {
            "candidate_id": candidate_id,
            "completed_trades": int(pnl.size),
            "net_profit_usd": total,
            "maximum_losing_streak": _max_losing_streak(pnl),
        }
        for count in (1, 5, 10):
            row[f"net_after_removing_best_{count}_usd"] = float(
                total - sorted_desc[:count].sum()
            )
        for percent in (1, 5, 10):
            count = max(1, int(np.ceil(pnl.size * percent / 100)))
            row[f"top_{percent}_percent_profit_share"] = (
                float(sorted_desc[:count].sum() / total)
                if total != 0
                else 0.0
            )
        for window in (20, 50, 100):
            row[f"worst_{window}_trade_result_usd"] = (
                float(
                    pd.Series(pnl).rolling(window).sum().min()
                )
                if pnl.size >= window
                else np.nan
            )
        rows.append(row)
    return pd.DataFrame.from_records(rows)


def session_pnl_table(
    arrays: Exp012Arrays,
    ledgers: Mapping[str, pd.DataFrame],
) -> pd.DataFrame:
    frame = pd.DataFrame(
        {"session_date": arrays.session_dates.astype(str)}
    )
    for candidate_id in FINALIST_IDS:
        pnl = ledgers[candidate_id].groupby("session_date")[
            "net_pnl_usd"
        ].sum()
        frame[candidate_id] = frame["session_date"].map(pnl).fillna(0.0)
    return frame


def _session_directions(
    ledgers: Mapping[str, pd.DataFrame],
) -> dict[str, dict[str, int]]:
    output: dict[str, dict[str, int]] = {}
    for candidate_id in FINALIST_IDS:
        trades = ledgers[candidate_id]
        if trades["session_date"].duplicated().any():
            raise ValueError(
                f"EXP-014 expected at most one {candidate_id} trade per session."
            )
        output[candidate_id] = {
            str(row["session_date"]): (
                1 if str(row["direction"]).lower() == "long" else -1
            )
            for row in trades.to_dict(orient="records")
        }
    return output


def overlap_measurements(
    session_pnl: pd.DataFrame,
    ledgers: Mapping[str, pd.DataFrame],
) -> pd.DataFrame:
    directions = _session_directions(ledgers)
    rows: list[dict[str, Any]] = []
    date_values = session_pnl["session_date"].astype(str).to_numpy()
    for left_index, left_id in enumerate(FINALIST_IDS):
        for right_id in FINALIST_IDS[left_index + 1:]:
            left = session_pnl[left_id].to_numpy(dtype=float)
            right = session_pnl[right_id].to_numpy(dtype=float)
            left_active = np.array(
                [date in directions[left_id] for date in date_values]
            )
            right_active = np.array(
                [date in directions[right_id] for date in date_values]
            )
            overlap = left_active & right_active
            same = 0
            opposite = 0
            for date in date_values[overlap]:
                if directions[left_id][date] == directions[right_id][date]:
                    same += 1
                else:
                    opposite += 1
            left_equity = np.cumsum(left)
            left_dd = left_equity - np.maximum.accumulate(
                np.r_[0.0, left_equity]
            )[1:]
            right_equity = np.cumsum(right)
            right_dd = right_equity - np.maximum.accumulate(
                np.r_[0.0, right_equity]
            )[1:]
            rows.append(
                {
                    "left_candidate_id": left_id,
                    "right_candidate_id": right_id,
                    "left_active_sessions": int(left_active.sum()),
                    "right_active_sessions": int(right_active.sum()),
                    "overlap_sessions": int(overlap.sum()),
                    "same_direction_overlap": same,
                    "opposite_direction_overlap": opposite,
                    "both_win_overlap": int(
                        ((left > 0) & (right > 0) & overlap).sum()
                    ),
                    "both_lose_overlap": int(
                        ((left < 0) & (right < 0) & overlap).sum()
                    ),
                    "offsetting_outcome_overlap": int(
                        (
                            (
                                ((left > 0) & (right < 0))
                                | ((left < 0) & (right > 0))
                            )
                            & overlap
                        ).sum()
                    ),
                    "all_session_pnl_correlation": _safe_correlation(
                        left, right
                    ),
                    "active_overlap_pnl_correlation": _safe_correlation(
                        left[overlap], right[overlap]
                    ),
                    "drawdown_correlation": _safe_correlation(
                        left_dd, right_dd
                    ),
                    "simultaneous_underwater_share": float(
                        ((left_dd < 0) & (right_dd < 0)).mean()
                    ),
                }
            )
    return pd.DataFrame.from_records(rows)


def sleeve_pair_measurements(
    session_pnl: pd.DataFrame,
    ledgers: Mapping[str, pd.DataFrame],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    directions = _session_directions(ledgers)
    pair_daily = session_pnl[["session_date"]].copy()
    dates = pd.to_datetime(pair_daily["session_date"])
    date_values = pair_daily["session_date"].astype(str).to_numpy()
    rows: list[dict[str, Any]] = []
    for pair in PAIR_DEFINITIONS:
        pair_id = str(pair["pair_id"])
        left_id = str(pair["first_candidate_id"])
        right_id = str(pair["second_candidate_id"])
        pnl = (
            session_pnl[left_id].to_numpy(dtype=float)
            + session_pnl[right_id].to_numpy(dtype=float)
        )
        pair_daily[pair_id] = pnl
        left_active = np.array(
            [date in directions[left_id] for date in date_values]
        )
        right_active = np.array(
            [date in directions[right_id] for date in date_values]
        )
        active = left_active | right_active
        overlap = left_active & right_active
        active_pnl = pnl[active]
        drawdown = maximum_drawdown(pnl)
        annual = pd.Series(pnl, index=dates).groupby(dates.dt.year).sum()
        monthly_period = dates.dt.to_period("M")
        monthly = pd.Series(
            pnl, index=monthly_period.to_numpy()
        ).groupby(level=0).sum()
        opposite = 0
        for date in date_values[overlap]:
            if directions[left_id][date] != directions[right_id][date]:
                opposite += 1
        rows.append(
            {
                "pair_id": pair_id,
                "first_candidate_id": left_id,
                "second_candidate_id": right_id,
                "component_trades": int(left_active.sum() + right_active.sum()),
                "active_sessions": int(active.sum()),
                "overlap_sessions": int(overlap.sum()),
                "opposite_direction_overlap": opposite,
                "net_profit_usd": float(pnl.sum()),
                "maximum_drawdown_usd": float(drawdown),
                "net_profit_to_drawdown": (
                    float(pnl.sum() / abs(drawdown))
                    if drawdown < 0
                    else 0.0
                ),
                "session_profit_factor": float(profit_factor(active_pnl)),
                "session_win_rate": (
                    float(np.mean(active_pnl > 0))
                    if active_pnl.size
                    else 0.0
                ),
                "profitable_years": int((annual > 0).sum()),
                "total_years": int(len(annual)),
                "profitable_months": int((monthly > 0).sum()),
                "total_months": int(len(monthly)),
                "worst_year_usd": float(annual.min()),
                "worst_month_usd": float(monthly.min()),
                "maximum_gross_contracts": 2,
                "diagnostic_not_executable_portfolio": True,
            }
        )
    return pd.DataFrame.from_records(rows), pair_daily


def _longest_true_run(mask: np.ndarray) -> tuple[int, int | None, int | None]:
    longest = 0
    best_start: int | None = None
    best_end: int | None = None
    current_start: int | None = None
    for index, value in enumerate(np.asarray(mask, dtype=bool)):
        if value and current_start is None:
            current_start = index
        if not value and current_start is not None:
            length = index - current_start
            if length > longest:
                longest = length
                best_start = current_start
                best_end = index - 1
            current_start = None
    if current_start is not None:
        length = len(mask) - current_start
        if length > longest:
            longest = length
            best_start = current_start
            best_end = len(mask) - 1
    return longest, best_start, best_end


def _drawdown_diagnostic(
    *,
    series_id: str,
    series_type: str,
    dates: pd.Series,
    pnl: np.ndarray,
) -> dict[str, Any]:
    values = np.asarray(pnl, dtype=float)
    equity = np.cumsum(values)
    augmented = np.r_[0.0, equity]
    peaks = np.maximum.accumulate(augmented)
    drawdown = augmented - peaks
    trough_augmented = int(np.argmin(drawdown))
    trough_index = trough_augmented - 1
    peak_value = float(peaks[trough_augmented])
    peak_positions = np.flatnonzero(
        np.isclose(augmented[: trough_augmented + 1], peak_value)
    )
    peak_augmented = int(peak_positions[-1]) if peak_positions.size else 0
    peak_index = peak_augmented - 1
    recovery_index: int | None = None
    if trough_index >= 0:
        recovered = np.flatnonzero(
            equity[trough_index + 1 :] >= peak_value
        )
        if recovered.size:
            recovery_index = trough_index + 1 + int(recovered[0])

    underwater = drawdown[1:] < 0
    longest, underwater_start, underwater_end = _longest_true_run(underwater)
    date_values = dates.astype(str).to_numpy()

    def date_at(index: int | None) -> str | None:
        if index is None or index < 0 or index >= len(date_values):
            return None
        return str(date_values[index])

    return {
        "series_id": series_id,
        "series_type": series_type,
        "maximum_drawdown_usd": float(drawdown.min()),
        "maximum_drawdown_peak_session": date_at(peak_index),
        "maximum_drawdown_trough_session": date_at(trough_index),
        "maximum_drawdown_recovery_session": date_at(recovery_index),
        "decline_duration_sessions": (
            int(trough_index - peak_index) if trough_index >= 0 else 0
        ),
        "recovery_duration_sessions": (
            int(recovery_index - trough_index)
            if recovery_index is not None and trough_index >= 0
            else np.nan
        ),
        "maximum_drawdown_recovered": recovery_index is not None,
        "longest_underwater_sessions": int(longest),
        "longest_underwater_start_session": date_at(underwater_start),
        "longest_underwater_end_session": date_at(underwater_end),
        "underwater_session_share": float(underwater.mean())
        if underwater.size
        else 0.0,
        "ending_underwater": bool(underwater[-1]) if underwater.size else False,
    }


def drawdown_diagnostics(
    session_pnl: pd.DataFrame,
    pair_session_pnl: pd.DataFrame,
) -> pd.DataFrame:
    dates = session_pnl["session_date"]
    rows = [
        _drawdown_diagnostic(
            series_id=candidate_id,
            series_type="standalone",
            dates=dates,
            pnl=session_pnl[candidate_id].to_numpy(dtype=float),
        )
        for candidate_id in FINALIST_IDS
    ]
    rows.extend(
        _drawdown_diagnostic(
            series_id=str(pair["pair_id"]),
            series_type="research_sleeve_pair",
            dates=dates,
            pnl=pair_session_pnl[str(pair["pair_id"])].to_numpy(dtype=float),
        )
        for pair in PAIR_DEFINITIONS
    )
    return pd.DataFrame.from_records(rows)
