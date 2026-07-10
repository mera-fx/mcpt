from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class CostModel:
    """
    Costs charged on each transaction side.

    Example:
    - Enter long: one side
    - Exit long: one side
    - Reverse long to short: two sides
    """

    commission_bps_per_side: float = 0.0
    slippage_bps_per_side: float = 0.0

    @property
    def total_rate_per_side(self) -> float:
        total_bps = (
            self.commission_bps_per_side
            + self.slippage_bps_per_side
        )

        return total_bps / 10_000


@dataclass
class BacktestResult:
    trades: pd.DataFrame
    equity_curve: pd.DataFrame
    summary: dict


def signal_to_target_position(
    signal: pd.Series,
    execution_lag_bars: int = 1,
) -> pd.Series:
    """
    Convert a strategy signal into the position held at each bar open.

    A lag of one means:
    - Signal observed at the current candle close
    - Position entered at the next candle open
    """

    if execution_lag_bars < 0:
        raise ValueError(
            "execution_lag_bars cannot be negative."
        )

    target = signal.astype(float).shift(
        execution_lag_bars
    )

    target = np.sign(
        target.fillna(0)
    ).astype(float)

    target.name = "target_position"

    return target


def _validate_inputs(
    data: pd.DataFrame,
    target_position: pd.Series,
) -> tuple[pd.DataFrame, pd.Series]:
    required_columns = {"open", "close"}
    missing_columns = required_columns.difference(
        data.columns
    )

    if missing_columns:
        raise ValueError(
            f"Missing required columns: "
            f"{sorted(missing_columns)}"
        )

    if data.empty:
        raise ValueError("The input data is empty.")

    clean_data = data.copy()
    clean_data.index = pd.to_datetime(
        clean_data.index
    )
    clean_data = clean_data.sort_index()

    if (
        clean_data[["open", "close"]] <= 0
    ).any().any():
        raise ValueError(
            "Open and close prices must be positive."
        )

    clean_target = (
        target_position
        .reindex(clean_data.index)
        .ffill()
        .fillna(0)
    )

    clean_target = np.sign(
        clean_target
    ).astype(float)

    return clean_data, clean_target


def _build_equity_curve(
    data: pd.DataFrame,
    target_position: pd.Series,
    cost_model: CostModel,
    starting_capital: float,
) -> pd.DataFrame:
    """
    Build mark-to-market equity using open-to-open returns.

    The final position is marked from the last open to the last close.
    """

    curve = pd.DataFrame(
        index=data.index
    )

    curve["open"] = data["open"]
    curve["close"] = data["close"]
    curve["position"] = target_position

    next_execution_price = (
        data["open"].shift(-1)
    )

    next_execution_price.iloc[-1] = (
        data["close"].iloc[-1]
    )

    curve["gross_log_return"] = (
        curve["position"]
        * np.log(
            next_execution_price
            / curve["open"]
        )
    )

    previous_position = (
        curve["position"]
        .shift(1)
        .fillna(0)
    )

    curve["transaction_sides"] = (
        curve["position"]
        - previous_position
    ).abs()

    # Close any remaining position at the end of the data.
    curve.loc[
        curve.index[-1],
        "transaction_sides",
    ] += abs(
        curve["position"].iloc[-1]
    )

    curve["cost_log_return"] = (
        curve["transaction_sides"]
        * cost_model.total_rate_per_side
    )

    curve["net_log_return"] = (
        curve["gross_log_return"]
        - curve["cost_log_return"]
    )

    curve["equity"] = (
        starting_capital
        * np.exp(
            curve["net_log_return"].cumsum()
        )
    )

    curve["drawdown"] = (
        curve["equity"]
        / curve["equity"].cummax()
        - 1
    )

    return curve


