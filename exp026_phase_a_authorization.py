from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any


EXP026_PHASE_A_AUTHORIZATION: dict[str, Any] = {'schema_version': 1,
 'experiment_id': 'EXP-026',
 'phase': 'A',
 'title': 'EXP-026 Phase A Development Execution Authorisation',
 'authorized_date': '2026-07-28',
 'authorization_status': 'AUTHORIZED',
 'execution_authorized': True,
 'one_time_run': True,
 'maximum_runs': 1,
 'preregistration_commit': 'ce661c7785fa6d8d409378ee2ad63a00f0e0a9b9',
 'preregistration_sha256': 'bbd2e6d8bb50c135d0c6ca04873eed2876c4e7db6a2714b91a934dcf554331a0',
 'locked_implementation_commit': '13ee0683dfcbbb5d763f7254f3b245ecc8e6d9cd',
 'protected_2026_access_authorized': False,
 'new_databento_download_authorized': False,
 'network_access_authorized': False,
 'paper_trading_authorized': False,
 'live_trading_authorized': False,
 'implementation_files': {'exp026_core.py': {'size_bytes': 75268,
                                             'sha256': 'bede84fc5835da73390afed99d12238da3e23e063b736ac6e4a8c34544b29b28'},
                          'exp026_statistics.py': {'size_bytes': 25581,
                                                   'sha256': 'a34817447673c5a4a3297492c064876717ab671f7c8e1fb82191293098c29f8b'},
                          'exp026_runner.py': {'size_bytes': 66018,
                                               'sha256': '9546e5a45f2f40b920dac8b707c21eaac03bd8caf553cbaadbd5a1eb7adbebc6'},
                          'exp026_implementation_preflight.py': {'size_bytes': 7782,
                                                                 'sha256': '4f42c6340d77b2d8885d39dcece9b79af3fe8cdb62cac05ac9d12cbd6052adaa'},
                          'research/EXP-026_implementation_report.md': {'size_bytes': 5199,
                                                                        'sha256': '99a043dcdbe784c4888d95849723804c44b1a580fab00c1947f3fe5c09a04944'},
                          'tests/test_exp026_core.py': {'size_bytes': 20873,
                                                        'sha256': 'b5559e8723ce0c82be38ff6fb22f68642d79e467c0a8329db6639312c22d51b2'},
                          'tests/test_exp026_implementation.py': {'size_bytes': 10813,
                                                                  'sha256': '6257e1b0b7f5720a9284dbeec9c3e2be2600182381cb45594efbad939b415fe7'}},
 'phase_scope': {'mode': 'DEVELOPMENT',
                 'allowed_session_start': '2010-06-07',
                 'allowed_session_end': '2017-12-31',
                 'primary_representation': 'BACKWARD_ADJUSTED',
                 'unadjusted_representation_authorized': False,
                 'development_candidate_count': 22,
                 'control_candidate_count': 2,
                 'reported_candidate_count': 24,
                 'development_candidate_ids': ('gap_fade_0p25_prior_close',
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
                 'maximum_survivors_per_family': 2,
                 'candidate_reselection_rule': 'Use only the frozen Phase A '
                                               'lexicographic ranking.',
                 'candidate_additions_authorized': False,
                 'candidate_removals_authorized': False,
                 'parameter_changes_authorized': False,
                 'position_sizing_changes_authorized': False},
 'required_outputs': ('development_summary.json',
                      'candidate_registry.csv',
                      'development_metrics.csv',
                      'development_annual_results.csv',
                      'phase_a_survivors.json',
                      'output_hashes.json',
                      'report.md',
                      'PHASE_A_COMPLETE.json'),
 'data_access_boundary': {'parquet_filter_pushdown_required': True,
                          'market_values_before_2010_06_07_authorized': False,
                          'phase_b_2018_2019_access_authorized': False,
                          'phase_c_2020_2025_access_authorized': False,
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
                        'authorization_commit_must_equal_head': True,
                        'output_directory_must_not_exist': True,
                        'partial_output_directory_must_not_exist': True,
                        'independent_rebuild_required': True,
                        'required_output_hash_manifest': True,
                        'phase_a_completion_commit_required_before_phase_b': True,
                        'rerun_after_completion_authorized': False},
 'interpretation': {'exploratory_development': True,
                    'measurement_first': True,
                    'survivors_are_not_validated_edges': True,
                    'phase_a_results_do_not_authorize_phase_b': True,
                    'phase_a_results_do_not_authorize_phase_c': True,
                    'phase_a_results_do_not_authorize_exp027': True,
                    'paper_trading_authorized': False,
                    'live_trading_authorized': False},
 'protected_actions': {'phase_b_execution_authorized': False,
                       'phase_c_execution_authorized': False,
                       'protected_2026_access_authorized': False,
                       'new_databento_download_authorized': False,
                       'network_access_authorized': False,
                       'paper_trading_authorized': False,
                       'live_trading_authorized': False}}

EXPECTED_EXP026_PHASE_A_AUTHORIZATION_SHA256 = (
    "527fdbba75095d9b987e0e64dd6410e6fa79d1bff5916049c933e4f6aa8a9dcc"
)


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


def get_exp026_phase_a_authorization() -> dict[str, Any]:
    return deepcopy(
        EXP026_PHASE_A_AUTHORIZATION
    )


def validate_exp026_phase_a_authorization(
    candidate: dict[str, Any] | None = None,
) -> None:
    record = (
        EXP026_PHASE_A_AUTHORIZATION
        if candidate is None
        else candidate
    )

    if (
        record.get("experiment_id") != "EXP-026"
        or record.get("phase") != "A"
        or record.get("authorized_date")
        != "2026-07-28"
        or record.get("authorization_status")
        != "AUTHORIZED"
        or record.get("execution_authorized")
        is not True
        or record.get("one_time_run")
        is not True
        or record.get("maximum_runs") != 1
    ):
        raise ValueError(
            "EXP-026 Phase A authorization identity changed."
        )

    if (
        record.get("preregistration_commit")
        != "ce661c7785fa6d8d409378ee2ad63a00f0e0a9b9"
        or record.get("preregistration_sha256")
        != "bbd2e6d8bb50c135d0c6ca04873eed2876c4e7db6a2714b91a934dcf554331a0"
        or record.get("locked_implementation_commit")
        != "13ee0683dfcbbb5d763f7254f3b245ecc8e6d9cd"
    ):
        raise ValueError(
            "EXP-026 Phase A frozen commit boundary changed."
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
            "EXP-026 Phase A runner boundary changed."
        )

    scope = record["phase_scope"]

    if (
        scope["mode"] != "DEVELOPMENT"
        or scope["allowed_session_start"]
        != "2010-06-07"
        or scope["allowed_session_end"]
        != "2017-12-31"
        or scope["primary_representation"]
        != "BACKWARD_ADJUSTED"
        or scope["unadjusted_representation_authorized"]
        is not False
        or scope["development_candidate_count"] != 22
        or scope["control_candidate_count"] != 2
        or scope["reported_candidate_count"] != 24
        or len(scope["development_candidate_ids"]) != 22
        or len(scope["control_candidate_ids"]) != 2
        or scope["maximum_survivors_per_family"] != 2
    ):
        raise ValueError(
            "EXP-026 Phase A scope changed."
        )

    boundary = record["data_access_boundary"]

    if (
        boundary[
            "parquet_filter_pushdown_required"
        ]
        is not True
        or boundary[
            "phase_b_2018_2019_access_authorized"
        ]
        is not False
        or boundary[
            "phase_c_2020_2025_access_authorized"
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
            "EXP-026 Phase A data-access boundary changed."
        )

    protected = record["protected_actions"]

    if (
        protected[
            "phase_b_execution_authorized"
        ]
        is not False
        or protected[
            "phase_c_execution_authorized"
        ]
        is not False
        or protected[
            "protected_2026_access_authorized"
        ]
        is not False
        or protected[
            "new_databento_download_authorized"
        ]
        is not False
        or protected[
            "network_access_authorized"
        ]
        is not False
        or protected[
            "paper_trading_authorized"
        ]
        is not False
        or protected[
            "live_trading_authorized"
        ]
        is not False
    ):
        raise ValueError(
            "EXP-026 Phase A protected actions changed."
        )

    if (
        tuple(record["required_outputs"])
        != ('development_summary.json', 'candidate_registry.csv', 'development_metrics.csv', 'development_annual_results.csv', 'phase_a_survivors.json', 'output_hashes.json', 'report.md', 'PHASE_A_COMPLETE.json')
    ):
        raise ValueError(
            "EXP-026 Phase A output requirement changed."
        )

    if (
        canonical_record_hash(record)
        != EXPECTED_EXP026_PHASE_A_AUTHORIZATION_SHA256
    ):
        raise ValueError(
            "EXP-026 Phase A authorization record changed."
        )
