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
    CONTRIBUTION_FIELDS,
    EXPECTED_CONTRACT_COUNT,
    EXPECTED_RECORD_COUNT,
    SERIES_COLUMNS,
)
from exp022_constructor_core import (
    EXPECTED_CALENDAR_FALLBACKS,
    EXPECTED_CLEAN_FALLBACKS,
    EXPECTED_CLEAN_TRANSITIONS,
    EXPECTED_VOLUME_TRANSITIONS,
    EXPECTED_WARNING_FALLBACKS,
    SELECTED_METHOD,
    SELECTED_ROLL_LEDGER_FIELDS,
    candidate_transition_semantic_hash,
    construct_selected_in_memory,
    final_classification,
    normalise_candidate_transition_rows,
    select_locked_candidate_rows,
    selected_transition_counts,
)
from exp022_preregistration import (
    EXPECTED_EXP021_CLOSURE_SHA256,
    EXPECTED_EXP022_PREREGISTRATION_SHA256,
    get_exp022_preregistration,
    validate_exp022_preregistration,
)


PROJECT_DIR = Path(__file__).resolve().parent

LOCKED_PREREGISTRATION_COMMIT = (
    "73c1255bcb904e71d927ed1097788de9b791bb54"
)

PREREGISTRATION_PATHS = (
    "exp022_preregistration.py",
    "research/EXP-022_preregistration.md",
    "tests/test_exp022_preregistration.py",
)

IMPLEMENTATION_PATHS = (
    "exp022_constructor.py",
    "exp022_constructor_core.py",
    "tests/test_exp022_constructor.py",
    "research/EXP-022_implementation_report.md",
)

AUTHORIZATION_MODULE = (
    "exp022_construction_authorization"
)

AUTHORIZATION_PATH = (
    PROJECT_DIR
    / "exp022_construction_authorization.py"
)

