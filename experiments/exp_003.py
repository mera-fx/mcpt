from pathlib import Path

from experiment_config import ResearchConfig


EXPERIMENT = ResearchConfig(
    experiment_id="EXP-003",
    experiment_name=(
        "BTCUSDT Hourly Long-Only "
        "Volatility-Compression Breakout"
    ),
    hypothesis=(
        "After an unusually quiet realized-volatility regime, "
        "an upside price-range breakout may be followed by "
        "positive continuation strong enough to overcome "
        "realistic trading costs."
    ),

    market_name="BTCUSDT spot",
    timeframe="1 hour",
    data_file=Path("data/BTCUSDT_1h.parquet"),

    strategy_name=(
        "volatility_compression_breakout_long"
    ),

    fixed_parameters={
        "vol_lookback": 48,
        "compression_quantile": 0.20,
        "breakout_lookback": 48,
    },

    optimization_grid={
        "vol_lookback": [24, 48, 72],
        "compression_quantile": [
            0.10,
            0.20,
            0.30,
        ],
        "breakout_lookback": [24, 48, 72],
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
    random_seed=42,

    run_walkforward=True,
    walkforward_training_bars=35_040,
    walkforward_retrain_bars=720,

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
