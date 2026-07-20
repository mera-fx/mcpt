from __future__ import annotations

import ast
from pathlib import Path

from exp012_preregistration import validate_exp012_preregistration
from experiment_lifecycle import get_experiment_lifecycle
from extended_session_data_result import verify_extended_session_data_result


PROJECT_DIR = Path(__file__).resolve().parent
LIFECYCLE_FILE = PROJECT_DIR / "experiment_lifecycle.py"


EXP012_BLOCK = r'''

    "EXP-012": ExperimentLifecycle(
        experiment_id="EXP-012",
        experiment_name="NQ/MNQ Extended-Hours Context Discovery",
        hypothesis=(
            "Information formed during the overnight and premarket "
            "sessions may identify cash-session gap, continuation, "
            "reversal and range-breakout strategies with meaningfully "
            "different performance and risk characteristics."
        ),
        stage="PRE_REGISTERED",
        stage_reason=(
            "Six extended-hours context families, 24 candidates, the "
            "2020-2025 aligned frozen NQ/MNQ sample, cash-session-only "
            "entries, costs, measurements and reporting rules were "
            "locked before any EXP-012 strategy result."
        ),
        next_action=(
            "Implement and commit the protected 24-candidate measurement "
            "engine before calculating results. Preserve every candidate "
            "and make no automatic winner, pass/fail, edge-confirmation "
            "or trading-authorization claim."
        ),
        market_name="NQ / MNQ futures",
        timeframe=(
            "Extended-session context / 5-minute signal / "
            "1-minute execution"
        ),
        strategy_name="extended_hours_context_discovery",
        preregistration_file=Path(
            "research/EXP-012_preregistration.md"
        ),
    ),
'''


def _atomic_write(path: Path, text: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def add_exp012_lifecycle(text: str) -> str:
    if '"EXP-012": ExperimentLifecycle(' in text:
        return text

    normalize_start = text.find("\ndef normalize_experiment_id")
    if normalize_start < 0:
        raise RuntimeError("Lifecycle normalize function was not found.")
    registry_end = text.rfind("\n}", 0, normalize_start)
    if registry_end < 0:
        raise RuntimeError("Lifecycle registry ending was not found.")

    updated = text[:registry_end] + EXP012_BLOCK + text[registry_end:]
    ast.parse(updated)
    return updated


def main() -> None:
    validate_exp012_preregistration()
    data_result = verify_extended_session_data_result()
    if data_result["complete_aligned_sessions"] != 1344:
        raise RuntimeError(
            "The frozen extended-session foundation must retain "
            "1,344 complete aligned sessions."
        )

    expected_stages = {
        "EXP-005": "ACCEPTED_FOR_PAPER_TESTING",
        "EXP-006": "REJECTED",
        "EXP-007": "REJECTED",
        "EXP-008": "REJECTED",
        "EXP-009": "REVIEW",
        "EXP-010": "REVIEW",
        "EXP-011": "REVIEW",
    }
    for experiment_id, expected_stage in expected_stages.items():
        actual = get_experiment_lifecycle(experiment_id).stage
        if actual != expected_stage:
            raise RuntimeError(
                f"{experiment_id} must remain {expected_stage}; "
                f"found {actual}."
            )

    original = LIFECYCLE_FILE.read_text(encoding="utf-8")
    updated = add_exp012_lifecycle(original)
    if updated == original:
        print("EXP-012 is already registered.")
    else:
        _atomic_write(LIFECYCLE_FILE, updated)
        print("Registered EXP-012 as PRE_REGISTERED.")

    print("Frozen extended-session data passed hash verification.")
    print("No EXP-012 strategy result was calculated.")
    print("No paper or live trading is authorized.")


if __name__ == "__main__":
    main()
