from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import pandas as pd

from experiment_lifecycle import (
    format_stage_label,
    get_experiment_lifecycle,
)
from research_report_ui import write_research_report


PROJECT_DIR = Path(__file__).resolve().parent

KNOWN_CHART_TITLES = {
    "01_equity.png": "Out-of-Sample Equity",
    "02_drawdown.png": "Out-of-Sample Drawdown",
    "03_parameter_search.png": "In-Sample Parameter Search",
    "04_mcpt.png": "Monte Carlo Permutation Test",
    "05_walkforward_parameters.png": "Walk-Forward Parameter Choices",
    "06_trade_return_distribution.png": (
        "Completed-Trade Return Distribution"
    ),
    "07_cumulative_trade_pnl.png": (
        "Cumulative PnL by Completed Trade"
    ),
    "08_rolling_trade_pf.png": (
        "Rolling Trade Profit Factor"
    ),
    "09_largest_losses.png": (
        "Largest Completed-Trade Losses"
    ),
}


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(
            f"Required file was not found: {path}"
        )

    return json.loads(
        path.read_text(encoding="utf-8")
    )


def _read_optional_csv(
    path: Path,
    *,
    index_col: str | int | None = None,
) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(
            path,
            index_col=index_col,
        )
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def _humanize_chart_filename(
    filename: str,
) -> str:
    stem = Path(filename).stem

    while stem and stem[0].isdigit():
        stem = stem[1:]

    stem = stem.lstrip("_-")

    return stem.replace("_", " ").title()


def discover_chart_sections(
    report_directory: Path,
) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []

    for path in sorted(
        report_directory.glob("*.png")
    ):
        title = KNOWN_CHART_TITLES.get(
            path.name,
            _humanize_chart_filename(path.name),
        )

        sections.append(
            (title, path.name)
        )

    return sections


def rebuild_report(
    experiment_id: str,
) -> Path:
    normalized_id = experiment_id.upper().replace(
        "_",
        "-",
    )

    results_directory = (
        PROJECT_DIR
        / "results"
        / normalized_id
    )

    metadata = _load_json(
        results_directory
        / "run_metadata.json"
    )

    config = metadata.get("config", {})

    report_root = Path(
        config.get(
            "reports_folder",
            "reports",
        )
    )

    if not report_root.is_absolute():
        report_root = PROJECT_DIR / report_root

    report_directory = (
        report_root
        / f"{normalized_id}-research-lab"
    )

    report_file = (
        report_directory / "report.html"
    )

    summary = pd.read_csv(
        results_directory / "summary.csv",
        index_col="test",
    )

    diagnostic_summary = _read_optional_csv(
        results_directory
        / "trade_diagnostics_summary.csv",
        index_col="test",
    )

    diagnostic_by_side = _read_optional_csv(
        results_directory
        / "trade_diagnostics_by_side.csv",
    )

    parameter_stability = _load_json(
        results_directory
        / "parameter_stability_summary.json"
    )

    lifecycle = get_experiment_lifecycle(
        normalized_id
    )

    chart_sections = discover_chart_sections(
        report_directory
    )

    return write_research_report(
        report_file=report_file,
        experiment_id=str(
            config.get(
                "experiment_id",
                normalized_id,
            )
        ),
        experiment_name=str(
            config.get(
                "experiment_name",
                normalized_id,
            )
        ),
        market_name=str(
            config.get(
                "market_name",
                "Unknown market",
            )
        ),
        timeframe=str(
            config.get(
                "timeframe",
                "Unknown timeframe",
            )
        ),
        hypothesis=str(
            config.get(
                "hypothesis",
                "No hypothesis recorded.",
            )
        ),
        effective_oos_start=(
            metadata.get(
                "effective_oos_start",
                config.get(
                    "out_of_sample_start",
                    "Unknown",
                ),
            )
        ),
        oos_end=(
            metadata.get(
                "effective_oos_end",
                config.get(
                    "out_of_sample_end",
                    "Unknown",
                ),
            )
        ),
        lifecycle_stage=format_stage_label(
            lifecycle.stage
        ),
        lifecycle_reason=lifecycle.stage_reason,
        lifecycle_next_action=(
            lifecycle.next_action
        ),
        best_parameters=dict(
            metadata.get(
                "best_in_sample_parameters",
                {},
            )
        ),
        fixed_parameters=dict(
            metadata.get(
                "configured_fixed_parameters",
                config.get(
                    "fixed_parameters",
                    {},
                ),
            )
        ),
        best_score=metadata.get(
            "best_in_sample_bar_profit_factor"
        ),
        mcpt_p_value=metadata.get(
            "mcpt_p_value"
        ),
        mcpt_source=str(
            metadata.get(
                "mcpt_source",
                "saved_results",
            )
        ),
        summary=summary,
        parameter_stability=(
            parameter_stability
        ),
        diagnostic_summary=(
            diagnostic_summary
        ),
        diagnostic_by_side=(
            diagnostic_by_side
        ),
        chart_sections=chart_sections,
        generated_from_saved_results=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Rebuild a responsive research report from saved "
            "result files without rerunning research."
        )
    )

    parser.add_argument(
        "--experiment",
        default="EXP-003",
        help="Experiment ID, for example EXP-003.",
    )

    parser.add_argument(
        "--open",
        action="store_true",
        help="Open the rebuilt report in the default browser.",
    )

    arguments = parser.parse_args()

    report_file = rebuild_report(
        arguments.experiment
    )

    print()
    print("RESEARCH REPORT REBUILT")
    print("=======================")
    print(
        f"Experiment: {arguments.experiment.upper()}"
    )
    print("Research rerun: NO")
    print(f"Report: {report_file}")

    if arguments.open:
        if os.name == "nt":
            os.startfile(report_file)
        else:
            print(
                "Automatic browser opening is supported "
                "on Windows."
            )


if __name__ == "__main__":
    main()
