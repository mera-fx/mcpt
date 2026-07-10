from pathlib import Path

from experiment_config import ResearchConfig


EXPERIMENT = ResearchConfig(
    experiment_id="EXP-002",
    experiment_name=(
        "BTCUSDT Hourly Long-Only Z-Score Mean Reversion"
    ),
    hypothesis=(
        "After an unusually large hourly downside deviation from "
        "its rolling mean, BTCUSDT tends to rebound enough to "
        "support a long-only mean-reversion trade."
    ),

    market_name="BTCUSDT spot",
    timeframe="1 hour",
    data_file=Path("data/BTCUSDT_1h.parquet"),

    strategy_name="zscore_mean_reversion_long",

    # Pre-specified before viewing EXP-002 out-of-sample results.
    fixed_parameters={
        "lookback": 72,
        "entry_z": 2.0,
    },

    optimization_grid={
        "lookback": [
            24,
            48,
            72,
            120,
            168,
        ],
        "entry_z": [
            1.0,
            1.5,
            2.0,
            2.5,
        ],
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

    cost_levels_bps_per_side=(
        0.0,
        1.0,
        2.0,
        3.0,
        5.0,
        7.0,
        10.0,
        15.0,
        20.0,
    ),
    rolling_trade_window=50,

    results_folder=Path("results"),
    reports_folder=Path("reports"),
)
