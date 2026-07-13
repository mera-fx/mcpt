from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Any

import numpy as np
import pandas as pd

from alpaca_historical_data import (
    validate_exp004_clean_data,
)


VALID_DIRECTION_MODES = (
    "long_only",
    "short_only",
    "both",
)


@dataclass(frozen=True)
class OrbBacktestResult:
    parameters: dict[str, Any]
    summary: dict[str, Any]
    trades: pd.DataFrame
    equity_curve: pd.DataFrame


def _profit_factor(
    pnl: pd.Series,
) -> float:
    gains = float(
        pnl[pnl > 0].sum()
    )

    losses = abs(
        float(
            pnl[pnl < 0].sum()
        )
    )

    if losses > 0:
        return gains / losses

    if gains > 0:
        return float("inf")

    return float("nan")


def _simulate_session(
    session: pd.DataFrame,
    *,
    opening_range_minutes: int,
    direction_mode: str,
    total_cost_bps_per_side: float,
) -> dict[str, Any] | None:
    opening_range_minutes = int(
        opening_range_minutes
    )

    if opening_range_minutes not in {
        5,
        15,
        30,
    }:
        raise ValueError(
            "opening_range_minutes must be "
            "5, 15, or 30."
        )

    if direction_mode not in (
        VALID_DIRECTION_MODES
    ):
        raise ValueError(
            "Invalid direction_mode."
        )

    if len(session) != 78:
        raise ValueError(
            "ORB sessions must contain "
            "exactly 78 bars."
        )

    local = session.copy()
    local.index = local.index.tz_convert(
        "America/New_York"
    )

    opening_bars = (
        opening_range_minutes // 5
    )

    range_frame = local.iloc[
        :opening_bars
    ]

    range_high = float(
        range_frame["high"].max()
    )

    range_low = float(
        range_frame["low"].min()
    )

    cutoff_clock = pd.Timestamp(
        "11:55"
    ).time()

    forced_flat_clock = pd.Timestamp(
        "15:55"
    ).time()

    forced_positions = np.flatnonzero(
        np.array(
            [
                timestamp.time()
                == forced_flat_clock
                for timestamp in local.index
            ],
            dtype=bool,
        )
    )

    if len(forced_positions) != 1:
        raise ValueError(
            "Session does not contain one "
            "15:55 ET forced-flat bar."
        )

    forced_position = int(
        forced_positions[0]
    )

    signal_position: int | None = None
    direction: int | None = None

    for position in range(
        opening_bars,
        forced_position,
    ):
        timestamp = local.index[
            position
        ]

        if timestamp.time() > cutoff_clock:
            break

        close = float(
            local["close"].iloc[
                position
            ]
        )

        long_break = (
            close > range_high
        )

        short_break = (
            close < range_low
        )

        if (
            long_break
            and direction_mode
            in {"long_only", "both"}
        ):
            signal_position = position
            direction = 1
            break

        if (
            short_break
            and direction_mode
            in {"short_only", "both"}
        ):
            signal_position = position
            direction = -1
            break

    if (
        signal_position is None
        or direction is None
    ):
        return None

    entry_position = (
        signal_position + 1
    )

    if entry_position >= forced_position:
        return None

    entry_time = local.index[
        entry_position
    ]

    if entry_time.time() > pd.Timestamp(
        "12:00"
    ).time():
        raise RuntimeError(
            "ORB entry occurred after the "
            "locked 12:00 ET deadline."
        )

    entry_price = float(
        local["open"].iloc[
            entry_position
        ]
    )

    stop_price = (
        range_low
        if direction == 1
        else range_high
    )

    exit_position: int | None = None
    exit_price: float | None = None
    exit_reason: str | None = None

    for position in range(
        entry_position,
        forced_position,
    ):
        bar_open = float(
            local["open"].iloc[
                position
            ]
        )

        bar_high = float(
            local["high"].iloc[
                position
            ]
        )

        bar_low = float(
            local["low"].iloc[
                position
            ]
        )

        if direction == 1:
            if bar_open <= stop_price:
                exit_position = position
                exit_price = bar_open
                exit_reason = (
                    "gap_through_range_stop"
                )
                break

            if bar_low <= stop_price:
                exit_position = position
                exit_price = stop_price
                exit_reason = (
                    "range_stop"
                )
                break
        else:
            if bar_open >= stop_price:
                exit_position = position
                exit_price = bar_open
                exit_reason = (
                    "gap_through_range_stop"
                )
                break

            if bar_high >= stop_price:
                exit_position = position
                exit_price = stop_price
                exit_reason = (
                    "range_stop"
                )
                break

    if exit_position is None:
        exit_position = forced_position
        exit_price = float(
            local["open"].iloc[
                forced_position
            ]
        )
        exit_reason = "forced_flat_1555"

    gross_return = (
        direction
        * (
            float(exit_price)
            - entry_price
        )
        / entry_price
    )

    total_cost_rate = (
        float(total_cost_bps_per_side)
        / 10_000
    )

    net_return = (
        gross_return
        - 2.0 * total_cost_rate
    )

    return {
        "session_date": str(
            session[
                "session_date"
            ].iloc[0]
        ),
        "direction": (
            "long"
            if direction == 1
            else "short"
        ),
        "signal_time": (
            local.index[
                signal_position
            ].isoformat()
        ),
        "entry_time": (
            local.index[
                entry_position
            ].isoformat()
        ),
        "exit_time": (
            local.index[
                exit_position
            ].isoformat()
        ),
        "opening_range_high": (
            range_high
        ),
        "opening_range_low": (
            range_low
        ),
        "entry_price": entry_price,
        "exit_price": float(
            exit_price
        ),
        "gross_return_percent": (
            gross_return * 100
        ),
        "net_return_percent": (
            net_return * 100
        ),
        "bars_held": int(
            max(
                1,
                exit_position
                - entry_position
                + 1,
            )
        ),
        "exit_reason": exit_reason,
    }


