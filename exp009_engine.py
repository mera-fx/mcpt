from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import numpy as np
import pandas as pd

from exp005_futures_orb import get_contract_spec
from exp005_session_mcpt import validate_one_minute_data
from exp009_preregistration import EXP009_CANDIDATES


MINUTES_PER_SESSION = 390
FIVE_MINUTE_BARS = 78
FORCED_FLAT_MINUTE = 385
REFERENCE_CAPITAL_USD = {"NQ": 100_000.0, "MNQ": 10_000.0}


@dataclass(frozen=True)
class Exp009Candidate:
    candidate_id: str
    family_id: str
    parameters: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "family_id": self.family_id,
            **self.parameters,
        }


def locked_exp009_candidates() -> tuple[Exp009Candidate, ...]:
    return tuple(
        Exp009Candidate(
            candidate_id=str(record["candidate_id"]),
            family_id=str(record["family_id"]),
            parameters={
                key: value
                for key, value in record.items()
                if key not in {"candidate_id", "family_id"}
            },
        )
        for record in EXP009_CANDIDATES
    )


def get_exp009_candidate(candidate_id: str) -> Exp009Candidate:
    matches = [
        candidate
        for candidate in locked_exp009_candidates()
        if candidate.candidate_id == candidate_id
    ]
    if len(matches) != 1:
        raise KeyError(f"Unknown EXP-009 candidate: {candidate_id}")
    return matches[0]


@dataclass(frozen=True)
class Exp009Arrays:
    session_dates: np.ndarray
    years: np.ndarray
    open: np.ndarray
    high: np.ndarray
    low: np.ndarray
    close: np.ndarray
    volume: np.ndarray
    open_5m: np.ndarray
    high_5m: np.ndarray
    low_5m: np.ndarray
    close_5m: np.ndarray
    volume_5m: np.ndarray
    vwap_5m: np.ndarray
    vwap_std_5m: np.ndarray

    @property
    def session_count(self) -> int:
        return int(self.open.shape[0])


@dataclass(frozen=True)
class Exp009Signals:
    candidate: Exp009Candidate
    direction: np.ndarray
    signal_five_minute_slot: np.ndarray
    entry_minute_slot: np.ndarray
    stop_price: np.ndarray
    target_price: np.ndarray
    setup_reference: np.ndarray


@dataclass(frozen=True)
class Exp009Simulation:
    candidate: Exp009Candidate
    symbol: str
    session_dates: np.ndarray
    years: np.ndarray
    direction: np.ndarray
    trade_mask: np.ndarray
    signal_five_minute_slot: np.ndarray
    entry_minute_slot: np.ndarray
    exit_minute_slot: np.ndarray
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
class Exp009Result:
    candidate: Exp009Candidate
    symbol: str
    summary: dict[str, Any]
    trades: pd.DataFrame
    equity_curve: pd.DataFrame
    yearly_results: pd.DataFrame


