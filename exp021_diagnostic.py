from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import gc
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

import pandas as pd

from exp020_constructor_core import (
    EXPECTED_CONTRACT_COUNT,
    EXPECTED_RECORD_COUNT,
    normalise_contract_frame,
    daily_volume,
)
from exp021_diagnostic_core import (
    CANDIDATE_SUMMARY_FIELDS,
    CANDIDATE_TRANSITION_FIELDS,
    DAILY_VOLUME_FIELDS,
    EXPECTED_CANDIDATE_IDS,
    build_diagnostics,
)
from exp021_preregistration import (
    EXPECTED_EXP020_CLOSURE_SHA256,
    EXPECTED_EXP021_PREREGISTRATION_SHA256,
    get_exp021_preregistration,
    validate_exp021_preregistration,
)


PROJECT_DIR = Path(__file__).resolve().parent

LOCKED_PREREGISTRATION_COMMIT = (
    "27a960ad68f2059e5ac9d60e42e41a9171fbda41"
)

PREREGISTRATION_PATHS = (
    "exp021_preregistration.py",
    "research/EXP-021_preregistration.md",
    "tests/test_exp021_preregistration.py",
)

IMPLEMENTATION_PATHS = (
    "exp021_diagnostic.py",
    "exp021_diagnostic_core.py",
    "tests/test_exp021_diagnostic.py",
    "research/EXP-021_implementation_report.md",
)

AUTHORIZATION_MODULE = (
    "exp021_diagnostic_authorization"
)

AUTHORIZATION_PATH = (
    PROJECT_DIR
    / "exp021_diagnostic_authorization.py"
)

AUTHORIZATION_PATHS = (
    "exp021_diagnostic_authorization.py",
    "research/EXP-021_diagnostic_authorization.md",
    "tests/test_exp021_diagnostic_authorization.py",
)

ARCHIVE_ROOT = (
    PROJECT_DIR
    / "data"
    / "EXP-019"
    / "exact_contract_archive"
)

EXP020_OUTPUT_DIR = (
    PROJECT_DIR
    / "results"
    / "EXP-020"
    / "continuous_series"
)

OUTPUT_PARENT = (
    PROJECT_DIR
    / "results"
    / "EXP-021"
)

OUTPUT_DIR = (
    OUTPUT_PARENT
    / "volume_roll_diagnostic"
)

PARTIAL_OUTPUT_DIR = (
    OUTPUT_PARENT
    / "volume_roll_diagnostic.partial"
)

VERIFICATION_OUTPUT_DIR = (
    OUTPUT_PARENT
    / "volume_roll_diagnostic.verification"
)

EXPECTED_ARCHIVE_SHA256 = (
    "225a64dc06cb6bb303fd83d186f2e7d8"
    "1e2a8a8bec44382380c8ccc1b0b6baa3"
)

EXPECTED_EXP020_OUTPUT_HASHES = {
    "calendar_roll_backward_adjusted.parquet": (
        "363670228327447833f23d1b223d63f75"
        "a44980804363770fd84dca907ada800"
    ),
    "calendar_roll_unadjusted.parquet": (
        "b4058e1f9f496f117e4bd78c66fe56e6"
        "b82eb869215eba088e783d5d6dbe0285"
    ),
    "CONSTRUCTION_COMPLETE.json": (
        "ba0b38184733d19df0cd56f5343797d2"
        "c6355407ac8bd72cf0b20bea6adbe593"
    ),
    "construction_summary.json": (
        "afe2a60f6f7f284a46e6f54de157b494"
        "8528bc229ee8c5d7a0b6fea23116f830"
    ),
    "contract_contribution.csv": (
        "0f11cc4681d71008ea851a83cce6f0789"
        "8c0437e77c6b0e239d39858a199e765"
    ),
    "method_comparison.csv": (
        "28438a952aa1696d9fe6381b67e9f8b8"
        "b5a563400bd9ab4882a9cbd35cfaf828"
    ),
    "output_hashes.json": (
        "8b06b1cc9967de27024ff19b29358d3b7"
        "d930bdfef82c91f62ca63d293f30580"
    ),
    "report.md": (
        "8ded0ddd7577bc82cab6898a0e61627f"
        "52b8888fd80d2e0353872e92415966d2"
    ),
    "roll_ledger.csv": (
        "6935bc97353cf68344795302ed15f6276"
        "af1492900ea333f3fb03ca34ff56214"
    ),
    "volume_roll_backward_adjusted.parquet": (
        "0a416d7ee25abadd899bc5033a4931edfc"
        "807d667749befa4ee5c3999788cc1e"
    ),
    "volume_roll_unadjusted.parquet": (
        "133e59235060ebf0d5a4c7c777729c8a"
        "b17d999b85a23aa401a6fb0daf825124"
    ),
}

