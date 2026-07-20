from __future__ import annotations

from copy import deepcopy
from typing import Any


FAMILY_CANDIDATES: dict[str, tuple[dict[str, Any], ...]] = {
    "gap_continuation": (
        {
            "candidate_id": "gap_continuation_0p25_time",
            "minimum_gap_fraction": 0.25,
            "exit_mode": "time",
        },
        {
            "candidate_id": "gap_continuation_0p25_1p5r",
            "minimum_gap_fraction": 0.25,
            "exit_mode": "1p5r_or_time",
        },
        {
            "candidate_id": "gap_continuation_0p50_time",
            "minimum_gap_fraction": 0.50,
            "exit_mode": "time",
        },
        {
            "candidate_id": "gap_continuation_0p50_1p5r",
            "minimum_gap_fraction": 0.50,
            "exit_mode": "1p5r_or_time",
        },
    ),
    "gap_fade": (
        {
            "candidate_id": "gap_fade_0p25_prior_close",
            "minimum_gap_fraction": 0.25,
            "exit_mode": "prior_cash_close_or_time",
        },
        {
            "candidate_id": "gap_fade_0p25_1r",
            "minimum_gap_fraction": 0.25,
            "exit_mode": "1r_or_time",
        },
        {
            "candidate_id": "gap_fade_0p50_prior_close",
            "minimum_gap_fraction": 0.50,
            "exit_mode": "prior_cash_close_or_time",
        },
        {
            "candidate_id": "gap_fade_0p50_1r",
            "minimum_gap_fraction": 0.50,
            "exit_mode": "1r_or_time",
        },
    ),
    "overnight_momentum_continuation": (
        {
            "candidate_id": "overnight_continuation_0p50_time",
            "minimum_drive_fraction": 0.50,
            "exit_mode": "time",
        },
        {
            "candidate_id": "overnight_continuation_0p50_1p5r",
            "minimum_drive_fraction": 0.50,
            "exit_mode": "1p5r_or_time",
        },
        {
            "candidate_id": "overnight_continuation_0p75_time",
            "minimum_drive_fraction": 0.75,
            "exit_mode": "time",
        },
        {
            "candidate_id": "overnight_continuation_0p75_1p5r",
            "minimum_drive_fraction": 0.75,
            "exit_mode": "1p5r_or_time",
        },
    ),
    "overnight_inventory_reversal": (
        {
            "candidate_id": "overnight_reversal_0p50_open",
            "minimum_drive_fraction": 0.50,
            "exit_mode": "overnight_open_or_time",
        },
        {
            "candidate_id": "overnight_reversal_0p50_1r",
            "minimum_drive_fraction": 0.50,
            "exit_mode": "1r_or_time",
        },
        {
            "candidate_id": "overnight_reversal_0p75_open",
            "minimum_drive_fraction": 0.75,
            "exit_mode": "overnight_open_or_time",
        },
        {
            "candidate_id": "overnight_reversal_0p75_1r",
            "minimum_drive_fraction": 0.75,
            "exit_mode": "1r_or_time",
        },
    ),
    "overnight_range_breakout": (
        {
            "candidate_id": "overnight_breakout_1030_1r",
            "last_signal_time": "10:30",
            "reward_to_risk": 1.0,
        },
        {
            "candidate_id": "overnight_breakout_1030_1p5r",
            "last_signal_time": "10:30",
            "reward_to_risk": 1.5,
        },
        {
            "candidate_id": "overnight_breakout_1200_1r",
            "last_signal_time": "12:00",
            "reward_to_risk": 1.0,
        },
        {
            "candidate_id": "overnight_breakout_1200_1p5r",
            "last_signal_time": "12:00",
            "reward_to_risk": 1.5,
        },
    ),
    "premarket_momentum_continuation": (
        {
            "candidate_id": "premarket_continuation_0p50_time",
            "minimum_drive_fraction": 0.50,
            "exit_mode": "time",
        },
        {
            "candidate_id": "premarket_continuation_0p50_1p5r",
            "minimum_drive_fraction": 0.50,
            "exit_mode": "1p5r_or_time",
        },
        {
            "candidate_id": "premarket_continuation_0p75_time",
            "minimum_drive_fraction": 0.75,
            "exit_mode": "time",
        },
        {
            "candidate_id": "premarket_continuation_0p75_1p5r",
            "minimum_drive_fraction": 0.75,
            "exit_mode": "1p5r_or_time",
        },
    ),
}


