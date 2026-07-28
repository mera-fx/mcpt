from __future__ import annotations

from copy import deepcopy
import hashlib
from importlib.metadata import PackageNotFoundError, version
import json
from typing import Any


EXP026_PHASE_C_AUTHORIZATION: dict[str, Any] = {'schema_version': 1,
 'experiment_id': 'EXP-026',
 'phase': 'C',
 'title': 'EXP-026 Phase C Known Comparison Execution Authorisation',
 'authorized_date': '2026-07-28',
 'authorization_status': 'AUTHORIZED',
 'execution_authorized': True,
 'one_time_run': True,
 'maximum_runs': 1,
 'preregistration_commit': 'ce661c7785fa6d8d409378ee2ad63a00f0e0a9b9',
 'preregistration_sha256': 'bbd2e6d8bb50c135d0c6ca04873eed2876c4e7db6a2714b91a934dcf554331a0',
 'locked_implementation_commit': '13ee0683dfcbbb5d763f7254f3b245ecc8e6d9cd',
 'phase_b_completion_commit': 'da8456d254dc710336806ad5940afcec649be016',
 'phase_b_completion_sha256': 'bbc5e38f4f08ef87d423f1d7890fd2dc87c5afd2068287f4272c7f46bcb1b3de',
 'finalist_candidate_ids': ('gap_fade_0p75_1r',
                            'opening_drive_0p75_time',
                            'premarket_continuation_0p875_1p5r'),
 'control_candidate_ids': ('orb_control_exp005_15m_both_time',
                           'orb_control_exp007_30m_long_1r'),
 'protected_2026_access_authorized': False,
 'new_databento_download_authorized': False,
 'network_access_authorized': False,
 'paper_trading_authorized': False,
 'live_trading_authorized': False,
 'runtime_environment': {'python_version': '3.14.6',
                         'pandas_version': '3.0.3',
                         'tabulate_version': '0.10.0',
                         'tabulate_version_required': '0.10.0',
                         'markdown_report_smoke_test_passed': True},
 'phase_scope': {'mode': 'KNOWN_COMPARISON',
                 'materialized_source_start': '2019-12-01',
                 'materialized_source_end': '2025-12-31',
                 'known_comparison_start': '2020-01-03',
                 'known_comparison_end': '2025-12-31',
                 'finalist_count': 3,
                 'finalist_candidate_ids': ('gap_fade_0p75_1r',
                                            'opening_drive_0p75_time',
                                            'premarket_continuation_0p875_1p5r'),
                 'control_candidate_count': 2,
                 'control_candidate_ids': ('orb_control_exp005_15m_both_time',
                                           'orb_control_exp007_30m_long_1r'),
                 'candidate_count': 5,
                 'primary_representation': 'BACKWARD_ADJUSTED',
                 'sensitivity_representation': 'UNADJUSTED',
                 'candidate_reselection': False,
                 'parameter_changes': False,
                 'position_sizing_changes': False,
                 'portfolio_weight_changes': False,
                 'finalist_identity_can_change': False,
                 'known_period_is_independent_confirmation': False,
                 'unadjusted_can_change_finalist_identity': False,
                 'cost_sensitivity_ticks_per_side': (0, 1, 2, 3)},
 'representation_scope': {'representations': {'BACKWARD_ADJUSTED': {'role': 'PRIMARY_RESEARCH_SERIES',
                                                                    'path': 'results/EXP-022/selected_continuous_series/selected_roll_backward_adjusted.parquet',
                                                                    'size_bytes': 71964074,
                                                                    'sha256': '61ccb3621b53fa313147a866948ec1f2c7a6b36956d2ba26090162b518c30c84',
                                                                    'semantic_sha256': '3c6fa83821183ca54bc547c555834ceb16a126be50f90d8c6db5684220929951'},
                                              'UNADJUSTED': {'role': 'POST_SELECTION_REPRESENTATION_SENSITIVITY_ONLY',
                                                             'path': 'results/EXP-022/selected_continuous_series/selected_roll_unadjusted.parquet',
                                                             'size_bytes': 73760121,
                                                             'sha256': '606a69bbba4f4a5db3e0356d7b2849f9481e4555dc24cae4c6b9d1d12f673ab1',
                                                             'semantic_sha256': '29daf3f20b022fb69967349095eb9663bd04276cbc5743a65b1ecabc33113640'}},
                          'both_representations_read_only': True,
                          'backward_adjusted_is_primary': True,
                          'unadjusted_is_post_selection_sensitivity_only': True,
                          'unadjusted_results_can_change_selection': False,
                          'roll_rule_change_authorized': False,
                          'adjustment_method_change_authorized': False},
 'required_outputs': ('known_comparison_summary.json',
                      'known_comparison_metrics.csv',
                      'annual_results.csv',
                      'monthly_results.csv',
                      'cost_sensitivity.csv',
                      'representation_sensitivity.csv',
                      'trade_distribution.csv',
                      'drawdown_episodes.csv',
                      'output_hashes.json',
                      'report.md',
                      'report.html',
                      'PHASE_C_COMPLETE.json'),
 'data_access_boundary': {'parquet_filter_pushdown_required': True,
                          'known_2020_2025_access_authorized': True,
                          'phase_c_access_authorized': True,
                          'backward_adjusted_access_authorized': True,
                          'unadjusted_access_authorized': True,
                          'maximum_materialized_trading_date': '2025-12-31',
                          'protected_2026_access_authorized': False,
                          'new_databento_download_authorized': False,
                          'databento_api_calls_authorized': 0,
                          'network_access_authorized': False,
                          'order_api_access_authorized': False,
                          'source_series_modification_authorized': False,
                          'missing_bar_fill_authorized': False,
                          'synthetic_bar_creation_authorized': False},
 'execution_boundary': {'repository_must_be_clean': True,
                        'branch_must_be_main': True,
                        'local_and_origin_must_align': True,
                        'phase_b_completion_must_precede_authorization': True,
                        'authorization_commit_must_equal_head': True,
                        'output_directory_must_not_exist': True,
                        'partial_output_directory_must_not_exist': True,
                        'independent_rebuild_required': True,
                        'required_output_hash_manifest': True,
                        'rerun_after_completion_authorized': False},
 'interpretation': {'known_comparison': True,
                    'measurement_first': True,
                    'known_period_is_not_independent_confirmation': True,
                    'finalists_are_not_confirmed_edges': True,
                    'finalist_identity_is_frozen': True,
                    'unadjusted_is_sensitivity_only': True,
                    'phase_c_results_do_not_authorize_exp027': True,
                    'no_strategy_is_accepted_for_trading': True,
                    'paper_trading_authorized': False,
                    'live_trading_authorized': False},
 'protected_actions': {'protected_2026_access_authorized': False,
                       'exp027_execution_authorized': False,
                       'new_databento_download_authorized': False,
                       'network_access_authorized': False,
                       'paper_trading_authorized': False,
                       'live_trading_authorized': False}}