CORE_OUTPUT_NAMES = (
    "daily_volume_diagnostics.csv",
    "candidate_transition_diagnostics.csv",
    "candidate_method_summary.csv",
    "selected_method.json",
)

REQUIRED_OUTPUT_NAMES = (
    *CORE_OUTPUT_NAMES,
    "output_hashes.json",
    "report.md",
    "DIAGNOSTIC_COMPLETE.json",
)


def run_git(
    *args: str,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=PROJECT_DIR,
        text=True,
        capture_output=True,
        check=check,
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for block in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


def canonical_json_bytes(payload: Any) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,
    ).encode("utf-8")


def atomic_write_text(
    path: Path,
    text: str,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    temporary = path.with_name(
        path.name + ".tmp"
    )

    if temporary.exists():
        raise RuntimeError(
            f"Temporary output already exists: {temporary}"
        )

    temporary.write_text(
        text,
        encoding="utf-8",
        newline="\n",
    )
    os.replace(temporary, path)


def atomic_write_json(
    path: Path,
    payload: dict[str, Any],
) -> None:
    atomic_write_text(
        path,
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            ensure_ascii=True,
            default=str,
        )
        + "\n",
    )


def write_csv(
    path: Path,
    rows: list[dict[str, Any]],
    fieldnames: tuple[str, ...],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    temporary = path.with_name(
        path.name + ".tmp"
    )

    if temporary.exists():
        raise RuntimeError(
            f"Temporary CSV exists: {temporary}"
        )

    with temporary.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            extrasaction="raise",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)

    os.replace(temporary, path)


def changed_paths(
    base: str,
    head: str,
) -> set[str]:
    return {
        line.strip().replace("\\", "/")
        for line in run_git(
            "diff",
            "--name-only",
            base,
            head,
        ).stdout.splitlines()
        if line.strip()
    }


def commit_that_added(
    relative_path: str,
) -> str:
    commits = run_git(
        "log",
        "--diff-filter=A",
        "--reverse",
        "--format=%H",
        "--",
        relative_path,
    ).stdout.strip().splitlines()

    if len(commits) != 1:
        raise RuntimeError(
            "Expected exactly one creation commit "
            f"for {relative_path}."
        )

    return commits[0]


def load_authorization() -> dict[str, Any]:
    if not AUTHORIZATION_PATH.is_file():
        raise RuntimeError(
            "EXP-021 diagnostic is not authorized. "
            "The separate authorization file is absent."
        )

    module = importlib.import_module(
        AUTHORIZATION_MODULE
    )
    validator = getattr(
        module,
        "validate_exp021_diagnostic_authorization",
        None,
    )
    getter = getattr(
        module,
        "get_exp021_diagnostic_authorization",
        None,
    )

    if validator is None or getter is None:
        raise RuntimeError(
            "EXP-021 authorization interface "
            "is incomplete."
        )

    validator()
    record = getter()

    if (
        record["experiment_id"] != "EXP-021"
        or record["diagnostic_authorized"] is not True
        or record["one_time_diagnostic"] is not True
        or record["maximum_diagnostic_runs"] != 1
        or record["databento_api_calls"] != 0
        or record["continuous_construction_authorized"]
        is not False
        or record["strategy_run_authorized"] is not False
    ):
        raise RuntimeError(
            "EXP-021 diagnostic authorization "
            "boundary changed."
        )

    implementation_commit = record[
        "locked_implementation_commit"
    ]

    if (
        not isinstance(implementation_commit, str)
        or len(implementation_commit) != 40
    ):
        raise RuntimeError(
            "Locked implementation commit is invalid."
        )

    return record


