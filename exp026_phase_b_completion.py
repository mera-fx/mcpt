from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

PROJECT_DIR = Path(__file__).resolve().parent
COMPLETION_PATHS = (
    "exp026_phase_b_completion.py",
    "research/EXP-026_phase_b_completion.md",
    "tests/test_exp026_phase_b_completion.py",
)
UNCOMMITTED_COMPLETION_COMMIT = "0000000000000000000000000000000000000000"
EXPECTED_OUTPUT_FILES: dict[str, dict[str, Any]] = {'PHASE_B_COMPLETE.json': {'size_bytes': 1534,
                           'sha256': '02fdd3fc5f8387d0daeee43b4da5d75a032cdf756d1c19783e067bbeb41343e0'},
 'assets/drawdown_curves.png': {'size_bytes': 286339,
                                'sha256': '24609b848f24fd72ab6d4e51e0e7f5abb12b0a034ad68bf255fed32dac16cb0f'},
 'assets/equity_curves.png': {'size_bytes': 254566,
                              'sha256': '6e2e99f073e4426c1e98f078e397193143ae58bb7c2e71d132e33341de5d414e'},
 'bootstrap_summary.csv': {'size_bytes': 705,
                           'sha256': '8ed99915e58cd211441580d345ff933a5734ff8a0e9ecfece60f857d71fee2fd'},
 'internal_validation_metrics.csv': {'size_bytes': 8042,
                                     'sha256': '9efb6a32d1991938a76aa910c739d3a2e8d9511dead6bf16f16eaa71d4a17f31'},
 'internal_validation_summary.json': {'size_bytes': 731,
                                      'sha256': 'fc94abdfe9027c497003918642e848aebd1694095107410ee283be904dbbea55'},
 'mcpt_summary.json': {'size_bytes': 769,
                       'sha256': 'ab9fc4c63a970c4e00fda819139612d7191e9afe6e63ad9b1d1b334f0b1f8d6f'},
 'output_hashes.json': {'size_bytes': 1694,
                        'sha256': 'c26b20ceadfec332e9dd72870bc25b37554e184216515a8b8f868c24c0e621a9'},
 'parameter_stability.csv': {'size_bytes': 4891,
                             'sha256': 'ba5b475b1683058e26e18067c37e8a9b028c638407b705645a828068fc300c1c'},
 'report.html': {'size_bytes': 20503,
                 'sha256': '7dd21d377d1217c347d629d494bddb83106bfa3a2f9c6986e4dc8bdf3b38e514'},
 'report.md': {'size_bytes': 6197,
               'sha256': '8c02b66565c06c7fd06b607bc5f3775425691fabcac949af8b5dbc08ca782728'},
 'selected_finalists.json': {'size_bytes': 504,
                             'sha256': '6c23d1b52501fafa3b966d9f4060421cad65e789b90651d25ca0ab582a1acc77'},
 'walk_forward_results.csv': {'size_bytes': 2674,
                              'sha256': 'ac52ce63ff9301be7791e9e9eb39318bbb5996264eff1ae4da693be0c9bb0a3f'}}
