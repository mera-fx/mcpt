from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from donchian import donchian_breakout, walkforward_donch
from trade_engine import (
    CostModel,
    backtest_signal_strategy,
    signal_to_target_position,
)


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent
DATA_FILE = PROJECT_DIR / "data" / "BTCUSDT_1h.parquet"

RESULTS_DIR = PROJECT_DIR / "results"
REPORT_DIR = PROJECT_DIR / "reports" / "EXP-001-robustness"

START_YEAR = 2018
END_YEAR = 2026  # Exclusive

FIXED_LOOKBACK = 49
TRAIN_WINDOW = 24 * 365 * 4
RETRAIN_EVERY_BARS = 24 * 30

STARTING_CAPITAL = 100_000

# The completed-trade report used 5 bps commission plus 2 bps
# slippage per side, for 7 total basis points per side.
BASE_TOTAL_COST_BPS_PER_SIDE = 7.0

# Total transaction cost per side used for the sensitivity test.
COST_LEVELS_BPS_PER_SIDE = [0, 1, 2, 3, 5, 7, 10, 15, 20]

ROLLING_TRADE_WINDOW = 50


# ============================================================
# HELPERS
# ============================================================

def make_cost_model(total_bps_per_side: float) -> CostModel:
    """Represent the cost sweep as one total cost per transaction side."""
    return CostModel(
        commission_bps_per_side=float(total_bps_per_side),
        slippage_bps_per_side=0.0,
    )


def profit_factor_from_pnl(pnl: pd.Series) -> float:
    pnl = pnl.dropna()

    gains = pnl[pnl > 0].sum()
    losses = abs(pnl[pnl < 0].sum())

    if losses == 0:
        return float("inf") if gains > 0 else np.nan

    return float(gains / losses)


def rolling_trade_profit_factor(
    trades: pd.DataFrame,
    window: int,
) -> pd.Series:
    if trades.empty:
        return pd.Series(dtype=float)

    working = trades.copy()
    working["exit_time"] = pd.to_datetime(working["exit_time"])
    working = working.sort_values("exit_time")

    pnl = working["pnl_cash"].astype(float)

    rolling_gains = (
        pnl.clip(lower=0)
        .rolling(window=window, min_periods=window)
        .sum()
    )

    rolling_losses = (
        (-pnl.clip(upper=0))
        .rolling(window=window, min_periods=window)
        .sum()
    )

    rolling_pf = rolling_gains / rolling_losses.replace(0, np.nan)
    rolling_pf.index = working["exit_time"]

    return rolling_pf


def break_even_description(cost_table: pd.DataFrame, strategy: str) -> str:
    rows = (
        cost_table[cost_table["strategy"] == strategy]
        .sort_values("cost_bps_per_side")
        .copy()
    )

    zero_cost_return = float(
        rows.loc[
            rows["cost_bps_per_side"] == 0,
            "total_return_percent",
        ].iloc[0]
    )

    if zero_cost_return <= 0:
        return "Already unprofitable before transaction costs."

    non_positive = rows[rows["total_return_percent"] <= 0]

    if non_positive.empty:
        return (
            f"Still profitable at the highest tested cost "
            f"({rows['cost_bps_per_side'].max():.1f} bps per side)."
        )

    first_bad = non_positive.iloc[0]
    previous = rows[
        rows["cost_bps_per_side"] < first_bad["cost_bps_per_side"]
    ].iloc[-1]

    x1 = float(previous["cost_bps_per_side"])
    y1 = float(previous["total_return_percent"])
    x2 = float(first_bad["cost_bps_per_side"])
    y2 = float(first_bad["total_return_percent"])

    if y2 == y1:
        estimated = x2
    else:
        estimated = x1 + (0 - y1) * (x2 - x1) / (y2 - y1)

    return f"Estimated break-even cost: about {estimated:.2f} bps per side."