def snapshot_paths(
    paths: dict[str, Path],
) -> dict[str, dict[str, Any]]:
    result = {}

    for name, path in paths.items():
        if not path.is_file():
            raise RuntimeError(
                f"Missing frozen file: {path}"
            )

        result[name] = {
            "size_bytes": int(path.stat().st_size),
            "sha256": sha256_file(path),
        }

    return result


def verify_frozen_evidence() -> dict[str, Any]:
    from exp019_preregistration import CONTRACT_PLAN
    from exp020_constructor import (
        verify_frozen_source_evidence,
    )
    from exp020_closure import (
        canonical_record_hash,
        get_exp020_closure,
        validate_exp020_closure,
    )

    validate_exp021_preregistration()
    validate_exp020_closure()

    preregistration = get_exp021_preregistration()
    closure = get_exp020_closure()

    if (
        canonical_record_hash(closure)
        != EXPECTED_EXP020_CLOSURE_SHA256
        or preregistration[
            "frozen_inputs"
        ][
            "exp020_closure_record_sha256"
        ]
        != EXPECTED_EXP020_CLOSURE_SHA256
    ):
        raise RuntimeError(
            "Frozen EXP-020 closure hash changed."
        )

    if (
        preregistration[
            "frozen_inputs"
        ][
            "exp019_archive_sha256"
        ]
        != EXPECTED_ARCHIVE_SHA256
    ):
        raise RuntimeError(
            "Frozen EXP-019 archive hash changed."
        )

    source = verify_frozen_source_evidence()

    if (
        len(source["contract_plan"])
        != EXPECTED_CONTRACT_COUNT
        or tuple(source["contract_plan"])
        != tuple(CONTRACT_PLAN)
    ):
        raise RuntimeError(
            "Frozen contract plan changed."
        )

    exp020_paths = {
        name: EXP020_OUTPUT_DIR / name
        for name in EXPECTED_EXP020_OUTPUT_HASHES
    }
    exp020_snapshot = snapshot_paths(
        exp020_paths
    )

    for name, expected in (
        EXPECTED_EXP020_OUTPUT_HASHES.items()
    ):
        if exp020_snapshot[name]["sha256"] != expected:
            raise RuntimeError(
                f"Frozen EXP-020 output changed: {name}"
            )

    return {
        **source,
        "exp020_snapshot": exp020_snapshot,
        "exp020_paths": exp020_paths,
    }


