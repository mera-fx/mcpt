from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from exp005_futures_orb import (
    FuturesOrbResult,
    get_contract_spec,
    validate_five_minute_data,
)
from exp006_preregistration import (
    FINAL_SIGNAL_BY_ENTRY,
    build_locked_parameter_grid,
)

EXPECTED_BARS_PER_SESSION = 78
FORCED_FLAT_SLOT = 77
FINAL_ENTRY_SLOT = {
    "10:30": 12,
    "11:15": 21,
    "12:00": 30,
}
FINAL_SIGNAL_SLOT = {
    key: value - 1
    for key, value in FINAL_ENTRY_SLOT.items()
}
DIRECTION_CODE = {
    "long": 1,
    "short": -1,
    "both": 0,
}


@dataclass(frozen=True)
class OrbParameters:
    opening_range_minutes: int
    final_entry_time_new_york: str
    direction_mode: str

    @property
    def opening_range_bars(self) -> int:
        return self.opening_range_minutes // 5

    @property
    def final_entry_slot(self) -> int:
        return FINAL_ENTRY_SLOT[
            self.final_entry_time_new_york
        ]

    @property
    def final_signal_slot(self) -> int:
        return FINAL_SIGNAL_SLOT[
            self.final_entry_time_new_york
        ]

    @property
    def final_signal_time_new_york(self) -> str:
        return FINAL_SIGNAL_BY_ENTRY[
            self.final_entry_time_new_york
        ]

    def key(self) -> str:
        return (
            f"or{self.opening_range_minutes}_"
            f"entry{self.final_entry_time_new_york.replace(':', '')}_"
            f"{self.direction_mode}"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "opening_range_minutes": (
                self.opening_range_minutes
            ),
            "final_entry_time_new_york": (
                self.final_entry_time_new_york
            ),
            "final_signal_time_new_york": (
                self.final_signal_time_new_york
            ),
            "direction_mode": self.direction_mode,
            "parameter_key": self.key(),
        }


@dataclass(frozen=True)
class OrbArrays:
    index: pd.DatetimeIndex
    session_dates: np.ndarray
    years: np.ndarray
    open: np.ndarray
    high: np.ndarray
    low: np.ndarray
    close: np.ndarray
    volume: np.ndarray

    @property
    def session_count(self) -> int:
        return int(self.open.shape[0])

    def subset(self, mask: np.ndarray) -> "OrbArrays":
        selected = np.asarray(mask, dtype=bool)
        if selected.shape != (self.session_count,):
            raise ValueError(
                "EXP-006 session mask has the wrong shape."
            )
        row_mask = np.repeat(
            selected,
            EXPECTED_BARS_PER_SESSION,
        )
        return OrbArrays(
            index=self.index[row_mask],
            session_dates=self.session_dates[selected],
            years=self.years[selected],
            open=self.open[selected],
            high=self.high[selected],
            low=self.low[selected],
            close=self.close[selected],
            volume=self.volume[selected],
        )


@dataclass(frozen=True)
class CandidateSimulation:
    parameters: OrbParameters
    session_dates: np.ndarray
    years: np.ndarray
    trade_mask: np.ndarray
    direction: np.ndarray
    signal_slot: np.ndarray
    entry_slot: np.ndarray
    exit_slot: np.ndarray
    range_high: np.ndarray
    range_low: np.ndarray
    entry_price: np.ndarray
    exit_price: np.ndarray
    net_pnl_usd: np.ndarray
    gross_pnl_usd: np.ndarray
    transaction_cost_usd: np.ndarray
    exit_reason: np.ndarray



def locked_parameters() -> tuple[OrbParameters, ...]:
    return tuple(
        OrbParameters(
            opening_range_minutes=int(
                item["opening_range_minutes"]
            ),
            final_entry_time_new_york=str(
                item["final_entry_time_new_york"]
            ),
            direction_mode=str(
                item["direction_mode"]
            ),
        )
        for item in build_locked_parameter_grid()
    )



