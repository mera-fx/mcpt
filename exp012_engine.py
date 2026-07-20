from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Callable, Iterable

import numpy as np
import pandas as pd

from exp009_engine import (
    Exp009Arrays,
    Exp009Candidate,
    Exp009Result,
    Exp009Signals,
    build_exp009_result,
    execute_exp009_signals,
    prepare_exp009_arrays,
)
from exp012_preregistration import EXP012_CANDIDATES
from extended_session_data import SESSION_QUALITY_FILE


CONTEXT_END_MINUTE = 1320
CASH_START_MINUTE = 930
PREMARKET_START_MINUTE = 840
CASH_MINUTES = 390
FIRST_CASH_SIGNAL_BAR = 0
FIRST_CASH_ENTRY_BAR = 1


@dataclass(frozen=True)
class Exp012Arrays:
    cash: Exp009Arrays
    overnight_open: np.ndarray
    overnight_high: np.ndarray
    overnight_low: np.ndarray
    overnight_close: np.ndarray
    overnight_drive_fraction: np.ndarray
    overnight_direction: np.ndarray
    premarket_open: np.ndarray
    premarket_high: np.ndarray
    premarket_low: np.ndarray
    premarket_close: np.ndarray
    premarket_drive_fraction: np.ndarray
    premarket_direction: np.ndarray
    previous_cash_available: np.ndarray
    previous_cash_close: np.ndarray
    previous_cash_range: np.ndarray
    gap_fraction: np.ndarray
    gap_direction: np.ndarray

    @property
    def session_dates(self) -> np.ndarray:
        return self.cash.session_dates

    @property
    def years(self) -> np.ndarray:
        return self.cash.years

    @property
    def session_count(self) -> int:
        return self.cash.session_count


def locked_exp012_candidates() -> tuple[Exp009Candidate, ...]:
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
        for record in EXP012_CANDIDATES
    )


def get_exp012_candidate(candidate_id: str) -> Exp009Candidate:
    matches = [
        candidate
        for candidate in locked_exp012_candidates()
        if candidate.candidate_id == candidate_id
    ]
    if len(matches) != 1:
        raise KeyError(f"Unknown EXP-012 candidate: {candidate_id}")
    return matches[0]


def _default_calendar_dates() -> list[str]:
    frame = pd.read_csv(
        Path(SESSION_QUALITY_FILE),
        usecols=["session_date"],
    )
    return sorted(frame["session_date"].astype(str).unique())


def _direction(values: np.ndarray) -> np.ndarray:
    return np.where(values > 0, 1, np.where(values < 0, -1, 0)).astype(
        np.int8
    )


def _safe_fraction(
    numerator: np.ndarray,
    denominator: np.ndarray,
) -> np.ndarray:
    result = np.full(len(numerator), np.nan, dtype=float)
    valid = (
        np.isfinite(numerator)
        & np.isfinite(denominator)
        & (denominator > 0)
    )
    result[valid] = np.abs(numerator[valid]) / denominator[valid]
    return result


