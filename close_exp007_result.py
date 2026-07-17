from __future__ import annotations

import ast
from pathlib import Path

from exp007_replication_result import (
    verify_local_exp007_replication_decision,
)


PROJECT_DIR = Path(__file__).resolve().parent
LIFECYCLE_FILE = (
    PROJECT_DIR / "experiment_lifecycle.py"
)


REPLACEMENT = r"""
    "EXP-007": ExperimentLifecycle(
        experiment_id="EXP-007",
        experiment_name=(
            "NQ/MNQ Fixed 30-Minute Long-Only "
            "1R Opening Range Breakout"
        ),
        hypothesis=(
            "A fixed long-only NQ opening-range "
            "breakout using the first 30 minutes, "
            "a stop at the opening-range low, a 1R "
            "target and a 14:00 New York time exit "
            "may generate a positive post-cost "
            "intraday edge."
        ),
        stage="REJECTED",
        stage_reason=(
            "The protected fixed replication produced "
            "positive NQ and MNQ results and passed nine "
            "of ten locked gates, but failed the required "
            "NQ session-aware MCPT gate: p=0.055944 "
            "versus the maximum 0.050000."
        ),
        next_action=(
            "Preserve EXP-007 as a completed negative "
            "historical result. Do not alter its rules, "
            "seed, permutation count or p-value gate. "
            "Any further exit or sizing research must be "
            "a separately preregistered experiment."
        ),
        market_name="NQ / MNQ futures",
        timeframe=(
            "5-minute signal / 1-minute execution"
        ),
        strategy_name=(
            "fixed_30m_long_only_1r_orb"
        ),
        preregistration_file=Path(
            "research/EXP-007_preregistration.md"
        ),
    ),
"""


def replace_exp007_block(
    text: str,
) -> str:
    start = text.find(
        '"EXP-007": ExperimentLifecycle('
    )
    if start < 0:
        raise RuntimeError(
            "EXP-007 lifecycle block was not found."
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
        and "0.055944" in current
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
        verify_local_exp007_replication_decision()
    )

    if (
        decision["evaluation"]["decision"]
        != "REJECT_EXP007_PRESERVE_AS_NEGATIVE_RESULT"
    ):
        raise RuntimeError(
            "EXP-007 decision is not the locked rejection."
        )

    original = LIFECYCLE_FILE.read_text(
        encoding="utf-8"
    )
    updated = replace_exp007_block(
        original
    )

    ast.parse(updated)

    if updated == original:
        print(
            "EXP-007 lifecycle was already closed."
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
        "EXP-007 is formally closed as REJECTED."
    )
    print(
        "Single failed gate: NQ session-aware "
        "MCPT p-value 0.055944 > 0.050000."
    )
    print(
        "NQ historical result remains positive: "
        "PF 1.116817, net $67,780, 988 trades."
    )
    print(
        "EXP-005 and EXP-006 remain frozen."
    )
    print(
        "No strategy, bootstrap or MCPT result "
        "was rerun."
    )


if __name__ == "__main__":
    main()
