from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import pandas as pd

from exp005_preregistration import (
    get_exp005_preregistration,
)


REQUIRED_COLUMNS = {
    "open",
    "high",
    "low",
    "close",
    "volume",
    "session_date",
    "slot",
}
NEW_YORK_TZ = "America/New_York"
EXPECTED_BARS_PER_SESSION = 78
OPENING_RANGE_BARS = 3
FINAL_SIGNAL_CLOCK = pd.Timestamp("11:55").time()
FINAL_ENTRY_CLOCK = pd.Timestamp("12:00").time()
FORCED_FLAT_CLOCK = pd.Timestamp("15:55").time()

# The protected importer validates the exact timestamp-to-slot map:
# slot 0 = 09:30 ET, slot 29 = 11:55 ET,
# slot 30 = 12:00 ET and slot 77 = 15:55 ET.
#
# Execution uses these integer slots rather than comparing
# pandas Timestamp.time() objects. This avoids platform/version
# differences in whether time objects retain timezone metadata.
FINAL_SIGNAL_SLOT = 29
FINAL_ENTRY_SLOT = 30
FORCED_FLAT_SLOT = 77


@dataclass(frozen=True)
class FuturesContractSpec:
    symbol: str
    multiplier_usd_per_point: float
    tick_size_points: float
    tick_value_usd: float
    commission_and_fees_usd_per_side: float
    slippage_ticks_per_side: float

    @property
    def slippage_usd_per_side(self) -> float:
        return (
            self.tick_value_usd
            * self.slippage_ticks_per_side
        )

    @property
    def total_cost_usd_per_side(self) -> float:
        return (
            self.commission_and_fees_usd_per_side
            + self.slippage_usd_per_side
        )

    @property
    def round_trip_cost_usd(self) -> float:
        return 2.0 * self.total_cost_usd_per_side

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.update(
            {
                "slippage_usd_per_side": (
                    self.slippage_usd_per_side
                ),
                "total_cost_usd_per_side": (
                    self.total_cost_usd_per_side
                ),
                "round_trip_cost_usd": (
                    self.round_trip_cost_usd
                ),
            }
        )
        return payload


@dataclass(frozen=True)
class FuturesOrbResult:
    symbol: str
    contract: FuturesContractSpec
    summary: dict[str, Any]
    trades: pd.DataFrame
    equity_curve: pd.DataFrame
    yearly_results: pd.DataFrame


def get_contract_spec(
    symbol: str,
    *,
    slippage_ticks_per_side: float = 1.0,
) -> FuturesContractSpec:
    normalized = symbol.strip().upper()

    if normalized not in {"NQ", "MNQ"}:
        raise ValueError(
            "EXP-005 supports only NQ and MNQ."
        )

    if slippage_ticks_per_side < 0:
        raise ValueError(
            "Slippage ticks cannot be negative."
        )

    record = get_exp005_preregistration()
    contract = record[
        "contract_and_cost_model"
    ][normalized]

    spec = FuturesContractSpec(
        symbol=normalized,
        multiplier_usd_per_point=float(
            contract[
                "contract_multiplier_usd_per_point"
            ]
        ),
        tick_size_points=float(
            contract["minimum_tick_points"]
        ),
        tick_value_usd=float(
            contract["tick_value_usd"]
        ),
        commission_and_fees_usd_per_side=float(
            contract[
                "commission_exchange_nfa_usd_per_side"
            ]
        ),
        slippage_ticks_per_side=float(
            slippage_ticks_per_side
        ),
    )

    expected_tick_value = (
        spec.multiplier_usd_per_point
        * spec.tick_size_points
    )

    if not np.isclose(
        expected_tick_value,
        spec.tick_value_usd,
        atol=1e-12,
        rtol=0.0,
    ):
        raise ValueError(
            f"{normalized} tick-value configuration "
            "is inconsistent."
        )

    return spec