def yearly_metrics(strategy_name: str, result) -> pd.DataFrame:
    curve = result.equity_curve.copy()
    trades = result.trades.copy()

    if not trades.empty:
        trades["exit_time"] = pd.to_datetime(trades["exit_time"])

    rows: list[dict] = []

    for year, year_curve in curve.groupby(curve.index.year):
        year_log_return = year_curve["net_log_return"].sum()
        year_return = (np.exp(year_log_return) - 1) * 100

        local_equity = np.exp(
            year_curve["net_log_return"].fillna(0).cumsum()
        )
        local_drawdown = local_equity / local_equity.cummax() - 1

        if trades.empty:
            year_trades = trades
        else:
            year_trades = trades[
                trades["exit_time"].dt.year == year
            ]

        pnl = (
            year_trades["pnl_cash"]
            if not year_trades.empty
            else pd.Series(dtype=float)
        )

        rows.append(
            {
                "strategy": strategy_name,
                "year": int(year),
                "return_percent": float(year_return),
                "within_year_max_drawdown_percent": float(
                    local_drawdown.min() * 100
                ),
                "trades": int(len(year_trades)),
                "win_rate_percent": (
                    float((pnl > 0).mean() * 100)
                    if len(pnl) > 0
                    else np.nan
                ),
                "trade_profit_factor": profit_factor_from_pnl(pnl),
            }
        )

    return pd.DataFrame(rows)


def save_current_figure(filename: str) -> None:
    output_path = REPORT_DIR / filename
    plt.tight_layout()
    plt.savefig(output_path, dpi=140, bbox_inches="tight")
    plt.close()


# ============================================================
# LOAD DATA AND CREATE SIGNALS
# ============================================================

if not DATA_FILE.exists():
    raise FileNotFoundError(f"Data file not found: {DATA_FILE}")

df = pd.read_parquet(DATA_FILE)
df.index = pd.to_datetime(df.index)
df = df.sort_index()

df = df[
    (df.index.year >= START_YEAR)
    & (df.index.year < END_YEAR)
].copy()

if len(df) <= TRAIN_WINDOW:
    raise RuntimeError("Not enough data for the selected training window.")

fixed_signal = donchian_breakout(df, FIXED_LOOKBACK)

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

oos_data = df.iloc[TRAIN_WINDOW:].copy()
fixed_target = fixed_target.iloc[TRAIN_WINDOW:].copy()
walkforward_target = walkforward_target.iloc[TRAIN_WINDOW:].copy()

fixed_long_target = fixed_target.where(fixed_target > 0, 0)
fixed_short_target = fixed_target.where(fixed_target < 0, 0)

walkforward_long_target = walkforward_target.where(
    walkforward_target > 0,
    0,
)
walkforward_short_target = walkforward_target.where(
    walkforward_target < 0,
    0,
)


# ============================================================
# BASE BACKTESTS
# ============================================================

