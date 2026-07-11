from __future__ import annotations

import html
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from exp003_preregistration import (
    get_exp003_preregistration,
    validate_exp003_preregistration,
)
from exp003_quick_screen import (
    evaluate_exp003_quick_screen,
    validate_exp003_config_matches_preregistration,
)
from experiment_config import load_experiment
from experiment_lifecycle import (
    format_stage_label,
    get_experiment_lifecycle,
)
from parameter_analysis import (
    analyze_parameter_stability,
    create_parameter_heatmaps,
)
from run_provenance import (
    append_run_history,
    combined_code_fingerprint,
    configuration_fingerprint,
    git_state,
    mcpt_base_signature,
    runtime_environment,
    save_mcpt_cache,
    sha256_file,
    utc_run_identity,
)
from run_research_lab import (
    build_cost_model,
    json_ready,
    optimize_strategy,
    run_mcpt,
)
from strategy_registry import (
    generate_signal,
    get_strategy,
)
from trade_diagnostics import (
    calculate_trade_diagnostics,
)
from trade_engine import (
    backtest_signal_strategy,
    signal_to_target_position,
)


PROJECT_DIR = Path(__file__).resolve().parent


def resolve_project_path(path: Path) -> Path:
    if path.is_absolute():
        return path

    return PROJECT_DIR / path


def load_exp003_in_sample_data(
    data_file: Path,
    *,
    in_sample_start: str,
    in_sample_end: str,
) -> pd.DataFrame:
    """Load and return only the locked in-sample research period."""

    if not data_file.exists():
        raise FileNotFoundError(
            f"Market data file was not found:\n{data_file}"
        )

    data = pd.read_parquet(data_file)
    data.index = pd.to_datetime(data.index)
    data = data.sort_index()

    required_columns = {
        "open",
        "high",
        "low",
        "close",
    }

    missing = required_columns.difference(
        data.columns
    )

    if missing:
        raise RuntimeError(
            "The dataset is missing required columns: "
            f"{sorted(missing)}"
        )

    if data.index.has_duplicates:
        raise RuntimeError(
            "The dataset contains duplicate timestamps."
        )

    if (
        data[["open", "high", "low", "close"]]
        <= 0
    ).any().any():
        raise RuntimeError(
            "OHLC prices must all be positive."
        )

    start = pd.Timestamp(in_sample_start)
    end = pd.Timestamp(in_sample_end)

    if start >= end:
        raise ValueError(
            "in_sample_start must be before in_sample_end."
        )

    in_sample = data.loc[
        (data.index >= start)
        & (data.index < end),
        ["open", "high", "low", "close"],
    ].copy()

    if in_sample.empty:
        raise RuntimeError(
            "No rows remain in the locked in-sample period."
        )

    if bool((in_sample.index >= end).any()):
        raise RuntimeError(
            "Out-of-sample rows entered the quick-screen dataset."
        )

    return in_sample


def run_fixed_in_sample_backtest(
    data: pd.DataFrame,
    config: Any,
):
    signal = generate_signal(
        config.strategy_name,
        data,
        config.fixed_parameters,
    )

    target = signal_to_target_position(
        signal,
        execution_lag_bars=(
            config.execution_lag_bars
        ),
    )

    return backtest_signal_strategy(
        data,
        target,
        cost_model=build_cost_model(config),
        starting_capital=config.starting_capital,
    )


def format_value(value: Any) -> str:
    if isinstance(value, bool):
        return "PASS" if value else "FAIL"

    if isinstance(value, float):
        if not np.isfinite(value):
            return "N/A"
        return f"{value:.4f}"

    return str(value)


