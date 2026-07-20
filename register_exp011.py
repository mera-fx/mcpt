from __future__ import annotations

import ast
from pathlib import Path

from exp010_validation_result import verify_local_exp010_validation_result
from exp011_preregistration import validate_exp011_preregistration
from experiment_lifecycle import get_experiment_lifecycle


PROJECT_DIR = Path(__file__).resolve().parent
LIFECYCLE_FILE = PROJECT_DIR / "experiment_lifecycle.py"


EXP011_BLOCK = r'''

    "EXP-011": ExperimentLifecycle(
        experiment_id="EXP-011",
        experiment_name="NQ/MNQ Opening-Drive Position-Sizing Study",
        hypothesis=(
            "Equal-dollar-risk sizing may reduce variation in initial "
            "trade risk and improve drawdown behaviour without changing "
            "the frozen EXP-010 opening-drive signals."
        ),
        stage="PRE_REGISTERED",
        stage_reason=(
            "The two frozen signal variants, calibration/evaluation "
            "split, risk-target rule, three sizing methods, execution, "
            "costs, paired bootstrap and measurement-first reporting "
            "were locked before any EXP-011 sizing result."
        ),
        next_action=(
            "Implement and commit the protected sizing engine before "
            "calculating results. Preserve both signal variants, show "
            "all six measurements, and make no signal-edge or trading "
            "authorization claim."
        ),
        market_name="NQ / MNQ futures",
        timeframe="5-minute signal / 1-minute execution",
        strategy_name="opening_drive_position_sizing_study",
        preregistration_file=Path(
            "research/EXP-011_preregistration.md"
        ),
    ),
'''


def _atomic_write(path: Path, text: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def add_exp011_lifecycle(text: str) -> str:
    if '"EXP-011": ExperimentLifecycle(' in text:
        return text

    normalize_start = text.find("\ndef normalize_experiment_id")
    if normalize_start < 0:
        raise RuntimeError("Lifecycle normalize function was not found.")
    registry_end = text.rfind("\n}", 0, normalize_start)
    if registry_end < 0:
        raise RuntimeError("Lifecycle registry ending was not found.")

    updated = text[:registry_end] + EXP011_BLOCK + text[registry_end:]
    ast.parse(updated)
    return updated


def main() -> None:
    validate_exp011_preregistration()
    result = verify_local_exp010_validation_result()
    if (
        result["evaluation"]["classification"]
        != "STRONG_HISTORICAL_EVIDENCE"
    ):
        raise RuntimeError(
            "EXP-010 must retain STRONG_HISTORICAL_EVIDENCE."
        )

    expected_stages = {
        "EXP-005": "ACCEPTED_FOR_PAPER_TESTING",
        "EXP-006": "REJECTED",
        "EXP-007": "REJECTED",
        "EXP-008": "REJECTED",
        "EXP-009": "REVIEW",
        "EXP-010": "REVIEW",
    }
    for experiment_id, expected_stage in expected_stages.items():
        actual = get_experiment_lifecycle(experiment_id).stage
        if actual != expected_stage:
            raise RuntimeError(
                f"{experiment_id} must remain {expected_stage}; "
                f"found {actual}."
            )

    original = LIFECYCLE_FILE.read_text(encoding="utf-8")
    updated = add_exp011_lifecycle(original)
    if updated == original:
        print("EXP-011 is already registered.")
    else:
        _atomic_write(LIFECYCLE_FILE, updated)
        print("Registered EXP-011 as PRE_REGISTERED.")

    print("EXP-010 signal rules remain frozen.")
    print("No EXP-011 sizing result was calculated.")
    print("No paper or live trading is authorized.")


if __name__ == "__main__":
    main()
