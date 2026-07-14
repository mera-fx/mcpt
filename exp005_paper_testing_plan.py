from __future__ import annotations

from copy import deepcopy
from typing import Any

EXP005_PAPER_TESTING_PLAN: dict[str, Any] = {'schema_version': 1,
 'experiment_id': 'EXP-005',
 'status': 'ACCEPTED_FOR_PAPER_TESTING',
 'mode': 'paper_only_end_of_day_replay',
 'accepted_review_sha256': '3ac6538b1645f674174bb2716a893eb3ec8e1a131c64d05de438db5d12829751',
 'purpose': 'Observe the unchanged fixed NQ/MNQ 5-minute opening-range breakout '
            'prospectively and verify exact implementation, data handling and auditability '
            'before any separate future live-trading decision.',
 'data_workflow': {'source': 'Lucid Trading / Rithmic through Quantower History Exporter',
                   'symbols': ['NQ', 'MNQ'],
                   'provider_symbol_type': 'provider front month',
                   'data_type': 'Last',
                   'source_timeframe': '1 minute',
                   'timestamp_interpretation': 'UTC',
                   'session_timezone': 'America/New_York',
                   'paper_update_frequency': 'one export after each completed trading '
                                             'session',
                   'paper_processing': 'offline end-of-day replay only',
                   'live_market_connection_required': False,
                   'broker_order_connection_allowed': False},
 'research_roles': {'primary_evidence_market': 'NQ',
                    'contract_implementation_shadow': 'MNQ',
                    'both_contracts_recorded': True},
 'fixed_strategy_rules': {'opening_range_minutes': 15,
                          'direction_mode': 'both',
                          'signal': 'completed 5-minute bar closes strictly outside '
                                    'opening range',
                          'entry': 'next 5-minute bar open',
                          'final_signal_time_new_york': '11:55',
                          'final_entry_time_new_york': '12:00',
                          'protective_stop': 'opposite opening-range boundary',
                          'gap_through_stop': 'fill at bar open; otherwise boundary',
                          'entry_bar_can_stop': True,
                          'maximum_trades_per_session': 1,
                          'reversal_allowed': False,
                          'forced_flat_time_new_york': '15:55',
                          'forced_flat_price': '15:55 bar open',
                          'overnight_positions': False,
                          'optimization': False,
                          'parameter_combinations': 1},
 'cost_model': {'NQ': {'multiplier_usd_per_point': 20.0,
                       'tick_size_points': 0.25,
                       'fees_usd_per_side': 2.5,
                       'slippage_ticks_per_side': 1.0,
                       'round_trip_cost_usd': 15.0},
                'MNQ': {'multiplier_usd_per_point': 2.0,
                        'tick_size_points': 0.25,
                        'fees_usd_per_side': 1.0,
                        'slippage_ticks_per_side': 1.0,
                        'round_trip_cost_usd': 3.0}},
 'analytical_reference_capital': {'NQ_usd': 100000.0,
                                  'MNQ_usd': 10000.0,
                                  'multiplier_ratio': 10.0,
                                  'purpose': 'Provide a transparent fixed denominator for '
                                             'return and drawdown percentages in reports.',
                                  'not_a_margin_requirement': True,
                                  'not_a_live_account_recommendation': True},
 'minimum_observation': {'calendar_weeks': 12,
                         'completed_nq_trades': 40,
                         'completion_rule': 'Both minimums must be met.'},
 'operational_gates': {'closed_session_data_only': True,
                       'complete_one_minute_cash_session_required': True,
                       'maximum_unresolved_data_errors': 0,
                       'maximum_duplicate_processed_sessions': 0,
                       'maximum_duplicate_paper_trades': 0,
                       'maximum_strategy_rule_mismatches': 0,
                       'maximum_unexplained_reconciliation_errors': 0,
                       'maximum_trades_on_invalid_sessions': 0,
                       'complete_audit_log_required': True,
                       'source_file_sha256_required': True,
                       'rebuild_must_be_deterministic': True},
 'interpretation': {'primary_pass_fail_focus': 'Implementation fidelity, data integrity '
                                               'and deterministic reconciliation.',
                    'profitability_treatment': 'Paper profit, Profit Factor, win rate, '
                                               'return percentage and drawdown percentage '
                                               'are reported, but are not by themselves '
                                               'pass/fail criteria over the minimum '
                                               'observation.',
                    'future_live_decision': 'Requires a new separately locked decision '
                                            'after paper observation; acceptance here does '
                                            'not authorize live trading.'},
 'prohibited_actions': ['No live orders.',
                        'No broker or exchange order API connection.',
                        'No leverage decision under EXP-005.',
                        'No parameter changes.',
                        'No new filters, stops, targets or exits under EXP-005.',
                        'No optimization.',
                        'No rerun of quick transfer, confirmation validation, MCPT or '
                        'review.',
                        'No editing historical paper records after they are accepted.',
                        'No treating analytical reference capital as a margin '
                        'recommendation.']}


