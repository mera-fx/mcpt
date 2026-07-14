from __future__ import annotations

from copy import deepcopy
from typing import Any

EXP005_REVIEW_IMPLEMENTATION: dict[str, Any] = {'schema_version': 1,
 'experiment_id': 'EXP-005',
 'stage': 'REVIEW',
 'locked_date': '2026-07-14',
 'status': 'LOCKED_AFTER_FULL_PASS_BEFORE_REVIEW_DECISION',
 'review_type': 'READ_ONLY_OPERATIONAL_QUALITY_REVIEW',
 'source_full_validation_commit': '1dc8b32f2eba1b19e19d3162d5f0acd2f820593e',
 'source_full_validation_result_sha256': '7d2a3d1eb8716851fc913482c55809c360959b7a5d9eb3e474389b21131b6987',
 'protections': {'strategy_rerun': False,
                 'mcpt_rerun': False,
                 'parameter_change': False,
                 'cost_change': False,
                 'data_change': False,
                 'gate_change': False,
                 'review_decision_calculated': False,
                 'automatic_lifecycle_edit_after_review': False},
 'all_checks_required': True,
 'checks': {'full_validation_integrity': {'decision': 'PASS_TO_REVIEW',
                                          'permutations': 1000,
                                          'maximum_mcpt_p_value': 0.05},
            'fixed_rule_integrity': {'opening_range_minutes': 15,
                                     'direction_mode': 'both',
                                     'parameter_combinations': 1,
                                     'optimization': False},
            'data_integrity': {'included_sessions': 733,
                               'maximum_included_invalid_sessions': 0,
                               'maximum_included_mismatch_sessions': 0},
            'cross_period_replication': {'minimum_profit_factor_strict': 1.0,
                                         'minimum_net_profit_usd_strict': 0.0},
            'all_confirmation_years_profitable': {'required_years': [2023, 2024, 2025]},
            'two_tick_cost_resilience': {'slippage_ticks_per_side': 2.0,
                                         'minimum_profit_factor_strict': 1.0,
                                         'minimum_net_profit_usd_strict': 0.0},
            'average_trade_cost_buffer': {'minimum_average_trade_to_round_trip_cost': 2.0},
            'drawdown_efficiency': {'minimum_net_profit_to_maximum_drawdown': 2.0},
            'contract_implementation_consistency': {'maximum_trade_count_difference': 2,
                                                    'maximum_profit_factor_difference': 0.1,
                                                    'maximum_scaled_net_profit_difference': 0.2,
                                                    'nq_to_mnq_multiplier_ratio': 10.0},
            'direction_balance': {'minimum_each_direction_share': 0.4},
            'tail_loss_concentration': {'maximum_top_five_loss_share': 0.2},
            'largest_loss_drawdown_share': {'maximum_largest_loss_share_of_drawdown': 0.3}},
 'pass_action': 'ACCEPT_FOR_PAPER_TESTING',
 'failure_action': 'REJECT',
 'interpretation': 'Paper-testing acceptance authorizes only a separate paper-only '
                   'simulator using unchanged fixed rules and locked cost assumptions. '
                   'It does not authorize live capital.'}

def get_exp005_review_implementation() -> dict[str, Any]:
    return deepcopy(EXP005_REVIEW_IMPLEMENTATION)

def validate_exp005_review_implementation(
    record: dict[str, Any] | None = None,
) -> None:
    current = EXP005_REVIEW_IMPLEMENTATION if record is None else record
    if (
        current.get("schema_version") != 1
        or current.get("experiment_id") != "EXP-005"
        or current.get("stage") != "REVIEW"
    ):
        raise ValueError("EXP-005 review implementation identity changed.")
    if current.get("status") != "LOCKED_AFTER_FULL_PASS_BEFORE_REVIEW_DECISION":
        raise ValueError("EXP-005 review was not locked before its decision.")
    if current.get("review_type") != "READ_ONLY_OPERATIONAL_QUALITY_REVIEW":
        raise ValueError("EXP-005 review type changed.")
    if current.get("source_full_validation_result_sha256") != "7d2a3d1eb8716851fc913482c55809c360959b7a5d9eb3e474389b21131b6987":
        raise ValueError("EXP-005 review source result changed.")
    expected_protections = {
        "strategy_rerun": False,
        "mcpt_rerun": False,
        "parameter_change": False,
        "cost_change": False,
        "data_change": False,
        "gate_change": False,
        "review_decision_calculated": False,
        "automatic_lifecycle_edit_after_review": False,
    }
    if current["protections"] != expected_protections:
        raise ValueError("EXP-005 review protections changed.")
    if current["all_checks_required"] is not True:
        raise ValueError("Every EXP-005 review check is required.")
    expected_names = {
        "full_validation_integrity",
        "fixed_rule_integrity",
        "data_integrity",
        "cross_period_replication",
        "all_confirmation_years_profitable",
        "two_tick_cost_resilience",
        "average_trade_cost_buffer",
        "drawdown_efficiency",
        "contract_implementation_consistency",
        "direction_balance",
        "tail_loss_concentration",
        "largest_loss_drawdown_share",
    }
    if set(current["checks"]) != expected_names:
        raise ValueError("EXP-005 review check set changed.")
    if (
        current["pass_action"] != "ACCEPT_FOR_PAPER_TESTING"
        or current["failure_action"] != "REJECT"
    ):
        raise ValueError("EXP-005 review actions changed.")

if __name__ == "__main__":
    validate_exp005_review_implementation()
    print("EXP-005 read-only review implementation is valid.")
