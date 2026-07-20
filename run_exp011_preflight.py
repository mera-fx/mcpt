from __future__ import annotations

from pathlib import Path

from exp010_validation_result import verify_local_exp010_validation_result
from exp011_preregistration import (
    get_exp011_preregistration,
    validate_exp011_preregistration,
)
from experiment_lifecycle import get_experiment_lifecycle


PROJECT_DIR = Path(__file__).resolve().parent
RESULT_ROOT = PROJECT_DIR / "results" / "EXP-011"


def main() -> None:
    validate_exp011_preregistration()
    exp010 = verify_local_exp010_validation_result()

    expected_stages = {
        "EXP-005": "ACCEPTED_FOR_PAPER_TESTING",
        "EXP-006": "REJECTED",
        "EXP-007": "REJECTED",
        "EXP-008": "REJECTED",
        "EXP-009": "REVIEW",
        "EXP-010": "REVIEW",
        "EXP-011": "PRE_REGISTERED",
    }
    for experiment_id, expected_stage in expected_stages.items():
        actual = get_experiment_lifecycle(experiment_id).stage
        if actual != expected_stage:
            raise RuntimeError(
                f"{experiment_id} must be {expected_stage}; found {actual}."
            )

    if RESULT_ROOT.exists() and any(
        path.is_file() for path in RESULT_ROOT.rglob("*")
    ):
        raise RuntimeError("EXP-011 result files already exist.")

    record = get_exp011_preregistration()
    sizing = record["sizing_lock"]
    calibration = record["risk_target_calibration"]
    bootstrap = record["paired_bootstrap_diagnostics"]

    print()
    print("EXP-011 POSITION-SIZING PREFLIGHT")
    print("=================================")
    print("Lifecycle: PRE_REGISTERED")
    print("Primary signal: opening_drive_0p5_time")
    print("User reference: opening_drive_0p5_1p5r")
    print("EXP-010 frozen result hash-verified: True")
    print(
        "EXP-010 classification: "
        f"{exp010['evaluation']['classification']}"
    )
    print("Signal variants: 2")
    print(f"Sizing methods: {sizing['method_count']}")
    print("Measurement rows: 6")
    print(
        "Risk-target calibration: "
        f"{record['market_and_data']['calibration_period']}"
    )
    print(
        "Evaluation period: "
        f"{record['market_and_data']['evaluation_period']}"
    )
    print(
        "Target-risk rule: "
        f"{calibration['target_dollar_risk_rule']}"
    )
    print("Target-risk optimization: False")
    print("Equity compounding: False")
    print("Automatic sizing winner: False")
    print("New MCPT: False")
    print(
        "Paired bootstrap: "
        f"{bootstrap['resamples']:,} evaluation-session resamples"
    )
    print("Paper trading authorized: False")
    print("Live trading authorized: False")
    print("EXP-011 results calculated: False")
    print("=================================")
    print("Preflight passed. No EXP-011 sizing result was calculated.")


if __name__ == "__main__":
    main()
