from __future__ import annotations

from exp005_preregistration import (
    get_exp005_preregistration,
    validate_exp005_preregistration,
)
from exp005_source_amendment import (
    validate_exp005_source_amendment,
)


def main() -> None:
    validate_exp005_preregistration()
    validate_exp005_source_amendment()
    record = get_exp005_preregistration()

    print()
    print("EXP-005 PREREGISTRATION")
    print("=======================")
    print(
        f"Status: {record['research_status']}"
    )
    print(
        "Amendment: EXP-005-A1 — free source locked"
    )
    print(
        "Strategy results viewed: "
        f"{record['results_viewed']}"
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
    print(
        "Implementation: "
        f"{record['implementation_status']}"
    )

    print()
    print("Fixed signal")
    print("------------")

    for name, value in record[
        "optimization"
    ]["fixed_parameters"].items():
        print(f"{name}: {value}")

    print()
    print("Amended free data source")
    print("------------------------")
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
        "Symbol type: "
        f"{market['input_symbol_type']}"
    )
    print(
        "Additional data cost: "
        f"${market['additional_data_cost']:.2f}"
    )
    print(
        "Roll rule: "
        f"{market['continuous_roll_rule']}"
    )
    print(
        "Adjustment: "
        f"{market['price_adjustment']}"
    )

    print()
    print("Source-validation samples")
    print("-------------------------")

    samples = market[
        "source_validation_samples"
    ]

    for symbol in ("NQ", "MNQ"):
        sample = samples[symbol]
        print(
            f"{symbol}: "
            f"{sample['cash_session_rows']} one-minute bars, "
            f"{sample['five_minute_bars']} five-minute bars, "
            f"{sample['missing_cash_minutes']} missing"
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
        "Commit the protected importer, prepare the incoming "
        "folders, then export NQ and MNQ once for 2019-05-06 "
        "through 2022-12-30. Do not export 2023–2025."
    )

    print()
    print("Documents")
    print("---------")
    print(
        "research/EXP-005_preregistration.md"
    )
    print(
        "research/EXP-005_source_amendment.md"
    )


if __name__ == "__main__":
    main()
