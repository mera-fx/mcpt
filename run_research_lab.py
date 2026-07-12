from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from experiment_config import (
    ResearchConfig,
    list_experiments,
    load_experiment,
)
from strategy_registry import (
    expand_parameter_grid,
    generate_signal,
    get_strategy,
)
from mcpt_engine import (
    McptExecutionInfo,
    run_mcpt_engine,
)
from trade_engine import (
    CostModel,
    BacktestResult,
    backtest_signal_strategy,
    signal_to_target_position,
)
from trade_diagnostics import calculate_trade_diagnostics
from parameter_analysis import (
    analyze_parameter_stability,
    create_parameter_heatmaps,
)
from experiment_lifecycle import (
    format_stage_label,
    get_experiment_lifecycle,
)
from research_access_control import (
    assert_full_research_allowed,
)
from research_report_ui import write_research_report
from run_provenance import (
    append_run_history,
    combined_code_fingerprint,
    configuration_fingerprint,
    git_state,
    load_compatible_mcpt_cache,
    mcpt_base_signature,
    runtime_environment,
    save_mcpt_cache,
    sha256_file,
    utc_run_identity,
)


PROJECT_DIR = Path(__file__).resolve().parent


# ============================================================
# GENERAL HELPERS
# ============================================================

def resolve_project_path(path: Path) -> Path:
    if path.is_absolute():
        return path

    return PROJECT_DIR / path


