from __future__ import annotations

from copy import deepcopy
import hashlib
from importlib.metadata import PackageNotFoundError, version
import json
from typing import Any

import pandas as pd


EXP026_PHASE_B_AUTHORIZATION: dict[str, Any] = {'schema_version': 1,
 'experiment_id': 'EXP-026',
 'phase': 'B',
 'title': 'EXP-026 Phase B Internal Validation Execution Authorisation',
 'authorized_date': '2026-07-28',
 'authorization_status': 'AUTHORIZED',
 'execution_authorized': True,
 'one_time_run': True,
 'maximum_runs': 1,
 'preregistration_commit': 'ce661c7785fa6d8d409378ee2ad63a00f0e0a9b9',
 'preregistration_sha256': 'bbd2e6d8bb50c135d0c6ca04873eed2876c4e7db6a2714b91a934dcf554331a0',
 'locked_implementation_commit': '13ee0683dfcbbb5d763f7254f3b245ecc8e6d9cd',
 'phase_a_completion_commit': '28bd4209711f0c9b98a7650ab91f6408c2bdf4b7',
 'phase_a_completion_sha256': '79899140135d5d4aba92c0f7aa7056dce6a0540f9e48d2e70383e7c4cc5ecf40',
 'phase_a_survivor_ids': ('gap_fade_0p75_1r',
                          'gap_fade_0p25_1r',
                          'opening_drive_0p75_1p5r',
                          'opening_drive_0p75_time',
                          'premarket_continuation_0p875_1p5r',
                          'premarket_continuation_0p625_1p5r'),
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
 'phase_scope': {'mode': 'INTERNAL_VALIDATION',
                 'primary_representation': 'BACKWARD_ADJUSTED',
                 'materialized_source_start': '2010-06-07',
                 'materialized_source_end': '2019-12-31',
                 'development_reference_start': '2010-06-07',
                 'development_reference_end': '2017-12-31',
                 'internal_validation_start': '2018-01-01',
                 'internal_validation_end': '2019-12-31',
                 'phase_a_survivor_count': 6,
                 'phase_a_survivor_ids': ('gap_fade_0p75_1r',
                                          'gap_fade_0p25_1r',
                                          'opening_drive_0p75_1p5r',
                                          'opening_drive_0p75_time',
                                          'premarket_continuation_0p875_1p5r',
                                          'premarket_continuation_0p625_1p5r'),
                 'control_candidate_count': 2,
                 'controls_are_not_selectable': True,
                 'maximum_finalists_per_family': 1,
                 'finalist_count_minimum': 0,
                 'finalist_count_maximum': 3,
                 'selection_rank': ('profitable_internal_validation_years descending',
                                    'internal_validation_trade_profit_factor '
                                    'descending',
                                    'internal_validation_net_profit_to_drawdown '
                                    'descending',
                                    'internal_validation_net_profit_usd descending',
                                    'development_trade_profit_factor descending',
                                    'candidate_id ascending'),
                 'zero_validation_trade_candidates_not_selectable': True,
                 'no_minimum_profit_gate': True,
                 'candidate_reselection_outside_frozen_rule_authorized': False,
                 'candidate_additions_authorized': False,
                 'candidate_removals_authorized': False,
                 'parameter_changes_authorized': False,
                 'position_sizing_changes_authorized': False,
                 'unadjusted_representation_authorized': False},
 'robustness_scope': {'selection_aware_mcpt_permutations': 1000,
                      'selection_aware_mcpt_seed': 26026,
                      'bootstrap_resamples': 10000,
                      'bootstrap_seed': 26027,
                      'bootstrap_confidence_level': 0.95,
                      'anchored_walk_forward_test_years': (2014,
                                                           2015,
                                                           2016,
                                                           2017,
                                                           2018,
                                                           2019),
                      'parameter_neighbour_stability': True,
                      'decision_gates': False},
 'required_outputs': ('internal_validation_summary.json',
                      'internal_validation_metrics.csv',
                      'selected_finalists.json',
                      'walk_forward_results.csv',
                      'bootstrap_summary.csv',
                      'mcpt_summary.json',
                      'parameter_stability.csv',
                      'output_hashes.json',
                      'report.md',
                      'report.html',
                      'PHASE_B_COMPLETE.json'),
 'data_access_boundary': {'parquet_filter_pushdown_required': True,
                          'phase_a_and_b_source_access_authorized': True,
                          'known_2020_2025_access_authorized': False,
                          'phase_c_access_authorized': False,
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
                        'phase_a_completion_must_precede_authorization': True,
                        'authorization_commit_must_equal_head': True,
                        'output_directory_must_not_exist': True,
                        'partial_output_directory_must_not_exist': True,
                        'independent_rebuild_required': True,
                        'required_output_hash_manifest': True,
                        'phase_b_completion_commit_required_before_phase_c': True,
                        'rerun_after_completion_authorized': False},
 'interpretation': {'internal_validation': True,
                    'measurement_first': True,
                    'robustness_results_are_context_not_gates': True,
                    'finalists_are_not_confirmed_edges': True,
                    'known_2020_2025_cannot_change_selection': True,
                    'phase_b_results_do_not_authorize_phase_c': True,
                    'phase_b_results_do_not_authorize_exp027': True,
                    'paper_trading_authorized': False,
                    'live_trading_authorized': False},
 'protected_actions': {'phase_c_execution_authorized': False,
                       'known_2020_2025_access_authorized': False,
                       'protected_2026_access_authorized': False,
                       'new_databento_download_authorized': False,
                       'network_access_authorized': False,
                       'paper_trading_authorized': False,
                       'live_trading_authorized': False}}

