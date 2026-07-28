from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any


EXP027_EXECUTION_AUTHORIZATION: dict[str, Any] = {'schema_version': 1,
 'experiment_id': 'EXP-027',
 'title': 'EXP-027 Protected 2026 Measurement Execution Authorisation',
 'authorized_date': '2026-07-28',
 'authorization_status': 'AUTHORIZED',
 'execution_authorized': True,
 'one_time_run': True,
 'maximum_runs': 1,
 'preregistration_commit': '21c182e119cde651e6c4fe22b1e4e8d6b99def5b',
 'preregistration_sha256': '3177e5bb81bbf330b8a020c3bfee56b584cd284da3546fcdad4b90df5ffd76bd',
 'locked_implementation_commit': '591cdf43b4c23abc312ae3d50b7d7948f88c90b2',
 'locked_exp026_engine_commit': '13ee0683dfcbbb5d763f7254f3b245ecc8e6d9cd',
 'exp026_closure_commit': '7fc1994e396bfb237fd5f05f5a4298e6c5b5e307',
 'exp026_closure_sha256': '8ec79810a26b58f2d445d47d3f496539f121d6f3e139eae4a9fd38ef029a386f',
 'protected_2026_access_authorized': True,
 'new_databento_download_authorized': False,
 'network_access_authorized': False,
 'paper_trading_authorized': False,
 'live_trading_authorized': False,
 'candidate_scope': {'strategy_candidate_ids': ('gap_fade_0p25_prior_close',
                                                'gap_fade_0p25_1r',
                                                'gap_fade_0p50_prior_close',
                                                'gap_fade_0p50_1r',
                                                'gap_fade_0p75_prior_close',
                                                'gap_fade_0p75_1r',
                                                'premarket_continuation_0p50_time',
                                                'premarket_continuation_0p50_1p5r',
                                                'premarket_continuation_0p625_time',
                                                'premarket_continuation_0p625_1p5r',
                                                'premarket_continuation_0p75_time',
                                                'premarket_continuation_0p75_1p5r',
                                                'premarket_continuation_0p875_time',
                                                'premarket_continuation_0p875_1p5r',
                                                'opening_drive_0p25_time',
                                                'opening_drive_0p25_1p5r',
                                                'opening_drive_0p50_time',
                                                'opening_drive_0p50_1p5r',
                                                'opening_drive_0p75_time',
                                                'opening_drive_0p75_1p5r',
                                                'opening_drive_1p00_time',
                                                'opening_drive_1p00_1p5r'),
                     'control_candidate_ids': ('orb_control_exp005_15m_both_time',
                                               'orb_control_exp007_30m_long_1r'),
                     'reported_ids': ('gap_fade_0p25_prior_close',
                                      'gap_fade_0p25_1r',
                                      'gap_fade_0p50_prior_close',
                                      'gap_fade_0p50_1r',
                                      'gap_fade_0p75_prior_close',
                                      'gap_fade_0p75_1r',
                                      'premarket_continuation_0p50_time',
                                      'premarket_continuation_0p50_1p5r',
                                      'premarket_continuation_0p625_time',
                                      'premarket_continuation_0p625_1p5r',
                                      'premarket_continuation_0p75_time',
                                      'premarket_continuation_0p75_1p5r',
                                      'premarket_continuation_0p875_time',
                                      'premarket_continuation_0p875_1p5r',
                                      'opening_drive_0p25_time',
                                      'opening_drive_0p25_1p5r',
                                      'opening_drive_0p50_time',
                                      'opening_drive_0p50_1p5r',
                                      'opening_drive_0p75_time',
                                      'opening_drive_0p75_1p5r',
                                      'opening_drive_1p00_time',
                                      'opening_drive_1p00_1p5r',
                                      'orb_control_exp005_15m_both_time',
                                      'orb_control_exp007_30m_long_1r'),
                     'strategy_candidate_count': 22,
                     'control_candidate_count': 2,
                     'reported_count': 24,
                     'primary_confirmation_cohort': ('gap_fade_0p75_1r',
                                                     'opening_drive_0p75_time',
                                                     'premarket_continuation_0p875_1p5r'),
                     'primary_count': 3,
                     'candidate_selection': False,
                     'candidate_reselection': False,
                     'secondary_candidate_promotion': False,
                     'parameter_changes': False,
                     'position_sizing_changes': False,
                     'portfolio_weight_changes': False,
                     'single_winner_selection': False,
                     'formal_accept_reject_gate': False},
 'protected_measurement_scope': {'mode': 'PROTECTED_2026_MEASUREMENT',
                                 'session_start': '2026-01-01',
                                 'session_end': '2026-07-23',
                                 'partial_year': True,
                                 'source_timestamp_timezone': 'UTC',
                                 'research_timezone': 'America/New_York',
                                 'primary_representation': 'BACKWARD_ADJUSTED',
                                 'sensitivity_representation': 'UNADJUSTED',
                                 'unadjusted_is_sensitivity_only': True,
                                 'unadjusted_can_change_primary_cohort': False,
                                 'cost_sensitivity_ticks_per_side': (0, 1, 2, 3),
                                 'fixed_one_nq_contract': True,
                                 'base_round_trip_cost_usd': 15.0,
                                 'same_minute_stop_target_rule': 'STOP_FIRST_CONSERVATIVE'},
 'representation_scope': {'representations': {'BACKWARD_ADJUSTED': {'role': 'PRIMARY_PROTECTED_MEASUREMENT_SERIES',
                                                                    'path': 'results/EXP-022/selected_continuous_series/selected_roll_backward_adjusted.parquet',
                                                                    'size_bytes': 71964074,
                                                                    'sha256': '61ccb3621b53fa313147a866948ec1f2c7a6b36956d2ba26090162b518c30c84',
                                                                    'semantic_sha256': '3c6fa83821183ca54bc547c555834ceb16a126be50f90d8c6db5684220929951'},
                                              'UNADJUSTED': {'role': 'REPRESENTATION_SENSITIVITY_ONLY',
                                                             'path': 'results/EXP-022/selected_continuous_series/selected_roll_unadjusted.parquet',
                                                             'size_bytes': 73760121,
                                                             'sha256': '606a69bbba4f4a5db3e0356d7b2849f9481e4555dc24cae4c6b9d1d12f673ab1',
                                                             'semantic_sha256': '29daf3f20b022fb69967349095eb9663bd04276cbc5743a65b1ecabc33113640'}},
                          'both_representations_read_only': True,
                          'roll_rule_change_authorized': False,
                          'adjustment_method_change_authorized': False,
                          'source_series_modification_authorized': False},
 'data_access_boundary': {'parquet_filter_pushdown_required': True,
                          'filter_applied_before_table_materialization': True,
                          'minimum_materialized_trading_date': '2026-01-01',
                          'maximum_materialized_trading_date': '2026-07-23',
                          'historical_2010_2025_market_access_authorized': False,
                          'protected_2026_access_authorized': True,
                          'backward_adjusted_access_authorized': True,
                          'unadjusted_access_authorized': True,
                          'new_databento_download_authorized': False,
                          'databento_api_calls_authorized': 0,
                          'network_access_authorized': False,
                          'order_api_access_authorized': False,
                          'missing_bar_fill_authorized': False,
                          'synthetic_bar_creation_authorized': False},
 'execution_boundary': {'repository_must_be_clean': True,
                        'branch_must_be_main': True,
                        'local_and_origin_must_align': True,
                        'authorization_commit_must_equal_head': True,
                        'implementation_commit_must_be_locked': True,
                        'output_directory_must_not_exist': True,
                        'partial_output_directory_must_not_exist': True,
                        'independent_rebuild_required': True,
                        'serial_parallel_parity_required': True,
                        'required_output_hash_manifest': True,
                        'rerun_after_completion_authorized': False,
                        'failure_recovery_requires_separate_review': True},
 'required_outputs': {'root': ('candidate_registry.csv',
                               'protected_measurement_summary.json',
                               'protected_measurement_metrics.csv',
                               'monthly_results.csv',
                               'cost_sensitivity.csv',
                               'representation_sensitivity.csv',
                               'trade_distribution.csv',
                               'drawdown_episodes.csv',
                               'historical_context.csv',
                               'output_hashes.json',
                               'report.md',
                               'report.html',
                               'EXP027_COMPLETE.json'),
                      'assets': ('assets/equity_curves.png', 'assets/drawdown_curves.png'),
                      'per_series_patterns': ('series/<candidate_id>/trades.csv',
                                              'series/<candidate_id>/equity.csv',
                                              'series/<candidate_id>/comparison_timeseries.csv',
                                              'series/<candidate_id>/metrics.csv'),
                      'per_series_count': 24,
                      'files_per_series': 4,
                      'zero_trade_header_ledger_required': True,
                      'zero_trade_flat_equity_required': True},
 'interpretation': {'measurement_first': True,
                    'protected_temporal_measurement': True,
                    'primary_cohort_predeclared': True,
                    'secondary_candidates_are_context_only': True,
                    'no_single_best_strategy_claim': True,
                    'no_automatic_edge_validation': True,
                    'no_automatic_strategy_failure': True,
                    'no_strategy_accepted_for_trading': True,
                    'paper_trading_authorized': False,
                    'live_trading_authorized': False},
 'protected_actions': {'only_exp027_runner_authorized': True,
                       'new_databento_download_authorized': False,
                       'network_access_authorized': False,
                       'databento_api_calls_authorized': 0,
                       'paper_trading_authorized': False,
                       'live_trading_authorized': False,
                       'order_access_authorized': False,
                       'capital_deployment_authorized': False}}