def json_ready(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)

    if isinstance(value, dict):
        return {
            str(key): json_ready(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [json_ready(item) for item in value]

    if isinstance(value, (np.integer,)):
        return int(value)

    if isinstance(value, (np.floating,)):
        return float(value)

    if isinstance(value, pd.Timestamp):
        return value.isoformat()

    return value


def safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def format_number(value: Any, decimals: int = 3) -> str:
    number = safe_float(value)

    if np.isnan(number):
        return "N/A"

    if np.isposinf(number):
        return "∞"

    if np.isneginf(number):
        return "-∞"

    return f"{number:,.{decimals}f}"


def format_percent(value: Any, decimals: int = 2) -> str:
    number = safe_float(value)

    if np.isnan(number):
        return "N/A"

    return f"{number:,.{decimals}f}%"


# ============================================================
# DATA LOADING AND VALIDATION
# ============================================================

def load_market_data(
    config: ResearchConfig,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Timestamp]:
    data_file = resolve_project_path(config.data_file)

    if not data_file.exists():
        raise FileNotFoundError(
            f"Market data file was not found:\n{data_file}"
        )

    data = pd.read_parquet(data_file)
    data.index = pd.to_datetime(data.index)
    data = data.sort_index()

    required_columns = {"open", "high", "low", "close"}
    missing_columns = required_columns.difference(data.columns)

    if missing_columns:
        raise RuntimeError(
            "The dataset is missing required columns: "
            f"{sorted(missing_columns)}"
        )

    if data.index.has_duplicates:
        duplicate_count = int(data.index.duplicated().sum())
        raise RuntimeError(
            f"The dataset contains {duplicate_count} duplicate timestamps."
        )

    if not data.index.is_monotonic_increasing:
        raise RuntimeError(
            "The market-data index is not in chronological order."
        )

    if (data[["open", "high", "low", "close"]] <= 0).any().any():
        raise RuntimeError(
            "OHLC prices must all be positive."
        )

    in_sample_start = pd.Timestamp(config.in_sample_start)
    in_sample_end = pd.Timestamp(config.in_sample_end)
    requested_oos_start = pd.Timestamp(config.out_of_sample_start)
    out_of_sample_end = pd.Timestamp(config.out_of_sample_end)

    if in_sample_start >= in_sample_end:
        raise ValueError(
            "in_sample_start must be earlier than in_sample_end."
        )

    if requested_oos_start >= out_of_sample_end:
        raise ValueError(
            "out_of_sample_start must be earlier than out_of_sample_end."
        )

    if in_sample_end > requested_oos_start:
        raise ValueError(
            "The in-sample period overlaps the out-of-sample period."
        )

    research_start = min(in_sample_start, requested_oos_start)

    research_data = data[
        (data.index >= research_start)
        & (data.index < out_of_sample_end)
    ].copy()

    in_sample_data = data[
        (data.index >= in_sample_start)
        & (data.index < in_sample_end)
    ].copy()

    if in_sample_data.empty:
        raise RuntimeError(
            "No data remains in the configured in-sample period."
        )

    if research_data.empty:
        raise RuntimeError(
            "No data remains in the configured research period."
        )

    requested_oos_positions = np.flatnonzero(
        research_data.index >= requested_oos_start
    )

    if len(requested_oos_positions) == 0:
        raise RuntimeError(
            "The configured out-of-sample start is after the available data."
        )

    requested_oos_position = int(requested_oos_positions[0])

    effective_oos_position = requested_oos_position

    if config.run_walkforward:
        effective_oos_position = max(
            requested_oos_position,
            config.walkforward_training_bars,
        )

    if effective_oos_position >= len(research_data):
        raise RuntimeError(
            "There is not enough history before the out-of-sample period "
            "for the configured walk-forward training window."
        )

    effective_oos_start = research_data.index[
        effective_oos_position
    ]

    out_of_sample_data = research_data[
        (research_data.index >= effective_oos_start)
        & (research_data.index < out_of_sample_end)
    ].copy()

    if out_of_sample_data.empty:
        raise RuntimeError(
            "No data remains in the effective out-of-sample period."
        )

    return (
        research_data,
        in_sample_data,
        out_of_sample_data,
        effective_oos_start,
    )


# ============================================================
# OPTIMIZATION
# ============================================================

def bar_return_profit_factor(
    data: pd.DataFrame,
    signal: pd.Series,
) -> float:
    """
    Match the original MCPT repository's fast optimization objective.

    This is a profit factor calculated from bar-level strategy returns,
    not from completed trades. Completed-trade metrics are calculated
    separately by trade_engine.py.
    """

    next_bar_return = (
        np.log(data["close"])
        .diff()
        .shift(-1)
    )

    strategy_returns = (
        signal.reindex(data.index)
        * next_bar_return
    ).dropna()

    if len(strategy_returns) < 10:
        return float("nan")

    gains = strategy_returns[
        strategy_returns > 0
    ].sum()

    losses = strategy_returns[
        strategy_returns < 0
    ].abs().sum()

    if losses <= 0:
        return float("nan")

    return float(gains / losses)


def optimize_strategy(
    data: pd.DataFrame,
    config: ResearchConfig,
) -> tuple[dict[str, Any], float, pd.DataFrame]:
    combinations = expand_parameter_grid(
        config.strategy_name,
        config.optimization_grid,
    )

    rows: list[dict[str, Any]] = []

    for parameters in combinations:
        signal = generate_signal(
            config.strategy_name,
            data,
            parameters,
        )

        objective = bar_return_profit_factor(
            data,
            signal,
        )

        rows.append(
            {
                **parameters,
                "bar_profit_factor": objective,
            }
        )

    table = pd.DataFrame(rows)
    valid = table.replace(
        [np.inf, -np.inf],
        np.nan,
    ).dropna(subset=["bar_profit_factor"])

    if valid.empty:
        raise RuntimeError(
            "Every parameter combination produced an invalid score."
        )

    best_index = valid["bar_profit_factor"].idxmax()
    best_row = valid.loc[best_index]

    strategy = get_strategy(config.strategy_name)

    best_parameters: dict[str, Any] = {}

    for parameter_name in strategy.parameter_names:
        raw_value = best_row[parameter_name]

        if hasattr(raw_value, "item"):
            raw_value = raw_value.item()

        example_value = config.optimization_grid[
            parameter_name
        ][0]

        if isinstance(example_value, bool):
            typed_value = bool(raw_value)
        elif isinstance(example_value, int):
            typed_value = int(raw_value)
        elif isinstance(example_value, float):
            typed_value = float(raw_value)
        elif isinstance(example_value, str):
            typed_value = str(raw_value)
        else:
            typed_value = raw_value

        best_parameters[parameter_name] = typed_value

    best_score = float(best_row["bar_profit_factor"])

    return best_parameters, best_score, table


# ============================================================
# WALK-FORWARD SIGNAL
# ============================================================

def build_walkforward_signal(
    research_data: pd.DataFrame,
    out_of_sample_data: pd.DataFrame,
    config: ResearchConfig,
) -> tuple[pd.Series, pd.DataFrame]:
    signal = pd.Series(
        np.nan,
        index=research_data.index,
        name="walkforward_signal",
        dtype=float,
    )

    parameter_rows: list[dict[str, Any]] = []

    oos_index = out_of_sample_data.index
    retrain_bars = config.walkforward_retrain_bars
    training_bars = config.walkforward_training_bars

    total_blocks = int(
        np.ceil(len(oos_index) / retrain_bars)
    )

    for block_number, block_start in enumerate(
        range(0, len(oos_index), retrain_bars),
        start=1,
    ):
        block_index = oos_index[
            block_start:
            block_start + retrain_bars
        ]

        first_timestamp = block_index[0]
        last_timestamp = block_index[-1]

        first_position = int(
            research_data.index.get_loc(first_timestamp)
        )

        last_position = int(
            research_data.index.get_loc(last_timestamp)
        )

        training_start_position = (
            first_position - training_bars
        )

        if training_start_position < 0:
            raise RuntimeError(
                "A walk-forward block does not have enough prior "
                "training history."
            )

        training_data = research_data.iloc[
            training_start_position:
            first_position
        ].copy()

        best_parameters, best_score, _ = optimize_strategy(
            training_data,
            config,
        )

        # Include the training window as historical context so rolling
        # indicators at the start of the test block are well-defined.
        context_data = research_data.iloc[
            training_start_position:
            last_position + 1
        ].copy()

        context_signal = generate_signal(
            config.strategy_name,
            context_data,
            best_parameters,
        )

        signal.loc[block_index] = context_signal.reindex(
            block_index
        )

        parameter_rows.append(
            {
                "block_number": block_number,
                "total_blocks": total_blocks,
                "test_start": first_timestamp,
                "test_end": last_timestamp,
                "training_start": training_data.index.min(),
                "training_end": training_data.index.max(),
                "training_rows": len(training_data),
                "best_bar_profit_factor": best_score,
                **best_parameters,
            }
        )

        print(
            f"Walk-forward block {block_number}/{total_blocks}: "
            f"{first_timestamp} to {last_timestamp} | "
            f"parameters={best_parameters}"
        )

    return signal, pd.DataFrame(parameter_rows)


# ============================================================
# MONTE CARLO PERMUTATION TEST
# ============================================================

def run_mcpt(
    in_sample_data: pd.DataFrame,
    config: ResearchConfig,
    permutations: int,
    *,
    requested_workers: int,
    checkpoint_directory: Path,
    checkpoint_every: int,
    resume: bool,
    checkpoint_signature: dict[str, Any],
) -> tuple[
    pd.DataFrame,
    float,
    int,
    McptExecutionInfo,
]:
    _, real_score, _ = optimize_strategy(
        in_sample_data,
        config,
    )

    return run_mcpt_engine(
        in_sample_data=in_sample_data,
        strategy_name=config.strategy_name,
        optimization_grid=config.optimization_grid,
        random_seed=config.random_seed,
        permutations=permutations,
        real_score=real_score,
        requested_workers=requested_workers,
        checkpoint_directory=checkpoint_directory,
        checkpoint_every=checkpoint_every,
        resume=resume,
        checkpoint_signature=(
            checkpoint_signature
        ),
    )


# ============================================================
# COMPLETED-TRADE BACKTESTS
# ============================================================

def build_cost_model(
    config: ResearchConfig,
) -> CostModel:
    return CostModel(
        commission_bps_per_side=(
            config.commission_bps_per_side
        ),
        slippage_bps_per_side=(
            config.slippage_bps_per_side
        ),
    )


def run_standard_benchmarks(
    out_of_sample_data: pd.DataFrame,
    config: ResearchConfig,
) -> dict[str, BacktestResult]:
    """
    Run consistent context benchmarks over the same OOS period.

    Buy and Hold:
    - Enter long at the first OOS bar open
    - Exit at the final OOS bar close
    - Uses the same configured transaction costs

    Cash:
    - Remain flat for the entire period
    - Provides a zero-return reference
    """

    buy_hold_target = pd.Series(
        1.0,
        index=out_of_sample_data.index,
        name="buy_hold_target",
    )

    cash_target = pd.Series(
        0.0,
        index=out_of_sample_data.index,
        name="cash_target",
    )

    cost_model = build_cost_model(config)

    return {
        "Buy and Hold": backtest_signal_strategy(
            out_of_sample_data,
            buy_hold_target,
            cost_model=cost_model,
            starting_capital=config.starting_capital,
        ),
        "Cash": backtest_signal_strategy(
            out_of_sample_data,
            cash_target,
            cost_model=cost_model,
            starting_capital=config.starting_capital,
        ),
    }


def run_fixed_backtest(
    research_data: pd.DataFrame,
    out_of_sample_data: pd.DataFrame,
    config: ResearchConfig,
) -> BacktestResult:
    full_signal = generate_signal(
        config.strategy_name,
        research_data,
        config.fixed_parameters,
    )

    full_target = signal_to_target_position(
        full_signal,
        execution_lag_bars=config.execution_lag_bars,
    )

    oos_target = full_target.reindex(
        out_of_sample_data.index
    )

    return backtest_signal_strategy(
        out_of_sample_data,
        oos_target,
        cost_model=build_cost_model(config),
        starting_capital=config.starting_capital,
    )


def run_walkforward_backtest(
    research_data: pd.DataFrame,
    out_of_sample_data: pd.DataFrame,
    config: ResearchConfig,
) -> tuple[BacktestResult, pd.DataFrame]:
    walkforward_signal, parameters = (
        build_walkforward_signal(
            research_data,
            out_of_sample_data,
            config,
        )
    )

    full_target = signal_to_target_position(
        walkforward_signal,
        execution_lag_bars=config.execution_lag_bars,
    )

    oos_target = full_target.reindex(
        out_of_sample_data.index
    )

    result = backtest_signal_strategy(
        out_of_sample_data,
        oos_target,
        cost_model=build_cost_model(config),
        starting_capital=config.starting_capital,
    )

    return result, parameters


def summary_row(
    name: str,
    result: BacktestResult,
) -> dict[str, Any]:
    return {
        "test": name,
        **result.summary,
    }


# ============================================================
# OUTPUT AND VISUAL REPORT
# ============================================================

def save_backtest_files(
    prefix: str,
    result: BacktestResult,
    results_directory: Path,
) -> None:
    result.trades.to_csv(
        results_directory / f"{prefix}_trades.csv",
        index=False,
    )

    result.equity_curve.to_csv(
        results_directory / f"{prefix}_equity.csv",
        index=True,
    )


def create_visual_report(
    config: ResearchConfig,
    report_directory: Path,
    summary: pd.DataFrame,
    optimization_table: pd.DataFrame,
    best_parameters: dict[str, Any],
    best_score: float,
    parameter_stability_summary: dict[str, Any],
    lifecycle_record: dict[str, Any],
    fixed_result: BacktestResult,
    walkforward_result: BacktestResult | None,
    benchmark_results: dict[str, BacktestResult],
    walkforward_parameters: pd.DataFrame | None,
    mcpt_results: pd.DataFrame | None,
    mcpt_p_value: float | None,
    mcpt_source: str,
    diagnostic_summary: pd.DataFrame,
    diagnostic_by_side: pd.DataFrame,
    effective_oos_start: pd.Timestamp,
    oos_end: pd.Timestamp,
) -> Path:
    report_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    plt.style.use("dark_background")

    # --------------------------------------------------------
    # Equity
    # --------------------------------------------------------

    plt.figure(figsize=(14, 7))

    plt.plot(
        fixed_result.equity_curve.index,
        fixed_result.equity_curve["equity"],
        linewidth=1.8,
        label="Fixed parameters",
    )

    if walkforward_result is not None:
        plt.plot(
            walkforward_result.equity_curve.index,
            walkforward_result.equity_curve["equity"],
            linewidth=1.8,
            label="Walk-forward",
        )

    for benchmark_name, benchmark_result in (
        benchmark_results.items()
    ):
        plt.plot(
            benchmark_result.equity_curve.index,
            benchmark_result.equity_curve["equity"],
            linewidth=1.4,
            linestyle="--",
            label=benchmark_name,
        )

    plt.axhline(
        config.starting_capital,
        linewidth=1,
        linestyle="--",
        label="Starting capital",
    )

    plt.title(
        f"{config.experiment_id} — Out-of-Sample Equity"
    )
    plt.xlabel("Date")
    plt.ylabel("Account Equity")
    plt.grid(alpha=0.2)
    plt.legend()
    plt.tight_layout()
    plt.savefig(
        report_directory / "01_equity.png",
        dpi=140,
        bbox_inches="tight",
    )
    plt.close()

    # --------------------------------------------------------
    # Drawdown
    # --------------------------------------------------------

    plt.figure(figsize=(14, 7))

    plt.plot(
        fixed_result.equity_curve.index,
        fixed_result.equity_curve["drawdown"] * 100,
        linewidth=1.8,
        label="Fixed parameters",
    )

    if walkforward_result is not None:
        plt.plot(
            walkforward_result.equity_curve.index,
            walkforward_result.equity_curve["drawdown"] * 100,
            linewidth=1.8,
            label="Walk-forward",
        )

    for benchmark_name, benchmark_result in (
        benchmark_results.items()
    ):
        plt.plot(
            benchmark_result.equity_curve.index,
            benchmark_result.equity_curve["drawdown"] * 100,
            linewidth=1.4,
            linestyle="--",
            label=benchmark_name,
        )

    plt.axhline(0, linewidth=1)
    plt.title(
        f"{config.experiment_id} — Out-of-Sample Drawdown"
    )
    plt.xlabel("Date")
    plt.ylabel("Drawdown (%)")
    plt.grid(alpha=0.2)
    plt.legend()
    plt.tight_layout()
    plt.savefig(
        report_directory / "02_drawdown.png",
        dpi=140,
        bbox_inches="tight",
    )
    plt.close()

    # --------------------------------------------------------
    # Parameter search
    # --------------------------------------------------------

    strategy = get_strategy(config.strategy_name)
    parameter_names = strategy.parameter_names

    plt.figure(figsize=(14, 7))

    if (
        len(parameter_names) == 1
        and pd.api.types.is_numeric_dtype(
            optimization_table[parameter_names[0]]
        )
    ):
        parameter_name = parameter_names[0]

        ordered = optimization_table.sort_values(
            parameter_name
        )

        plt.plot(
            ordered[parameter_name],
            ordered["bar_profit_factor"],
            linewidth=1.8,
        )

        plt.scatter(
            [best_parameters[parameter_name]],
            [best_score],
            s=90,
            label=(
                f"Best: {parameter_name}="
                f"{best_parameters[parameter_name]}"
            ),
        )

        plt.xlabel(parameter_name)
        plt.ylabel("In-Sample Bar Profit Factor")
        plt.legend()

    else:
        top = (
            optimization_table
            .sort_values(
                "bar_profit_factor",
                ascending=False,
            )
            .head(20)
            .copy()
        )

        labels = []

        for _, row in top.iterrows():
            labels.append(
                ", ".join(
                    f"{name}={row[name]}"
                    for name in parameter_names
                )
            )

        positions = np.arange(len(top))

        plt.bar(
            positions,
            top["bar_profit_factor"],
        )

        plt.xticks(
            positions,
            labels,
            rotation=65,
            ha="right",
        )

        plt.ylabel("In-Sample Bar Profit Factor")

    plt.axhline(
        1.0,
        linewidth=1,
        linestyle="--",
        label="PF = 1.0",
    )
    plt.title(
        f"{config.experiment_id} — In-Sample Parameter Search"
    )
    plt.grid(axis="y", alpha=0.2)
    plt.tight_layout()
    plt.savefig(
        report_directory / "03_parameter_search.png",
        dpi=140,
        bbox_inches="tight",
    )
    plt.close()

    chart_sections = [
        (
            "Out-of-Sample Equity",
            "01_equity.png",
        ),
        (
            "Out-of-Sample Drawdown",
            "02_drawdown.png",
        ),
        (
            "In-Sample Parameter Search",
            "03_parameter_search.png",
        ),
    ]

    heatmap_sections = create_parameter_heatmaps(
        optimization_table=optimization_table,
        parameter_names=parameter_names,
        best_parameters=best_parameters,
        output_directory=report_directory,
    )

    chart_sections.extend(
        heatmap_sections
    )

    # --------------------------------------------------------
    # MCPT distribution
    # --------------------------------------------------------

    if (
        mcpt_results is not None
        and mcpt_p_value is not None
        and not mcpt_results.empty
    ):
        plt.figure(figsize=(14, 7))

        plt.hist(
            mcpt_results["best_bar_profit_factor"],
            bins=40,
            alpha=0.85,
        )

        plt.axvline(
            best_score,
            linewidth=3,
            label=(
                f"Real optimized PF: "
                f"{best_score:.4f}"
            ),
        )

        plt.title(
            f"{config.experiment_id} — MCPT Distribution"
        )
        plt.xlabel("Best Optimized Bar Profit Factor")
        plt.ylabel("Permutations")
        plt.grid(alpha=0.15)
        plt.legend()
        plt.tight_layout()
        plt.savefig(
            report_directory / "04_mcpt.png",
            dpi=140,
            bbox_inches="tight",
        )
        plt.close()

        chart_sections.append(
            (
                "Monte Carlo Permutation Test",
                "04_mcpt.png",
            )
        )

    # --------------------------------------------------------
    # Walk-forward parameters
    # --------------------------------------------------------

    if (
        walkforward_parameters is not None
        and not walkforward_parameters.empty
        and len(parameter_names) == 1
        and pd.api.types.is_numeric_dtype(
            walkforward_parameters[
                parameter_names[0]
            ]
        )
    ):
        parameter_name = parameter_names[0]

        plt.figure(figsize=(14, 7))

        plt.step(
            pd.to_datetime(
                walkforward_parameters["test_start"]
            ),
            walkforward_parameters[parameter_name],
            where="post",
            linewidth=1.8,
        )

        plt.title(
            f"{config.experiment_id} — "
            f"Walk-Forward {parameter_name}"
        )
        plt.xlabel("Out-of-Sample Date")
        plt.ylabel(parameter_name)
        plt.grid(alpha=0.2)
        plt.tight_layout()
        plt.savefig(
            report_directory / "05_walkforward_parameters.png",
            dpi=140,
            bbox_inches="tight",
        )
        plt.close()

        chart_sections.append(
            (
                "Walk-Forward Parameter Choices",
                "05_walkforward_parameters.png",
            )
        )

    # --------------------------------------------------------
    # Unified trade diagnostics
    # --------------------------------------------------------

    trade_sets: dict[str, pd.DataFrame] = {
        "Fixed parameters": fixed_result.trades,
    }

    if walkforward_result is not None:
        trade_sets["Walk-forward"] = (
            walkforward_result.trades
        )

    # Completed-trade return distribution.
    plt.figure(figsize=(14, 7))

    for test_name, trades in trade_sets.items():
        if trades.empty:
            continue

        plt.hist(
            trades["net_return_percent"],
            bins=45,
            alpha=0.55,
            label=test_name,
        )

    plt.axvline(0, linewidth=1)
    plt.title(
        f"{config.experiment_id} — Completed-Trade Returns"
    )
    plt.xlabel("Net Return per Trade (%)")
    plt.ylabel("Completed Trades")
    plt.grid(alpha=0.2)
    plt.legend()
    plt.tight_layout()
    plt.savefig(
        report_directory
        / "06_trade_return_distribution.png",
        dpi=140,
        bbox_inches="tight",
    )
    plt.close()

    chart_sections.append(
        (
            "Completed-Trade Return Distribution",
            "06_trade_return_distribution.png",
        )
    )

    # Cumulative PnL by completed trade.
    plt.figure(figsize=(14, 7))

    for test_name, trades in trade_sets.items():
        if trades.empty:
            continue

        ordered = trades.sort_values(
            ["exit_time", "trade_id"]
        ).reset_index(drop=True)

        trade_number = np.arange(
            1,
            len(ordered) + 1,
        )

        plt.plot(
            trade_number,
            ordered["pnl_cash"].cumsum(),
            linewidth=1.8,
            label=test_name,
        )

    plt.axhline(0, linewidth=1, linestyle="--")
    plt.title(
        f"{config.experiment_id} — Cumulative PnL by Trade"
    )
    plt.xlabel("Completed Trade Number")
    plt.ylabel("Cumulative PnL")
    plt.grid(alpha=0.2)
    plt.legend()
    plt.tight_layout()
    plt.savefig(
        report_directory
        / "07_cumulative_trade_pnl.png",
        dpi=140,
        bbox_inches="tight",
    )
    plt.close()

    chart_sections.append(
        (
            "Cumulative PnL by Completed Trade",
            "07_cumulative_trade_pnl.png",
        )
    )

    # Rolling trade Profit Factor.
    plt.figure(figsize=(14, 7))

    for test_name, trades in trade_sets.items():
        if trades.empty:
            continue

        ordered = trades.sort_values(
            ["exit_time", "trade_id"]
        ).reset_index(drop=True)

        pnl = ordered["pnl_cash"].astype(float)

        rolling_gains = (
            pnl.clip(lower=0)
            .rolling(
                config.rolling_trade_window,
                min_periods=config.rolling_trade_window,
            )
            .sum()
        )

        rolling_losses = (
            (-pnl.clip(upper=0))
            .rolling(
                config.rolling_trade_window,
                min_periods=config.rolling_trade_window,
            )
            .sum()
        )

        rolling_pf = (
            rolling_gains
            / rolling_losses.replace(0, np.nan)
        )

        plt.plot(
            pd.to_datetime(ordered["exit_time"]),
            rolling_pf,
            linewidth=1.7,
            label=test_name,
        )

    plt.axhline(
        1.0,
        linewidth=1,
        linestyle="--",
        label="PF = 1.0",
    )
    plt.title(
        f"{config.experiment_id} — Rolling "
        f"{config.rolling_trade_window}-Trade Profit Factor"
    )
    plt.xlabel("Trade Exit Date")
    plt.ylabel("Rolling Trade Profit Factor")
    plt.ylim(bottom=0)
    plt.grid(alpha=0.2)
    plt.legend()
    plt.tight_layout()
    plt.savefig(
        report_directory
        / "08_rolling_trade_pf.png",
        dpi=140,
        bbox_inches="tight",
    )
    plt.close()

    chart_sections.append(
        (
            "Rolling Trade Profit Factor",
            "08_rolling_trade_pf.png",
        )
    )

    # Twenty largest completed-trade losses.
    plt.figure(figsize=(14, 7))

    for test_name, trades in trade_sets.items():
        if trades.empty:
            continue

        worst = (
            trades.nsmallest(
                20,
                "net_return_percent",
            )
            .sort_values("net_return_percent")
            .reset_index(drop=True)
        )

        loss_rank = np.arange(
            1,
            len(worst) + 1,
        )

        plt.plot(
            loss_rank,
            worst["net_return_percent"],
            marker="o",
            linewidth=1.5,
            label=test_name,
        )

    plt.axhline(0, linewidth=1)
    plt.title(
        f"{config.experiment_id} — Twenty Largest "
        "Completed-Trade Losses"
    )
    plt.xlabel("Loss Rank")
    plt.ylabel("Net Trade Return (%)")
    plt.grid(alpha=0.2)
    plt.legend()
    plt.tight_layout()
    plt.savefig(
        report_directory
        / "09_largest_losses.png",
        dpi=140,
        bbox_inches="tight",
    )
    plt.close()

    chart_sections.append(
        (
            "Largest Completed-Trade Losses",
            "09_largest_losses.png",
        )
    )

    report_file = report_directory / "report.html"

    return write_research_report(
        report_file=report_file,
        experiment_id=config.experiment_id,
        experiment_name=config.experiment_name,
        market_name=config.market_name,
        timeframe=config.timeframe,
        hypothesis=config.hypothesis,
        effective_oos_start=effective_oos_start,
        oos_end=oos_end,
        lifecycle_stage=format_stage_label(
            lifecycle_record["stage"]
        ),
        lifecycle_reason=str(
            lifecycle_record["stage_reason"]
        ),
        lifecycle_next_action=str(
            lifecycle_record["next_action"]
        ),
        best_parameters=best_parameters,
        fixed_parameters=config.fixed_parameters,
        best_score=best_score,
        mcpt_p_value=mcpt_p_value,
        mcpt_source=mcpt_source,
        summary=summary,
        parameter_stability=(
            parameter_stability_summary
        ),
        diagnostic_summary=diagnostic_summary,
        diagnostic_by_side=diagnostic_by_side,
        chart_sections=chart_sections,
        generated_from_saved_results=False,
    )


# ============================================================
# MAIN RUNNER
# ============================================================

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run one configured quantitative research experiment."
        )
    )

    parser.add_argument(
        "--experiment",
        default="EXP-001",
        help=(
            "Experiment configuration to run, for example "
            "EXP-001 or exp_001."
        ),
    )

    parser.add_argument(
        "--list-experiments",
        action="store_true",
        help="List available experiment configurations and exit.",
    )

    parser.add_argument(
        "--quick",
        action="store_true",
        help=(
            "Use at most 25 MCPT permutations for a fast framework test."
        ),
    )

    parser.add_argument(
        "--skip-mcpt",
        action="store_true",
        help="Skip the Monte Carlo permutation test.",
    )

    parser.add_argument(
        "--mcpt-workers",
        type=int,
        default=0,
        help=(
            "MCPT process workers. 0 selects automatic mode, "
            "1 forces serial mode."
        ),
    )

    parser.add_argument(
        "--mcpt-checkpoint-every",
        type=int,
        default=10,
        help=(
            "Save MCPT progress after this many newly completed "
            "permutations."
        ),
    )

    parser.add_argument(
        "--no-mcpt-resume",
        action="store_true",
        help=(
            "Ignore compatible MCPT checkpoints and start the "
            "requested permutation run from zero."
        ),
    )

    parser.add_argument(
        "--skip-walkforward",
        action="store_true",
        help="Skip walk-forward testing.",
    )

    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()

    if arguments.list_experiments:
        configs = list_experiments()

        if not configs:
            print("No experiment configuration files found.")
        else:
            print("Available experiments")
            print("---------------------")

            for available_config in configs:
                available_lifecycle = (
                    get_experiment_lifecycle(
                        available_config.experiment_id,
                        experiment_name=(
                            available_config.experiment_name
                        ),
                        hypothesis=(
                            available_config.hypothesis
                        ),
                        market_name=(
                            available_config.market_name
                        ),
                        timeframe=(
                            available_config.timeframe
                        ),
                        strategy_name=(
                            available_config.strategy_name
                        ),
                    )
                )

                print(
                    f"{available_config.experiment_id}: "
                    f"{available_config.experiment_name} | "
                    f"{format_stage_label(
                        available_lifecycle.stage
                    )}"
                )

        return

    config = load_experiment(arguments.experiment)

    lifecycle = get_experiment_lifecycle(
        config.experiment_id,
        experiment_name=config.experiment_name,
        hypothesis=config.hypothesis,
        market_name=config.market_name,
        timeframe=config.timeframe,
        strategy_name=config.strategy_name,
    )

    assert_full_research_allowed(
        config,
        lifecycle,
    )

    lifecycle_record = lifecycle.to_dict()

    run_id, run_started_at_utc = (
        utc_run_identity()
    )

    data_file_path = resolve_project_path(
        config.data_file
    )

    if not data_file_path.exists():
        raise FileNotFoundError(
            f"Market data file was not found:\n"
            f"{data_file_path}"
        )

    data_file_sha256 = sha256_file(
        data_file_path
    )

    code_fingerprint = (
        combined_code_fingerprint(
            PROJECT_DIR,
            (
                "run_research_lab.py",
                "research_report_ui.py",
                "mcpt_engine.py",
                "run_provenance.py",
                "strategy_registry.py",
                "research_access_control.py",
                "trade_engine.py",
                "bar_permute.py",
                "donchian.py",
            ),
        )
    )

    git_information = git_state(
        PROJECT_DIR
    )

    environment_information = (
        runtime_environment()
    )

    config_fingerprint = (
        configuration_fingerprint(config)
    )

    results_directory = (
        resolve_project_path(config.results_folder)
        / config.experiment_id
    )

    report_directory = (
        resolve_project_path(config.reports_folder)
        / f"{config.experiment_id}-research-lab"
    )

    results_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    report_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    run_directory = (
        results_directory
        / "runs"
        / run_id
    )

    run_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    print()
    print("==============================================")
    print(f"Experiment: {config.experiment_id}")
    print(f"Name:       {config.experiment_name}")
    print(f"Strategy:   {config.strategy_name}")
    print(f"Market:     {config.market_name}")
    print(
        f"Stage:      "
        f"{format_stage_label(lifecycle.stage)}"
    )
    print(f"Run ID:     {run_id}")
    print(
        f"Git commit: "
        f"{git_information.get('short_commit') or 'Unavailable'}"
    )
    print(
        f"Git dirty:  "
        f"{git_information.get('working_tree_dirty')}"
    )
    print(
        f"Next action: {lifecycle.next_action}"
    )
    print("==============================================")
    print()

    (
        research_data,
        in_sample_data,
        out_of_sample_data,
        effective_oos_start,
    ) = load_market_data(config)

    requested_oos_start = pd.Timestamp(
        config.out_of_sample_start
    )

    if effective_oos_start > requested_oos_start:
        print(
            "Effective out-of-sample start was moved forward "
            "to provide the full walk-forward training window:"
        )
        print(f"Requested: {requested_oos_start}")
        print(f"Effective: {effective_oos_start}")
        print()

    gap_count = int(
        (
            research_data.index
            .to_series()
            .diff()
            > pd.Timedelta(config.timeframe)
        ).sum()
    ) if config.timeframe in {
        "1 hour",
        "1h",
    } else np.nan

    print(
        f"In-sample rows:     {len(in_sample_data):,}"
    )
    print(
        f"Out-of-sample rows: {len(out_of_sample_data):,}"
    )

    if not np.isnan(gap_count):
        print(
            f"Detected time gaps: {int(gap_count):,}"
        )

    print()
    print("Optimizing on the in-sample period...")

    (
        best_parameters,
        best_score,
        optimization_table,
    ) = optimize_strategy(
        in_sample_data,
        config,
    )

    print(f"Best parameters: {best_parameters}")
    print(
        f"Best in-sample bar PF: {best_score:.4f}"
    )
    print(
        f"Configured fixed parameters: "
        f"{config.fixed_parameters}"
    )

    optimization_table.to_csv(
        results_directory / "optimization.csv",
        index=False,
    )

    strategy_definition = get_strategy(
        config.strategy_name
    )

    parameter_analysis = (
        analyze_parameter_stability(
            optimization_table=optimization_table,
            parameter_names=(
                strategy_definition.parameter_names
            ),
            best_parameters=best_parameters,
        )
    )

    parameter_analysis.detail.to_csv(
        results_directory
        / "parameter_stability_detail.csv",
        index=False,
    )

    (
        results_directory
        / "parameter_stability_summary.json"
    ).write_text(
        json.dumps(
            json_ready(
                parameter_analysis.summary
            ),
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print("========== PARAMETER SURFACE ==========")
    print(
        "Edge assessment: "
        + parameter_analysis.summary[
            "edge_assessment"
        ].replace("_", " ").title()
    )
    print(
        "Local surface:   "
        + parameter_analysis.summary[
            "local_surface_assessment"
        ].replace("_", " ").title()
    )
    print(
        "PF >= 1.0:       "
        f"{parameter_analysis.summary['break_even_count']}"
        "/"
        f"{parameter_analysis.summary['valid_combinations']}"
    )
    print(
        "Within 95% best: "
        f"{parameter_analysis.summary['near_best_count']}"
        "/"
        f"{parameter_analysis.summary['valid_combinations']}"
    )

    print()
    print("Running fixed-parameter completed-trade backtest...")

    fixed_result = run_fixed_backtest(
        research_data,
        out_of_sample_data,
        config,
    )

    save_backtest_files(
        "fixed",
        fixed_result,
        results_directory,
    )

    print()
    print("Running standard benchmarks...")

    benchmark_results = run_standard_benchmarks(
        out_of_sample_data,
        config,
    )

    save_backtest_files(
        "buy_hold",
        benchmark_results["Buy and Hold"],
        results_directory,
    )

    save_backtest_files(
        "cash",
        benchmark_results["Cash"],
        results_directory,
    )

    walkforward_result: BacktestResult | None = None
    walkforward_parameters: pd.DataFrame | None = None

    should_run_walkforward = (
        config.run_walkforward
        and not arguments.skip_walkforward
    )

    if should_run_walkforward:
        print()
        print("Running walk-forward optimization...")

        (
            walkforward_result,
            walkforward_parameters,
        ) = run_walkforward_backtest(
            research_data,
            out_of_sample_data,
            config,
        )

        save_backtest_files(
            "walkforward",
            walkforward_result,
            results_directory,
        )

        walkforward_parameters.to_csv(
            results_directory
            / "walkforward_parameters.csv",
            index=False,
        )

    mcpt_results: pd.DataFrame | None = None
    mcpt_p_value: float | None = None
    better_or_equal: int | None = None
    mcpt_permutations_used: int | None = None
    mcpt_execution_info: McptExecutionInfo | None = None
    mcpt_source = "disabled"

    mcpt_signature = mcpt_base_signature(
        config=config,
        data_file_sha256=data_file_sha256,
        code_fingerprint=code_fingerprint,
    )

    should_run_mcpt = (
        config.run_mcpt
        and not arguments.skip_mcpt
    )

    if should_run_mcpt:
        permutations = config.mcpt_permutations

        if arguments.quick:
            permutations = min(
                permutations,
                25,
            )

        (
            mcpt_results,
            mcpt_p_value,
            better_or_equal,
            mcpt_execution_info,
        ) = run_mcpt(
            in_sample_data,
            config,
            permutations,
            requested_workers=(
                arguments.mcpt_workers
            ),
            checkpoint_directory=(
                results_directory
                / "mcpt_checkpoint"
            ),
            checkpoint_every=(
                arguments.mcpt_checkpoint_every
            ),
            resume=(
                not arguments.no_mcpt_resume
            ),
            checkpoint_signature=(
                mcpt_signature
            ),
        )

        cache_metadata = save_mcpt_cache(
            results_directory=results_directory,
            results=mcpt_results,
            p_value=mcpt_p_value,
            better_or_equal=better_or_equal,
            permutations=permutations,
            configured_full_permutations=(
                config.mcpt_permutations
            ),
            base_signature=mcpt_signature,
            real_score=best_score,
        )

        mcpt_permutations_used = permutations
        mcpt_source = (
            f"{cache_metadata['cache_kind']}_run"
        )

    elif config.run_mcpt:
        (
            cached_results,
            cached_metadata,
        ) = load_compatible_mcpt_cache(
            results_directory=results_directory,
            base_signature=mcpt_signature,
        )

        if (
            cached_results is not None
            and cached_metadata is not None
        ):
            mcpt_results = cached_results
            mcpt_p_value = float(
                cached_metadata["p_value"]
            )
            better_or_equal = int(
                cached_metadata[
                    "better_or_equal"
                ]
            )
            mcpt_permutations_used = int(
                cached_metadata["permutations"]
            )
            mcpt_source = (
                "cached_"
                + str(
                    cached_metadata[
                        "cache_kind"
                    ]
                )
            )

            print()
            print(
                "Using compatible cached MCPT result: "
                f"{mcpt_source} "
                f"({mcpt_permutations_used:,} permutations)"
            )
        else:
            mcpt_source = (
                "skipped_no_compatible_cache"
            )

            print()
            print(
                "MCPT was skipped and no compatible "
                "provenance-verified cache was found."
            )

    summary_rows = [
        summary_row(
            "Fixed parameters",
            fixed_result,
        )
    ]

    if walkforward_result is not None:
        summary_rows.append(
            summary_row(
                "Walk-forward",
                walkforward_result,
            )
        )

    summary_rows.extend(
        [
            summary_row(
                "Buy and Hold",
                benchmark_results["Buy and Hold"],
            ),
            summary_row(
                "Cash",
                benchmark_results["Cash"],
            ),
        ]
    )

    summary = pd.DataFrame(
        summary_rows
    ).set_index("test")

    summary.to_csv(
        results_directory / "summary.csv"
    )

    diagnostic_rows: list[dict[str, Any]] = []
    diagnostic_side_frames: list[pd.DataFrame] = []
    diagnostic_streak_frames: list[pd.DataFrame] = []

    diagnostic_tests: list[
        tuple[str, BacktestResult]
    ] = [
        ("Fixed parameters", fixed_result),
    ]

    if walkforward_result is not None:
        diagnostic_tests.append(
            ("Walk-forward", walkforward_result)
        )

    for test_name, result in diagnostic_tests:
        diagnostics = calculate_trade_diagnostics(
            result.trades
        )

        diagnostic_rows.append(
            {
                "test": test_name,
                **diagnostics.summary,
            }
        )

        side_table = diagnostics.by_side.copy()

        if not side_table.empty:
            side_table.insert(
                0,
                "test",
                test_name,
            )
            diagnostic_side_frames.append(
                side_table
            )

        streak_table = diagnostics.streaks.copy()

        if not streak_table.empty:
            streak_table.insert(
                0,
                "test",
                test_name,
            )
            diagnostic_streak_frames.append(
                streak_table
            )

    diagnostic_summary = pd.DataFrame(
        diagnostic_rows
    ).set_index("test")

    diagnostic_by_side = (
        pd.concat(
            diagnostic_side_frames,
            ignore_index=True,
        )
        if diagnostic_side_frames
        else pd.DataFrame()
    )

    diagnostic_streaks = (
        pd.concat(
            diagnostic_streak_frames,
            ignore_index=True,
        )
        if diagnostic_streak_frames
        else pd.DataFrame()
    )

    diagnostic_summary.to_csv(
        results_directory
        / "trade_diagnostics_summary.csv"
    )

    diagnostic_by_side.to_csv(
        results_directory
        / "trade_diagnostics_by_side.csv",
        index=False,
    )

    diagnostic_streaks.to_csv(
        results_directory
        / "trade_streaks.csv",
        index=False,
    )

    metadata = {
        "run_id": run_id,
        "run_started_at_utc": run_started_at_utc,
        "run_mode": (
            "quick"
            if arguments.quick
            else "standard"
        ),
        "cli_options": {
            "experiment": arguments.experiment,
            "quick": arguments.quick,
            "skip_mcpt": arguments.skip_mcpt,
            "mcpt_workers": arguments.mcpt_workers,
            "mcpt_checkpoint_every": (
                arguments.mcpt_checkpoint_every
            ),
            "mcpt_resume": (
                not arguments.no_mcpt_resume
            ),
            "skip_walkforward": (
                arguments.skip_walkforward
            ),
        },
        "git": git_information,
        "runtime_environment": (
            environment_information
        ),
        "data_file": str(data_file_path),
        "data_file_sha256": data_file_sha256,
        "code_fingerprint": code_fingerprint,
        "configuration_fingerprint": (
            config_fingerprint
        ),
        "research_lifecycle": lifecycle_record,
        "config": json_ready(asdict(config)),
        "effective_oos_start": effective_oos_start,
        "effective_oos_end": out_of_sample_data.index.max(),
        "in_sample_rows": len(in_sample_data),
        "out_of_sample_rows": len(out_of_sample_data),
        "best_in_sample_parameters": best_parameters,
        "best_in_sample_bar_profit_factor": best_score,
        "parameter_stability": (
            parameter_analysis.summary
        ),
        "configured_fixed_parameters": (
            config.fixed_parameters
        ),
        "mcpt_p_value": mcpt_p_value,
        "mcpt_better_or_equal": better_or_equal,
        "mcpt_permutations_used": (
            mcpt_permutations_used
        ),
        "mcpt_source": mcpt_source,
        "mcpt_signature": mcpt_signature,
        "mcpt_execution": (
            mcpt_execution_info.to_dict()
            if mcpt_execution_info is not None
            else None
        ),
        "quick_mode": arguments.quick,
        "walkforward_ran": (
            walkforward_result is not None
        ),
        "mcpt_ran": mcpt_results is not None,
        "benchmarks": {
            benchmark_name: {
                "total_return_percent": (
                    benchmark_result.summary[
                        "total_return_percent"
                    ]
                ),
                "max_drawdown_percent": (
                    benchmark_result.summary[
                        "max_drawdown_percent"
                    ]
                ),
                "trade_profit_factor": (
                    benchmark_result.summary[
                        "trade_profit_factor"
                    ]
                ),
                "total_trades": (
                    benchmark_result.summary[
                        "total_trades"
                    ]
                ),
            }
            for (
                benchmark_name,
                benchmark_result,
            ) in benchmark_results.items()
        },
    }

    metadata_text = json.dumps(
        json_ready(metadata),
        indent=2,
    )

    (
        results_directory
        / "run_metadata.json"
    ).write_text(
        metadata_text,
        encoding="utf-8",
    )

    (
        run_directory
        / "run_metadata.json"
    ).write_text(
        metadata_text,
        encoding="utf-8",
    )

    append_run_history(
        history_file=(
            results_directory
            / "run_history.csv"
        ),
        row={
            "run_id": run_id,
            "started_at_utc": (
                run_started_at_utc
            ),
            "experiment_id": (
                config.experiment_id
            ),
            "research_stage": lifecycle.stage,
            "research_next_action": (
                lifecycle.next_action
            ),
            "git_commit": (
                git_information.get("commit")
            ),
            "git_dirty": (
                git_information.get(
                    "working_tree_dirty"
                )
            ),
            "configuration_fingerprint": (
                config_fingerprint
            ),
            "data_file_sha256": (
                data_file_sha256
            ),
            "code_fingerprint": (
                code_fingerprint
            ),
            "quick_mode": arguments.quick,
            "walkforward_ran": (
                walkforward_result is not None
            ),
            "mcpt_source": mcpt_source,
            "mcpt_permutations": (
                mcpt_permutations_used
            ),
            "mcpt_p_value": mcpt_p_value,
            "parameter_edge_assessment": (
                parameter_analysis.summary[
                    "edge_assessment"
                ]
            ),
            "parameter_surface_assessment": (
                parameter_analysis.summary[
                    "local_surface_assessment"
                ]
            ),
            "parameter_break_even_share": (
                parameter_analysis.summary[
                    "break_even_share"
                ]
            ),
            "parameter_near_best_share": (
                parameter_analysis.summary[
                    "near_best_share"
                ]
            ),
            "fixed_return_percent": (
                fixed_result.summary[
                    "total_return_percent"
                ]
            ),
            "fixed_trade_profit_factor": (
                fixed_result.summary[
                    "trade_profit_factor"
                ]
            ),
            "walkforward_return_percent": (
                walkforward_result.summary[
                    "total_return_percent"
                ]
                if walkforward_result
                is not None
                else None
            ),
            "walkforward_trade_profit_factor": (
                walkforward_result.summary[
                    "trade_profit_factor"
                ]
                if walkforward_result
                is not None
                else None
            ),
        },
    )

    report_file = create_visual_report(
        config=config,
        report_directory=report_directory,
        summary=summary,
        optimization_table=optimization_table,
        best_parameters=best_parameters,
        best_score=best_score,
        parameter_stability_summary=(
            parameter_analysis.summary
        ),
        lifecycle_record=lifecycle_record,
        fixed_result=fixed_result,
        walkforward_result=walkforward_result,
        benchmark_results=benchmark_results,
        walkforward_parameters=walkforward_parameters,
        mcpt_results=mcpt_results,
        mcpt_p_value=mcpt_p_value,
        mcpt_source=mcpt_source,
        diagnostic_summary=diagnostic_summary,
        diagnostic_by_side=diagnostic_by_side,
        effective_oos_start=effective_oos_start,
        oos_end=out_of_sample_data.index.max(),
    )

    print()
    print("================ RESULTS ================")
    print(
        summary[
            [
                "total_return_percent",
                "max_drawdown_percent",
                "total_trades",
                "win_rate_percent",
                "trade_profit_factor",
                "average_trade_percent",
            ]
        ]
        .round(3)
        .to_string()
    )

    print()
    print("============== BENCHMARK CONTEXT =============")
    print(
        f"Fixed excess vs Buy and Hold: "
        f"{(
            fixed_result.summary['total_return_percent']
            - benchmark_results['Buy and Hold'].summary[
                'total_return_percent'
            ]
        ):.3f}%"
    )

    print()
    print("============= TRADE DIAGNOSTICS =============")
    print(
        diagnostic_summary[
            [
                "average_winner_percent",
                "average_loser_percent",
                "payoff_ratio",
                "largest_loss_percent",
                "top_5_loss_share_percent",
                "max_consecutive_losses",
            ]
        ]
        .round(3)
        .to_string()
    )

    print()
    print(
        f"MCPT source:  {mcpt_source}"
    )

    if mcpt_p_value is not None:
        print(
            f"MCPT p-value: {mcpt_p_value:.4f}"
        )

    print()
    print(
        f"Research stage: "
        f"{format_stage_label(lifecycle.stage)}"
    )
    print(f"Results folder: {results_directory}")
    print(f"Run snapshot:   {run_directory}")
    print(f"Visual report:  {report_file}")
    print("=========================================")


if __name__ == "__main__":
    main()