def prepare_exp012_arrays(
    data: pd.DataFrame,
    *,
    calendar_session_dates: Iterable[str] | None = None,
    require_production_session_count: bool = False,
) -> Exp012Arrays:
    required = {
        "open",
        "high",
        "low",
        "close",
        "volume",
        "session_date",
        "session_minute",
        "segment",
    }
    missing = sorted(required.difference(data.columns))
    if missing:
        raise ValueError(
            "EXP-012 data are missing columns: " + ", ".join(missing)
        )

    local = data.copy()
    local["session_date"] = local["session_date"].astype(str)
    years = pd.to_datetime(local["session_date"]).dt.year
    local = local.loc[years.between(2020, 2025)].copy()
    local = local.loc[
        local["session_minute"].between(0, CONTEXT_END_MINUTE - 1)
    ].sort_values(["session_date", "session_minute"], kind="stable")

    if local.duplicated(["session_date", "session_minute"]).any():
        raise ValueError("EXP-012 data contain duplicate session minutes.")
    counts = local.groupby("session_date", sort=True).size()
    if counts.empty or not counts.eq(CONTEXT_END_MINUTE).all():
        raise ValueError(
            "Every EXP-012 session must contain minutes 0 through 1319."
        )
    if require_production_session_count and len(counts) != 1331:
        raise ValueError(
            f"EXP-012 expected 1,331 sessions; found {len(counts):,}."
        )

    session_count = int(len(counts))
    shape = (session_count, CONTEXT_END_MINUTE)
    slots = local["session_minute"].to_numpy(dtype=int).reshape(shape)
    expected_slots = np.arange(CONTEXT_END_MINUTE, dtype=int)
    if not np.all(slots == expected_slots):
        raise ValueError("EXP-012 session-minute sequence changed.")

    session_dates = (
        local["session_date"].to_numpy().reshape(shape)[:, 0]
    )
    open_1m = local["open"].to_numpy(dtype=float).reshape(shape)
    high_1m = local["high"].to_numpy(dtype=float).reshape(shape)
    low_1m = local["low"].to_numpy(dtype=float).reshape(shape)
    close_1m = local["close"].to_numpy(dtype=float).reshape(shape)

    cash_frame = local.loc[local["segment"].eq("cash")].copy()
    cash_counts = cash_frame.groupby("session_date", sort=True).size()
    if (
        len(cash_counts) != session_count
        or not cash_counts.eq(CASH_MINUTES).all()
    ):
        raise ValueError(
            "Every EXP-012 session must retain 390 cash minutes."
        )
    cash_frame["minute_slot"] = (
        cash_frame["session_minute"] - CASH_START_MINUTE
    )
    cash = prepare_exp009_arrays(
        cash_frame,
        validate_data=False,
    )
    if not np.array_equal(cash.session_dates, session_dates):
        raise ValueError("EXP-012 context/cash session alignment changed.")

    overnight_open = open_1m[:, 0]
    overnight_close = close_1m[:, CASH_START_MINUTE - 1]
    overnight_high = np.max(high_1m[:, :CASH_START_MINUTE], axis=1)
    overnight_low = np.min(low_1m[:, :CASH_START_MINUTE], axis=1)
    overnight_move = overnight_close - overnight_open
    overnight_drive = _safe_fraction(
        overnight_move,
        overnight_high - overnight_low,
    )

    premarket_open = open_1m[:, PREMARKET_START_MINUTE]
    premarket_close = close_1m[:, CASH_START_MINUTE - 1]
    premarket_high = np.max(
        high_1m[:, PREMARKET_START_MINUTE:CASH_START_MINUTE],
        axis=1,
    )
    premarket_low = np.min(
        low_1m[:, PREMARKET_START_MINUTE:CASH_START_MINUTE],
        axis=1,
    )
    premarket_move = premarket_close - premarket_open
    premarket_drive = _safe_fraction(
        premarket_move,
        premarket_high - premarket_low,
    )

    calendar = (
        sorted({str(value) for value in calendar_session_dates})
        if calendar_session_dates is not None
        else _default_calendar_dates()
    )
    calendar_position = {
        session_date: position
        for position, session_date in enumerate(calendar)
    }
    included_position = {
        session_date: position
        for position, session_date in enumerate(session_dates)
    }
    previous_available = np.zeros(session_count, dtype=bool)
    previous_close = np.full(session_count, np.nan, dtype=float)
    previous_range = np.full(session_count, np.nan, dtype=float)
    for current_index, session_date in enumerate(session_dates):
        position = calendar_position.get(str(session_date))
        if position is None or position == 0:
            continue
        previous_date = calendar[position - 1]
        previous_index = included_position.get(previous_date)
        if previous_index is None:
            continue
        previous_available[current_index] = True
        previous_close[current_index] = close_1m[
            previous_index, CONTEXT_END_MINUTE - 1
        ]
        previous_range[current_index] = (
            np.max(
                high_1m[
                    previous_index,
                    CASH_START_MINUTE:CONTEXT_END_MINUTE,
                ]
            )
            - np.min(
                low_1m[
                    previous_index,
                    CASH_START_MINUTE:CONTEXT_END_MINUTE,
                ]
            )
        )

    gap_move = cash.open[:, 0] - previous_close
    gap_fraction = _safe_fraction(gap_move, previous_range)
    gap_fraction[~previous_available] = np.nan

    return Exp012Arrays(
        cash=cash,
        overnight_open=overnight_open.copy(),
        overnight_high=overnight_high,
        overnight_low=overnight_low,
        overnight_close=overnight_close.copy(),
        overnight_drive_fraction=overnight_drive,
        overnight_direction=_direction(overnight_move),
        premarket_open=premarket_open.copy(),
        premarket_high=premarket_high,
        premarket_low=premarket_low,
        premarket_close=premarket_close.copy(),
        premarket_drive_fraction=premarket_drive,
        premarket_direction=_direction(premarket_move),
        previous_cash_available=previous_available,
        previous_cash_close=previous_close,
        previous_cash_range=previous_range,
        gap_fraction=gap_fraction,
        gap_direction=_direction(gap_move),
    )