EXPECTED_EXP026_PHASE_B_AUTHORIZATION_SHA256 = (
    "3522b27be25a3f3dced19492d1043dda69b3a134e480453f0b868e9ae310eee5"
)

EXPECTED_PHASE_A_SURVIVORS = ('gap_fade_0p75_1r', 'gap_fade_0p25_1r', 'opening_drive_0p75_1p5r', 'opening_drive_0p75_time', 'premarket_continuation_0p875_1p5r', 'premarket_continuation_0p625_1p5r')

EXPECTED_PHASE_B_OUTPUTS = ('internal_validation_summary.json', 'internal_validation_metrics.csv', 'selected_finalists.json', 'walk_forward_results.csv', 'bootstrap_summary.csv', 'mcpt_summary.json', 'parameter_stability.csv', 'output_hashes.json', 'report.md', 'report.html', 'PHASE_B_COMPLETE.json')

EXPECTED_PHASE_B_SELECTION_RANK = ('profitable_internal_validation_years descending', 'internal_validation_trade_profit_factor descending', 'internal_validation_net_profit_to_drawdown descending', 'internal_validation_net_profit_usd descending', 'development_trade_profit_factor descending', 'candidate_id ascending')


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


def get_exp026_phase_b_authorization() -> dict[str, Any]:
    return deepcopy(
        EXP026_PHASE_B_AUTHORIZATION
    )


def validate_exp026_phase_b_authorization(
    candidate: dict[str, Any] | None = None,
) -> None:
    record = (
        EXP026_PHASE_B_AUTHORIZATION
        if candidate is None
        else candidate
    )

    if (
        record.get("experiment_id") != "EXP-026"
        or record.get("phase") != "B"
        or record.get("authorization_status")
        != "AUTHORIZED"
        or record.get("execution_authorized")
        is not True
        or record.get("one_time_run")
        is not True
        or record.get("maximum_runs") != 1
    ):
        raise ValueError(
            "EXP-026 Phase B authorization identity changed."
        )

    if (
        record.get("preregistration_commit")
        != "ce661c7785fa6d8d409378ee2ad63a00f0e0a9b9"
        or record.get("preregistration_sha256")
        != "bbd2e6d8bb50c135d0c6ca04873eed2876c4e7db6a2714b91a934dcf554331a0"
        or record.get("locked_implementation_commit")
        != "13ee0683dfcbbb5d763f7254f3b245ecc8e6d9cd"
        or record.get("phase_a_completion_commit")
        != "28bd4209711f0c9b98a7650ab91f6408c2bdf4b7"
        or record.get("phase_a_completion_sha256")
        != "79899140135d5d4aba92c0f7aa7056dce6a0540f9e48d2e70383e7c4cc5ecf40"
    ):
        raise ValueError(
            "EXP-026 Phase B frozen ancestry changed."
        )

    if tuple(
        record.get(
            "phase_a_survivor_ids",
            (),
        )
    ) != EXPECTED_PHASE_A_SURVIVORS:
        raise ValueError(
            "EXP-026 Phase B survivor population changed."
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
            "EXP-026 Phase B runner boundary changed."
        )

    scope = record["phase_scope"]

    if (
        scope["mode"] != "INTERNAL_VALIDATION"
        or scope["primary_representation"]
        != "BACKWARD_ADJUSTED"
        or scope["materialized_source_start"]
        != "2010-06-07"
        or scope["materialized_source_end"]
        != "2019-12-31"
        or scope["internal_validation_start"]
        != "2018-01-01"
        or scope["internal_validation_end"]
        != "2019-12-31"
        or tuple(
            scope["phase_a_survivor_ids"]
        )
        != EXPECTED_PHASE_A_SURVIVORS
        or scope["maximum_finalists_per_family"]
        != 1
        or scope["finalist_count_minimum"] != 0
        or scope["finalist_count_maximum"] != 3
        or tuple(scope["selection_rank"])
        != EXPECTED_PHASE_B_SELECTION_RANK
        or scope["unadjusted_representation_authorized"]
        is not False
    ):
        raise ValueError(
            "EXP-026 Phase B scope changed."
        )

    boundary = record["data_access_boundary"]

    if (
        boundary[
            "parquet_filter_pushdown_required"
        ]
        is not True
        or boundary[
            "known_2020_2025_access_authorized"
        ]
        is not False
        or boundary[
            "phase_c_access_authorized"
        ]
        is not False
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
            "EXP-026 Phase B data boundary changed."
        )

    if tuple(
        record["required_outputs"]
    ) != EXPECTED_PHASE_B_OUTPUTS:
        raise ValueError(
            "EXP-026 Phase B outputs changed."
        )

    runtime = record["runtime_environment"]
    try:
        installed_tabulate = version("tabulate")
    except PackageNotFoundError as error:
        raise ValueError(
            "EXP-026 Phase B tabulate dependency is absent."
        ) from error

    if (
        runtime["tabulate_version_required"]
        != "0.10.0"
        or runtime["tabulate_version"]
        != "0.10.0"
        or installed_tabulate != "0.10.0"
        or runtime[
            "markdown_report_smoke_test_passed"
        ]
        is not True
    ):
        raise ValueError(
            "EXP-026 Phase B runtime dependency changed."
        )

    if (
        canonical_record_hash(record)
        != EXPECTED_EXP026_PHASE_B_AUTHORIZATION_SHA256
    ):
        raise ValueError(
            "EXP-026 Phase B authorization record changed."
        )