def validate_parameters(
    parameters: OrbParameters,
) -> None:
    if parameters not in locked_parameters():
        raise ValueError(
            "EXP-006 parameters are outside the locked "
            "27-combination grid."
        )
    if parameters.opening_range_minutes % 5:
        raise ValueError(
            "Opening-range minutes must align to five-minute bars."
        )
    if (
        parameters.opening_range_bars < 1
        or parameters.final_signal_slot
        < parameters.opening_range_bars
    ):
        raise ValueError(
            "EXP-006 signal window is invalid."
        )



def prepare_orb_arrays(
    data: pd.DataFrame,
    *,
    validate_data: bool = True,
) -> OrbArrays:
    if validate_data:
        validate_five_minute_data(data)

    local = data.sort_index().copy()
    counts = local.groupby(
        "session_date",
        sort=True,
    ).size()
    if (
        counts.empty
        or not counts.eq(
            EXPECTED_BARS_PER_SESSION
        ).all()
    ):
        raise ValueError(
            "Every EXP-006 session must contain 78 bars."
        )

    session_count = int(len(counts))
    sessions = (
        local["session_date"]
        .astype(str)
        .to_numpy()
        .reshape(
            session_count,
            EXPECTED_BARS_PER_SESSION,
        )[:, 0]
    )
    years = pd.to_datetime(sessions).year.to_numpy(
        dtype=int
    )

    return OrbArrays(
        index=local.index,
        session_dates=sessions,
        years=years,
        open=local["open"].to_numpy(
            dtype=float
        ).reshape(
            session_count,
            EXPECTED_BARS_PER_SESSION,
        ),
        high=local["high"].to_numpy(
            dtype=float
        ).reshape(
            session_count,
            EXPECTED_BARS_PER_SESSION,
        ),
        low=local["low"].to_numpy(
            dtype=float
        ).reshape(
            session_count,
            EXPECTED_BARS_PER_SESSION,
        ),
        close=local["close"].to_numpy(
            dtype=float
        ).reshape(
            session_count,
            EXPECTED_BARS_PER_SESSION,
        ),
        volume=local["volume"].to_numpy(
            dtype=float
        ).reshape(
            session_count,
            EXPECTED_BARS_PER_SESSION,
        ),
    )



