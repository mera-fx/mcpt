from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from donchian import (
    donchian_breakout,
    walkforward_donch,
)

from trade_engine import (
    CostModel,
    backtest_signal_strategy,
    signal_to_target_position,
)


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent
DATA_FILE = (
    PROJECT_DIR
    / "data"
    / "BTCUSDT_1h.parquet"
)

RESULTS_DIR = PROJECT_DIR / "results"
REPORT_DIR = (
    PROJECT_DIR
    / "reports"
    / "EXP-001-trades"
)

START_YEAR = 2018
END_YEAR = 2026  # Exclusive

FIXED_LOOKBACK = 49

TRAIN_WINDOW = 24 * 365 * 4
RETRAIN_EVERY_BARS = 24 * 30

STARTING_CAPITAL = 100_000

# These are illustrative assumptions, not claims about
# the exact costs at any particular exchange or broker.
COST_MODEL = CostModel(
    commission_bps_per_side=5.0,
    slippage_bps_per_side=2.0,
)


# ============================================================
# LOAD DATA
# ============================================================

if not DATA_FILE.exists():
    raise FileNotFoundError(
        f"Data file not found: {DATA_FILE}"
    )

df = pd.read_parquet(DATA_FILE)
df.index = pd.to_datetime(df.index)
df = df.sort_index()

df = df[
    (df.index.year >= START_YEAR)
    & (df.index.year < END_YEAR)
].copy()

if len(df) <= TRAIN_WINDOW:
    raise RuntimeError(
        "Not enough data for the training window."
    )


# ============================================================
# BUILD SIGNALS
# ============================================================

fixed_signal = donchian_breakout(
    df,
    FIXED_LOOKBACK,
)

walkforward_signal = pd.Series(
    walkforward_donch(
        df,
        train_lookback=TRAIN_WINDOW,
        train_step=RETRAIN_EVERY_BARS,
    ),
    index=df.index,
    name="walkforward_signal",
)

fixed_target = signal_to_target_position(
    fixed_signal,
    execution_lag_bars=1,
)

walkforward_target = signal_to_target_position(
    walkforward_signal,
    execution_lag_bars=1,
)

buy_hold_target = pd.Series(
    1.0,
    index=df.index,
    name="buy_hold_target",
)


# ============================================================
# SAME OUT-OF-SAMPLE PERIOD FOR EVERY METHOD
# ============================================================

oos_data = df.iloc[
    TRAIN_WINDOW:
].copy()

fixed_target = fixed_target.iloc[
    TRAIN_WINDOW:
]

walkforward_target = walkforward_target.iloc[
    TRAIN_WINDOW:
]

buy_hold_target = buy_hold_target.iloc[
    TRAIN_WINDOW:
]


# ============================================================
# RUN COMPLETED-TRADE BACKTESTS
# ============================================================

print()
print("Running completed-trade backtests...")
print()

fixed_result = backtest_signal_strategy(
    oos_data,
    fixed_target,
    cost_model=COST_MODEL,
    starting_capital=STARTING_CAPITAL,
)

walkforward_result = backtest_signal_strategy(
    oos_data,
    walkforward_target,
    cost_model=COST_MODEL,
    starting_capital=STARTING_CAPITAL,
)

buy_hold_result = backtest_signal_strategy(
    oos_data,
    buy_hold_target,
    cost_model=COST_MODEL,
    starting_capital=STARTING_CAPITAL,
)


# ============================================================
# SUMMARY TABLE
# ============================================================

summary = pd.DataFrame(
    [
        {
            "strategy": "Fixed Donchian 49",
            **fixed_result.summary,
        },
        {
            "strategy": "Walk-Forward Donchian",
            **walkforward_result.summary,
        },
        {
            "strategy": "Buy and Hold",
            **buy_hold_result.summary,
        },
    ]
)

summary = summary.set_index("strategy")

RESULTS_DIR.mkdir(exist_ok=True)
REPORT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

summary_file = (
    RESULTS_DIR
    / "EXP-001_trade_summary.csv"
)

summary.to_csv(summary_file)

fixed_result.trades.to_csv(
    RESULTS_DIR
    / "EXP-001_fixed_trades.csv",
    index=False,
)

walkforward_result.trades.to_csv(
    RESULTS_DIR
    / "EXP-001_walkforward_trades.csv",
    index=False,
)

buy_hold_result.trades.to_csv(
    RESULTS_DIR
    / "EXP-001_buy_hold_trades.csv",
    index=False,
)


# ============================================================
# VISUALS
# ============================================================

plt.style.use("dark_background")


def save_chart(
    filename: str,
) -> None:
    plt.tight_layout()
    plt.savefig(
        REPORT_DIR / filename,
        dpi=140,
        bbox_inches="tight",
    )
    plt.close()


plt.figure(figsize=(14, 7))

plt.plot(
    fixed_result.equity_curve.index,
    fixed_result.equity_curve["equity"],
    label="Fixed Donchian 49",
)

plt.plot(
    walkforward_result.equity_curve.index,
    walkforward_result.equity_curve["equity"],
    label="Walk-Forward Donchian",
)

plt.plot(
    buy_hold_result.equity_curve.index,
    buy_hold_result.equity_curve["equity"],
    label="Buy and Hold",
)

plt.title(
    "EXP-001 — Costed Trade-Level Equity"
)

plt.xlabel("Date")
plt.ylabel("Account Equity")
plt.grid(alpha=0.2)
plt.legend()