EXPECTED_EXP026_PHASE_C_AUTHORIZATION_SHA256 = (
    "7b3e59989061ac9f907d8e6ff749fedc6b40a71a4e03ab1b5ff045096c63b4ce"
)

EXPECTED_FINALIST_CANDIDATE_IDS = ('gap_fade_0p75_1r', 'opening_drive_0p75_time', 'premarket_continuation_0p875_1p5r')

EXPECTED_CONTROL_CANDIDATE_IDS = ('orb_control_exp005_15m_both_time', 'orb_control_exp007_30m_long_1r')

EXPECTED_PHASE_C_OUTPUTS = ('known_comparison_summary.json', 'known_comparison_metrics.csv', 'annual_results.csv', 'monthly_results.csv', 'cost_sensitivity.csv', 'representation_sensitivity.csv', 'trade_distribution.csv', 'drawdown_episodes.csv', 'output_hashes.json', 'report.md', 'report.html', 'PHASE_C_COMPLETE.json')

EXPECTED_REPRESENTATIONS = {'BACKWARD_ADJUSTED': {'role': 'PRIMARY_RESEARCH_SERIES',
                       'path': 'results/EXP-022/selected_continuous_series/selected_roll_backward_adjusted.parquet',
                       'size_bytes': 71964074,
                       'sha256': '61ccb3621b53fa313147a866948ec1f2c7a6b36956d2ba26090162b518c30c84',
                       'semantic_sha256': '3c6fa83821183ca54bc547c555834ceb16a126be50f90d8c6db5684220929951'},
 'UNADJUSTED': {'role': 'POST_SELECTION_REPRESENTATION_SENSITIVITY_ONLY',
                'path': 'results/EXP-022/selected_continuous_series/selected_roll_unadjusted.parquet',
                'size_bytes': 73760121,
                'sha256': '606a69bbba4f4a5db3e0356d7b2849f9481e4555dc24cae4c6b9d1d12f673ab1',
                'semantic_sha256': '29daf3f20b022fb69967349095eb9663bd04276cbc5743a65b1ecabc33113640'}}


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


def get_exp026_phase_c_authorization() -> dict[str, Any]:
    return deepcopy(
        EXP026_PHASE_C_AUTHORIZATION
    )


