from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from exp005_futures_orb import get_contract_spec
from exp005_session_mcpt import validate_one_minute_data


EXPECTED_MINUTES_PER_SESSION = 390
EXPECTED_FIVE_MINUTE_BARS = 78
OPENING_RANGE_MINUTES = 30
OPENING_RANGE_FIVE_MINUTE_BARS = 6
FIRST_SIGNAL_FIVE_MINUTE_SLOT = 6
LAST_SIGNAL_FIVE_MINUTE_SLOT = 52
FORCED_FLAT_MINUTE_SLOT = 270
REFERENCE_CAPITAL_USD = {
    "NQ": 100_000.0,
    "MNQ": 10_000.0,
}


@dataclass(frozen=True)
class Exp007Arrays:
    session_dates: np.ndarray
    years: np.ndarray
    open: np.ndarray
    high: np.ndarray
    low: np.ndarray
    close: np.ndarray
    volume: np.ndarray
    index_ns: np.ndarray | None = None

    @property
    def session_count(self) -> int:
        return int(self.open.shape[0])

    def subset(self, mask: np.ndarray) -> "Exp007Arrays":
        selected = np.asarray(mask, dtype=bool)
        if selected.shape != (self.session_count,):
            raise ValueError("EXP-007 session mask has the wrong shape.")
        return Exp007Arrays(
            session_dates=self.session_dates[selected],
            years=self.years[selected],
            open=self.open[selected],
            high=self.high[selected],
            low=self.low[selected],
            close=self.close[selected],
            volume=self.volume[selected],
            index_ns=(
                None
                if self.index_ns is None
                else self.index_ns[selected]
            ),
        )


@dataclass(frozen=True)
class Exp007Simulation:
    session_dates: np.ndarray
    years: np.ndarray
    trade_mask: np.ndarray
    signal_five_minute_slot: np.ndarray
    entry_minute_slot: np.ndarray
    exit_minute_slot: np.ndarray
    opening_range_high: np.ndarray
    opening_range_low: np.ndarray
    entry_price: np.ndarray
    stop_price: np.ndarray
    target_price: np.ndarray
    exit_price: np.ndarray
    risk_points: np.ndarray
    gross_pnl_usd: np.ndarray
    transaction_cost_usd: np.ndarray
    net_pnl_usd: np.ndarray
    exit_reason: np.ndarray


@dataclass(frozen=True)
class Exp007Result:
    symbol: str
    summary: dict[str, Any]
    trades: pd.DataFrame
    equity_curve: pd.DataFrame
    yearly_results: pd.DataFrame


def prepare_exp007_arrays(
    data: pd.DataFrame,
    *,
    validate_data: bool = True,
) -> Exp007Arrays:
    if validate_data:
        validate_one_minute_data(data)

    local = data.sort_values(
        ["session_date", "minute_slot"],
        kind="stable",
    ).copy()

    counts = local.groupby("session_date", sort=True).size()
    if (
        counts.empty
        or not counts.eq(EXPECTED_MINUTES_PER_SESSION).all()
    ):
        raise ValueError(
            "Every EXP-007 session must contain exactly 390 minutes."
        )

    session_count = int(len(counts))
    shape = (session_count, EXPECTED_MINUTES_PER_SESSION)
    session_dates = (
        local["session_date"]
        .astype(str)
        .to_numpy()
        .reshape(shape)[:, 0]
    )
    years = pd.to_datetime(session_dates).year.to_numpy(dtype=int)

    index_ns = None
    if isinstance(local.index, pd.DatetimeIndex):
        index_ns = local.index.asi8.reshape(shape)

    return Exp007Arrays(
        session_dates=session_dates,
        years=years,
        open=local["open"].to_numpy(dtype=float).reshape(shape),
        high=local["high"].to_numpy(dtype=float).reshape(shape),
        low=local["low"].to_numpy(dtype=float).reshape(shape),
        close=local["close"].to_numpy(dtype=float).reshape(shape),
        volume=local["volume"].to_numpy(dtype=float).reshape(shape),
        index_ns=index_ns,
    )


