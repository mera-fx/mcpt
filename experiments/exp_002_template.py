from pathlib import Path

from experiment_config import ResearchConfig


# Copy this file to exp_002.py only after EXP-002 has a genuinely
# different hypothesis and strategy rule.
EXPERIMENT = ResearchConfig(
    experiment_id="EXP-002",
    experiment_name="Replace with experiment name",
    hypothesis=(
        "Write a clear, falsifiable market hypothesis here."
    ),

    market_name="BTCUSDT spot",
    timeframe="1 hour",
    data_file=Path("data/BTCUSDT_1h.parquet"),

    strategy_name="replace_with_registered_strategy",

    fixed_parameters={
        "replace_parameter": 1,
    },

    optimization_grid={
        "replace_parameter": [1, 2, 3],
    },

    in_sample_start="2018-01-01",
    in_sample_end="2022-01-01",
    out_of_sample_start="2022-01-01",
    out_of_sample_end="2026-01-01",

    starting_capital=100_000.0,
    commission_bps_per_side=5.0,
    slippage_bps_per_side=2.0,
    execution_lag_bars=1,

    run_mcpt=True,
    mcpt_permutations=1_000,
    random_seed=20_000,

    run_walkforward=True,
    walkforward_training_bars=24 * 365 * 4,
    walkforward_retrain_bars=24 * 30,
)