def _blank_signals(
    arrays: Exp012Arrays,
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
    arrays: Exp012Arrays,
    session: int,
    *,
    direction: int,
    signal_bar: int,
    entry_bar: int,
    stop: float,
    target: float,
    reference: float,
) -> bool:
    cash = arrays.cash
    entry_minute = entry_bar * 5
    if (
        direction not in {-1, 1}
        or entry_bar >= cash.open_5m.shape[1]
        or entry_minute >= 385
        or not np.isfinite(stop)
    ):
        return False
    entry = float(cash.open_5m[session, entry_bar])
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


def _first_bar_stop(
    arrays: Exp012Arrays,
    session: int,
    direction: int,
) -> float:
    return float(
        arrays.cash.low_5m[session, 0]
        if direction == 1
        else arrays.cash.high_5m[session, 0]
    )


def _first_bar_direction(
    arrays: Exp012Arrays,
    session: int,
) -> int:
    move = (
        arrays.cash.close_5m[session, 0]
        - arrays.cash.open_5m[session, 0]
    )
    return 1 if move > 0 else -1 if move < 0 else 0


def _gap_continuation_signals(
    arrays: Exp012Arrays,
    candidate: Exp009Candidate,
) -> Exp009Signals:
    signals = _blank_signals(arrays, candidate)
    threshold = float(candidate.parameters["minimum_gap_fraction"])
    exit_mode = str(candidate.parameters["exit_mode"])
    for session in range(arrays.session_count):
        direction = int(arrays.gap_direction[session])
        if (
            not np.isfinite(arrays.gap_fraction[session])
            or arrays.gap_fraction[session] < threshold
            or direction == 0
            or _first_bar_direction(arrays, session) != direction
        ):
            continue
        stop = _first_bar_stop(arrays, session, direction)
        entry = float(arrays.cash.open_5m[session, 1])
        risk = direction * (entry - stop)
        target = (
            np.nan
            if exit_mode == "time"
            else entry + direction * 1.5 * risk
        )
        _assign_signal(
            signals,
            arrays,
            session,
            direction=direction,
            signal_bar=0,
            entry_bar=1,
            stop=stop,
            target=target,
            reference=float(arrays.gap_fraction[session]),
        )
    return signals


def _gap_fade_signals(
    arrays: Exp012Arrays,
    candidate: Exp009Candidate,
) -> Exp009Signals:
    signals = _blank_signals(arrays, candidate)
    threshold = float(candidate.parameters["minimum_gap_fraction"])
    exit_mode = str(candidate.parameters["exit_mode"])
    for session in range(arrays.session_count):
        gap_direction = int(arrays.gap_direction[session])
        direction = -gap_direction
        if (
            not np.isfinite(arrays.gap_fraction[session])
            or arrays.gap_fraction[session] < threshold
            or gap_direction == 0
            or _first_bar_direction(arrays, session) != direction
        ):
            continue
        stop = _first_bar_stop(arrays, session, direction)
        entry = float(arrays.cash.open_5m[session, 1])
        risk = direction * (entry - stop)
        target = (
            float(arrays.previous_cash_close[session])
            if exit_mode == "prior_cash_close_or_time"
            else entry + direction * risk
        )
        _assign_signal(
            signals,
            arrays,
            session,
            direction=direction,
            signal_bar=0,
            entry_bar=1,
            stop=stop,
            target=target,
            reference=float(arrays.gap_fraction[session]),
        )
    return signals


def _overnight_continuation_signals(
    arrays: Exp012Arrays,
    candidate: Exp009Candidate,
) -> Exp009Signals:
    signals = _blank_signals(arrays, candidate)
    threshold = float(candidate.parameters["minimum_drive_fraction"])
    exit_mode = str(candidate.parameters["exit_mode"])
    for session in range(arrays.session_count):
        direction = int(arrays.overnight_direction[session])
        if (
            not np.isfinite(arrays.overnight_drive_fraction[session])
            or arrays.overnight_drive_fraction[session] < threshold
            or direction == 0
            or _first_bar_direction(arrays, session) != direction
        ):
            continue
        stop = _first_bar_stop(arrays, session, direction)
        entry = float(arrays.cash.open_5m[session, 1])
        risk = direction * (entry - stop)
        target = (
            np.nan
            if exit_mode == "time"
            else entry + direction * 1.5 * risk
        )
        _assign_signal(
            signals,
            arrays,
            session,
            direction=direction,
            signal_bar=0,
            entry_bar=1,
            stop=stop,
            target=target,
            reference=float(arrays.overnight_drive_fraction[session]),
        )
    return signals