def _first_true(values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    present = values.any(axis=1)
    position = values.argmax(axis=1)
    return present, position


def simulate_exp007_arrays(
    arrays: Exp007Arrays,
    *,
    symbol: str,
    slippage_ticks_per_side: float = 1.0,
) -> Exp007Simulation:
    contract = get_contract_spec(
        symbol,
        slippage_ticks_per_side=slippage_ticks_per_side,
    )

    session_count = arrays.session_count
    row = np.arange(session_count)

    opening_range_high = arrays.high[:, :OPENING_RANGE_MINUTES].max(axis=1)
    opening_range_low = arrays.low[:, :OPENING_RANGE_MINUTES].min(axis=1)

    five_minute_close = arrays.close[:, 4::5]
    if five_minute_close.shape[1] != EXPECTED_FIVE_MINUTE_BARS:
        raise RuntimeError("EXP-007 five-minute close reconstruction failed.")

    signal_window = five_minute_close[
        :,
        FIRST_SIGNAL_FIVE_MINUTE_SLOT : LAST_SIGNAL_FIVE_MINUTE_SLOT + 1,
    ]
    breakouts = signal_window > opening_range_high[:, None]
    has_signal, first_relative = _first_true(breakouts)
    signal_slot = FIRST_SIGNAL_FIVE_MINUTE_SLOT + first_relative
    entry_slot = (signal_slot + 1) * 5

    safe_entry_slot = np.where(has_signal, entry_slot, 0)
    entry_price = arrays.open[row, safe_entry_slot]
    stop_price = opening_range_low.copy()
    risk_points = entry_price - stop_price
    target_price = entry_price + risk_points

    trade_mask = (
        has_signal
        & (entry_slot < FORCED_FLAT_MINUTE_SLOT)
        & np.isfinite(entry_price)
        & np.isfinite(stop_price)
        & (risk_points > 0.0)
    )

    minutes = np.arange(EXPECTED_MINUTES_PER_SESSION)[None, :]
    active = (
        trade_mask[:, None]
        & (minutes >= safe_entry_slot[:, None])
        & (minutes < FORCED_FLAT_MINUTE_SLOT)
    )

    stop_gap = active & (arrays.open <= stop_price[:, None])
    stop_touch = active & (arrays.low <= stop_price[:, None])
    stop_event = stop_gap | stop_touch

    target_gap = active & (arrays.open >= target_price[:, None])
    target_touch = active & (arrays.high >= target_price[:, None])
    # Conservative ambiguity rule: when both boundaries occur inside the
    # same one-minute bar, the stop wins.
    target_event = (target_gap | target_touch) & ~stop_event

    any_event = stop_event | target_event
    has_event, first_event_slot = _first_true(any_event)

    exit_slot = np.where(
        trade_mask & has_event,
        first_event_slot,
        FORCED_FLAT_MINUTE_SLOT,
    ).astype(int)
    safe_exit_slot = np.where(
        trade_mask,
        exit_slot,
        FORCED_FLAT_MINUTE_SLOT,
    )

    event_is_stop = stop_event[row, safe_exit_slot]
    event_is_target = target_event[row, safe_exit_slot]
    gap_stop_at_exit = stop_gap[row, safe_exit_slot]

    forced_exit = arrays.open[:, FORCED_FLAT_MINUTE_SLOT]
    stop_fill = np.where(
        gap_stop_at_exit,
        arrays.open[row, safe_exit_slot],
        stop_price,
    )
    exit_price = np.where(
        trade_mask & event_is_stop,
        stop_fill,
        np.where(
            trade_mask & event_is_target,
            target_price,
            forced_exit,
        ),
    )

    gross_points = np.where(
        trade_mask,
        exit_price - entry_price,
        0.0,
    )
    gross_pnl = gross_points * contract.multiplier_usd_per_point
    transaction_cost = np.where(
        trade_mask,
        contract.round_trip_cost_usd,
        0.0,
    )
    net_pnl = np.where(
        trade_mask,
        gross_pnl - transaction_cost,
        0.0,
    )

    exit_reason = np.where(
        ~trade_mask,
        "no_trade",
        np.where(
            event_is_stop,
            np.where(
                gap_stop_at_exit,
                "gap_through_opening_range_stop",
                "opening_range_stop",
            ),
            np.where(
                event_is_target,
                "one_r_target",
                "forced_flat_1400",
            ),
        ),
    ).astype(object)

    return Exp007Simulation(
        session_dates=arrays.session_dates.copy(),
        years=arrays.years.copy(),
        trade_mask=trade_mask,
        signal_five_minute_slot=signal_slot.astype(int),
        entry_minute_slot=entry_slot.astype(int),
        exit_minute_slot=exit_slot,
        opening_range_high=opening_range_high,
        opening_range_low=opening_range_low,
        entry_price=entry_price,
        stop_price=stop_price,
        target_price=target_price,
        exit_price=exit_price,
        risk_points=risk_points,
        gross_pnl_usd=gross_pnl,
        transaction_cost_usd=transaction_cost,
        net_pnl_usd=net_pnl,
        exit_reason=exit_reason,
    )


def profit_factor(values: np.ndarray) -> float:
    pnl = np.asarray(values, dtype=float)
    gains = float(pnl[pnl > 0.0].sum())
    losses = abs(float(pnl[pnl < 0.0].sum()))
    if losses > 0.0:
        return gains / losses
    if gains > 0.0:
        return float("inf")
    return float("nan")


def summarize_exp007_simulation(
    simulation: Exp007Simulation,
    *,
    symbol: str,
    slippage_ticks_per_side: float,
) -> dict[str, Any]:
    symbol_key = symbol.upper()
    contract = get_contract_spec(
        symbol_key,
        slippage_ticks_per_side=slippage_ticks_per_side,
    )
    completed = int(simulation.trade_mask.sum())
    trade_pnl = simulation.net_pnl_usd[simulation.trade_mask]
    cumulative = np.cumsum(simulation.net_pnl_usd)
    peak = np.maximum.accumulate(np.maximum(cumulative, 0.0))
    drawdown = cumulative - peak
    max_drawdown = float(drawdown.min()) if drawdown.size else 0.0
    net_profit = float(trade_pnl.sum())
    reference_capital = REFERENCE_CAPITAL_USD[symbol_key]

    yearly_net: dict[int, float] = {}
    profitable_years = 0
    for year in sorted(set(simulation.years)):
        value = float(
            simulation.net_pnl_usd[simulation.years == year].sum()
        )
        yearly_net[int(year)] = value
        profitable_years += int(value > 0.0)

    return {
        "strategy_key": "or30_long_1r_flat1400",
        "symbol": symbol_key,
        "included_sessions": int(len(simulation.session_dates)),
        "completed_trades": completed,
        "long_trades": completed,
        "short_trades": 0,
        "net_profit_usd": net_profit,
        "trade_profit_factor": float(profit_factor(trade_pnl)),
        "win_rate_percent": (
            float((trade_pnl > 0.0).mean() * 100.0)
            if completed
            else 0.0
        ),
        "average_trade_usd": (
            float(trade_pnl.mean()) if completed else float("nan")
        ),
        "median_trade_usd": (
            float(np.median(trade_pnl)) if completed else float("nan")
        ),
        "gross_profit_usd": float(trade_pnl[trade_pnl > 0.0].sum()),
        "gross_loss_usd": abs(float(trade_pnl[trade_pnl < 0.0].sum())),
        "maximum_drawdown_usd": max_drawdown,
        "maximum_drawdown_percent": (
            max_drawdown / reference_capital * 100.0
        ),
        "return_percent": net_profit / reference_capital * 100.0,
        "net_profit_to_drawdown": (
            net_profit / abs(max_drawdown)
            if max_drawdown < 0.0
            else float("inf")
        ),
        "average_trade_to_cost": (
            float(trade_pnl.mean()) / contract.round_trip_cost_usd
            if completed
            else float("nan")
        ),
        "profitable_calendar_years": int(profitable_years),
        "yearly_net_profit_usd": yearly_net,
        "slippage_ticks_per_side": float(slippage_ticks_per_side),
        "round_trip_cost_usd": float(contract.round_trip_cost_usd),
        "reference_capital_usd": float(reference_capital),
    }


def _timestamp_iso(
    index_ns: np.ndarray | None,
    row: int,
    slot: int,
    *,
    offset_minutes: int = 0,
) -> str:
    if index_ns is None:
        return ""
    timestamp = pd.Timestamp(int(index_ns[row, slot]), tz="UTC")
    if offset_minutes:
        timestamp = timestamp + pd.Timedelta(minutes=int(offset_minutes))
    return timestamp.isoformat()


def _build_trade_ledger(
    arrays: Exp007Arrays,
    simulation: Exp007Simulation,
    *,
    symbol: str,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    cumulative = 0.0
    for session_index in np.flatnonzero(simulation.trade_mask):
        signal_slot = int(
            simulation.signal_five_minute_slot[session_index]
        )
        entry_slot = int(simulation.entry_minute_slot[session_index])
        exit_slot = int(simulation.exit_minute_slot[session_index])
        net_pnl = float(simulation.net_pnl_usd[session_index])
        cumulative += net_pnl
        risk = float(simulation.risk_points[session_index])
        gross_points = float(
            simulation.exit_price[session_index]
            - simulation.entry_price[session_index]
        )
        rows.append(
            {
                "symbol": symbol.upper(),
                "session_date": str(simulation.session_dates[session_index]),
                "direction": "long",
                "signal_bar_start_time": _timestamp_iso(
                    arrays.index_ns,
                    session_index,
                    signal_slot * 5,
                ),
                "signal_close_time": _timestamp_iso(
                    arrays.index_ns,
                    session_index,
                    signal_slot * 5 + 4,
                    offset_minutes=1,
                ),
                "entry_time": _timestamp_iso(
                    arrays.index_ns,
                    session_index,
                    entry_slot,
                ),
                "exit_time": _timestamp_iso(
                    arrays.index_ns,
                    session_index,
                    exit_slot,
                ),
                "opening_range_high": float(
                    simulation.opening_range_high[session_index]
                ),
                "opening_range_low": float(
                    simulation.opening_range_low[session_index]
                ),
                "entry_price": float(simulation.entry_price[session_index]),
                "stop_price": float(simulation.stop_price[session_index]),
                "target_price": float(simulation.target_price[session_index]),
                "exit_price": float(simulation.exit_price[session_index]),
                "risk_points": risk,
                "gross_r_multiple": (
                    gross_points / risk if risk > 0.0 else float("nan")
                ),
                "gross_pnl_usd": float(
                    simulation.gross_pnl_usd[session_index]
                ),
                "transaction_cost_usd": float(
                    simulation.transaction_cost_usd[session_index]
                ),
                "net_pnl_usd": net_pnl,
                "cumulative_net_pnl_usd": cumulative,
                "minutes_held": int(max(1, exit_slot - entry_slot + 1)),
                "exit_reason": str(simulation.exit_reason[session_index]),
                "strategy_key": "or30_long_1r_flat1400",
            }
        )
    return pd.DataFrame(rows)


def _build_equity_curve(simulation: Exp007Simulation) -> pd.DataFrame:
    cumulative = np.cumsum(simulation.net_pnl_usd)
    peak = np.maximum.accumulate(np.maximum(cumulative, 0.0))
    return pd.DataFrame(
        {
            "session_date": simulation.session_dates,
            "session_net_pnl_usd": simulation.net_pnl_usd,
            "cumulative_net_pnl_usd": cumulative,
            "drawdown_usd": cumulative - peak,
            "had_trade": simulation.trade_mask,
        }
    )


def _build_yearly_results(simulation: Exp007Simulation) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for year in sorted(set(simulation.years)):
        mask = simulation.years == year
        trades = mask & simulation.trade_mask
        pnl = simulation.net_pnl_usd[trades]
        rows.append(
            {
                "year": int(year),
                "included_sessions": int(mask.sum()),
                "completed_trades": int(trades.sum()),
                "long_trades": int(trades.sum()),
                "short_trades": 0,
                "net_profit_usd": float(pnl.sum()),
                "trade_profit_factor": float(profit_factor(pnl)),
                "win_rate_percent": (
                    float((pnl > 0.0).mean() * 100.0)
                    if pnl.size
                    else 0.0
                ),
                "average_trade_usd": (
                    float(pnl.mean()) if pnl.size else float("nan")
                ),
            }
        )
    return pd.DataFrame(rows)


def run_exp007_orb(
    data: pd.DataFrame,
    *,
    symbol: str,
    slippage_ticks_per_side: float = 1.0,
    validate_data: bool = True,
) -> Exp007Result:
    arrays = prepare_exp007_arrays(data, validate_data=validate_data)
    simulation = simulate_exp007_arrays(
        arrays,
        symbol=symbol,
        slippage_ticks_per_side=slippage_ticks_per_side,
    )
    summary = summarize_exp007_simulation(
        simulation,
        symbol=symbol,
        slippage_ticks_per_side=slippage_ticks_per_side,
    )
    return Exp007Result(
        symbol=symbol.upper(),
        summary=summary,
        trades=_build_trade_ledger(arrays, simulation, symbol=symbol),
        equity_curve=_build_equity_curve(simulation),
        yearly_results=_build_yearly_results(simulation),
    )
