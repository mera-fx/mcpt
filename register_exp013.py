from __future__ import annotations

import ast
from pathlib import Path

from exp012_tournament_result import verify_local_exp012_tournament_result
from exp013_preregistration import validate_exp013_preregistration
from experiment_lifecycle import get_experiment_lifecycle


PROJECT_DIR = Path(__file__).resolve().parent
LIFECYCLE_FILE = PROJECT_DIR / "experiment_lifecycle.py"


EXP013_BLOCK = r'''

    "EXP-013": ExperimentLifecycle(
        experiment_id="EXP-013",
        experiment_name=(
            "Extended-Context Three-Finalist Deep Validation"
        ),
        hypothesis=(
            "The locked gap-fade and premarket-continuation review "
            "candidates may retain attractive performance, risk and "
            "consistency after temporal testing and a discovery-wide "
            "24-candidate permutation test."
        ),
        stage="PRE_REGISTERED",
        stage_reason=(
            "The three EXP-012 review candidates, their post-result "
            "selection limitations, frozen data, execution, costs, four "
            "anchored folds, bootstrap seed and discovery-wide 24-"
            "candidate MCPT were locked before any EXP-013 result."
        ),
        next_action=(
            "Implement and commit the protected three-finalist validation "
            "before calculating EXP-013 measurements. Preserve EXP-012, "
            "the low-sample warning and the post-selection limitation. "
            "Do not authorize paper or live trading."
        ),
        market_name="NQ / MNQ futures",
        timeframe=(
            "Extended-session context / 5-minute signal / "
            "1-minute execution"
        ),
        strategy_name="extended_context_finalist_validation",
        preregistration_file=Path(
            "research/EXP-013_preregistration.md"
        ),
    ),
'''


def _atomic_write(path: Path, text: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def add_exp013_lifecycle(text: str) -> str:
    if '"EXP-013": ExperimentLifecycle(' in text:
        return text

    normalize_start = text.find("\ndef normalize_experiment_id")
    if normalize_start < 0:
        raise RuntimeError("Lifecycle normalize function was not found.")
    registry_end = text.rfind("\n}", 0, normalize_start)
    if registry_end < 0:
        raise RuntimeError("Lifecycle registry ending was not found.")

    updated = text[:registry_end] + EXP013_BLOCK + text[registry_end:]
    ast.parse(updated)
    return updated


def main() -> None:
    validate_exp013_preregistration()
    verify_local_exp012_tournament_result()

    expected_stages = {
        "EXP-005": "ACCEPTED_FOR_PAPER_TESTING",
        "EXP-006": "REJECTED",
        "EXP-007": "REJECTED",
        "EXP-008": "REJECTED",
        "EXP-009": "REVIEW",
        "EXP-010": "REVIEW",
        "EXP-011": "REVIEW",
        "EXP-012": "REVIEW",
    }
    for experiment_id, expected_stage in expected_stages.items():
        actual = get_experiment_lifecycle(experiment_id).stage
        if actual != expected_stage:
            raise RuntimeError(
                f"{experiment_id} must remain {expected_stage}; "
                f"found {actual}."
            )

    original = LIFECYCLE_FILE.read_text(encoding="utf-8")
    updated = add_exp013_lifecycle(original)
    if updated == original:
        print("EXP-013 is already registered.")
    else:
        _atomic_write(LIFECYCLE_FILE, updated)
        print("Registered EXP-013 as PRE_REGISTERED.")

    print("Three EXP-012 review candidates are locked.")
    print("Primary MCPT will rerun all 24 EXP-012 candidates.")
    print("No EXP-013 result was calculated.")
    print("No paper or live trading is authorized.")


if __name__ == "__main__":
    main()
