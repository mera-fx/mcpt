from __future__ import annotations

import ast
from pathlib import Path

from exp013_validation_result import verify_local_exp013_validation_result
from exp014_preregistration import validate_exp014_preregistration
from experiment_lifecycle import get_experiment_lifecycle


PROJECT_DIR = Path(__file__).resolve().parent
LIFECYCLE_FILE = PROJECT_DIR / "experiment_lifecycle.py"


EXP014_BLOCK = r'''

    "EXP-014": ExperimentLifecycle(
        experiment_id="EXP-014",
        experiment_name=(
            "Finalist Behaviour and Complementarity Study"
        ),
        hypothesis=(
            "The three frozen EXP-013 finalists may exhibit distinct "
            "direction, regime, exit, tail and drawdown behaviour, while "
            "gap fade and premarket continuation may provide complementary "
            "session-level P&L rather than duplicating the same risk."
        ),
        stage="PRE_REGISTERED",
        stage_reason=(
            "The exact three finalists, frozen 2020-2025 data, trade "
            "reconstruction checks, 2025 failure diagnostics, entry-known "
            "regimes, pairwise overlap measures and two unweighted "
            "cross-family research sleeve pairs were locked before any "
            "EXP-014 measurement."
        ),
        next_action=(
            "Implement and commit the protected behaviour study before "
            "reconstructing trades. Preserve all EXP-013 evidence, make "
            "no rule, filter or parameter selection, and do not treat the "
            "arithmetic sleeve pairs as executable portfolios."
        ),
        market_name="NQ / MNQ futures",
        timeframe=(
            "Extended-session context / 5-minute signal / "
            "1-minute execution"
        ),
        strategy_name="finalist_behaviour_and_complementarity",
        preregistration_file=Path(
            "research/EXP-014_preregistration.md"
        ),
    ),
'''


def _atomic_write(path: Path, text: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def add_exp014_lifecycle(text: str) -> str:
    if '"EXP-014": ExperimentLifecycle(' in text:
        return text
    normalize_start = text.find("\ndef normalize_experiment_id")
    if normalize_start < 0:
        raise RuntimeError("Lifecycle normalize function was not found.")
    registry_end = text.rfind("\n}", 0, normalize_start)
    if registry_end < 0:
        raise RuntimeError("Lifecycle registry ending was not found.")
    updated = text[:registry_end] + EXP014_BLOCK + text[registry_end:]
    ast.parse(updated)
    return updated


def main() -> None:
    validate_exp014_preregistration()
    verify_local_exp013_validation_result()
    expected = {
        "EXP-005": "ACCEPTED_FOR_PAPER_TESTING",
        "EXP-006": "REJECTED",
        "EXP-007": "REJECTED",
        "EXP-008": "REJECTED",
        "EXP-009": "REVIEW",
        "EXP-010": "REVIEW",
        "EXP-011": "REVIEW",
        "EXP-012": "REVIEW",
        "EXP-013": "REVIEW",
    }
    for experiment_id, stage in expected.items():
        actual = get_experiment_lifecycle(experiment_id).stage
        if actual != stage:
            raise RuntimeError(
                f"{experiment_id} must remain {stage}; found {actual}."
            )

    original = LIFECYCLE_FILE.read_text(encoding="utf-8")
    updated = add_exp014_lifecycle(original)
    if updated == original:
        print("EXP-014 is already registered.")
    else:
        _atomic_write(LIFECYCLE_FILE, updated)
        print("Registered EXP-014 as PRE_REGISTERED.")

    print("Three EXP-013 finalists remain unchanged.")
    print("Two fixed cross-family research sleeve pairs are locked.")
    print("No strategy, filter, weight or parameter is optimized.")
    print("No EXP-014 measurement was calculated.")
    print("No paper or live trading is authorized.")


if __name__ == "__main__":
    main()
