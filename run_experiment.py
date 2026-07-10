from pathlib import Path

import pandas as pd
from tqdm import tqdm

from bar_permute import get_permutation
from donchian import optimize_donchian


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent
DATA_FILE = PROJECT_DIR / "data" / "BTCUSDT_1h.parquet"

MARKET = "BTCUSDT spot"
START_YEAR = 2018
END_YEAR = 2022  # Exclusive: includes 2018 through 2021

# Start with 100 to verify the experiment works.
# We can increase this to 1,000 after the first successful run.
N_PERMUTATIONS = 1000
BASE_RANDOM_SEED = 10_000


# ============================================================
# LOAD AND CHECK DATA
# ============================================================

if not DATA_FILE.exists():
    raise FileNotFoundError(f"Data file not found: {DATA_FILE}")

df = pd.read_parquet(DATA_FILE)
df.index = pd.to_datetime(df.index)

df = df[
    (df.index.year >= START_YEAR)
    & (df.index.year < END_YEAR)
].copy()

if df.empty:
    raise RuntimeError("No rows remain after applying the year filter.")

required_columns = {"open", "high", "low", "close"}
missing_columns = required_columns.difference(df.columns)

if missing_columns:
    raise RuntimeError(
        f"Dataset is missing required columns: {sorted(missing_columns)}"
    )

hourly_differences = df.index.to_series().diff()
sample_gap_count = int(
    (hourly_differences > pd.Timedelta(hours=1)).sum()
)


# ============================================================
# REAL-MARKET BASELINE
# ============================================================

best_lookback, best_real_pf = optimize_donchian(df)


# ============================================================
# MONTE CARLO PERMUTATION TEST
# ============================================================

permuted_pfs = []

print()
print(f"Running {N_PERMUTATIONS} market permutations...")

for permutation_number in tqdm(
    range(N_PERMUTATIONS),
    desc="MCPT",
):
    permuted_df = get_permutation(
        df,
        seed=BASE_RANDOM_SEED + permutation_number,
    )

    _, best_permuted_pf = optimize_donchian(permuted_df)
    permuted_pfs.append(best_permuted_pf)

permuted_results = pd.Series(
    permuted_pfs,
    name="best_permuted_pf",
)

better_or_equal_count = int(
    (permuted_results >= best_real_pf).sum()
)

# The +1 correction prevents an estimated probability of exactly zero.
mcpt_p_value = (
    better_or_equal_count + 1
) / (
    N_PERMUTATIONS + 1
)


# ============================================================
# SAVE AND DISPLAY RESULTS
# ============================================================

results_directory = PROJECT_DIR / "results"
results_directory.mkdir(exist_ok=True)

results_file = results_directory / "EXP-001_mcpt.csv"
permuted_results.to_csv(results_file, index=False)

print()
print("============== EXP-001 ==============")
print(f"Market:                 {MARKET}")
print(f"Period:                 {START_YEAR}-{END_YEAR - 1}")
print(f"Hourly rows:            {len(df):,}")
print(f"Gaps within sample:     {sample_gap_count}")
print()
print(f"Best real lookback:     {best_lookback}")
print(f"Best real PF:           {best_real_pf:.4f}")
print()
print(f"Permutations:           {N_PERMUTATIONS}")
print(f"Median permuted PF:     {permuted_results.median():.4f}")
print(f"Maximum permuted PF:    {permuted_results.max():.4f}")
print(f"Permutations >= real:   {better_or_equal_count}")
print(f"MCPT p-value:           {mcpt_p_value:.4f}")
print()
print(f"Results saved to:       {results_file}")
print("=====================================")