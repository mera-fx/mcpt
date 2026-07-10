from pathlib import Path

import numpy as np
import pandas as pd

from donchian import donchian_breakout, walkforward_donch


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent
DATA_FILE = PROJECT_DIR / "data" / "BTCUSDT_1h.parquet"

START_YEAR = 2018
END_YEAR = 2026  # Exclusive

FIXED_LOOKBACK = 49

TRAIN_WINDOW = 24 * 365 * 4
RETRAIN_EVERY_BARS = 24 * 30


# ============================================================
# HELPER
# ============================================================

def calculate_metrics(returns: pd.Series, signal: pd.Series) -> dict:
    returns = returns.dropna()

    gains = returns[returns > 0].sum()
    losses = returns[returns < 0].abs().sum()

    profit_factor = gains / losses if losses > 0 else float("inf")

    equity = np.exp(returns.fillna(0).cumsum())
    drawdown = equity / equity.cummax() - 1

    total_return = (equity.iloc[-1] - 1) * 100
    max_drawdown = drawdown.min() * 100

    clean_signal = signal.dropna()
    position_changes = int(
        clean_signal.ne(clean_signal.shift()).sum()
    )

    return {
        "profit_factor": profit_factor,
        "total_return_percent": total_return,
        "max_drawdown_percent": max_drawdown,
        "position_changes": position_changes,
    }


# ============================================================
# LOAD DATA
# ============================================================

df = pd.read_parquet(DATA_FILE)
df.index = pd.to_datetime(df.index)
df = df.sort_index()

df = df[
    (df.index.year >= START_YEAR)
    & (df.index.year < END_YEAR)
].copy()

df["market_return"] = np.log(df["close"]).diff().shift(-1)


# ============================================================
# CREATE STRATEGIES
# ============================================================

# Fixed lookback chosen using the earlier 2018–2021 experiment.
df["fixed_signal"] = donchian_breakout(
    df,
    FIXED_LOOKBACK,
)

# Rolling four-year training window, re-optimized monthly.
df["walkforward_signal"] = walkforward_donch(
    df,
    train_lookback=TRAIN_WINDOW,
    train_step=RETRAIN_EVERY_BARS,
)

# Buy and hold is permanently long.
df["buy_hold_signal"] = 1.0


# ============================================================
# USE THE SAME UNSEEN PERIOD FOR ALL THREE
# ============================================================

oos = df.iloc[TRAIN_WINDOW:].copy()

oos["fixed_return"] = (
    oos["fixed_signal"] * oos["market_return"]
)

oos["walkforward_return"] = (
    oos["walkforward_signal"] * oos["market_return"]
)

oos["buy_hold_return"] = (
    oos["buy_hold_signal"] * oos["market_return"]
)


# ============================================================
# CALCULATE RESULTS
# ============================================================

fixed_metrics = calculate_metrics(
    oos["fixed_return"],
    oos["fixed_signal"],
)

walkforward_metrics = calculate_metrics(
    oos["walkforward_return"],
    oos["walkforward_signal"],
)

buy_hold_metrics = calculate_metrics(
    oos["buy_hold_return"],
    oos["buy_hold_signal"],
)

results = pd.DataFrame(
    {
        "Fixed Donchian 49": fixed_metrics,
        "Walk-Forward Donchian": walkforward_metrics,
        "Buy and Hold": buy_hold_metrics,
    }
).T


# ============================================================
# SAVE AND DISPLAY
# ============================================================

results_directory = PROJECT_DIR / "results"
results_directory.mkdir(exist_ok=True)

summary_file = results_directory / "EXP-001_comparison.csv"
detail_file = results_directory / "EXP-001_comparison_detail.csv"

results.to_csv(summary_file)

oos[
    [
        "close",
        "market_return",
        "fixed_signal",
        "fixed_return",
        "walkforward_signal",
        "walkforward_return",
        "buy_hold_return",
    ]
].to_csv(detail_file)

print()
print("============== EXP-001 COMPARISON ==============")
print(f"Comparison start: {oos.index.min()}")
print(f"Comparison end:   {oos.index.max()}")
print(f"Rows:             {len(oos):,}")
print()
print(results.round(4).to_string())
print()
print(f"Summary saved to: {summary_file}")
print(f"Details saved to: {detail_file}")
print("================================================")