RESULTS_DIR.mkdir(exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

base_cost_model = make_cost_model(BASE_TOTAL_COST_BPS_PER_SIDE)

print()
print("Running robustness analysis...")
print()

fixed_full = backtest_signal_strategy(
    oos_data,
    fixed_target,
    cost_model=base_cost_model,
    starting_capital=STARTING_CAPITAL,
)

fixed_long = backtest_signal_strategy(
    oos_data,
    fixed_long_target,
    cost_model=base_cost_model,
    starting_capital=STARTING_CAPITAL,
)

fixed_short = backtest_signal_strategy(
    oos_data,
    fixed_short_target,
    cost_model=base_cost_model,
    starting_capital=STARTING_CAPITAL,
)

walkforward_full = backtest_signal_strategy(
    oos_data,
    walkforward_target,
    cost_model=base_cost_model,
    starting_capital=STARTING_CAPITAL,
)

walkforward_long = backtest_signal_strategy(
    oos_data,
    walkforward_long_target,
    cost_model=base_cost_model,
    starting_capital=STARTING_CAPITAL,
)

walkforward_short = backtest_signal_strategy(
    oos_data,
    walkforward_short_target,
    cost_model=base_cost_model,
    starting_capital=STARTING_CAPITAL,
)


# ============================================================
# COST SENSITIVITY
# ============================================================

cost_rows: list[dict] = []

for cost_bps in COST_LEVELS_BPS_PER_SIDE:
    model = make_cost_model(cost_bps)

    for strategy_name, target in [
        ("Fixed Donchian 49", fixed_target),
        ("Walk-Forward Donchian", walkforward_target),
    ]:
        result = backtest_signal_strategy(
            oos_data,
            target,
            cost_model=model,
            starting_capital=STARTING_CAPITAL,
        )

        cost_rows.append(
            {
                "strategy": strategy_name,
                "cost_bps_per_side": float(cost_bps),
                "round_trip_cost_bps": float(cost_bps * 2),
                "total_return_percent": float(
                    result.summary["total_return_percent"]
                ),
                "ending_capital": float(
                    result.summary["ending_capital"]
                ),
                "trade_profit_factor": float(
                    result.summary["trade_profit_factor"]
                ),
                "max_drawdown_percent": float(
                    result.summary["max_drawdown_percent"]
                ),
            }
        )

cost_table = pd.DataFrame(cost_rows)
cost_table.to_csv(
    RESULTS_DIR / "EXP-001_cost_sensitivity.csv",
    index=False,
)


# ============================================================
# LONG / SHORT SUMMARY
# ============================================================

side_rows = []

for strategy_name, version_name, result in [
    ("Fixed Donchian 49", "Full long/short", fixed_full),
    ("Fixed Donchian 49", "Long only", fixed_long),
    ("Fixed Donchian 49", "Short only", fixed_short),
    ("Walk-Forward Donchian", "Full long/short", walkforward_full),
    ("Walk-Forward Donchian", "Long only", walkforward_long),
    ("Walk-Forward Donchian", "Short only", walkforward_short),
]:
    side_rows.append(
        {
            "strategy": strategy_name,
            "version": version_name,
            "total_return_percent": result.summary[
                "total_return_percent"
            ],
            "max_drawdown_percent": result.summary[
                "max_drawdown_percent"
            ],
            "total_trades": result.summary["total_trades"],
            "win_rate_percent": result.summary["win_rate_percent"],
            "trade_profit_factor": result.summary[
                "trade_profit_factor"
            ],
            "average_trade_percent": result.summary[
                "average_trade_percent"
            ],
        }
    )

side_table = pd.DataFrame(side_rows)
side_table.to_csv(
    RESULTS_DIR / "EXP-001_long_short_summary.csv",
    index=False,
)


# ============================================================
# YEAR-BY-YEAR RESULTS
# ============================================================

yearly_table = pd.concat(
    [
        yearly_metrics("Fixed Donchian 49", fixed_full),
        yearly_metrics("Walk-Forward Donchian", walkforward_full),
    ],
    ignore_index=True,
)

yearly_table.to_csv(
    RESULTS_DIR / "EXP-001_yearly_results.csv",
    index=False,
)


# ============================================================
# CHART 1 — COST SENSITIVITY
# ============================================================

plt.style.use("dark_background")

plt.figure(figsize=(14, 7))

for strategy_name, group in cost_table.groupby("strategy"):
    plt.plot(
        group["cost_bps_per_side"],
        group["total_return_percent"],
        marker="o",
        linewidth=2,
        label=strategy_name,
    )

plt.axhline(0, linewidth=1, linestyle="--")
plt.title("EXP-001 — Transaction-Cost Sensitivity")
plt.xlabel("Total Cost per Transaction Side (basis points)")
plt.ylabel("Out-of-Sample Total Return (%)")
plt.grid(alpha=0.2)
plt.legend()

save_current_figure("01_cost_sensitivity.png")


# ============================================================
# CHART 2 — FIXED LONG / SHORT EQUITY
# ============================================================

plt.figure(figsize=(14, 7))

for label, result in [
    ("Full long/short", fixed_full),
    ("Long only", fixed_long),
    ("Short only", fixed_short),
]:
    plt.plot(
        result.equity_curve.index,
        result.equity_curve["equity"],
        linewidth=1.8,
        label=label,
    )

plt.axhline(STARTING_CAPITAL, linewidth=1, linestyle="--")
plt.title("EXP-001 — Fixed Donchian 49: Long vs Short")
plt.xlabel("Date")
plt.ylabel("Account Equity")
plt.grid(alpha=0.2)
plt.legend()

save_current_figure("02_fixed_long_short_equity.png")


# ============================================================
# CHART 3 — WALK-FORWARD LONG / SHORT EQUITY
# ============================================================

plt.figure(figsize=(14, 7))

for label, result in [
    ("Full long/short", walkforward_full),
    ("Long only", walkforward_long),
    ("Short only", walkforward_short),
]:
    plt.plot(
        result.equity_curve.index,
        result.equity_curve["equity"],
        linewidth=1.8,
        label=label,
    )

plt.axhline(STARTING_CAPITAL, linewidth=1, linestyle="--")
plt.title("EXP-001 — Walk-Forward Donchian: Long vs Short")
plt.xlabel("Date")
plt.ylabel("Account Equity")
plt.grid(alpha=0.2)
plt.legend()

save_current_figure("03_walkforward_long_short_equity.png")


# ============================================================
# CHART 4 — ROLLING TRADE PROFIT FACTOR
# ============================================================

fixed_rolling_pf = rolling_trade_profit_factor(
    fixed_full.trades,
    ROLLING_TRADE_WINDOW,
)

walkforward_rolling_pf = rolling_trade_profit_factor(
    walkforward_full.trades,
    ROLLING_TRADE_WINDOW,
)

plt.figure(figsize=(14, 7))

plt.plot(
    fixed_rolling_pf.index,
    fixed_rolling_pf,
    linewidth=1.7,
    label="Fixed Donchian 49",
)

plt.plot(
    walkforward_rolling_pf.index,
    walkforward_rolling_pf,
    linewidth=1.7,
    label="Walk-Forward Donchian",
)

plt.axhline(1.0, linewidth=1, linestyle="--", label="PF = 1.0")
plt.title(
    f"EXP-001 — Rolling {ROLLING_TRADE_WINDOW}-Trade Profit Factor"
)
plt.xlabel("Trade Exit Date")
plt.ylabel("Rolling Trade Profit Factor")
plt.ylim(bottom=0)
plt.grid(alpha=0.2)
plt.legend()

save_current_figure("04_rolling_trade_pf.png")


# ============================================================
# CHART 5 — YEARLY RETURNS
# ============================================================

yearly_returns = yearly_table.pivot(
    index="year",
    columns="strategy",
    values="return_percent",
)

yearly_returns.plot(kind="bar", figsize=(14, 7))

plt.axhline(0, linewidth=1)
plt.title("EXP-001 — Year-by-Year Net Returns")
plt.xlabel("Year")
plt.ylabel("Return (%)")
plt.xticks(rotation=0)
plt.grid(axis="y", alpha=0.2)
plt.legend(title="Strategy")

save_current_figure("05_yearly_returns.png")


# ============================================================
# CHART 6 — YEARLY TRADE PROFIT FACTOR
# ============================================================

yearly_pf = yearly_table.pivot(
    index="year",
    columns="strategy",
    values="trade_profit_factor",
)

yearly_pf.plot(kind="bar", figsize=(14, 7))

plt.axhline(1.0, linewidth=1, linestyle="--")
plt.title("EXP-001 — Year-by-Year Trade Profit Factor")
plt.xlabel("Year")
plt.ylabel("Trade Profit Factor")
plt.xticks(rotation=0)
plt.grid(axis="y", alpha=0.2)
plt.legend(title="Strategy")

save_current_figure("06_yearly_trade_pf.png")


# ============================================================
# HTML REPORT
# ============================================================

cost_display = cost_table.copy()
cost_display[
    [
        "cost_bps_per_side",
        "round_trip_cost_bps",
        "total_return_percent",
        "trade_profit_factor",
        "max_drawdown_percent",
    ]
] = cost_display[
    [
        "cost_bps_per_side",
        "round_trip_cost_bps",
        "total_return_percent",
        "trade_profit_factor",
        "max_drawdown_percent",
    ]
].round(3)

side_display = side_table.copy()
side_display[
    [
        "total_return_percent",
        "max_drawdown_percent",
        "win_rate_percent",
        "trade_profit_factor",
        "average_trade_percent",
    ]
] = side_display[
    [
        "total_return_percent",
        "max_drawdown_percent",
        "win_rate_percent",
        "trade_profit_factor",
        "average_trade_percent",
    ]
].round(3)

yearly_display = yearly_table.copy()
yearly_display[
    [
        "return_percent",
        "within_year_max_drawdown_percent",
        "win_rate_percent",
        "trade_profit_factor",
    ]
] = yearly_display[
    [
        "return_percent",
        "within_year_max_drawdown_percent",
        "win_rate_percent",
        "trade_profit_factor",
    ]
].round(3)

fixed_break_even = break_even_description(
    cost_table,
    "Fixed Donchian 49",
)

walkforward_break_even = break_even_description(
    cost_table,
    "Walk-Forward Donchian",
)

report_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>EXP-001 Robustness Report</title>

<style>
body {{
    background: #090909;
    color: #eeeeee;
    font-family: Arial, Helvetica, sans-serif;
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

h2 {{
    margin-top: 45px;
    border-bottom: 1px solid #333333;
    padding-bottom: 8px;
}}

.subtitle {{
    color: #aaaaaa;
    margin-bottom: 25px;
}}

.decision {{
    background: #1c1010;
    border-left: 6px solid #ff4d4d;
    padding: 20px;
    margin: 25px 0;
}}

.note {{
    background: #151515;
    border-left: 5px solid #888888;
    padding: 18px;
    margin: 20px 0;
}}

.chart {{
    width: 100%;
    border: 1px solid #333333;
    border-radius: 8px;
    margin: 15px 0 35px;
}}

table {{
    width: 100%;
    border-collapse: collapse;
    background: #151515;
    margin: 15px 0 30px;
}}

th, td {{
    border: 1px solid #333333;
    padding: 10px;
    text-align: center;
}}

th {{
    background: #222222;
}}
</style>
</head>

<body>
<div class="page">

<h1>EXP-001 — Robustness Report</h1>

<div class="subtitle">
BTCUSDT hourly data · Out-of-sample period
{oos_data.index.min()} through {oos_data.index.max()}
</div>

<div class="decision">
<strong>Decision: REJECTED</strong>

<p>
Both Donchian variants lose money before costs and deteriorate
further as trading friction rises. Long-only and short-only
decompositions do not reveal a robust profitable component.
</p>
</div>

<h2>Transaction-Cost Sensitivity</h2>

<div class="note">
<p><strong>Fixed Donchian:</strong> {fixed_break_even}</p>
<p><strong>Walk-forward Donchian:</strong> {walkforward_break_even}</p>
</div>

<img class="chart" src="01_cost_sensitivity.png"
     alt="Cost sensitivity">

{cost_display.to_html(index=False, border=0)}

<h2>Fixed Donchian: Long vs Short</h2>

<img class="chart" src="02_fixed_long_short_equity.png"
     alt="Fixed Donchian long and short">

<h2>Walk-Forward Donchian: Long vs Short</h2>

<img class="chart" src="03_walkforward_long_short_equity.png"
     alt="Walk-forward Donchian long and short">

{side_display.to_html(index=False, border=0)}

<h2>Rolling Trade Profit Factor</h2>

<p>
Each point uses the most recent {ROLLING_TRADE_WINDOW}
completed trades. Values above 1 indicate that gains exceeded
losses within that rolling trade window.
</p>

<img class="chart" src="04_rolling_trade_pf.png"
     alt="Rolling trade profit factor">

<h2>Year-by-Year Results</h2>

<img class="chart" src="05_yearly_returns.png"
     alt="Yearly returns">

<img class="chart" src="06_yearly_trade_pf.png"
     alt="Yearly trade profit factor">

{yearly_display.to_html(index=False, border=0)}

<h2>Research Interpretation</h2>

<p>
The strategy is not failing solely because of an aggressive
cost assumption. It is already unprofitable at zero transaction
cost. Costs merely expose how little margin the strategy had.
</p>

<p>
The yearly and rolling charts show whether performance was
consistently weak or concentrated in isolated periods. These
views are more informative than one full-sample number.
</p>

</div>
</body>
</html>
"""

report_file = REPORT_DIR / "report.html"
report_file.write_text(report_html, encoding="utf-8")

print("Robustness report created.")
print()
print(f"Report: {report_file}")
print(f"Cost table: {RESULTS_DIR / 'EXP-001_cost_sensitivity.csv'}")
print(
    f"Long/short table: "
    f"{RESULTS_DIR / 'EXP-001_long_short_summary.csv'}"
)
print(
    f"Yearly table: "
    f"{RESULTS_DIR / 'EXP-001_yearly_results.csv'}"
)