save_chart(
    "01_trade_equity.png"
)


plt.figure(figsize=(14, 7))

plt.plot(
    fixed_result.equity_curve.index,
    fixed_result.equity_curve["drawdown"] * 100,
    label="Fixed Donchian 49",
)

plt.plot(
    walkforward_result.equity_curve.index,
    (
        walkforward_result
        .equity_curve["drawdown"]
        * 100
    ),
    label="Walk-Forward Donchian",
)

plt.plot(
    buy_hold_result.equity_curve.index,
    buy_hold_result.equity_curve["drawdown"] * 100,
    label="Buy and Hold",
)

plt.title(
    "EXP-001 — Costed Drawdown"
)

plt.xlabel("Date")
plt.ylabel("Drawdown (%)")
plt.grid(alpha=0.2)
plt.legend()

save_chart(
    "02_trade_drawdown.png"
)


plt.figure(figsize=(14, 7))

plt.hist(
    fixed_result.trades[
        "net_return_percent"
    ],
    bins=40,
    alpha=0.6,
    label="Fixed Donchian 49",
)

plt.hist(
    walkforward_result.trades[
        "net_return_percent"
    ],
    bins=40,
    alpha=0.6,
    label="Walk-Forward Donchian",
)

plt.axvline(
    0,
    linewidth=1,
)

plt.title(
    "EXP-001 — Distribution of Completed-Trade Returns"
)

plt.xlabel("Net Trade Return (%)")
plt.ylabel("Completed Trades")
plt.grid(alpha=0.2)
plt.legend()

save_chart(
    "03_trade_return_distribution.png"
)


# ============================================================
# HTML REPORT
# ============================================================

display_columns = [
    "ending_capital",
    "total_return_percent",
    "max_drawdown_percent",
    "total_trades",
    "win_rate_percent",
    "trade_profit_factor",
    "average_trade_percent",
    "average_holding_hours",
    "exposure_percent",
    "long_trades",
    "short_trades",
    "long_net_profit",
    "short_net_profit",
]

display_summary = summary[
    display_columns
].copy()

display_summary = display_summary.round(2)

summary_html = display_summary.to_html(
    classes="metrics",
    border=0,
)

report_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>EXP-001 Trade Report</title>

<style>
body {{
    background: #090909;
    color: #eeeeee;
    font-family: Arial, sans-serif;
    margin: 0;
}}

.page {{
    max-width: 1450px;
    margin: auto;
    padding: 35px;
}}

h1 {{
    font-size: 38px;
    margin-bottom: 5px;
}}

.subtitle {{
    color: #aaaaaa;
    margin-bottom: 25px;
}}

.warning {{
    background: #241d0c;
    border-left: 5px solid #ffb000;
    padding: 18px;
    margin: 25px 0;
}}

.decision {{
    background: #1c1010;
    border-left: 6px solid #ff4d4d;
    padding: 20px;
    margin: 25px 0;
}}

.chart {{
    width: 100%;
    border: 1px solid #333333;
    border-radius: 8px;
    margin: 15px 0 35px;
}}

.metrics {{
    width: 100%;
    border-collapse: collapse;
    background: #151515;
}}

.metrics th,
.metrics td {{
    border: 1px solid #333333;
    padding: 11px;
    text-align: center;
}}

.metrics th {{
    background: #222222;
}}
</style>
</head>

<body>
<div class="page">

<h1>EXP-001 — Completed-Trade Report</h1>

<div class="subtitle">
BTCUSDT hourly data · Out-of-sample period
{oos_data.index.min()} through {oos_data.index.max()}
</div>

<div class="decision">
<strong>Decision: Rejected</strong>

<p>
The Donchian variants failed on unseen data.
This report uses completed trades, next-open execution
and explicit cost assumptions.
</p>
</div>

<div class="warning">
Cost scenario: {COST_MODEL.commission_bps_per_side:.1f}
bps commission plus
{COST_MODEL.slippage_bps_per_side:.1f}
bps slippage per transaction side.
These are illustrative assumptions and should later be
replaced with costs for the intended venue and instrument.
</div>

<h2>Completed-Trade Metrics</h2>

{summary_html}

<h2>Equity</h2>
<img
    class="chart"
    src="01_trade_equity.png"
    alt="Trade equity chart"
>

<h2>Drawdown</h2>
<img
    class="chart"
    src="02_trade_drawdown.png"
    alt="Trade drawdown chart"
>

<h2>Trade Return Distribution</h2>
<img
    class="chart"
    src="03_trade_return_distribution.png"
    alt="Trade return distribution"
>

<h2>Files</h2>

<p>
The detailed completed-trade ledgers are stored in the
<code>results</code> folder. Each row represents one
entry-to-exit trade.
</p>

</div>
</body>
</html>
"""

report_file = (
    REPORT_DIR / "report.html"
)

report_file.write_text(
    report_html,
    encoding="utf-8",
)


# ============================================================
# TERMINAL OUTPUT
# ============================================================

print(
    summary[
        [
            "total_return_percent",
            "max_drawdown_percent",
            "total_trades",
            "win_rate_percent",
            "trade_profit_factor",
            "average_trade_percent",
            "long_net_profit",
            "short_net_profit",
        ]
    ]
    .round(3)
    .to_string()
)

print()
print(f"Summary: {summary_file}")
print(f"Report:  {report_file}")