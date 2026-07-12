from __future__ import annotations

from dataclasses import dataclass
import hashlib
import html
import json
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class PaperSimulationResult:
    isolated_signal: pd.Series
    target_position: pd.Series
    equity_curve: pd.DataFrame
    completed_trades: pd.DataFrame
    audit_log: pd.DataFrame
    open_position: dict[str, Any] | None
    summary: dict[str, Any]
    reconciliation: dict[str, Any]


def isolate_post_activation_signal(
    raw_signal: pd.Series,
    *,
    activation_cutoff: pd.Timestamp,
) -> pd.Series:
    signal = (
        raw_signal.astype(float)
        .reindex(raw_signal.index)
        .fillna(0.0)
        .clip(lower=0.0, upper=1.0)
    )

    cutoff = pd.Timestamp(
        activation_cutoff
    )

    isolated = pd.Series(
        0.0,
        index=signal.index,
        dtype=float,
        name="paper_signal",
    )

    post_index = signal.index[
        signal.index > cutoff
    ]

    if not len(post_index):
        return isolated

    prior_values = signal.loc[
        signal.index <= cutoff
    ]

    inherited_long = (
        bool(prior_values.iloc[-1] == 1.0)
        if len(prior_values)
        else False
    )

    armed = not inherited_long

    for timestamp in post_index:
        value = float(
            signal.loc[timestamp]
        )

        if not armed:
            isolated.loc[timestamp] = 0.0

            if value == 0.0:
                armed = True

            continue

        isolated.loc[timestamp] = value

    return isolated


def build_next_open_target(
    isolated_signal: pd.Series,
) -> pd.Series:
    target = (
        isolated_signal.shift(1)
        .fillna(0.0)
        .clip(lower=0.0, upper=1.0)
        .astype(float)
    )

    target.name = "target_position"

    return target


def _empty_trade_frame() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "trade_id",
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
    )


