from __future__ import annotations

from pathlib import Path

from experiment_config import ResearchConfig


EXPERIMENT = ResearchConfig(
    experiment_id="EXP-004",
    experiment_name=(
        "QQQ 5-Minute Opening Range Breakout"
    ),
    hypothesis=(
        "After QQQ establishes its opening range, "
        "the first confirmed break outside that "
        "range may continue far enough during the "
        "same regular session to overcome realistic "
        "intraday trading costs."
    ),
    market_name="QQQ ETF",
    timeframe="5 minutes",
    data_file=Path(
        "data/QQQ_5m_SIP.parquet"
    ),
    strategy_name=(
        "opening_range_breakout"
    ),
    fixed_parameters={
        "opening_range_minutes": 15,
        "direction_mode": "both",
    },
    optimization_grid={
        "opening_range_minutes": [
            5,
            15,
            30,
        ],
        "direction_mode": [
            "long_only",
            "short_only",
            "both",
        ],
    },
    in_sample_start="2019-01-02",
    in_sample_end="2022-12-31",
    out_of_sample_start="2023-01-03",
    out_of_sample_end="2026-01-01",
    starting_capital=100_000.0,
    commission_bps_per_side=0.5,
    slippage_bps_per_side=1.0,
    execution_lag_bars=1,
    run_mcpt=True,
    mcpt_permutations=1_000,
    random_seed=44,
    run_walkforward=True,
    walkforward_training_bars=(
        504 * 78
    ),
    walkforward_retrain_bars=(
        21 * 78
    ),
    results_folder=Path("results"),
    reports_folder=Path("reports"),
)


if __name__ == "__main__":
    EXPERIMENT.validate()

    print(
        "EXP-004 configuration is valid."
    )