AUTHORIZATION_PATHS = (
    "exp022_construction_authorization.py",
    "research/EXP-022_construction_authorization.md",
    "tests/test_exp022_construction_authorization.py",
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

EXP021_OUTPUT_DIR = (
    PROJECT_DIR
    / "results"
    / "EXP-021"
    / "volume_roll_diagnostic"
)

SELECTED_TRANSITION_PATH = (
    EXP021_OUTPUT_DIR
    / "candidate_transition_diagnostics.csv"
)

OUTPUT_PARENT = (
    PROJECT_DIR
    / "results"
    / "EXP-022"
)

OUTPUT_DIR = (
    OUTPUT_PARENT
    / "selected_continuous_series"
)

PARTIAL_OUTPUT_DIR = (
    OUTPUT_PARENT
    / "selected_continuous_series.partial"
)

VERIFICATION_OUTPUT_DIR = (
    OUTPUT_PARENT
    / "selected_continuous_series.verification"
)

EXPECTED_ARCHIVE_SHA256 = (
    "225a64dc06cb6bb303fd83d186f2e7d8"
    "1e2a8a8bec44382380c8ccc1b0b6baa3"
)

EXPECTED_EXP021_CLOSURE_COMMIT = (
    "253ef695bae819102ec75c3e0cadfa99c8f78d3f"
)

EXPECTED_SELECTED_EVIDENCE_BYTE_SHA256 = (
    "942e7f47fcfc19adfffafd33f04168904a4512967fe0af2d71fd0935c8f2e573"
)

EXPECTED_SELECTED_EVIDENCE_SEMANTIC_SHA256 = (
    "4fd9e261e3b6afe31509f4ec2bf20e58930a8a2dc1e2d30a58215535d439b435"
)

MINIMUM_FREE_BYTES = 3_000_000_000

CORE_OUTPUT_NAMES = (
    "roll_ledger.csv",
    "contract_contribution.csv",
    "selected_roll_unadjusted.parquet",
    "selected_roll_backward_adjusted.parquet",
)

REQUIRED_OUTPUT_NAMES = (
    *CORE_OUTPUT_NAMES,
    "construction_summary.json",
    "output_hashes.json",
    "report.md",
    "CONSTRUCTION_COMPLETE.json",
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


def write_parquet(
    path: Path,
    frame: pd.DataFrame,
) -> None:
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise RuntimeError(
            "pyarrow is required for the locked "
            "EXP-022 Parquet outputs."
        ) from exc

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    temporary = path.with_name(
        path.name + ".tmp"
    )

    if temporary.exists():
        raise RuntimeError(
            f"Temporary Parquet exists: {temporary}"
        )

    table = pa.Table.from_pandas(
        frame.loc[:, SERIES_COLUMNS],
        preserve_index=False,
        safe=True,
    ).replace_schema_metadata(
        {
            b"exp022_schema": (
                b"selected-continuous-series-v1"
            )
        }
    )

    pq.write_table(
        table,
        temporary,
        compression="zstd",
        use_dictionary=False,
        write_statistics=True,
        version="2.6",
        data_page_version="1.0",
        row_group_size=250_000,
    )
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


def load_authorization() -> dict[str, Any]:
    if not AUTHORIZATION_PATH.is_file():
        raise RuntimeError(
            "EXP-022 construction is not authorized. "
            "The separate authorization file is absent."
        )

    module = importlib.import_module(
        AUTHORIZATION_MODULE
    )
    validator = getattr(
        module,
        "validate_exp022_construction_authorization",
        None,
    )
    getter = getattr(
        module,
        "get_exp022_construction_authorization",
        None,
    )

    if validator is None or getter is None:
        raise RuntimeError(
            "EXP-022 authorization interface "
            "is incomplete."
        )

    validator()
    record = getter()

    if (
        record["experiment_id"] != "EXP-022"
        or record["construction_authorized"]
        is not True
        or record["one_time_construction"]
        is not True
        or record["maximum_construction_runs"] != 1
        or record["selected_method"]
        != SELECTED_METHOD
        or record["databento_api_calls"] != 0
        or record["strategy_run_authorized"]
        is not False
    ):
        raise RuntimeError(
            "EXP-022 construction authorization "
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


def load_selected_transition_evidence(
) -> dict[str, Any]:
    if not SELECTED_TRANSITION_PATH.is_file():
        raise RuntimeError(
            "Missing frozen EXP-021 transition evidence."
        )

    if (
        sha256_file(SELECTED_TRANSITION_PATH)
        != EXPECTED_SELECTED_EVIDENCE_BYTE_SHA256
    ):
        raise RuntimeError(
            "Frozen EXP-021 transition file changed."
        )

    frame = pd.read_csv(
        SELECTED_TRANSITION_PATH
    )
    all_rows = normalise_candidate_transition_rows(
        frame
    )
    semantic = candidate_transition_semantic_hash(
        all_rows
    )

    if (
        semantic
        != EXPECTED_SELECTED_EVIDENCE_SEMANTIC_SHA256
    ):
        raise RuntimeError(
            "Frozen EXP-021 transition semantics changed."
        )

    selected = select_locked_candidate_rows(
        all_rows
    )

    return {
        "all_rows": all_rows,
        "selected_rows": selected,
        "semantic_sha256": semantic,
        "byte_sha256": (
            EXPECTED_SELECTED_EVIDENCE_BYTE_SHA256
        ),
        "counts": selected_transition_counts(
            selected
        ),
    }


def verify_frozen_evidence() -> dict[str, Any]:
    from exp020_closure import (
        get_exp020_closure,
        validate_exp020_closure,
    )
    from exp020_constructor import (
        snapshot_archive_files,
        verify_frozen_source_evidence,
    )
    from exp021_closure import (
        canonical_record_hash,
        get_exp021_closure,
        validate_exp021_closure,
    )

    validate_exp022_preregistration()
    validate_exp020_closure()
    validate_exp021_closure()

    preregistration = get_exp022_preregistration()
    exp020_closure = get_exp020_closure()
    exp021_closure = get_exp021_closure()

    if (
        canonical_record_hash(exp021_closure)
        != EXPECTED_EXP021_CLOSURE_SHA256
        or preregistration["frozen_inputs"][
            "exp021_closure_record_sha256"
        ]
        != EXPECTED_EXP021_CLOSURE_SHA256
    ):
        raise RuntimeError(
            "Frozen EXP-021 closure hash changed."
        )

    if (
        preregistration["frozen_inputs"][
            "exp021_closure_commit"
        ]
        != EXPECTED_EXP021_CLOSURE_COMMIT
    ):
        raise RuntimeError(
            "Frozen EXP-021 closure commit changed."
        )

    source = verify_frozen_source_evidence()

    if (
        preregistration["frozen_inputs"][
            "exp019_archive_sha256"
        ]
        != EXPECTED_ARCHIVE_SHA256
        or len(source["contract_plan"])
        != EXPECTED_CONTRACT_COUNT
    ):
        raise RuntimeError(
            "Frozen EXP-019 archive boundary changed."
        )

    exp020_paths = {
        name: EXP020_OUTPUT_DIR / name
        for name in exp020_closure[
            "output_hashes"
        ]
    }
    exp020_snapshot = snapshot_paths(
        exp020_paths
    )

    for name, expected in exp020_closure[
        "output_hashes"
    ].items():
        if exp020_snapshot[name]["sha256"] != expected:
            raise RuntimeError(
                f"Frozen EXP-020 output changed: {name}"
            )

    exp021_paths = {
        name: EXP021_OUTPUT_DIR / name
        for name in exp021_closure[
            "output_files"
        ]
    }
    exp021_snapshot = snapshot_paths(
        exp021_paths
    )

    for name, expected in exp021_closure[
        "output_files"
    ].items():
        if (
            exp021_snapshot[name]["sha256"]
            != expected["sha256"]
            or exp021_snapshot[name]["size_bytes"]
            != int(expected["size_bytes"])
        ):
            raise RuntimeError(
                f"Frozen EXP-021 output changed: {name}"
            )

    selected = load_selected_transition_evidence()

    return {
        **source,
        "snapshot_archive_files": (
            snapshot_archive_files
        ),
        "exp020_paths": exp020_paths,
        "exp020_snapshot": exp020_snapshot,
        "exp021_paths": exp021_paths,
        "exp021_snapshot": exp021_snapshot,
        "selected_evidence": selected,
    }


def repository_preflight() -> dict[str, Any]:
    if os.environ.get(
        "DATABENTO_API_KEY",
        "",
    ).strip():
        raise RuntimeError(
            "DATABENTO_API_KEY must not be set "
            "for EXP-022."
        )

    if run_git(
        "status",
        "--porcelain",
    ).stdout.strip():
        raise RuntimeError(
            "Repository must be clean before "
            "EXP-022 preflight or construction."
        )

    branch = run_git(
        "branch",
        "--show-current",
    ).stdout.strip()

    if branch != "main":
        raise RuntimeError(
            f"EXP-022 must run on main, found {branch!r}."
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
            "Locked EXP-022 preregistration commit "
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
            "Locked EXP-022 preregistration files changed."
        )

    authorization = load_authorization()
    implementation_commit = authorization[
        "locked_implementation_commit"
    ]

    if changed_paths(
        LOCKED_PREREGISTRATION_COMMIT,
        implementation_commit,
    ) != set(IMPLEMENTATION_PATHS):
        raise RuntimeError(
            "EXP-022 implementation scope changed."
        )

    authorization_commit = commit_that_added(
        "exp022_construction_authorization.py"
    )

    if changed_paths(
        implementation_commit,
        authorization_commit,
    ) != set(AUTHORIZATION_PATHS):
        raise RuntimeError(
            "EXP-022 authorization scope changed."
        )

    if (
        run_git(
            "merge-base",
            "--is-ancestor",
            implementation_commit,
            authorization_commit,
            check=False,
        ).returncode
        != 0
        or run_git(
            "merge-base",
            "--is-ancestor",
            authorization_commit,
            "HEAD",
            check=False,
        ).returncode
        != 0
    ):
        raise RuntimeError(
            "EXP-022 implementation/authorization "
            "ancestry is invalid."
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
            "Protected EXP-022 files changed after "
            "authorization."
        )

    for path in (
        OUTPUT_DIR,
        PARTIAL_OUTPUT_DIR,
        VERIFICATION_OUTPUT_DIR,
    ):
        if path.exists():
            raise RuntimeError(
                "EXP-022 output already exists. "
                "Refusing to rerun."
            )

    free_bytes = shutil.disk_usage(
        PROJECT_DIR
    ).free

    if free_bytes < MINIMUM_FREE_BYTES:
        raise RuntimeError(
            "EXP-022 requires at least "
            f"{MINIMUM_FREE_BYTES:,} free bytes; "
            f"found {free_bytes:,}."
        )

    try:
        import databento
        import pyarrow
    except ImportError as exc:
        raise RuntimeError(
            "EXP-022 requires installed databento "
            "and pyarrow packages."
        ) from exc

    evidence = verify_frozen_evidence()

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
        "free_bytes": int(free_bytes),
        "databento_version": getattr(
            databento,
            "__version__",
            "unknown",
        ),
        "pyarrow_version": getattr(
            pyarrow,
            "__version__",
            "unknown",
        ),
        **evidence,
    }


def load_contract_frames(
    preflight: dict[str, Any],
) -> dict[str, pd.DataFrame]:
    import databento as db
    from exp020_constructor_core import (
        normalise_contract_frame,
    )

    frames: dict[str, pd.DataFrame] = {}
    completed = preflight[
        "completed_by_symbol"
    ]

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
        frames[symbol] = normalise_contract_frame(
            store.to_df(),
            canonical_symbol=symbol,
        )

    total_records = sum(
        len(frame)
        for frame in frames.values()
    )

    if total_records != EXPECTED_RECORD_COUNT:
        raise RuntimeError(
            "Loaded source record count changed: "
            f"{total_records:,}."
        )

    return frames


def write_core_outputs(
    directory: Path,
    construction: dict[str, Any],
) -> dict[str, str]:
    directory.mkdir(
        parents=True,
        exist_ok=False,
    )

    write_csv(
        directory / "roll_ledger.csv",
        construction["ledger"],
        SELECTED_ROLL_LEDGER_FIELDS,
    )
    write_csv(
        directory / "contract_contribution.csv",
        construction["contributions"],
        CONTRIBUTION_FIELDS,
    )
    write_parquet(
        directory / "selected_roll_unadjusted.parquet",
        construction["unadjusted"],
    )
    write_parquet(
        directory
        / "selected_roll_backward_adjusted.parquet",
        construction["adjusted"],
    )

    return dict(
        construction["semantic_hashes"]
    )


def core_output_hashes(
    directory: Path,
) -> dict[str, str]:
    return {
        name: sha256_file(
            directory / name
        )
        for name in CORE_OUTPUT_NAMES
    }


def build_report(
    summary: dict[str, Any],
) -> str:
    counts = summary[
        "selected_transition_counts"
    ]

    lines = [
        "# EXP-022 Selected-Roll Construction",
        "",
        (
            f"**Classification:** "
            f"`{summary['classification']}`"
        ),
        "",
        "## Locked roll schedule",
        "",
        f"- Method: `{SELECTED_METHOD}`",
        (
            "- Effective roll dates: frozen from "
            "EXP-021 without recalculation"
        ),
        (
            "- Volume-driven transitions: "
            f"{counts['volume_driven_transition_count']}"
        ),
        (
            "- Calendar fallbacks: "
            f"{counts['calendar_fallback_count']}"
        ),
        (
            "- Warning fallbacks: "
            f"{counts['warning_calendar_fallback_count']}"
        ),
        (
            "- Clean fallbacks: "
            f"{counts['clean_calendar_fallback_count']}"
        ),
        "",
        "## Constructed representations",
        "",
        (
            "- `selected_roll_unadjusted.parquet`: "
            f"{summary['row_count']:,} rows"
        ),
        (
            "- `selected_roll_backward_adjusted.parquet`: "
            f"{summary['row_count']:,} rows"
        ),
        "",
        "## Scope",
        "",
        "- Databento API calls: 0",
        "- Credentials used: No",
        "- EXP-019 archive modified: No",
        "- EXP-020 outputs modified: No",
        "- EXP-021 outputs modified: No",
        "- Strategy run: No",
        "- Optimisation, MCPT or walk-forward run: No",
        "- Paper or live trading authorised: No",
        "",
        "## Hard checks",
        "",
        "| Check | Passed |",
        "|---|---:|",
    ]

    for name, passed in summary[
        "hard_checks"
    ].items():
        lines.append(
            f"| {name} | {passed} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "Qualification applies only to the "
                "constructed selected-roll dataset."
            ),
            (
                "The roll rule was selected operationally "
                "in EXP-021, not by strategy performance."
            ),
            (
                "This construction does not establish "
                "strategy edge, exchange accuracy or "
                "best-vendor status."
            ),
            "",
        ]
    )

    return "\n".join(lines)


