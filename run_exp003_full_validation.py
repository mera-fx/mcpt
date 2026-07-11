from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

import pandas as pd

from exp003_full_validation import (
    calculate_profitable_calendar_years,
    evaluate_exp003_full_validation,
)
from exp003_quick_screen_record import (
    validate_exp003_quick_screen_record,
)
from experiment_config import load_experiment
from experiment_lifecycle import (
    get_experiment_lifecycle,
)
from research_access_control import (
    EXP003_FULL_VALIDATION_ENVIRONMENT_KEY,
)
from run_provenance import (
    git_state,
)


PROJECT_DIR = Path(__file__).resolve().parent


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): json_ready(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [
            json_ready(item)
            for item in value
        ]

    if hasattr(value, "item"):
        try:
            return value.item()
        except ValueError:
            pass

    return value


def main() -> None:
    validate_exp003_quick_screen_record()

    config = load_experiment("EXP-003")

    lifecycle = get_experiment_lifecycle(
        "EXP-003"
    )

    if lifecycle.stage != "FULL_VALIDATION":
        raise RuntimeError(
            "EXP-003 protected full validation requires lifecycle "
            f"stage FULL_VALIDATION, not {lifecycle.stage}."
        )

    results_directory = (
        PROJECT_DIR
        / config.results_folder
        / "EXP-003"
    )

    decision_directory = (
        results_directory
        / "full_validation"
    )

    decision_file = (
        decision_directory
        / "full_validation_decision.json"
    )

    if decision_file.exists():
        raise RuntimeError(
            "EXP-003 full-validation decision already exists. "
            "Do not rerun or repeatedly inspect new OOS results. "
            "Review the existing decision instead:\n"
            f"{decision_file}"
        )

    git_information = git_state(
        PROJECT_DIR
    )

    if git_information.get(
        "working_tree_dirty"
    ) is not False:
        raise RuntimeError(
            "Commit and push the FULL_VALIDATION stage update "
            "before revealing EXP-003 out-of-sample results. "
            "Git must report a clean working tree."
        )

    print()
    print("==============================================")
    print("EXP-003 PROTECTED FULL VALIDATION")
    print("OOS disclosure: AUTHORIZED ONCE")
    print(
        "Git commit:    "
        f"{git_information.get('short_commit')}"
    )
    print("==============================================")
    print(
        "Running the locked 1,000-permutation MCPT, fixed OOS "
        "backtest and walk-forward validation..."
    )
    print()

    environment = os.environ.copy()
    environment[
        EXP003_FULL_VALIDATION_ENVIRONMENT_KEY
    ] = "1"

    completed = subprocess.run(
        [
            sys.executable,
            str(
                PROJECT_DIR
                / "run_research_lab.py"
            ),
            "--experiment",
            "EXP-003",
        ],
        cwd=PROJECT_DIR,
        env=environment,
        check=False,
    )

    if completed.returncode != 0:
        raise RuntimeError(
            "The underlying full research run failed. No "
            "full-validation decision was written. Correct the "
            "runtime error without changing locked research rules, "
            "then run this protected wrapper again."
        )

    summary_file = (
        results_directory
        / "summary.csv"
    )

    metadata_file = (
        results_directory
        / "run_metadata.json"
    )

    fixed_equity_file = (
        results_directory
        / "fixed_equity.csv"
    )

    required_files = [
        summary_file,
        metadata_file,
        fixed_equity_file,
    ]

    missing = [
        str(path)
        for path in required_files
        if not path.exists()
    ]

    if missing:
        raise RuntimeError(
            "Full research completed but required evaluation "
            f"files are missing: {missing}"
        )

    summary = pd.read_csv(
        summary_file,
        index_col="test",
    )

    metadata = json.loads(
        metadata_file.read_text(
            encoding="utf-8"
        )
    )

    fixed_equity = pd.read_csv(
        fixed_equity_file,
        index_col=0,
        parse_dates=True,
    )

    (
        profitable_year_count,
        yearly_table,
    ) = calculate_profitable_calendar_years(
        fixed_equity,
        starting_capital=(
            config.starting_capital
        ),
    )

    evaluation = (
        evaluate_exp003_full_validation(
            summary=summary,
            mcpt_p_value=float(
                metadata["mcpt_p_value"]
            ),
            mcpt_permutations=int(
                metadata[
                    "mcpt_permutations_used"
                ]
            ),
            mcpt_source=str(
                metadata["mcpt_source"]
            ),
            profitable_calendar_years=(
                profitable_year_count
            ),
        )
    )

    decision_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    yearly_table.to_csv(
        decision_directory
        / "fixed_oos_calendar_years.csv",
        index=False,
    )

    decision_payload = {
        **evaluation.to_dict(),
        "experiment_id": "EXP-003",
        "source_run_id": metadata.get(
            "run_id"
        ),
        "source_git_commit": (
            metadata.get("git", {})
            .get("commit")
        ),
        "source_report": (
            "reports/EXP-003-research-lab/"
            "report.html"
        ),
        "profitable_calendar_years": (
            profitable_year_count
        ),
    }

    # Decision is deliberately written last.
    decision_file.write_text(
        json.dumps(
            json_ready(decision_payload),
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print("============== FULL VALIDATION ==============")
    print(
        f"Decision: {evaluation.decision}"
    )

    for gate_name, gate in (
        evaluation.gates.items()
    ):
        status = (
            "PASS"
            if gate["passed"]
            else "FAIL"
        )

        print(
            f"{status:4} | {gate_name}: "
            f"{gate['actual']} "
            f"{gate['operator']} "
            f"{gate['threshold']}"
        )

    print()
    print(
        f"Decision file: {decision_file}"
    )
    print(
        "Research report: "
        f"{PROJECT_DIR / config.reports_folder / 'EXP-003-research-lab' / 'report.html'}"
    )
    print("=============================================")


if __name__ == "__main__":
    main()
