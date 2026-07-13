from __future__ import annotations

from exp004_preregistration import (
    get_exp004_preregistration,
    validate_exp004_preregistration,
)


def main() -> None:
    validate_exp004_preregistration()
    record = get_exp004_preregistration()

    print()
    print("EXP-004 PREREGISTRATION")
    print("=======================")
    print(
        f"Status: {record['research_status']}"
    )
    print(
        f"Market: "
        f"{record['market_and_data']['primary_market']}"
    )
    print(
        f"Bars:   "
        f"{record['market_and_data']['timeframe']}"
    )

    print()
    print("Fixed parameters")
    print("----------------")

    for name, value in (
        record["fixed_parameters"].items()
    ):
        print(f"{name}: {value}")

    print()
    print("Parameter grid")
    print("--------------")

    for name, values in (
        record["optimized_parameters"].items()
    ):
        print(
            f"{name}: "
            + ", ".join(
                str(value)
                for value in values
            )
        )

    print()
    print(
        "Total combinations: "
        f"{record['parameter_count']}"
    )

    print()
    print("Research periods")
    print("----------------")
    split = record["research_split"]
    print(
        "In sample:  "
        f"{split['in_sample_start']} through "
        f"{split['in_sample_end']}"
    )
    print(
        "Out of sample: "
        f"{split['out_of_sample_start']} through "
        f"{split['out_of_sample_end']}"
    )

    print()
    print("Next action")
    print("-----------")
    print(
        "Build the QQQ SIP downloader and session-aware "
        "ORB engine. Do not expose OOS results."
    )

    print()
    print("Full document")
    print("-------------")
    print(
        "research/EXP-004_preregistration.md"
    )


if __name__ == "__main__":
    main()
