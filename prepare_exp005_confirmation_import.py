from __future__ import annotations

from pathlib import Path

from exp005_confirmation_import import (
    CONFIRMATION_ROOT,
    INCOMING_ROOT,
    PROCESSED_ROOT,
    RAW_ROOT,
    RESULTS_ROOT,
)
from exp005_quick_transfer_result import (
    verify_local_quick_transfer_decision,
)


def main() -> None:
    verify_local_quick_transfer_decision()

    folders = (
        INCOMING_ROOT / "NQ",
        INCOMING_ROOT / "MNQ",
        RAW_ROOT / "NQ",
        RAW_ROOT / "MNQ",
        PROCESSED_ROOT,
        RESULTS_ROOT,
    )

    for folder in folders:
        folder.mkdir(
            parents=True,
            exist_ok=True,
        )
        print(f"Ready: {folder.resolve()}")

    print()
    print(
        "EXP-005 confirmation acquisition is unlocked."
    )
    print(
        "Quick-transfer strategy results were not rerun."
    )
    print(
        "Place only 2023-01-03 through 2025-12-31 "
        "NQ/MNQ exports in the confirmation incoming folders."
    )


if __name__ == "__main__":
    main()