def validate_exp026_phase_c_authorization(
    candidate: dict[str, Any] | None = None,
) -> None:
    record = (
        EXP026_PHASE_C_AUTHORIZATION
        if candidate is None
        else candidate
    )

    if (
        record.get("experiment_id")
        != "EXP-026"
        or record.get("phase") != "C"
        or record.get(
            "authorization_status"
        )
        != "AUTHORIZED"
        or record.get(
            "execution_authorized"
        )
        is not True
        or record.get("one_time_run")
        is not True
        or record.get("maximum_runs")
        != 1
    ):
        raise ValueError(
            "EXP-026 Phase C authorization identity changed."
        )

    if (
        record.get(
            "preregistration_commit"
        )
        != "ce661c7785fa6d8d409378ee2ad63a00f0e0a9b9"
        or record.get(
            "preregistration_sha256"
        )
        != "bbd2e6d8bb50c135d0c6ca04873eed2876c4e7db6a2714b91a934dcf554331a0"
        or record.get(
            "locked_implementation_commit"
        )
        != "13ee0683dfcbbb5d763f7254f3b245ecc8e6d9cd"
        or record.get(
            "phase_b_completion_commit"
        )
        != "da8456d254dc710336806ad5940afcec649be016"
        or record.get(
            "phase_b_completion_sha256"
        )
        != "bbc5e38f4f08ef87d423f1d7890fd2dc87c5afd2068287f4272c7f46bcb1b3de"
    ):
        raise ValueError(
            "EXP-026 Phase C frozen ancestry changed."
        )

    if (
        tuple(
            record.get(
                "finalist_candidate_ids",
                (),
            )
        )
        != EXPECTED_FINALIST_CANDIDATE_IDS
        or tuple(
            record.get(
                "control_candidate_ids",
                (),
            )
        )
        != EXPECTED_CONTROL_CANDIDATE_IDS
    ):
        raise ValueError(
            "EXP-026 Phase C candidate population changed."
        )

    if (
        record.get(
            "protected_2026_access_authorized"
        )
        is not False
        or record.get(
            "new_databento_download_authorized"
        )
        is not False
        or record.get(
            "network_access_authorized"
        )
        is not False
        or record.get(
            "paper_trading_authorized"
        )
        is not False
        or record.get(
            "live_trading_authorized"
        )
        is not False
    ):
        raise ValueError(
            "EXP-026 Phase C runner boundary changed."
        )

    scope = record["phase_scope"]

    if (
        scope["mode"]
        != "KNOWN_COMPARISON"
        or scope[
            "materialized_source_start"
        ]
        != "2019-12-01"
        or scope[
            "materialized_source_end"
        ]
        != "2025-12-31"
        or scope[
            "known_comparison_start"
        ]
        != "2020-01-03"
        or scope[
            "known_comparison_end"
        ]
        != "2025-12-31"
        or tuple(
            scope[
                "finalist_candidate_ids"
            ]
        )
        != EXPECTED_FINALIST_CANDIDATE_IDS
        or tuple(
            scope[
                "control_candidate_ids"
            ]
        )
        != EXPECTED_CONTROL_CANDIDATE_IDS
        or scope[
            "candidate_reselection"
        ]
        is not False
        or scope[
            "parameter_changes"
        ]
        is not False
        or scope[
            "finalist_identity_can_change"
        ]
        is not False
        or scope[
            "known_period_is_independent_confirmation"
        ]
        is not False
        or scope[
            "unadjusted_can_change_finalist_identity"
        ]
        is not False
    ):
        raise ValueError(
            "EXP-026 Phase C scope changed."
        )

    representations = record[
        "representation_scope"
    ]

    if (
        representations[
            "representations"
        ]
        != EXPECTED_REPRESENTATIONS
        or representations[
            "both_representations_read_only"
        ]
        is not True
        or representations[
            "backward_adjusted_is_primary"
        ]
        is not True
        or representations[
            "unadjusted_is_post_selection_sensitivity_only"
        ]
        is not True
        or representations[
            "unadjusted_results_can_change_selection"
        ]
        is not False
    ):
        raise ValueError(
            "EXP-026 Phase C representation boundary changed."
        )

    boundary = record[
        "data_access_boundary"
    ]

    if (
        boundary[
            "parquet_filter_pushdown_required"
        ]
        is not True
        or boundary[
            "known_2020_2025_access_authorized"
        ]
        is not True
        or boundary[
            "phase_c_access_authorized"
        ]
        is not True
        or boundary[
            "maximum_materialized_trading_date"
        ]
        != "2025-12-31"
        or boundary[
            "protected_2026_access_authorized"
        ]
        is not False
        or boundary[
            "new_databento_download_authorized"
        ]
        is not False
        or boundary[
            "databento_api_calls_authorized"
        ]
        != 0
        or boundary[
            "network_access_authorized"
        ]
        is not False
        or boundary[
            "order_api_access_authorized"
        ]
        is not False
    ):
        raise ValueError(
            "EXP-026 Phase C data boundary changed."
        )

    if tuple(
        record["required_outputs"]
    ) != EXPECTED_PHASE_C_OUTPUTS:
        raise ValueError(
            "EXP-026 Phase C outputs changed."
        )

    runtime = record[
        "runtime_environment"
    ]

    try:
        installed_tabulate = version(
            "tabulate"
        )
    except PackageNotFoundError as error:
        raise ValueError(
            "EXP-026 Phase C tabulate dependency is absent."
        ) from error

    if (
        runtime[
            "tabulate_version_required"
        ]
        != "0.10.0"
        or runtime[
            "tabulate_version"
        ]
        != "0.10.0"
        or installed_tabulate
        != "0.10.0"
        or runtime[
            "markdown_report_smoke_test_passed"
        ]
        is not True
    ):
        raise ValueError(
            "EXP-026 Phase C runtime dependency changed."
        )

    if (
        canonical_record_hash(record)
        != EXPECTED_EXP026_PHASE_C_AUTHORIZATION_SHA256
    ):
        raise ValueError(
            "EXP-026 Phase C authorization record changed."
        )