def run_orb_backtest(
    data: pd.DataFrame,
    *,
    opening_range_minutes: int,
    direction_mode: str,
    starting_capital: float = 100_000.0,
    total_cost_bps_per_side: float = 1.5,
) -> OrbBacktestResult:
    validate_exp004_clean_data(
        data
    )

    if starting_capital <= 0:
        raise ValueError(
            "starting_capital must be "
            "positive."
        )

    if total_cost_bps_per_side < 0:
        raise ValueError(
            "Costs cannot be negative."
        )

    parameters = {
        "opening_range_minutes": int(
            opening_range_minutes
        ),
        "direction_mode": (
            direction_mode
        ),
    }

    equity = float(
        starting_capital
    )

    peak = equity
    trade_rows: list[
        dict[str, Any]
    ] = []

    equity_rows: list[
        dict[str, Any]
    ] = []

    for session_date, session in (
        data.groupby(
            "session_date",
            sort=True,
        )
    ):
        trade = _simulate_session(
            session,
            opening_range_minutes=(
                opening_range_minutes
            ),
            direction_mode=(
                direction_mode
            ),
            total_cost_bps_per_side=(
                total_cost_bps_per_side
            ),
        )

        session_return = 0.0

        if trade is not None:
            equity_before = equity

            session_return = (
                float(
                    trade[
                        "net_return_percent"
                    ]
                )
                / 100
            )

            equity = (
                equity
                * (
                    1.0
                    + session_return
                )
            )

            trade[
                "equity_before"
            ] = equity_before

            trade["pnl_cash"] = (
                equity - equity_before
            )

            trade[
                "equity_after"
            ] = equity

            trade_rows.append(
                trade
            )

        peak = max(
            peak,
            equity,
        )

        drawdown = (
            equity / peak - 1.0
        )

        equity_rows.append(
            {
                "session_date": (
                    session_date
                ),
                "session_return_percent": (
                    session_return * 100
                ),
                "equity": equity,
                "drawdown_percent": (
                    drawdown * 100
                ),
                "had_trade": (
                    trade is not None
                ),
            }
        )

    trades = pd.DataFrame(
        trade_rows
    )

    equity_curve = pd.DataFrame(
        equity_rows
    )

    if trades.empty:
        profit_factor = float(
            "nan"
        )
        win_rate = 0.0
        average_trade = float(
            "nan"
        )
        long_trades = 0
        short_trades = 0
    else:
        profit_factor = (
            _profit_factor(
                trades["pnl_cash"]
            )
        )

        win_rate = float(
            (
                trades[
                    "pnl_cash"
                ] > 0
            ).mean()
            * 100
        )

        average_trade = float(
            trades[
                "net_return_percent"
            ].mean()
        )

        long_trades = int(
            trades[
                "direction"
            ].eq("long").sum()
        )

        short_trades = int(
            trades[
                "direction"
            ].eq("short").sum()
        )

    total_return = (
        equity
        / starting_capital
        - 1.0
    ) * 100

    max_drawdown = (
        float(
            equity_curve[
                "drawdown_percent"
            ].min()
        )
        if not equity_curve.empty
        else 0.0
    )

    summary = {
        "starting_capital": float(
            starting_capital
        ),
        "ending_equity": float(
            equity
        ),
        "total_return_percent": (
            float(total_return)
        ),
        "max_drawdown_percent": (
            max_drawdown
        ),
        "completed_trades": int(
            len(trades)
        ),
        "long_trades": (
            long_trades
        ),
        "short_trades": (
            short_trades
        ),
        "win_rate_percent": (
            win_rate
        ),
        "trade_profit_factor": (
            float(profit_factor)
        ),
        "average_trade_percent": (
            average_trade
        ),
    }

    return OrbBacktestResult(
        parameters=parameters,
        summary=summary,
        trades=trades,
        equity_curve=equity_curve,
    )


