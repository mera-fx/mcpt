from __future__ import annotations

from exp005_quick_transfer_result import (
    verify_local_quick_transfer_decision,
)


def main() -> None:
    record = verify_local_quick_transfer_decision()
    nq = record["results"]["NQ"]
    mnq = record["results"]["MNQ"]
    mcpt = record["mcpt"]

    print()
    print("EXP-005 QUICK-TRANSFER RESULT")
    print("=============================")
    print(
        f"Decision: {record['evaluation']['decision']}"
    )
    print(
        f"Implementation commit: "
        f"{record['git']['short_commit']}"
    )
    print(
        f"Sessions: {record['data']['included_sessions']}"
    )
    print(
        f"NQ PF / net: "
        f"{nq['trade_profit_factor']:.6f} / "
        f"${nq['net_profit_usd']:,.2f}"
    )
    print(
        f"MNQ PF / net: "
        f"{mnq['trade_profit_factor']:.6f} / "
        f"${mnq['net_profit_usd']:,.2f}"
    )
    print(
        f"NQ trades: {nq['completed_trades']} "
        f"({nq['long_trades']} long / "
        f"{nq['short_trades']} short)"
    )
    print(
        f"NQ MCPT: {mcpt['permutations']} permutations, "
        f"p={mcpt['p_value']:.6f}"
    )
    print(
        "Confirmation accessed: "
        f"{record['confirmation_period_accessed']}"
    )
    print(
        "Next stage: FULL_VALIDATION"
    )


if __name__ == "__main__":
    main()