def _first_true(
    values: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    present = values.any(axis=1)
    position = values.argmax(axis=1)
    return present, position



def simulate_candidate(
    arrays: OrbArrays,
    *,
    parameters: OrbParameters,
    symbol: str,
    slippage_ticks_per_side: float = 1.0,
) -> CandidateSimulation:
    validate_parameters(parameters)
    contract = get_contract_spec(
        symbol,
        slippage_ticks_per_side=(
            slippage_ticks_per_side
        ),
    )

    session_count = arrays.session_count
    opening_bars = parameters.opening_range_bars
    range_high = arrays.high[
        :, :opening_bars
    ].max(axis=1)
    range_low = arrays.low[
        :, :opening_bars
    ].min(axis=1)

    start = opening_bars
    stop = parameters.final_signal_slot + 1
    candidate_close = arrays.close[:, start:stop]
    allow_long = parameters.direction_mode in {
        "long",
        "both",
    }
    allow_short = parameters.direction_mode in {
        "short",
        "both",
    }
    long_break = (
        candidate_close > range_high[:, None]
        if allow_long
        else np.zeros_like(
            candidate_close,
            dtype=bool,
        )
    )
    short_break = (
        candidate_close < range_low[:, None]
        if allow_short
        else np.zeros_like(
            candidate_close,
            dtype=bool,
        )
    )
    trigger = long_break | short_break
    trade_mask, first_relative = _first_true(
        trigger
    )
    signal_slot = start + first_relative
    row = np.arange(session_count)
    first_long = long_break[row, first_relative]
    direction = np.where(
        trade_mask,
        np.where(first_long, 1, -1),
        0,
    ).astype(int)
    entry_slot = signal_slot + 1

    if np.any(
        trade_mask
        & (
            entry_slot
            > parameters.final_entry_slot
        )
    ):
        raise RuntimeError(
            "EXP-006 entry exceeded the locked final-entry slot."
        )

    safe_entry_slot = np.where(
        trade_mask,
        entry_slot,
        0,
    )
    entry_price = arrays.open[
        row,
        safe_entry_slot,
    ]
    stop_price = np.where(
        direction == 1,
        range_low,
        range_high,
    )

    slots = np.arange(
        EXPECTED_BARS_PER_SESSION
    )[None, :]
    active = (
        trade_mask[:, None]
        & (slots >= safe_entry_slot[:, None])
        & (slots < FORCED_FLAT_SLOT)
    )
    long_gap = (
        arrays.open <= stop_price[:, None]
    ) & active & (direction[:, None] == 1)
    long_touch = (
        arrays.low <= stop_price[:, None]
    ) & active & (direction[:, None] == 1)
    short_gap = (
        arrays.open >= stop_price[:, None]
    ) & active & (direction[:, None] == -1)
    short_touch = (
        arrays.high >= stop_price[:, None]
    ) & active & (direction[:, None] == -1)
    stop_hit = (
        long_gap
        | long_touch
        | short_gap
        | short_touch
    )
    has_stop, first_stop = _first_true(stop_hit)
    exit_slot = np.where(
        trade_mask & has_stop,
        first_stop,
        FORCED_FLAT_SLOT,
    ).astype(int)
    safe_exit_slot = np.where(
        trade_mask,
        exit_slot,
        FORCED_FLAT_SLOT,
    )
    gap_at_exit = (
        long_gap[row, safe_exit_slot]
        | short_gap[row, safe_exit_slot]
    )
    forced_price = arrays.open[
        row,
        FORCED_FLAT_SLOT,
    ]
    exit_price = np.where(
        trade_mask & has_stop,
        np.where(
            gap_at_exit,
            arrays.open[row, safe_exit_slot],
            stop_price,
        ),
        forced_price,
    )
    gross_points = direction * (
        exit_price - entry_price
    )
    gross_pnl = (
        gross_points
        * contract.multiplier_usd_per_point
    )
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
            ~has_stop,
            "forced_flat_1555",
            np.where(
                gap_at_exit,
                "gap_through_range_stop",
                "range_stop",
            ),
        ),
    ).astype(object)

    return CandidateSimulation(
        parameters=parameters,
        session_dates=arrays.session_dates.copy(),
        years=arrays.years.copy(),
        trade_mask=trade_mask,
        direction=direction,
        signal_slot=signal_slot.astype(int),
        entry_slot=entry_slot.astype(int),
        exit_slot=exit_slot,
        range_high=range_high,
        range_low=range_low,
        entry_price=entry_price,
        exit_price=exit_price,
        net_pnl_usd=net_pnl,
        gross_pnl_usd=gross_pnl,
        transaction_cost_usd=transaction_cost,
        exit_reason=exit_reason,
    )



def _profit_factor(pnl: np.ndarray) -> float:
    values = np.asarray(pnl, dtype=float)
    gains = float(values[values > 0].sum())
    losses = abs(
        float(values[values < 0].sum())
    )
    if losses > 0:
        return gains / losses
    if gains > 0:
        return float("inf")
    return float("nan")



