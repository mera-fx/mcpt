from __future__ import annotations

from copy import deepcopy
from typing import Any


EXP004_PREREGISTRATION: dict[str, Any] = {
    "schema_version": 1,
    "experiment_id": "EXP-004",
    "title": (
        "QQQ 5-Minute Opening Range Breakout"
    ),
    "locked_date": "2026-07-13",
    "research_status": "PRE_REGISTERED",
    "implementation_status": "NOT_IMPLEMENTED",
    "results_viewed": "NONE",
    "hypothesis": (
        "After QQQ establishes its opening range, the first "
        "confirmed break outside that range may continue far "
        "enough during the same regular session to overcome "
        "realistic intraday trading costs."
    ),
    "null_hypothesis": (
        "A confirmed QQQ opening-range break does not produce "
        "returns distinguishable from a session-aware random "
        "market and does not remain profitable out of sample "
        "after costs."
    ),
    "market_and_data": {
        "primary_market": "QQQ",
        "asset_class": "US equity ETF",
        "timeframe": "5 minutes",
        "data_provider": "Alpaca Market Data API",
        "historical_feed": "sip",
        "bar_adjustment": "split",
        "data_file": "data/QQQ_5m_SIP.parquet",
        "source_timestamp_timezone": "UTC",
        "research_timezone": "America/New_York",
        "regular_session_start": "09:30",
        "regular_session_end": "16:00",
        "expected_full_session_bars": 78,
        "early_close_sessions": "EXCLUDED",
        "incomplete_sessions": "EXCLUDED",
        "missing_bar_fill": "PROHIBITED",
        "duplicate_timestamp_action": "STOP",
        "out_of_order_timestamp_action": "STOP",
        "provider_access_rule": (
            "Historical SIP requests must explicitly set "
            "feed=sip and use an end timestamp safely older "
            "than the provider's delayed-data boundary."
        ),
        "position_direction": (
            "Long or short according to direction_mode"
        ),
        "maximum_gross_exposure": 1.0,
        "leverage": 1.0,
        "pyramiding": False,
        "overnight_positions": False,
        "maximum_trades_per_session": 1,
    },
    "research_split": {
        "in_sample_start": "2019-01-02",
        "in_sample_end": "2022-12-30",
        "out_of_sample_start": "2023-01-03",
        "out_of_sample_end": "2025-12-31",
        "walkforward_training_sessions": 504,
        "walkforward_retrain_sessions": 21,
        "effective_oos_rule": (
            "The effective OOS start may move forward only "
            "by the minimum number of official full sessions "
            "needed to supply the locked 504-session training "
            "window. No other date change is permitted."
        ),
        "calendar_rule": (
            "Only official full regular sessions are included. "
            "Scheduled early closes and incomplete sessions "
            "are excluded before any strategy calculation."
        ),
    },
    "signal_definition": {
        "session_identity": (
            "Each session is defined in America/New_York "
            "using the official US equity calendar."
        ),
        "opening_range": (
            "For opening_range_minutes M, opening_range_high "
            "is the maximum high and opening_range_low is the "
            "minimum low of the first M minutes beginning at "
            "09:30 ET. The range is fixed after its final bar."
        ),
        "first_eligible_signal_bar": (
            "The first completed 5-minute bar immediately "
            "after the opening-range window."
        ),
        "long_breakout": (
            "A long signal occurs when an eligible completed "
            "bar closes strictly above opening_range_high."
        ),
        "short_breakout": (
            "A short signal occurs when an eligible completed "
            "bar closes strictly below opening_range_low."
        ),
        "direction_mode": (
            "long_only permits only long signals; short_only "
            "permits only short signals; both permits whichever "
            "eligible breakout occurs first."
        ),
        "entry_cutoff": (
            "The final eligible breakout signal bar closes at "
            "11:55 ET, allowing execution at the 12:00 ET open. "
            "No new position may be opened after 12:00 ET."
        ),
        "entry_execution": (
            "The first eligible breakout signal executes at "
            "the next 5-minute bar open."
        ),
        "entry_gap_rule": (
            "The strategy enters at the actual next-bar open "
            "even when that open gaps farther beyond the range. "
            "No maximum-gap filter is allowed."
        ),
        "protective_exit": (
            "A long position exits when price reaches the "
            "opening_range_low. A short position exits when "
            "price reaches the opening_range_high."
        ),
        "stop_fill_rule": (
            "When a bar opens through the stop, fill at that "
            "bar open. Otherwise fill at the locked range "
            "boundary when the bar high/low reaches it."
        ),
        "same_entry_bar_stop": (
            "The entry bar may trigger the protective exit "
            "after the position is filled at its open."
        ),
        "forced_flat": (
            "Any open position exits at the 15:55 ET bar open, "
            "before the regular-session closing bar."
        ),
        "trade_limit": (
            "Only the first eligible trade of the session is "
            "allowed. No reversal or second entry is permitted."
        ),
        "session_end_state": (
            "Every included session must finish flat."
        ),
    },
    "optimized_parameters": {
        "opening_range_minutes": [
            5,
            15,
            30,
        ],
        "direction_mode": [
            "long_only",
            "short_only",
            "both",
        ],
    },
    "fixed_parameters": {
        "opening_range_minutes": 15,
        "direction_mode": "both",
    },
    "parameter_count": 9,
    "cost_and_execution_model": {
        "starting_capital": 100000.0,
        "commission_and_fees_bps_per_side": 0.5,
        "slippage_bps_per_side": 1.0,
        "total_cost_bps_per_side": 1.5,
        "execution_lag_bars": 1,
        "position_sizing": (
            "Use 100% of current equity as gross notional "
            "for each long or short paper position."
        ),
        "intraday_short_borrow_cost": 0.0,
        "shorting_assumption": (
            "QQQ is assumed available to borrow for an "
            "intraday unlevered short. Availability failures "
            "must be handled during later paper testing."
        ),
    },
    "optimization_plan": {
        "primary_objective": (
            "In-sample completed-trade Profit Factor after "
            "the locked costs."
        ),
        "minimum_valid_combination_trades": 100,
        "tie_break_order": [
            "Higher completed-trade Profit Factor",
            "Higher total net return",
            "Lower absolute maximum drawdown",
            "Original preregistered grid order",
        ],
        "retain_all_combinations": True,
    },
    "statistical_plan": {
        "random_seed": 44,
        "quick_mcpt_permutations": 25,
        "full_mcpt_permutations": 1000,
        "permutation_method": (
            "Time-of-day-stratified session permutation. "
            "For each 5-minute slot, relative OHLC components "
            "are independently permuted across complete sessions; "
            "overnight/session-opening gaps are permuted "
            "separately; synthetic sessions are reconstructed "
            "in chronological slot order. This preserves the "
            "intraday volatility pattern and session boundaries "
            "while destroying within-session continuation."
        ),
        "permutation_constraints": [
            "Preserve exactly 78 bars per synthetic session.",
            "Preserve each 5-minute time-of-day distribution.",
            "Never mix regular-session and overnight components.",
            "Optimize all 9 locked combinations on every permutation.",
            "Use deterministic numbered seeds and multicore parity checks.",
        ],
        "benchmark_context": [
            "Cash",
            "QQQ Buy and Hold",
            "QQQ regular-session always-long",
        ],
    },
    "quick_screen": {
        "data_access_rule": (
            "The quick screen may use only the in-sample "
            "sessions. OOS strategy returns, trades, charts "
            "and parameter scores must not be calculated or "
            "displayed before the decision is locked."
        ),
        "all_gates_required": True,
        "gates": {
            "best_in_sample_trade_pf_strictly_above": 1.10,
            "fixed_in_sample_trade_pf_strictly_above": 1.05,
            "minimum_parameter_combinations_pf_ge_1": 3,
            "maximum_quick_mcpt_p_value": 0.20,
            "minimum_fixed_in_sample_completed_trades": 250,
            "minimum_fixed_long_trades": 50,
            "minimum_fixed_short_trades": 50,
            "maximum_included_invalid_sessions": 0,
        },
        "failure_action": (
            "Set EXP-004 to REJECTED and stop. Do not inspect "
            "out-of-sample strategy results."
        ),
        "pass_action": (
            "Advance to FULL_VALIDATION and reveal the locked "
            "out-of-sample period exactly once."
        ),
    },
    "full_validation": {
        "all_gates_required": True,
        "gates": {
            "maximum_full_mcpt_p_value": 0.05,
            "minimum_fixed_oos_total_return_percent": 0.0,
            "minimum_fixed_oos_trade_profit_factor": 1.05,
            "minimum_fixed_oos_completed_trades": 150,
            "minimum_walkforward_total_return_percent": 0.0,
            "minimum_walkforward_trade_profit_factor": 1.0,
            "minimum_walkforward_completed_trades": 150,
            "maximum_absolute_fixed_oos_drawdown_percent": 25.0,
            "minimum_profitable_oos_calendar_years": 2,
            "maximum_included_invalid_sessions": 0,
        },
        "benchmark_rule": (
            "Cash, QQQ Buy and Hold and regular-session "
            "always-long must be reported. Outperforming QQQ "
            "Buy and Hold is context, not a mandatory gate, "
            "because EXP-004 is flat overnight and has lower "
            "market exposure."
        ),
        "failure_action": (
            "Set EXP-004 to REJECTED and preserve it as a "
            "completed negative result."
        ),
        "pass_action": (
            "Advance to REVIEW. Paper-testing acceptance "
            "requires a separate documented review."
        ),
    },
    "cross_market_transfer_plan": {
        "exp004_discovery_market": "QQQ only",
        "prohibited_during_exp004": (
            "SPY, NQ, MNQ, ES and MES results cannot influence "
            "EXP-004 parameters, gates or implementation."
        ),
        "future_locked_transfers": [
            {
                "planned_experiment": "EXP-005",
                "markets": ["NQ", "MNQ"],
                "rule": (
                    "Apply the final fixed EXP-004 strategy "
                    "without reoptimizing its signal parameters."
                ),
            },
            {
                "planned_experiment": "EXP-006",
                "markets": ["SPY"],
                "rule": (
                    "Apply the final fixed EXP-004 strategy "
                    "without reoptimizing its signal parameters."
                ),
            },
            {
                "planned_experiment": "EXP-007",
                "markets": ["ES", "MES"],
                "rule": (
                    "Apply the final fixed EXP-004 strategy "
                    "without reoptimizing its signal parameters."
                ),
            },
        ],
    },
    "prohibited_post_result_changes": [
        (
            "Do not change the opening-range definition, "
            "entry cutoff, next-open execution, range stop, "
            "forced-flat time, trade limit, costs, dates or gates."
        ),
        (
            "Do not add volume, gap, ATR, moving-average, "
            "news, day-of-week, profit-target or trailing-stop "
            "filters after viewing EXP-004 results."
        ),
        (
            "Do not use SPY or futures results to select or "
            "repair EXP-004. A changed rule set requires a "
            "new experiment ID and preregistration."
        ),
    ],
}