def create_quick_screen_report(
    *,
    report_directory: Path,
    run_id: str,
    config: Any,
    best_parameters: dict[str, Any],
    best_score: float,
    parameter_summary: dict[str, Any],
    fixed_result: Any,
    mcpt_p_value: float,
    evaluation: Any,
    heatmaps: list[tuple[str, str]],
) -> Path:
    report_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    gate_rows = []

    for gate_name, gate in (
        evaluation.gates.items()
    ):
        gate_rows.append(
            "<tr>"
            f"<td>{html.escape(gate_name)}</td>"
            f"<td>{html.escape(format_value(gate['actual']))}</td>"
            f"<td>{html.escape(str(gate['operator']))}</td>"
            f"<td>{html.escape(format_value(gate['threshold']))}</td>"
            f"<td>{'PASS' if gate['passed'] else 'FAIL'}</td>"
            "</tr>"
        )

    heatmap_html = "".join(
        (
            f"<h3>{html.escape(title)}</h3>"
            f"<img src=\"{html.escape(filename)}\" "
            "style=\"max-width:100%;height:auto\">"
        )
        for title, filename in heatmaps
    )

    decision_label = (
        "PASS TO FULL VALIDATION"
        if evaluation.passed
        else "REJECT"
    )

    document = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>EXP-003 Quick Screen</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 32px; color: #222; }}
