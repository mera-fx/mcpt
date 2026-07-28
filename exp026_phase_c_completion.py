from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parent

COMPLETION_PATHS = (
    "exp026_phase_c_completion.py",
    "research/EXP-026_phase_c_completion.md",
    "tests/test_exp026_phase_c_completion.py",
)

UNCOMMITTED_COMPLETION_COMMIT = (
    "0000000000000000000000000000000000000000"
)

EXPECTED_OUTPUT_FILES: dict[str, dict[str, Any]] = {'PHASE_C_COMPLETE.json': {'size_bytes': 1319,
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
                            'sha256': 'a83ba336b79a136145edc63a7e3e20b9889645a50e5fce5888ae3f60df4b0060'}}

EXP026_PHASE_C_COMPLETION: dict[str, Any] = {'schema_version': 1,
 'experiment_id': 'EXP-026',
 'phase': 'C',
 'title': 'EXP-026 Phase C Completion Record',
 'completed': True,
 'completion_date': '2026-07-28',
 'experiment_status': 'PHASE_C_COMPLETED_PENDING_CLOSURE',
 'implementation_commit': '13ee0683dfcbbb5d763f7254f3b245ecc8e6d9cd',
 'phase_b_completion_commit': 'da8456d254dc710336806ad5940afcec649be016',
 'authorization_commit': '5e03bb449468b980e003c133ce076cf1b87b3ac7',
 'authorization_sha256': '7b3e59989061ac9f907d8e6ff749fedc6b40a71a4e03ab1b5ff045096c63b4ce',
 'output_directory': 'results/EXP-026/phase_c_known_comparison',
 'materialized_source_start': '2019-12-01',
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
 'candidate_reselection': False,
 'parameter_changes': False,
 'known_period_is_confirmation': False,
 'independent_rebuild': True,
 'primary_representation': 'BACKWARD_ADJUSTED',
 'sensitivity_representation': 'UNADJUSTED',
 'unadjusted_can_change_finalist_identity': False,
 'required_output_names': ('known_comparison_summary.json',
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
 'all_output_paths': ('PHASE_C_COMPLETE.json',
                      'annual_results.csv',
                      'assets/drawdown_curves.png',
                      'assets/equity_curves.png',
                      'cost_sensitivity.csv',
                      'drawdown_episodes.csv',
                      'known_comparison_metrics.csv',
                      'known_comparison_summary.json',
                      'monthly_results.csv',
                      'output_hashes.json',
                      'report.html',
                      'report.md',
                      'representation_sensitivity.csv',
                      'trade_distribution.csv'),
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
                                             'sha256': 'a83ba336b79a136145edc63a7e3e20b9889645a50e5fce5888ae3f60df4b0060'}},
 'output_manifest_sha256': 'c1a66777fa04fb69306ffe737cb15a1190051d0c1f9c34aa2a0b8542049a25c5',
 'completion_marker_sha256': '7df37817253333f1960a0fbe96dd2c4dc8e5af2204766a1121d35a37d1a23b05',
 'protected_2026_accessed': False,
 'protected_2026_access_authorized': False,
 'exp027_execution_authorized': False,
 'new_databento_download_authorized': False,
 'databento_api_calls': 0,
 'network_access': False,
 'paper_trading_authorized': False,
 'live_trading_authorized': False,
 'exp026_closed': False,
 'interpretation': {'known_comparison': True,
                    'measurement_first': True,
                    'known_period_is_not_independent_confirmation': True,
                    'finalists_are_not_confirmed_edges': True,
                    'finalist_identity_remained_frozen': True,
                    'unadjusted_was_sensitivity_only': True,
                    'separate_exp026_closure_commit_required': True,
                    'exp027_requires_separate_preregistration_and_authorization': True,
                    'no_strategy_is_accepted_for_trading': True}}