def summarize_simulation(
    simulation: CandidateSimulation,
    *,
    symbol: str,
    round_trip_cost_usd: float,
    reference_capital_usd: float,
) -> dict[str, Any]:
    trade_pnl = simulation.net_pnl_usd[
        simulation.trade_mask
    ]
    cumulative = np.cumsum(
        simulation.net_pnl_usd
    )
    peak = np.maximum.accumulate(
        np.maximum(cumulative, 0.0)
    )
    drawdown = cumulative - peak
    maximum_drawdown = (
        float(drawdown.min())
        if drawdown.size
        else 0.0
    )
    completed = int(
        simulation.trade_mask.sum()
    )
    profitable_years = 0
    yearly_net: dict[int, float] = {}
    for year in sorted(set(simulation.years)):
        value = float(
            simulation.net_pnl_usd[
                simulation.years == year
            ].sum()
        )
        yearly_net[int(year)] = value
        profitable_years += int(value > 0.0)

    gross_profit = float(
        trade_pnl[trade_pnl > 0].sum()
    )
    gross_loss = abs(
        float(trade_pnl[trade_pnl < 0].sum())
    )
    net_profit = float(trade_pnl.sum())

    return {
        **simulation.parameters.to_dict(),
        "symbol": symbol.upper(),
        "included_sessions": int(
            len(simulation.session_dates)
        ),
        "completed_trades": completed,
        "long_trades": int(
            (
                simulation.trade_mask
                & (simulation.direction == 1)
            ).sum()
        ),
        "short_trades": int(
            (
                simulation.trade_mask
                & (simulation.direction == -1)
            ).sum()
        ),
        "net_profit_usd": net_profit,
        "trade_profit_factor": float(
            _profit_factor(trade_pnl)
        ),
        "win_rate_percent": (
            float((trade_pnl > 0).mean() * 100.0)
            if completed
            else 0.0
        ),
        "average_trade_usd": (
            float(trade_pnl.mean())
            if completed
            else float("nan")
        ),
        "median_trade_usd": (
            float(np.median(trade_pnl))
            if completed
            else float("nan")
        ),
        "gross_profit_usd": gross_profit,
        "gross_loss_usd": gross_loss,
        "maximum_drawdown_usd": maximum_drawdown,
        "maximum_drawdown_percent": (
            maximum_drawdown
            / float(reference_capital_usd)
            * 100.0
        ),
        "return_percent": (
            net_profit
            / float(reference_capital_usd)
            * 100.0
        ),
        "net_profit_to_drawdown": (
            net_profit / abs(maximum_drawdown)
            if maximum_drawdown < 0
            else float("inf")
        ),
        "average_trade_to_cost": (
            float(trade_pnl.mean())
            / float(round_trip_cost_usd)
            if completed
            else float("nan")
        ),
        "profitable_calendar_years": int(
            profitable_years
        ),
        "yearly_net_profit_usd": yearly_net,
        "round_trip_cost_usd": float(
            round_trip_cost_usd
        ),
        "reference_capital_usd": float(
            reference_capital_usd
        ),
    }



def run_candidate_summary(
    arrays: OrbArrays,
    *,
    parameters: OrbParameters,
    symbol: str,
    slippage_ticks_per_side: float = 1.0,
) -> dict[str, Any]:
    contract = get_contract_spec(
        symbol,
        slippage_ticks_per_side=(
            slippage_ticks_per_side
        ),
    )
    reference = (
        100_000.0
        if symbol.upper() == "NQ"
        else 10_000.0
    )
    simulation = simulate_candidate(
        arrays,
        parameters=parameters,
        symbol=symbol,
        slippage_ticks_per_side=(
            slippage_ticks_per_side
        ),
    )
    return summarize_simulation(
        simulation,
        symbol=symbol,
        round_trip_cost_usd=(
            contract.round_trip_cost_usd
        ),
        reference_capital_usd=reference,
    )



