from __future__ import annotations

import ast
from pathlib import Path

from exp012_tournament_result import verify_local_exp012_tournament_result


PROJECT_DIR = Path(__file__).resolve().parent
LIFECYCLE_FILE = PROJECT_DIR / "experiment_lifecycle.py"


EXP012_REVIEW_BLOCK = r'''
    "EXP-012": ExperimentLifecycle(
        experiment_id="EXP-012",
        experiment_name="NQ/MNQ Extended-Hours Context Discovery",
        hypothesis=(
            "Information formed during the overnight and premarket "
            "sessions may identify cash-session gap, continuation, "
            "reversal and range-breakout strategies with meaningfully "
            "different performance and risk characteristics."
        ),
        stage="REVIEW",
        stage_reason=(
            "All 24 preregistered candidates across six extended-context "
            "families were measured on 1,331 aligned 2020-2025 NQ/MNQ "
            "sessions. Eighteen candidates were profitable at base and "
            "two-tick NQ costs. Gap fade and premarket momentum were the "
            "strongest measured families. Three candidates were retained "
            "for deeper review without an automatic winner, pass/fail or "
            "edge-confirmation claim."
        ),
        next_action=(
            "Preserve EXP-012 as a completed discovery measurement in "
            "REVIEW. Under EXP-013, deeply validate the locked gap-fade "
            "0.50 / 1R and premarket-continuation 0.50 and 0.75 time-exit "
            "candidates. Explicitly account for their post-EXP-012 "
            "selection and do not authorize paper or live trading."
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


def replace_exp012_block(text: str) -> str:
    start = text.find('"EXP-012": ExperimentLifecycle(')
    if start < 0:
        raise RuntimeError("EXP-012 lifecycle block was not found.")
    next_block = text.find(
        '\n    "EXP-013": ExperimentLifecycle(', start
    )
    normalize_start = text.find("\ndef normalize_experiment_id", start)
    registry_end = (
        text.rfind("\n}", start, normalize_start)
        if normalize_start >= 0
        else -1
    )
    end = next_block if next_block >= 0 else registry_end
    if end < 0:
        raise RuntimeError("Lifecycle registry ending was not found.")

    current = text[start:end]
    if (
        'stage="REVIEW"' in current
        and "All 24 preregistered candidates" in current
    ):
        return text
    updated = text[:start] + EXP012_REVIEW_BLOCK.strip() + text[end:]
    ast.parse(updated)
    return updated


def _atomic_write(path: Path, text: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def main() -> None:
    result = verify_local_exp012_tournament_result()
    if (
        result["manifest"]["result_status"]
        != "MEASURED_AWAITING_USER_REVIEW"
    ):
        raise RuntimeError("EXP-012 result is not the locked review result.")

    original = LIFECYCLE_FILE.read_text(encoding="utf-8")
    updated = replace_exp012_block(original)
    if updated == original:
        print("EXP-012 lifecycle was already closed to REVIEW.")
    else:
        _atomic_write(LIFECYCLE_FILE, updated)
        print("Updated: experiment_lifecycle.py")

    print()
    print("EXP-012 is formally closed to REVIEW.")
    print("All 24 candidates and six families remain visible.")
    print("Three review candidates are context, not automatic winners.")
    print("MCPT, bootstrap and walk-forward remain not run.")
    print("No paper or live trading is authorized.")


if __name__ == "__main__":
    main()