def run_paper_simulation(
    *,
    data: pd.DataFrame,
    raw_signal: pd.Series,
    activation_cutoff: pd.Timestamp,
    starting_capital: float,
    commission_bps_per_side: float,
    slippage_bps_per_side: float,
) -> PaperSimulationResult:
    if starting_capital <= 0:
        raise ValueError(
            "starting_capital must be positive."
        )

    clean_data = data.copy()
    clean_data.index = pd.to_datetime(
        clean_data.index
    )
    clean_data = clean_data.sort_index()

    cutoff = pd.Timestamp(
        activation_cutoff
    )

    if cutoff not in clean_data.index:
        raise ValueError(
            "activation_cutoff is not present "
            "in the candle data."
        )

    isolated_signal = (
        isolate_post_activation_signal(
            raw_signal.reindex(
                clean_data.index
            ),
            activation_cutoff=cutoff,
        )
    )

    target = build_next_open_target(
        isolated_signal
    )

    simulation_data = clean_data.loc[
        clean_data.index >= cutoff
    ].copy()

    simulation_target = target.reindex(
        simulation_data.index
    ).fillna(0.0)

    total_cost_rate = (
        float(commission_bps_per_side)
        + float(slippage_bps_per_side)
    ) / 10_000

    curve = pd.DataFrame(
        index=simulation_data.index
    )

    curve["open"] = simulation_data[
        "open"
    ].astype(float)

    curve["close"] = simulation_data[
        "close"
    ].astype(float)

    curve["position"] = (
        simulation_target.astype(float)
    )

    next_execution_price = (
        curve["open"].shift(-1)
    )

    next_execution_price.iloc[-1] = (
        curve["close"].iloc[-1]
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
        .fillna(0.0)
    )

    curve["transaction_sides"] = (
        curve["position"]
        - previous_position
    ).abs()

    curve["cost_log_return"] = (
        curve["transaction_sides"]
        * total_cost_rate
    )

    curve["net_log_return"] = (
        curve["gross_log_return"]
        - curve["cost_log_return"]
    )

    curve["equity"] = (
        starting_capital
        * np.exp(
            curve[
                "net_log_return"
            ].cumsum()
        )
    )

    curve["drawdown"] = (
        curve["equity"]
        / curve["equity"].cummax()
        - 1.0
    )

    trades: list[dict[str, Any]] = []
    audit_events: list[dict[str, Any]] = []

    current_position = 0
    entry_time: pd.Timestamp | None = None
    entry_price: float | None = None
    entry_bar: int | None = None
    trade_equity = float(
        starting_capital
    )
    trade_id = 0

    for bar_number, timestamp in enumerate(
        simulation_data.index
    ):
        desired = int(
            simulation_target.iloc[
                bar_number
            ]
        )

        if desired == current_position:
            continue

        fill_price = float(
            simulation_data[
                "open"
            ].iloc[bar_number]
        )

        audit_events.append(
            {
                "timestamp": timestamp,
                "event_type": "SIMULATED_FILL",
                "from_position": current_position,
                "to_position": desired,
                "price": fill_price,
                "transaction_sides": abs(
                    desired - current_position
                ),
                "note": (
                    "Paper-only next-open execution"
                ),
            }
        )

        if (
            current_position == 1
            and entry_time is not None
            and entry_price is not None
            and entry_bar is not None
        ):
            trade_id += 1

            gross_log_return = np.log(
                fill_price / entry_price
            )

            net_log_return = (
                gross_log_return
                - 2.0 * total_cost_rate
            )

            gross_return = (
                np.exp(
                    gross_log_return
                ) - 1.0
            )

            net_return = (
                np.exp(
                    net_log_return
                ) - 1.0
            )

            equity_before = trade_equity
            pnl_cash = (
                equity_before * net_return
            )
            equity_after = (
                equity_before + pnl_cash
            )

            trades.append(
                {
                    "trade_id": trade_id,
                    "entry_time": entry_time,
                    "exit_time": timestamp,
                    "entry_price": entry_price,
                    "exit_price": fill_price,
                    "bars_held": max(
                        1,
                        bar_number - entry_bar,
                    ),
                    "hours_held": (
                        timestamp - entry_time
                    ).total_seconds() / 3600,
                    "gross_return_percent": (
                        gross_return * 100
                    ),
                    "net_return_percent": (
                        net_return * 100
                    ),
                    "commission_bps_round_trip": (
                        2
                        * commission_bps_per_side
                    ),
                    "slippage_bps_round_trip": (
                        2
                        * slippage_bps_per_side
                    ),
                    "equity_before": (
                        equity_before
                    ),
                    "pnl_cash": pnl_cash,
                    "equity_after": (
                        equity_after
                    ),
                    "exit_reason": (
                        "signal_change"
                    ),
                }
            )

            trade_equity = equity_after

        if desired == 1:
            entry_time = timestamp
            entry_price = fill_price
            entry_bar = bar_number
        else:
            entry_time = None
            entry_price = None
            entry_bar = None

        current_position = desired

    completed_trades = (
        pd.DataFrame(trades)
        if trades
        else _empty_trade_frame()
    )

    open_position: (
        dict[str, Any] | None
    ) = None

    if (
        current_position == 1
        and entry_time is not None
        and entry_price is not None
        and entry_bar is not None
    ):
        mark_price = float(
            simulation_data[
                "close"
            ].iloc[-1]
        )

        gross_log_return = np.log(
            mark_price / entry_price
        )

        current_net_log_return = (
            gross_log_return
            - total_cost_rate
        )

        estimated_round_trip_log_return = (
            gross_log_return
            - 2.0 * total_cost_rate
        )

        open_position = {
            "side": "Long",
            "entry_time": (
                entry_time.isoformat()
            ),
            "entry_price": entry_price,
            "mark_time": (
                simulation_data.index[-1]
                .isoformat()
            ),
            "mark_price": mark_price,
            "bars_held": max(
                1,
                len(simulation_data)
                - entry_bar,
            ),
            "gross_return_percent": (
                (
                    np.exp(
                        gross_log_return
                    ) - 1.0
                )
                * 100
            ),
            "current_net_return_percent": (
                (
                    np.exp(
                        current_net_log_return
                    ) - 1.0
                )
                * 100
            ),
            "estimated_after_exit_cost_percent": (
                (
                    np.exp(
                        estimated_round_trip_log_return
                    ) - 1.0
                )
                * 100
            ),
        }

    signal_changes = (
        isolated_signal
        .loc[
            isolated_signal.index
            >= cutoff
        ]
        .diff()
        .fillna(0.0)
        .ne(0.0)
    )

    for timestamp in signal_changes[
        signal_changes
    ].index:
        audit_events.append(
            {
                "timestamp": (
                    timestamp
                    + pd.Timedelta(hours=1)
                ),
                "event_type": (
                    "SIGNAL_AT_CANDLE_CLOSE"
                ),
                "from_position": None,
                "to_position": int(
                    isolated_signal.loc[
                        timestamp
                    ]
                ),
                "price": float(
                    clean_data.loc[
                        timestamp,
                        "close",
                    ]
                ),
                "transaction_sides": 0,
                "note": (
                    "Signal observed only after "
                    "the hourly candle closed"
                ),
            }
        )

    audit_log = pd.DataFrame(
        audit_events,
        columns=[
            "timestamp",
            "event_type",
            "from_position",
            "to_position",
            "price",
            "transaction_sides",
            "note",
        ],
    )

    if not audit_log.empty:
        audit_log = audit_log.sort_values(
            ["timestamp", "event_type"]
        ).reset_index(drop=True)

    position_values_valid = bool(
        simulation_target.isin(
            [0.0, 1.0]
        ).all()
    )

    duplicate_fill_count = 0

    if not audit_log.empty:
        fill_events = audit_log[
            audit_log["event_type"]
            == "SIMULATED_FILL"
        ]

        duplicate_fill_count = int(
            fill_events.duplicated(
                subset=[
                    "timestamp",
                    "to_position",
                ]
            ).sum()
        )

    reconciliation_errors: list[str] = []

    if not position_values_valid:
        reconciliation_errors.append(
            "Position values outside long/flat."
        )

    if duplicate_fill_count:
        reconciliation_errors.append(
            "Duplicate simulated fills detected."
        )

    if not np.isfinite(
        curve["equity"].to_numpy()
    ).all():
        reconciliation_errors.append(
            "Non-finite equity values detected."
        )

    expected_fill_sides = int(
        curve["transaction_sides"].sum()
    )

    actual_fill_sides = int(
        audit_log.loc[
            audit_log["event_type"]
            == "SIMULATED_FILL",
            "transaction_sides",
        ].sum()
        if not audit_log.empty
        else 0
    )

    if (
        expected_fill_sides
        != actual_fill_sides
    ):
        reconciliation_errors.append(
            "Fill-side count does not match "
            "the equity curve."
        )

    if reconciliation_errors:
        raise RuntimeError(
            "Paper simulation reconciliation failed:\n- "
            + "\n- ".join(
                reconciliation_errors
            )
        )

    winners = (
        completed_trades[
            completed_trades[
                "pnl_cash"
            ] > 0
        ]
        if not completed_trades.empty
        else completed_trades
    )

    losers = (
        completed_trades[
            completed_trades[
                "pnl_cash"
            ] < 0
        ]
        if not completed_trades.empty
        else completed_trades
    )

    gross_profit = (
        float(
            winners["pnl_cash"].sum()
        )
        if not winners.empty
        else 0.0
    )

    gross_loss = (
        abs(
            float(
                losers["pnl_cash"].sum()
            )
        )
        if not losers.empty
        else 0.0
    )

    trade_pf = (
        gross_profit / gross_loss
        if gross_loss > 0
        else (
            float("inf")
            if gross_profit > 0
            else float("nan")
        )
    )

    ending_equity = float(
        curve["equity"].iloc[-1]
    )

    summary = {
        "activation_cutoff": (
            cutoff.isoformat()
        ),
        "latest_closed_candle": (
            simulation_data.index[-1]
            .isoformat()
        ),
        "starting_capital": (
            float(starting_capital)
        ),
        "mark_to_market_equity": (
            ending_equity
        ),
        "total_return_percent": (
            (
                ending_equity
                / starting_capital
                - 1.0
            )
            * 100
        ),
        "max_drawdown_percent": (
            float(
                curve["drawdown"].min()
                * 100
            )
        ),
        "completed_trades": int(
            len(completed_trades)
        ),
        "winning_trades": int(
            len(winners)
        ),
        "losing_trades": int(
            len(losers)
        ),
        "trade_profit_factor": (
            float(trade_pf)
        ),
        "current_position": int(
            current_position
        ),
        "latest_strategy_signal": int(
            isolated_signal.iloc[-1]
        ),
        "pending_next_open_target": int(
            isolated_signal.iloc[-1]
        ),
        "exposure_percent": float(
            simulation_target.mean()
            * 100
        ),
    }

    reconciliation = {
        "passed": True,
        "unresolved_errors": 0,
        "duplicate_fills": (
            duplicate_fill_count
        ),
        "position_values_valid": (
            position_values_valid
        ),
        "expected_fill_sides": (
            expected_fill_sides
        ),
        "actual_fill_sides": (
            actual_fill_sides
        ),
    }

    return PaperSimulationResult(
        isolated_signal=(
            isolated_signal
        ),
        target_position=target,
        equity_curve=curve,
        completed_trades=(
            completed_trades
        ),
        audit_log=audit_log,
        open_position=open_position,
        summary=summary,
        reconciliation=reconciliation,
    )


