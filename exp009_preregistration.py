from __future__ import annotations

from copy import deepcopy
from typing import Any


FAMILY_CANDIDATES: dict[str, tuple[dict[str, Any], ...]] = {
    "orb_pullback_continuation": (
        {
            "candidate_id": "orb_pullback_long_1r",
            "direction_mode": "long_only",
            "reward_to_risk": 1.0,
        },
        {
            "candidate_id": "orb_pullback_long_1p5r",
            "direction_mode": "long_only",
            "reward_to_risk": 1.5,
        },
        {
            "candidate_id": "orb_pullback_both_1r",
            "direction_mode": "both",
            "reward_to_risk": 1.0,
        },
        {
            "candidate_id": "orb_pullback_both_1p5r",
            "direction_mode": "both",
            "reward_to_risk": 1.5,
        },
    ),
    "failed_orb_reversal": (
        {
            "candidate_id": "failed_orb_30m_1r",
            "failure_window_minutes": 30,
            "reward_to_risk": 1.0,
        },
        {
            "candidate_id": "failed_orb_30m_1p5r",
            "failure_window_minutes": 30,
            "reward_to_risk": 1.5,
        },
        {
            "candidate_id": "failed_orb_60m_1r",
            "failure_window_minutes": 60,
            "reward_to_risk": 1.0,
        },
        {
            "candidate_id": "failed_orb_60m_1p5r",
            "failure_window_minutes": 60,
            "reward_to_risk": 1.5,
        },
    ),
    "vwap_mean_reversion": (
        {
            "candidate_id": "vwap_reversion_1p5sd_vwap",
            "band_standard_deviations": 1.5,
            "exit_mode": "vwap",
        },
        {
            "candidate_id": "vwap_reversion_1p5sd_1r",
            "band_standard_deviations": 1.5,
            "exit_mode": "1r",
        },
        {
            "candidate_id": "vwap_reversion_2sd_vwap",
            "band_standard_deviations": 2.0,
            "exit_mode": "vwap",
        },
        {
            "candidate_id": "vwap_reversion_2sd_1r",
            "band_standard_deviations": 2.0,
            "exit_mode": "1r",
        },
    ),
    "vwap_trend_pullback": (
        {
            "candidate_id": "vwap_trend_1close_1r",
            "confirmation_closes": 1,
            "reward_to_risk": 1.0,
        },
        {
            "candidate_id": "vwap_trend_1close_1p5r",
            "confirmation_closes": 1,
            "reward_to_risk": 1.5,
        },
        {
            "candidate_id": "vwap_trend_2close_1r",
            "confirmation_closes": 2,
            "reward_to_risk": 1.0,
        },
        {
            "candidate_id": "vwap_trend_2close_1p5r",
            "confirmation_closes": 2,
            "reward_to_risk": 1.5,
        },
    ),
    "intraday_compression_breakout": (
        {
            "candidate_id": "compression_0p5_1r",
            "compression_fraction_of_opening_range": 0.5,
            "reward_to_risk": 1.0,
        },
        {
            "candidate_id": "compression_0p5_1p5r",
            "compression_fraction_of_opening_range": 0.5,
            "reward_to_risk": 1.5,
        },
        {
            "candidate_id": "compression_0p75_1r",
            "compression_fraction_of_opening_range": 0.75,
            "reward_to_risk": 1.0,
        },
        {
            "candidate_id": "compression_0p75_1p5r",
            "compression_fraction_of_opening_range": 0.75,
            "reward_to_risk": 1.5,
        },
    ),
    "opening_drive_continuation": (
        {
            "candidate_id": "opening_drive_0p5_time",
            "minimum_drive_fraction": 0.5,
            "exit_mode": "time",
        },
        {
            "candidate_id": "opening_drive_0p5_1p5r",
            "minimum_drive_fraction": 0.5,
            "exit_mode": "1p5r_or_time",
        },
        {
            "candidate_id": "opening_drive_0p75_time",
            "minimum_drive_fraction": 0.75,
            "exit_mode": "time",
        },
        {
            "candidate_id": "opening_drive_0p75_1p5r",
            "minimum_drive_fraction": 0.75,
            "exit_mode": "1p5r_or_time",
        },
    ),
}