def repository_preflight() -> dict[str, Any]:
    if os.environ.get(
        "DATABENTO_API_KEY",
        "",
    ).strip():
        raise RuntimeError(
            "DATABENTO_API_KEY must not be set "
            "for EXP-021."
        )

    if run_git(
        "status",
        "--porcelain",
    ).stdout.strip():
        raise RuntimeError(
            "Repository must be clean before "
            "EXP-021 preflight or diagnostic."
        )

    branch = run_git(
        "branch",
        "--show-current",
    ).stdout.strip()

    if branch != "main":
        raise RuntimeError(
            f"EXP-021 must run on main, found {branch!r}."
        )

    head = run_git(
        "rev-parse",
        "HEAD",
    ).stdout.strip()
    origin_main = run_git(
        "rev-parse",
        "origin/main",
    ).stdout.strip()

    if head != origin_main:
        raise RuntimeError(
            "Local HEAD and origin/main are not aligned."
        )

    if run_git(
        "merge-base",
        "--is-ancestor",
        LOCKED_PREREGISTRATION_COMMIT,
        "HEAD",
        check=False,
    ).returncode != 0:
        raise RuntimeError(
            "Locked EXP-021 preregistration commit "
            "is not an ancestor of HEAD."
        )

    if run_git(
        "diff",
        "--quiet",
        LOCKED_PREREGISTRATION_COMMIT,
        "HEAD",
        "--",
        *PREREGISTRATION_PATHS,
        check=False,
    ).returncode != 0:
        raise RuntimeError(
            "Locked EXP-021 preregistration files changed."
        )

    authorization = load_authorization()
    implementation_commit = authorization[
        "locked_implementation_commit"
    ]

    if run_git(
        "merge-base",
        "--is-ancestor",
        LOCKED_PREREGISTRATION_COMMIT,
        implementation_commit,
        check=False,
    ).returncode != 0:
        raise RuntimeError(
            "EXP-021 implementation ancestry is invalid."
        )

    if run_git(
        "merge-base",
        "--is-ancestor",
        implementation_commit,
        "HEAD",
        check=False,
    ).returncode != 0:
        raise RuntimeError(
            "Locked EXP-021 implementation is not "
            "an ancestor of HEAD."
        )

    if changed_paths(
        LOCKED_PREREGISTRATION_COMMIT,
        implementation_commit,
    ) != set(IMPLEMENTATION_PATHS):
        raise RuntimeError(
            "EXP-021 implementation scope changed."
        )

    authorization_commit = commit_that_added(
        "exp021_diagnostic_authorization.py"
    )

    if run_git(
        "merge-base",
        "--is-ancestor",
        implementation_commit,
        authorization_commit,
        check=False,
    ).returncode != 0:
        raise RuntimeError(
            "EXP-021 authorization ancestry is invalid."
        )

    if run_git(
        "merge-base",
        "--is-ancestor",
        authorization_commit,
        "HEAD",
        check=False,
    ).returncode != 0:
        raise RuntimeError(
            "EXP-021 authorization is not an ancestor "
            "of HEAD."
        )

    if changed_paths(
        implementation_commit,
        authorization_commit,
    ) != set(AUTHORIZATION_PATHS):
        raise RuntimeError(
            "EXP-021 authorization scope changed."
        )

    protected_paths = (
        *PREREGISTRATION_PATHS,
        *IMPLEMENTATION_PATHS,
        *AUTHORIZATION_PATHS,
    )

    if run_git(
        "diff",
        "--quiet",
        authorization_commit,
        "HEAD",
        "--",
        *protected_paths,
        check=False,
    ).returncode != 0:
        raise RuntimeError(
            "Protected EXP-021 files changed after "
            "authorization."
        )

    for path in (
        OUTPUT_DIR,
        PARTIAL_OUTPUT_DIR,
        VERIFICATION_OUTPUT_DIR,
    ):
        if path.exists():
            raise RuntimeError(
                "EXP-021 output already exists. "
                "Refusing to rerun."
            )

    try:
        import databento
    except ImportError as exc:
        raise RuntimeError(
            "EXP-021 requires installed databento."
        ) from exc

    frozen = verify_frozen_evidence()

    return {
        "branch": branch,
        "head": head,
        "origin_main": origin_main,
        "implementation_commit": (
            implementation_commit
        ),
        "authorization_commit": (
            authorization_commit
        ),
        "databento_version": getattr(
            databento,
            "__version__",
            "unknown",
        ),
        **frozen,
    }


def load_daily_volumes(
    preflight: dict[str, Any],
) -> dict[str, pd.Series]:
    import databento as db

    completed = preflight["completed_by_symbol"]
    daily_by_contract: dict[str, pd.Series] = {}
    total_records = 0

    for sequence, contract in enumerate(
        preflight["contract_plan"],
        start=1,
    ):
        symbol = contract[0]
        entry = completed[symbol]
        path = (
            ARCHIVE_ROOT
            / entry["relative_path"]
        )
        print(
            f"[{sequence:02d}/"
            f"{EXPECTED_CONTRACT_COUNT}] "
            f"Loading {symbol}"
        )
        store = db.DBNStore.from_file(path)
        frame = normalise_contract_frame(
            store.to_df(),
            canonical_symbol=symbol,
        )
        total_records += len(frame)
        daily_by_contract[symbol] = daily_volume(
            frame
        )
        del frame
        del store

    if total_records != EXPECTED_RECORD_COUNT:
        raise RuntimeError(
            "Loaded source record count changed: "
            f"{total_records:,}."
        )

    return daily_by_contract