def candle_fingerprints(
    data: pd.DataFrame,
) -> pd.DataFrame:
    records: list[dict[str, str]] = []

    for timestamp, row in data.iterrows():
        canonical = "|".join(
            [
                timestamp.isoformat(),
                f"{float(row['open']):.12f}",
                f"{float(row['high']):.12f}",
                f"{float(row['low']):.12f}",
                f"{float(row['close']):.12f}",
                (
                    f"{float(row['volume']):.12f}"
                    if "volume" in row.index
                    else ""
                ),
            ]
        )

        digest = hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()

        records.append(
            {
                "timestamp": (
                    timestamp.isoformat()
                ),
                "sha256": digest,
            }
        )

    return pd.DataFrame(records)


def validate_fingerprint_history(
    *,
    previous: pd.DataFrame,
    current: pd.DataFrame,
) -> None:
    if previous.empty:
        return

    previous_map = previous.set_index(
        "timestamp"
    )["sha256"]

    current_map = current.set_index(
        "timestamp"
    )["sha256"]

    missing = previous_map.index.difference(
        current_map.index
    )

    if len(missing):
        raise RuntimeError(
            "Previously observed candles disappeared "
            f"from paper data: {missing[0]}"
        )

    changed = previous_map[
        previous_map
        != current_map.reindex(
            previous_map.index
        )
    ]

    if len(changed):
        raise RuntimeError(
            "A previously observed closed candle changed: "
            f"{changed.index[0]}"
        )