def _yearly_results_frame(
    simulation: CandidateSimulation,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for year in sorted(set(simulation.years)):
        mask = simulation.years == year
        trade_mask = mask & simulation.trade_mask
        pnl = simulation.net_pnl_usd[trade_mask]
        rows.append(
            {
                "year": int(year),
                "completed_trades": int(
                    trade_mask.sum()
                ),
                "long_trades": int(
                    (
                        trade_mask
                        & (simulation.direction == 1)
                    ).sum()
                ),
                "short_trades": int(
                    (
                        trade_mask
                        & (simulation.direction == -1)
                    ).sum()
                ),
                "net_profit_usd": float(pnl.sum()),
                "trade_profit_factor": float(
                    _profit_factor(pnl)
                ),
                "win_rate_percent": (
                    float((pnl > 0).mean() * 100.0)
                    if pnl.size
                    else 0.0
                ),
                "average_trade_usd": (
                    float(pnl.mean())
                    if pnl.size
                    else float("nan")
                ),
            }
        )
    return pd.DataFrame(rows)



def run_parameterized_orb(
    data: pd.DataFrame,
    *,
    parameters: OrbParameters,
    symbol: str,
    slippage_ticks_per_side: float = 1.0,
    validate_data: bool = True,
) -> FuturesOrbResult:
    arrays = prepare_orb_arrays(
        data,
        validate_data=validate_data,
    )
    contract = get_contract_spec(
        symbol,
        slippage_ticks_per_side=(
            slippage_ticks_per_side
        ),
    )
    simulation = simulate_candidate(
        arrays,
        parameters=parameters,
        symbol=symbol,
        slippage_ticks_per_side=(
            slippage_ticks_per_side
        ),
    )
    summary = summarize_simulation(
        simulation,
        symbol=symbol,
        round_trip_cost_usd=(
            contract.round_trip_cost_usd
        ),
        reference_capital_usd=(
            100_000.0
            if symbol.upper() == "NQ"
            else 10_000.0
        ),
    )

    local_index = arrays.index.tz_convert(
        "America/New_York"
    ).to_numpy().reshape(
        arrays.session_count,
        EXPECTED_BARS_PER_SESSION,
    )
    trade_rows: list[dict[str, Any]] = []
    cumulative = 0.0
    for index in np.flatnonzero(
        simulation.trade_mask
    ):
        pnl = float(
            simulation.net_pnl_usd[index]
        )
        cumulative += pnl
        direction = int(
            simulation.direction[index]
        )
        signal_slot = int(
            simulation.signal_slot[index]
        )
        entry_slot = int(
            simulation.entry_slot[index]
        )
        exit_slot = int(
            simulation.exit_slot[index]
        )
        trade_rows.append(
            {
                "symbol": symbol.upper(),
                "session_date": str(
                    simulation.session_dates[index]
                ),
                "direction": (
                    "long"
                    if direction == 1
                    else "short"
                ),
                "signal_time": pd.Timestamp(
                    local_index[index, signal_slot]
                ).isoformat(),
                "entry_time": pd.Timestamp(
                    local_index[index, entry_slot]
                ).isoformat(),
                "exit_time": pd.Timestamp(
                    local_index[index, exit_slot]
                ).isoformat(),
                "opening_range_high": float(
                    simulation.range_high[index]
                ),
                "opening_range_low": float(
                    simulation.range_low[index]
                ),
                "entry_price": float(
                    simulation.entry_price[index]
                ),
                "exit_price": float(
                    simulation.exit_price[index]
                ),
                "gross_pnl_usd": float(
                    simulation.gross_pnl_usd[index]
                ),
                "transaction_cost_usd": float(
                    simulation.transaction_cost_usd[index]
                ),
                "net_pnl_usd": pnl,
                "cumulative_net_pnl_usd": cumulative,
                "bars_held": int(
                    max(
                        1,
                        exit_slot - entry_slot + 1,
                    )
                ),
                "exit_reason": str(
                    simulation.exit_reason[index]
                ),
                **parameters.to_dict(),
            }
        )
    trades = pd.DataFrame(trade_rows)

    cumulative_session = np.cumsum(
        simulation.net_pnl_usd
    )
    peak = np.maximum.accumulate(
        np.maximum(cumulative_session, 0.0)
    )
    equity_curve = pd.DataFrame(
        {
            "session_date": (
                simulation.session_dates
            ),
            "session_net_pnl_usd": (
                simulation.net_pnl_usd
            ),
            "cumulative_net_pnl_usd": (
                cumulative_session
            ),
            "drawdown_usd": (
                cumulative_session - peak
            ),
            "had_trade": simulation.trade_mask,
        }
    )

    return FuturesOrbResult(
        symbol=symbol.upper(),
        contract=contract,
        summary=summary,
        trades=trades,
        equity_curve=equity_curve,
        yearly_results=_yearly_results_frame(
            simulation
        ),
    )