EXPECTED_EXP027_EXECUTION_AUTHORIZATION_SHA256 = (
    "d0745af1570530772ec8b647aedb81c4c0a88f4358c087b9dd72765d694ff383"
)

EXPECTED_STRATEGY_CANDIDATE_IDS = ('gap_fade_0p25_prior_close', 'gap_fade_0p25_1r', 'gap_fade_0p50_prior_close', 'gap_fade_0p50_1r', 'gap_fade_0p75_prior_close', 'gap_fade_0p75_1r', 'premarket_continuation_0p50_time', 'premarket_continuation_0p50_1p5r', 'premarket_continuation_0p625_time', 'premarket_continuation_0p625_1p5r', 'premarket_continuation_0p75_time', 'premarket_continuation_0p75_1p5r', 'premarket_continuation_0p875_time', 'premarket_continuation_0p875_1p5r', 'opening_drive_0p25_time', 'opening_drive_0p25_1p5r', 'opening_drive_0p50_time', 'opening_drive_0p50_1p5r', 'opening_drive_0p75_time', 'opening_drive_0p75_1p5r', 'opening_drive_1p00_time', 'opening_drive_1p00_1p5r')

EXPECTED_CONTROL_CANDIDATE_IDS = ('orb_control_exp005_15m_both_time', 'orb_control_exp007_30m_long_1r')

