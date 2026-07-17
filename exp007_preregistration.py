from __future__ import annotations

from copy import deepcopy
from typing import Any


EXP007_PREREGISTRATION: dict[str, Any] = {
    "schema_version": 1,
    "experiment_id": "EXP-007",
    "title": (
        "NQ/MNQ Fixed 30-Minute Long-Only "
        "1R Opening Range Breakout"
    ),
    "locked_date": "2026-07-17",
    "research_status": "PRE_REGISTERED",
    "implementation_status": "NOT_RUN",
    "results_viewed": "NONE",
    "source_idea": {
        "video_url": (
            "https://youtu.be/wm6XQFw1GHI"
        ),
        "video_strategy_role": (
            "RESEARCH_IDEA_AND_RULE_SOURCE_ONLY"
        ),
        "academic_context": [
            {
                "title": (
                    "Market Intraday Momentum"
                ),
                "authors": (
                    "Gao, Han, Li and Zhou"
                ),
                "publication": (
                    "Journal of Financial "
                    "Economics 129(2), 2018"
                ),
                "doi": (
                    "10.1016/j.jfineco.2018.05.009"
                ),
                "boundary": (
                    "Supports an intraday-momentum "
                    "mechanism; does not directly "
                    "validate this exact NQ rule set."
                ),
            },
            {
                "title": (
                    "Volatility-Managed Portfolios"
                ),
                "authors": (
                    "Moreira and Muir"
                ),
                "publication": (
                    "Journal of Finance 72(4), 2017"
                ),
                "doi": "10.1111/jofi.12513",
                "boundary": (
                    "Motivates a later sizing study; "
                    "position sizing is not tested "
                    "inside EXP-007."
                ),
            },
            {
                "title": (
                    "The Impact of Volatility Targeting"
                ),
                "authors": (
                    "Harvey, Hoyle, Korgaonkar, "
                    "Rattray, Sargaison and Van Hemert"
                ),
                "publication": (
                    "Journal of Portfolio Management "
                    "45(1), 2018"
                ),
                "boundary": (
                    "Motivates a later sizing study; "
                    "position sizing is not tested "
                    "inside EXP-007."
                ),
            },
        ],
    },
    "experiment_relationships": {
        "exp005": {
            "relationship": (
                "ACCEPTED_FROZEN_CONTROL"
            ),
            "required_stage": (
                "ACCEPTED_FOR_PAPER_TESTING"
            ),
            "must_remain_unchanged": True,
        },
        "exp006": {
            "relationship": (
                "COMPLETED_REJECTED_OPTIMIZATION"
            ),
            "required_stage": "REJECTED",
            "must_remain_unchanged": True,
            "failed_gate_is_not_reused": True,
        },
    },
    "hypothesis": (
        "A fixed long-only NQ opening-range breakout "
        "using the first 30 minutes, a stop at the "
        "opening-range low, a 1R target and a 14:00 "
        "New York time exit may generate a positive "
        "post-cost intraday edge."
    ),
    "null_hypothesis": (
        "The fixed strategy does not generate a "
        "positive and temporally robust post-cost "
        "edge after session-aware permutation testing."
    ),
    "interpretation": {
        "historical_status": (
            "EXPLORATORY_BECAUSE_2019_2025_WAS_ALREADY_VIEWED"
        ),
        "historical_result_cannot_authorize_live_trading": True,
        "best_possible_historical_decision": (
            "FIXED_CANDIDATE_FOR_FORWARD_PAPER_COMPARISON"
        ),
        "final_confirmation_source": (
            "NEW_FORWARD_DATA_ONLY"
        ),
        "academic_papers_are_context_not_direct_proof": True,
        "video_results_are_not_imported_as_evidence": True,
    },
    "market_and_data": {
        "primary_evidence_market": "NQ",
        "secondary_implementation_market": "MNQ",
        "secondary_is_independent_evidence": False,
        "data_source": (
            "Frozen EXP-005 Quantower/Lucid-Rithmic "
            "NQ and MNQ datasets"
        ),
        "historical_start": "2019-05-06",
        "historical_end": "2025-12-31",
        "source_timeframe": "1 minute",
        "signal_timeframe": "5 minutes",
        "source_timezone": "UTC",
        "research_timezone": (
            "America/New_York"
        ),
        "cash_session": "09:30-16:00",
        "expected_included_sessions": 1639,
        "expected_one_minute_bars_per_full_session": 390,
        "expected_five_minute_bars_per_full_session": 78,
        "reuse_only_frozen_exp005_clean_sessions": True,
        "new_data_cleaning_decisions_prohibited": True,
        "missing_bar_fill_prohibited": True,
        "raw_source_editing_prohibited": True,
    },
    "fixed_strategy_rules": {
        "optimization_enabled": False,
        "parameter_combinations": 1,
        "direction_mode": "long_only",
        "opening_range_start_new_york": "09:30",
        "opening_range_end_new_york": "10:00",
        "opening_range_minutes": 30,
        "opening_range_five_minute_bars": 6,
        "opening_range_high": (
            "Maximum high of the six complete "
            "09:30-10:00 five-minute bars."
        ),
        "opening_range_low": (
            "Minimum low of the six complete "
            "09:30-10:00 five-minute bars."
        ),
        "breakout_signal": (
            "First completed five-minute candle "
            "closing strictly above the opening-range high."
        ),
        "signal_requires_completed_bar": True,
        "signal_price_comparison": (
            "five-minute close > opening-range high"
        ),
        "delta_confirmation": "DISABLED",
        "other_filters": "NONE",
        "maximum_trades_per_session": 1,
        "same_day_reentry": False,
        "short_entries": False,
        "last_eligible_breakout_bar": (
            "13:50-13:55 New York"
        ),
        "final_signal_close_time_new_york": "13:55",
        "entry": (
            "Next five-minute bar open after the "
            "completed breakout signal."
        ),
        "latest_entry_time_new_york": "13:55",
        "entry_gap_filter": "NONE",
        "entry_uses_actual_open_price": True,
        "protective_stop": (
            "Opening-range low."
        ),
        "risk_points": (
            "Actual entry price minus opening-range low."
        ),
        "invalid_nonpositive_risk_trade": (
            "DO_NOT_ENTER"
        ),
        "profit_target": (
            "Actual entry price plus one times risk_points."
        ),
        "reward_to_risk": 1.0,
        "forced_flat_time_new_york": "14:00",
        "forced_flat_price": (
            "14:00 one-minute bar open."
        ),
        "overnight_positions": False,
    },
    "intrabar_execution": {
        "execution_resolution": "1 minute",
        "entry_minute_can_exit": True,
        "evaluate_minutes_in_chronological_order": True,
        "stop_gap_rule": (
            "If a one-minute bar opens at or below "
            "the stop, fill at that opening price."
        ),
        "stop_touch_rule": (
            "Otherwise fill at the stop boundary "
            "when the minute low touches it."
        ),
        "target_gap_rule": (
            "A target gap receives no favourable "
            "price improvement; fill at the target."
        ),
        "target_touch_rule": (
            "Fill at the target boundary."
        ),
        "same_minute_stop_and_target_rule": (
            "STOP_FIRST_CONSERVATIVE"
        ),
        "time_exit_precedence": (
            "Positions still open are closed at "
            "the 14:00 one-minute opening price."
        ),
    },
    "position_sizing": {
        "method": "FIXED_ONE_CONTRACT",
        "NQ_contracts": 1,
        "MNQ_contracts": 1,
        "volatility_targeting_enabled": False,
        "reason": (
            "EXP-007 isolates signal and exit validity. "
            "Sizing is reserved for a separate experiment."
        ),
    },
    "contract_and_cost_model": {
        "NQ": {
            "multiplier_usd_per_point": 20.0,
            "tick_size_points": 0.25,
            "fees_usd_per_side": 2.50,
            "base_slippage_ticks_per_side": 1.0,
            "base_round_trip_cost_usd": 15.0,
            "analytical_reference_capital_usd": 100000.0,
        },
        "MNQ": {
            "multiplier_usd_per_point": 2.0,
            "tick_size_points": 0.25,
            "fees_usd_per_side": 1.00,
            "base_slippage_ticks_per_side": 1.0,
            "base_round_trip_cost_usd": 3.0,
            "analytical_reference_capital_usd": 10000.0,
        },
        "cost_sensitivity_ticks_per_side": [0, 1, 2],
        "decision_cost_stress_ticks_per_side": 2,
    },
    "temporal_robustness": {
        "fixed_rules_never_reselected": True,
        "development_context_period": {
            "start": "2019-05-06",
            "end": "2020-12-31",
        },
        "annual_evaluation_blocks": [
            {
                "start": "2021-01-01",
                "end": "2021-12-31",
            },
            {
                "start": "2022-01-01",
                "end": "2022-12-31",
            },
            {
                "start": "2023-01-01",
                "end": "2023-12-31",
            },
            {
                "start": "2024-01-01",
                "end": "2024-12-31",
            },
            {
                "start": "2025-01-01",
                "end": "2025-12-31",
            },
        ],
        "block_count": 5,
        "minimum_profitable_nq_blocks": 3,
        "combined_2021_2025_nq_net_profit_must_be_positive": True,
        "not_claimed_as_untouched_out_of_sample": True,
    },
    "session_aware_mcpt": {
        "enabled": True,
        "primary_market": "NQ",
        "permutations": 1000,
        "random_seed": 47,
        "engine_family": (
            "EXP-005 session-aware one-minute permutation"
        ),
        "strategy_reoptimized_inside_permutation": False,
        "reason_no_reoptimization": (
            "EXP-007 contains one fixed rule set and "
            "performs no parameter selection."
        ),
        "test_statistic": "trade_profit_factor",
        "p_value_formula": (
            "(1 + permutations with PF >= real PF) "
            "/ (1 + permutations)"
        ),
        "maximum_p_value": 0.05,
        "exact_serial_parallel_parity_required": True,
    },
    "bootstrap_diagnostics": {
        "enabled": True,
        "resamples": 10000,
        "random_seed": 4701,
        "sampling_unit": "completed_trade",
        "method": (
            "Sample completed trades with replacement "
            "using the locked random seed."
        ),
        "reported_intervals": [
            "95% percentile interval for average trade USD",
            "95% percentile interval for trade Profit Factor",
        ],
        "decision_gate": False,
        "reason_report_only": (
            "The bootstrap is descriptive and must not "
            "duplicate or replace the preregistered MCPT gate."
        ),
    },
    "historical_decision_gates": {
        "all_required": True,
        "minimum_nq_trade_profit_factor_strict": 1.0,
        "minimum_nq_net_profit_usd_strict": 0.0,
        "minimum_nq_average_trade_usd_strict": 0.0,
        "minimum_nq_completed_trades": 500,
        "minimum_profitable_nq_annual_blocks": 3,
        "minimum_combined_2021_2025_nq_net_profit_usd_strict": 0.0,
        "maximum_nq_mcpt_p_value": 0.05,
        "minimum_nq_two_tick_stress_net_profit_usd_strict": 0.0,
        "minimum_mnq_trade_profit_factor_strict": 1.0,
        "minimum_mnq_net_profit_usd_strict": 0.0,
        "profit_factor_improvement_vs_exp005_required": False,
        "failure_action": (
            "REJECT_EXP007_PRESERVE_AS_NEGATIVE_RESULT"
        ),
        "pass_action": (
            "LOCK_FIXED_EXP007_CANDIDATE_FOR_FORWARD_"
            "PAPER_COMPARISON"
        ),
    },
    "future_experiment_boundaries": {
        "exit_parameter_optimization": (
            "SEPARATE_FUTURE_EXPERIMENT_ONLY"
        ),
        "volatility_targeted_position_sizing": (
            "SEPARATE_FUTURE_EXPERIMENT_ONLY"
        ),
        "delta_confirmation": (
            "NOT_AVAILABLE_IN_FROZEN_OHLCV_DATA"
        ),
    },
    "prohibited_actions": [
        "Changing EXP-005.",
        "Reopening or changing EXP-006.",
        "Optimizing any EXP-007 parameter.",
        "Adding short trades.",
        "Adding delta confirmation.",
        "Adding indicators or discretionary filters.",
        "Changing the 1R target after results are viewed.",
        "Changing the 14:00 time exit after results are viewed.",
        "Applying volatility targeting inside EXP-007.",
        "Treating the video result as independent evidence.",
        "Claiming 2019-2025 is untouched confirmation data.",
        "Running fewer than 1,000 NQ permutations.",
        "Changing the decision gates after results are viewed.",
        "Authorizing live trading from historical EXP-007 results.",
    ],
}