def run_construction() -> dict[str, Any]:
    preflight = repository_preflight()
    source_before = preflight[
        "source_snapshot"
    ]
    exp020_before = preflight[
        "exp020_snapshot"
    ]
    exp021_before = preflight[
        "exp021_snapshot"
    ]
    selected_rows = preflight[
        "selected_evidence"
    ]["selected_rows"]
    selected_counts = preflight[
        "selected_evidence"
    ]["counts"]
    started_at = datetime.now(
        timezone.utc
    ).isoformat()

    try:
        frames = load_contract_frames(
            preflight
        )
        main_build = construct_selected_in_memory(
            frames,
            preflight["contract_plan"],
            selected_rows,
        )
        main_semantic = write_core_outputs(
            PARTIAL_OUTPUT_DIR,
            main_build,
        )
        main_hashes = core_output_hashes(
            PARTIAL_OUTPUT_DIR
        )
        main_checks = dict(
            main_build["checks"]
        )
        row_count = int(
            len(main_build["unadjusted"])
        )
        first_timestamp = (
            main_build["unadjusted"][
                "ts_event"
            ].min().isoformat()
        )
        last_timestamp = (
            main_build["unadjusted"][
                "ts_event"
            ].max().isoformat()
        )
        del main_build
        del frames
        gc.collect()

        verification_frames = (
            load_contract_frames(
                preflight
            )
        )
        verification_build = (
            construct_selected_in_memory(
                verification_frames,
                preflight["contract_plan"],
                selected_rows,
            )
        )
        verification_semantic = (
            write_core_outputs(
                VERIFICATION_OUTPUT_DIR,
                verification_build,
            )
        )
        verification_hashes = (
            core_output_hashes(
                VERIFICATION_OUTPUT_DIR
            )
        )
        independent_match = bool(
            main_semantic
            == verification_semantic
            and main_hashes
            == verification_hashes
        )
        del verification_build
        del verification_frames
        gc.collect()

        source_after = preflight[
            "snapshot_archive_files"
        ](
            preflight["manifest"]
        )
        exp020_after = snapshot_paths(
            preflight["exp020_paths"]
        )
        exp021_after = snapshot_paths(
            preflight["exp021_paths"]
        )
        prior_unchanged = bool(
            source_before == source_after
            and exp020_before == exp020_after
            and exp021_before == exp021_after
        )

        counts_match = (
            selected_counts
            == {
                "transition_count": 65,
                "clean_transition_count": (
                    EXPECTED_CLEAN_TRANSITIONS
                ),
                "volume_driven_transition_count": (
                    EXPECTED_VOLUME_TRANSITIONS
                ),
                "calendar_fallback_count": (
                    EXPECTED_CALENDAR_FALLBACKS
                ),
                "warning_calendar_fallback_count": (
                    EXPECTED_WARNING_FALLBACKS
                ),
                "clean_calendar_fallback_count": (
                    EXPECTED_CLEAN_FALLBACKS
                ),
            }
        )

        timestamps_valid = bool(
            main_checks[
                "timestamps_are_strictly_increasing"
            ]
            and main_checks[
                "constructed_timestamps_are_unique"
            ]
        )

        hard_checks = {
            "frozen_exp021_closure_hash_matches": True,
            "frozen_exp021_output_hashes_match": True,
            "frozen_exp019_archive_hash_matches": True,
            "exactly_66_source_contract_files": (
                len(source_before)
                == EXPECTED_CONTRACT_COUNT
            ),
            "source_and_prior_outputs_remain_read_only": (
                prior_unchanged
            ),
            "selected_method_is_vol_gt_out_2s_e3": (
                all(
                    row["candidate_id"]
                    == SELECTED_METHOD
                    for row in selected_rows
                )
            ),
            "exactly_65_ordered_transitions": (
                main_checks[
                    "exactly_65_ordered_transitions"
                ]
            ),
            "selected_counts_match_40_25_23_2": (
                counts_match
            ),
            "selected_ledger_semantic_hash_matches": (
                preflight[
                    "selected_evidence"
                ]["semantic_sha256"]
                == EXPECTED_SELECTED_EVIDENCE_SEMANTIC_SHA256
            ),
            "all_boundaries_are_inside_locked_overlap": (
                main_checks[
                    "all_boundaries_are_inside_locked_overlap"
                ]
            ),
            "no_effective_boundary_is_after_expiry": (
                main_checks[
                    "no_effective_boundary_is_after_expiry"
                ]
            ),
            "one_boundary_per_adjacent_pair": (
                main_checks[
                    "one_boundary_per_adjacent_pair"
                ]
            ),
            "stitching_boundary_rule_is_exact": (
                main_checks[
                    "stitching_boundary_rule_is_exact"
                ]
            ),
            "stitched_rows_reconcile_to_source": (
                main_checks[
                    "stitched_rows_reconcile_to_source"
                ]
            ),
            "timestamps_are_unique_and_monotonic": (
                timestamps_valid
            ),
            "adjustment_references_exist_and_are_finite": (
                main_checks[
                    "adjustment_references_exist_and_are_finite"
                ]
            ),
            "backward_adjustment_reconciles": (
                main_checks[
                    "backward_adjustment_reconciles"
                ]
            ),
            "adjusted_and_unadjusted_nonprice_fields_match": (
                main_checks[
                    "adjusted_and_unadjusted_nonprice_fields_match"
                ]
            ),
            "independent_rebuild_hashes_match": (
                independent_match
            ),
            "required_outputs_complete_and_no_strategy_or_api": True,
        }

        if len(hard_checks) != 20:
            raise RuntimeError(
                "EXP-022 hard-check count changed."
            )

        classification = final_classification(
            hard_checks
        )
        completed_at = datetime.now(
            timezone.utc
        ).isoformat()

        summary = {
            "experiment_id": "EXP-022",
            "classification": classification,
            "started_at_utc": started_at,
            "completed_at_utc": completed_at,
            "repository": {
                "head": preflight["head"],
                "implementation_commit": (
                    preflight[
                        "implementation_commit"
                    ]
                ),
                "authorization_commit": (
                    preflight[
                        "authorization_commit"
                    ]
                ),
            },
            "selected_method": SELECTED_METHOD,
            "selected_transition_counts": (
                selected_counts
            ),
            "row_count": row_count,
            "first_timestamp_utc": first_timestamp,
            "last_timestamp_utc": last_timestamp,
            "series_count": 2,
            "hard_checks": hard_checks,
            "hard_failure_count": sum(
                not value
                for value in hard_checks.values()
            ),
            "independent_rebuild": True,
            "source_contracts": (
                EXPECTED_CONTRACT_COUNT
            ),
            "source_records": (
                EXPECTED_RECORD_COUNT
            ),
            "databento_api_calls": 0,
            "credentials_used": False,
            "continuous_construction": True,
            "strategy_run": False,
            "strategy_use_authorized": False,
            "paper_trading_authorized": False,
            "live_trading_authorized": False,
            "construction_rerun_authorized": False,
            "semantic_hashes": main_semantic,
            "core_output_hashes": main_hashes,
        }

        atomic_write_json(
            PARTIAL_OUTPUT_DIR
            / "construction_summary.json",
            summary,
        )
        atomic_write_json(
            PARTIAL_OUTPUT_DIR
            / "output_hashes.json",
            {
                "byte_hashes": main_hashes,
                "semantic_hashes": main_semantic,
            },
        )
        atomic_write_text(
            PARTIAL_OUTPUT_DIR / "report.md",
            build_report(summary),
        )
        atomic_write_json(
            PARTIAL_OUTPUT_DIR
            / "CONSTRUCTION_COMPLETE.json",
            {
                **summary,
                "construction_complete": True,
                "required_output_count": len(
                    REQUIRED_OUTPUT_NAMES
                ),
            },
        )

        missing = [
            name
            for name in REQUIRED_OUTPUT_NAMES
            if not (
                PARTIAL_OUTPUT_DIR / name
            ).is_file()
        ]

        if missing:
            raise RuntimeError(
                "EXP-022 required outputs missing: "
                + ", ".join(missing)
            )

        shutil.rmtree(
            VERIFICATION_OUTPUT_DIR
        )
        os.replace(
            PARTIAL_OUTPUT_DIR,
            OUTPUT_DIR,
        )

        print("EXP-022 construction complete.")
        print(
            "Classification:          "
            f"{classification}"
        )
        print(
            "Selected method:         "
            f"{SELECTED_METHOD}"
        )
        print(
            "Series representations:  2"
        )
        print(
            "Rows per series:         "
            f"{row_count:,}"
        )
        print(
            "Volume transitions:      "
            f"{selected_counts['volume_driven_transition_count']}"
        )
        print(
            "Calendar fallbacks:      "
            f"{selected_counts['calendar_fallback_count']}"
        )
        print(
            "Hard checks passed:      "
            f"{sum(hard_checks.values())}/20"
        )
        print("Databento API calls:    0")
        print("Strategy run:           False")
        print("Construction rerun:     Prohibited")

        return summary
    except Exception:
        raise


def print_preflight(
    preflight: dict[str, Any],
) -> None:
    print("EXP-022 construction preflight passed.")
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
    print(
        "Selected method:        "
        + SELECTED_METHOD
    )
    print("Frozen transitions:     65")
    print("Source contracts:       66")
    print("Source records:         6276486")
    print("Databento API calls:    0")
    print("Construction run:       False")
    print("Strategy run:           False")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Protected EXP-022 selected-roll "
            "continuous-series construction."
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
        "--construct",
        action="store_true",
    )
    parser.add_argument(
        "--confirm-one-time-construction",
        action="store_true",
    )
    args = parser.parse_args()

    if args.preflight:
        if args.confirm_one_time_construction:
            parser.error(
                "The construction confirmation flag "
                "cannot accompany --preflight."
            )
        print_preflight(
            repository_preflight()
        )
        return

    if not args.confirm_one_time_construction:
        parser.error(
            "--construct requires "
            "--confirm-one-time-construction."
        )

    run_construction()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(
            f"ERROR: {exc}",
            file=sys.stderr,
        )
        raise SystemExit(1)
