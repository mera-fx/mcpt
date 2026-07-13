from __future__ import annotations

from exp005_preregistration import (
    get_exp005_preregistration,
    validate_exp005_preregistration,
)


def main() -> None:
    validate_exp005_preregistration()
    record = get_exp005_preregistration()

    print()
    print("EXP-005 PREREGISTRATION")
    print("=======================")
    print(
        f"Status: {record['research_status']}"
    )
    print(
        "Transfer: unchanged EXP-004 fixed rules"
    )
    print(
        "Primary evidence: "
        f"{record['market_and_data']['primary_evidence_market']}"
    )
    print(
        "Secondary cost check: "
        f"{record['market_and_data']['secondary_cost_market']}"
    )
    print(
        "Optimization enabled: "
        f"{record['optimization']['enabled']}"
    )

    print()
    print("Fixed signal")
    print("------------")

    for name, value in record[
        "optimization"
    ]["fixed_parameters"].items():
        print(f"{name}: {value}")

    print()
    print("Data")
    print("----")
    market = record["market_and_data"]
    print(
        f"Provider: {market['data_provider']}"
    )
    print(
        f"Dataset:  {market['dataset']}"
    )
    print(
        "Symbols:  "
        f"{market['symbols']['NQ']}, "
        f"{market['symbols']['MNQ']}"
    )
    print(
        "Roll rule: "
        f"{market['continuous_roll_rule']}"
    )

    print()
    print("Protected periods")
    print("-----------------")
    split = record["research_split"]
    print(
        "Quick transfer: "
        f"{split['quick_transfer_start']} through "
        f"{split['quick_transfer_end']}"
    )
    print(
        "Confirmation:   "
        f"{split['confirmation_start']} through "
        f"{split['confirmation_end']} "
        f"({split['confirmation_access']})"
    )

    print()
    print("Next action")
    print("-----------")
    print(
        "Set up Databento, estimate the historical request "
        "cost, then build the protected quick-transfer "
        "downloader and runner. Do not download or expose "
        "the confirmation period."
    )

    print()
    print("Full document")
    print("-------------")
    print(
        "research/EXP-005_preregistration.md"
    )


if __name__ == "__main__":
    main()