EXPECTED_EXP026_PHASE_C_COMPLETION_SHA256 = (
    "743aa1638cd00c279e216e6ccfedb402d7d9ce1954daafc3538e6362f4cc247a"
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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(block)
    return digest.hexdigest()


def _latest_commit(
    relative_path: str,
) -> str:
    return subprocess.run(
        [
            "git",
            "log",
            "-1",
            "--format=%H",
            "--",
            relative_path,
        ],
        cwd=PROJECT_DIR,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()


def resolve_exp026_phase_c_completion_commit() -> str:
    commits = {
        _latest_commit(path)
        for path in COMPLETION_PATHS
    }
    if commits == {""}:
        return UNCOMMITTED_COMPLETION_COMMIT
    if (
        len(commits) != 1
        or "" in commits
    ):
        raise RuntimeError(
            "EXP-026 Phase C completion files "
            "do not share one commit."
        )
    value = next(iter(commits))
    if len(value) != 40:
        raise RuntimeError(
            "EXP-026 Phase C completion commit is invalid."
        )
    return value


def get_exp026_phase_c_completion() -> dict[str, Any]:
    record = deepcopy(
        EXP026_PHASE_C_COMPLETION
    )
    record["completion_commit"] = (
        resolve_exp026_phase_c_completion_commit()
    )
    return record


def _validate_output_evidence() -> None:
    output_dir = (
        PROJECT_DIR
        / "results"
        / "EXP-026"
        / "phase_c_known_comparison"
    )
    partial_dir = output_dir.with_name(
        "phase_c_known_comparison.partial"
    )

    if not output_dir.is_dir():
        raise ValueError(
            "EXP-026 Phase C final output is missing."
        )
    if partial_dir.exists():
        raise ValueError(
            "EXP-026 Phase C partial output still exists."
        )

    actual_paths = {
        str(path.relative_to(output_dir)).replace(
            "\\",
            "/",
        )
        for path in output_dir.rglob("*")
        if path.is_file()
    }

    if actual_paths != set(
        EXPECTED_OUTPUT_FILES
    ):
        raise ValueError(
            "EXP-026 Phase C output population changed."
        )

    for relative_path, expected in (
        EXPECTED_OUTPUT_FILES.items()
    ):
        path = (
            output_dir
            / Path(relative_path)
        )
        if (
            int(path.stat().st_size)
            != int(expected["size_bytes"])
            or sha256_file(path)
            != str(expected["sha256"])
        ):
            raise ValueError(
                "EXP-026 Phase C output changed: "
                f"{relative_path}."
            )


def validate_exp026_phase_c_completion(
    candidate: dict[str, Any] | None = None,
) -> None:
    record = (
        EXP026_PHASE_C_COMPLETION
        if candidate is None
        else candidate
    )

    if (
        record.get("experiment_id")
        != "EXP-026"
        or record.get("phase") != "C"
        or record.get("completed")
        is not True
        or record.get("completion_date")
        != "2026-07-28"
        or record.get(
            "experiment_status"
        )
        != "PHASE_C_COMPLETED_PENDING_CLOSURE"
    ):
        raise ValueError(
            "EXP-026 Phase C completion identity changed."
        )

    if (
        record.get(
            "implementation_commit"
        )
        != "13ee0683dfcbbb5d763f7254f3b245ecc8e6d9cd"
        or record.get(
            "phase_b_completion_commit"
        )
        != "da8456d254dc710336806ad5940afcec649be016"
        or record.get(
            "authorization_commit"
        )
        != "5e03bb449468b980e003c133ce076cf1b87b3ac7"
        or record.get(
            "authorization_sha256"
        )
        != "7b3e59989061ac9f907d8e6ff749fedc6b40a71a4e03ab1b5ff045096c63b4ce"
    ):
        raise ValueError(
            "EXP-026 Phase C completion ancestry changed."
        )

    if (
        record.get(
            "known_comparison_start"
        )
        != "2020-01-03"
        or record.get(
            "known_comparison_end"
        )
        != "2025-12-31"
        or record.get("finalist_count")
        != 3
        or tuple(
            record.get(
                "finalist_candidate_ids",
                (),
            )
        )
        != ('gap_fade_0p75_1r', 'opening_drive_0p75_time', 'premarket_continuation_0p875_1p5r')
        or record.get("control_count")
        != 2
        or tuple(
            record.get(
                "control_candidate_ids",
                (),
            )
        )
        != ('orb_control_exp005_15m_both_time', 'orb_control_exp007_30m_long_1r')
        or record.get(
            "candidate_reselection"
        )
        is not False
        or record.get(
            "parameter_changes"
        )
        is not False
        or record.get(
            "known_period_is_confirmation"
        )
        is not False
        or record.get(
            "independent_rebuild"
        )
        is not True
    ):
        raise ValueError(
            "EXP-026 Phase C completion evidence changed."
        )

    if (
        record.get(
            "protected_2026_accessed"
        )
        is not False
        or record.get(
            "protected_2026_access_authorized"
        )
        is not False
        or record.get(
            "exp027_execution_authorized"
        )
        is not False
        or record.get(
            "new_databento_download_authorized"
        )
        is not False
        or record.get(
            "databento_api_calls"
        )
        != 0
        or record.get(
            "network_access"
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
        or record.get(
            "exp026_closed"
        )
        is not False
    ):
        raise ValueError(
            "EXP-026 Phase C protected boundary changed."
        )

    if (
        canonical_record_hash(record)
        != EXPECTED_EXP026_PHASE_C_COMPLETION_SHA256
    ):
        raise ValueError(
            "EXP-026 Phase C completion record changed."
        )

    if candidate is None:
        _validate_output_evidence()
