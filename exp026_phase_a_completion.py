from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parent

COMPLETION_PATHS = (
    "exp026_phase_a_completion.py",
    "research/EXP-026_phase_a_completion.md",
    "tests/test_exp026_phase_a_completion.py",
)

UNCOMMITTED_COMPLETION_COMMIT = "0000000000000000000000000000000000000000"

EXPECTED_OUTPUT_FILES: dict[str, dict[str, Any]] = {'development_summary.json': {'size_bytes': 567,
                              'sha256': '4a18a93c22eeefbf2d4cc028bdb8c36bc6e49dd1ab2a5dbf675a0b10b3910caf'},
 'candidate_registry.csv': {'size_bytes': 2997,
                            'sha256': '325c043aecdbf498f994da07975cf09bb8b44f48812028014aef9998cfe4010f'},
 'development_metrics.csv': {'size_bytes': 24066,
                             'sha256': '5bd340778f3baa239298bc0f79e7cc9b184f820f9a852be6b081106a1a7df45f'},
 'development_annual_results.csv': {'size_bytes': 22801,
                                    'sha256': '753cf86ccb3f6dd0eba9698edd36facdc5b416a035992bdd5cd7385883865146'},
 'phase_a_survivors.json': {'size_bytes': 502,
                            'sha256': 'e9d940a3c247d885d1ea7537a7673ce67a15517ef79ba18ef5d243096a5f27cf'},
 'output_hashes.json': {'size_bytes': 952,
                        'sha256': '6406c73e0944fdde3a4087f9fde98740210c4ec4bbebd97a888aaeb1ccad962b'},
 'report.md': {'size_bytes': 9788,
               'sha256': '0d4fe9e17105c117bdfd54f70f4658ac552fd6bbff3bdc9515900b8375bd6d18'},
 'PHASE_A_COMPLETE.json': {'size_bytes': 1275,
                           'sha256': 'c39eb9eb0f5093bc8b6e3135b280af27be8b229bd577d2bd59828e91447b3342'}}

EXP026_PHASE_A_COMPLETION: dict[str, Any] = {'schema_version': 1,
 'experiment_id': 'EXP-026',
 'phase': 'A',
 'title': 'EXP-026 Phase A Completion Record',
 'completed': True,
 'completion_date': '2026-07-28',
 'completion_mode': 'AUTHORIZED_COMPUTATION_PLUS_PRESENTATION_ONLY_RECOVERY',
 'implementation_commit': '13ee0683dfcbbb5d763f7254f3b245ecc8e6d9cd',
 'authorization_commit': '5fa417ed56c2d620c5d348e9ab43f3d7634518b8',
 'recovery_commit': 'd54289659ffa058ae31558ad3b99b646c31d0bf7',
 'output_directory': 'results/EXP-026/phase_a_development',
 'source_session_start': '2010-06-07',
 'source_session_end': '2017-12-31',
 'decision_rows': 46584,
 'trade_rows': 11502,
 'reported_candidate_count': 24,
 'development_candidate_count': 22,
 'control_candidate_count': 2,
 'survivor_count': 6,
 'survivor_candidate_ids': ('gap_fade_0p75_1r',
                            'gap_fade_0p25_1r',
                            'opening_drive_0p75_1p5r',
                            'opening_drive_0p75_time',
                            'premarket_continuation_0p875_1p5r',
                            'premarket_continuation_0p625_1p5r'),
 'maximum_survivors_per_family': 2,
 'independent_rebuild': True,
 'recovery_id': 'EXP-026-A-R1',
 'recovery_read_market_values': False,
 'recovery_recalculated_strategy': False,
 'required_output_names': ('development_summary.json',
                           'candidate_registry.csv',
                           'development_metrics.csv',
                           'development_annual_results.csv',
                           'phase_a_survivors.json',
                           'output_hashes.json',
                           'report.md',
                           'PHASE_A_COMPLETE.json'),
 'output_files': {'development_summary.json': {'size_bytes': 567,
                                               'sha256': '4a18a93c22eeefbf2d4cc028bdb8c36bc6e49dd1ab2a5dbf675a0b10b3910caf'},
                  'candidate_registry.csv': {'size_bytes': 2997,
                                             'sha256': '325c043aecdbf498f994da07975cf09bb8b44f48812028014aef9998cfe4010f'},
                  'development_metrics.csv': {'size_bytes': 24066,
                                              'sha256': '5bd340778f3baa239298bc0f79e7cc9b184f820f9a852be6b081106a1a7df45f'},
                  'development_annual_results.csv': {'size_bytes': 22801,
                                                     'sha256': '753cf86ccb3f6dd0eba9698edd36facdc5b416a035992bdd5cd7385883865146'},
                  'phase_a_survivors.json': {'size_bytes': 502,
                                             'sha256': 'e9d940a3c247d885d1ea7537a7673ce67a15517ef79ba18ef5d243096a5f27cf'},
                  'output_hashes.json': {'size_bytes': 952,
                                         'sha256': '6406c73e0944fdde3a4087f9fde98740210c4ec4bbebd97a888aaeb1ccad962b'},
                  'report.md': {'size_bytes': 9788,
                                'sha256': '0d4fe9e17105c117bdfd54f70f4658ac552fd6bbff3bdc9515900b8375bd6d18'},
                  'PHASE_A_COMPLETE.json': {'size_bytes': 1275,
                                            'sha256': 'c39eb9eb0f5093bc8b6e3135b280af27be8b229bd577d2bd59828e91447b3342'}},
 'output_manifest_sha256': '6406c73e0944fdde3a4087f9fde98740210c4ec4bbebd97a888aaeb1ccad962b',
 'completion_marker_sha256': 'c39eb9eb0f5093bc8b6e3135b280af27be8b229bd577d2bd59828e91447b3342',
 'phase_b_execution_authorized': False,
 'phase_c_execution_authorized': False,
 'protected_2026_accessed': False,
 'protected_2026_access_authorized': False,
 'new_databento_download_authorized': False,
 'databento_api_calls': 0,
 'network_access': False,
 'paper_trading_authorized': False,
 'live_trading_authorized': False,
 'interpretation': {'exploratory_development': True,
                    'measurement_first': True,
                    'survivors_are_not_validated_edges': True,
                    'phase_b_requires_separate_authorization': True,
                    'phase_c_requires_separate_authorization': True,
                    'exp027_not_authorized': True}}