EXP026_PHASE_B_COMPLETION: dict[str, Any] = {'schema_version': 1,
 'experiment_id': 'EXP-026',
 'phase': 'B',
 'title': 'EXP-026 Phase B Completion Record',
 'completed': True,
 'completion_date': '2026-07-28',
 'implementation_commit': '13ee0683dfcbbb5d763f7254f3b245ecc8e6d9cd',
 'phase_a_completion_commit': '28bd4209711f0c9b98a7650ab91f6408c2bdf4b7',
 'authorization_commit': '20ed5ba203f2e4bb3940de389afface6b749d7c7',
 'authorization_sha256': '3522b27be25a3f3dced19492d1043dda69b3a134e480453f0b868e9ae310eee5',
 'output_directory': 'results/EXP-026/phase_b_internal_validation',
 'materialized_source_start': '2010-06-07',
 'materialized_source_end': '2019-12-31',
 'internal_validation_start': '2018-01-01',
 'internal_validation_end': '2019-12-31',
 'phase_a_survivor_count': 6,
 'phase_a_survivor_ids': ('gap_fade_0p75_1r',
                          'gap_fade_0p25_1r',
                          'opening_drive_0p75_1p5r',
                          'opening_drive_0p75_time',
                          'premarket_continuation_0p875_1p5r',
                          'premarket_continuation_0p625_1p5r'),
 'finalist_count': 3,
 'finalist_candidate_ids': ('gap_fade_0p75_1r',
                            'opening_drive_0p75_time',
                            'premarket_continuation_0p875_1p5r'),
 'maximum_finalists_per_family': 1,
 'walk_forward_fold_count': 6,
 'bootstrap_resamples': 10000,
 'bootstrap_random_seed': 26027,
 'mcpt_permutations': 1000,
 'mcpt_random_seed': 26026,
 'mcpt_permutations_greater_or_equal_real': 465,
 'mcpt_plus_one_p_value': 0.46553446553446554,
 'mcpt_real_statistic': 14.0,
 'mcpt_null_method': 'SESSION_SHARED_POST_ENTRY_PATH_SIGN_PERMUTATION',
 'mcpt_signals_conditioned_on_entry_known_data': True,
 'robustness_results_are_decision_gates': False,
 'independent_rebuild': True,
 'required_output_names': ('internal_validation_summary.json',
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
 'all_output_paths': ('PHASE_B_COMPLETE.json',
                      'assets/drawdown_curves.png',
                      'assets/equity_curves.png',
                      'bootstrap_summary.csv',
                      'internal_validation_metrics.csv',
                      'internal_validation_summary.json',
                      'mcpt_summary.json',
                      'output_hashes.json',
                      'parameter_stability.csv',
                      'report.html',
                      'report.md',
                      'selected_finalists.json',
                      'walk_forward_results.csv'),
 'output_files': {'PHASE_B_COMPLETE.json': {'size_bytes': 1534,
                                            'sha256': '02fdd3fc5f8387d0daeee43b4da5d75a032cdf756d1c19783e067bbeb41343e0'},
                  'assets/drawdown_curves.png': {'size_bytes': 286339,
                                                 'sha256': '24609b848f24fd72ab6d4e51e0e7f5abb12b0a034ad68bf255fed32dac16cb0f'},
                  'assets/equity_curves.png': {'size_bytes': 254566,
                                               'sha256': '6e2e99f073e4426c1e98f078e397193143ae58bb7c2e71d132e33341de5d414e'},
                  'bootstrap_summary.csv': {'size_bytes': 705,
                                            'sha256': '8ed99915e58cd211441580d345ff933a5734ff8a0e9ecfece60f857d71fee2fd'},
                  'internal_validation_metrics.csv': {'size_bytes': 8042,
                                                      'sha256': '9efb6a32d1991938a76aa910c739d3a2e8d9511dead6bf16f16eaa71d4a17f31'},
                  'internal_validation_summary.json': {'size_bytes': 731,
                                                       'sha256': 'fc94abdfe9027c497003918642e848aebd1694095107410ee283be904dbbea55'},
                  'mcpt_summary.json': {'size_bytes': 769,
                                        'sha256': 'ab9fc4c63a970c4e00fda819139612d7191e9afe6e63ad9b1d1b334f0b1f8d6f'},
                  'output_hashes.json': {'size_bytes': 1694,
                                         'sha256': 'c26b20ceadfec332e9dd72870bc25b37554e184216515a8b8f868c24c0e621a9'},
                  'parameter_stability.csv': {'size_bytes': 4891,
                                              'sha256': 'ba5b475b1683058e26e18067c37e8a9b028c638407b705645a828068fc300c1c'},
                  'report.html': {'size_bytes': 20503,
                                  'sha256': '7dd21d377d1217c347d629d494bddb83106bfa3a2f9c6986e4dc8bdf3b38e514'},
                  'report.md': {'size_bytes': 6197,
                                'sha256': '8c02b66565c06c7fd06b607bc5f3775425691fabcac949af8b5dbc08ca782728'},
                  'selected_finalists.json': {'size_bytes': 504,
                                              'sha256': '6c23d1b52501fafa3b966d9f4060421cad65e789b90651d25ca0ab582a1acc77'},
                  'walk_forward_results.csv': {'size_bytes': 2674,
                                               'sha256': 'ac52ce63ff9301be7791e9e9eb39318bbb5996264eff1ae4da693be0c9bb0a3f'}},
 'output_manifest_sha256': 'c26b20ceadfec332e9dd72870bc25b37554e184216515a8b8f868c24c0e621a9',
 'completion_marker_sha256': '02fdd3fc5f8387d0daeee43b4da5d75a032cdf756d1c19783e067bbeb41343e0',
 'known_2020_2025_accessed': False,
 'known_2020_2025_access_authorized': False,
 'phase_c_execution_authorized': False,
 'protected_2026_accessed': False,
 'protected_2026_access_authorized': False,
 'new_databento_download_authorized': False,
 'databento_api_calls': 0,
 'network_access': False,
 'paper_trading_authorized': False,
 'live_trading_authorized': False,
 'interpretation': {'internal_validation': True,
                    'measurement_first': True,
                    'finalists_are_not_confirmed_edges': True,
                    'mcpt_is_conditional_on_entry_known_setups': True,
                    'phase_c_requires_separate_authorization': True,
                    'known_2020_2025_cannot_change_finalist_identity': True,
                    'exp027_not_authorized': True}}
EXPECTED_EXP026_PHASE_B_COMPLETION_SHA256 = "bbc5e38f4f08ef87d423f1d7890fd2dc87c5afd2068287f4272c7f46bcb1b3de"


def canonical_record_hash(record: dict[str, Any]) -> str:
    encoded = json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _latest_commit(relative_path: str) -> str:
    return subprocess.run(
        ["git", "log", "-1", "--format=%H", "--", relative_path],
        cwd=PROJECT_DIR,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()


def resolve_exp026_phase_b_completion_commit() -> str:
    commits = {_latest_commit(path) for path in COMPLETION_PATHS}
    if commits == {""}:
        return UNCOMMITTED_COMPLETION_COMMIT
    if len(commits) != 1 or "" in commits:
        raise RuntimeError(
            "EXP-026 Phase B completion files do not share one commit."
        )
    value = next(iter(commits))
    if len(value) != 40:
        raise RuntimeError("EXP-026 Phase B completion commit is invalid.")
    return value


def get_exp026_phase_b_completion() -> dict[str, Any]:
    record = deepcopy(EXP026_PHASE_B_COMPLETION)
    record["completion_commit"] = resolve_exp026_phase_b_completion_commit()
    return record


def _validate_output_evidence() -> None:
    output_dir = (
        PROJECT_DIR / "results" / "EXP-026" / "phase_b_internal_validation"
    )
    partial_dir = output_dir.with_name("phase_b_internal_validation.partial")
    if not output_dir.is_dir():
        raise ValueError("EXP-026 Phase B final output is missing.")
    if partial_dir.exists():
        raise ValueError("EXP-026 Phase B partial output still exists.")
    actual = {
        str(path.relative_to(output_dir)).replace("\\", "/")
        for path in output_dir.rglob("*")
        if path.is_file()
    }
    if actual != set(EXPECTED_OUTPUT_FILES):
        raise ValueError("EXP-026 Phase B output population changed.")
    for relative_path, expected in EXPECTED_OUTPUT_FILES.items():
        path = output_dir / Path(relative_path)
        if (
            int(path.stat().st_size) != int(expected["size_bytes"])
            or sha256_file(path) != str(expected["sha256"])
        ):
            raise ValueError(
                f"EXP-026 Phase B output changed: {relative_path}."
            )


def validate_exp026_phase_b_completion(
    candidate: dict[str, Any] | None = None,
) -> None:
    record = EXP026_PHASE_B_COMPLETION if candidate is None else candidate
    if (
        record.get("experiment_id") != "EXP-026"
        or record.get("phase") != "B"
        or record.get("completed") is not True
        or record.get("completion_date") != "2026-07-28"
    ):
        raise ValueError("EXP-026 Phase B completion identity changed.")
    if (
        record.get("implementation_commit") != "13ee0683dfcbbb5d763f7254f3b245ecc8e6d9cd"
        or record.get("phase_a_completion_commit") != "28bd4209711f0c9b98a7650ab91f6408c2bdf4b7"
        or record.get("authorization_commit") != "20ed5ba203f2e4bb3940de389afface6b749d7c7"
        or record.get("authorization_sha256") != "3522b27be25a3f3dced19492d1043dda69b3a134e480453f0b868e9ae310eee5"
    ):
        raise ValueError("EXP-026 Phase B completion ancestry changed.")
    if (
        record.get("internal_validation_start") != "2018-01-01"
        or record.get("internal_validation_end") != "2019-12-31"
        or tuple(record.get("phase_a_survivor_ids", ())) != ('gap_fade_0p75_1r', 'gap_fade_0p25_1r', 'opening_drive_0p75_1p5r', 'opening_drive_0p75_time', 'premarket_continuation_0p875_1p5r', 'premarket_continuation_0p625_1p5r')
        or record.get("finalist_count") != 3
        or tuple(record.get("finalist_candidate_ids", ())) != ('gap_fade_0p75_1r', 'opening_drive_0p75_time', 'premarket_continuation_0p875_1p5r')
        or record.get("maximum_finalists_per_family") != 1
        or record.get("independent_rebuild") is not True
    ):
        raise ValueError("EXP-026 Phase B completion evidence changed.")
    if (
        record.get("mcpt_permutations") != 1000
        or record.get("mcpt_permutations_greater_or_equal_real") != 465
        or record.get("mcpt_plus_one_p_value") != 0.46553446553446554
        or record.get("robustness_results_are_decision_gates") is not False
    ):
        raise ValueError("EXP-026 Phase B robustness evidence changed.")
    if (
        record.get("known_2020_2025_accessed") is not False
        or record.get("known_2020_2025_access_authorized") is not False
        or record.get("phase_c_execution_authorized") is not False
        or record.get("protected_2026_accessed") is not False
        or record.get("protected_2026_access_authorized") is not False
        or record.get("new_databento_download_authorized") is not False
        or record.get("databento_api_calls") != 0
        or record.get("network_access") is not False
        or record.get("paper_trading_authorized") is not False
        or record.get("live_trading_authorized") is not False
    ):
        raise ValueError("EXP-026 Phase B protected boundary changed.")
    if canonical_record_hash(record) != EXPECTED_EXP026_PHASE_B_COMPLETION_SHA256:
        raise ValueError("EXP-026 Phase B completion record changed.")
    if candidate is None:
        _validate_output_evidence()