def write_core_outputs(
    output_dir: Path,
    result: dict[str, Any],
) -> dict[str, str]:
    output_dir.mkdir(
        parents=True,
        exist_ok=False,
    )

    write_csv(
        output_dir
        / "daily_volume_diagnostics.csv",
        result["daily_volume_rows"],
        DAILY_VOLUME_FIELDS,
    )
    write_csv(
        output_dir
        / "candidate_transition_diagnostics.csv",
        result["candidate_transition_rows"],
        CANDIDATE_TRANSITION_FIELDS,
    )
    write_csv(
        output_dir
        / "candidate_method_summary.csv",
        result["candidate_summaries"],
        CANDIDATE_SUMMARY_FIELDS,
    )
    atomic_write_json(
        output_dir / "selected_method.json",
        result["selected_method"],
    )

    return {
        name: sha256_file(output_dir / name)
        for name in CORE_OUTPUT_NAMES
    }


def build_report(
    *,
    summary_rows: list[dict[str, Any]],
    selected: dict[str, Any],
    classification: str,
) -> str:
    lines = [
        "# EXP-021 Volume-Roll Diagnostic",
        "",
        f"**Classification:** `{classification}`",
        "",
        "## Candidate results",
        "",
        "| Rank | Candidate | Clean triggers | "
        "Fallbacks | Non-calendar rolls | Pass |",
        "|---:|---|---:|---:|---:|---|",
    ]

    for row in summary_rows:
        lines.append(
            "| "
            f"{row['selection_rank']} | "
            f"`{row['candidate_id']}` | "
            f"{row['volume_trigger_count_clean_transitions']} | "
            f"{row['calendar_fallback_count']} | "
            f"{row['noncalendar_roll_date_count']} | "
            f"{'Yes' if row['passes_selection_gates'] else 'No'} |"
        )

    lines.extend(
        [
            "",
            "## Selection",
            "",
            (
                f"Selected candidate: `{selected['candidate_id']}`"
                if selected["selected"]
                else "No candidate passed every locked gate."
            ),
            "",
            "This is diagnostic data engineering only. "
            "No continuous series was constructed and no "
            "strategy, return, optimisation, MCPT, paper or "
            "live-trading analysis was run.",
            "",
        ]
    )

    return "\n".join(lines)


def hard_checks(
    *,
    preflight: dict[str, Any],
    first: dict[str, Any],
    second: dict[str, Any],
    first_byte_hashes: dict[str, str],
    second_byte_hashes: dict[str, str],
) -> dict[str, bool]:
    summaries = first["candidate_summaries"]
    transitions = first[
        "candidate_transition_rows"
    ]
    preregistration = (
        get_exp021_preregistration()
    )
    control = next(
        row
        for row in summaries
        if row["candidate_id"]
        == "VOL_GT_OUT_2S_E0"
    )

    source_after = {
        symbol: {
            "relative_path": snapshot[
                "relative_path"
            ],
            "size_bytes": int(
                (
                    ARCHIVE_ROOT
                    / snapshot["relative_path"]
                ).stat().st_size
            ),
            "sha256": sha256_file(
                ARCHIVE_ROOT
                / snapshot["relative_path"]
            ),
        }
        for symbol, snapshot in (
            preflight["source_snapshot"].items()
        )
    }
    exp020_after = snapshot_paths(
        preflight["exp020_paths"]
    )

    all_candidate_counts = {
        candidate_id: sum(
            row["candidate_id"] == candidate_id
            for row in transitions
        )
        for candidate_id in EXPECTED_CANDIDATE_IDS
    }

    checks = {
        "frozen_exp020_closure_hash_matches": (
            preregistration[
                "frozen_inputs"
            ][
                "exp020_closure_record_sha256"
            ]
            == EXPECTED_EXP020_CLOSURE_SHA256
        ),
        "frozen_exp019_archive_hash_matches": (
            preregistration[
                "frozen_inputs"
            ][
                "exp019_archive_sha256"
            ]
            == EXPECTED_ARCHIVE_SHA256
        ),
        "exactly_66_source_contract_files": (
            len(preflight["source_snapshot"])
            == EXPECTED_CONTRACT_COUNT
        ),
        "source_and_exp020_outputs_remain_read_only": (
            source_after
            == preflight["source_snapshot"]
            and exp020_after
            == preflight["exp020_snapshot"]
        ),
        "all_65_adjacent_transitions_present": (
            len({
                row["transition_sequence"]
                for row in transitions
            })
            == 65
        ),
        "daily_volume_aggregation_is_deterministic": (
            first["semantic_hashes"][
                "daily_volume_semantic_sha256"
            ]
            == second["semantic_hashes"][
                "daily_volume_semantic_sha256"
            ]
        ),
        "candidate_matrix_is_exactly_8_methods": (
            tuple(all_candidate_counts)
            == EXPECTED_CANDIDATE_IDS
            and all(
                count == 65
                for count in (
                    all_candidate_counts.values()
                )
            )
        ),
        "control_reproduces_exp020_zero_crossovers": (
            control[
                "volume_trigger_count_all_transitions"
            ]
            == 0
            and control[
                "calendar_fallback_count"
            ]
            == 65
        ),
        "warning_transition_count_is_23": all(
            row["warning_transition_count"]
            == 23
            for row in summaries
        ),
        "warning_transitions_never_select_volume_boundary": (
            all(
                not row["selected_warning_volume"]
                for row in transitions
            )
        ),
        "all_candidates_resolve_65_transitions_with_fallback": (
            all(
                row["resolved_transition_count"]
                == 65
                for row in summaries
            )
        ),
        "all_boundaries_are_inside_locked_overlap": (
            all(
                row["boundary_in_common_overlap"]
                for row in transitions
            )
        ),
        "no_effective_boundary_is_after_expiry": (
            all(
                not row["post_expiry_boundary"]
                for row in transitions
            )
        ),
        "no_strategy_or_return_metric_is_computed": (
            preregistration[
                "objective"
            ][
                "inspect_strategy_performance"
            ]
            is False
            and preregistration[
                "objective"
            ][
                "construct_continuous_series"
            ]
            is False
        ),
        "independent_rebuild_hashes_match": (
            first["semantic_hashes"]
            == second["semantic_hashes"]
            and first_byte_hashes
            == second_byte_hashes
        ),
        "required_outputs_are_complete": True,
    }

    return checks