def validate_five_minute_data(
    data: pd.DataFrame,
) -> None:
    missing = REQUIRED_COLUMNS.difference(
        data.columns
    )

    if missing:
        raise ValueError(
            "EXP-005 five-minute data is missing: "
            f"{sorted(missing)}"
        )

    if not isinstance(
        data.index,
        pd.DatetimeIndex,
    ):
        raise TypeError(
            "EXP-005 data must use a DatetimeIndex."
        )

    if data.index.tz is None:
        raise ValueError(
            "EXP-005 timestamps must be timezone-aware."
        )

    if data.index.has_duplicates:
        raise ValueError(
            "EXP-005 timestamps cannot be duplicated."
        )

    if not data.index.is_monotonic_increasing:
        raise ValueError(
            "EXP-005 timestamps must be sorted."
        )

    counts = data.groupby(
        "session_date",
        sort=True,
    ).size()

    if counts.empty:
        raise ValueError(
            "EXP-005 data contains no sessions."
        )

    if not counts.eq(
        EXPECTED_BARS_PER_SESSION
    ).all():
        raise ValueError(
            "Every EXP-005 session must contain "
            "exactly 78 five-minute bars."
        )

    numeric = data[
        [
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]
    ].astype(float)

    if not np.isfinite(
        numeric.to_numpy()
    ).all():
        raise ValueError(
            "EXP-005 OHLCV data contains non-finite values."
        )

    if (
        (numeric[["open", "high", "low", "close"]] <= 0)
        .any()
        .any()
    ):
        raise ValueError(
            "EXP-005 prices must be positive."
        )

    if (
        (numeric["high"] < numeric[["open", "close"]].max(axis=1))
        .any()
        or (
            numeric["low"]
            > numeric[["open", "close"]].min(axis=1)
        ).any()
        or (numeric["high"] < numeric["low"]).any()
    ):
        raise ValueError(
            "EXP-005 OHLC relationships are invalid."
        )

    for session_date, session in data.groupby(
        "session_date",
        sort=True,
    ):
        slots = session["slot"].to_numpy(
            dtype=int
        )

        if not np.array_equal(
            slots,
            np.arange(
                EXPECTED_BARS_PER_SESSION,
                dtype=int,
            ),
        ):
            raise ValueError(
                f"{session_date} slots are not 0 through 77."
            )

        local_index = session.index.tz_convert(
            NEW_YORK_TZ
        )

        expected = pd.date_range(
            start=(
                pd.Timestamp(
                    str(session_date),
                    tz=NEW_YORK_TZ,
                )
                + pd.Timedelta(
                    hours=9,
                    minutes=30,
                )
            ),
            periods=EXPECTED_BARS_PER_SESSION,
            freq="5min",
        )

        if not local_index.equals(expected):
            raise ValueError(
                f"{session_date} does not contain the locked "
                "09:30–15:55 ET five-minute timestamps."
            )


def _profit_factor(
    pnl: pd.Series,
) -> float:
    numeric = pnl.astype(float)
    gains = float(
        numeric[numeric > 0].sum()
    )
    losses = abs(
        float(
            numeric[numeric < 0].sum()
        )
    )

    if losses > 0:
        return gains / losses

    if gains > 0:
        return float("inf")

    return float("nan")


def _max_drawdown_cash(
    cumulative_pnl: pd.Series,
) -> float:
    if cumulative_pnl.empty:
        return 0.0

    equity = cumulative_pnl.astype(float)
    peaks = np.maximum.accumulate(
        np.maximum(
            equity.to_numpy(),
            0.0,
        )
    )
    drawdowns = (
        equity.to_numpy()
        - peaks
    )

    return float(
        drawdowns.min()
    )