def _build_trade_list(
    data: pd.DataFrame,
    target_position: pd.Series,
    cost_model: CostModel,
    starting_capital: float,
) -> pd.DataFrame:
    trades: list[dict] = []

    current_position = 0
    entry_time = None
    entry_price = None
    entry_bar = None

    equity = starting_capital
    trade_number = 0

    cost_rate = cost_model.total_rate_per_side

    def close_trade(
        *,
        exit_time: pd.Timestamp,
        exit_price: float,
        exit_bar: int,
        exit_reason: str,
    ) -> None:
        nonlocal equity
        nonlocal trade_number
        nonlocal current_position
        nonlocal entry_time
        nonlocal entry_price
        nonlocal entry_bar

        if (
            current_position == 0
            or entry_time is None
            or entry_price is None
            or entry_bar is None
        ):
            return

        trade_number += 1

        gross_log_return = (
            current_position
            * np.log(
                exit_price / entry_price
            )
        )

        # Each completed trade has one entry side and one exit side.
        net_log_return = (
            gross_log_return
            - 2 * cost_rate
        )

        gross_return = (
            np.exp(gross_log_return) - 1
        )

        net_return = (
            np.exp(net_log_return) - 1
        )

        equity_before = equity
        pnl_cash = equity_before * net_return
        equity_after = equity_before + pnl_cash

        duration_hours = (
            exit_time - entry_time
        ).total_seconds() / 3600

        bars_held = max(
            1,
            exit_bar - entry_bar,
        )

        trades.append(
            {
                "trade_id": trade_number,
                "side": (
                    "Long"
                    if current_position == 1
                    else "Short"
                ),
                "direction": current_position,
                "entry_time": entry_time,
                "exit_time": exit_time,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "bars_held": bars_held,
                "hours_held": duration_hours,
                "gross_return_percent": (
                    gross_return * 100
                ),
                "net_return_percent": (
                    net_return * 100
                ),
                "commission_bps_round_trip": (
                    2
                    * cost_model.commission_bps_per_side
                ),
                "slippage_bps_round_trip": (
                    2
                    * cost_model.slippage_bps_per_side
                ),
                "equity_before": equity_before,
                "pnl_cash": pnl_cash,
                "equity_after": equity_after,
                "exit_reason": exit_reason,
            }
        )

        equity = equity_after

    for bar_number, timestamp in enumerate(
        data.index
    ):
        desired_position = int(
            target_position.iloc[bar_number]
        )

        if desired_position == current_position:
            continue

        current_open = float(
            data["open"].iloc[bar_number]
        )

        # Close the old position first.
        if current_position != 0:
            close_trade(
                exit_time=timestamp,
                exit_price=current_open,
                exit_bar=bar_number,
                exit_reason="signal_change",
            )

        # Open the new position at the same bar open.
        if desired_position != 0:
            current_position = desired_position
            entry_time = timestamp
            entry_price = current_open
            entry_bar = bar_number
        else:
            current_position = 0
            entry_time = None
            entry_price = None
            entry_bar = None

    # Close a final open position using the last candle close.
    if current_position != 0:
        close_trade(
            exit_time=data.index[-1],
            exit_price=float(
                data["close"].iloc[-1]
            ),
            exit_bar=len(data),
            exit_reason="end_of_data",
        )

    columns = [
        "trade_id",
        "side",
        "direction",
        "entry_time",
        "exit_time",
        "entry_price",
        "exit_price",
        "bars_held",
        "hours_held",
        "gross_return_percent",
        "net_return_percent",
        "commission_bps_round_trip",
        "slippage_bps_round_trip",
        "equity_before",
        "pnl_cash",
        "equity_after",
        "exit_reason",
    ]

    return pd.DataFrame(
        trades,
        columns=columns,
    )


