from __future__ import annotations

import ast
from pathlib import Path

from exp010_validation_result import verify_local_exp010_validation_result


PROJECT_DIR = Path(__file__).resolve().parent
LIFECYCLE_FILE = PROJECT_DIR / "experiment_lifecycle.py"


EXP010_REVIEW_BLOCK = r'''
    "EXP-010": ExperimentLifecycle(
        experiment_id="EXP-010",
        experiment_name="NQ/MNQ Opening-Drive Deep Validation",
        hypothesis=(
            "The four locked EXP-009 opening-drive candidates may retain "
            "attractive performance, risk, consistency and cost "
            "characteristics after family-level selection is accounted "
            "for with anchored walk-forward and selection-aware MCPT."
        ),
        stage="REVIEW",
        stage_reason=(
            "The locked four-candidate validation produced strong "
            "historical evidence. The measurement leader was the 0.5 "
            "minimum-drive time-exit candidate: NQ PF 1.350073, net "
            "$213,905, 775 trades and $25,280 maximum drawdown. Four of "
            "five anchored folds were profitable with $114,695 combined "
            "net profit, MNQ confirmed directionally, two-tick stress "
            "remained profitable, and selection-aware MCPT p=0.025974."
        ),
        next_action=(
            "Preserve the complete EXP-010 measurement in REVIEW. Keep "
            "the 0.5 time-exit measurement leader and the user-preferred "
            "0.5 / 1.5R reference visible as distinct alternatives. The "
            "result is not independent confirmation because the opening-"
            "drive family and 2019-2025 data were already viewed, so do "
            "not authorize paper or live trading automatically."
        ),
        market_name="NQ / MNQ futures",
        timeframe="5-minute signal / 1-minute execution",
        strategy_name="opening_drive_deep_validation",
        preregistration_file=Path(
            "research/EXP-010_preregistration.md"
        ),
    ),
'''


def replace_exp010_block(text: str) -> str:
    start = text.find('"EXP-010": ExperimentLifecycle(')
    if start < 0:
        raise RuntimeError("EXP-010 lifecycle block was not found.")
    normalize_start = text.find("\ndef normalize_experiment_id", start)
    end = text.rfind("\n}", start, normalize_start)
    if end < 0:
        raise RuntimeError("Lifecycle registry ending was not found.")

    current = text[start:end]
    if (
        'stage="REVIEW"' in current
        and "selection-aware MCPT p=0.025974" in current
    ):
        return text
    return text[:start] + EXP010_REVIEW_BLOCK.strip() + text[end:]


def _atomic_write(path: Path, text: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def main() -> None:
    result = verify_local_exp010_validation_result()
    if result["evaluation"]["classification"] != (
        "STRONG_HISTORICAL_EVIDENCE"
    ):
        raise RuntimeError("EXP-010 is not the locked strong result.")

    original = LIFECYCLE_FILE.read_text(encoding="utf-8")
    updated = replace_exp010_block(original)
    ast.parse(updated)
    if updated == original:
        print("EXP-010 lifecycle was already closed to REVIEW.")
    else:
        _atomic_write(LIFECYCLE_FILE, updated)
        print("Updated: experiment_lifecycle.py")

    print()
    print("EXP-010 is formally closed to REVIEW.")
    print("Evidence context: STRONG_HISTORICAL_EVIDENCE.")
    print("Measurement leader: opening_drive_0p5_time.")
    print("User reference remains: opening_drive_0p5_1p5r.")
    print("Prior six-family selection remains explicitly uncorrected.")
    print("No paper or live trading is authorized.")


if __name__ == "__main__":
    main()