def get_exp004_preregistration(
) -> dict[str, Any]:
    return deepcopy(
        EXP004_PREREGISTRATION
    )


def validate_exp004_preregistration(
    preregistration: (
        dict[str, Any] | None
    ) = None,
) -> None:
    record = (
        EXP004_PREREGISTRATION
        if preregistration is None
        else preregistration
    )

    if record.get(
        "experiment_id"
    ) != "EXP-004":
        raise ValueError(
            "EXP-004 preregistration must use EXP-004."
        )

    if record.get(
        "research_status"
    ) != "PRE_REGISTERED":
        raise ValueError(
            "EXP-004 must remain PRE_REGISTERED."
        )

    if record.get(
        "implementation_status"
    ) != "NOT_IMPLEMENTED":
        raise ValueError(
            "EXP-004 implementation must not exist yet."
        )

    if record.get(
        "results_viewed"
    ) != "NONE":
        raise ValueError(
            "EXP-004 cannot record viewed results."
        )

    market = record[
        "market_and_data"
    ]

    if market[
        "primary_market"
    ] != "QQQ":
        raise ValueError(
            "EXP-004 discovery market must remain QQQ."
        )

    if market[
        "expected_full_session_bars"
    ] != 78:
        raise ValueError(
            "QQQ full sessions must contain 78 bars."
        )

    if market[
        "early_close_sessions"
    ] != "EXCLUDED":
        raise ValueError(
            "Early-close sessions must remain excluded."
        )

    if market[
        "missing_bar_fill"
    ] != "PROHIBITED":
        raise ValueError(
            "Missing intraday bars cannot be filled."
        )

    optimized = record[
        "optimized_parameters"
    ]

    required = {
        "opening_range_minutes",
        "direction_mode",
    }

    if set(optimized) != required:
        raise ValueError(
            "EXP-004 parameter names changed."
        )

    expected_count = 1

    for values in optimized.values():
        if not values:
            raise ValueError(
                "Parameter lists cannot be empty."
            )

        expected_count *= len(values)

    if expected_count != record[
        "parameter_count"
    ]:
        raise ValueError(
            "parameter_count does not match the grid."
        )

    fixed = record[
        "fixed_parameters"
    ]

    for name, value in fixed.items():
        if value not in optimized[name]:
            raise ValueError(
                f"Fixed {name} is outside the grid."
            )

    quick = record[
        "quick_screen"
    ]

    if not quick[
        "all_gates_required"
    ]:
        raise ValueError(
            "Every quick-screen gate is mandatory."
        )

    access_rule = quick[
        "data_access_rule"
    ].lower()

    if (
        "only the in-sample"
        not in access_rule
        or "must not be calculated"
        not in access_rule
    ):
        raise ValueError(
            "OOS quick-screen lock is missing."
        )

    full = record[
        "full_validation"
    ]

    if not full[
        "all_gates_required"
    ]:
        raise ValueError(
            "Every full-validation gate is mandatory."
        )

    permutation = record[
        "statistical_plan"
    ]["permutation_method"].lower()

    for required_phrase in (
        "time-of-day",
        "session",
        "78 bars",
    ):
        if required_phrase not in (
            permutation
            + " "
            + " ".join(
                record[
                    "statistical_plan"
                ]["permutation_constraints"]
            ).lower()
        ):
            raise ValueError(
                "Session-aware MCPT definition is incomplete."
            )

    transfer = record[
        "cross_market_transfer_plan"
    ]

    if transfer[
        "exp004_discovery_market"
    ] != "QQQ only":
        raise ValueError(
            "EXP-004 cannot become multi-market discovery."
        )

    if not record[
        "prohibited_post_result_changes"
    ]:
        raise ValueError(
            "Post-result restrictions cannot be empty."
        )


if __name__ == "__main__":
    validate_exp004_preregistration()

    print(
        "EXP-004 ORB preregistration is valid and locked."
    )