def execute_diagnostic(
    preflight: dict[str, Any],
) -> dict[str, Any]:
    preregistration = (
        get_exp021_preregistration()
    )
    candidates = preregistration[
        "candidate_methods"
    ]
    fixed_order = preregistration[
        "fixed_selection_order"
    ]
    gates = preregistration[
        "selection_gates"
    ]
    started = datetime.now(timezone.utc)

    first_daily = load_daily_volumes(
        preflight
    )
    first = build_diagnostics(
        first_daily,
        preflight["contract_plan"],
        candidates=candidates,
        fixed_order=fixed_order,
        gates=gates,
    )
    del first_daily
    gc.collect()

    first_byte_hashes = write_core_outputs(
        PARTIAL_OUTPUT_DIR,
        first,
    )

    second_daily = load_daily_volumes(
        preflight
    )
    second = build_diagnostics(
        second_daily,
        preflight["contract_plan"],
        candidates=candidates,
        fixed_order=fixed_order,
        gates=gates,
    )
    del second_daily
    gc.collect()

    second_byte_hashes = write_core_outputs(
        VERIFICATION_OUTPUT_DIR,
        second,
    )

    checks = hard_checks(
        preflight=preflight,
        first=first,
        second=second,
        first_byte_hashes=first_byte_hashes,
        second_byte_hashes=second_byte_hashes,
    )

    failed = [
        key
        for key, passed in checks.items()
        if not passed
    ]

    if failed:
        atomic_write_json(
            PARTIAL_OUTPUT_DIR
            / "DIAGNOSTIC_FAILED.json",
            {
                "experiment_id": "EXP-021",
                "failed_checks": failed,
                "diagnostic_complete": False,
                "databento_api_calls": 0,
                "continuous_construction": False,
                "strategy_run": False,
            },
        )
        raise RuntimeError(
            "EXP-021 hard checks failed: "
            + ", ".join(failed)
        )

    selected = first["selected_method"]
    classification = selected[
        "classification"
    ]

    report = build_report(
        summary_rows=first[
            "candidate_summaries"
        ],
        selected=selected,
        classification=classification,
    )
    atomic_write_text(
        PARTIAL_OUTPUT_DIR / "report.md",
        report,
    )

    output_hashes = {
        name: sha256_file(
            PARTIAL_OUTPUT_DIR / name
        )
        for name in (
            *CORE_OUTPUT_NAMES,
            "report.md",
        )
    }
    atomic_write_json(
        PARTIAL_OUTPUT_DIR
        / "output_hashes.json",
        {
            "schema_version": 1,
            "experiment_id": "EXP-021",
            "semantic_hashes": first[
                "semantic_hashes"
            ],
            "byte_hashes": output_hashes,
        },
    )
    output_hashes["output_hashes.json"] = (
        sha256_file(
            PARTIAL_OUTPUT_DIR
            / "output_hashes.json"
        )
    )

    completed = datetime.now(timezone.utc)
    completion = {
        "schema_version": 1,
        "experiment_id": "EXP-021",
        "classification": classification,
        "diagnostic_complete": True,
        "diagnostic_rerun_authorized": False,
        "selected_method": selected,
        "hard_checks": checks,
        "hard_failure_count": 0,
        "candidate_count": 8,
        "transition_count_per_candidate": 65,
        "source_contracts": 66,
        "source_records": 6_276_486,
        "started_at_utc": started.isoformat(),
        "completed_at_utc": completed.isoformat(),
        "repository": {
            "head": preflight["head"],
            "implementation_commit": preflight[
                "implementation_commit"
            ],
            "authorization_commit": preflight[
                "authorization_commit"
            ],
        },
        "output_hashes": output_hashes,
        "databento_api_calls": 0,
        "continuous_construction": False,
        "strategy_run": False,
        "strategy_use_authorized": False,
        "paper_trading_authorized": False,
        "live_trading_authorized": False,
    }
    atomic_write_json(
        PARTIAL_OUTPUT_DIR
        / "DIAGNOSTIC_COMPLETE.json",
        completion,
    )

    if set(
        path.name
        for path in PARTIAL_OUTPUT_DIR.iterdir()
    ) != set(REQUIRED_OUTPUT_NAMES):
        raise RuntimeError(
            "EXP-021 required output set changed."
        )

    shutil.rmtree(
        VERIFICATION_OUTPUT_DIR
    )
    os.replace(
        PARTIAL_OUTPUT_DIR,
        OUTPUT_DIR,
    )

    return completion