def get_exp007_preregistration() -> dict[str, Any]:
    return deepcopy(EXP007_PREREGISTRATION)


def validate_exp007_preregistration(
    record: dict[str, Any] | None = None,
) -> None:
    current = (
        EXP007_PREREGISTRATION
        if record is None
        else record
    )

    if (
        current.get("schema_version") != 1
        or current.get("experiment_id") != "EXP-007"
        or current.get("research_status") != "PRE_REGISTERED"
        or current.get("implementation_status") != "NOT_RUN"
        or current.get("results_viewed") != "NONE"
    ):
        raise ValueError(
            "EXP-007 preregistration identity or "
            "pre-result state changed."
        )

    relationships = current[
        "experiment_relationships"
    ]
    if (
        relationships["exp005"]["required_stage"]
        != "ACCEPTED_FOR_PAPER_TESTING"
        or relationships["exp005"][
            "must_remain_unchanged"
        ] is not True
        or relationships["exp006"]["required_stage"]
        != "REJECTED"
        or relationships["exp006"][
            "must_remain_unchanged"
        ] is not True
        or relationships["exp006"][
            "failed_gate_is_not_reused"
        ] is not True
    ):
        raise ValueError(
            "EXP-007 prior-experiment boundary changed."
        )

    interpretation = current["interpretation"]
    if (
        interpretation["historical_status"]
        != "EXPLORATORY_BECAUSE_2019_2025_WAS_ALREADY_VIEWED"
        or interpretation[
            "historical_result_cannot_authorize_live_trading"
        ] is not True
        or interpretation[
            "best_possible_historical_decision"
        ]
        != "FIXED_CANDIDATE_FOR_FORWARD_PAPER_COMPARISON"
        or interpretation[
            "final_confirmation_source"
        ] != "NEW_FORWARD_DATA_ONLY"
        or interpretation[
            "academic_papers_are_context_not_direct_proof"
        ] is not True
        or interpretation[
            "video_results_are_not_imported_as_evidence"
        ] is not True
    ):
        raise ValueError(
            "EXP-007 interpretation boundary changed."
        )

    data = current["market_and_data"]
    if (
        data["primary_evidence_market"] != "NQ"
        or data["secondary_implementation_market"] != "MNQ"
        or data["secondary_is_independent_evidence"] is not False
        or data["expected_included_sessions"] != 1639
        or data[
            "reuse_only_frozen_exp005_clean_sessions"
        ] is not True
        or data[
            "new_data_cleaning_decisions_prohibited"
        ] is not True
    ):
        raise ValueError(
            "EXP-007 market/data lock changed."
        )

    rules = current["fixed_strategy_rules"]
    if (
        rules["optimization_enabled"] is not False
        or rules["parameter_combinations"] != 1
        or rules["direction_mode"] != "long_only"
        or rules["opening_range_minutes"] != 30
        or rules["opening_range_five_minute_bars"] != 6
        or rules["delta_confirmation"] != "DISABLED"
        or rules["maximum_trades_per_session"] != 1
        or rules["short_entries"] is not False
        or rules["reward_to_risk"] != 1.0
        or rules["forced_flat_time_new_york"] != "14:00"
    ):
        raise ValueError(
            "EXP-007 fixed strategy changed."
        )

    intrabar = current["intrabar_execution"]
    if (
        intrabar["execution_resolution"] != "1 minute"
        or intrabar[
            "evaluate_minutes_in_chronological_order"
        ] is not True
        or intrabar[
            "same_minute_stop_and_target_rule"
        ] != "STOP_FIRST_CONSERVATIVE"
    ):
        raise ValueError(
            "EXP-007 intrabar execution changed."
        )

    sizing = current["position_sizing"]
    if (
        sizing["method"] != "FIXED_ONE_CONTRACT"
        or sizing["NQ_contracts"] != 1
        or sizing["MNQ_contracts"] != 1
        or sizing[
            "volatility_targeting_enabled"
        ] is not False
    ):
        raise ValueError(
            "EXP-007 sizing isolation changed."
        )

    temporal = current["temporal_robustness"]
    if (
        temporal["fixed_rules_never_reselected"] is not True
        or temporal["block_count"] != 5
        or len(
            temporal["annual_evaluation_blocks"]
        ) != 5
        or temporal[
            "minimum_profitable_nq_blocks"
        ] != 3
        or temporal[
            "not_claimed_as_untouched_out_of_sample"
        ] is not True
    ):
        raise ValueError(
            "EXP-007 temporal-robustness plan changed."
        )

    mcpt = current["session_aware_mcpt"]
    if (
        mcpt["enabled"] is not True
        or mcpt["primary_market"] != "NQ"
        or mcpt["permutations"] != 1000
        or mcpt["random_seed"] != 47
        or mcpt[
            "strategy_reoptimized_inside_permutation"
        ] is not False
        or mcpt["test_statistic"]
        != "trade_profit_factor"
        or mcpt["maximum_p_value"] != 0.05
        or mcpt[
            "exact_serial_parallel_parity_required"
        ] is not True
    ):
        raise ValueError(
            "EXP-007 MCPT plan changed."
        )

    bootstrap = current["bootstrap_diagnostics"]
    if (
        bootstrap["enabled"] is not True
        or bootstrap["resamples"] != 10000
        or bootstrap["random_seed"] != 4701
        or bootstrap["decision_gate"] is not False
    ):
        raise ValueError(
            "EXP-007 bootstrap diagnostic changed."
        )

    gates = current["historical_decision_gates"]
    if (
        gates["all_required"] is not True
        or gates[
            "minimum_nq_trade_profit_factor_strict"
        ] != 1.0
        or gates["minimum_nq_completed_trades"] != 500
        or gates[
            "minimum_profitable_nq_annual_blocks"
        ] != 3
        or gates["maximum_nq_mcpt_p_value"] != 0.05
        or gates[
            "profit_factor_improvement_vs_exp005_required"
        ] is not False
        or gates["failure_action"]
        != "REJECT_EXP007_PRESERVE_AS_NEGATIVE_RESULT"
        or gates["pass_action"]
        != (
            "LOCK_FIXED_EXP007_CANDIDATE_FOR_FORWARD_"
            "PAPER_COMPARISON"
        )
    ):
        raise ValueError(
            "EXP-007 historical decision gates changed."
        )

    prohibited = " ".join(
        current["prohibited_actions"]
    ).lower()
    for phrase in (
        "changing exp-005",
        "changing exp-006",
        "optimizing any exp-007 parameter",
        "adding short",
        "delta confirmation",
        "volatility targeting",
        "untouched confirmation",
        "1,000 nq permutations",
        "decision gates",
        "live trading",
    ):
        if phrase not in prohibited:
            raise ValueError(
                "EXP-007 prohibition missing: "
                f"{phrase}."
            )


if __name__ == "__main__":
    validate_exp007_preregistration()
    print(
        "EXP-007 fixed video-ORB preregistration "
        "is valid and contains no results."
    )
