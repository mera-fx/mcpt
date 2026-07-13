from __future__ import annotations

from copy import deepcopy
from typing import Any

from exp004_preregistration import (
    get_exp004_preregistration,
)


EXP005_PREREGISTRATION: dict[str, Any] = {
    "schema_version": 1,
    "experiment_id": "EXP-005",
    "title": (
        "NQ/MNQ 5-Minute ORB Locked Transfer"
    ),
    "locked_date": "2026-07-13",
    "research_status": "PRE_REGISTERED",
    "implementation_status": "NOT_IMPLEMENTED",
    "results_viewed": "NONE",
    "source_experiment": {
        "experiment_id": "EXP-004",
        "source_decision": "REJECT",
        "transfer_type": (
            "UNCHANGED_FIXED_RULES_NO_OPTIMIZATION"
        ),
        "reason": (
            "Test whether the exact basic ORB behaves "
            "differently on Nasdaq-100 futures. This transfer "
            "does not rescue, alter or reopen EXP-004."
        ),
    },
    "hypothesis": (
        "The unchanged fixed EXP-004 opening-range rules may "
        "transfer from QQQ to Nasdaq-100 futures and remain "
        "profitable after contract-specific futures costs."
    ),
    "null_hypothesis": (
        "The unchanged fixed opening-range rules do not "
        "produce positive, statistically convincing results "
        "on NQ/MNQ after futures costs."
    ),
    "market_and_data": {
        "primary_evidence_market": "NQ",
        "secondary_cost_market": "MNQ",
        "secondary_is_independent_evidence": False,
        "dataset": "GLBX.MDP3",
        "data_provider": "Databento",
        "input_schema": "ohlcv-1m",
        "output_timeframe": "5 minutes",
        "input_symbol_type": "continuous",
        "symbols": {
            "NQ": "NQ.v.0",
            "MNQ": "MNQ.v.0",
        },
        "continuous_roll_rule": (
            "volume-ranked front contract"
        ),
        "price_adjustment": "none",
        "continuous_prices": "original_unadjusted",
        "source_timezone": "UTC",
        "research_timezone": "America/New_York",
        "orb_anchor": "US_CASH_OPEN",
        "regular_session_start": "09:30",
        "regular_session_end": "16:00",
        "expected_one_minute_bars": 390,
        "expected_five_minute_bars": 78,
        "aggregation": {
            "open": "first",
            "high": "maximum",
            "low": "minimum",
            "close": "last",
            "volume": "sum",
        },
        "early_close_sessions": "EXCLUDED",
        "incomplete_sessions": "EXCLUDED",
        "missing_bar_fill": "PROHIBITED",
        "duplicate_timestamp_action": "STOP",
        "roll_switch_inside_session": "EXCLUDE_SESSION",
        "included_roll_switch_sessions": 0,
        "overnight_data_use": (
            "Downloaded only when required to identify "
            "session-opening gaps or contract mapping; no "
            "overnight signal or position is permitted."
        ),
    },
    "research_split": {
        "quick_transfer_start": "2019-05-06",
        "quick_transfer_end": "2022-12-30",
        "confirmation_start": "2023-01-03",
        "confirmation_end": "2025-12-31",
        "confirmation_access": "LOCKED_UNTIL_QUICK_PASS",
        "period_selection_reason": (
            "2019-05-06 is the MNQ launch date. The later "
            "period remains untouched confirmation data."
        ),
    },
    "fixed_signal_rules": {
        "opening_range_minutes": 15,
        "direction_mode": "both",
        "opening_range": (
            "Maximum high and minimum low from 09:30 through "
            "09:44:59 ET, using the first three five-minute "
            "bars. The range is then fixed."
        ),
        "first_eligible_signal_bar": (
            "The completed 09:45–09:49:59 ET bar."
        ),
        "long_breakout": (
            "Eligible completed bar closes strictly above "
            "the fixed opening-range high."
        ),
        "short_breakout": (
            "Eligible completed bar closes strictly below "
            "the fixed opening-range low."
        ),
        "direction_selection": (
            "Whichever eligible long or short breakout "
            "occurs first."
        ),
        "final_signal_bar": (
            "The completed 11:55 ET bar, permitting entry "
            "at the 12:00 ET bar open."
        ),
        "entry_execution": (
            "Enter at the next five-minute bar open."
        ),
        "entry_gap_filter": "NONE",
        "long_protective_exit": (
            "Fixed opening-range low."
        ),
        "short_protective_exit": (
            "Fixed opening-range high."
        ),
        "stop_gap_fill": (
            "If a bar opens through the stop, fill at that "
            "bar open; otherwise fill at the stop price."
        ),
        "same_entry_bar_stop": True,
        "maximum_trades_per_session": 1,
        "same_day_reversal": False,
        "forced_flat": (
            "15:55 ET five-minute bar open."
        ),
        "overnight_positions": False,
    },
    "optimization": {
        "enabled": False,
        "parameter_combinations": 1,
        "fixed_parameters": {
            "opening_range_minutes": 15,
            "direction_mode": "both",
        },
        "prohibited": [
            "Parameter search",
            "Market-specific signal changes",
            "Alternative stops or targets",
            "Volume, gap, trend or volatility filters",
            "Choosing NQ or MNQ after seeing results",
        ],
    },
    "contract_and_cost_model": {
        "reporting_basis": (
            "One contract per instrument. Profit Factor is "
            "the primary scale-independent comparison; NQ "
            "and MNQ are not independent evidence."
        ),
        "NQ": {
            "contract_multiplier_usd_per_point": 20.0,
            "minimum_tick_points": 0.25,
            "tick_value_usd": 5.0,
            "commission_exchange_nfa_usd_per_side": 2.50,
            "slippage_ticks_per_side": 1.0,
            "slippage_usd_per_side": 5.0,
            "total_modeled_cost_usd_per_side": 7.50,
            "round_trip_cost_usd": 15.0,
        },
        "MNQ": {
            "contract_multiplier_usd_per_point": 2.0,
            "minimum_tick_points": 0.25,
            "tick_value_usd": 0.50,
            "commission_exchange_nfa_usd_per_side": 1.00,
            "slippage_ticks_per_side": 1.0,
            "slippage_usd_per_side": 0.50,
            "total_modeled_cost_usd_per_side": 1.50,
            "round_trip_cost_usd": 3.0,
        },
        "capital_return_gate": "NONE",
        "reason_no_return_gate": (
            "Whole-contract futures exposure changes with "
            "index level and account size. The transfer "
            "decision uses per-contract net P&L, Profit "
            "Factor, trade counts and statistical evidence."
        ),
        "cost_sensitivity_report": [
            "0 ticks slippage per side",
            "1 tick slippage per side (decision model)",
            "2 ticks slippage per side",
        ],
    },
    "statistical_plan": {
        "random_seed": 45,
        "quick_mcpt_permutations": 25,
        "full_mcpt_permutations": 1000,
        "primary_mcpt_market": "NQ",
        "optimization_inside_permutation": False,
        "permutation_method": (
            "Time-of-day-stratified session permutation "
            "matching the locked EXP-004 method. Relative "
            "OHLC components are permuted across complete "
            "sessions within each one-minute time slot, "
            "session-opening gaps are permuted separately, "
            "and synthetic sessions are reconstructed before "
            "five-minute aggregation."
        ),
        "constraints": [
            "Preserve 390 one-minute bars per full session.",
            "Preserve 78 five-minute bars after aggregation.",
            "Preserve time-of-day distributions.",
            "Never mix overnight and regular-session components.",
            "Do not optimize any parameter on real or permuted data.",
            "Use deterministic numbered seeds.",
            "Require exact serial and multicore parity.",
        ],
    },
    "quick_transfer": {
        "data_access_rule": (
            "Use only 2019-05-06 through 2022-12-30. "
            "Confirmation-period NQ/MNQ trades, metrics, "
            "charts and parameter results must not be "
            "calculated or displayed before a passing "
            "quick-transfer decision is recorded."
        ),
        "all_gates_required": True,
        "gates": {
            "minimum_nq_trade_profit_factor_strict": 1.05,
            "minimum_mnq_trade_profit_factor_strict": 1.00,
            "minimum_nq_net_profit_usd_strict": 0.0,
            "minimum_mnq_net_profit_usd_strict": 0.0,
            "maximum_nq_mcpt_p_value": 0.20,
            "minimum_nq_completed_trades": 700,
            "minimum_nq_long_trades": 150,
            "minimum_nq_short_trades": 150,
            "maximum_included_invalid_sessions": 0,
            "maximum_included_roll_switch_sessions": 0,
        },
        "failure_action": (
            "Set EXP-005 to REJECTED and keep 2023–2025 "
            "confirmation results locked."
        ),
        "pass_action": (
            "Advance once to FULL_VALIDATION and reveal the "
            "locked 2023–2025 confirmation period."
        ),
    },
    "full_validation": {
        "all_gates_required": True,
        "gates": {
            "minimum_nq_trade_profit_factor_strict": 1.05,
            "minimum_mnq_trade_profit_factor_strict": 1.00,
            "minimum_nq_net_profit_usd_strict": 0.0,
            "minimum_mnq_net_profit_usd_strict": 0.0,
            "maximum_nq_mcpt_p_value": 0.05,
            "minimum_nq_completed_trades": 500,
            "minimum_profitable_nq_calendar_years": 2,
            "maximum_included_invalid_sessions": 0,
            "maximum_included_roll_switch_sessions": 0,
        },
        "failure_action": (
            "Set EXP-005 to REJECTED and preserve the "
            "unchanged transfer as a completed negative result."
        ),
        "pass_action": (
            "Advance to REVIEW. Paper-testing acceptance "
            "requires a separate operational review."
        ),
    },
    "interpretation_limits": [
        (
            "NQ is the primary transfer evidence. MNQ is a "
            "contract-size and cost implementation check, "
            "not a second independent market."
        ),
        (
            "A rejection applies only to the unchanged basic "
            "ORB. It does not test structured ORB variants."
        ),
        (
            "A pass would show transfer of this exact rule set; "
            "it would not justify post-result parameter changes."
        ),
    ],
    "future_orb_variants": {
        "status": "SEPARATE_FUTURE_EXPERIMENTS",
        "roadmap_file": (
            "research/ORB_structured_variant_roadmap.md"
        ),
        "prohibited_in_exp005": True,
    },
}


