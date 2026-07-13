from __future__ import annotations

from pathlib import Path

from exp005_quantower_import import (
    INCOMING_ROOT,
    PROCESSED_ROOT,
    RAW_ROOT,
    RESULTS_ROOT,
)


def main() -> None:
    folders = [
        INCOMING_ROOT / "NQ",
        INCOMING_ROOT / "MNQ",
        RAW_ROOT / "NQ",
        RAW_ROOT / "MNQ",
        PROCESSED_ROOT,
        RESULTS_ROOT,
    ]

    for folder in folders:
        Path(folder).mkdir(
            parents=True,
            exist_ok=True,
        )

    print()
    print(
        "EXP-005 Quantower import folders are ready."
    )
    print()
    print("Export NQ once:")
    print(
        "  Symbol: NQ — Front Month for NQ"
    )
    print(
        "  Data type: Last"
    )
    print(
        "  Aggregation: Time - Time"
    )
    print(
        "  Timeframe: 1 minute"
    )
    print(
        "  Start: 6 May 2019 00:00"
    )
    print(
        "  End:   31 December 2022 23:59"
    )
    print(
        f"  Put CSV in: {INCOMING_ROOT / 'NQ'}"
    )
    print()
    print("Export MNQ once:")
    print(
        "  Symbol: MNQ — Front Month for MNQ"
    )
    print(
        "  Use the same settings and dates."
    )
    print(
        f"  Put CSV in: {INCOMING_ROOT / 'MNQ'}"
    )
    print()
    print(
        "If Quantower refuses the full range, export yearly "
        "chunks into the same symbol folders. Overlapping "
        "identical rows are deduplicated automatically."
    )
    print()
    print(
        "Do not export any date in 2023–2025."
    )
    print(
        "Do not run a strategy or inspect performance yet."
    )
    print()
    print(
        "After both exports are copied, run:"
    )
    print(
        r".\.venv\Scripts\python.exe "
        "import_exp005_quantower_quick_data.py"
    )


if __name__ == "__main__":
    main()
