from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import subprocess
from typing import Any

import numpy as np
import pandas as pd

from exp006_data import load_exp006_frozen_data
from exp009_engine import (
    Exp009Result,
    get_exp009_candidate,
    prepare_exp009_arrays,
    run_exp009_candidate,
)
from exp010_validation_result import (
    load_validation_result,
    verify_local_exp010_validation_result,
)
from exp011_bootstrap import paired_sizing_bootstrap
from exp011_implementation import validate_exp011_implementation
from exp011_measurements import (
    SIGNAL_IDS,
    build_exp011_annual_table,
    build_exp011_measurement_table,
    build_exp011_monthly_table,
)
from exp011_preregistration import (
    get_exp011_preregistration,
    validate_exp011_preregistration,
)
from exp011_report import build_exp011_report
from exp011_sizing import (
    SIZING_IDS,
    Exp011SizedResult,
    apply_locked_sizing,
    calibrate_target_dollar_risk,
)
from experiment_lifecycle import get_experiment_lifecycle


PROJECT_DIR = Path(__file__).resolve().parent
RESULT_DIR = PROJECT_DIR / "results" / "EXP-011" / "position_sizing"
REPORT_DIR = PROJECT_DIR / "reports" / "EXP-011-research-lab"
RESULT_FILE = RESULT_DIR / "sizing_result.json"


def _run_git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=PROJECT_DIR,
        text=True,
        capture_output=True,
        check=True,
    )
    return completed.stdout.strip()


def git_provenance() -> dict[str, Any]:
    commit = _run_git("rev-parse", "HEAD")
    return {
        "commit": commit,
        "short_commit": commit[:7],
        "working_tree_clean": not bool(
            _run_git("status", "--porcelain")
        ),
    }


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return number if math.isfinite(number) else None
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    return value


def _atomic_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(_json_safe(payload), indent=2, allow_nan=False),
        encoding="utf-8",
    )
    temporary.replace(path)


def _verify_lifecycle() -> None:
    expected = {
        "EXP-005": "ACCEPTED_FOR_PAPER_TESTING",
        "EXP-006": "REJECTED",
        "EXP-007": "REJECTED",
        "EXP-008": "REJECTED",
        "EXP-009": "REVIEW",
        "EXP-010": "REVIEW",
        "EXP-011": "PRE_REGISTERED",
    }
    for experiment_id, stage in expected.items():
        actual = get_experiment_lifecycle(experiment_id).stage
        if actual != stage:
            raise RuntimeError(
                f"{experiment_id} must remain {stage}; found {actual}."
            )


def protected_preflight() -> tuple[dict[str, Any], Any]:
    validate_exp011_preregistration()
    validate_exp011_implementation()
    _verify_lifecycle()
    verify_local_exp010_validation_result()
    exp010 = load_validation_result()
    if (
        exp010["evaluation"]["classification"]
        != "STRONG_HISTORICAL_EVIDENCE"
    ):
        raise RuntimeError("Frozen EXP-010 evidence context changed.")

    git = git_provenance()
    if not git["working_tree_clean"]:
        raise RuntimeError(
            "Commit the EXP-011 implementation before preflight or results."
        )
    if RESULT_FILE.exists():
        raise RuntimeError(
            "EXP-011 already has a result. Do not rerun it."
        )
    if RESULT_DIR.exists():
        unexpected = [
            path for path in RESULT_DIR.rglob("*") if path.is_file()
        ]
        if unexpected:
            raise RuntimeError(
                "Unexpected partial EXP-011 output exists: "
                + ", ".join(str(path) for path in unexpected)
            )

    frozen = load_exp006_frozen_data()
    if int(frozen.audit["included_sessions"]) != 1639:
        raise RuntimeError("EXP-011 frozen session count changed.")

    print()
    print("EXP-011 IMPLEMENTATION PREFLIGHT")
    print("================================")
    print("Lifecycle:       PRE_REGISTERED")
    print("Implementation:  IMPLEMENTED_NOT_RUN")
    print("Signals:         2 frozen EXP-010 variants")
    print("Sizing methods:  fixed NQ / fractional NQ / integer MNQ")
    print("Measurement rows: 6")
    print("Calibration:     2019-05-06 through 2020-12-31")
    print("Evaluation:      2021-01-04 through 2025-12-31")
    print("Target rule:     median primary one-NQ initial risk")
    print("Bootstrap:       10,000 paired session resamples")
    print("New MCPT:        disabled")
    print("Automatic winner: False")
    print(f"Git commit:      {git['short_commit']}")
    print("Git clean:       True")
    print("EXP-010 hash-verified: True")
    print("Results:         not calculated")
    print("================================")
    return git, frozen


