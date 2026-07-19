from __future__ import annotations

import re
from pathlib import Path

from exp006_optimization_result import (
    verify_local_exp006_optimization_decision,
)
from exp007_replication_result import (
    verify_local_exp007_replication_decision,
)
from exp008_optimization_result import (
    verify_local_exp008_optimization_decision,
)
from exp009_preregistration import (
    validate_exp009_preregistration,
)
from experiment_lifecycle import (
    get_experiment_lifecycle,
)


PROJECT_DIR = Path(__file__).resolve().parent
LIFECYCLE_FILE = PROJECT_DIR / "experiment_lifecycle.py"


EXP009_BLOCK = r'''

    "EXP-009": ExperimentLifecycle(
        experiment_id="EXP-009",
        experiment_name=(
            "NQ/MNQ Multi-Strategy Discovery Tournament"
        ),
        hypothesis=(
            "Several structurally different, reproducible intraday "
            "strategy families may display meaningfully different "
            "profitability, drawdown, consistency, cost resilience "
            "and practical trading behaviour under one common test."
        ),
        stage="PRE_REGISTERED",
        stage_reason=(
            "Six cash-session strategy families, four candidates per "
            "family, shared data and execution rules, complete "
            "measurement requirements and the no-winner discovery "
            "boundary were locked before any EXP-009 result."
        ),
        next_action=(
            "Implement and test all 24 candidates without changing "
            "the frozen candidate budget. Commit the implementation "
            "before calculating discovery measurements."
        ),
        market_name="NQ / MNQ futures",
        timeframe="5-minute signal / 1-minute execution",
        strategy_name="multi_strategy_discovery_tournament",
        preregistration_file=Path(
            "research/EXP-009_preregistration.md"
        ),
    ),
'''


def _atomic_write(path: Path, text: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def add_exp009_lifecycle(text: str) -> str:
    if '"EXP-009": ExperimentLifecycle(' in text:
        return text

    pattern = re.compile(
        r"(?m)^}\s*\n\s*def normalize_experiment_id"
    )
    match = pattern.search(text)
    if match is None:
        raise RuntimeError("The lifecycle registry ending was not found.")

    insertion = EXP009_BLOCK + "}\n\n\ndef normalize_experiment_id"
    return text[: match.start()] + insertion + text[match.end() :]


def _verify_prior_results() -> None:
    exp006 = verify_local_exp006_optimization_decision()
    exp007 = verify_local_exp007_replication_decision()
    exp008 = verify_local_exp008_optimization_decision()

    if (
        exp006["evaluation"]["decision"]
        != "REJECT_EXP006_KEEP_EXP005_CONTROL"
        or exp007["evaluation"]["decision"]
        != "REJECT_EXP007_PRESERVE_AS_NEGATIVE_RESULT"
        or exp008["evaluation"]["decision"]
        != "REJECT_EXP008_PRESERVE_AS_NEGATIVE_RESULT"
    ):
        raise RuntimeError("A frozen prior experiment decision changed.")


def main() -> None:
    validate_exp009_preregistration()

    expected_stages = {
        "EXP-005": "ACCEPTED_FOR_PAPER_TESTING",
        "EXP-006": "REJECTED",
        "EXP-007": "REJECTED",
        "EXP-008": "REJECTED",
    }
    for experiment_id, expected_stage in expected_stages.items():
        actual = get_experiment_lifecycle(experiment_id).stage
        if actual != expected_stage:
            raise RuntimeError(
                f"{experiment_id} must remain {expected_stage}; "
                f"found {actual}."
            )

    _verify_prior_results()

    original = LIFECYCLE_FILE.read_text(encoding="utf-8")
    updated = add_exp009_lifecycle(original)

    if updated == original:
        print("EXP-009 is already registered.")
    else:
        _atomic_write(LIFECYCLE_FILE, updated)
        print("Registered EXP-009 as PRE_REGISTERED.")

    print("No EXP-009 strategy result was calculated.")
    print("EXP-005 through EXP-008 remain frozen.")


if __name__ == "__main__":
    main()

