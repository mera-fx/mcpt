from __future__ import annotations

import ast
from pathlib import Path

from exp008_optimization_result import (
    verify_local_exp008_optimization_decision,
)


PROJECT_DIR = Path(__file__).resolve().parent
LIFECYCLE_FILE = (
    PROJECT_DIR / "experiment_lifecycle.py"
)


REPLACEMENT = r"""
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
        stage="REJECTED",
        stage_reason=(
            "The protected 27-candidate optimization "
            "selected the stable 45-minute, 1.5R, "
            "15:55 candidate and passed twelve of "
            "thirteen locked gates, but failed the "
            "selection-aware NQ MCPT requirement: "
            "p=0.138861 versus the maximum 0.050000."
        ),
        next_action=(
            "Preserve EXP-008 as a completed negative "
            "historical result. Do not alter its grid, "
            "selection procedure, seed, permutation "
            "count or decision gates. Any further "
            "research must be separately preregistered."
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


def replace_exp008_block(
    text: str,
) -> str:
    start = text.find(
        '"EXP-008": ExperimentLifecycle('
    )
    if start < 0:
        raise RuntimeError(
            "EXP-008 lifecycle block was not found."
        )

    marker = (
        "\n}\n\ndef normalize_experiment_id"
    )
    end = text.find(marker, start)
    if end < 0:
        raise RuntimeError(
            "Lifecycle registry ending was not found."
        )

    current = text[start:end]

    if (
        'stage="REJECTED"' in current
        and "0.138861" in current
        and "0.050000" in current
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
        verify_local_exp008_optimization_decision()
    )

    if (
        decision["evaluation"]["decision"]
        != "REJECT_EXP008_PRESERVE_AS_NEGATIVE_RESULT"
    ):
        raise RuntimeError(
            "EXP-008 decision is not the locked rejection."
        )

    original = LIFECYCLE_FILE.read_text(
        encoding="utf-8"
    )
    updated = replace_exp008_block(
        original
    )

    ast.parse(updated)

    if updated == original:
        print(
            "EXP-008 lifecycle was already closed."
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
        "EXP-008 is formally closed as REJECTED."
    )
    print(
        "Single failed gate: selection-aware NQ "
        "MCPT p-value 0.138861 > 0.050000."
    )
    print(
        "Selected historical candidate remains "
        "45-minute OR, 1.5R, 15:55 flat."
    )
    print(
        "Selected NQ result remains positive: "
        "PF 1.156583, net $102,802.50, "
        "994 trades."
    )
    print(
        "EXP-005, EXP-006 and EXP-007 remain frozen."
    )
    print(
        "No grid, walk-forward, bootstrap or MCPT "
        "result was rerun."
    )


if __name__ == "__main__":
    main()