def _base_results(
    nq_arrays: Any,
    mnq_arrays: Any,
) -> dict[tuple[str, str], Exp009Result]:
    results: dict[tuple[str, str], Exp009Result] = {}
    for signal_id in SIGNAL_IDS:
        candidate = get_exp009_candidate(signal_id)
        results[(signal_id, "NQ")] = run_exp009_candidate(
            nq_arrays,
            candidate,
            symbol="NQ",
            slippage_ticks_per_side=1.0,
        )
        results[(signal_id, "MNQ")] = run_exp009_candidate(
            mnq_arrays,
            candidate,
            symbol="MNQ",
            slippage_ticks_per_side=1.0,
        )
    return results


def _sized_results(
    base: dict[tuple[str, str], Exp009Result],
    *,
    target_dollar_risk_usd: float,
    nq_session_dates: np.ndarray,
    mnq_session_dates: np.ndarray,
) -> dict[tuple[str, str], Exp011SizedResult]:
    if not np.array_equal(nq_session_dates, mnq_session_dates):
        raise RuntimeError(
            "EXP-011 NQ and MNQ frozen session dates do not match."
        )
    results: dict[tuple[str, str], Exp011SizedResult] = {}
    for signal_id in SIGNAL_IDS:
        results[(signal_id, "fixed_one_nq")] = apply_locked_sizing(
            base[(signal_id, "NQ")],
            sizing_id="fixed_one_nq",
            target_dollar_risk_usd=target_dollar_risk_usd,
            evaluation_session_dates=nq_session_dates,
        )
        results[
            (signal_id, "fractional_nq_equal_risk")
        ] = apply_locked_sizing(
            base[(signal_id, "NQ")],
            sizing_id="fractional_nq_equal_risk",
            target_dollar_risk_usd=target_dollar_risk_usd,
            evaluation_session_dates=nq_session_dates,
        )
        results[
            (signal_id, "integer_mnq_equal_risk")
        ] = apply_locked_sizing(
            base[(signal_id, "MNQ")],
            sizing_id="integer_mnq_equal_risk",
            target_dollar_risk_usd=target_dollar_risk_usd,
            evaluation_session_dates=mnq_session_dates,
        )
    return results


def _write_sized_result(result: Exp011SizedResult) -> None:
    directory = (
        RESULT_DIR
        / "rows"
        / result.signal_candidate_id
        / result.sizing_id
    )
    directory.mkdir(parents=True, exist_ok=True)
    result.signals.to_csv(directory / "signals.csv", index=False)
    result.trades.to_csv(directory / "trades.csv", index=False)
    result.equity_curve.to_csv(directory / "equity_curve.csv", index=False)
    result.yearly_results.to_csv(
        directory / "yearly_results.csv", index=False
    )
    result.monthly_results.to_csv(
        directory / "monthly_results.csv", index=False
    )


