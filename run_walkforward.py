from pathlib import Path

import numpy as np
import pandas as pd

from donchian import walkforward_donch


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent
DATA_FILE = PROJECT_DIR / "data" / "BTCUSDT_1h.parquet"

MARKET = "BTCUSDT spot"

# Use complete calendar years from 2018 through 2025.
START_YEAR = 2018
END_YEAR = 2026  # Exclusive

# Four years of hourly bars for each training window.
TRAIN_YEARS = 4
TRAIN_WINDOW = 24 * 365 * TRAIN_YEARS

# Re-optimize approximately once per month.
RETRAIN_EVERY_BARS = 24 * 30


# ============================================================
# LOAD DATA
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

required_columns = {"open", "high", "low", "close"}
missing_columns = required_columns.difference(df.columns)

if missing_columns:
    raise RuntimeError(
        f"Dataset is missing required columns: {sorted(missing_columns)}"
    )

if len(df) <= TRAIN_WINDOW:
    raise RuntimeError(
        "There is not enough data for the selected training window."
    )


# ============================================================
# CALCULATE MARKET RETURNS
# ============================================================

# This aligns each signal with the following bar's return.
df["market_return"] = np.log(df["close"]).diff().shift(-1)


# ============================================================
# WALK-FORWARD STRATEGY
# ============================================================

print()
print("Running real-market walk-forward test...")
print("This may take several minutes.")
print()

df["wf_signal"] = walkforward_donch(
    df,
    train_lookback=TRAIN_WINDOW,
    train_step=RETRAIN_EVERY_BARS,
)

df["strategy_return"] = (
    df["wf_signal"] * df["market_return"]
)


# Only evaluate the portion after the initial training window.
oos = df.iloc[TRAIN_WINDOW:].copy()

valid_returns = oos["strategy_return"].dropna()
positive_returns = valid_returns[valid_returns > 0].sum()
negative_returns = valid_returns[valid_returns < 0].abs().sum()

if negative_returns == 0:
    walkforward_pf = float("inf")
else:
    walkforward_pf = positive_returns / negative_returns


# ============================================================
# EQUITY AND DRAWDOWN
# ============================================================

oos["equity"] = np.exp(
    oos["strategy_return"].fillna(0).cumsum()
)

oos["drawdown"] = (
    oos["equity"] / oos["equity"].cummax() - 1
)

total_log_return = valid_returns.sum()
total_return_percent = (
    np.exp(total_log_return) - 1
) * 100

max_drawdown_percent = oos["drawdown"].min() * 100

positions = oos["wf_signal"].dropna()

if positions.empty:
    position_changes = 0
else:
    position_changes = int(
        positions.ne(positions.shift()).sum()
    )


# ============================================================
# DATA QUALITY
# ============================================================

time_differences = df.index.to_series().diff()
gap_count = int(
    (time_differences > pd.Timedelta(hours=1)).sum()
)


# ============================================================
# SAVE RESULTS
# ============================================================

results_directory = PROJECT_DIR / "results"
results_directory.mkdir(exist_ok=True)

results_file = results_directory / "EXP-001_walkforward.csv"

columns_to_save = [
    "close",
    "market_return",
    "wf_signal",
    "strategy_return",
    "equity",
    "drawdown",
]

oos[columns_to_save].to_csv(
    results_file,
    index=True,
)


# ============================================================
# DISPLAY SUMMARY
# ============================================================

print("========== EXP-001 WALK-FORWARD ==========")
print(f"Market:                    {MARKET}")
print(f"Full data period:          {df.index.min()}")
print(f"                           to {df.index.max()}")
print()
print(f"Training window:           {TRAIN_YEARS} years")
print(f"Retraining frequency:      {RETRAIN_EVERY_BARS} bars")
print()
print(f"Walk-forward start:        {oos.index.min()}")
print(f"Walk-forward end:          {oos.index.max()}")
print(f"Walk-forward rows:         {len(oos):,}")
print(f"Data gaps in full sample:  {gap_count}")
print()
print(f"Walk-forward PF:           {walkforward_pf:.4f}")
print(f"Total return, no costs:    {total_return_percent:.2f}%")
print(f"Maximum drawdown:          {max_drawdown_percent:.2f}%")
print(f"Position changes:          {position_changes}")
print()
print(f"Results saved to:          {results_file}")
print("==========================================")