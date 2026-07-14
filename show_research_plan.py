from __future__ import annotations

from experiment_lifecycle import (
    format_stage_label,
    list_experiment_lifecycles,
    validate_lifecycle_registry,
)


def main() -> None:
    validate_lifecycle_registry()

    records = list_experiment_lifecycles()

    print()
    print("QUANTITATIVE RESEARCH PLAN")
    print("==========================")

    for record in records:
        print()
        print(
            f"{record.experiment_id} — "
            f"{record.experiment_name}"
        )
        print(
            f"Stage: {format_stage_label(record.stage)}"
        )
        print(
            f"Market: {record.market_name}"
        )
        print(
            f"Timeframe: {record.timeframe}"
        )
        print(
            f"Reason: {record.stage_reason}"
        )
        print(
            f"Next: {record.next_action}"
        )

    print()
    print("Current project milestone")
    print("-------------------------")
    print(
        "EXP-003 continues automatic paper testing. "
        "EXP-004 remains a rejected QQQ basic-ORB result. "
        "EXP-005 passed its protected 2019–2022 NQ/MNQ "
        "quick transfer with no optimization and has advanced "
        "to full validation. The 2023–2025 confirmation data "
        "may now be exported once and imported through the "
        "protected confirmation workflow. Structured ORB "
        "optimization remains a separate future path."
    )


if __name__ == "__main__":
    main()