def run_study() -> None:
    git, frozen = protected_preflight()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    nq_arrays = prepare_exp009_arrays(frozen.nq_1m)
    mnq_arrays = prepare_exp009_arrays(frozen.mnq_1m)

    print()
    print("========== EXP-011 POSITION-SIZING STUDY ==========")
    print("Preparing unchanged EXP-010 signal and execution records...")
    base = _base_results(nq_arrays, mnq_arrays)
    print("Calibrating one target from 2019-2020 primary NQ trades...")
    calibration = calibrate_target_dollar_risk(
        base[("opening_drive_0p5_time", "NQ")]
    )
    print(
        "Frozen target dollar risk: "
        f"${calibration.target_dollar_risk_usd:,.2f}"
    )
    print("Measuring all six locked signal × sizing rows...")
    sized = _sized_results(
        base,
        target_dollar_risk_usd=calibration.target_dollar_risk_usd,
        nq_session_dates=nq_arrays.session_dates,
        mnq_session_dates=mnq_arrays.session_dates,
    )
    measurement_table = build_exp011_measurement_table(sized)
    annual_table = build_exp011_annual_table(sized)
    monthly_table = build_exp011_monthly_table(sized)

    print("Running four paired 10,000-resample diagnostics...")
    bootstrap = []
    for signal_id in SIGNAL_IDS:
        fixed = sized[(signal_id, "fixed_one_nq")]
        bootstrap.append(
            paired_sizing_bootstrap(
                fixed,
                sized[(signal_id, "fractional_nq_equal_risk")],
            )
        )
        bootstrap.append(
            paired_sizing_bootstrap(
                fixed,
                sized[(signal_id, "integer_mnq_equal_risk")],
                comparison_scale_to_nq=1.0,
            )
        )

    exp010 = load_validation_result()
    preregistration = get_exp011_preregistration()
    decision = {
        "schema_version": 1,
        "experiment_id": "EXP-011",
        "result_status": "MEASURED_POSITION_SIZING_STUDY",
        "calculated_at_utc": datetime.now(timezone.utc).isoformat(),
        "git": git,
        "data": {
            "source_experiment": "EXP-005",
            "included_sessions": int(nq_arrays.session_count),
            "historical_start": "2019-05-06",
            "historical_end": "2025-12-31",
            "calibration_period": "2019-05-06 through 2020-12-31",
            "evaluation_period": "2021-01-04 through 2025-12-31",
            "fingerprints": frozen.audit["fingerprints"],
            "new_data_cleaning_decisions": 0,
        },
        "calibration": calibration.to_dict(),
        "results": measurement_table.to_dict(orient="records"),
        "paired_bootstrap": bootstrap,
        "signal_context": {
            "source_experiment": "EXP-010",
            "classification": exp010["evaluation"]["classification"],
            "exp010_selection_aware_mcpt_p_value": exp010["mcpt"][
                "selection_aware_p_value"
            ],
            "hash_verified": True,
            "context_only": True,
        },
        "research_interpretation": {
            "automatic_sizing_winner": False,
            "composite_score": False,
            "pass_fail_gate": False,
            "new_signal_edge_test": False,
            "new_mcpt": False,
            "independent_confirmation": False,
            "historical_status": preregistration[
                "relationship_to_exp010"
            ]["historical_status"],
        },
        "paper_trading_authorized": False,
        "live_trading_authorized": False,
        "automatic_lifecycle_source_edit": False,
    }

    measurement_table.to_csv(
        RESULT_DIR / "measurement_summary.csv", index=False
    )
    annual_table.to_csv(RESULT_DIR / "annual_results.csv", index=False)
    monthly_table.to_csv(RESULT_DIR / "monthly_results.csv", index=False)
    _atomic_json(
        calibration.to_dict(), RESULT_DIR / "calibration.json"
    )
    _atomic_json(
        {"diagnostics": bootstrap},
        RESULT_DIR / "paired_bootstrap.json",
    )
    for result in sized.values():
        _write_sized_result(result)
    report = build_exp011_report(
        decision=_json_safe(decision),
        calibration=calibration,
        results=sized,
        measurement_table=measurement_table,
        bootstrap=bootstrap,
        nq_arrays=nq_arrays,
        output_dir=REPORT_DIR,
    )
    _atomic_json(decision, RESULT_FILE)

    print()
    print("EXP-011 position-sizing study completed.")
    print(f"Target dollar risk: ${calibration.target_dollar_risk_usd:,.2f}")
    print("Measurement rows: 6/6")
    print("Automatic sizing winner: False")
    print("New signal edge test or MCPT: False")
    print(f"Result: {RESULT_FILE}")
    print(f"Report: {report}")
    print("No paper or live trading is authorized.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Protected EXP-011 position-sizing study."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--preflight",
        action="store_true",
        help="Verify the committed implementation without results.",
    )
    mode.add_argument(
        "--run",
        action="store_true",
        help="Run the one-time protected position-sizing study.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.preflight:
        protected_preflight()
        print()
        print(
            "Preflight passed. No EXP-011 calibration, sizing, "
            "bootstrap or report result was calculated."
        )
        return
    run_study()


if __name__ == "__main__":
    main()
