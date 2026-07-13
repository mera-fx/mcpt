from __future__ import annotations

from copy import deepcopy
from typing import Any

from exp004_preregistration import (
    get_exp004_preregistration,
)


EXP005_PREREGISTRATION: dict[str, Any] = {
    "schema_version": 2,
    "experiment_id": "EXP-005",
    "title": (
        "NQ/MNQ 5-Minute ORB Locked Transfer"
    ),
    "locked_date": "2026-07-13",
    "research_status": "PRE_REGISTERED",
    "implementation_status": "NOT_IMPLEMENTED",
    "results_viewed": "NONE",
    "source_validation_samples_viewed": True,
    "source_amendment": {
        "amendment_id": "EXP-005-A1",
        "amended_date": "2026-07-13",
        "status": "LOCKED_BEFORE_FULL_DATA_EXPORT",
        "reason": (
            "The originally named paid historical source was "
            "incompatible with the project requirement that "
            "all research tooling and data remain free. A "
            "Lucid Trading account with Rithmic history was "
            "already available at no additional cost."
        ),
        "changed_scope": "DATA_SOURCE_AND_ROLL_OBSERVABILITY_ONLY",
        "unchanged": [
            "Hypothesis",
            "Fixed ORB signal and execution rules",
            "No-optimization rule",
            "Quick and confirmation periods",
            "Contract multipliers and cost assumptions",
            "MCPT method and permutation counts",
            "Every quick and full pass/fail threshold",
            "Confirmation-period lock",
        ],
        "document": "research/EXP-005_source_amendment.md",
    },
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
        "dataset": (
            "Rithmic provider-managed CME front-month history"
        ),
        "data_provider": (
            "Lucid Trading / Rithmic via Quantower "
            "History Exporter"
        ),
        "additional_data_cost": 0.0,
        "input_schema": (
            "Quantower Time-Time one-minute CSV"
        ),
        "output_timeframe": "5 minutes",
        "input_symbol_type": "provider_front_month",
        "symbols": {
            "NQ": "NQ",
            "MNQ": "MNQ",
        },
        "symbol_identity": {
            "NQ": (
                "NQ@CME; description begins "
                "'Front Month for NQ'"
            ),
            "MNQ": (
                "MNQ front-month root; separate from "
                "specific contracts such as MNQU6"
            ),
        },
        "continuous_roll_rule": (
            "provider-defined front month; exact rollover "
            "trigger is not exposed in the CSV export"
        ),
        "price_adjustment": (
            "provider-defined or unknown; no adjusted/"
            "unadjusted claim is made"
        ),
        "roll_observability": "INDIRECT_ONLY",
        "same_session_only_reason": (
            "The ORB range, breakout, entry, stop and forced "
            "exit all occur inside the same 09:30–16:00 ET "
            "cash session. No previous close, overnight gap, "
            "cross-session return or overnight position is used."
        ),
        "source_timezone": "UTC",
        "source_timezone_evidence": (
            "A Quantower task requested at UK local midnight "
            "produced a CSV beginning one hour earlier during "
            "British Summer Time; the US cash session aligned "
            "to 13:30–19:59 UTC."
        ),
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
        "data_acquisition": {
            "method": "MANUAL_HISTORY_EXPORTER_CSV",
            "connection": "Lucid Trading",
            "aggregation": "Time - Time",
            "bar_size": "1 minute",
            "data_type": "trade/last",
            "full_quick_export_completed": False,
            "confirmation_export_prohibited": True,
            "raw_files_are_immutable": True,
            "multiple_chunks_allowed": True,
        },
        "early_close_sessions": "EXCLUDED",
        "incomplete_sessions": "EXCLUDED",
        "missing_bar_fill": "PROHIBITED",
        "duplicate_timestamp_action": "STOP",
        "cross_symbol_alignment": {
            "required_for_inclusion": True,
            "identical_cash_minute_timestamps": True,
            "maximum_median_absolute_close_difference_points": 5.0,
            "maximum_single_absolute_close_difference_points": 20.0,
            "failure_action": (
                "Exclude the session from both NQ and MNQ as "
                "a potential front-month mismatch or data anomaly."
            ),
        },
        "roll_switch_inside_session": (
            "POTENTIAL_SWITCH_OR_MISMATCH_SESSION_EXCLUDED"
        ),
        "included_roll_switch_sessions": 0,
        "overnight_data_use": (
            "Raw exports may contain surrounding futures bars, "
            "but the research importer retains only the locked "
            "09:30–16:00 ET cash-session bars. No overnight "
            "signal, feature or position is permitted."
        ),
        "source_validation_samples": {
            "date": "2019-08-09",
            "research_results_calculated": False,
            "NQ": {
                "raw_rows": 1305,
                "cash_session_rows": 390,
                "five_minute_bars": 78,
                "missing_cash_minutes": 0,
                "duplicate_timestamps": 0,
                "invalid_ohlc_rows": 0,
                "tick_nonconforming_values": 0,
                "sha256": (
                    "9fd2ac2ab4e9185ce937d969cc0184c6"
                    "f7757a108c4eb8dd58d13d27840678c9"
                ),
            },
            "MNQ": {
                "raw_rows": 1300,
                "cash_session_rows": 390,
                "five_minute_bars": 78,
                "missing_cash_minutes": 0,
                "duplicate_timestamps": 0,
                "invalid_ohlc_rows": 0,
                "tick_nonconforming_values": 0,
                "sha256": (
                    "e330ee53d485975772de33bc60d97006"
                    "bc7d9f24c10345579a9f01225a6bb369"
                ),
            },
        },
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

    if current.get(
        "source_validation_samples_viewed"
    ) is not True:
        raise ValueError(
            "EXP-005 source-validation samples must be "
            "recorded honestly."
        )

    amendment = current[
        "source_amendment"
    ]

    if (
        amendment["amendment_id"] != "EXP-005-A1"
        or amendment["status"]
        != "LOCKED_BEFORE_FULL_DATA_EXPORT"
        or amendment["changed_scope"]
        != "DATA_SOURCE_AND_ROLL_OBSERVABILITY_ONLY"
    ):
        raise ValueError(
            "EXP-005 source amendment changed scope."
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
        "data_provider"
    ] != (
        "Lucid Trading / Rithmic via Quantower "
        "History Exporter"
    ):
        raise ValueError(
            "EXP-005 must use the locked free source."
        )

    if market[
        "additional_data_cost"
    ] != 0.0:
        raise ValueError(
            "EXP-005 data must remain zero additional cost."
        )

    if market[
        "symbols"
    ] != {
        "NQ": "NQ",
        "MNQ": "MNQ",
    }:
        raise ValueError(
            "EXP-005 front-month symbols changed."
        )

    if market[
        "input_symbol_type"
    ] != "provider_front_month":
        raise ValueError(
            "EXP-005 symbol type changed."
        )

    if market[
        "continuous_roll_rule"
    ] != (
        "provider-defined front month; exact rollover "
        "trigger is not exposed in the CSV export"
    ):
        raise ValueError(
            "EXP-005 provider roll statement changed."
        )

    if market[
        "price_adjustment"
    ] != (
        "provider-defined or unknown; no adjusted/"
        "unadjusted claim is made"
    ):
        raise ValueError(
            "EXP-005 cannot claim an unknown adjustment method."
        )

    if market[
        "source_timezone"
    ] != "UTC":
        raise ValueError(
            "EXP-005 CSV timestamps must be parsed as UTC."
        )

    acquisition = market[
        "data_acquisition"
    ]

    if acquisition[
        "full_quick_export_completed"
    ] is not False:
        raise ValueError(
            "Full EXP-005 quick data cannot be recorded yet."
        )

    if acquisition[
        "confirmation_export_prohibited"
    ] is not True:
        raise ValueError(
            "EXP-005 confirmation export is not blocked."
        )

    alignment = market[
        "cross_symbol_alignment"
    ]

    if (
        alignment[
            "maximum_median_absolute_close_difference_points"
        ] != 5.0
        or alignment[
            "maximum_single_absolute_close_difference_points"
        ] != 20.0
    ):
        raise ValueError(
            "EXP-005 NQ/MNQ alignment thresholds changed."
        )

    samples = market[
        "source_validation_samples"
    ]

    if samples[
        "research_results_calculated"
    ] is not False:
        raise ValueError(
            "Source-validation samples cannot contain results."
        )

    for symbol, rows in (
        ("NQ", 1305),
        ("MNQ", 1300),
    ):
        sample = samples[
            symbol
        ]

        if (
            sample["raw_rows"] != rows
            or sample["cash_session_rows"] != 390
            or sample["five_minute_bars"] != 78
            or sample["missing_cash_minutes"] != 0
            or sample["duplicate_timestamps"] != 0
            or sample["invalid_ohlc_rows"] != 0
            or sample["tick_nonconforming_values"] != 0
        ):
            raise ValueError(
                f"{symbol} source-validation evidence changed."
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
    ] != (
        "POTENTIAL_SWITCH_OR_MISMATCH_SESSION_EXCLUDED"
    ):
        raise ValueError(
            "Potential front-month mismatch sessions must "
            "be excluded."
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