def build_exp009_candidates() -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []

    for family_id, family_candidates in FAMILY_CANDIDATES.items():
        for family_candidate in family_candidates:
            candidate = deepcopy(family_candidate)
            candidate["family_id"] = family_id
            candidates.append(candidate)

    return candidates


EXP009_CANDIDATES = build_exp009_candidates()


EXP009_PREREGISTRATION: dict[str, Any] = {
    "schema_version": 1,
    "experiment_id": "EXP-009",
    "title": "NQ/MNQ Multi-Strategy Discovery Tournament",
    "locked_date": "2026-07-19",
    "research_status": "PRE_REGISTERED",
    "implementation_status": "NOT_RUN",
    "results_viewed": "NONE",
    "purpose": (
        "Measure several structurally different intraday strategy "
        "families under one consistent data, execution and reporting "
        "standard. EXP-009 is a discovery and comparison experiment, "
        "not a pass/fail validation."
    ),
    "research_question": (
        "Which reproducible strategy families offer the most attractive "
        "combination of profitability, win rate, average trade, drawdown, "
        "consistency, cost resilience and practical trading behaviour?"
    ),
    "experiment_relationships": {
        "EXP-005": {
            "required_stage": "ACCEPTED_FOR_PAPER_TESTING",
            "must_remain_unchanged": True,
        },
        "EXP-006": {
            "required_stage": "REJECTED",
            "must_remain_unchanged": True,
        },
        "EXP-007": {
            "required_stage": "REJECTED",
            "must_remain_unchanged": True,
        },
        "EXP-008": {
            "required_stage": "REJECTED",
            "must_remain_unchanged": True,
        },
    },
    "interpretation": {
        "historical_status": (
            "EXPLORATORY_BECAUSE_2019_2025_HAS_ALREADY_BEEN_VIEWED"
        ),
        "no_single_pass_fail_decision": True,
        "no_automatic_winner": True,
        "lifecycle_result_after_measurement": "REVIEW",
        "live_trading_authorized": False,
        "paper_testing_authorized": False,
        "candidate_measurement_does_not_confirm_edge": True,
        "future_deep_validation_requires_new_experiment_ids": True,
    },
    "market_and_data": {
        "primary_measurement_market": "NQ",
        "secondary_implementation_market": "MNQ",
        "secondary_is_independent_confirmation": False,
        "data_source": (
            "Frozen EXP-005 Quantower/Lucid-Rithmic NQ and MNQ datasets"
        ),
        "historical_start": "2019-05-06",
        "historical_end": "2025-12-31",
        "source_timeframe": "1 minute",
        "signal_timeframe": "5 minutes",
        "research_timezone": "America/New_York",
        "cash_session": "09:30-16:00",
        "expected_included_sessions": 1639,
        "expected_one_minute_bars_per_session": 390,
        "available_columns": [
            "open",
            "high",
            "low",
            "close",
            "volume",
            "session_date",
            "minute_slot",
        ],
        "reuse_only_frozen_exp005_clean_sessions": True,
        "new_data_cleaning_decisions_prohibited": True,
        "missing_bar_fill_prohibited": True,
        "raw_source_editing_prohibited": True,
        "overnight_data_available": False,
        "previous_session_settlement_available": False,
    },
    "excluded_families": {
        "overnight_gap_continuation": (
            "Excluded because the frozen files begin at 09:30 and do not "
            "contain an independently verified overnight session or prior "
            "settlement."
        ),
        "overnight_gap_fade": (
            "Excluded for the same data-availability reason."
        ),
        "order_flow_delta": (
            "Excluded because the frozen OHLCV data do not contain "
            "bid/ask delta."
        ),
    },
    "shared_execution_and_risk_rules": {
        "completed_five_minute_signal_bars_only": True,
        "entry": "Next five-minute bar open after the completed signal.",
        "entry_uses_actual_open": True,
        "execution_resolution": "1 minute",
        "evaluate_exit_minutes_chronologically": True,
        "entry_minute_can_exit": True,
        "stop_gap_rule": (
            "If a one-minute bar opens through the protective stop, "
            "fill at the opening price; otherwise fill at the stop."
        ),
        "target_gap_rule": (
            "No favourable target price improvement; fill at the target."
        ),
        "same_minute_stop_and_target_rule": "STOP_FIRST_CONSERVATIVE",
        "forced_flat_time_new_york": "15:55",
        "forced_flat_price": "15:55 one-minute bar open",
        "maximum_completed_trades_per_candidate_per_session": 1,
        "same_day_reentry": False,
        "overnight_positions": False,
        "invalid_nonpositive_risk_trade": "DO_NOT_ENTER",
    },
    "position_sizing": {
        "method": "FIXED_ONE_CONTRACT",
        "NQ_contracts": 1,
        "MNQ_contracts": 1,
        "volatility_targeting_enabled": False,
        "reason": (
            "Discovery compares signal behaviour without allowing sizing "
            "to create an apparent edge."
        ),
    },
    "contract_and_cost_model": {
        "NQ": {
            "multiplier_usd_per_point": 20.0,
            "tick_size_points": 0.25,
            "fees_usd_per_side": 2.50,
            "base_slippage_ticks_per_side": 1.0,
            "base_round_trip_cost_usd": 15.0,
            "reference_capital_usd": 100000.0,
        },
        "MNQ": {
            "multiplier_usd_per_point": 2.0,
            "tick_size_points": 0.25,
            "fees_usd_per_side": 1.00,
            "base_slippage_ticks_per_side": 1.0,
            "base_round_trip_cost_usd": 3.0,
            "reference_capital_usd": 10000.0,
        },
        "nq_cost_sensitivity_ticks_per_side": [0, 1, 2],
    },
    "family_definitions": {
        "orb_pullback_continuation": {
            "opening_range_minutes": 30,
            "breakout": (
                "First completed five-minute close strictly outside the "
                "30-minute opening range."
            ),
            "retest_window_minutes": 30,
            "long_retest": (
                "After an upside breakout, a completed bar trades at or "
                "below the range high and closes strictly above it."
            ),
            "short_retest": (
                "Mirror rule after a downside breakout."
            ),
            "entry": "Next five-minute open after the qualifying retest.",
            "stop": "Opening-range midpoint.",
            "target": "Candidate reward_to_risk times actual entry risk.",
        },
        "failed_orb_reversal": {
            "opening_range_minutes": 30,
            "breakout": (
                "First completed five-minute close strictly outside the "
                "30-minute opening range."
            ),
            "failure": (
                "A later completed bar closes back inside the opening "
                "range within the candidate failure window."
            ),
            "direction_mode": "both",
            "entry": "Next five-minute open in the reversal direction.",
            "stop": (
                "Extreme high or low from the breakout bar through the "
                "failure bar, inclusive."
            ),
            "target": "Candidate reward_to_risk times actual entry risk.",
        },
        "vwap_mean_reversion": {
            "first_eligible_signal_time_new_york": "10:30",
            "vwap": (
                "Cash-session cumulative volume-weighted typical price, "
                "where typical price is (high + low + close) / 3."
            ),
            "band": (
                "Cash-session cumulative volume-weighted standard "
                "deviation around VWAP times the candidate multiplier."
            ),
            "setup": "Completed close strictly outside a VWAP band.",
            "signal": (
                "First later completed close back inside that same side's "
                "current band."
            ),
            "direction_mode": "both",
            "entry": "Next five-minute open toward VWAP.",
            "stop": (
                "Most adverse high or low from the outside-band setup "
                "through the re-entry signal, inclusive."
            ),
            "target": "Candidate exit_mode: current VWAP or fixed 1R.",
        },
        "vwap_trend_pullback": {
            "first_eligible_signal_time_new_york": "10:00",
            "trend_definition": (
                "Long when the latest completed close is above VWAP and "
                "VWAP is above its value three completed five-minute bars "
                "earlier; short uses the mirror rule."
            ),
            "pullback": (
                "A completed bar touches VWAP and closes on the trend side."
            ),
            "confirmation": (
                "Candidate one or two consecutive completed closes on the "
                "trend side, beginning with the pullback bar."
            ),
            "direction_mode": "both",
            "entry": "Next five-minute open after confirmation.",
            "stop": "Most adverse extreme across the confirmation bars.",
            "target": "Candidate reward_to_risk times actual entry risk.",
        },
        "intraday_compression_breakout": {
            "opening_range_minutes": 30,
            "first_eligible_compression_time_new_york": "10:30",
            "compression_window_minutes": 30,
            "compression": (
                "The earliest completed rolling 30-minute high-low range "
                "not exceeding the candidate fraction of the initial "
                "30-minute opening-range width."
            ),
            "breakout_window_minutes": 60,
            "signal": (
                "First completed close outside the frozen compression "
                "range within the following 60 minutes."
            ),
            "direction_mode": "both",
            "entry": "Next five-minute open in the breakout direction.",
            "stop": "Opposite compression boundary.",
            "target": "Candidate reward_to_risk times actual entry risk.",
        },
        "opening_drive_continuation": {
            "measurement_window": "09:30-10:00 New York",
            "drive": (
                "Absolute first-30-minute close-minus-open divided by the "
                "first-30-minute high-low range."
            ),
            "signal": (
                "Trade in the sign of the 30-minute return when drive is "
                "at least the candidate minimum fraction."
            ),
            "direction_mode": "both",
            "entry": "10:00 five-minute bar open.",
            "stop": "Opposite side of the 30-minute opening range.",
            "target": (
                "Candidate time exit only, or 1.5R target with the same "
                "15:55 time exit."
            ),
        },
    },
    "candidate_budget": {
        "family_count": 6,
        "candidates_per_family": 4,
        "total_candidates": 24,
        "candidates": EXP009_CANDIDATES,
        "candidate_additions_after_results_prohibited": True,
        "candidate_removals_after_results_prohibited": True,
    },
    "measurement_plan": {
        "primary_outputs": [
            "NQ base-cost trade ledger and equity",
            "MNQ base-cost implementation comparison",
            "NQ zero-, one- and two-tick cost sensitivity",
            "annual and monthly results",
            "rolling 100-trade Profit Factor and average trade",
            "drawdown depth, duration and recovery",
            "entry time, exit time, holding time and exit reasons",
            "profit concentration and trade distribution",
            "normalized NQ benchmark comparison",
        ],
        "performance_metrics": [
            "net_profit_usd",
            "gross_profit_usd",
            "gross_loss_usd",
            "trade_profit_factor",
            "completed_trades",
            "win_rate",
            "average_trade_usd",
            "median_trade_usd",
            "average_winner_usd",
            "average_loser_usd",
            "payoff_ratio",
        ],
        "risk_metrics": [
            "maximum_drawdown_usd",
            "maximum_drawdown_percent",
            "net_profit_to_drawdown",
            "longest_drawdown_duration",
            "longest_recovery_duration",
            "maximum_consecutive_losses",
            "worst_20_trade_result",
            "worst_50_trade_result",
            "worst_100_trade_result",
        ],
        "consistency_metrics": [
            "profitable_year_fraction",
            "profitable_month_fraction",
            "best_year_profit_contribution",
            "top_5_trade_profit_contribution",
            "rolling_profit_factor_stability",
        ],
        "practical_metrics": [
            "trades_per_year",
            "session_participation_rate",
            "average_holding_minutes",
            "median_holding_minutes",
            "average_trade_to_round_trip_cost",
        ],
    },
    "comparison_and_review": {
        "formal_accept_reject_gates": False,
        "single_composite_score": False,
        "automatic_strategy_winner": False,
        "pareto_views": [
            "profit_factor versus maximum_drawdown",
            "win_rate versus payoff_ratio",
            "average_trade_to_cost versus trade_count",
            "net_profit_to_drawdown versus drawdown_duration",
            "consistency versus cost_resilience",
        ],
        "reliability_flags_are_context_not_rejection": {
            "low_sample": "fewer than 150 completed trades",
            "concentrated_activity": "trades occur in fewer than 3 years",
            "cost_fragile": "two-tick NQ net profit is not positive",
            "mnq_divergence": "NQ and MNQ Profit Factors fall on opposite sides of 1.0",
        },
        "review_action": (
            "Display all 24 candidates and family summaries. The user may "
            "select up to three personally attractive finalists after "
            "reviewing the complete measurements."
        ),
        "finalist_count_maximum": 3,
        "finalist_selection_is_not_edge_confirmation": True,
        "each_finalist_requires_new_preregistered_deep_validation": True,
    },
    "deferred_expensive_tests": {
        "mcpt_run_in_exp009": False,
        "bootstrap_run_in_exp009": False,
        "family_optimization_run_in_exp009": False,
        "reason": (
            "EXP-009 is a broad measurement screen. Selection-aware MCPT, "
            "bootstrap analysis and family-specific optimization are "
            "reserved for separately preregistered finalist experiments."
        ),
    },
    "reporting_requirements": {
        "plain_english_what_and_how": True,
        "plain_english_what_happened_and_why": True,
        "main_dashboard_comparison_remains_separate_tab": True,
        "one_section_per_family": True,
        "all_24_candidate_table": True,
        "family_leader_table": True,
        "pareto_charts": True,
        "normalized_benchmark_comparison": True,
        "drawdown_and_recovery_visuals": True,
        "monthly_heatmaps": True,
        "trade_behaviour_visuals": True,
        "profit_concentration_visuals": True,
        "positive_numbers_use_neutral_text": True,
        "adverse_numbers_use_red_text": True,
        "green_reserved_for_status_words": True,
    },
    "prohibited_actions": [
        "Changing any EXP-005 through EXP-008 result or lifecycle decision.",
        "Using overnight gap strategies without independently verified overnight data.",
        "Using order-flow delta that is absent from the frozen OHLCV data.",
        "Adding or removing candidates after an EXP-009 result is viewed.",
        "Changing the common cost or execution model after results are viewed.",
        "Using variable position sizing or volatility targeting.",
        "Calling any discovery candidate a confirmed edge.",
        "Authorizing paper or live trading from EXP-009.",
        "Running MCPT, bootstrap or family optimization under EXP-009.",
        "Hiding candidates because their measurements are unattractive.",
    ],
}


