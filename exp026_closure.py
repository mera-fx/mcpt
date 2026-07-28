from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any


EXP026_CLOSURE: dict[str, Any] = {'schema_version': 1,
 'experiment_id': 'EXP-026',
 'closed_date': '2026-07-28',
 'research_status': 'REVIEW',
 'classification': 'COMPLETED_MEASUREMENT_REVIEW',
 'repository': {'preregistration_commit': 'ce661c7785fa6d8d409378ee2ad63a00f0e0a9b9',
                'implementation_commit': '13ee0683dfcbbb5d763f7254f3b245ecc8e6d9cd',
                'phase_a_authorization_commit': '5fa417ed56c2d620c5d348e9ab43f3d7634518b8',
                'phase_a_recovery_commit': 'd54289659ffa058ae31558ad3b99b646c31d0bf7',
                'phase_a_completion_commit': '28bd4209711f0c9b98a7650ab91f6408c2bdf4b7',
                'phase_b_authorization_commit': '20ed5ba203f2e4bb3940de389afface6b749d7c7',
                'phase_b_completion_commit': 'da8456d254dc710336806ad5940afcec649be016',
                'phase_c_authorization_commit': '5e03bb449468b980e003c133ce076cf1b87b3ac7',
                'phase_c_completion_commit': 'a400a373b87b780c21dc2d15048b1e1a5ad1050a',
                'closure_base_head': 'a400a373b87b780c21dc2d15048b1e1a5ad1050a'},
 'locked_records': {'preregistration_sha256': 'bbd2e6d8bb50c135d0c6ca04873eed2876c4e7db6a2714b91a934dcf554331a0',
                    'phase_a_completion_sha256': '79899140135d5d4aba92c0f7aa7056dce6a0540f9e48d2e70383e7c4cc5ecf40',
                    'phase_b_completion_sha256': 'bbc5e38f4f08ef87d423f1d7890fd2dc87c5afd2068287f4272c7f46bcb1b3de',
                    'phase_c_completion_sha256': '743aa1638cd00c279e216e6ccfedb402d7d9ce1954daafc3538e6362f4cc247a',
                    'historical_data_policy_path': 'research/HISTORICAL_DATA_POLICY.md',
                    'historical_data_policy_sha256': '638cd9da878590bd0cb08302a7fcde81d0fa3380d0d2262af4491c9da63a19b9'},
 'phase_a_development': {'session_start': '2010-06-07',
                         'session_end': '2017-12-31',
                         'reported_candidate_count': 24,
                         'development_candidate_count': 22,
                         'control_candidate_count': 2,
                         'decision_rows': 46584,
                         'trade_rows': 11502,
                         'survivor_count': 6,
                         'survivor_candidate_ids': ('gap_fade_0p75_1r',
                                                    'gap_fade_0p25_1r',
                                                    'opening_drive_0p75_1p5r',
                                                    'opening_drive_0p75_time',
                                                    'premarket_continuation_0p875_1p5r',
                                                    'premarket_continuation_0p625_1p5r'),
                         'maximum_survivors_per_family': 2,
                         'independent_rebuild': True,
                         'presentation_recovery_used': True,
                         'recovery_id': 'EXP-026-A-R1',
                         'recovery_read_market_values': False,
                         'recovery_recalculated_strategy': False},
 'phase_b_internal_validation': {'session_start': '2018-01-01',
                                 'session_end': '2019-12-31',
                                 'survivor_count': 6,
                                 'finalist_count': 3,
                                 'finalist_candidate_ids': ('gap_fade_0p75_1r',
                                                            'opening_drive_0p75_time',
                                                            'premarket_continuation_0p875_1p5r'),
                                 'maximum_finalists_per_family': 1,
                                 'walk_forward_fold_count': 6,
                                 'bootstrap_resamples': 10000,
                                 'mcpt_permutations': 1000,
                                 'mcpt_permutations_greater_or_equal_real': 465,
                                 'mcpt_plus_one_p_value': 0.46553446553446554,
                                 'mcpt_null_method': 'SESSION_SHARED_POST_ENTRY_PATH_SIGN_PERMUTATION',
                                 'mcpt_signals_conditioned_on_entry_known_data': True,
                                 'robustness_results_were_decision_gates': False,
                                 'independent_rebuild': True},
 'phase_c_known_comparison': {'materialized_source_start': '2019-12-01',
                              'materialized_source_end': '2025-12-31',
                              'known_comparison_start': '2020-01-03',
                              'known_comparison_end': '2025-12-31',
                              'finalist_count': 3,
                              'finalist_candidate_ids': ('gap_fade_0p75_1r',
                                                         'opening_drive_0p75_time',
                                                         'premarket_continuation_0p875_1p5r'),
                              'control_count': 2,
                              'control_candidate_ids': ('orb_control_exp005_15m_both_time',
                                                        'orb_control_exp007_30m_long_1r'),
                              'reported_candidate_count': 5,
                              'primary_representation': 'BACKWARD_ADJUSTED',
                              'sensitivity_representation': 'UNADJUSTED',
                              'candidate_reselection': False,
                              'parameter_changes': False,
                              'known_period_is_confirmation': False,
                              'unadjusted_can_change_finalist_identity': False,
                              'independent_rebuild': True,
                              'output_file_count': 14,
                              'output_manifest_sha256': 'c1a66777fa04fb69306ffe737cb15a1190051d0c1f9c34aa2a0b8542049a25c5',
                              'completion_marker_sha256': '7df37817253333f1960a0fbe96dd2c4dc8e5af2204766a1121d35a37d1a23b05',
                              'output_files': {'PHASE_C_COMPLETE.json': {'size_bytes': 1319,
                                                                         'sha256': '7df37817253333f1960a0fbe96dd2c4dc8e5af2204766a1121d35a37d1a23b05'},
                                               'annual_results.csv': {'size_bytes': 3714,
                                                                      'sha256': 'ce3b489daf6c47b27e510b3d4c5086d60d0d512b1c98039f25959c5b914b6392'},
                                               'assets/drawdown_curves.png': {'size_bytes': 362808,
                                                                              'sha256': 'b8e2d570c81b1451996eed31a9204ad3dfd0c451b28c5d74033e69045362d566'},
                                               'assets/equity_curves.png': {'size_bytes': 205202,
                                                                            'sha256': 'c0db2fa8f3bca3e4e18ec92510c4353d74a69e6fc73d49d4e9afc8a1e17f0dd6'},
                                               'cost_sensitivity.csv': {'size_bytes': 1990,
                                                                        'sha256': '277cad1090024860fa3233b251129cf76ede643b60fa016ff48dbd772690ffa3'},
                                               'drawdown_episodes.csv': {'size_bytes': 12561,
                                                                         'sha256': 'ce48212324a4d2e94138d13e7da4dbbb1039f01c573a34a08c5a5f1ab3b5e66f'},
                                               'known_comparison_metrics.csv': {'size_bytes': 5362,
                                                                                'sha256': '22da9e4599d5ccf912409adf3578cd9880e7db976ef21a0a204f9716a8e26fab'},
                                               'known_comparison_summary.json': {'size_bytes': 506,
                                                                                 'sha256': 'c3a053fe074980187d5363c38376664dc30b3bb5954aaa67b531ea7ee92e1435'},
                                               'monthly_results.csv': {'size_bytes': 23126,
                                                                       'sha256': '973db92d1fb64a61536e0505fecc9f52080b0da4ebc2afbe5a2caee7308fe17b'},
                                               'output_hashes.json': {'size_bytes': 1841,
                                                                      'sha256': 'c1a66777fa04fb69306ffe737cb15a1190051d0c1f9c34aa2a0b8542049a25c5'},
                                               'report.html': {'size_bytes': 14048,
                                                               'sha256': 'e2ca5cce5d6b01e64723f113c782d2146020a0636897ef807963a9312351e461'},
                                               'report.md': {'size_bytes': 4226,
                                                             'sha256': '48b509018d1a16776130d395e8b4afe32db677e56ec81499a0de5d80b7d07e3a'},
                                               'representation_sensitivity.csv': {'size_bytes': 4807,
                                                                                  'sha256': 'e90449d02aa27d8461e43949f840cacaad6004bcdf3da46eb1385bd92c5f8657'},
                                               'trade_distribution.csv': {'size_bytes': 1934,
                                                                          'sha256': 'a83ba336b79a136145edc63a7e3e20b9889645a50e5fce5888ae3f60df4b0060'}}},
 'execution': {'phase_a_completed': True,
               'phase_b_completed': True,
               'phase_c_completed': True,
               'all_three_phases_completed': True,
               'phase_rerun_after_completion': False,
               'candidate_reselection_after_phase_b': False,
               'parameter_changes_after_registration': False,
               'position_sizing_optimization': False,
               'portfolio_weight_optimization': False,
               'protected_2026_accessed': False,
               'protected_2026_strategy_results_calculated': False,
               'databento_api_calls': 0,
               'new_databento_download_performed': False,
               'network_access_by_python': False,
               'order_api_accessed': False,
               'paper_trading_authorized': False,
               'live_trading_authorized': False},
 'interpretation': {'measurement_first_research_completed': True,
                    'bounded_candidate_comparison_completed': True,
                    'three_family_finalists_selected': True,
                    'finalists_are_measurement_leaders': True,
                    'selection_aware_mcpt_is_contextual': True,
                    'selection_aware_mcpt_establishes_edge': False,
                    'known_2020_2025_is_independent_confirmation': False,
                    'protected_2026_is_confirmation': False,
                    'strategy_edge_validated': False,
                    'strategy_failure_established': False,
                    'candidate_accepted_for_trading': False,
                    'candidate_rejected_by_formal_gate': False,
                    'no_automatic_winner': True,
                    'no_strategy_is_accepted_for_trading_by_exp026': True},
 'next_research_boundary': {'exp026_frozen': True,
                            'rerun_phase_a_prohibited': True,
                            'rerun_phase_b_prohibited': True,
                            'rerun_phase_c_prohibited': True,
                            'modify_exp026_preregistration_prohibited': True,
                            'modify_exp026_implementation_prohibited': True,
                            'modify_exp026_authorizations_prohibited': True,
                            'modify_exp026_completion_records_prohibited': True,
                            'modify_exp026_outputs_prohibited': True,
                            'existing_exp026_outputs_may_be_reviewed': True,
                            'finalists_retained_as_separate_evidence_rows': True,
                            'protected_2026_remains_reserved_for_new_experiment': True,
                            'exp027_requires_separate_preregistration': True,
                            'exp027_requires_separate_authorization': True,
                            'exp027_authorized_by_closure': False,
                            'new_databento_download_authorized_by_closure': False,
                            'paper_or_live_trading_not_authorized': True}}