def _simulate_session(
    session: pd.DataFrame,
    *,
    contract: FuturesContractSpec,
) -> dict[str, Any] | None:
    local = session.copy()
    local.index = local.index.tz_convert(
        NEW_YORK_TZ
    )

    range_frame = local.iloc[
        :OPENING_RANGE_BARS
    ]

    range_high = float(
        range_frame["high"].max()
    )
    range_low = float(
        range_frame["low"].min()
    )

    slots = local["slot"].to_numpy(
        dtype=int
    )

    forced_positions = np.flatnonzero(
        slots == FORCED_FLAT_SLOT
    )

    if len(forced_positions) != 1:
        raise ValueError(
            "Session must contain exactly one "
            "slot-77 / 15:55 ET forced-flat bar."
        )

    forced_position = int(
        forced_positions[0]
    )
    signal_position: int | None = None
    direction: int | None = None

    for position in range(
        OPENING_RANGE_BARS,
        forced_position,
    ):
        if slots[position] > FINAL_SIGNAL_SLOT:
            break

        close = float(
            local["close"].iloc[position]
        )

        if close > range_high:
            signal_position = position
            direction = 1
            break

        if close < range_low:
            signal_position = position
            direction = -1
            break

    if (
        signal_position is None
        or direction is None
    ):
        return None

    entry_position = signal_position + 1

    if entry_position >= forced_position:
        return None

    entry_time = local.index[
        entry_position
    ]

    if slots[entry_position] > FINAL_ENTRY_SLOT:
        raise RuntimeError(
            "EXP-005 entry occurred after "
            "slot 30 / 12:00 ET."
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
            local["open"].iloc[position]
        )
        bar_high = float(
            local["high"].iloc[position]
        )
        bar_low = float(
            local["low"].iloc[position]
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
                exit_reason = "range_stop"
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
                exit_reason = "range_stop"
                break

    if exit_position is None:
        exit_position = forced_position
        exit_price = float(
            local["open"].iloc[
                forced_position
            ]
        )
        exit_reason = "forced_flat_1555"

    gross_points = (
        direction
        * (
            float(exit_price)
            - entry_price
        )
    )
    gross_pnl = (
        gross_points
        * contract.multiplier_usd_per_point
    )
    net_pnl = (
        gross_pnl
        - contract.round_trip_cost_usd
    )

    return {
        "symbol": contract.symbol,
        "session_date": str(
            session["session_date"].iloc[0]
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
        "opening_range_high": range_high,
        "opening_range_low": range_low,
        "entry_price": entry_price,
        "exit_price": float(exit_price),
        "gross_points": float(gross_points),
        "gross_pnl_usd": float(gross_pnl),
        "transaction_cost_usd": float(
            contract.round_trip_cost_usd
        ),
        "net_pnl_usd": float(net_pnl),
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


def _yearly_results(
    trades: pd.DataFrame,
) -> pd.DataFrame:
    columns = [
        "year",
        "completed_trades",
        "long_trades",
        "short_trades",
        "net_profit_usd",
        "trade_profit_factor",
        "win_rate_percent",
        "average_trade_usd",
    ]

    if trades.empty:
        return pd.DataFrame(
            columns=columns
        )

    local = trades.copy()
    local["year"] = pd.to_datetime(
        local["session_date"]
    ).dt.year.astype(int)

    rows: list[dict[str, Any]] = []

    for year, group in local.groupby(
        "year",
        sort=True,
    ):
        rows.append(
            {
                "year": int(year),
                "completed_trades": int(
                    len(group)
                ),
                "long_trades": int(
                    group["direction"]
                    .eq("long")
                    .sum()
                ),
                "short_trades": int(
                    group["direction"]
                    .eq("short")
                    .sum()
                ),
                "net_profit_usd": float(
                    group["net_pnl_usd"].sum()
                ),
                "trade_profit_factor": float(
                    _profit_factor(
                        group["net_pnl_usd"]
                    )
                ),
                "win_rate_percent": float(
                    group["net_pnl_usd"]
                    .gt(0)
                    .mean()
                    * 100.0
                ),
                "average_trade_usd": float(
                    group["net_pnl_usd"].mean()
                ),
            }
        )

    return pd.DataFrame(
        rows,
        columns=columns,
    )


def run_futures_orb(
    data: pd.DataFrame,
    *,
    symbol: str,
    slippage_ticks_per_side: float = 1.0,
    validate_data: bool = True,
) -> FuturesOrbResult:
    if validate_data:
        validate_five_minute_data(data)

    contract = get_contract_spec(
        symbol,
        slippage_ticks_per_side=(
            slippage_ticks_per_side
        ),
    )

    trade_rows: list[
        dict[str, Any]
    ] = []
    equity_rows: list[
        dict[str, Any]
    ] = []
    cumulative_pnl = 0.0
    peak_pnl = 0.0

    for session_date, session in data.groupby(
        "session_date",
        sort=True,
    ):
        trade = _simulate_session(
            session,
            contract=contract,
        )
        session_pnl = 0.0

        if trade is not None:
            session_pnl = float(
                trade["net_pnl_usd"]
            )
            cumulative_pnl += session_pnl
            trade["cumulative_net_pnl_usd"] = (
                cumulative_pnl
            )
            trade_rows.append(trade)

        peak_pnl = max(
            peak_pnl,
            cumulative_pnl,
        )

        equity_rows.append(
            {
                "session_date": str(
                    session_date
                ),
                "session_net_pnl_usd": (
                    session_pnl
                ),
                "cumulative_net_pnl_usd": (
                    cumulative_pnl
                ),
                "drawdown_usd": (
                    cumulative_pnl
                    - peak_pnl
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
        gross_profit = 0.0
        gross_loss = 0.0
        profit_factor = float("nan")
        win_rate = 0.0
        average_trade = float("nan")
        median_trade = float("nan")
        long_trades = 0
        short_trades = 0
        gross_pnl = 0.0
        costs = 0.0
    else:
        pnl = trades["net_pnl_usd"].astype(
            float
        )
        gross_profit = float(
            pnl[pnl > 0].sum()
        )
        gross_loss = abs(
            float(
                pnl[pnl < 0].sum()
            )
        )
        profit_factor = _profit_factor(
            pnl
        )
        win_rate = float(
            pnl.gt(0).mean()
            * 100.0
        )
        average_trade = float(
            pnl.mean()
        )
        median_trade = float(
            pnl.median()
        )
        long_trades = int(
            trades["direction"]
            .eq("long")
            .sum()
        )
        short_trades = int(
            trades["direction"]
            .eq("short")
            .sum()
        )
        gross_pnl = float(
            trades[
                "gross_pnl_usd"
            ].sum()
        )
        costs = float(
            trades[
                "transaction_cost_usd"
            ].sum()
        )

    summary = {
        "symbol": contract.symbol,
        "included_sessions": int(
            data["session_date"].nunique()
        ),
        "completed_trades": int(
            len(trades)
        ),
        "long_trades": long_trades,
        "short_trades": short_trades,
        "gross_pnl_usd": gross_pnl,
        "transaction_costs_usd": costs,
        "net_profit_usd": float(
            cumulative_pnl
        ),
        "gross_profit_usd": gross_profit,
        "gross_loss_usd": gross_loss,
        "trade_profit_factor": float(
            profit_factor
        ),
        "win_rate_percent": win_rate,
        "average_trade_usd": average_trade,
        "median_trade_usd": median_trade,
        "maximum_drawdown_usd": (
            float(
                equity_curve[
                    "drawdown_usd"
                ].min()
            )
            if not equity_curve.empty
            else 0.0
        ),
        "slippage_ticks_per_side": float(
            slippage_ticks_per_side
        ),
        "round_trip_cost_usd": float(
            contract.round_trip_cost_usd
        ),
    }

    return FuturesOrbResult(
        symbol=contract.symbol,
        contract=contract,
        summary=summary,
        trades=trades,
        equity_curve=equity_curve,
        yearly_results=_yearly_results(
            trades
        ),
    )


def run_cost_sensitivity(
    data: pd.DataFrame,
    *,
    symbol: str,
    slippage_ticks: tuple[
        float,
        ...,
    ] = (0.0, 1.0, 2.0),
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []

    for ticks in slippage_ticks:
        result = run_futures_orb(
            data,
            symbol=symbol,
            slippage_ticks_per_side=float(
                ticks
            ),
        )

        rows.append(
            {
                "symbol": result.symbol,
                "slippage_ticks_per_side": (
                    float(ticks)
                ),
                "round_trip_cost_usd": (
                    result.contract
                    .round_trip_cost_usd
                ),
                "completed_trades": (
                    result.summary[
                        "completed_trades"
                    ]
                ),
                "net_profit_usd": (
                    result.summary[
                        "net_profit_usd"
                    ]
                ),
                "trade_profit_factor": (
                    result.summary[
                        "trade_profit_factor"
                    ]
                ),
                "maximum_drawdown_usd": (
                    result.summary[
                        "maximum_drawdown_usd"
                    ]
                ),
            }
        )

    return pd.DataFrame(rows)