EXPECTED_PRIMARY_COHORT_IDS = ('gap_fade_0p75_1r', 'opening_drive_0p75_time', 'premarket_continuation_0p875_1p5r')

EXPECTED_ROOT_OUTPUTS = ('candidate_registry.csv', 'protected_measurement_summary.json', 'protected_measurement_metrics.csv', 'monthly_results.csv', 'cost_sensitivity.csv', 'representation_sensitivity.csv', 'trade_distribution.csv', 'drawdown_episodes.csv', 'historical_context.csv', 'output_hashes.json', 'report.md', 'report.html', 'EXP027_COMPLETE.json')

EXPECTED_ASSET_OUTPUTS = ('assets/equity_curves.png', 'assets/drawdown_curves.png')

EXPECTED_PER_SERIES_PATTERNS = ('series/<candidate_id>/trades.csv', 'series/<candidate_id>/equity.csv', 'series/<candidate_id>/comparison_timeseries.csv', 'series/<candidate_id>/metrics.csv')


def canonical_record_hash(
    record: dict[str, Any],
) -> str:
    encoded = json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def get_exp027_execution_authorization() -> dict[str, Any]:
    return deepcopy(EXP027_EXECUTION_AUTHORIZATION)


def validate_exp027_execution_authorization(
    candidate: dict[str, Any] | None = None,
) -> None:
    record = (
        EXP027_EXECUTION_AUTHORIZATION
        if candidate is None
        else candidate
    )

    if (
        record.get("experiment_id") != "EXP-027"
        or record.get("authorization_status") != "AUTHORIZED"
        or record.get("execution_authorized") is not True
        or record.get("one_time_run") is not True
        or record.get("maximum_runs") != 1
    ):
        raise ValueError(
            "EXP-027 authorization identity changed."
        )

    if (
        record.get("preregistration_commit")
        != "21c182e119cde651e6c4fe22b1e4e8d6b99def5b"
        or record.get("preregistration_sha256")
        != "3177e5bb81bbf330b8a020c3bfee56b584cd284da3546fcdad4b90df5ffd76bd"
        or record.get("locked_implementation_commit")
        != "591cdf43b4c23abc312ae3d50b7d7948f88c90b2"
        or record.get("locked_exp026_engine_commit")
        != "13ee0683dfcbbb5d763f7254f3b245ecc8e6d9cd"
        or record.get("exp026_closure_commit")
        != "7fc1994e396bfb237fd5f05f5a4298e6c5b5e307"
        or record.get("exp026_closure_sha256")
        != "8ec79810a26b58f2d445d47d3f496539f121d6f3e139eae4a9fd38ef029a386f"
    ):
        raise ValueError(
            "EXP-027 frozen ancestry changed."
        )

    scope = record["candidate_scope"]
    if (
        tuple(scope["strategy_candidate_ids"])
        != EXPECTED_STRATEGY_CANDIDATE_IDS
        or tuple(scope["control_candidate_ids"])
        != EXPECTED_CONTROL_CANDIDATE_IDS
        or tuple(scope["reported_ids"])
        != (
            EXPECTED_STRATEGY_CANDIDATE_IDS
            + EXPECTED_CONTROL_CANDIDATE_IDS
        )
        or tuple(scope["primary_confirmation_cohort"])
        != EXPECTED_PRIMARY_COHORT_IDS
        or scope["strategy_candidate_count"] != 22
        or scope["control_candidate_count"] != 2
        or scope["reported_count"] != 24
        or scope["primary_count"] != 3
        or scope["candidate_selection"] is not False
        or scope["candidate_reselection"] is not False
        or scope["secondary_candidate_promotion"] is not False
        or scope["parameter_changes"] is not False
        or scope["single_winner_selection"] is not False
    ):
        raise ValueError(
            "EXP-027 candidate scope changed."
        )

    measurement = record["protected_measurement_scope"]
    if (
        measurement["mode"]
        != "PROTECTED_2026_MEASUREMENT"
        or measurement["session_start"] != "2026-01-01"
        or measurement["session_end"] != "2026-07-23"
        or measurement["primary_representation"]
        != "BACKWARD_ADJUSTED"
        or measurement["sensitivity_representation"]
        != "UNADJUSTED"
        or measurement["unadjusted_is_sensitivity_only"]
        is not True
        or measurement[
            "unadjusted_can_change_primary_cohort"
        ]
        is not False
        or tuple(
            measurement[
                "cost_sensitivity_ticks_per_side"
            ]
        )
        != (0, 1, 2, 3)
        or measurement["base_round_trip_cost_usd"] != 15.0
        or measurement["same_minute_stop_target_rule"]
        != "STOP_FIRST_CONSERVATIVE"
    ):
        raise ValueError(
            "EXP-027 protected measurement scope changed."
        )

    boundary = record["data_access_boundary"]
    if (
        boundary["parquet_filter_pushdown_required"]
        is not True
        or boundary[
            "filter_applied_before_table_materialization"
        ]
        is not True
        or boundary["minimum_materialized_trading_date"]
        != "2026-01-01"
        or boundary["maximum_materialized_trading_date"]
        != "2026-07-23"
        or boundary[
            "historical_2010_2025_market_access_authorized"
        ]
        is not False
        or boundary["protected_2026_access_authorized"]
        is not True
        or boundary["new_databento_download_authorized"]
        is not False
        or boundary["databento_api_calls_authorized"] != 0
        or boundary["network_access_authorized"] is not False
        or boundary["order_api_access_authorized"] is not False
    ):
        raise ValueError(
            "EXP-027 data-access boundary changed."
        )

    representations = record["representation_scope"]
    expected_representations = {
        "BACKWARD_ADJUSTED": {
            "role": "PRIMARY_PROTECTED_MEASUREMENT_SERIES",
            "path": (
                "results/EXP-022/selected_continuous_series/"
                "selected_roll_backward_adjusted.parquet"
            ),
            "size_bytes": 71_964_074,
            "sha256": (
                "61ccb3621b53fa313147a866948ec1f2c7a6b36956d2ba26090162b518c30c84"
            ),
            "semantic_sha256": (
                "3c6fa83821183ca54bc547c555834ceb16a126be50f90d8c6db5684220929951"
            ),
        },
        "UNADJUSTED": {
            "role": "REPRESENTATION_SENSITIVITY_ONLY",
            "path": (
                "results/EXP-022/selected_continuous_series/"
                "selected_roll_unadjusted.parquet"
            ),
            "size_bytes": 73_760_121,
            "sha256": (
                "606a69bbba4f4a5db3e0356d7b2849f9481e4555dc24cae4c6b9d1d12f673ab1"
            ),
            "semantic_sha256": (
                "29daf3f20b022fb69967349095eb9663bd04276cbc5743a65b1ecabc33113640"
            ),
        },
    }
    if (
        representations["representations"]
        != expected_representations
        or representations["both_representations_read_only"]
        is not True
        or representations["roll_rule_change_authorized"]
        is not False
        or representations[
            "adjustment_method_change_authorized"
        ]
        is not False
        or representations[
            "source_series_modification_authorized"
        ]
        is not False
    ):
        raise ValueError(
            "EXP-027 representation scope changed."
        )

    execution = record["execution_boundary"]
    if (
        execution["repository_must_be_clean"] is not True
        or execution["branch_must_be_main"] is not True
        or execution["local_and_origin_must_align"] is not True
        or execution["authorization_commit_must_equal_head"]
        is not True
        or execution["output_directory_must_not_exist"]
        is not True
        or execution["partial_output_directory_must_not_exist"]
        is not True
        or execution["independent_rebuild_required"]
        is not True
        or execution["serial_parallel_parity_required"]
        is not True
        or execution["rerun_after_completion_authorized"]
        is not False
    ):
        raise ValueError(
            "EXP-027 execution boundary changed."
        )

    outputs = record["required_outputs"]
    if (
        tuple(outputs["root"]) != EXPECTED_ROOT_OUTPUTS
        or tuple(outputs["assets"])
        != EXPECTED_ASSET_OUTPUTS
        or tuple(outputs["per_series_patterns"])
        != EXPECTED_PER_SERIES_PATTERNS
        or outputs["per_series_count"] != 24
        or outputs["files_per_series"] != 4
        or outputs["zero_trade_header_ledger_required"]
        is not True
        or outputs["zero_trade_flat_equity_required"]
        is not True
    ):
        raise ValueError(
            "EXP-027 output contract changed."
        )

    if (
        record.get("protected_2026_access_authorized")
        is not True
        or record.get("new_databento_download_authorized")
        is not False
        or record.get("network_access_authorized")
        is not False
        or record.get("paper_trading_authorized")
        is not False
        or record.get("live_trading_authorized")
        is not False
    ):
        raise ValueError(
            "EXP-027 authorization boundary changed."
        )

    protected = record["protected_actions"]
    if (
        protected["only_exp027_runner_authorized"]
        is not True
        or protected["new_databento_download_authorized"]
        is not False
        or protected["network_access_authorized"]
        is not False
        or protected["databento_api_calls_authorized"] != 0
        or protected["paper_trading_authorized"]
        is not False
        or protected["live_trading_authorized"]
        is not False
        or protected["order_access_authorized"] is not False
        or protected["capital_deployment_authorized"]
        is not False
    ):
        raise ValueError(
            "EXP-027 protected actions changed."
        )

    if (
        canonical_record_hash(record)
        != EXPECTED_EXP027_EXECUTION_AUTHORIZATION_SHA256
    ):
        raise ValueError(
            "EXP-027 authorization record changed."
        )