def _calculate_summary(
    trades: pd.DataFrame,
    equity_curve: pd.DataFrame,
    target_position: pd.Series,
    starting_capital: float,
) -> dict:
    if trades.empty:
        return {
            "starting_capital": starting_capital,
            "ending_capital": starting_capital,
            "net_profit": 0.0,
            "total_return_percent": 0.0,
            "max_drawdown_percent": 0.0,
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate_percent": 0.0,
            "trade_profit_factor": np.nan,
            "average_trade_percent": np.nan,
            "average_win_percent": np.nan,
            "average_loss_percent": np.nan,
            "payoff_ratio": np.nan,
            "expectancy_cash": np.nan,
            "average_holding_hours": np.nan,
            "exposure_percent": 0.0,
            "long_trades": 0,
            "short_trades": 0,
            "long_net_profit": 0.0,
            "short_net_profit": 0.0,
        }

    winners = trades[
        trades["pnl_cash"] > 0
    ]

    losers = trades[
        trades["pnl_cash"] < 0
    ]

    gross_profit = winners["pnl_cash"].sum()
    gross_loss = abs(
        losers["pnl_cash"].sum()
    )

    if gross_loss > 0:
        profit_factor = (
            gross_profit / gross_loss
        )
    else:
        profit_factor = float("inf")

    average_win = (
        winners["net_return_percent"].mean()
        if not winners.empty
        else np.nan
    )

    average_loss = (
        losers["net_return_percent"].mean()
        if not losers.empty
        else np.nan
    )

    if (
        pd.notna(average_win)
        and pd.notna(average_loss)
        and average_loss != 0
    ):
        payoff_ratio = (
            average_win / abs(average_loss)
        )
    else:
        payoff_ratio = np.nan

    ending_capital = float(
        equity_curve["equity"].iloc[-1]
    )

    long_trades = trades[
        trades["side"] == "Long"
    ]

    short_trades = trades[
        trades["side"] == "Short"
    ]

    return {
        "starting_capital": starting_capital,
        "ending_capital": ending_capital,
        "net_profit": (
            ending_capital - starting_capital
        ),
        "total_return_percent": (
            ending_capital / starting_capital - 1
        ) * 100,
        "max_drawdown_percent": (
            equity_curve["drawdown"].min()
            * 100
        ),
        "total_trades": len(trades),
        "winning_trades": len(winners),
        "losing_trades": len(losers),
        "win_rate_percent": (
            len(winners) / len(trades) * 100
        ),
        "trade_profit_factor": profit_factor,
        "average_trade_percent": trades[
            "net_return_percent"
        ].mean(),
        "average_win_percent": average_win,
        "average_loss_percent": average_loss,
        "payoff_ratio": payoff_ratio,
        "expectancy_cash": trades[
            "pnl_cash"
        ].mean(),
        "average_holding_hours": trades[
            "hours_held"
        ].mean(),
        "exposure_percent": (
            target_position.abs().gt(0).mean()
            * 100
        ),
        "long_trades": len(long_trades),
        "short_trades": len(short_trades),
        "long_net_profit": long_trades[
            "pnl_cash"
        ].sum(),
        "short_net_profit": short_trades[
            "pnl_cash"
        ].sum(),
    }


def backtest_signal_strategy(
    data: pd.DataFrame,
    target_position: pd.Series,
    *,
    cost_model: CostModel | None = None,
    starting_capital: float = 100_000,
) -> BacktestResult:
    """
    Run a completed-trade backtest from a target-position series.
    """

    if starting_capital <= 0:
        raise ValueError(
            "starting_capital must be positive."
        )

    if cost_model is None:
        cost_model = CostModel()

    clean_data, clean_target = _validate_inputs(
        data,
        target_position,
    )

    equity_curve = _build_equity_curve(
        clean_data,
        clean_target,
        cost_model,
        starting_capital,
    )

    trades = _build_trade_list(
        clean_data,
        clean_target,
        cost_model,
        starting_capital,
    )

    summary = _calculate_summary(
        trades,
        equity_curve,
        clean_target,
        starting_capital,
    )

    return BacktestResult(
        trades=trades,
        equity_curve=equity_curve,
        summary=summary,
    )