def prepare_exp009_arrays(
    data: pd.DataFrame,
    *,
    validate_data: bool = True,
) -> Exp009Arrays:
    if validate_data:
        validate_one_minute_data(data)

    slot_column = (
        "minute_slot"
        if "minute_slot" in data.columns
        else "slot"
    )
    required = {
        "session_date",
        slot_column,
        "open",
        "high",
        "low",
        "close",
        "volume",
    }
    missing = sorted(required.difference(data.columns))
    if missing:
        raise ValueError(
            "EXP-009 data are missing columns: " + ", ".join(missing)
        )

    local = data.sort_values(
        ["session_date", slot_column], kind="stable"
    ).copy()
    counts = local.groupby("session_date", sort=True).size()
    if counts.empty or not counts.eq(MINUTES_PER_SESSION).all():
        raise ValueError(
            "Every EXP-009 session must contain exactly 390 one-minute bars."
        )

    session_count = int(len(counts))
    minute_shape = (session_count, MINUTES_PER_SESSION)
    five_shape = (session_count, FIVE_MINUTE_BARS, 5)

    session_dates = (
        local["session_date"]
        .astype(str)
        .to_numpy()
        .reshape(minute_shape)[:, 0]
    )
    years = pd.to_datetime(session_dates).year.to_numpy(dtype=int)

    open_1m = local["open"].to_numpy(dtype=float).reshape(minute_shape)
    high_1m = local["high"].to_numpy(dtype=float).reshape(minute_shape)
    low_1m = local["low"].to_numpy(dtype=float).reshape(minute_shape)
    close_1m = local["close"].to_numpy(dtype=float).reshape(minute_shape)
    volume_1m = local["volume"].to_numpy(dtype=float).reshape(minute_shape)

    open_5m = open_1m.reshape(five_shape)[:, :, 0]
    high_5m = high_1m.reshape(five_shape).max(axis=2)
    low_5m = low_1m.reshape(five_shape).min(axis=2)
    close_5m = close_1m.reshape(five_shape)[:, :, -1]
    volume_5m = volume_1m.reshape(five_shape).sum(axis=2)

    typical = (high_1m + low_1m + close_1m) / 3.0
    cumulative_volume = np.cumsum(volume_1m, axis=1)
    safe_volume = np.where(cumulative_volume > 0, cumulative_volume, np.nan)
    cumulative_pv = np.cumsum(typical * volume_1m, axis=1)
    cumulative_p2v = np.cumsum(typical * typical * volume_1m, axis=1)
    vwap_1m = cumulative_pv / safe_volume
    variance_1m = np.maximum(
        cumulative_p2v / safe_volume - vwap_1m * vwap_1m,
        0.0,
    )
    vwap_5m = vwap_1m[:, 4::5]
    vwap_std_5m = np.sqrt(variance_1m[:, 4::5])

    return Exp009Arrays(
        session_dates=session_dates,
        years=years,
        open=open_1m,
        high=high_1m,
        low=low_1m,
        close=close_1m,
        volume=volume_1m,
        open_5m=open_5m,
        high_5m=high_5m,
        low_5m=low_5m,
        close_5m=close_5m,
        volume_5m=volume_5m,
        vwap_5m=vwap_5m,
        vwap_std_5m=vwap_std_5m,
    )


def _blank_signals(
    arrays: Exp009Arrays,
    candidate: Exp009Candidate,
) -> Exp009Signals:
    n = arrays.session_count
    return Exp009Signals(
        candidate=candidate,
        direction=np.zeros(n, dtype=np.int8),
        signal_five_minute_slot=np.full(n, -1, dtype=np.int16),
        entry_minute_slot=np.full(n, -1, dtype=np.int16),
        stop_price=np.full(n, np.nan, dtype=float),
        target_price=np.full(n, np.nan, dtype=float),
        setup_reference=np.full(n, np.nan, dtype=float),
    )


def _assign_signal(
    signals: Exp009Signals,
    session: int,
    *,
    direction: int,
    signal_bar: int,
    entry_bar: int,
    stop: float,
    target: float,
    reference: float,
    arrays: Exp009Arrays,
) -> bool:
    entry_minute = int(entry_bar * 5)
    if (
        direction not in {-1, 1}
        or entry_bar >= FIVE_MINUTE_BARS
        or entry_minute >= FORCED_FLAT_MINUTE
        or not np.isfinite(stop)
    ):
        return False

    entry = float(arrays.open_5m[session, entry_bar])
    risk = direction * (entry - stop)
    if not np.isfinite(entry) or risk <= 0:
        return False
    if np.isfinite(target) and direction * (target - entry) <= 0:
        return False

    signals.direction[session] = direction
    signals.signal_five_minute_slot[session] = signal_bar
    signals.entry_minute_slot[session] = entry_minute
    signals.stop_price[session] = stop
    signals.target_price[session] = target
    signals.setup_reference[session] = reference
    return True


def _opening_range(arrays: Exp009Arrays, session: int) -> tuple[float, float]:
    return (
        float(np.max(arrays.high[session, :30])),
        float(np.min(arrays.low[session, :30])),
    )


