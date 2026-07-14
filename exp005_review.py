from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from exp005_review_implementation import get_exp005_review_implementation


@dataclass(frozen=True)
class Exp005ReviewEvaluation:
    decision: str
    passed: bool
    checks: dict[str, dict[str, Any]]
    failed_checks: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "passed": self.passed,
            "checks": self.checks,
            "failed_checks": list(self.failed_checks),
        }


def _check(*, actual: Any, operator: str, threshold: Any, passed: bool) -> dict[str, Any]:
    return {
        "actual": actual,
        "operator": operator,
        "threshold": threshold,
        "passed": bool(passed),
    }


def _cost_row(frame: pd.DataFrame, *, symbol: str, ticks: float) -> pd.Series:
    required = {
        "symbol",
        "slippage_ticks_per_side",
        "net_profit_usd",
        "trade_profit_factor",
    }
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Cost-sensitivity data is missing: {sorted(missing)}")
    selected = frame.loc[
        frame["symbol"].astype(str).str.upper().eq(symbol)
        & np.isclose(
            frame["slippage_ticks_per_side"].astype(float),
            ticks,
            atol=1e-12,
            rtol=0.0,
        )
    ]
    if len(selected) != 1:
        raise ValueError(
            f"Expected one {symbol} cost row at {ticks} ticks per side."
        )
    return selected.iloc[0]


def _yearly_nq(yearly: pd.DataFrame) -> pd.DataFrame:
    required = {"symbol", "year", "net_profit_usd"}
    missing = required.difference(yearly.columns)
    if missing:
        raise ValueError(f"Yearly data is missing: {sorted(missing)}")
    return yearly.loc[
        yearly["symbol"].astype(str).str.upper().eq("NQ")
    ].copy()


def _trade_metrics(trades: pd.DataFrame) -> dict[str, float]:
    required = {"direction", "net_pnl_usd"}
    missing = required.difference(trades.columns)
    if missing:
        raise ValueError(f"Trade data is missing: {sorted(missing)}")
    pnl = trades["net_pnl_usd"].astype(float)
    losses = pnl.loc[pnl < 0.0].abs()
    gross_loss = float(losses.sum())
    top_five_share = (
        float(losses.nlargest(5).sum()) / gross_loss
        if gross_loss > 0.0
        else 0.0
    )
    largest_loss = float(losses.max()) if not losses.empty else 0.0
    total = int(len(trades))
    long_share = (
        float(trades["direction"].astype(str).str.lower().eq("long").sum()) / total
        if total
        else 0.0
    )
    short_share = (
        float(trades["direction"].astype(str).str.lower().eq("short").sum()) / total
        if total
        else 0.0
    )
    return {
        "top_five_loss_share": top_five_share,
        "largest_loss_usd": largest_loss,
        "long_share": long_share,
        "short_share": short_share,
    }


