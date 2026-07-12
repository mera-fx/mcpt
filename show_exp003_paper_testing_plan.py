from __future__ import annotations

from paper_testing_plan import (
    get_exp003_paper_testing_plan,
    validate_exp003_paper_testing_plan,
)


def main() -> None:
    validate_exp003_paper_testing_plan()
    plan = get_exp003_paper_testing_plan()

    print()
    print("EXP-003 PAPER-TESTING PLAN")
    print("==========================")
    print(
        f"Status: {plan['status']}"
    )
    print(
        f"Mode:   {plan['mode']}"
    )

    print()
    print("Fixed parameters")
    print("----------------")

    for name, value in (
        plan["fixed_parameters"].items()
    ):
        print(f"{name}: {value}")

    print()
    print("Minimum observation")
    print("-------------------")
    print(
        f"Weeks:  "
        f"{plan['minimum_observation']['calendar_weeks']}"
    )
    print(
        f"Trades: "
        f"{plan['minimum_observation']['completed_trades']}"
    )
    print(
        plan[
            "minimum_observation"
        ]["completion_rule"]
    )

    print()
    print("Purpose")
    print("-------")
    print(
        plan["acceptance_interpretation"]
    )

    print()
    print("Full document")
    print("-------------")
    print(
        "research/EXP-003_paper_testing_plan.md"
    )


if __name__ == "__main__":
    main()
