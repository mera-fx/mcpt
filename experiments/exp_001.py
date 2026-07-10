from pathlib import Path

from experiment_config import ResearchConfig


EXPERIMENT = ResearchConfig(
    experiment_id="EXP-001",
    experiment_name="BTCUSDT Hourly Donchian Breakout",
    hypothesis=(
        "BTCUSDT may exhibit trend persistence that can be "
        "captured by a closing-price Donchian breakout."
    ),

    market_name="BTCUSDT spot",
    timeframe="1 hour",
    data_file=Path("data/BTCUSDT_1h.parquet"),

    strategy_name="donchian_breakout",

    fixed_parameters={
        "lookback": 49,
    },

    optimization_grid={
        "lookback": list(range(12, 169)),
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
    random_seed=10_000,

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
