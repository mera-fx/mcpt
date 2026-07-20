from __future__ import annotations

import argparse
from pathlib import Path

from extended_session_data import (
    AUDIT_FILE,
    OUTPUT_FILES,
    build_extended_session_dataset,
    load_frozen_cash_frames,
    load_source_specs,
    write_extended_session_dataset,
)


def run_preflight() -> None:
    specs = load_source_specs(
        verify_files=True,
    )
    frozen = load_frozen_cash_frames()
    sessions = int(
        frozen["NQ"]["session_date"].nunique()
    )
    primary = sum(item.primary for item in specs)
    fallback = len(specs) - primary

    print()
    print("EXTENDED-SESSION DATA PREFLIGHT")
    print("================================")
    print("Source:          frozen Quantower raw exports")
    print(f"Protected files: {len(specs):,}")
    print(f"Primary exports: {primary:,}")
    print(f"Fallback files:  {fallback:,}")
    print(f"Cash sessions:   {sessions:,}")
    print("Session clock:   18:00 previous day to 17:00 ET")
    print("Legacy pause:    handled through 2021-06-27")
    print("Cash overlay:    frozen EXP-005 data")
    print("Missing bars:    never filled")
    print("Strategy run:    disabled")
    print("Optimization:    disabled")
    print("MCPT/bootstrap:  disabled")
    print("Outputs written: False")
    print("================================")
    print(
        "Preflight passed. No extended-session dataset "
        "or strategy result was written."
    )


def run_build() -> None:
    if AUDIT_FILE.exists() or any(
        Path(path).exists()
        for path in OUTPUT_FILES.values()
    ):
        raise RuntimeError(
            "Extended-session outputs already exist. "
            "Preserve them; do not silently overwrite the audit."
        )

    print()
    print("Building protected extended-session data...")
    build = build_extended_session_dataset(
        verify_source_files=True,
    )
    audit = write_extended_session_dataset(build)

    print()
    print("Extended-session data build completed.")
    print(
        "Complete aligned sessions: "
        f"{audit['complete_aligned_sessions']:,}"
    )
    print(
        "Excluded incomplete sessions: "
        f"{audit['excluded_incomplete_sessions']:,}"
    )
    print(
        "NQ/MNQ one-minute rows each: "
        f"{audit['outputs']['NQ_1m']['rows']:,}"
    )
    print(
        "NQ/MNQ five-minute rows each: "
        f"{audit['outputs']['NQ_5m']['rows']:,}"
    )
    print(f"Audit: {AUDIT_FILE}")
    print("No strategy result was calculated.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Build the protected NQ/MNQ extended-session "
            "data foundation from frozen Quantower exports."
        )
    )
    parser.add_argument(
        "--preflight",
        action="store_true",
        help="Verify protected inputs without writing outputs.",
    )
    args = parser.parse_args()

    if args.preflight:
        run_preflight()
    else:
        run_build()


if __name__ == "__main__":
    main()