def print_preflight(
    preflight: dict[str, Any],
) -> None:
    print("EXP-021 diagnostic preflight passed.")
    print(
        "Repository HEAD:        "
        + preflight["head"]
    )
    print(
        "Implementation commit:  "
        + preflight["implementation_commit"]
    )
    print(
        "Authorization commit:   "
        + preflight["authorization_commit"]
    )
    print("Candidate methods:      8")
    print("Source contracts:       66")
    print("Source records:         6276486")
    print("Databento API calls:    0")
    print("Diagnostic run:         False")
    print("Continuous construction: False")
    print("Strategy run:           False")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Protected EXP-021 volume-roll diagnostic."
        )
    )
    mode = parser.add_mutually_exclusive_group(
        required=True
    )
    mode.add_argument(
        "--preflight",
        action="store_true",
    )
    mode.add_argument(
        "--diagnose",
        action="store_true",
    )
    parser.add_argument(
        "--confirm-one-time-diagnostic",
        action="store_true",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    preflight = repository_preflight()

    if args.preflight:
        print_preflight(preflight)
        return

    if not args.confirm_one_time_diagnostic:
        raise RuntimeError(
            "The one-time diagnostic confirmation "
            "flag is required."
        )

    completion = execute_diagnostic(
        preflight
    )
    print("EXP-021 diagnostic complete.")
    print(
        "Classification:         "
        + completion["classification"]
    )
    print("Candidate methods:      8")
    print("Transitions/candidate:  65")
    print(
        "Selected method:        "
        + str(
            completion["selected_method"][
                "candidate_id"
            ]
        )
    )
    print("Hard checks passed:     16/16")
    print("Databento API calls:    0")
    print("Continuous construction: False")
    print("Strategy run:           False")
    print("Diagnostic rerun:       Prohibited")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(
            f"ERROR: {exc}",
            file=sys.stderr,
        )
        raise SystemExit(1)
