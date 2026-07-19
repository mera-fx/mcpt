from __future__ import annotations

import ast
from pathlib import Path

from exp009_tournament_result import verify_local_exp009_tournament_result


PROJECT_DIR = Path(__file__).resolve().parent
LIFECYCLE_FILE = PROJECT_DIR / "experiment_lifecycle.py"


EXP009_REVIEW_BLOCK = r'''
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
        stage="REVIEW",
        stage_reason=(
            "All 24 preregistered candidates across six families were "
            "measured under the common NQ/MNQ execution and cost model. "
            "Twelve candidates were profitable, ten remained profitable "
            "at two ticks of slippage per side, and the four opening-drive "
            "candidates formed the strongest measured family. EXP-009 "
            "made no automatic winner, pass/fail or edge-confirmation "
            "claim and ran no MCPT, bootstrap or family optimization."
        ),
        next_action=(
            "Preserve EXP-009 as a completed discovery measurement in "
            "REVIEW. Deeply validate the four locked opening-drive "
            "candidates under EXP-010 with anchored walk-forward and "
            "selection-aware MCPT. Do not authorize paper or live trading "
            "from EXP-009."
        ),
        market_name="NQ / MNQ futures",
        timeframe="5-minute signal / 1-minute execution",
        strategy_name="multi_strategy_discovery_tournament",
        preregistration_file=Path(
            "research/EXP-009_preregistration.md"
        ),
    ),
'''


def replace_exp009_block(text: str) -> str:
    start = text.find('"EXP-009": ExperimentLifecycle(')
    if start < 0:
        raise RuntimeError("EXP-009 lifecycle block was not found.")
    next_block = text.find(
        '\n    "EXP-010": ExperimentLifecycle(', start
    )
    normalize_start = text.find(
        "\ndef normalize_experiment_id", start
    )
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
    return text[:start] + EXP009_REVIEW_BLOCK.strip() + text[end:]


def _atomic_write(path: Path, text: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def main() -> None:
    result = verify_local_exp009_tournament_result()
    if (
        result["manifest"]["result_status"]
        != "MEASURED_AWAITING_USER_REVIEW"
    ):
        raise RuntimeError("EXP-009 result is not the locked review result.")

    original = LIFECYCLE_FILE.read_text(encoding="utf-8")
    updated = replace_exp009_block(original)
    ast.parse(updated)
    if updated == original:
        print("EXP-009 lifecycle was already closed to REVIEW.")
    else:
        _atomic_write(LIFECYCLE_FILE, updated)
        print("Updated: experiment_lifecycle.py")

    print()
    print("EXP-009 is formally closed to REVIEW.")
    print("All 24 candidates and six families remain visible.")
    print("No automatic winner or pass/fail decision was added.")
    print("MCPT, bootstrap and family optimization remain not run.")
    print("No paper or live trading is authorized.")


if __name__ == "__main__":
    main()