def build_exp012_candidates() -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for family_id, family_candidates in FAMILY_CANDIDATES.items():
        for family_candidate in family_candidates:
            candidate = deepcopy(family_candidate)
            candidate["family_id"] = family_id
            candidates.append(candidate)
    return candidates


EXP012_CANDIDATES = build_exp012_candidates()


EXP012_PREREGISTRATION: dict[str, Any] = {
    "schema_version": 1,
    "experiment_id": "EXP-012",
    "title": "NQ/MNQ Extended-Hours Context Discovery",
    "locked_date": "2026-07-20",
    "research_status": "PRE_REGISTERED",
    "implementation_status": "NOT_RUN",
    "results_viewed": "NONE",
    "purpose": (
        "Measure whether information formed outside the regular cash "
        "session helps describe attractive cash-session trading ideas. "
        "The experiment compares six extended-hours strategy families "
        "under one common execution, cost and reporting standard."
    ),
    "research_question": (
        "Which overnight, premarket and opening-gap contexts provide the "
        "best measured combination of profitability, win rate, drawdown, "
        "consistency, cost resilience and practical trading behaviour?"
    ),
    "relationship_to_prior_research": {
        "extended_session_data_result_must_verify": True,
        "cash_outcomes_from_2020_2025_have_been_viewed": True,
        "extended_hour_features_have_not_been_strategy_tested": True,
        "historical_status": (
            "EXPLORATORY_EXTENDED_CONTEXT_ON_PREVIOUSLY_VIEWED_CASH_YEARS"
        ),
        "independent_confirmation": False,
        "prior_experiments_must_remain_unchanged": True,
    },
    "required_lifecycle_stages": {
        "EXP-005": "ACCEPTED_FOR_PAPER_TESTING",
        "EXP-006": "REJECTED",
        "EXP-007": "REJECTED",
        "EXP-008": "REJECTED",
        "EXP-009": "REVIEW",
        "EXP-010": "REVIEW",
        "EXP-011": "REVIEW",
    },
    "interpretation": {
        "measurement_first": True,
        "no_single_pass_fail_decision": True,
        "no_automatic_winner": True,
        "lifecycle_result_after_measurement": "REVIEW",
        "candidate_measurement_does_not_confirm_edge": True,
        "paper_trading_authorized": False,
        "live_trading_authorized": False,
        "future_deep_validation_requires_new_experiment_id": True,
    },
    "market_and_data": {
        "primary_measurement_market": "NQ",
        "secondary_implementation_market": "MNQ",
        "secondary_is_independent_confirmation": False,
        "data_source": "Frozen aligned extended-session NQ/MNQ dataset",
        "dataset_result_file": (
            "research/EXTENDED_SESSION_DATA_RESULT.json"
        ),
        "historical_start": "2020-01-02",
        "historical_end": "2025-12-31",
        "included_years": [2020, 2021, 2022, 2023, 2024, 2025],
        "expected_complete_aligned_sessions": 1331,
        "source_timeframe": "1 minute",
        "signal_timeframe": "5 minutes",
        "research_timezone": "America/New_York",
        "full_session": "18:00 prior trade date through 16:59 session date",
        "overnight_window": "18:00-09:30",
        "premarket_window": "08:00-09:30",
        "cash_session": "09:30-16:00",
        "post_cash_window": "16:00-17:00",
        "required_segments": [
            "evening",
            "overnight",
            "premarket",
            "cash",
            "post_cash",
        ],
        "use_only_complete_aligned_nq_mnq_sessions": True,
        "exclude_2019_due_to_limited_aligned_coverage": True,
        "missing_bar_fill_prohibited": True,
        "source_editing_prohibited": True,
        "new_data_cleaning_decisions_prohibited": True,
    },
    "feature_definitions": {
        "previous_cash_close": (
            "The final one-minute close before 16:00 on the immediately "
            "preceding exchange trade date. If that trade date is not a "
            "complete aligned included session, gap families do not trade."
        ),
        "previous_cash_range": (
            "High minus low from 09:30 through 15:59 on that same "
            "immediately preceding complete aligned session."
        ),
        "gap_fraction": (
            "Absolute 09:30 open minus previous cash close, divided by "
            "previous cash range. A zero or nonpositive denominator is "
            "ineligible."
        ),
        "overnight_drive_fraction": (
            "Absolute 09:29 close minus 18:00 open, divided by the "
            "18:00-through-09:29 high-low range."
        ),
        "premarket_drive_fraction": (
            "Absolute 09:29 close minus 08:00 open, divided by the "
            "08:00-through-09:29 high-low range."
        ),
        "direction_zero_rule": "A zero directional return is ineligible.",
        "fraction_boundary_rule": (
            "A feature qualifies when its fraction is greater than or "
            "equal to the candidate threshold."
        ),
    },
    "shared_execution_and_risk_rules": {
        "entries_during_cash_session_only": True,
        "overnight_positions": False,
        "completed_five_minute_signal_bars_only": True,
        "entry": "Next five-minute bar open after the completed signal.",
        "entry_uses_actual_open": True,
        "execution_resolution": "1 minute",
        "evaluate_exit_minutes_chronologically": True,
        "entry_minute_can_exit": True,
        "same_minute_stop_and_target_rule": "STOP_FIRST_CONSERVATIVE",
        "stop_gap_rule": (
            "If a one-minute bar opens through the protective stop, fill "
            "at that opening price; otherwise fill at the stop."
        ),
        "target_gap_rule": (
            "No favourable target improvement; fill at the target."
        ),
        "forced_flat_time_new_york": "15:55",
        "forced_flat_price": "15:55 one-minute bar open",
        "maximum_completed_trades_per_candidate_per_session": 1,
        "same_day_reentry": False,
        "invalid_nonpositive_risk_trade": "DO_NOT_ENTER",
    },
    "position_sizing": {
        "method": "FIXED_ONE_CONTRACT",
        "NQ_contracts": 1,
        "MNQ_contracts": 1,
        "volatility_targeting_enabled": False,
        "reason": (
            "The discovery comparison measures signal behaviour without "
            "allowing sizing to manufacture an apparent advantage."
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
        "overnight_execution_cost_model_claimed": False,
    },
    "family_definitions": {
        "gap_continuation": {
            "plain_english": (
                "A meaningful opening gap may continue when the first "
                "five-minute cash bar also moves in the gap direction."
            ),
            "setup": "Gap fraction meets the candidate threshold.",
            "signal": (
                "The 09:30-09:35 completed bar closes beyond its open in "
                "the same direction as the gap."
            ),
            "direction_mode": "both",
            "entry": "09:35 five-minute bar open.",
            "stop": "Opposite extreme of the 09:30-09:35 bar.",
            "target": "Candidate time exit or 1.5R with time exit.",
        },
        "gap_fade": {
            "plain_english": (
                "A meaningful opening gap may reverse when the first "
                "five-minute cash bar starts moving back toward the "
                "previous cash close."
            ),
            "setup": "Gap fraction meets the candidate threshold.",
            "signal": (
                "The 09:30-09:35 completed bar closes beyond its open in "
                "the direction opposite the gap."
            ),
            "direction_mode": "both",
            "entry": "09:35 five-minute bar open toward prior cash close.",
            "stop": "Outer extreme of the 09:30-09:35 bar.",
            "target": (
                "Candidate previous-cash-close target or 1R target, both "
                "with the same time exit."
            ),
        },
        "overnight_momentum_continuation": {
            "plain_english": (
                "A directional overnight move may continue after the "
                "cash open when the first cash bar agrees."
            ),
            "setup": (
                "Overnight drive fraction meets the candidate threshold."
            ),
            "signal": (
                "The 09:30-09:35 completed bar closes beyond its open in "
                "the overnight direction."
            ),
            "direction_mode": "both",
            "entry": "09:35 five-minute bar open.",
            "stop": "Opposite extreme of the 09:30-09:35 bar.",
            "target": "Candidate time exit or 1.5R with time exit.",
        },
        "overnight_inventory_reversal": {
            "plain_english": (
                "A directional overnight move may represent inventory "
                "that reverses after the cash session opens."
            ),
            "setup": (
                "Overnight drive fraction meets the candidate threshold."
            ),
            "signal": (
                "The 09:30-09:35 completed bar closes beyond its open "
                "opposite the overnight direction."
            ),
            "direction_mode": "both",
            "entry": "09:35 five-minute bar open.",
            "stop": "Outer extreme of the 09:30-09:35 bar.",
            "target": (
                "Candidate 18:00 overnight-open target or 1R target, both "
                "with the same time exit."
            ),
        },
        "overnight_range_breakout": {
            "plain_english": (
                "The overnight high and low form a range; a cash-session "
                "close beyond that range may begin a continuation move."
            ),
            "frozen_range": "18:00 through 09:29 high and low.",
            "signal": (
                "First completed cash-session five-minute close strictly "
                "above the overnight high or below the overnight low, no "
                "later than the candidate last signal time."
            ),
            "direction_mode": "both",
            "entry": "Next five-minute bar open.",
            "stop": "Opposite extreme of the breakout signal bar.",
            "target": "Candidate reward-to-risk target with time exit.",
        },
        "premarket_momentum_continuation": {
            "plain_english": (
                "A directional move during the final 90 minutes before "
                "the cash open may continue when the first cash bar agrees."
            ),
            "setup": (
                "Premarket drive fraction meets the candidate threshold."
            ),
            "signal": (
                "The 09:30-09:35 completed bar closes beyond its open in "
                "the premarket direction."
            ),
            "direction_mode": "both",
            "entry": "09:35 five-minute bar open.",
            "stop": "Opposite extreme of the 09:30-09:35 bar.",
            "target": "Candidate time exit or 1.5R with time exit.",
        },
    },
    "candidate_budget": {
        "family_count": 6,
        "candidates_per_family": 4,
        "total_candidates": 24,
        "candidates": EXP012_CANDIDATES,
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
            "extended-hours feature coverage and distributions",
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
        "context_metrics": [
            "feature_eligible_sessions",
            "signal_confirmed_sessions",
            "feature_fraction_distribution",
            "gap_size_distribution",
            "overnight_direction_balance",
            "premarket_direction_balance",
        ],
    },
    "comparison_and_review": {
        "formal_accept_reject_gates": False,
        "single_composite_score": False,
        "automatic_strategy_winner": False,
        "all_candidates_remain_visible": True,
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
            "mnq_divergence": (
                "NQ and MNQ Profit Factors fall on opposite sides of 1.0"
            ),
        },
        "finalist_count_maximum": 3,
        "finalist_selection_is_not_edge_confirmation": True,
        "each_finalist_requires_new_preregistered_deep_validation": True,
    },
    "deferred_expensive_tests": {
        "mcpt_run_in_exp012": False,
        "bootstrap_run_in_exp012": False,
        "walk_forward_run_in_exp012": False,
        "family_optimization_run_in_exp012": False,
        "reason": (
            "EXP-012 is a broad measurement screen. Expensive statistical "
            "testing and family optimization are reserved for separately "
            "preregistered finalists the user actually wants to develop."
        ),
    },
    "reporting_requirements": {
        "plain_english_strategy_explanation_for_every_family": True,
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
        "extended_context_visuals": True,
        "chart_canvas_is_solid_opaque_white": True,
        "positive_numbers_use_neutral_text": True,
        "adverse_numbers_use_red_text": True,
        "green_reserved_for_status_words": True,
    },
    "prohibited_actions": [
        "Changing any frozen prior experiment result or lifecycle decision.",
        "Editing or rebuilding the frozen extended-session data.",
        "Synthesizing missing bars or using incomplete sessions.",
        "Entering positions before the 09:30 cash-session open.",
        "Claiming the cash-session cost model validates overnight execution.",
        "Adding or removing candidates after an EXP-012 result is viewed.",
        "Changing common costs or execution after results are viewed.",
        "Using variable position sizing or volatility targeting.",
        "Calling a discovery candidate a confirmed edge.",
        "Authorizing paper or live trading from EXP-012.",
        "Running MCPT, bootstrap, walk-forward or optimization under EXP-012.",
        "Hiding candidates because their measurements are unattractive.",
    ],
}


