from __future__ import annotations

import ast
from pathlib import Path

from exp015_catalog_result import verify_local_exp015_catalog_result


PROJECT_DIR = Path(__file__).resolve().parent
LIFECYCLE_FILE = PROJECT_DIR / "experiment_lifecycle.py"


EXP015_REVIEW_BLOCK = r'''

    "EXP-015": ExperimentLifecycle(
        experiment_id="EXP-015",
        experiment_name=(
            "London Strategic Edge NQ/MNQ Data-Source Qualification"
        ),
        hypothesis=(
            "London Strategic Edge may provide identifiable, structurally "
            "complete and sufficiently consistent one-minute NQ/MNQ history "
            "for new research when compared with the frozen Quantower reference."
        ),
        stage="REVIEW",
        stage_reason=(
            "The protected official-client catalog audit returned 69 futures "
            "rows. It found one NQ candidate, NQ.F, spanning 29 May 2016 through "
            "20 July 2026, but no MNQ candidate. The catalog did not resolve "
            "continuous-contract identity, roll construction or price "
            "adjustment. The frozen classification is IDENTITY_UNRESOLVED. "
            "No historical bars were downloaded and no prior data was replaced."
        ),
        next_action=(
            "Preserve EXP-015 in REVIEW as evidence that London Strategic Edge "
            "is not qualified as the primary NQ/MNQ historical source. Keep "
            "NQ.F available only as an unresolved supplementary candidate. Any "
            "NQ.F-only sample audit or new vendor-data use requires a new "
            "preregistered experiment and must not replace frozen Quantower "
            "data. No paper or live trading is authorized."
        ),
        market_name="NQ / MNQ futures",
        timeframe="One-minute historical data-source qualification",
        strategy_name="london_strategic_edge_data_qualification",
        preregistration_file=Path(
            "research/EXP-015_preregistration.md"
        ),
    ),
'''


def replace_exp015_block(text: str) -> str:
    start = text.find('"EXP-015": ExperimentLifecycle(')
    if start < 0:
        raise RuntimeError("EXP-015 lifecycle block was not found.")

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
        and "IDENTITY_UNRESOLVED" in current
        and "No paper or live trading" in current
    ):
        return text

    updated = (
        text[:start]
        + EXP015_REVIEW_BLOCK.strip()
        + text[end:]
    )
    ast.parse(updated)
    return updated


def _atomic_write(path: Path, text: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def main() -> None:
    result = verify_local_exp015_catalog_result()

    original = LIFECYCLE_FILE.read_text(encoding="utf-8")
    updated = replace_exp015_block(original)
    if updated == original:
        print("EXP-015 lifecycle was already closed to REVIEW.")
    else:
        _atomic_write(LIFECYCLE_FILE, updated)
        print("Updated: experiment_lifecycle.py")

    print()
    print("EXP-015 is formally closed to REVIEW.")
    print("Official futures catalog rows: 69.")
    print("NQ catalog candidate: NQ.F.")
    print("MNQ catalog candidates: 0.")
    print(
        "Classification: "
        f'{result["assessment"]["classification"]}.'
    )
    print("Contract, roll and price-adjustment methods: unresolved.")
    print("Historical bars downloaded: False.")
    print("Frozen Quantower data replaced: False.")
    print("London Strategic Edge qualified as primary NQ/MNQ source: False.")
    print("No paper or live trading is authorized.")


if __name__ == "__main__":
    main()
