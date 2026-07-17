from __future__ import annotations

import ast
from pathlib import Path

from exp006_optimization_result import (
    verify_local_exp006_optimization_decision,
)


PROJECT_DIR = Path(__file__).resolve().parent
LIFECYCLE_FILE = (
    PROJECT_DIR / "experiment_lifecycle.py"
)


REPLACEMENT = r"""
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
        stage="REJECTED",
        stage_reason=(
            "The protected 27-combination optimization "
            "selected the 15-minute, 10:30, both-direction "
            "candidate. It passed every locked check except "
            "the NQ Profit Factor improvement gate: "
            "0.017995 versus the required 0.020000."
        ),
        next_action=(
            "Preserve EXP-006 as a completed negative result. "
            "Keep EXP-005 unchanged as the accepted control. "
            "Do not loosen the failed gate or rerun EXP-006."
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
"""


def replace_exp006_block(text: str) -> str:
    start = text.find(
        '"EXP-006": ExperimentLifecycle('
    )
    if start < 0:
        raise RuntimeError(
            "EXP-006 lifecycle block was not found."
        )

    marker = (
        '\n}\n\ndef normalize_experiment_id'
    )
    end = text.find(marker, start)
    if end < 0:
        raise RuntimeError(
            "Lifecycle registry ending was not found."
        )

    current = text[start:end]

    if (
        'stage="REJECTED"' in current
        and "0.017995" in current
        and "0.020000" in current
    ):
        return text

    return (
        text[:start]
        + REPLACEMENT.rstrip()
        + text[end:]
    )


def atomic_write(
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


def main() -> None:
    decision = (
        verify_local_exp006_optimization_decision()
    )

    if (
        decision["evaluation"]["decision"]
        != "REJECT_EXP006_KEEP_EXP005_CONTROL"
    ):
        raise RuntimeError(
            "EXP-006 decision is not the locked rejection."
        )

    original = LIFECYCLE_FILE.read_text(
        encoding="utf-8"
    )
    updated = replace_exp006_block(
        original
    )

    ast.parse(updated)

    if updated == original:
        print(
            "EXP-006 lifecycle was already closed."
        )
    else:
        atomic_write(
            LIFECYCLE_FILE,
            updated,
        )
        print(
            "Updated: experiment_lifecycle.py"
        )

    print()
    print(
        "EXP-006 is formally closed as REJECTED."
    )
    print(
        "Single failed gate: NQ Profit Factor "
        "improvement 0.017995 < 0.020000."
    )
    print(
        "EXP-005 remains the accepted frozen control."
    )
    print(
        "No strategy, grid, walk-forward or MCPT "
        "result was rerun."
    )


if __name__ == "__main__":
    main()