def expand_orb_grid(
    grid: dict[str, list[Any]],
) -> list[dict[str, Any]]:
    expected = {
        "opening_range_minutes",
        "direction_mode",
    }

    if set(grid) != expected:
        raise ValueError(
            "ORB grid must contain exactly "
            "opening_range_minutes and "
            "direction_mode."
        )

    combinations = []

    for opening_range, direction in (
        product(
            grid[
                "opening_range_minutes"
            ],
            grid["direction_mode"],
        )
    ):
        combinations.append(
            {
                "opening_range_minutes": int(
                    opening_range
                ),
                "direction_mode": str(
                    direction
                ),
            }
        )

    return combinations


def optimize_orb(
    data: pd.DataFrame,
    *,
    grid: dict[str, list[Any]],
    starting_capital: float = 100_000.0,
    total_cost_bps_per_side: float = 1.5,
    minimum_valid_trades: int = 100,
) -> tuple[
    pd.DataFrame,
    dict[str, Any],
    OrbBacktestResult,
]:
    combinations = expand_orb_grid(
        grid
    )

    rows: list[
        dict[str, Any]
    ] = []

    results: list[
        OrbBacktestResult
    ] = []

    for grid_position, parameters in (
        enumerate(combinations)
    ):
        result = run_orb_backtest(
            data,
            **parameters,
            starting_capital=(
                starting_capital
            ),
            total_cost_bps_per_side=(
                total_cost_bps_per_side
            ),
        )

        valid = (
            result.summary[
                "completed_trades"
            ]
            >= minimum_valid_trades
            and not np.isnan(
                result.summary[
                    "trade_profit_factor"
                ]
            )
        )

        row = {
            **parameters,
            **result.summary,
            "minimum_valid_trades": int(
                minimum_valid_trades
            ),
            "valid": bool(valid),
            "grid_position": int(
                grid_position
            ),
        }

        rows.append(row)
        results.append(result)

    optimization = pd.DataFrame(
        rows
    )

    valid_rows = optimization[
        optimization["valid"]
    ].copy()

    if valid_rows.empty:
        raise RuntimeError(
            "Every ORB parameter combination "
            "was invalid under the locked "
            "minimum trade count."
        )

    ranked = valid_rows.sort_values(
        by=[
            "trade_profit_factor",
            "total_return_percent",
            "max_drawdown_percent",
            "grid_position",
        ],
        ascending=[
            False,
            False,
            False,
            True,
        ],
        kind="mergesort",
    )

    best_row = ranked.iloc[0]

    best_parameters = {
        "opening_range_minutes": int(
            best_row[
                "opening_range_minutes"
            ]
        ),
        "direction_mode": str(
            best_row[
                "direction_mode"
            ]
        ),
    }

    best_index = int(
        best_row["grid_position"]
    )

    return (
        optimization,
        best_parameters,
        results[best_index],
    )
