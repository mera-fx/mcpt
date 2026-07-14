from __future__ import annotations
from exp005_full_validation_result import verify_local_full_validation_decision

def main() -> None:
    result = verify_local_full_validation_decision()
    nq = result["results"]["NQ"]
    mnq = result["results"]["MNQ"]
    print()
    print("EXP-005 FULL-VALIDATION RESULT")
    print("==============================")
    print(f"Decision: {result['evaluation']['decision']}")
    print(f"Implementation commit: {result['git']['short_commit']}")
    print(f"Sessions: {result['data']['included_sessions']}")
    print(f"NQ PF / net: {nq['trade_profit_factor']:.6f} / ${nq['net_profit_usd']:,.2f}")
    print(f"MNQ PF / net: {mnq['trade_profit_factor']:.6f} / ${mnq['net_profit_usd']:,.2f}")
    print(
        f"NQ trades: {nq['completed_trades']} "
        f"({nq['long_trades']} long / {nq['short_trades']} short)"
    )
    print(
        f"NQ MCPT: {result['mcpt']['permutations']} permutations, "
        f"p={result['mcpt']['p_value']:.6f}"
    )
    print(f"Profitable NQ years: {result['results']['profitable_nq_calendar_years']}")
    print("Next stage: REVIEW")

if __name__ == "__main__":
    main()