def write_paper_report(
    *,
    result: PaperSimulationResult,
    activation: dict[str, Any],
    report_directory: Path,
    observation_weeks: float,
    required_weeks: int,
    required_trades: int,
) -> Path:
    report_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    equity_image = (
        report_directory
        / "paper_equity.png"
    )

    drawdown_image = (
        report_directory
        / "paper_drawdown.png"
    )

    plt.figure(figsize=(11, 5))
    plt.plot(
        result.equity_curve.index,
        result.equity_curve["equity"],
        linewidth=1.8,
    )
    plt.title(
        "EXP-003 Paper Mark-to-Market Equity"
    )
    plt.xlabel("UTC")
    plt.ylabel("Equity")
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(
        equity_image,
        dpi=150,
    )
    plt.close()

    plt.figure(figsize=(11, 4))
    plt.plot(
        result.equity_curve.index,
        result.equity_curve[
            "drawdown"
        ] * 100,
        linewidth=1.8,
    )
    plt.axhline(0, linewidth=1)
    plt.title(
        "EXP-003 Paper Drawdown"
    )
    plt.xlabel("UTC")
    plt.ylabel("Drawdown (%)")
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(
        drawdown_image,
        dpi=150,
    )
    plt.close()

    summary = result.summary

    weeks_pass = (
        observation_weeks
        >= required_weeks
    )

    trades_pass = (
        summary["completed_trades"]
        >= required_trades
    )

    latest_events = (
        result.audit_log.tail(20)
        .to_html(
            index=False,
            border=0,
        )
        if not result.audit_log.empty
        else "<p>No signal or fill events yet.</p>"
    )

    latest_trades = (
        result.completed_trades.tail(15)
        .to_html(
            index=False,
            border=0,
            float_format=lambda value: (
                f"{value:,.4f}"
            ),
        )
        if not result.completed_trades.empty
        else "<p>No completed paper trades yet.</p>"
    )

    open_position_text = (
        "<p>Flat.</p>"
        if result.open_position is None
        else (
            "<pre>"
            + html.escape(
                json.dumps(
                    result.open_position,
                    indent=2,
                )
            )
            + "</pre>"
        )
    )

    report = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>EXP-003 Paper Status</title>
