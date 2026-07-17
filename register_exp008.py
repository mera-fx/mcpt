from __future__ import annotations

import re
from pathlib import Path

from exp006_optimization_result import (
    verify_local_exp006_optimization_decision,
)
from exp007_replication_result import (
    verify_local_exp007_replication_decision,
)
from exp008_preregistration import (
    validate_exp008_preregistration,
)
from experiment_lifecycle import (
    get_experiment_lifecycle,
)


PROJECT_DIR = Path(__file__).resolve().parent
LIFECYCLE_FILE = (
    PROJECT_DIR / "experiment_lifecycle.py"
)


EXP008_BLOCK = r"""
    "EXP-008": ExperimentLifecycle(
        experiment_id="EXP-008",
        experiment_name=(
            "NQ/MNQ Structured Long-Only ORB "
            "Exit-Geometry Optimization"
        ),
        hypothesis=(
            "A small, structured search over "
            "opening-range length, profit-target "
            "distance and forced-flat time may identify "
            "a stable long-only NQ/MNQ ORB geometry "
            "with stronger post-cost evidence than the "
            "fixed EXP-007 baseline."
        ),
        stage="PRE_REGISTERED",
        stage_reason=(
            "All 27 opening-range, target and time-exit "
            "combinations; candidate-selection rules; "
            "neighbor checks; five anchored folds; "
            "selection-aware 1,000-permutation MCPT; "
            "cost checks and decision gates were locked "
            "before any EXP-008 result was calculated."
        ),
        next_action=(
            "Implement and test the protected 27-candidate "
            "EXP-008 workflow. Commit the implementation "
            "before running it. Do not change the grid, "
            "selection procedure, seed or gates."
        ),
        market_name="NQ / MNQ futures",
        timeframe=(
            "5-minute signal / 1-minute execution"
        ),
        strategy_name=(
            "structured_long_only_orb_exit_geometry"
        ),
        preregistration_file=Path(
            "research/EXP-008_preregistration.md"
        ),
    ),
"""


def _atomic_write(
    path: Path,
    text: str,
) -> None:
    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )
    temporary.write_text(
        text,
        encoding="utf-8",
    )
    temporary.replace(path)


def add_exp008_lifecycle(
    text: str,
) -> str:
    if '"EXP-008": ExperimentLifecycle(' in text:
        return text

    pattern = re.compile(
        r"(?m)^}\s*\n\s*def normalize_experiment_id"
    )
    match = pattern.search(text)

    if match is None:
        raise RuntimeError(
            "The lifecycle registry ending "
            "was not found."
        )

    insertion = (
        EXP008_BLOCK
        + "}\n\n"
        + "def normalize_experiment_id"
    )

    return (
        text[:match.start()]
        + insertion
        + text[match.end():]
    )


def main() -> None:
    validate_exp008_preregistration()

    exp005 = get_experiment_lifecycle(
        "EXP-005"
    )
    exp006 = get_experiment_lifecycle(
        "EXP-006"
    )
    exp007 = get_experiment_lifecycle(
        "EXP-007"
    )

    if (
        exp005.stage
        != "ACCEPTED_FOR_PAPER_TESTING"
    ):
        raise RuntimeError(
            "EXP-005 must remain accepted and frozen."
        )

    if exp006.stage != "REJECTED":
        raise RuntimeError(
            "EXP-006 must remain rejected and frozen."
        )

    if exp007.stage != "REJECTED":
        raise RuntimeError(
            "EXP-007 must be formally closed as "
            "REJECTED before EXP-008 is registered."
        )

    exp006_decision = (
        verify_local_exp006_optimization_decision()
    )
    if (
        exp006_decision["evaluation"]["decision"]
        != "REJECT_EXP006_KEEP_EXP005_CONTROL"
    ):
        raise RuntimeError(
            "Frozen EXP-006 rejection changed."
        )

    exp007_decision = (
        verify_local_exp007_replication_decision()
    )
    if (
        exp007_decision["evaluation"]["decision"]
        != "REJECT_EXP007_PRESERVE_AS_NEGATIVE_RESULT"
    ):
        raise RuntimeError(
            "Frozen EXP-007 rejection changed."
        )

    original = LIFECYCLE_FILE.read_text(
        encoding="utf-8"
    )
    updated = add_exp008_lifecycle(
        original
    )

    if updated == original:
        print(
            "EXP-008 is already registered."
        )
    else:
        _atomic_write(
            LIFECYCLE_FILE,
            updated,
        )
        print(
            "Registered EXP-008 as PRE_REGISTERED."
        )

    print(
        "No EXP-008 strategy result was calculated."
    )
    print(
        "EXP-005, EXP-006 and EXP-007 remain frozen."
    )


if __name__ == "__main__":
    main()