.container {{ max-width: 1120px; margin: auto; }}
table {{ border-collapse: collapse; width: 100%; margin: 18px 0; }}
th, td {{ border: 1px solid #ccc; padding: 9px; text-align: left; }}
th {{ background: #f0f0f0; }}
.note {{ padding: 14px; border: 1px solid #bbb; background: #fafafa; }}
.decision {{ font-size: 1.5rem; font-weight: bold; }}
code {{ background: #f2f2f2; padding: 2px 5px; }}
</style>
</head>
<body>
<div class="container">
<h1>EXP-003 In-Sample Quick Screen</h1>
<p><strong>Run ID:</strong> {html.escape(run_id)}</p>
<p><strong>Decision:</strong> <span class="decision">{decision_label}</span></p>

<div class="note">
This report used only the locked in-sample period. EXP-003
out-of-sample strategy results were not calculated or displayed.
</div>

<h2>Locked experiment</h2>
<p>{html.escape(config.experiment_name)}</p>
<p><strong>Configured fixed parameters:</strong>
<code>{html.escape(str(config.fixed_parameters))}</code></p>
<p><strong>Best optimized parameters:</strong>
<code>{html.escape(str(best_parameters))}</code></p>

<h2>Quick-screen gates</h2>
<table>
<thead><tr><th>Gate</th><th>Actual</th><th>Rule</th><th>Threshold</th><th>Result</th></tr></thead>
<tbody>{''.join(gate_rows)}</tbody>
</table>

<h2>Key in-sample measurements</h2>
<table>
<tr><th>Best bar Profit Factor</th><td>{best_score:.4f}</td></tr>
<tr><th>Combinations PF ≥ 1</th><td>{parameter_summary['break_even_count']} / {parameter_summary['valid_combinations']}</td></tr>
<tr><th>Neighbour median / best</th><td>{format_value(parameter_summary['neighbor_retention_ratio'])}</td></tr>
<tr><th>Quick MCPT p-value</th><td>{mcpt_p_value:.4f}</td></tr>
<tr><th>Fixed completed trades</th><td>{int(fixed_result.summary['total_trades'])}</td></tr>
<tr><th>Fixed in-sample total return</th><td>{float(fixed_result.summary['total_return_percent']):.3f}%</td></tr>
<tr><th>Fixed in-sample trade PF</th><td>{format_value(float(fixed_result.summary['trade_profit_factor']))}</td></tr>
</table>

<h2>Parameter surface</h2>
<p>{html.escape(parameter_summary['interpretation'])}</p>
{heatmap_html}

<h2>Required next action</h2>
<p>{html.escape(
    get_exp003_preregistration()['quick_screen'][
        'pass_action' if evaluation.passed else 'failure_action'
    ]
)}</p>
</div>
</body>
</html>
"""

    report_file = report_directory / "report.html"
    report_file.write_text(
        document,
        encoding="utf-8",
    )

    return report_file


def main() -> None:
    validate_exp003_preregistration()

    config = load_experiment("EXP-003")
    validate_exp003_config_matches_preregistration(
        config
    )

    lifecycle = get_experiment_lifecycle(
        config.experiment_id,
        experiment_name=config.experiment_name,
        hypothesis=config.hypothesis,
        market_name=config.market_name,
        timeframe=config.timeframe,
        strategy_name=config.strategy_name,
    )

    if lifecycle.stage != "PRE_REGISTERED":
        raise RuntimeError(
            "EXP-003 quick screen requires lifecycle stage "
            f"PRE_REGISTERED, not {lifecycle.stage}."
        )

    results_directory = (
        resolve_project_path(
            config.results_folder
        )
        / "EXP-003"
        / "quick_screen"
    )

    report_directory = (
        resolve_project_path(
            config.reports_folder
        )
        / "EXP-003-quick-screen"
    )

    decision_file = (
        results_directory
        / "quick_screen_decision.json"
    )

    if decision_file.exists():
        raise RuntimeError(
            "EXP-003 quick-screen decision already exists. "
            "Do not rerun the screen or repeatedly inspect new "
            "permutations. Review the existing decision instead:\n"
            f"{decision_file}"
        )

    git_information = git_state(
        PROJECT_DIR
    )

    if git_information.get(
        "working_tree_dirty"
    ) is not False:
        raise RuntimeError(
            "Commit all implementation changes before running "
            "the locked EXP-003 quick screen. Git must report a "
            "clean working tree so the result has an exact code "
            "checkpoint."
        )

    run_id, run_started_at_utc = (
        utc_run_identity()
    )

    results_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    report_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    data_file = resolve_project_path(
        config.data_file
    )

    data_file_sha256 = sha256_file(
        data_file
    )

    code_fingerprint = (
        combined_code_fingerprint(
            PROJECT_DIR,
            (
                "run_exp003_quick_screen.py",
                "exp003_quick_screen.py",
                "exp003_preregistration.py",
                "experiments/exp_003.py",
                "strategy_registry.py",
                "trade_engine.py",
                "parameter_analysis.py",
                "bar_permute.py",
            ),
        )
    )

    in_sample_data = load_exp003_in_sample_data(
        data_file,
        in_sample_start=config.in_sample_start,
        in_sample_end=config.in_sample_end,
    )

    gap_count = int(
        (
            in_sample_data.index
            .to_series()
            .diff()
            > pd.Timedelta("1 hour")
        ).sum()
    )

    print()
    print("==============================================")
    print("EXP-003 LOCKED IN-SAMPLE QUICK SCREEN")
    print(f"Stage:       {format_stage_label(lifecycle.stage)}")
    print(f"Run ID:      {run_id}")
    print(
        "Git commit:  "
        f"{git_information.get('short_commit')}"
    )
    print("Git dirty:   False")
    print("OOS access:  BLOCKED")
    print("==============================================")
    print(f"In-sample rows: {len(in_sample_data):,}")
    print(f"Detected gaps:  {gap_count:,}")

    (
        best_parameters,
        best_score,
        optimization_table,
    ) = optimize_strategy(
        in_sample_data,
        config,
    )

    strategy = get_strategy(
        config.strategy_name
    )

    parameter_analysis = (
        analyze_parameter_stability(
            optimization_table=optimization_table,
            parameter_names=(
                strategy.parameter_names
            ),
            best_parameters=best_parameters,
        )
    )

    fixed_result = run_fixed_in_sample_backtest(
        in_sample_data,
        config,
    )

    quick_permutations = int(
        get_exp003_preregistration()[
            "statistical_plan"
        ]["quick_mcpt_permutations"]
    )

    (
        mcpt_results,
        mcpt_p_value,
        better_or_equal,
    ) = run_mcpt(
        in_sample_data,
        config,
        quick_permutations,
    )

    evaluation = evaluate_exp003_quick_screen(
        best_in_sample_bar_pf=best_score,
        break_even_combination_count=(
            parameter_analysis.summary[
                "break_even_count"
            ]
        ),
        neighbor_retention_ratio=(
            parameter_analysis.summary[
                "neighbor_retention_ratio"
            ]
        ),
        quick_mcpt_p_value=mcpt_p_value,
        fixed_in_sample_completed_trades=int(
            fixed_result.summary[
                "total_trades"
            ]
        ),
    )

    optimization_table.to_csv(
        results_directory / "optimization.csv",
        index=False,
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

    fixed_result.trades.to_csv(
        results_directory
        / "fixed_in_sample_trades.csv",
        index=False,
    )

    fixed_result.equity_curve.to_csv(
        results_directory
        / "fixed_in_sample_equity.csv"
    )

    diagnostics = calculate_trade_diagnostics(
        fixed_result.trades
    )

    pd.DataFrame(
        [diagnostics.summary]
    ).to_csv(
        results_directory
        / "fixed_in_sample_diagnostics.csv",
        index=False,
    )

    mcpt_signature = mcpt_base_signature(
        config=config,
        data_file_sha256=data_file_sha256,
        code_fingerprint=code_fingerprint,
    )

    save_mcpt_cache(
        results_directory=results_directory,
        results=mcpt_results,
        p_value=mcpt_p_value,
        better_or_equal=better_or_equal,
        permutations=quick_permutations,
        configured_full_permutations=(
            config.mcpt_permutations
        ),
        base_signature=mcpt_signature,
        real_score=best_score,
    )

    heatmaps = create_parameter_heatmaps(
        optimization_table=optimization_table,
        parameter_names=(
            strategy.parameter_names
        ),
        best_parameters=best_parameters,
        output_directory=report_directory,
        maximum_slices=16,
    )

    report_file = create_quick_screen_report(
        report_directory=report_directory,
        run_id=run_id,
        config=config,
        best_parameters=best_parameters,
        best_score=best_score,
        parameter_summary=(
            parameter_analysis.summary
        ),
        fixed_result=fixed_result,
        mcpt_p_value=mcpt_p_value,
        evaluation=evaluation,
        heatmaps=heatmaps,
    )

    metadata = {
        "run_id": run_id,
        "run_started_at_utc": (
            run_started_at_utc
        ),
        "run_type": (
            "EXP-003_IN_SAMPLE_QUICK_SCREEN"
        ),
        "out_of_sample_calculated": False,
        "git": git_information,
        "runtime_environment": (
            runtime_environment()
        ),
        "data_file": str(data_file),
        "data_file_sha256": data_file_sha256,
        "code_fingerprint": code_fingerprint,
        "configuration_fingerprint": (
            configuration_fingerprint(config)
        ),
        "config": json_ready(asdict(config)),
        "in_sample_start": (
            in_sample_data.index.min()
        ),
        "in_sample_end": (
            in_sample_data.index.max()
        ),
        "in_sample_rows": len(
            in_sample_data
        ),
        "best_parameters": best_parameters,
        "best_in_sample_bar_pf": best_score,
        "parameter_stability": (
            parameter_analysis.summary
        ),
        "fixed_in_sample_summary": (
            fixed_result.summary
        ),
        "quick_mcpt_permutations": (
            quick_permutations
        ),
        "quick_mcpt_p_value": (
            mcpt_p_value
        ),
        "quick_mcpt_better_or_equal": (
            better_or_equal
        ),
        "evaluation": evaluation.to_dict(),
    }

    (
        results_directory
        / "quick_screen_metadata.json"
    ).write_text(
        json.dumps(
            json_ready(metadata),
            indent=2,
        ),
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
            "git_commit": (
                git_information.get("commit")
            ),
            "data_file_sha256": (
                data_file_sha256
            ),
            "code_fingerprint": (
                code_fingerprint
            ),
            "best_in_sample_bar_pf": (
                best_score
            ),
            "break_even_combinations": (
                parameter_analysis.summary[
                    "break_even_count"
                ]
            ),
            "neighbor_retention_ratio": (
                parameter_analysis.summary[
                    "neighbor_retention_ratio"
                ]
            ),
            "quick_mcpt_p_value": (
                mcpt_p_value
            ),
            "fixed_in_sample_trades": (
                fixed_result.summary[
                    "total_trades"
                ]
            ),
            "decision": evaluation.decision,
        },
    )

    # Write the decision last. Its existence prevents repeated screens.
    decision_file.write_text(
        json.dumps(
            json_ready(
                evaluation.to_dict()
            ),
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print("============== QUICK-SCREEN GATES ==============")

    for gate_name, gate in (
        evaluation.gates.items()
    ):
        result_label = (
            "PASS"
            if gate["passed"]
            else "FAIL"
        )

        print(
            f"{result_label:4} | {gate_name}: "
            f"actual={format_value(gate['actual'])} "
            f"{gate['operator']} "
            f"{format_value(gate['threshold'])}"
        )

    print()
    print("================ DECISION =================")
    print(evaluation.decision)
    print("Out-of-sample results remained locked.")
    print(f"Decision file: {decision_file}")
    print(f"Visual report: {report_file}")
    print("===========================================")


if __name__ == "__main__":
    main()
