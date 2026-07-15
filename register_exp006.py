from __future__ import annotations

import re
from pathlib import Path

from exp006_preregistration import (
    validate_exp006_preregistration,
)
from experiment_lifecycle import (
    get_experiment_lifecycle,
)


PROJECT_DIR = Path(__file__).resolve().parent
LIFECYCLE_FILE = (
    PROJECT_DIR / "experiment_lifecycle.py"
)


EXP006_BLOCK = r'''
"EXP-006": ExperimentLifecycle(
    experiment_id="EXP-006",
    experiment_name=(
        "NQ/MNQ Structured ORB Optimization"
    ),
    hypothesis=(
        "A small, structured set of opening-range "
        "length, final-entry time and direction "
        "choices may improve risk-adjusted NQ/MNQ "
        "ORB performance without a large parameter "
        "search."
    ),
    stage="PRE_REGISTERED",
    stage_reason=(
        "The exact 27-combination grid, anchored "
        "walk-forward process, stability rules, "
        "selection-aware 1,000-permutation MCPT and "
        "decision gates were locked before any "
        "EXP-006 result was calculated."
    ),
    next_action=(
        "Implement and test the protected EXP-006 "
        "optimizer. Commit the implementation before "
        "running it. Keep EXP-005 frozen as the "
        "paper-testing control."
    ),
    market_name="NQ / MNQ futures",
    timeframe="5 minutes",
    strategy_name=(
        "structured_opening_range_breakout"
    ),
    preregistration_file=Path(
        "research/EXP-006_preregistration.md"
    ),
),
'''


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


def add_exp006_lifecycle(
    text: str,
) -> str:
    if '"EXP-006": ExperimentLifecycle(' in text:
        return text

    pattern = re.compile(
        r"(?m)^}\s*\n\s*def normalize_experiment_id"
    )
    match = pattern.search(text)

    if match is None:
        raise RuntimeError(
            "The lifecycle registry ending was not found."
        )

    insertion = (
        EXP006_BLOCK
        + "}\n\n"
        + "def normalize_experiment_id"
    )

    return (
        text[:match.start()]
        + insertion
        + text[match.end():]
    )


def main() -> None:
    validate_exp006_preregistration()

    exp005 = get_experiment_lifecycle(
        "EXP-005"
    )

    if (
        exp005.stage
        != "ACCEPTED_FOR_PAPER_TESTING"
    ):
        raise RuntimeError(
            "EXP-005 must remain accepted and frozen "
            "before EXP-006 is registered."
        )

    original = LIFECYCLE_FILE.read_text(
        encoding="utf-8"
    )
    updated = add_exp006_lifecycle(
        original
    )

    if updated == original:
        print(
            "EXP-006 is already registered."
        )
    else:
        _atomic_write(
            LIFECYCLE_FILE,
            updated,
        )
        print(
            "Registered EXP-006 as PRE_REGISTERED."
        )

    print(
        "No EXP-006 strategy result was calculated."
    )
    print(
        "EXP-005 remains the frozen control."
    )


if __name__ == "__main__":
    main()
