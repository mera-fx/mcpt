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
            f"Reason: {record.stage_reason}"
        )
        print(
            f"Next: {record.next_action}"
        )

    print()
    print("Current project milestone")
    print("-------------------------")
    print(
        "EXP-003 is accepted for paper testing. "
        "The research result is frozen. The next engineering task "
        "is a paper-only simulator using the fixed preregistered "
        "parameters and the locked operational plan."
    )


if __name__ == "__main__":
    main()