def get_exp009_preregistration() -> dict[str, Any]:
    return deepcopy(EXP009_PREREGISTRATION)


def validate_exp009_preregistration(
    record: dict[str, Any] | None = None,
) -> None:
    current = EXP009_PREREGISTRATION if record is None else record

    if (
        current.get("schema_version") != 1
        or current.get("experiment_id") != "EXP-009"
        or current.get("research_status") != "PRE_REGISTERED"
        or current.get("implementation_status") != "NOT_RUN"
        or current.get("results_viewed") != "NONE"
    ):
        raise ValueError("EXP-009 identity or pre-result state changed.")

    relationships = current["experiment_relationships"]
    expected_stages = {
        "EXP-005": "ACCEPTED_FOR_PAPER_TESTING",
        "EXP-006": "REJECTED",
        "EXP-007": "REJECTED",
        "EXP-008": "REJECTED",
    }
    for experiment_id, stage in expected_stages.items():
        relationship = relationships[experiment_id]
        if (
            relationship["required_stage"] != stage
            or relationship["must_remain_unchanged"] is not True
        ):
            raise ValueError("EXP-009 prior-experiment boundary changed.")

    interpretation = current["interpretation"]
    if (
        interpretation["no_single_pass_fail_decision"] is not True
        or interpretation["no_automatic_winner"] is not True
        or interpretation["live_trading_authorized"] is not False
        or interpretation["paper_testing_authorized"] is not False
        or interpretation["future_deep_validation_requires_new_experiment_ids"]
        is not True
    ):
        raise ValueError("EXP-009 interpretation boundary changed.")

    data = current["market_and_data"]
    if (
        data["primary_measurement_market"] != "NQ"
        or data["secondary_implementation_market"] != "MNQ"
        or data["expected_included_sessions"] != 1639
        or data["expected_one_minute_bars_per_session"] != 390
        or data["reuse_only_frozen_exp005_clean_sessions"] is not True
        or data["overnight_data_available"] is not False
    ):
        raise ValueError("EXP-009 market/data lock changed.")

    excluded = current["excluded_families"]
    if (
        "overnight_gap_continuation" not in excluded
        or "overnight_gap_fade" not in excluded
        or "order_flow_delta" not in excluded
    ):
        raise ValueError("EXP-009 unavailable-data exclusions changed.")

    execution = current["shared_execution_and_risk_rules"]
    if (
        execution["completed_five_minute_signal_bars_only"] is not True
        or execution["execution_resolution"] != "1 minute"
        or execution["same_minute_stop_and_target_rule"]
        != "STOP_FIRST_CONSERVATIVE"
        or execution["forced_flat_time_new_york"] != "15:55"
        or execution["maximum_completed_trades_per_candidate_per_session"] != 1
        or execution["overnight_positions"] is not False
    ):
        raise ValueError("EXP-009 common execution rules changed.")

    sizing = current["position_sizing"]
    if (
        sizing["method"] != "FIXED_ONE_CONTRACT"
        or sizing["NQ_contracts"] != 1
        or sizing["MNQ_contracts"] != 1
        or sizing["volatility_targeting_enabled"] is not False
    ):
        raise ValueError("EXP-009 sizing isolation changed.")

    budget = current["candidate_budget"]
    expected_candidates = build_exp009_candidates()
    candidates = budget["candidates"]
    candidate_ids = [item["candidate_id"] for item in candidates]
    family_ids = [item["family_id"] for item in candidates]
    if (
        budget["family_count"] != 6
        or budget["candidates_per_family"] != 4
        or budget["total_candidates"] != 24
        or candidates != expected_candidates
        or len(candidate_ids) != 24
        or len(set(candidate_ids)) != 24
        or set(family_ids) != set(FAMILY_CANDIDATES)
        or any(family_ids.count(family_id) != 4 for family_id in FAMILY_CANDIDATES)
        or budget["candidate_additions_after_results_prohibited"] is not True
        or budget["candidate_removals_after_results_prohibited"] is not True
    ):
        raise ValueError("EXP-009 candidate budget changed.")

    review = current["comparison_and_review"]
    if (
        review["formal_accept_reject_gates"] is not False
        or review["single_composite_score"] is not False
        or review["automatic_strategy_winner"] is not False
        or review["finalist_count_maximum"] != 3
        or review["each_finalist_requires_new_preregistered_deep_validation"]
        is not True
    ):
        raise ValueError("EXP-009 comparison/review procedure changed.")

    deferred = current["deferred_expensive_tests"]
    if (
        deferred["mcpt_run_in_exp009"] is not False
        or deferred["bootstrap_run_in_exp009"] is not False
        or deferred["family_optimization_run_in_exp009"] is not False
    ):
        raise ValueError("EXP-009 discovery boundary changed.")

    reporting = current["reporting_requirements"]
    if (
        reporting["all_24_candidate_table"] is not True
        or reporting["pareto_charts"] is not True
        or reporting["positive_numbers_use_neutral_text"] is not True
        or reporting["adverse_numbers_use_red_text"] is not True
        or reporting["green_reserved_for_status_words"] is not True
    ):
        raise ValueError("EXP-009 reporting standard changed.")

    prohibited = " ".join(current["prohibited_actions"]).lower()
    for phrase in (
        "exp-005 through exp-008",
        "overnight gap",
        "order-flow delta",
        "adding or removing candidates",
        "variable position sizing",
        "confirmed edge",
        "paper or live trading",
        "mcpt, bootstrap or family optimization",
        "hiding candidates",
    ):
        if phrase not in prohibited:
            raise ValueError(f"EXP-009 prohibition missing: {phrase}.")