def _orb_pullback_signals(
    arrays: Exp009Arrays,
    candidate: Exp009Candidate,
) -> Exp009Signals:
    signals = _blank_signals(arrays, candidate)
    both = candidate.parameters["direction_mode"] == "both"
    rr = float(candidate.parameters["reward_to_risk"])

    for s in range(arrays.session_count):
        high, low = _opening_range(arrays, s)
        midpoint = (high + low) / 2.0
        breakout_bar = -1
        direction = 0
        for bar in range(6, FIVE_MINUTE_BARS - 1):
            close = arrays.close_5m[s, bar]
            if close > high:
                breakout_bar, direction = bar, 1
                break
            if both and close < low:
                breakout_bar, direction = bar, -1
                break
        if breakout_bar < 0:
            continue

        final_retest = min(breakout_bar + 6, FIVE_MINUTE_BARS - 2)
        for bar in range(breakout_bar + 1, final_retest + 1):
            qualifies = (
                arrays.low_5m[s, bar] <= high
                and arrays.close_5m[s, bar] > high
                if direction == 1
                else arrays.high_5m[s, bar] >= low
                and arrays.close_5m[s, bar] < low
            )
            if not qualifies:
                continue
            entry = float(arrays.open_5m[s, bar + 1])
            risk = direction * (entry - midpoint)
            target = entry + direction * rr * risk
            _assign_signal(
                signals,
                s,
                direction=direction,
                signal_bar=bar,
                entry_bar=bar + 1,
                stop=midpoint,
                target=target,
                reference=high if direction == 1 else low,
                arrays=arrays,
            )
            break
    return signals


def _failed_orb_signals(
    arrays: Exp009Arrays,
    candidate: Exp009Candidate,
) -> Exp009Signals:
    signals = _blank_signals(arrays, candidate)
    window_bars = int(candidate.parameters["failure_window_minutes"]) // 5
    rr = float(candidate.parameters["reward_to_risk"])

    for s in range(arrays.session_count):
        high, low = _opening_range(arrays, s)
        breakout_bar = -1
        breakout_direction = 0
        for bar in range(6, FIVE_MINUTE_BARS - 1):
            close = arrays.close_5m[s, bar]
            if close > high:
                breakout_bar, breakout_direction = bar, 1
                break
            if close < low:
                breakout_bar, breakout_direction = bar, -1
                break
        if breakout_bar < 0:
            continue

        final_bar = min(
            breakout_bar + window_bars, FIVE_MINUTE_BARS - 2
        )
        for bar in range(breakout_bar + 1, final_bar + 1):
            close = arrays.close_5m[s, bar]
            failed = low < close < high
            if not failed:
                continue
            direction = -breakout_direction
            stop = (
                float(
                    np.max(
                        arrays.high_5m[s, breakout_bar : bar + 1]
                    )
                )
                if direction == -1
                else float(
                    np.min(arrays.low_5m[s, breakout_bar : bar + 1])
                )
            )
            entry = float(arrays.open_5m[s, bar + 1])
            risk = direction * (entry - stop)
            target = entry + direction * rr * risk
            _assign_signal(
                signals,
                s,
                direction=direction,
                signal_bar=bar,
                entry_bar=bar + 1,
                stop=stop,
                target=target,
                reference=high if breakout_direction == 1 else low,
                arrays=arrays,
            )
            break
    return signals


