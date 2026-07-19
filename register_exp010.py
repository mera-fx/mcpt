from __future__ import annotations

import ast
from pathlib import Path

from exp009_tournament_result import verify_local_exp009_tournament_result
from exp010_preregistration import validate_exp010_preregistration
from experiment_lifecycle import get_experiment_lifecycle


PROJECT_DIR = Path(__file__).resolve().parent
LIFECYCLE_FILE = PROJECT_DIR / "experiment_lifecycle.py"


EXP010_BLOCK = r'''

    "EXP-010": ExperimentLifecycle(
        experiment_id="EXP-010",
        experiment_name="NQ/MNQ Opening-Drive Deep Validation",
        hypothesis=(
            "The four locked EXP-009 opening-drive candidates may retain "
            "attractive performance, risk, consistency and cost "
            "characteristics after family-level selection is accounted "
            "for with anchored walk-forward and selection-aware MCPT."
        ),
        stage="PRE_REGISTERED",
        stage_reason=(
            "All four EXP-009 opening-drive candidates, the user-preferred "
            "reference, data, execution, costs, walk-forward procedure, "
            "bootstrap diagnostics, random seeds and selection-aware MCPT "
            "were locked before any EXP-010 result."
        ),
        next_action=(
            "Implement the protected four-candidate validation and commit "
            "it before calculating EXP-010 measurements. Preserve all "
            "EXP-009 results and the prior-family-selection limitation."
        ),
        market_name="NQ / MNQ futures",
        timeframe="5-minute signal / 1-minute execution",
        strategy_name="opening_drive_deep_validation",
        preregistration_file=Path(
            "research/EXP-010_preregistration.md"
        ),
    ),
'''


def _atomic_write(path: Path, text: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def add_exp010_lifecycle(text: str) -> str:
    if '"EXP-010": ExperimentLifecycle(' in text:
        return text

    normalize_start = text.find("\ndef normalize_experiment_id")
    if normalize_start < 0:
        raise RuntimeError("Lifecycle normalize function was not found.")
    registry_end = text.rfind("\n}", 0, normalize_start)
    if registry_end < 0:
        raise RuntimeError("Lifecycle registry ending was not found.")

    updated = text[:registry_end] + EXP010_BLOCK + text[registry_end:]
    ast.parse(updated)
    return updated


def main() -> None:
    validate_exp010_preregistration()
    verify_local_exp009_tournament_result()

    expected_stages = {
        "EXP-005": "ACCEPTED_FOR_PAPER_TESTING",
        "EXP-006": "REJECTED",
        "EXP-007": "REJECTED",
        "EXP-008": "REJECTED",
        "EXP-009": "REVIEW",
    }
    for experiment_id, expected_stage in expected_stages.items():
        actual = get_experiment_lifecycle(experiment_id).stage
        if actual != expected_stage:
            raise RuntimeError(
                f"{experiment_id} must remain {expected_stage}; "
                f"found {actual}."
            )

    original = LIFECYCLE_FILE.read_text(encoding="utf-8")
    updated = add_exp010_lifecycle(original)
    if updated == original:
        print("EXP-010 is already registered.")
    else:
        _atomic_write(LIFECYCLE_FILE, updated)
        print("Registered EXP-010 as PRE_REGISTERED.")

    print("All four EXP-009 opening-drive candidates are locked.")
    print("No EXP-010 result was calculated.")
    print("No paper or live trading is authorized.")


if __name__ == "__main__":
    main()
