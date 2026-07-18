from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import sys
from typing import Iterable

import pandas as pd

from exp006_data import load_exp006_frozen_data
from experiment_lifecycle import get_experiment_lifecycle
from strategy_measurement_report import (
    build_strategy_measurement_report,
    measurement_specs,
    validate_measurement_inputs,
)


PROJECT_DIR = Path(__file__).resolve().parent
MEASUREMENT_RESULTS_DIR = PROJECT_DIR / "results" / "strategy_measurements"


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Rebuild explanatory and visual strategy measurement reports "
            "from frozen EXP-005 through EXP-008 result files."
        )
    )
    parser.add_argument(
        "--preflight",
        action="store_true",
        help="Verify frozen inputs and report configuration without writing reports.",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Open the research dashboard after the reports are rebuilt.",
    )
    parser.add_argument(
        "--experiments",
        nargs="*",
        default=["EXP-005", "EXP-006", "EXP-007", "EXP-008"],
        help="Optional experiment IDs to rebuild.",
    )
    return parser.parse_args()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def protected_input_files(specs: Iterable) -> list[Path]:
    files: list[Path] = []
    for spec in specs:
        for path in (
            spec.decision_file,
            spec.nq_trades_file,
            spec.mnq_trades_file,
            spec.nq_equity_file,
            spec.mnq_equity_file,
            spec.yearly_file,
            spec.cost_file,
            spec.mcpt_file,
            spec.walk_forward_file,
            spec.grid_file,
            spec.bootstrap_file,
            spec.review_file,
        ):
            if path is not None and path.exists():
                files.append(path)
    return sorted(set(files))


def verify_lifecycle() -> None:
    expected = {
        "EXP-005": "ACCEPTED_FOR_PAPER_TESTING",
        "EXP-006": "REJECTED",
        "EXP-007": "REJECTED",
        "EXP-008": "REJECTED",
    }
    for experiment_id, stage in expected.items():
        actual = get_experiment_lifecycle(experiment_id).stage
        if actual != stage:
            raise RuntimeError(
                f"{experiment_id} lifecycle changed: expected {stage}, got {actual}."
            )


def main() -> None:
    arguments = parse_arguments()
    requested = {value.upper() for value in arguments.experiments}
    specs = [
        spec
        for spec in measurement_specs(PROJECT_DIR)
        if spec.experiment_id in requested
    ]
    if not specs:
        raise RuntimeError("No valid experiments were selected.")

    verify_lifecycle()
    for spec in specs:
        validate_measurement_inputs(spec)

    inputs = protected_input_files(specs)
    before = {path: file_sha256(path) for path in inputs}

    frozen = load_exp006_frozen_data()
    if int(frozen.audit.get("included_sessions", 0)) != 1639:
        raise RuntimeError("Frozen EXP-005 combined session count changed.")

    print()
    print("STRATEGY MEASUREMENT REPORT PREFLIGHT")
    print("=====================================")
    print("Experiments:      " + ", ".join(spec.experiment_id for spec in specs))
    print("Source:           saved frozen trades, equity, decisions and diagnostics")
    print("Benchmark:        normalized NQ session-close price path")
    print("Research rerun:   disabled")
    print("Optimization:     disabled")
    print("MCPT/bootstrap:   disabled")
    print("Lifecycle edits:  disabled")
    print("Protected inputs: " + f"{len(inputs):,}")
    print("=====================================")

    if arguments.preflight:
        print("Preflight passed. No report or dashboard file was written.")
        return

    rows = []
    for spec in specs:
        print(f"Building {spec.experiment_id} measurement report...")
        output_dir = PROJECT_DIR / "reports" / f"{spec.experiment_id}-research-lab"
        summary = build_strategy_measurement_report(
            spec=spec,
            benchmark_one_minute=frozen.nq_1m,
            output_dir=output_dir,
            measurement_results_dir=MEASUREMENT_RESULTS_DIR,
        )
        rows.append(summary)

    MEASUREMENT_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    comparison_file = MEASUREMENT_RESULTS_DIR / "strategy_comparison.csv"
    pd.DataFrame(rows).sort_values("experiment_id").to_csv(comparison_file, index=False)

    after = {path: file_sha256(path) for path in inputs}
    changed = [str(path) for path in inputs if before[path] != after[path]]
    if changed:
        raise RuntimeError("Protected result inputs changed: " + ", ".join(changed))

    print("Building the research dashboard...")
    subprocess.run(
        [sys.executable, str(PROJECT_DIR / "build_research_dashboard.py")],
        cwd=PROJECT_DIR,
        check=True,
    )

    dashboard = PROJECT_DIR / "reports" / "research_dashboard" / "index.html"
    print()
    print("Strategy measurement upgrade completed.")
    print(f"Comparison CSV: {comparison_file}")
    print(f"Dashboard:      {dashboard}")
    print("Frozen strategy results and lifecycle decisions were unchanged.")

    if arguments.open:
        if os.name == "nt":
            os.startfile(dashboard)  # type: ignore[attr-defined]
        else:
            print("Automatic opening is supported on Windows only.")


if __name__ == "__main__":
    main()
