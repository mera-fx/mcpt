from __future__ import annotations

import ast
from pathlib import Path

from exp014_behaviour_result import (
    verify_local_exp014_behaviour_result,
)


PROJECT_DIR = Path(__file__).resolve().parent
LIFECYCLE_FILE = PROJECT_DIR / "experiment_lifecycle.py"


EXP014_REVIEW_BLOCK = r'''
    "EXP-014": ExperimentLifecycle(
        experiment_id="EXP-014",
        experiment_name=(
            "Finalist Behaviour and Complementarity Study"
        ),
        hypothesis=(
            "The three frozen EXP-013 finalists may exhibit distinct "
            "direction, regime, exit, tail and drawdown behaviour, while "
            "gap fade and premarket continuation may provide complementary "
            "session-level P&L rather than duplicating the same risk."
        ),
        stage="REVIEW",
        stage_reason=(
            "The protected behaviour study exactly reconstructed all three "
            "EXP-013 finalists and measured their 2025 behaviour, trade "
            "concentration, entry-known regimes, overlap and fixed arithmetic "
            "sleeve pairs. Gap fade earned $6,070 in 2025, premarket "
            "continuation 0.50 earned $9,635 with a $20,695 maximum drawdown "
            "and an 18-loss streak, and premarket continuation 0.75 lost "
            "$2,890 on 10 trades. Cross-family all-session P&L correlations "
            "were 0.041 and 0.021. The two diagnostic sleeve pairs had "
            "net-profit-to-drawdown ratios of 6.679 and 9.822 after the "
            "documented annual-measurement correction."
        ),
        next_action=(
            "Preserve EXP-014 in REVIEW as descriptive evidence. Keep the "
            "2025 weakness, 88-trade warning and same-instrument sleeve "
            "limitations visible. Any strategy change, regime filter, pair "
            "selection, weighting or executable portfolio design requires a "
            "new preregistered experiment ID. No paper or live trading is "
            "authorized by this study."
        ),
        market_name="NQ / MNQ futures",
        timeframe=(
            "Extended-session context / 5-minute signal / "
            "1-minute execution"
        ),
        strategy_name="finalist_behaviour_and_complementarity",
        preregistration_file=Path(
            "research/EXP-014_preregistration.md"
        ),
    ),
'''


def replace_exp014_block(text: str) -> str:
    start = text.find('"EXP-014": ExperimentLifecycle(')
    if start < 0:
        raise RuntimeError("EXP-014 lifecycle block was not found.")

    normalize_start = text.find(
        "\ndef normalize_experiment_id",
        start,
    )
    if normalize_start < 0:
        raise RuntimeError(
            "Lifecycle normalization function was not found."
        )

    end = text.rfind("\n}", start, normalize_start)
    if end < 0:
        raise RuntimeError("Lifecycle registry ending was not found.")

    current = text[start:end]
    if (
        'stage="REVIEW"' in current
        and "documented annual-measurement correction" in current
        and "No paper or live trading" in current
    ):
        return text

    updated = (
        text[:start]
        + EXP014_REVIEW_BLOCK.strip()
        + text[end:]
    )
    ast.parse(updated)
    return updated


def _atomic_write(path: Path, text: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def main() -> None:
    result = verify_local_exp014_behaviour_result()

    original = LIFECYCLE_FILE.read_text(encoding="utf-8")
    updated = replace_exp014_block(original)
    if updated == original:
        print("EXP-014 lifecycle was already closed to REVIEW.")
    else:
        _atomic_write(LIFECYCLE_FILE, updated)
        print("Updated: experiment_lifecycle.py")

    pairs = {
        item["pair_id"]: item
        for item in result["sleeve_pair_results"]
    }

    print()
    print("EXP-014 is formally closed to REVIEW.")
    print("Three exact finalist reconstructions: passed.")
    print("2025 gap fade net profit: $6,070.")
    print("2025 premarket 0.50 net profit: $9,635.")
    print("2025 premarket 0.75 net profit: -$2,890.")
    print(
        "Gap fade + premarket 0.50 profitable years: "
        f'{pairs["gap_fade_plus_premarket_0p50"]["profitable_years"]}/'
        f'{pairs["gap_fade_plus_premarket_0p50"]["total_years"]}.'
    )
    print(
        "Gap fade + premarket 0.75 profitable years: "
        f'{pairs["gap_fade_plus_premarket_0p75"]["profitable_years"]}/'
        f'{pairs["gap_fade_plus_premarket_0p75"]["total_years"]}.'
    )
    print("No winner, filter or executable portfolio was selected.")
    print("No paper or live trading is authorized.")


if __name__ == "__main__":
    main()