def _overnight_reversal_signals(
    arrays: Exp012Arrays,
    candidate: Exp009Candidate,
) -> Exp009Signals:
    signals = _blank_signals(arrays, candidate)
    threshold = float(candidate.parameters["minimum_drive_fraction"])
    exit_mode = str(candidate.parameters["exit_mode"])
    for session in range(arrays.session_count):
        overnight_direction = int(arrays.overnight_direction[session])
        direction = -overnight_direction
        if (
            not np.isfinite(arrays.overnight_drive_fraction[session])
            or arrays.overnight_drive_fraction[session] < threshold
            or overnight_direction == 0
            or _first_bar_direction(arrays, session) != direction
        ):
            continue
        stop = _first_bar_stop(arrays, session, direction)
        entry = float(arrays.cash.open_5m[session, 1])
        risk = direction * (entry - stop)
        target = (
            float(arrays.overnight_open[session])
            if exit_mode == "overnight_open_or_time"
            else entry + direction * risk
        )
        _assign_signal(
            signals,
            arrays,
            session,
            direction=direction,
            signal_bar=0,
            entry_bar=1,
            stop=stop,
            target=target,
            reference=float(arrays.overnight_drive_fraction[session]),
        )
    return signals


def _overnight_breakout_signals(
    arrays: Exp012Arrays,
    candidate: Exp009Candidate,
) -> Exp009Signals:
    signals = _blank_signals(arrays, candidate)
    deadline = str(candidate.parameters["last_signal_time"])
    final_signal_bar = {"10:30": 11, "12:00": 29}[deadline]
    reward_to_risk = float(candidate.parameters["reward_to_risk"])
    for session in range(arrays.session_count):
        overnight_high = float(arrays.overnight_high[session])
        overnight_low = float(arrays.overnight_low[session])
        if (
            not np.isfinite(overnight_high)
            or not np.isfinite(overnight_low)
            or overnight_high <= overnight_low
        ):
            continue
        for bar in range(0, final_signal_bar + 1):
            close = float(arrays.cash.close_5m[session, bar])
            direction = (
                1
                if close > overnight_high
                else -1
                if close < overnight_low
                else 0
            )
            if direction == 0:
                continue
            stop = float(
                arrays.cash.low_5m[session, bar]
                if direction == 1
                else arrays.cash.high_5m[session, bar]
            )
            entry = float(arrays.cash.open_5m[session, bar + 1])
            risk = direction * (entry - stop)
            target = entry + direction * reward_to_risk * risk
            _assign_signal(
                signals,
                arrays,
                session,
                direction=direction,
                signal_bar=bar,
                entry_bar=bar + 1,
                stop=stop,
                target=target,
                reference=overnight_high - overnight_low,
            )
            break
    return signals


def _premarket_continuation_signals(
    arrays: Exp012Arrays,
    candidate: Exp009Candidate,
) -> Exp009Signals:
    signals = _blank_signals(arrays, candidate)
    threshold = float(candidate.parameters["minimum_drive_fraction"])
    exit_mode = str(candidate.parameters["exit_mode"])
    for session in range(arrays.session_count):
        direction = int(arrays.premarket_direction[session])
        if (
            not np.isfinite(arrays.premarket_drive_fraction[session])
            or arrays.premarket_drive_fraction[session] < threshold
            or direction == 0
            or _first_bar_direction(arrays, session) != direction
        ):
            continue
        stop = _first_bar_stop(arrays, session, direction)
        entry = float(arrays.cash.open_5m[session, 1])
        risk = direction * (entry - stop)
        target = (
            np.nan
            if exit_mode == "time"
            else entry + direction * 1.5 * risk
        )
        _assign_signal(
            signals,
            arrays,
            session,
            direction=direction,
            signal_bar=0,
            entry_bar=1,
            stop=stop,
            target=target,
            reference=float(arrays.premarket_drive_fraction[session]),
        )
    return signals


SIGNAL_BUILDERS: dict[
    str,
    Callable[[Exp012Arrays, Exp009Candidate], Exp009Signals],
] = {
    "gap_continuation": _gap_continuation_signals,
    "gap_fade": _gap_fade_signals,
    "overnight_momentum_continuation": (
        _overnight_continuation_signals
    ),
    "overnight_inventory_reversal": _overnight_reversal_signals,
    "overnight_range_breakout": _overnight_breakout_signals,
    "premarket_momentum_continuation": (
        _premarket_continuation_signals
    ),
}