EXPECTED_EXP026_PHASE_A_COMPLETION_SHA256 = (
    "79899140135d5d4aba92c0f7aa7056dce6a0540f9e48d2e70383e7c4cc5ecf40"
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


def _latest_commit(relative_path: str) -> str:
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


def resolve_exp026_phase_a_completion_commit() -> str:
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
            "EXP-026 Phase A completion files "
            "do not share one commit."
        )
    value = next(iter(commits))
    if len(value) != 40:
        raise RuntimeError(
            "EXP-026 Phase A completion commit is invalid."
        )
    return value


def get_exp026_phase_a_completion() -> dict[str, Any]:
    record = deepcopy(
        EXP026_PHASE_A_COMPLETION
    )
    record["completion_commit"] = (
        resolve_exp026_phase_a_completion_commit()
    )
    return record


def _validate_output_evidence() -> None:
    output_dir = (
        PROJECT_DIR
        / "results"
        / "EXP-026"
        / "phase_a_development"
    )
    partial_dir = output_dir.with_name(
        "phase_a_development.partial"
    )
    if not output_dir.is_dir():
        raise ValueError(
            "EXP-026 Phase A final output is missing."
        )
    if partial_dir.exists():
        raise ValueError(
            "EXP-026 Phase A partial output still exists."
        )
    names = {
        path.name
        for path in output_dir.iterdir()
        if path.is_file()
    }
    if names != set(EXPECTED_OUTPUT_FILES):
        raise ValueError(
            "EXP-026 Phase A output population changed."
        )
    for name, expected in (
        EXPECTED_OUTPUT_FILES.items()
    ):
        path = output_dir / name
        if (
            int(path.stat().st_size)
            != int(expected["size_bytes"])
            or sha256_file(path)
            != str(expected["sha256"])
        ):
            raise ValueError(
                "EXP-026 Phase A output changed: "
                f"{name}."
            )


def validate_exp026_phase_a_completion(
    candidate: dict[str, Any] | None = None,
) -> None:
    record = (
        EXP026_PHASE_A_COMPLETION
        if candidate is None
        else candidate
    )

    if (
        record.get("experiment_id") != "EXP-026"
        or record.get("phase") != "A"
        or record.get("completed") is not True
        or record.get("completion_date")
        != "2026-07-28"
        or record.get("completion_mode")
        != (
            "AUTHORIZED_COMPUTATION_PLUS_"
            "PRESENTATION_ONLY_RECOVERY"
        )
    ):
        raise ValueError(
            "EXP-026 Phase A completion identity changed."
        )

    if (
        record.get("implementation_commit")
        != "13ee0683dfcbbb5d763f7254f3b245ecc8e6d9cd"
        or record.get("authorization_commit")
        != "5fa417ed56c2d620c5d348e9ab43f3d7634518b8"
        or record.get("recovery_commit")
        != "d54289659ffa058ae31558ad3b99b646c31d0bf7"
    ):
        raise ValueError(
            "EXP-026 Phase A completion ancestry changed."
        )

    if (
        record.get("source_session_start")
        != "2010-06-07"
        or record.get("source_session_end")
        != "2017-12-31"
        or record.get("decision_rows") != 46584
        or record.get("trade_rows") != 11502
        or record.get("survivor_count") != 6
        or tuple(
            record.get(
                "survivor_candidate_ids",
                (),
            )
        )
        != ('gap_fade_0p75_1r', 'gap_fade_0p25_1r', 'opening_drive_0p75_1p5r', 'opening_drive_0p75_time', 'premarket_continuation_0p875_1p5r', 'premarket_continuation_0p625_1p5r')
        or record.get("independent_rebuild")
        is not True
    ):
        raise ValueError(
            "EXP-026 Phase A completion evidence changed."
        )

    if (
        record.get("phase_b_execution_authorized")
        is not False
        or record.get("phase_c_execution_authorized")
        is not False
        or record.get("protected_2026_accessed")
        is not False
        or record.get(
            "protected_2026_access_authorized"
        )
        is not False
        or record.get(
            "new_databento_download_authorized"
        )
        is not False
        or record.get("databento_api_calls") != 0
        or record.get("network_access") is not False
        or record.get("paper_trading_authorized")
        is not False
        or record.get("live_trading_authorized")
        is not False
    ):
        raise ValueError(
            "EXP-026 Phase A protected boundary changed."
        )

    if (
        canonical_record_hash(record)
        != EXPECTED_EXP026_PHASE_A_COMPLETION_SHA256
    ):
        raise ValueError(
            "EXP-026 Phase A completion record changed."
        )

    if candidate is None:
        _validate_output_evidence()
