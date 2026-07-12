from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent

SUMMARY_FILE = (
    PROJECT_DIR
    / "paper_results"
    / "EXP-003"
    / "paper_summary.json"
)

ACTIVATION_FILE = (
    PROJECT_DIR
    / "paper_state"
    / "EXP-003"
    / "activation.json"
)

REPORT_FILE = (
    PROJECT_DIR
    / "paper_reports"
    / "EXP-003"
    / "index.html"
)


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--open",
        action="store_true",
        help=(
            "Open the paper-status report "
            "in the default browser."
        ),
    )

    arguments = parser.parse_args()

    if not ACTIVATION_FILE.exists():
        raise RuntimeError(
            "Paper observation has not been initialized. "
            "Run run_exp003_paper_update.py first."
        )

    activation = json.loads(
        ACTIVATION_FILE.read_text(
            encoding="utf-8"
        )
    )

    if SUMMARY_FILE.exists():
        summary = json.loads(
            SUMMARY_FILE.read_text(
                encoding="utf-8"
            )
        )
    else:
        summary = {}

    print()
    print("EXP-003 PAPER STATUS")
    print("====================")
    print("Mode: PAPER ONLY")
    print(
        "Activation cutoff: "
        f"{activation['activation_cutoff']}"
    )
    print(
        "Latest candle:     "
        f"{summary.get('latest_closed_candle', 'N/A')}"
    )
    print(
        "Completed trades:  "
        f"{summary.get('completed_trades', 0)}"
    )
    print(
        "Current position:  "
        + (
            "LONG"
            if summary.get(
                "current_position",
                0,
            ) == 1
            else "FLAT"
        )
    )
    print(
        "Paper return:      "
        f"{summary.get('total_return_percent', 0.0):.3f}%"
    )
    print(
        "Reconciliation:    "
        + (
            "PASS"
            if summary.get(
                "reconciliation",
                {},
            ).get(
                "passed",
                False,
            )
            else "NOT AVAILABLE"
        )
    )
    print(
        f"Report:            {REPORT_FILE}"
    )

    if arguments.open:
        if not REPORT_FILE.exists():
            raise RuntimeError(
                "The paper report does not exist yet."
            )

        os.startfile(REPORT_FILE)


if __name__ == "__main__":
    main()