def generate_exp012_signals(
    arrays: Exp012Arrays,
    candidate: Exp009Candidate,
) -> Exp009Signals:
    builder = SIGNAL_BUILDERS.get(candidate.family_id)
    if builder is None:
        raise ValueError(
            f"Unsupported EXP-012 family: {candidate.family_id}"
        )
    return builder(arrays, candidate)


def _candidate_context(
    arrays: Exp012Arrays,
    candidate: Exp009Candidate,
) -> tuple[np.ndarray, np.ndarray, str]:
    family = candidate.family_id
    if family.startswith("gap_"):
        values = arrays.gap_fraction
        threshold = float(candidate.parameters["minimum_gap_fraction"])
        eligible = np.isfinite(values) & (values >= threshold)
        return values, eligible, "gap_fraction"
    if family.startswith("overnight_momentum") or family.startswith(
        "overnight_inventory"
    ):
        values = arrays.overnight_drive_fraction
        threshold = float(candidate.parameters["minimum_drive_fraction"])
        eligible = np.isfinite(values) & (values >= threshold)
        return values, eligible, "overnight_drive_fraction"
    if family == "premarket_momentum_continuation":
        values = arrays.premarket_drive_fraction
        threshold = float(candidate.parameters["minimum_drive_fraction"])
        eligible = np.isfinite(values) & (values >= threshold)
        return values, eligible, "premarket_drive_fraction"
    values = arrays.overnight_high - arrays.overnight_low
    eligible = np.isfinite(values) & (values > 0)
    return values, eligible, "overnight_range_points"


def run_exp012_candidate(
    arrays: Exp012Arrays,
    candidate: Exp009Candidate,
    *,
    symbol: str,
    slippage_ticks_per_side: float = 1.0,
) -> Exp009Result:
    signals = generate_exp012_signals(arrays, candidate)
    simulation = execute_exp009_signals(
        arrays.cash,
        signals,
        symbol=symbol,
        slippage_ticks_per_side=slippage_ticks_per_side,
    )
    base = build_exp009_result(simulation)
    context_values, eligible, value_name = _candidate_context(
        arrays, candidate
    )
    trade_value_map = dict(zip(arrays.session_dates, context_values))
    trades = base.trades.assign(
        context_value_name=value_name,
        context_value=base.trades["session_date"].map(trade_value_map),
    )
    eligible_values = context_values[eligible]
    trade_directions = simulation.direction[simulation.trade_mask]
    summary = {
        **base.summary,
        "context_value_name": value_name,
        "feature_eligible_sessions": int(eligible.sum()),
        "feature_eligible_rate": float(eligible.mean()),
        "signal_confirmed_sessions": int(simulation.trade_mask.sum()),
        "signal_confirmation_rate": (
            float(simulation.trade_mask.sum() / eligible.sum())
            if eligible.sum()
            else 0.0
        ),
        "context_value_mean": (
            float(np.mean(eligible_values))
            if eligible_values.size
            else 0.0
        ),
        "context_value_median": (
            float(np.median(eligible_values))
            if eligible_values.size
            else 0.0
        ),
        "context_long_trades": int((trade_directions == 1).sum()),
        "context_short_trades": int((trade_directions == -1).sum()),
    }
    return replace(base, summary=summary, trades=trades)


def context_feature_table(arrays: Exp012Arrays) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "session_date": arrays.session_dates,
            "year": arrays.years,
            "previous_cash_available": arrays.previous_cash_available,
            "previous_cash_close": arrays.previous_cash_close,
            "previous_cash_range": arrays.previous_cash_range,
            "gap_fraction": arrays.gap_fraction,
            "gap_direction": arrays.gap_direction,
            "overnight_open": arrays.overnight_open,
            "overnight_high": arrays.overnight_high,
            "overnight_low": arrays.overnight_low,
            "overnight_close": arrays.overnight_close,
            "overnight_drive_fraction": (
                arrays.overnight_drive_fraction
            ),
            "overnight_direction": arrays.overnight_direction,
            "premarket_open": arrays.premarket_open,
            "premarket_high": arrays.premarket_high,
            "premarket_low": arrays.premarket_low,
            "premarket_close": arrays.premarket_close,
            "premarket_drive_fraction": (
                arrays.premarket_drive_fraction
            ),
            "premarket_direction": arrays.premarket_direction,
        }
    )