def _vwap_reversion_signals(
    arrays: Exp009Arrays,
    candidate: Exp009Candidate,
) -> Exp009Signals:
    signals = _blank_signals(arrays, candidate)
    band_multiple = float(
        candidate.parameters["band_standard_deviations"]
    )
    exit_mode = str(candidate.parameters["exit_mode"])

    for s in range(arrays.session_count):
        setup_side = 0
        setup_bar = -1
        for bar in range(11, FIVE_MINUTE_BARS - 1):
            vwap = float(arrays.vwap_5m[s, bar])
            std = float(arrays.vwap_std_5m[s, bar])
            if not np.isfinite(vwap) or not np.isfinite(std):
                continue
            upper = vwap + band_multiple * std
            lower = vwap - band_multiple * std
            close = float(arrays.close_5m[s, bar])

            if setup_side == 0:
                if close > upper:
                    setup_side, setup_bar = 1, bar
                elif close < lower:
                    setup_side, setup_bar = -1, bar
                continue

            reentered = (
                close <= upper if setup_side == 1 else close >= lower
            )
            if not reentered:
                continue
            direction = -setup_side
            stop = (
                float(np.max(arrays.high_5m[s, setup_bar : bar + 1]))
                if direction == -1
                else float(np.min(arrays.low_5m[s, setup_bar : bar + 1]))
            )
            entry = float(arrays.open_5m[s, bar + 1])
            risk = direction * (entry - stop)
            target = (
                vwap
                if exit_mode == "vwap"
                else entry + direction * risk
            )
            _assign_signal(
                signals,
                s,
                direction=direction,
                signal_bar=bar,
                entry_bar=bar + 1,
                stop=stop,
                target=target,
                reference=vwap,
                arrays=arrays,
            )
            break
    return signals


def _vwap_trend_signals(
    arrays: Exp009Arrays,
    candidate: Exp009Candidate,
) -> Exp009Signals:
    signals = _blank_signals(arrays, candidate)
    confirmations = int(candidate.parameters["confirmation_closes"])
    rr = float(candidate.parameters["reward_to_risk"])

    for s in range(arrays.session_count):
        # Bar 5 is the 09:55-10:00 completed signal bar. Its next-bar
        # opening price is the locked 10:00 entry, so 10:00 is eligible.
        for bar in range(5, FIVE_MINUTE_BARS - confirmations):
            vwap = float(arrays.vwap_5m[s, bar])
            prior_vwap = float(arrays.vwap_5m[s, bar - 3])
            close = float(arrays.close_5m[s, bar])
            direction = 0
            if (
                close > vwap
                and vwap > prior_vwap
                and arrays.low_5m[s, bar] <= vwap
            ):
                direction = 1
            elif (
                close < vwap
                and vwap < prior_vwap
                and arrays.high_5m[s, bar] >= vwap
            ):
                direction = -1
            if direction == 0:
                continue

            confirmation_slice = slice(bar, bar + confirmations)
            confirmation_closes = arrays.close_5m[
                s, confirmation_slice
            ]
            confirmation_vwap = arrays.vwap_5m[s, confirmation_slice]
            confirmed = bool(
                np.all(confirmation_closes > confirmation_vwap)
                if direction == 1
                else np.all(confirmation_closes < confirmation_vwap)
            )
            if not confirmed:
                continue
            signal_bar = bar + confirmations - 1
            stop = (
                float(np.min(arrays.low_5m[s, confirmation_slice]))
                if direction == 1
                else float(np.max(arrays.high_5m[s, confirmation_slice]))
            )
            entry = float(arrays.open_5m[s, signal_bar + 1])
            risk = direction * (entry - stop)
            target = entry + direction * rr * risk
            _assign_signal(
                signals,
                s,
                direction=direction,
                signal_bar=signal_bar,
                entry_bar=signal_bar + 1,
                stop=stop,
                target=target,
                reference=vwap,
                arrays=arrays,
            )
            break
    return signals


