from __future__ import annotations

import ast
from pathlib import Path

from exp013_validation_result import verify_local_exp013_validation_result


PROJECT_DIR = Path(__file__).resolve().parent
LIFECYCLE_FILE = PROJECT_DIR / "experiment_lifecycle.py"


EXP013_REVIEW_BLOCK = r'''
    "EXP-013": ExperimentLifecycle(
        experiment_id="EXP-013",
        experiment_name=(
            "Extended-Context Three-Finalist Deep Validation"
        ),
        hypothesis=(
            "The locked gap-fade and premarket-continuation review "
            "candidates may retain attractive performance, risk and "
            "consistency after temporal testing and a discovery-wide "
            "24-candidate permutation test."
        ),
        stage="REVIEW",
        stage_reason=(
            "The locked three-finalist validation produced strong "
            "historical evidence. Premarket continuation at a 0.75 "
            "drive fraction with a time exit led the measurement with "
            "NQ PF 2.023738, $44,205 net profit, 88 trades and $5,540 "
            "maximum drawdown. Three of four anchored test years were "
            "profitable with $26,295 combined net profit. All 24 source "
            "candidates were repeated inside the discovery-wide MCPT, "
            "which produced p=0.003996."
        ),
        next_action=(
            "Preserve the complete EXP-013 measurement in REVIEW and "
            "keep all three finalists visible as different trade-offs. "
            "The result is not independent confirmation because the "
            "finalists were selected after viewing EXP-012. Any further "
            "rule change or optimization requires a new experiment ID; "
            "do not authorize paper or live trading automatically."
        ),
        market_name="NQ / MNQ futures",
        timeframe=(
            "Extended-session context / 5-minute signal / "
            "1-minute execution"
        ),
        strategy_name="extended_context_finalist_validation",
        preregistration_file=Path(
            "research/EXP-013_preregistration.md"
        ),
    ),
'''


def replace_exp013_block(text: str) -> str:
    start = text.find('"EXP-013": ExperimentLifecycle(')
    if start < 0:
        raise RuntimeError("EXP-013 lifecycle block was not found.")
    next_block = text.find(
        '\n    "EXP-014": ExperimentLifecycle(', start
    )
    normalize_start = text.find("\ndef normalize_experiment_id", start)
    registry_end = text.rfind("\n}", start, normalize_start)
    end = next_block if next_block >= 0 else registry_end
    if end < 0:
        raise RuntimeError("Lifecycle registry ending was not found.")

    current = text[start:end]
    if (
        'stage="REVIEW"' in current
        and "discovery-wide MCPT" in current
        and "p=0.003996" in current
    ):
        return text
    updated = text[:start] + EXP013_REVIEW_BLOCK.strip() + text[end:]
    ast.parse(updated)
    return updated


def _atomic_write(path: Path, text: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def main() -> None:
    result = verify_local_exp013_validation_result()
    if (
        result["evaluation"]["classification"]
        != "STRONG_HISTORICAL_EVIDENCE"
    ):
        raise RuntimeError("EXP-013 is not the locked strong result.")

    original = LIFECYCLE_FILE.read_text(encoding="utf-8")
    updated = replace_exp013_block(original)
    if updated == original:
        print("EXP-013 lifecycle was already closed to REVIEW.")
    else:
        _atomic_write(LIFECYCLE_FILE, updated)
        print("Updated: experiment_lifecycle.py")

    print()
    print("EXP-013 is formally closed to REVIEW.")
    print("Evidence context: STRONG_HISTORICAL_EVIDENCE.")
    print("Measurement leader: premarket_continuation_0p75_time.")
    print("Discovery-wide MCPT: 3/1,000 exceedances, p=0.003996.")
    print("Three of four anchored test years were profitable.")
    print("Post-EXP-012 selection remains explicitly disclosed.")
    print("No paper or live trading is authorized.")


if __name__ == "__main__":
    main()
