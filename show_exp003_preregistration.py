from __future__ import annotations

from exp003_preregistration import (
    get_exp003_preregistration,
    validate_exp003_preregistration,
)


def main() -> None:
    validate_exp003_preregistration()
    record = get_exp003_preregistration()

    print()
    print("EXP-003 PREREGISTRATION")
    print("=======================")
    print(record["title"])
    print(
        f"Status: {record['research_status']}"
    )
    print(
        f"Locked: {record['locked_date']}"
    )

    print()
    print("Hypothesis")
    print("----------")
    print(record["hypothesis"])

    print()
    print("Locked parameter grid")
    print("---------------------")

    for name, values in (
        record[
            "optimized_parameters"
        ].items()
    ):
        print(f"{name}: {values}")

    print(
        f"Total combinations: "
        f"{record['parameter_count']}"
    )

    print()
    print("Quick-screen rule")
    print("-----------------")
    print(
        record[
            "quick_screen"
        ]["data_access_rule"]
    )

    print()
    print("Quick-screen gates")

    for name, value in (
        record[
            "quick_screen"
        ]["gates"].items()
    ):
        print(f"- {name}: {value}")

    print()
    print("Full-validation gates")

    for name, value in (
        record[
            "full_validation"
        ]["gates"].items()
    ):
        print(f"- {name}: {value}")

    print()
    print(
        "Full document: "
        "research/EXP-003_preregistration.md"
    )


if __name__ == "__main__":
    main()