def _compression_signals(
    arrays: Exp009Arrays,
    candidate: Exp009Candidate,
) -> Exp009Signals:
    signals = _blank_signals(arrays, candidate)
    fraction = float(
        candidate.parameters["compression_fraction_of_opening_range"]
    )
    rr = float(candidate.parameters["reward_to_risk"])

    for s in range(arrays.session_count):
        opening_high, opening_low = _opening_range(arrays, s)
        opening_width = opening_high - opening_low
        if opening_width <= 0:
            continue

        compression_bar = -1
        compression_high = np.nan
        compression_low = np.nan
        for bar in range(11, FIVE_MINUTE_BARS - 1):
            start = bar - 5
            window_high = float(
                np.max(arrays.high_5m[s, start : bar + 1])
            )
            window_low = float(
                np.min(arrays.low_5m[s, start : bar + 1])
            )
            if window_high - window_low <= fraction * opening_width:
                compression_bar = bar
                compression_high = window_high
                compression_low = window_low
                break
        if compression_bar < 0:
            continue

        final_bar = min(compression_bar + 12, FIVE_MINUTE_BARS - 2)
        for bar in range(compression_bar + 1, final_bar + 1):
            close = float(arrays.close_5m[s, bar])
            direction = (
                1
                if close > compression_high
                else -1
                if close < compression_low
                else 0
            )
            if direction == 0:
                continue
            stop = (
                compression_low if direction == 1 else compression_high
            )
            entry = float(arrays.open_5m[s, bar + 1])
            risk = direction * (entry - stop)
            target = entry + direction * rr * risk
            _assign_signal(
                signals,
                s,
                direction=direction,
                signal_bar=bar,
                entry_bar=bar + 1,
                stop=stop,
                target=target,
                reference=(compression_high + compression_low) / 2.0,
                arrays=arrays,
            )
            break
    return signals


def _opening_drive_signals(
    arrays: Exp009Arrays,
    candidate: Exp009Candidate,
) -> Exp009Signals:
    signals = _blank_signals(arrays, candidate)
    minimum = float(candidate.parameters["minimum_drive_fraction"])
    exit_mode = str(candidate.parameters["exit_mode"])

    for s in range(arrays.session_count):
        high, low = _opening_range(arrays, s)
        width = high - low
        if width <= 0:
            continue
        opening = float(arrays.open[s, 0])
        close = float(arrays.close[s, 29])
        move = close - opening
        if move == 0 or abs(move) / width < minimum:
            continue
        direction = 1 if move > 0 else -1
        stop = low if direction == 1 else high
        entry = float(arrays.open_5m[s, 6])
        risk = direction * (entry - stop)
        target = (
            np.nan
            if exit_mode == "time"
            else entry + direction * 1.5 * risk
        )
        _assign_signal(
            signals,
            s,
            direction=direction,
            signal_bar=5,
            entry_bar=6,
            stop=stop,
            target=target,
            reference=abs(move) / width,
            arrays=arrays,
        )
    return signals


SIGNAL_BUILDERS: dict[
    str, Callable[[Exp009Arrays, Exp009Candidate], Exp009Signals]
] = {
    "orb_pullback_continuation": _orb_pullback_signals,
    "failed_orb_reversal": _failed_orb_signals,
    "vwap_mean_reversion": _vwap_reversion_signals,
    "vwap_trend_pullback": _vwap_trend_signals,
    "intraday_compression_breakout": _compression_signals,
    "opening_drive_continuation": _opening_drive_signals,
}


def generate_exp009_signals(
    arrays: Exp009Arrays,
    candidate: Exp009Candidate,
) -> Exp009Signals:
    if candidate.family_id not in SIGNAL_BUILDERS:
        raise ValueError(f"Unsupported EXP-009 family: {candidate.family_id}")
    return SIGNAL_BUILDERS[candidate.family_id](arrays, candidate)