def get_exp012_preregistration() -> dict[str, Any]:
    return deepcopy(EXP012_PREREGISTRATION)


def validate_exp012_preregistration(
    record: dict[str, Any] | None = None,
) -> None:
    current = EXP012_PREREGISTRATION if record is None else record

    if (
        current.get("schema_version") != 1
        or current.get("experiment_id") != "EXP-012"
        or current.get("research_status") != "PRE_REGISTERED"
        or current.get("implementation_status") != "NOT_RUN"
        or current.get("results_viewed") != "NONE"
    ):
        raise ValueError("EXP-012 identity or pre-result state changed.")

    relationship = current["relationship_to_prior_research"]
    if (
        relationship["extended_session_data_result_must_verify"] is not True
        or relationship["extended_hour_features_have_not_been_strategy_tested"]
        is not True
        or relationship["independent_confirmation"] is not False
        or relationship["prior_experiments_must_remain_unchanged"] is not True
    ):
        raise ValueError("EXP-012 research boundary changed.")

    expected_stages = {
        "EXP-005": "ACCEPTED_FOR_PAPER_TESTING",
        "EXP-006": "REJECTED",
        "EXP-007": "REJECTED",
        "EXP-008": "REJECTED",
        "EXP-009": "REVIEW",
        "EXP-010": "REVIEW",
        "EXP-011": "REVIEW",
    }
    if current["required_lifecycle_stages"] != expected_stages:
        raise ValueError("EXP-012 prior lifecycle lock changed.")

    interpretation = current["interpretation"]
    if (
        interpretation["measurement_first"] is not True
        or interpretation["no_single_pass_fail_decision"] is not True
        or interpretation["no_automatic_winner"] is not True
        or interpretation["paper_trading_authorized"] is not False
        or interpretation["live_trading_authorized"] is not False
        or interpretation["future_deep_validation_requires_new_experiment_id"]
        is not True
    ):
        raise ValueError("EXP-012 interpretation boundary changed.")

    data = current["market_and_data"]
    if (
        data["primary_measurement_market"] != "NQ"
        or data["secondary_implementation_market"] != "MNQ"
        or data["included_years"] != [2020, 2021, 2022, 2023, 2024, 2025]
        or data["expected_complete_aligned_sessions"] != 1331
        or data["use_only_complete_aligned_nq_mnq_sessions"] is not True
        or data["exclude_2019_due_to_limited_aligned_coverage"] is not True
        or data["missing_bar_fill_prohibited"] is not True
        or data["source_editing_prohibited"] is not True
    ):
        raise ValueError("EXP-012 market/data lock changed.")

    features = current["feature_definitions"]
    if (
        "immediately preceding exchange trade date"
        not in features["previous_cash_close"]
        or "09:29 close minus 18:00 open"
        not in features["overnight_drive_fraction"]
        or "09:29 close minus 08:00 open"
        not in features["premarket_drive_fraction"]
        or features["direction_zero_rule"]
        != "A zero directional return is ineligible."
    ):
        raise ValueError("EXP-012 feature definitions changed.")

    execution = current["shared_execution_and_risk_rules"]
    if (
        execution["entries_during_cash_session_only"] is not True
        or execution["overnight_positions"] is not False
        or execution["completed_five_minute_signal_bars_only"] is not True
        or execution["execution_resolution"] != "1 minute"
        or execution["same_minute_stop_and_target_rule"]
        != "STOP_FIRST_CONSERVATIVE"
        or execution["forced_flat_time_new_york"] != "15:55"
        or execution["maximum_completed_trades_per_candidate_per_session"] != 1
    ):
        raise ValueError("EXP-012 common execution rules changed.")

    sizing = current["position_sizing"]
    if (
        sizing["method"] != "FIXED_ONE_CONTRACT"
        or sizing["NQ_contracts"] != 1
        or sizing["MNQ_contracts"] != 1
        or sizing["volatility_targeting_enabled"] is not False
    ):
        raise ValueError("EXP-012 sizing isolation changed.")

    costs = current["contract_and_cost_model"]
    if (
        costs["NQ"]["base_round_trip_cost_usd"] != 15.0
        or costs["MNQ"]["base_round_trip_cost_usd"] != 3.0
        or costs["nq_cost_sensitivity_ticks_per_side"] != [0, 1, 2]
        or costs["overnight_execution_cost_model_claimed"] is not False
    ):
        raise ValueError("EXP-012 contract/cost model changed.")

    budget = current["candidate_budget"]
    expected_candidates = build_exp012_candidates()
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
        or any(
            family_ids.count(family_id) != 4
            for family_id in FAMILY_CANDIDATES
        )
        or budget["candidate_additions_after_results_prohibited"] is not True
        or budget["candidate_removals_after_results_prohibited"] is not True
    ):
        raise ValueError("EXP-012 candidate budget changed.")

    families = current["family_definitions"]
    if set(families) != set(FAMILY_CANDIDATES):
        raise ValueError("EXP-012 family definitions changed.")
    if any(
        not family["plain_english"].strip()
        for family in families.values()
    ):
        raise ValueError("EXP-012 plain-English family explanation missing.")

    review = current["comparison_and_review"]
    if (
        review["formal_accept_reject_gates"] is not False
        or review["single_composite_score"] is not False
        or review["automatic_strategy_winner"] is not False
        or review["all_candidates_remain_visible"] is not True
        or review["finalist_count_maximum"] != 3
        or review["each_finalist_requires_new_preregistered_deep_validation"]
        is not True
    ):
        raise ValueError("EXP-012 comparison/review procedure changed.")

    deferred = current["deferred_expensive_tests"]
    if any(
        deferred[key] is not False
        for key in (
            "mcpt_run_in_exp012",
            "bootstrap_run_in_exp012",
            "walk_forward_run_in_exp012",
            "family_optimization_run_in_exp012",
        )
    ):
        raise ValueError("EXP-012 discovery boundary changed.")

    reporting = current["reporting_requirements"]
    if (
        reporting["plain_english_strategy_explanation_for_every_family"]
        is not True
        or reporting["all_24_candidate_table"] is not True
        or reporting["extended_context_visuals"] is not True
        or reporting["chart_canvas_is_solid_opaque_white"] is not True
        or reporting["positive_numbers_use_neutral_text"] is not True
        or reporting["adverse_numbers_use_red_text"] is not True
        or reporting["green_reserved_for_status_words"] is not True
    ):
        raise ValueError("EXP-012 reporting standard changed.")

    prohibited = " ".join(current["prohibited_actions"]).lower()
    for phrase in (
        "frozen extended-session data",
        "incomplete sessions",
        "before the 09:30",
        "overnight execution",
        "confirmed edge",
        "paper or live trading",
    ):
        if phrase not in prohibited:
            raise ValueError("EXP-012 prohibited-action boundary changed.")


if __name__ == "__main__":
    validate_exp012_preregistration()
    print("EXP-012 preregistration is valid and result-free.")