def evaluate_exp005_review(
    *,
    full_result: dict[str, Any],
    quick_result: dict[str, Any],
    cost_sensitivity: pd.DataFrame,
    yearly_results: pd.DataFrame,
    nq_trades: pd.DataFrame,
    mnq_trades: pd.DataFrame,
) -> Exp005ReviewEvaluation:
    config = get_exp005_review_implementation()["checks"]
    checks: dict[str, dict[str, Any]] = {}

    full_eval = full_result["evaluation"]
    full_mcpt = full_result["mcpt"]
    checks["full_validation_integrity"] = _check(
        actual={
            "decision": full_eval["decision"],
            "passed": full_eval["passed"],
            "failed_gates": full_eval["failed_gates"],
            "permutations": full_mcpt["permutations"],
            "p_value": full_mcpt["p_value"],
        },
        operator="all required",
        threshold=config["full_validation_integrity"],
        passed=(
            full_eval["decision"] == "PASS_TO_REVIEW"
            and full_eval["passed"] is True
            and full_eval["failed_gates"] == []
            and all(gate["passed"] is True for gate in full_eval["gates"].values())
            and full_mcpt["permutations"] == 1000
            and float(full_mcpt["p_value"]) <= 0.05
        ),
    )

    fixed = full_result["fixed_rules"]
    checks["fixed_rule_integrity"] = _check(
        actual=fixed,
        operator="==",
        threshold=config["fixed_rule_integrity"],
        passed=(
            fixed == config["fixed_rule_integrity"]
            and full_result["quick_transfer_rerun"] is False
        ),
    )

    data = full_result["data"]
    checks["data_integrity"] = _check(
        actual={
            "included_sessions": data["included_sessions"],
            "included_invalid_sessions": data["included_invalid_sessions"],
            "included_mismatch_sessions": data["included_roll_switch_sessions"],
            "mismatch_sessions_excluded": data[
                "potential_front_month_mismatch_sessions_excluded"
            ],
        },
        operator="all required",
        threshold=config["data_integrity"],
        passed=(
            data["included_sessions"] == 733
            and data["included_invalid_sessions"] == 0
            and data["included_roll_switch_sessions"] == 0
            and data["potential_front_month_mismatch_sessions_excluded"] == 9
        ),
    )

    periods: list[dict[str, Any]] = []
    cross_period_pass = True
    for name, result in (("quick", quick_result), ("confirmation", full_result)):
        for symbol in ("NQ", "MNQ"):
            metrics = result["results"][symbol]
            periods.append(
                {
                    "period": name,
                    "symbol": symbol,
                    "profit_factor": metrics["trade_profit_factor"],
                    "net_profit_usd": metrics["net_profit_usd"],
                }
            )
            cross_period_pass = (
                cross_period_pass
                and float(metrics["trade_profit_factor"]) > 1.0
                and float(metrics["net_profit_usd"]) > 0.0
            )
    checks["cross_period_replication"] = _check(
        actual=periods,
        operator="PF > 1 and net > 0",
        threshold=config["cross_period_replication"],
        passed=cross_period_pass,
    )

    nq_yearly = _yearly_nq(yearly_results)
    observed_years = sorted(nq_yearly["year"].astype(int).tolist())
    year_pnl = {
        int(row.year): float(row.net_profit_usd)
        for row in nq_yearly.itertuples(index=False)
    }
    required_years = config["all_confirmation_years_profitable"]["required_years"]
    checks["all_confirmation_years_profitable"] = _check(
        actual=year_pnl,
        operator="> 0 for each required year",
        threshold=required_years,
        passed=(
            observed_years == required_years
            and all(year_pnl[year] > 0.0 for year in required_years)
        ),
    )

    nq_two = _cost_row(cost_sensitivity, symbol="NQ", ticks=2.0)
    mnq_two = _cost_row(cost_sensitivity, symbol="MNQ", ticks=2.0)
    two_tick_actual = {
        "NQ": {
            "profit_factor": float(nq_two["trade_profit_factor"]),
            "net_profit_usd": float(nq_two["net_profit_usd"]),
        },
        "MNQ": {
            "profit_factor": float(mnq_two["trade_profit_factor"]),
            "net_profit_usd": float(mnq_two["net_profit_usd"]),
        },
    }
    checks["two_tick_cost_resilience"] = _check(
        actual=two_tick_actual,
        operator="PF > 1 and net > 0",
        threshold=config["two_tick_cost_resilience"],
        passed=all(
            item["profit_factor"] > 1.0 and item["net_profit_usd"] > 0.0
            for item in two_tick_actual.values()
        ),
    )

    nq = full_result["results"]["NQ"]
    mnq = full_result["results"]["MNQ"]
    cost_ratios = {
        "NQ": float(nq["average_trade_usd"]) / float(nq["round_trip_cost_usd"]),
        "MNQ": float(mnq["average_trade_usd"]) / float(mnq["round_trip_cost_usd"]),
    }
    minimum_cost_ratio = config["average_trade_cost_buffer"][
        "minimum_average_trade_to_round_trip_cost"
    ]
    checks["average_trade_cost_buffer"] = _check(
        actual=cost_ratios,
        operator=">=",
        threshold=minimum_cost_ratio,
        passed=all(value >= minimum_cost_ratio for value in cost_ratios.values()),
    )

    drawdown_ratios = {
        "NQ": float(nq["net_profit_usd"]) / abs(float(nq["maximum_drawdown_usd"])),
        "MNQ": float(mnq["net_profit_usd"]) / abs(float(mnq["maximum_drawdown_usd"])),
    }
    minimum_drawdown_ratio = config["drawdown_efficiency"][
        "minimum_net_profit_to_maximum_drawdown"
    ]
    checks["drawdown_efficiency"] = _check(
        actual=drawdown_ratios,
        operator=">=",
        threshold=minimum_drawdown_ratio,
        passed=all(
            value >= minimum_drawdown_ratio for value in drawdown_ratios.values()
        ),
    )

    consistency = config["contract_implementation_consistency"]
    trade_count_difference = abs(
        int(nq["completed_trades"]) - int(mnq["completed_trades"])
    )
    pf_difference = abs(
        float(nq["trade_profit_factor"]) - float(mnq["trade_profit_factor"])
    )
    scaled_nq_net = (
        float(nq["net_profit_usd"]) / consistency["nq_to_mnq_multiplier_ratio"]
    )
    mnq_net = float(mnq["net_profit_usd"])
    scaled_net_difference = abs(scaled_nq_net - mnq_net) / max(
        abs(scaled_nq_net), abs(mnq_net), 1e-12
    )
    consistency_actual = {
        "trade_count_difference": trade_count_difference,
        "profit_factor_difference": pf_difference,
        "scaled_net_profit_difference": scaled_net_difference,
    }
    checks["contract_implementation_consistency"] = _check(
        actual=consistency_actual,
        operator="<=",
        threshold=consistency,
        passed=(
            trade_count_difference <= consistency["maximum_trade_count_difference"]
            and pf_difference <= consistency["maximum_profit_factor_difference"]
            and scaled_net_difference
            <= consistency["maximum_scaled_net_profit_difference"]
        ),
    )

    nq_trade_metrics = _trade_metrics(nq_trades)
    mnq_trade_metrics = _trade_metrics(mnq_trades)
    direction_actual = {
        "NQ": {
            "long_share": nq_trade_metrics["long_share"],
            "short_share": nq_trade_metrics["short_share"],
        },
        "MNQ": {
            "long_share": mnq_trade_metrics["long_share"],
            "short_share": mnq_trade_metrics["short_share"],
        },
    }
    minimum_direction = config["direction_balance"]["minimum_each_direction_share"]
    checks["direction_balance"] = _check(
        actual=direction_actual,
        operator=">=",
        threshold=minimum_direction,
        passed=all(
            value >= minimum_direction
            for symbol_values in direction_actual.values()
            for value in symbol_values.values()
        ),
    )

    tail_actual = {
        "NQ": nq_trade_metrics["top_five_loss_share"],
        "MNQ": mnq_trade_metrics["top_five_loss_share"],
    }
    maximum_tail = config["tail_loss_concentration"]["maximum_top_five_loss_share"]
    checks["tail_loss_concentration"] = _check(
        actual=tail_actual,
        operator="<=",
        threshold=maximum_tail,
        passed=all(value <= maximum_tail for value in tail_actual.values()),
    )

    largest_loss_ratios = {
        "NQ": nq_trade_metrics["largest_loss_usd"]
        / abs(float(nq["maximum_drawdown_usd"])),
        "MNQ": mnq_trade_metrics["largest_loss_usd"]
        / abs(float(mnq["maximum_drawdown_usd"])),
    }
    maximum_largest = config["largest_loss_drawdown_share"][
        "maximum_largest_loss_share_of_drawdown"
    ]
    checks["largest_loss_drawdown_share"] = _check(
        actual=largest_loss_ratios,
        operator="<=",
        threshold=maximum_largest,
        passed=all(value <= maximum_largest for value in largest_loss_ratios.values()),
    )

    failed = tuple(name for name, check in checks.items() if not check["passed"])
    passed = not failed
    return Exp005ReviewEvaluation(
        decision="ACCEPT_FOR_PAPER_TESTING" if passed else "REJECT",
        passed=passed,
        checks=checks,
        failed_checks=failed,
    )