def execute_exp009_signals(
    arrays: Exp009Arrays,
    signals: Exp009Signals,
    *,
    symbol: str,
    slippage_ticks_per_side: float = 1.0,
) -> Exp009Simulation:
    contract = get_contract_spec(
        symbol, slippage_ticks_per_side=slippage_ticks_per_side
    )
    n = arrays.session_count
    trade_mask = np.zeros(n, dtype=bool)
    exit_slot = np.full(n, -1, dtype=np.int16)
    entry_price = np.full(n, np.nan)
    exit_price = np.full(n, np.nan)
    risk_points = np.full(n, np.nan)
    gross = np.zeros(n)
    costs = np.zeros(n)
    net = np.zeros(n)
    reasons = np.full(n, "no_trade", dtype=object)

    for s in range(n):
        direction = int(signals.direction[s])
        entry_minute = int(signals.entry_minute_slot[s])
        if direction == 0 or entry_minute < 0:
            continue
        entry = float(arrays.open[s, entry_minute])
        stop = float(signals.stop_price[s])
        target = float(signals.target_price[s])
        risk = direction * (entry - stop)
        if not np.isfinite(entry) or not np.isfinite(stop) or risk <= 0:
            continue

        trade_mask[s] = True
        entry_price[s] = entry
        risk_points[s] = risk
        chosen_exit = float(arrays.open[s, FORCED_FLAT_MINUTE])
        chosen_slot = FORCED_FLAT_MINUTE
        chosen_reason = "forced_flat_1555"

        for minute in range(entry_minute, FORCED_FLAT_MINUTE):
            bar_open = float(arrays.open[s, minute])
            bar_high = float(arrays.high[s, minute])
            bar_low = float(arrays.low[s, minute])

            if direction == 1:
                stop_gap = bar_open <= stop
                stop_touch = bar_low <= stop
                target_touch = np.isfinite(target) and bar_high >= target
            else:
                stop_gap = bar_open >= stop
                stop_touch = bar_high >= stop
                target_touch = np.isfinite(target) and bar_low <= target

            if stop_gap:
                chosen_exit = bar_open
                chosen_slot = minute
                chosen_reason = "gap_through_stop"
                break
            if stop_touch:
                chosen_exit = stop
                chosen_slot = minute
                chosen_reason = "protective_stop"
                break
            if target_touch:
                chosen_exit = target
                chosen_slot = minute
                chosen_reason = "profit_target"
                break

        pnl_points = direction * (chosen_exit - entry)
        gross[s] = pnl_points * contract.multiplier_usd_per_point
        costs[s] = contract.round_trip_cost_usd
        net[s] = gross[s] - costs[s]
        exit_price[s] = chosen_exit
        exit_slot[s] = chosen_slot
        reasons[s] = chosen_reason

    return Exp009Simulation(
        candidate=signals.candidate,
        symbol=contract.symbol,
        session_dates=arrays.session_dates.copy(),
        years=arrays.years.copy(),
        direction=signals.direction.copy(),
        trade_mask=trade_mask,
        signal_five_minute_slot=signals.signal_five_minute_slot.copy(),
        entry_minute_slot=signals.entry_minute_slot.copy(),
        exit_minute_slot=exit_slot,
        entry_price=entry_price,
        stop_price=signals.stop_price.copy(),
        target_price=signals.target_price.copy(),
        exit_price=exit_price,
        risk_points=risk_points,
        gross_pnl_usd=gross,
        transaction_cost_usd=costs,
        net_pnl_usd=net,
        exit_reason=reasons,
    )


def profit_factor(values: np.ndarray) -> float:
    local = np.asarray(values, dtype=float)
    gains = float(local[local > 0].sum())
    losses = float(-local[local < 0].sum())
    if losses == 0:
        return float("inf") if gains > 0 else 0.0
    return gains / losses


def maximum_drawdown(values: np.ndarray) -> float:
    equity = np.cumsum(np.asarray(values, dtype=float))
    if equity.size == 0:
        return 0.0
    peaks = np.maximum.accumulate(np.r_[0.0, equity])
    drawdowns = np.r_[0.0, equity] - peaks
    return float(drawdowns.min())