EXPECTED_EXP026_CLOSURE_SHA256 = (
    "8ec79810a26b58f2d445d47d3f496539f121d6f3e139eae4a9fd38ef029a386f"
)


def canonical_record_hash(record: dict[str, Any]) -> str:
    encoded = json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def get_exp026_closure() -> dict[str, Any]:
    return deepcopy(EXP026_CLOSURE)


def validate_exp026_closure(candidate: dict[str, Any] | None = None) -> None:
    record = EXP026_CLOSURE if candidate is None else candidate

    if (
        record.get("experiment_id") != "EXP-026"
        or record.get("closed_date") != "2026-07-28"
        or record.get("research_status") != "REVIEW"
        or record.get("classification") != "COMPLETED_MEASUREMENT_REVIEW"
    ):
        raise ValueError("EXP-026 closure identity changed.")

    repository = record["repository"]
    if (
        repository["preregistration_commit"] != "ce661c7785fa6d8d409378ee2ad63a00f0e0a9b9"
        or repository["implementation_commit"] != "13ee0683dfcbbb5d763f7254f3b245ecc8e6d9cd"
        or repository["phase_a_completion_commit"] != "28bd4209711f0c9b98a7650ab91f6408c2bdf4b7"
        or repository["phase_b_completion_commit"] != "da8456d254dc710336806ad5940afcec649be016"
        or repository["phase_c_completion_commit"] != "a400a373b87b780c21dc2d15048b1e1a5ad1050a"
        or repository["closure_base_head"] != "a400a373b87b780c21dc2d15048b1e1a5ad1050a"
    ):
        raise ValueError("EXP-026 closure repository chain changed.")

    phase_a = record["phase_a_development"]
    phase_b = record["phase_b_internal_validation"]
    phase_c = record["phase_c_known_comparison"]

    if (
        phase_a["decision_rows"] != 46_584
        or phase_a["trade_rows"] != 11_502
        or phase_a["survivor_count"] != 6
        or tuple(phase_a["survivor_candidate_ids"]) != ('gap_fade_0p75_1r', 'gap_fade_0p25_1r', 'opening_drive_0p75_1p5r', 'opening_drive_0p75_time', 'premarket_continuation_0p875_1p5r', 'premarket_continuation_0p625_1p5r')
        or phase_a["recovery_read_market_values"] is not False
        or phase_a["recovery_recalculated_strategy"] is not False
    ):
        raise ValueError("EXP-026 Phase A closure evidence changed.")

    if (
        phase_b["finalist_count"] != 3
        or tuple(phase_b["finalist_candidate_ids"]) != ('gap_fade_0p75_1r', 'opening_drive_0p75_time', 'premarket_continuation_0p875_1p5r')
        or phase_b["mcpt_permutations"] != 1_000
        or phase_b["mcpt_permutations_greater_or_equal_real"] != 465
        or phase_b["mcpt_plus_one_p_value"] != 0.46553446553446554
        or phase_b["robustness_results_were_decision_gates"] is not False
    ):
        raise ValueError("EXP-026 Phase B closure evidence changed.")

    if (
        phase_c["known_comparison_start"] != "2020-01-03"
        or phase_c["known_comparison_end"] != "2025-12-31"
        or tuple(phase_c["finalist_candidate_ids"]) != ('gap_fade_0p75_1r', 'opening_drive_0p75_time', 'premarket_continuation_0p875_1p5r')
        or tuple(phase_c["control_candidate_ids"]) != ('orb_control_exp005_15m_both_time', 'orb_control_exp007_30m_long_1r')
        or phase_c["candidate_reselection"] is not False
        or phase_c["parameter_changes"] is not False
        or phase_c["known_period_is_confirmation"] is not False
        or phase_c["independent_rebuild"] is not True
        or phase_c["output_file_count"] != 14
    ):
        raise ValueError("EXP-026 Phase C closure evidence changed.")

    execution = record["execution"]
    interpretation = record["interpretation"]
    boundary = record["next_research_boundary"]

    if (
        execution["all_three_phases_completed"] is not True
        or execution["protected_2026_accessed"] is not False
        or execution["protected_2026_strategy_results_calculated"] is not False
        or execution["databento_api_calls"] != 0
        or execution["new_databento_download_performed"] is not False
        or execution["network_access_by_python"] is not False
        or execution["order_api_accessed"] is not False
        or execution["paper_trading_authorized"] is not False
        or execution["live_trading_authorized"] is not False
    ):
        raise ValueError("EXP-026 closure execution boundary changed.")

    if (
        interpretation["measurement_first_research_completed"] is not True
        or interpretation["finalists_are_measurement_leaders"] is not True
        or interpretation["selection_aware_mcpt_establishes_edge"] is not False
        or interpretation["known_2020_2025_is_independent_confirmation"] is not False
        or interpretation["strategy_edge_validated"] is not False
        or interpretation["strategy_failure_established"] is not False
        or interpretation["candidate_accepted_for_trading"] is not False
        or interpretation["no_strategy_is_accepted_for_trading_by_exp026"] is not True
    ):
        raise ValueError("EXP-026 closure interpretation changed.")

    if (
        boundary["exp026_frozen"] is not True
        or boundary["rerun_phase_a_prohibited"] is not True
        or boundary["rerun_phase_b_prohibited"] is not True
        or boundary["rerun_phase_c_prohibited"] is not True
        or boundary["protected_2026_remains_reserved_for_new_experiment"] is not True
        or boundary["exp027_requires_separate_preregistration"] is not True
        or boundary["exp027_requires_separate_authorization"] is not True
        or boundary["exp027_authorized_by_closure"] is not False
        or boundary["new_databento_download_authorized_by_closure"] is not False
        or boundary["paper_or_live_trading_not_authorized"] is not True
    ):
        raise ValueError("EXP-026 closure next-research boundary changed.")

    if canonical_record_hash(record) != EXPECTED_EXP026_CLOSURE_SHA256:
        raise ValueError("EXP-026 closure record changed.")

    if candidate is None:
        from experiment_lifecycle import get_experiment_lifecycle
        from exp026_phase_a_completion import validate_exp026_phase_a_completion
        from exp026_phase_b_completion import validate_exp026_phase_b_completion
        from exp026_phase_c_completion import validate_exp026_phase_c_completion

        validate_exp026_phase_a_completion()
        validate_exp026_phase_b_completion()
        validate_exp026_phase_c_completion()
        lifecycle = get_experiment_lifecycle("EXP-026")
        if (
            lifecycle.stage != "REVIEW"
            or "COMPLETED_MEASUREMENT_REVIEW" not in lifecycle.stage_reason
        ):
            raise ValueError("EXP-026 closure lifecycle changed.")