def get_exp005_paper_testing_plan() -> dict[str, Any]:
    return deepcopy(EXP005_PAPER_TESTING_PLAN)


def validate_exp005_paper_testing_plan(
    plan: dict[str, Any] | None = None,
) -> None:
    record = EXP005_PAPER_TESTING_PLAN if plan is None else plan

    if (
        record.get("schema_version") != 1
        or record.get("experiment_id") != "EXP-005"
        or record.get("status") != "ACCEPTED_FOR_PAPER_TESTING"
    ):
        raise ValueError("EXP-005 paper-plan identity changed.")

    if record.get("mode") != "paper_only_end_of_day_replay":
        raise ValueError("EXP-005 must begin with offline paper-only replay.")

    if record["accepted_review_sha256"] != "3ac6538b1645f674174bb2716a893eb3ec8e1a131c64d05de438db5d12829751":
        raise ValueError("EXP-005 paper plan is tied to another review result.")

    data = record["data_workflow"]
    if (
        data["symbols"] != ["NQ", "MNQ"]
        or data["data_type"] != "Last"
        or data["source_timeframe"] != "1 minute"
        or data["timestamp_interpretation"] != "UTC"
        or data["live_market_connection_required"] is not False
        or data["broker_order_connection_allowed"] is not False
    ):
        raise ValueError("EXP-005 paper data workflow changed.")

    rules = record["fixed_strategy_rules"]
    required_rules = {
        "opening_range_minutes": 15,
        "direction_mode": "both",
        "final_signal_time_new_york": "11:55",
        "final_entry_time_new_york": "12:00",
        "maximum_trades_per_session": 1,
        "reversal_allowed": False,
        "forced_flat_time_new_york": "15:55",
        "overnight_positions": False,
        "optimization": False,
        "parameter_combinations": 1,
    }
    for key, expected in required_rules.items():
        if rules[key] != expected:
            raise ValueError(f"EXP-005 paper rule changed: {key}.")

    expected_costs = {
        "NQ": {
            "multiplier_usd_per_point": 20.0,
            "tick_size_points": 0.25,
            "fees_usd_per_side": 2.5,
            "slippage_ticks_per_side": 1.0,
            "round_trip_cost_usd": 15.0,
        },
        "MNQ": {
            "multiplier_usd_per_point": 2.0,
            "tick_size_points": 0.25,
            "fees_usd_per_side": 1.0,
            "slippage_ticks_per_side": 1.0,
            "round_trip_cost_usd": 3.0,
        },
    }
    if record["cost_model"] != expected_costs:
        raise ValueError("EXP-005 paper cost model changed.")

    capital = record["analytical_reference_capital"]
    if (
        capital["NQ_usd"] != 100000.0
        or capital["MNQ_usd"] != 10000.0
        or capital["multiplier_ratio"] != 10.0
        or capital["not_a_margin_requirement"] is not True
        or capital["not_a_live_account_recommendation"] is not True
    ):
        raise ValueError("EXP-005 analytical capital basis changed.")

    observation = record["minimum_observation"]
    if (
        observation["calendar_weeks"] != 12
        or observation["completed_nq_trades"] != 40
        or observation["completion_rule"] != "Both minimums must be met."
    ):
        raise ValueError("EXP-005 paper observation requirement changed.")

    gates = record["operational_gates"]
    for key in (
        "maximum_unresolved_data_errors",
        "maximum_duplicate_processed_sessions",
        "maximum_duplicate_paper_trades",
        "maximum_strategy_rule_mismatches",
        "maximum_unexplained_reconciliation_errors",
        "maximum_trades_on_invalid_sessions",
    ):
        if gates[key] != 0:
            raise ValueError(f"{key} must remain zero.")

    for key in (
        "closed_session_data_only",
        "complete_one_minute_cash_session_required",
        "complete_audit_log_required",
        "source_file_sha256_required",
        "rebuild_must_be_deterministic",
    ):
        if gates[key] is not True:
            raise ValueError(f"{key} must remain true.")

    prohibited = " ".join(record["prohibited_actions"]).lower()
    for required in (
        "no live orders",
        "no parameter changes",
        "no optimization",
        "no rerun",
    ):
        if required not in prohibited:
            raise ValueError(f"EXP-005 paper prohibition changed: {required}.")


if __name__ == "__main__":
    validate_exp005_paper_testing_plan()
    print("EXP-005 paper-testing plan is valid and locked.")