def build_exp009_result(
    simulation: Exp009Simulation,
) -> Exp009Result:
    mask = simulation.trade_mask
    pnl = simulation.net_pnl_usd[mask]
    gross_pnl = simulation.gross_pnl_usd[mask]
    dates = simulation.session_dates[mask]
    years = simulation.years[mask]
    direction = simulation.direction[mask]

    trades = pd.DataFrame(
        {
            "candidate_id": simulation.candidate.candidate_id,
            "family_id": simulation.candidate.family_id,
            "symbol": simulation.symbol,
            "session_date": dates,
            "year": years,
            "direction": np.where(direction == 1, "long", "short"),
            "signal_five_minute_slot": simulation.signal_five_minute_slot[
                mask
            ],
            "entry_minute_slot": simulation.entry_minute_slot[mask],
            "exit_minute_slot": simulation.exit_minute_slot[mask],
            "holding_minutes": (
                simulation.exit_minute_slot[mask]
                - simulation.entry_minute_slot[mask]
            ),
            "entry_price": simulation.entry_price[mask],
            "stop_price": simulation.stop_price[mask],
            "target_price": simulation.target_price[mask],
            "exit_price": simulation.exit_price[mask],
            "risk_points": simulation.risk_points[mask],
            "gross_pnl_usd": gross_pnl,
            "transaction_cost_usd": simulation.transaction_cost_usd[mask],
            "net_pnl_usd": pnl,
            "exit_reason": simulation.exit_reason[mask],
        }
    )
    equity = np.cumsum(pnl)
    peaks = np.maximum.accumulate(np.r_[0.0, equity])[1:]
    reference = REFERENCE_CAPITAL_USD[simulation.symbol]
    equity_curve = pd.DataFrame(
        {
            "session_date": dates,
            "net_pnl_usd": pnl,
            "cumulative_net_profit_usd": equity,
            "equity_usd": reference + equity,
            "drawdown_usd": equity - peaks,
        }
    )

    yearly = (
        trades.groupby("year", as_index=False)
        .agg(
            completed_trades=("net_pnl_usd", "size"),
            net_profit_usd=("net_pnl_usd", "sum"),
        )
        if not trades.empty
        else pd.DataFrame(
            columns=["year", "completed_trades", "net_profit_usd"]
        )
    )
    if not yearly.empty:
        yearly["profit_factor"] = yearly["year"].map(
            {
                int(year): profit_factor(
                    trades.loc[trades["year"] == year, "net_pnl_usd"]
                    .to_numpy(dtype=float)
                )
                for year in yearly["year"]
            }
        )

    wins = pnl[pnl > 0]
    losses = pnl[pnl < 0]
    max_dd = maximum_drawdown(pnl)
    summary = {
        "candidate_id": simulation.candidate.candidate_id,
        "family_id": simulation.candidate.family_id,
        "symbol": simulation.symbol,
        "completed_trades": int(pnl.size),
        "long_trades": int((direction == 1).sum()),
        "short_trades": int((direction == -1).sum()),
        "gross_profit_usd": float(wins.sum()),
        "gross_loss_usd": float(losses.sum()),
        "net_profit_usd": float(pnl.sum()),
        "trade_profit_factor": float(profit_factor(pnl)),
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
        "maximum_drawdown_usd": float(max_dd),
        "maximum_drawdown_percent": float(abs(max_dd) / reference),
        "net_profit_to_drawdown": (
            float(pnl.sum() / abs(max_dd)) if max_dd < 0 else 0.0
        ),
        "round_trip_cost_usd": (
            float(simulation.transaction_cost_usd[mask][0])
            if pnl.size
            else float(
                get_contract_spec(simulation.symbol).round_trip_cost_usd
            )
        ),
        "average_trade_to_round_trip_cost": (
            float(
                pnl.mean()
                / simulation.transaction_cost_usd[mask][0]
            )
            if pnl.size
            else 0.0
        ),
    }
    return Exp009Result(
        candidate=simulation.candidate,
        symbol=simulation.symbol,
        summary=summary,
        trades=trades,
        equity_curve=equity_curve,
        yearly_results=yearly,
    )


def run_exp009_candidate(
    arrays: Exp009Arrays,
    candidate: Exp009Candidate,
    *,
    symbol: str,
    slippage_ticks_per_side: float = 1.0,
) -> Exp009Result:
    signals = generate_exp009_signals(arrays, candidate)
    simulation = execute_exp009_signals(
        arrays,
        signals,
        symbol=symbol,
        slippage_ticks_per_side=slippage_ticks_per_side,
    )
    return build_exp009_result(simulation)
