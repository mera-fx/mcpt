from __future__ import annotations

import re
from pathlib import Path

from exp007_preregistration import (
    validate_exp007_preregistration,
)
from experiment_lifecycle import (
    get_experiment_lifecycle,
)


PROJECT_DIR = Path(__file__).resolve().parent
LIFECYCLE_FILE = (
    PROJECT_DIR / "experiment_lifecycle.py"
)


EXP007_BLOCK = r"""
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
        stage="PRE_REGISTERED",
        stage_reason=(
            "The exact fixed entry, stop, target, "
            "time exit, intrabar ambiguity rules, "
            "cost model, temporal checks, 1,000-"
            "permutation MCPT and absolute decision "
            "gates were locked before any EXP-007 "
            "result was calculated."
        ),
        next_action=(
            "Implement and test the protected fixed-"
            "rule EXP-007 replication. Commit the "
            "implementation before running it. Do not "
            "optimize exits, filters or position sizing "
            "inside EXP-007."
        ),
        market_name="NQ / MNQ futures",
        timeframe="5-minute signal / 1-minute execution",
        strategy_name=(
            "fixed_30m_long_only_1r_orb"
        ),
        preregistration_file=Path(
            "research/EXP-007_preregistration.md"
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


def add_exp007_lifecycle(
    text: str,
) -> str:
    if '"EXP-007": ExperimentLifecycle(' in text:
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
        EXP007_BLOCK
        + "}\n\n"
        + "def normalize_experiment_id"
    )

    return (
        text[:match.start()]
        + insertion
        + text[match.end():]
    )


def _verify_exp006_closure() -> None:
    try:
        from exp006_optimization_result import (
            verify_local_exp006_optimization_decision,
        )
    except ImportError as error:
        raise RuntimeError(
            "Freeze and close EXP-006 before "
            "registering EXP-007. The module "
            "exp006_optimization_result.py is missing."
        ) from error

    decision = (
        verify_local_exp006_optimization_decision()
    )

    if (
        decision["evaluation"]["decision"]
        != "REJECT_EXP006_KEEP_EXP005_CONTROL"
    ):
        raise RuntimeError(
            "The frozen EXP-006 decision is not "
            "the required rejection."
        )


def main() -> None:
    validate_exp007_preregistration()

    exp005 = get_experiment_lifecycle(
        "EXP-005"
    )
    exp006 = get_experiment_lifecycle(
        "EXP-006"
    )

    if (
        exp005.stage
        != "ACCEPTED_FOR_PAPER_TESTING"
    ):
        raise RuntimeError(
            "EXP-005 must remain accepted and "
            "frozen before EXP-007 is registered."
        )

    if exp006.stage != "REJECTED":
        raise RuntimeError(
            "EXP-006 must be formally closed as "
            "REJECTED before EXP-007 is registered."
        )

    _verify_exp006_closure()

    original = LIFECYCLE_FILE.read_text(
        encoding="utf-8"
    )
    updated = add_exp007_lifecycle(
        original
    )

    if updated == original:
        print(
            "EXP-007 is already registered."
        )
    else:
        _atomic_write(
            LIFECYCLE_FILE,
            updated,
        )
        print(
            "Registered EXP-007 as PRE_REGISTERED."
        )

    print(
        "No EXP-007 strategy result was calculated."
    )
    print(
        "EXP-005 and EXP-006 remain frozen."
    )


if __name__ == "__main__":
    main()
