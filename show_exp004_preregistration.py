from __future__ import annotations

from exp004_preregistration import (
    get_exp004_preregistration,
    validate_exp004_preregistration,
)
from exp004_quick_screen_record import (
    get_exp004_quick_screen_record,
    validate_exp004_quick_screen_record,
)
from experiment_lifecycle import (
    get_experiment_lifecycle,
)


def main() -> None:
    validate_exp004_preregistration()
    validate_exp004_quick_screen_record()

    preregistration = (
        get_exp004_preregistration()
    )
    result = (
        get_exp004_quick_screen_record()
    )
    lifecycle = get_experiment_lifecycle(
        "EXP-004"
    )

    print()
    print("EXP-004 FINAL RECORD")
    print("====================")
    print(
        f"Lifecycle: {lifecycle.stage}"
    )
    print(
        f"Decision:  {result['decision']}"
    )
    print(
        "OOS disclosure: "
        f"{result['out_of_sample_disclosure']}"
    )
    print(
        "2023–2025 viewed: "
        f"{result['out_of_sample_period_viewed']}"
    )

    print()
    print("Original fixed parameters")
    print("-------------------------")

    for name, value in preregistration[
        "fixed_parameters"
    ].items():
        print(f"{name}: {value}")

    print()
    print("Failed quick-screen gates")
    print("-------------------------")

    for name in result["failed_gates"]:
        gate = result["gates"][name]

        print(
            f"{name}: {gate['actual']} "
            f"{gate['operator']} "
            f"{gate['threshold']} -> FAIL"
        )

    print()
    print("Sample")
    print("------")
    print(
        "Included sessions: "
        f"{result['data']['included_sessions']}"
    )
    print(
        "Completed trades: "
        f"{result['observed']['fixed_in_sample_completed_trades']}"
    )
    print(
        "Included invalid sessions: "
        f"{result['data']['included_invalid_sessions']}"
    )

    print()
    print("Final instruction")
    print("-----------------")
    print(
        "Do not rerun EXP-004 or reveal its locked OOS "
        "period. More structured ORB rules require a new "
        "experiment ID."
    )

    print()
    print("Tracked result")
    print("--------------")
    print(
        "research/EXP-004_quick_screen_result.md"
    )


if __name__ == "__main__":
    main()