def get_exp005_preregistration(
) -> dict[str, Any]:
    return deepcopy(
        EXP005_PREREGISTRATION
    )


def validate_exp005_preregistration(
    record: dict[str, Any] | None = None,
) -> None:
    current = (
        EXP005_PREREGISTRATION
        if record is None
        else record
    )

    if current.get(
        "experiment_id"
    ) != "EXP-005":
        raise ValueError(
            "EXP-005 preregistration must use EXP-005."
        )

    if current.get(
        "research_status"
    ) != "PRE_REGISTERED":
        raise ValueError(
            "EXP-005 must remain PRE_REGISTERED."
        )

    if current.get(
        "implementation_status"
    ) != "NOT_IMPLEMENTED":
        raise ValueError(
            "EXP-005 cannot be implemented in this update."
        )

    if current.get(
        "results_viewed"
    ) != "NONE":
        raise ValueError(
            "EXP-005 cannot record viewed results."
        )

    source = current[
        "source_experiment"
    ]

    if (
        source["experiment_id"] != "EXP-004"
        or source["source_decision"] != "REJECT"
        or source["transfer_type"]
        != "UNCHANGED_FIXED_RULES_NO_OPTIMIZATION"
    ):
        raise ValueError(
            "EXP-005 transfer relationship changed."
        )

    exp004_fixed = (
        get_exp004_preregistration()[
            "fixed_parameters"
        ]
    )

    fixed = current[
        "optimization"
    ]["fixed_parameters"]

    if fixed != exp004_fixed:
        raise ValueError(
            "EXP-005 fixed rules no longer match EXP-004."
        )

    if current[
        "optimization"
    ]["enabled"] is not False:
        raise ValueError(
            "EXP-005 optimization must remain disabled."
        )

    if current[
        "optimization"
    ]["parameter_combinations"] != 1:
        raise ValueError(
            "EXP-005 must contain exactly one fixed rule set."
        )

    market = current[
        "market_and_data"
    ]

    if market[
        "primary_evidence_market"
    ] != "NQ":
        raise ValueError(
            "NQ must remain the primary evidence market."
        )

    if market[
        "secondary_cost_market"
    ] != "MNQ":
        raise ValueError(
            "MNQ must remain the secondary cost market."
        )

    if market[
        "secondary_is_independent_evidence"
    ] is not False:
        raise ValueError(
            "MNQ cannot be treated as independent evidence."
        )

    if market[
        "symbols"
    ] != {
        "NQ": "NQ.v.0",
        "MNQ": "MNQ.v.0",
    }:
        raise ValueError(
            "EXP-005 continuous symbols changed."
        )

    if market[
        "continuous_roll_rule"
    ] != "volume-ranked front contract":
        raise ValueError(
            "EXP-005 roll rule changed."
        )

    if market[
        "price_adjustment"
    ] != "none":
        raise ValueError(
            "EXP-005 prices must remain unadjusted."
        )

    if (
        market["expected_one_minute_bars"] != 390
        or market["expected_five_minute_bars"] != 78
    ):
        raise ValueError(
            "EXP-005 session bar counts changed."
        )

    if market[
        "roll_switch_inside_session"
    ] != "EXCLUDE_SESSION":
        raise ValueError(
            "Intraday roll switches must be excluded."
        )

    split = current[
        "research_split"
    ]

    if split[
        "quick_transfer_start"
    ] != "2019-05-06":
        raise ValueError(
            "EXP-005 must begin at the MNQ launch date."
        )

    if split[
        "confirmation_access"
    ] != "LOCKED_UNTIL_QUICK_PASS":
        raise ValueError(
            "EXP-005 confirmation data is not locked."
        )

    contracts = current[
        "contract_and_cost_model"
    ]

    for symbol in (
        "NQ",
        "MNQ",
    ):
        contract = contracts[
            symbol
        ]

        expected_tick_value = (
            contract[
                "contract_multiplier_usd_per_point"
            ]
            * contract[
                "minimum_tick_points"
            ]
        )

        if abs(
            expected_tick_value
            - contract["tick_value_usd"]
        ) > 1e-12:
            raise ValueError(
                f"{symbol} tick value is inconsistent."
            )

        expected_slippage = (
            contract[
                "tick_value_usd"
            ]
            * contract[
                "slippage_ticks_per_side"
            ]
        )

        if abs(
            expected_slippage
            - contract[
                "slippage_usd_per_side"
            ]
        ) > 1e-12:
            raise ValueError(
                f"{symbol} slippage is inconsistent."
            )

        expected_total = (
            contract[
                "commission_exchange_nfa_usd_per_side"
            ]
            + contract[
                "slippage_usd_per_side"
            ]
        )

        if abs(
            expected_total
            - contract[
                "total_modeled_cost_usd_per_side"
            ]
        ) > 1e-12:
            raise ValueError(
                f"{symbol} total side cost is inconsistent."
            )

        if abs(
            2.0 * expected_total
            - contract["round_trip_cost_usd"]
        ) > 1e-12:
            raise ValueError(
                f"{symbol} round-trip cost is inconsistent."
            )

    if not current[
        "quick_transfer"
    ]["all_gates_required"]:
        raise ValueError(
            "Every EXP-005 quick-transfer gate is mandatory."
        )

    access_rule = current[
        "quick_transfer"
    ]["data_access_rule"].lower()

    if (
        "must not be calculated"
        not in access_rule
        or "2023–2025"
        not in current[
            "quick_transfer"
        ]["failure_action"]
    ):
        raise ValueError(
            "EXP-005 confirmation lock is incomplete."
        )

    if not current[
        "full_validation"
    ]["all_gates_required"]:
        raise ValueError(
            "Every EXP-005 full-validation gate is mandatory."
        )

    statistical = current[
        "statistical_plan"
    ]

    if statistical[
        "optimization_inside_permutation"
    ] is not False:
        raise ValueError(
            "EXP-005 cannot optimize inside MCPT."
        )

    method = statistical[
        "permutation_method"
    ].lower()

    for phrase in (
        "time-of-day",
        "session",
        "one-minute",
    ):
        if phrase not in method:
            raise ValueError(
                "EXP-005 session-aware MCPT is incomplete."
            )

    if current[
        "future_orb_variants"
    ]["prohibited_in_exp005"] is not True:
        raise ValueError(
            "Structured ORB variants leaked into EXP-005."
        )


if __name__ == "__main__":
    validate_exp005_preregistration()

    print(
        "EXP-005 locked NQ/MNQ transfer preregistration "
        "is valid."
    )