<style>
body {{
    font-family: Arial, sans-serif;
    max-width: 1180px;
    margin: 32px auto;
    padding: 0 20px;
    background: #f5f6f8;
    color: #20242a;
}}
h1, h2 {{ margin-top: 30px; }}
.cards {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
    gap: 14px;
}}
.card {{
    background: white;
    border-radius: 10px;
    padding: 16px;
    box-shadow: 0 1px 4px rgba(0,0,0,.08);
}}
.label {{
    color: #616975;
    font-size: 13px;
}}
.value {{
    font-size: 24px;
    font-weight: 700;
    margin-top: 7px;
}}
.panel {{
    background: white;
    border-radius: 10px;
    padding: 18px;
    margin-top: 18px;
    box-shadow: 0 1px 4px rgba(0,0,0,.08);
    overflow-x: auto;
}}
img {{ max-width: 100%; }}
table {{
    border-collapse: collapse;
    width: 100%;
    font-size: 13px;
}}
th, td {{
    border-bottom: 1px solid #e6e8eb;
    padding: 8px;
    text-align: right;
}}
th:first-child, td:first-child {{
    text-align: left;
}}
</style>
</head>
<body>
<h1>EXP-003 Paper-Testing Status</h1>
<p>
Paper only. No exchange keys and no live orders.
All timestamps are UTC.
</p>

<div class="cards">
<div class="card">
<div class="label">Observation weeks</div>
<div class="value">{observation_weeks:.2f} / {required_weeks}</div>
</div>
<div class="card">
<div class="label">Completed trades</div>
<div class="value">{summary['completed_trades']} / {required_trades}</div>
</div>
<div class="card">
<div class="label">Mark-to-market return</div>
<div class="value">{summary['total_return_percent']:.2f}%</div>
</div>
<div class="card">
<div class="label">Max drawdown</div>
<div class="value">{summary['max_drawdown_percent']:.2f}%</div>
</div>
<div class="card">
<div class="label">Current position</div>
<div class="value">{'Long' if summary['current_position'] == 1 else 'Flat'}</div>
</div>
<div class="card">
<div class="label">Reconciliation</div>
<div class="value">{'PASS' if result.reconciliation['passed'] else 'FAIL'}</div>
</div>
</div>

<div class="panel">
<h2>Minimum-observation progress</h2>
<p>
Weeks requirement: <strong>{'PASS' if weeks_pass else 'IN PROGRESS'}</strong><br>
Trades requirement: <strong>{'PASS' if trades_pass else 'IN PROGRESS'}</strong><br>
Both conditions must pass.
</p>
<p>
Activation cutoff: {html.escape(str(activation['activation_cutoff']))}<br>
Latest closed candle: {html.escape(str(summary['latest_closed_candle']))}
</p>
</div>

<div class="panel">
<img src="paper_equity.png" alt="Paper equity">
</div>

<div class="panel">
<img src="paper_drawdown.png" alt="Paper drawdown">
</div>

<div class="panel">
<h2>Open paper position</h2>
{open_position_text}
</div>

<div class="panel">
<h2>Recent completed trades</h2>
{latest_trades}
</div>

<div class="panel">
<h2>Recent audit events</h2>
{latest_events}
</div>
</body>
</html>
"""

    report_file = (
        report_directory
        / "index.html"
    )

    report_file.write_text(
        report,
        encoding="utf-8",
    )

    return report_file
