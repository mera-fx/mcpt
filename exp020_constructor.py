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
from typing import Any, Iterable

import pandas as pd

from exp020_constructor_core import (
    CALENDAR_METHOD,
    CONTRIBUTION_FIELDS,
    EXPECTED_CONTRACT_COUNT,
    EXPECTED_RECORD_COUNT,
    EXPECTED_TRANSITION_COUNT,
    KNOWN_PROVIDER_WARNING_CONTRACTS,
    METHOD_COMPARISON_FIELDS,
    PRIMARY_METHOD,
    ROLL_LEDGER_FIELDS,
    SERIES_COLUMNS,
    adjustment_reconciles,
    apply_backward_adjustment,
    build_roll_ledgers,
    contribution_rows,
    ledger_semantic_hash,
    method_comparison_row,
    normalise_contract_frame,
    rows_match_source,
    semantic_frame_hash,
    stitch_series,
    validate_series,
)


PROJECT_DIR = Path(__file__).resolve().parent

LOCKED_PREREGISTRATION_COMMIT = (
    "93776c52806820e137ec02f7fe6382d8981c4500"
)

PREREGISTRATION_PATHS = (
    "exp020_preregistration.py",
    "research/EXP-020_preregistration.md",
)

IMPLEMENTATION_PATHS = (
    "exp020_constructor.py",
    "exp020_constructor_core.py",
    "tests/test_exp020_constructor.py",
    "research/EXP-020_implementation_report.md",
)

AUTHORIZATION_MODULE = (
    "exp020_construction_authorization"
)
AUTHORIZATION_PATH = (
    PROJECT_DIR
    / "exp020_construction_authorization.py"
)
AUTHORIZATION_REPORT_PATH = (
    PROJECT_DIR
    / "research"
    / "EXP-020_construction_authorization.md"
)

ORIGINAL_AUTHORIZATION_COMMIT = (
    "e497b1abf247ed83295caa9378c2a4e6869922b1"
)

PREFLIGHT_CORRECTION_AUTHORIZATION_MODULE = (
    "exp020_preflight_correction_authorization"
)
PREFLIGHT_CORRECTION_AUTHORIZATION_PATH = (
    PROJECT_DIR
    / "exp020_preflight_correction_authorization.py"
)
PREFLIGHT_CORRECTION_AUTHORIZATION_REPORT_PATH = (
    PROJECT_DIR
    / "research"
    / "EXP-020_preflight_correction_authorization.md"
)

PREFLIGHT_CORRECTION_IMPLEMENTATION_PATHS = (
    "exp020_constructor.py",
    "tests/test_exp020_preflight_correction.py",
    "research/EXP-020_preflight_correction_implementation.md",
)

PREFLIGHT_CORRECTION_AUTHORIZATION_PATHS = (
    "exp020_preflight_correction_authorization.py",
    "tests/test_exp020_preflight_correction_authorization.py",
    "research/EXP-020_preflight_correction_authorization.md",
)

ARCHIVE_ROOT = (
    PROJECT_DIR
    / "data"
    / "EXP-019"
    / "exact_contract_archive"
)
RAW_DIR = ARCHIVE_ROOT / "raw"
MANIFEST_PATH = (
    ARCHIVE_ROOT
    / "acquisition_manifest.json"
)
ACQUISITION_COMPLETION_PATH = (
    ARCHIVE_ROOT
    / "ACQUISITION_COMPLETE.json"
)

AUDIT_DIR = (
    PROJECT_DIR
    / "results"
    / "EXP-019"
    / "archive_audit"
)
AUDIT_EVIDENCE_PATHS = {
    "audit_summary_sha256": (
        AUDIT_DIR
        / "exp019_archive_audit_summary.json"
    ),
    "audit_contracts_sha256": (
        AUDIT_DIR
        / "exp019_archive_audit_contracts.csv"
    ),
    "audit_overlaps_sha256": (
        AUDIT_DIR
        / "exp019_archive_audit_overlaps.csv"
    ),
    "audit_report_sha256": (
        AUDIT_DIR / "report.md"
    ),
    "audit_completion_sha256": (
        AUDIT_DIR / "AUDIT_COMPLETE.json"
    ),
}

OUTPUT_PARENT = (
    PROJECT_DIR
    / "results"
    / "EXP-020"
)
OUTPUT_DIR = (
    OUTPUT_PARENT
    / "continuous_series"
)
PARTIAL_OUTPUT_DIR = (
    OUTPUT_PARENT
    / "continuous_series.partial"
)
VERIFICATION_OUTPUT_DIR = (
    OUTPUT_PARENT
    / "continuous_series.verification"
)

EXPECTED_TOTAL_BYTES = 104_491_346
EXPECTED_MANIFEST_SHA256 = (
    "f8fbac395bbe7f9cdafd0187a00c3d77"
    "ee8f6ded31d7ba6870d6ed3c8e3007b3"
)
EXPECTED_ACQUISITION_COMPLETION_SHA256 = (
    "ef8ad499e62284d872edfd480e7aa635"
    "a26340e85ba1d74d98a51ed80f71f935"
)
EXPECTED_ARCHIVE_SHA256 = (
    "225a64dc06cb6bb303fd83d186f2e7d8"
    "1e2a8a8bec44382380c8ccc1b0b6baa3"
)
MINIMUM_FREE_BYTES = 4_000_000_000

CORE_OUTPUT_NAMES = (
    "roll_ledger.csv",
    "contract_contribution.csv",
    "method_comparison.csv",
    "volume_roll_unadjusted.parquet",
    "volume_roll_backward_adjusted.parquet",
    "calendar_roll_unadjusted.parquet",
    "calendar_roll_backward_adjusted.parquet",
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


def archive_digest(
    completed: Iterable[dict[str, Any]],
) -> str:
    payload = [
        {
            "sequence": int(row["sequence"]),
            "canonical_symbol": row[
                "canonical_symbol"
            ],
            "sha256": row["sha256"],
            "size_bytes": int(row["size_bytes"]),
        }
        for row in sorted(
            completed,
            key=lambda item: int(item["sequence"]),
        )
    ]
    encoded = json.dumps(
        payload,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


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
            "EXP-020 Parquet outputs."
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
            b"exp020_schema": (
                b"continuous-series-v1"
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


def snapshot_archive_files(
    manifest: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    snapshot: dict[str, dict[str, Any]] = {}

    for entry in manifest["completed"]:
        path = (
            ARCHIVE_ROOT
            / entry["relative_path"]
        )
        snapshot[entry["canonical_symbol"]] = {
            "relative_path": entry["relative_path"],
            "size_bytes": int(path.stat().st_size),
            "sha256": sha256_file(path),
        }

    return snapshot


def verify_frozen_source_evidence() -> dict[str, Any]:
    from exp019_closure import (
        get_exp019_closure,
        validate_exp019_closure,
    )
    from exp019_preregistration import (
        CONTRACT_PLAN,
        validate_exp019_preregistration,
    )
    from exp020_preregistration import (
        get_exp020_preregistration,
        validate_exp020_preregistration,
    )

    validate_exp019_closure()
    validate_exp019_preregistration()
    validate_exp020_preregistration()

    closure = get_exp019_closure()
    preregistration = (
        get_exp020_preregistration()
    )

    if (
        closure["classification"]
        != (
            "QUALIFIED_WITH_KNOWN_"
            "PROVIDER_CONDITIONS"
        )
        or closure["source"]["contract_count"]
        != EXPECTED_CONTRACT_COUNT
        or closure["audit"]["records_audited"]
        != EXPECTED_RECORD_COUNT
        or closure["audit"]["hard_failure_count"]
        != 0
    ):
        raise RuntimeError(
            "Frozen EXP-019 closure changed."
        )

    frozen = preregistration["frozen_input"]
    if frozen["archive_sha256"] != EXPECTED_ARCHIVE_SHA256:
        raise RuntimeError(
            "EXP-020 frozen archive hash changed."
        )

    if not MANIFEST_PATH.is_file():
        raise RuntimeError(
            "Missing EXP-019 acquisition manifest."
        )
    if not ACQUISITION_COMPLETION_PATH.is_file():
        raise RuntimeError(
            "Missing EXP-019 completion marker."
        )
    if sha256_file(MANIFEST_PATH) != EXPECTED_MANIFEST_SHA256:
        raise RuntimeError(
            "Acquisition manifest hash changed."
        )
    if (
        sha256_file(ACQUISITION_COMPLETION_PATH)
        != EXPECTED_ACQUISITION_COMPLETION_SHA256
    ):
        raise RuntimeError(
            "Acquisition completion hash changed."
        )

    evidence_hashes = frozen["evidence_hashes"]
    for key, path in AUDIT_EVIDENCE_PATHS.items():
        if not path.is_file():
            raise RuntimeError(
                f"Missing audit evidence: {path}"
            )
        if sha256_file(path) != evidence_hashes[key]:
            raise RuntimeError(
                "EXP-019 audit evidence changed: "
                f"{path.name}"
            )

    manifest = json.loads(
        MANIFEST_PATH.read_text(encoding="utf-8")
    )
    completion = json.loads(
        ACQUISITION_COMPLETION_PATH.read_text(
            encoding="utf-8"
        )
    )

    if (
        manifest["experiment_id"] != "EXP-019"
        or manifest["status"] != "COMPLETE"
        or len(manifest["completed"])
        != EXPECTED_CONTRACT_COUNT
    ):
        raise RuntimeError(
            "EXP-019 manifest state changed."
        )

    if (
        completion["archive_sha256"]
        != EXPECTED_ARCHIVE_SHA256
        or archive_digest(manifest["completed"])
        != EXPECTED_ARCHIVE_SHA256
    ):
        raise RuntimeError(
            "EXP-019 archive digest changed."
        )

    completed_by_symbol = {
        row["canonical_symbol"]: row
        for row in manifest["completed"]
    }

    total_bytes = 0
    for contract in CONTRACT_PLAN:
        symbol = contract[0]
        entry = completed_by_symbol.get(symbol)
        if entry is None:
            raise RuntimeError(
                f"Missing manifest contract: {symbol}"
            )
        path = ARCHIVE_ROOT / entry["relative_path"]
        if not path.is_file():
            raise RuntimeError(
                f"Missing raw contract file: {path}"
            )
        size = int(path.stat().st_size)
        total_bytes += size
        if (
            size != int(entry["size_bytes"])
            or sha256_file(path) != entry["sha256"]
        ):
            raise RuntimeError(
                f"Raw contract changed: {symbol}"
            )

    if total_bytes != EXPECTED_TOTAL_BYTES:
        raise RuntimeError(
            "EXP-019 compressed-byte total changed."
        )

    return {
        "manifest": manifest,
        "completed_by_symbol": completed_by_symbol,
        "contract_plan": tuple(CONTRACT_PLAN),
        "source_snapshot": snapshot_archive_files(
            manifest
        ),
    }


def load_authorization() -> dict[str, Any]:
    if not AUTHORIZATION_PATH.is_file():
        raise RuntimeError(
            "EXP-020 construction is not authorized. "
            "The separate authorization file is absent."
        )

    module = importlib.import_module(
        AUTHORIZATION_MODULE
    )
    validator = getattr(
        module,
        "validate_exp020_construction_authorization",
        None,
    )
    getter = getattr(
        module,
        "get_exp020_construction_authorization",
        None,
    )

    if validator is None or getter is None:
        raise RuntimeError(
            "EXP-020 construction authorization "
            "interface is incomplete."
        )

    validator()
    record = getter()

    if (
        record["experiment_id"] != "EXP-020"
        or record["construction_authorized"]
        is not True
        or record["one_time_construction"]
        is not True
        or record["maximum_construction_runs"] != 1
        or record["databento_api_calls"] != 0
        or record["strategy_run_authorized"]
        is not False
    ):
        raise RuntimeError(
            "EXP-020 construction authorization "
            "boundary changed."
        )

    return record


def load_preflight_correction_authorization(
) -> dict[str, Any]:
    if not PREFLIGHT_CORRECTION_AUTHORIZATION_PATH.is_file():
        raise RuntimeError(
            "EXP-020 preflight digest correction is not authorized. "
            "The separate correction authorization file is absent."
        )

    module = importlib.import_module(
        PREFLIGHT_CORRECTION_AUTHORIZATION_MODULE
    )
    validator = getattr(
        module,
        "validate_exp020_preflight_correction_authorization",
        None,
    )
    getter = getattr(
        module,
        "get_exp020_preflight_correction_authorization",
        None,
    )

    if validator is None or getter is None:
        raise RuntimeError(
            "EXP-020 preflight correction authorization "
            "interface is incomplete."
        )

    validator()
    record = getter()

    if (
        record["experiment_id"] != "EXP-020"
        or record["correction_id"]
        != "EXP-020-PREFLIGHT-DIGEST-001"
        or record["correction_authorized"] is not True
        or record["original_authorization_commit"]
        != ORIGINAL_AUTHORIZATION_COMMIT
        or record["archive_digest_protocol"]
        != "EXP-019_INSERTION_ORDER_JSON_V1"
        or record["databento_api_calls"] != 0
        or record["source_archive_modified"] is not False
        or record["construction_run"] is not False
        or record["construction_authorization_unchanged"]
        is not True
        or record["strategy_run_authorized"] is not False
    ):
        raise RuntimeError(
            "EXP-020 preflight correction authorization "
            "boundary changed."
        )

    corrected_commit = record[
        "locked_corrected_implementation_commit"
    ]

    if (
        not isinstance(corrected_commit, str)
        or len(corrected_commit) != 40
    ):
        raise RuntimeError(
            "Corrected implementation commit is invalid."
        )

    return record


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


def commit_that_added(relative_path: str) -> str:
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


def repository_preflight() -> dict[str, Any]:
    if os.environ.get("DATABENTO_API_KEY", "").strip():
        raise RuntimeError(
            "DATABENTO_API_KEY must not be set "
            "for EXP-020."
        )

    if run_git("status", "--porcelain").stdout.strip():
        raise RuntimeError(
            "Repository must be clean before "
            "EXP-020 preflight or construction."
        )

    branch = run_git(
        "branch",
        "--show-current",
    ).stdout.strip()
    if branch != "main":
        raise RuntimeError(
            f"EXP-020 must run on main, found {branch!r}."
        )

    head = run_git("rev-parse", "HEAD").stdout.strip()
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
            "Locked EXP-020 preregistration commit "
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
            "Locked EXP-020 preregistration files changed."
        )

    authorization = load_authorization()
    implementation_commit = authorization[
        "locked_implementation_commit"
    ]

    if run_git(
        "merge-base",
        "--is-ancestor",
        implementation_commit,
        "HEAD",
        check=False,
    ).returncode != 0:
        raise RuntimeError(
            "Locked implementation commit is not "
            "an ancestor of HEAD."
        )

    authorization_commit = commit_that_added(
        "exp020_construction_authorization.py"
    )

    if authorization_commit != ORIGINAL_AUTHORIZATION_COMMIT:
        raise RuntimeError(
            "Original EXP-020 authorization commit changed."
        )

    if run_git(
        "diff",
        "--quiet",
        implementation_commit,
        authorization_commit,
        "--",
        *IMPLEMENTATION_PATHS,
        check=False,
    ).returncode != 0:
        raise RuntimeError(
            "EXP-020 implementation changed between "
            "implementation lock and authorization."
        )

    correction = (
        load_preflight_correction_authorization()
    )
    corrected_implementation_commit = correction[
        "locked_corrected_implementation_commit"
    ]

    if (
        run_git(
            "merge-base",
            "--is-ancestor",
            authorization_commit,
            corrected_implementation_commit,
            check=False,
        ).returncode
        != 0
        or run_git(
            "merge-base",
            "--is-ancestor",
            corrected_implementation_commit,
            "HEAD",
            check=False,
        ).returncode
        != 0
    ):
        raise RuntimeError(
            "Corrected EXP-020 implementation ancestry "
            "is invalid."
        )

    if changed_paths(
        authorization_commit,
        corrected_implementation_commit,
    ) != set(PREFLIGHT_CORRECTION_IMPLEMENTATION_PATHS):
        raise RuntimeError(
            "EXP-020 correction implementation scope changed."
        )

    correction_authorization_commit = commit_that_added(
        "exp020_preflight_correction_authorization.py"
    )

    if (
        run_git(
            "merge-base",
            "--is-ancestor",
            corrected_implementation_commit,
            correction_authorization_commit,
            check=False,
        ).returncode
        != 0
        or run_git(
            "merge-base",
            "--is-ancestor",
            correction_authorization_commit,
            "HEAD",
            check=False,
        ).returncode
        != 0
    ):
        raise RuntimeError(
            "EXP-020 correction authorization ancestry "
            "is invalid."
        )

    if changed_paths(
        corrected_implementation_commit,
        correction_authorization_commit,
    ) != set(PREFLIGHT_CORRECTION_AUTHORIZATION_PATHS):
        raise RuntimeError(
            "EXP-020 correction authorization scope changed."
        )

    protected_paths = (
        *PREREGISTRATION_PATHS,
        *IMPLEMENTATION_PATHS,
        "exp020_construction_authorization.py",
        "research/EXP-020_construction_authorization.md",
        *PREFLIGHT_CORRECTION_IMPLEMENTATION_PATHS,
        *PREFLIGHT_CORRECTION_AUTHORIZATION_PATHS,
    )

    if run_git(
        "diff",
        "--quiet",
        correction_authorization_commit,
        "HEAD",
        "--",
        *protected_paths,
        check=False,
    ).returncode != 0:
        raise RuntimeError(
            "Protected EXP-020 files changed after "
            "preflight correction authorization."
        )

    for path in (
        OUTPUT_DIR,
        PARTIAL_OUTPUT_DIR,
        VERIFICATION_OUTPUT_DIR,
    ):
        if path.exists():
            raise RuntimeError(
                "EXP-020 output already exists. "
                "Refusing to rerun."
            )

    free_bytes = shutil.disk_usage(PROJECT_DIR).free
    if free_bytes < MINIMUM_FREE_BYTES:
        raise RuntimeError(
            "EXP-020 requires at least "
            f"{MINIMUM_FREE_BYTES:,} free bytes; "
            f"found {free_bytes:,}."
        )

    try:
        import databento
        import pyarrow
    except ImportError as exc:
        raise RuntimeError(
            "EXP-020 requires installed databento "
            "and pyarrow packages."
        ) from exc

    source = verify_frozen_source_evidence()

    return {
        "branch": branch,
        "head": head,
        "origin_main": origin_main,
        "implementation_commit": implementation_commit,
        "authorization_commit": authorization_commit,
        "corrected_implementation_commit": (
            corrected_implementation_commit
        ),
        "correction_authorization_commit": (
            correction_authorization_commit
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
        **source,
    }


def load_contract_frames(
    preflight: dict[str, Any],
) -> dict[str, pd.DataFrame]:
    import databento as db

    frames: dict[str, pd.DataFrame] = {}
    completed = preflight["completed_by_symbol"]

    for sequence, contract in enumerate(
        preflight["contract_plan"],
        start=1,
    ):
        symbol = contract[0]
        entry = completed[symbol]
        path = ARCHIVE_ROOT / entry["relative_path"]
        print(
            f"[{sequence:02d}/{EXPECTED_CONTRACT_COUNT}] "
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


def ledger_checks(
    ledger: list[dict[str, Any]],
) -> dict[str, bool]:
    ordered = sorted(
        ledger,
        key=lambda row: int(
            row["transition_sequence"]
        ),
    )
    dates = [
        row["roll_trading_date"]
        for row in ordered
    ]

    return {
        "all_65_adjacent_transitions_resolved": (
            len(ordered) == EXPECTED_TRANSITION_COUNT
        ),
        "roll_boundaries_within_locked_overlap": all(
            int(row["common_overlap_sessions"]) > 0
            for row in ordered
        ),
        "one_ordered_roll_per_adjacent_pair": (
            len(
                {
                    (
                        row["outgoing_contract"],
                        row["incoming_contract"],
                    )
                    for row in ordered
                }
            )
            == EXPECTED_TRANSITION_COUNT
            and dates == sorted(dates)
        ),
        "common_adjustment_reference_exists": all(
            bool(row["reference_timestamp_utc"])
            for row in ordered
        ),
    }


def construct_in_memory(
    preflight: dict[str, Any],
) -> dict[str, Any]:
    frames = load_contract_frames(preflight)
    plan = preflight["contract_plan"]
    volume_ledger, calendar_ledger = (
        build_roll_ledgers(frames, plan)
    )
    expected_contracts = {
        contract[0]
        for contract in plan
    }
    methods: dict[str, dict[str, Any]] = {}

    for method, ledger in (
        (PRIMARY_METHOD, volume_ledger),
        (CALENDAR_METHOD, calendar_ledger),
    ):
        unadjusted = stitch_series(
            frames,
            plan,
            ledger,
            method=method,
        )
        adjusted = apply_backward_adjustment(
            unadjusted,
            ledger,
        )
        checks = validate_series(
            unadjusted,
            adjusted,
            expected_contracts=expected_contracts,
        )
        checks[
            "unadjusted_rows_match_source_ohlcv"
        ] = rows_match_source(
            unadjusted,
            frames,
        )
        checks[
            "adjustment_ledger_reconciles_exactly"
        ] = adjustment_reconciles(
            unadjusted,
            adjusted,
            ledger,
        )
        checks.update(ledger_checks(ledger))

        methods[method] = {
            "ledger": ledger,
            "unadjusted": unadjusted,
            "adjusted": adjusted,
            "checks": checks,
            "contributions": contribution_rows(
                unadjusted,
                adjusted,
                method=method,
            ),
            "comparison": method_comparison_row(
                unadjusted,
                adjusted,
                ledger,
                method=method,
            ),
        }

    return {
        "frames": frames,
        "methods": methods,
    }


def write_core_outputs(
    directory: Path,
    construction: dict[str, Any],
) -> dict[str, str]:
    directory.mkdir(
        parents=True,
        exist_ok=False,
    )

    volume = construction["methods"][PRIMARY_METHOD]
    calendar = construction["methods"][CALENDAR_METHOD]
    roll_rows = volume["ledger"] + calendar["ledger"]
    contribution = (
        volume["contributions"]
        + calendar["contributions"]
    )
    comparisons = [
        volume["comparison"],
        calendar["comparison"],
    ]

    write_csv(
        directory / "roll_ledger.csv",
        roll_rows,
        ROLL_LEDGER_FIELDS,
    )
    write_csv(
        directory / "contract_contribution.csv",
        contribution,
        CONTRIBUTION_FIELDS,
    )
    write_csv(
        directory / "method_comparison.csv",
        comparisons,
        METHOD_COMPARISON_FIELDS,
    )
    write_parquet(
        directory / "volume_roll_unadjusted.parquet",
        volume["unadjusted"],
    )
    write_parquet(
        directory
        / "volume_roll_backward_adjusted.parquet",
        volume["adjusted"],
    )
    write_parquet(
        directory / "calendar_roll_unadjusted.parquet",
        calendar["unadjusted"],
    )
    write_parquet(
        directory
        / "calendar_roll_backward_adjusted.parquet",
        calendar["adjusted"],
    )

    return {
        "roll_ledger_semantic_sha256": (
            ledger_semantic_hash(roll_rows)
        ),
        "volume_roll_unadjusted_semantic_sha256": (
            volume["comparison"][
                "unadjusted_semantic_sha256"
            ]
        ),
        "volume_roll_backward_adjusted_semantic_sha256": (
            volume["comparison"][
                "adjusted_semantic_sha256"
            ]
        ),
        "calendar_roll_unadjusted_semantic_sha256": (
            calendar["comparison"][
                "unadjusted_semantic_sha256"
            ]
        ),
        "calendar_roll_backward_adjusted_semantic_sha256": (
            calendar["comparison"][
                "adjusted_semantic_sha256"
            ]
        ),
    }


def core_output_hashes(
    directory: Path,
) -> dict[str, str]:
    return {
        name: sha256_file(directory / name)
        for name in CORE_OUTPUT_NAMES
    }


def all_method_checks(
    construction: dict[str, Any],
) -> dict[str, bool]:
    methods = construction["methods"]
    names: set[str] = set()
    for result in methods.values():
        names.update(result["checks"])

    return {
        name: all(
            result["checks"].get(name, False)
            for result in methods.values()
        )
        for name in sorted(names)
    }


def final_classification(
    *,
    hard_checks: dict[str, bool],
    fallback_count: int,
) -> str:
    if not all(hard_checks.values()):
        return "NOT_QUALIFIED"
    if fallback_count > 0:
        return (
            "QUALIFIED_WITH_DISCLOSED_"
            "CALENDAR_FALLBACKS"
        )
    return (
        "QUALIFIED_VOLUME_CROSSOVER_"
        "CONTINUOUS_SERIES"
    )


def build_report(summary: dict[str, Any]) -> str:
    lines = [
        "# EXP-020 Continuous-Series Construction",
        "",
        (
            f"**Classification:** "
            f"`{summary['classification']}`"
        ),
        "",
        "## Scope",
        "",
        "- Frozen EXP-019 exact-contract archive only",
        "- Databento API calls: 0",
        "- Credentials used: No",
        "- Source archive modified: No",
        "- Strategy run: No",
        "- Optimisation run: No",
        "- Paper or live trading authorised: No",
        "",
        "## Constructed outputs",
        "",
        (
            "| Method | Rows | Calendar fallbacks | "
            "Warning transitions | Largest missing run |"
        ),
        "|---|---:|---:|---:|---:|",
    ]

    for row in summary["method_comparison"]:
        lines.append(
            "| "
            + str(row["method"])
            + " | "
            + f"{int(row['row_count']):,}"
            + " | "
            + str(row["calendar_fallback_count"])
            + " | "
            + str(row[
                "provider_warning_transition_count"
            ])
            + " | "
            + f"{int(row['largest_missing_minute_run']):,}"
            + " |"
        )

    lines.extend(
        [
            "",
            "## Warning-window treatment",
            "",
            (
                "The frozen EXP-019 closure identifies 16 "
                "provider-warning contract windows but does "
                "not freeze finer session-level warning dates."
            ),
            (
                "EXP-020 therefore excludes the entire common "
                "overlap whenever either contract is one of "
                "those warning windows."
            ),
            (
                "Those transitions cannot trigger a volume "
                "roll and use the locked calendar fallback."
            ),
            "",
            "## Hard checks",
            "",
            "| Check | Passed |",
            "|---|---:|",
        ]
    )

    for name, passed in summary["hard_checks"].items():
        lines.append(f"| {name} | {passed} |")

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "Qualification applies only to the "
                "constructed dataset."
            ),
            (
                "This result does not establish exchange "
                "accuracy, best-vendor status or a strategy edge."
            ),
            (
                "A separately preregistered experiment is "
                "required before strategy research."
            ),
            "",
        ]
    )

    return "\n".join(lines)


def run_construction() -> dict[str, Any]:
    preflight = repository_preflight()
    source_before = preflight["source_snapshot"]
    started_at = datetime.now(timezone.utc).isoformat()

    try:
        main_build = construct_in_memory(preflight)
        main_semantic = write_core_outputs(
            PARTIAL_OUTPUT_DIR,
            main_build,
        )
        main_hashes = core_output_hashes(
            PARTIAL_OUTPUT_DIR
        )
        main_checks = all_method_checks(main_build)
        main_comparison = [
            main_build["methods"][PRIMARY_METHOD][
                "comparison"
            ],
            main_build["methods"][CALENDAR_METHOD][
                "comparison"
            ],
        ]
        del main_build
        gc.collect()

        verification_build = construct_in_memory(
            preflight
        )
        verification_semantic = write_core_outputs(
            VERIFICATION_OUTPUT_DIR,
            verification_build,
        )
        verification_hashes = core_output_hashes(
            VERIFICATION_OUTPUT_DIR
        )
        independent_match = bool(
            main_semantic == verification_semantic
            and main_hashes == verification_hashes
        )
        del verification_build
        gc.collect()

        source_after = snapshot_archive_files(
            preflight["manifest"]
        )
        source_unchanged = (
            source_before == source_after
        )

        hard_checks = {
            "frozen_exp019_evidence_hashes_match": True,
            "exactly_66_source_contract_files": (
                len(source_before)
                == EXPECTED_CONTRACT_COUNT
            ),
            "all_source_files_remain_read_only": (
                source_unchanged
            ),
            "all_65_adjacent_transitions_resolved": (
                main_checks[
                    "all_65_adjacent_transitions_resolved"
                ]
            ),
            "roll_boundaries_within_locked_overlap": (
                main_checks[
                    "roll_boundaries_within_locked_overlap"
                ]
            ),
            "one_ordered_roll_per_adjacent_pair": (
                main_checks[
                    "one_ordered_roll_per_adjacent_pair"
                ]
            ),
            "common_adjustment_reference_exists": (
                main_checks[
                    "common_adjustment_reference_exists"
                ]
            ),
            "constructed_series_is_nonempty": (
                main_checks[
                    "constructed_series_is_nonempty"
                ]
            ),
            "timestamps_are_strictly_increasing": (
                main_checks[
                    "timestamps_are_strictly_increasing"
                ]
            ),
            "constructed_timestamps_are_unique": (
                main_checks[
                    "constructed_timestamps_are_unique"
                ]
            ),
            "source_contract_identity_is_complete": (
                main_checks[
                    "source_contract_identity_is_complete"
                ]
            ),
            "unadjusted_rows_match_source_ohlcv": (
                main_checks[
                    "unadjusted_rows_match_source_ohlcv"
                ]
            ),
            "all_ohlcv_values_are_finite": (
                main_checks[
                    "all_ohlcv_values_are_finite"
                ]
            ),
            "unadjusted_ohlc_invariants_hold": (
                main_checks[
                    "unadjusted_ohlc_invariants_hold"
                ]
            ),
            "adjusted_ohlc_invariants_hold": (
                main_checks[
                    "adjusted_ohlc_invariants_hold"
                ]
            ),
            "volume_is_nonnegative": (
                main_checks["volume_is_nonnegative"]
            ),
            "unadjusted_prices_are_quarter_tick_aligned": (
                main_checks[
                    "unadjusted_prices_are_quarter_tick_aligned"
                ]
            ),
            "adjustments_are_quarter_tick_aligned": (
                main_checks[
                    "adjustments_are_quarter_tick_aligned"
                ]
            ),
            "adjustment_ledger_reconciles_exactly": (
                main_checks[
                    "adjustment_ledger_reconciles_exactly"
                ]
            ),
            "independent_rebuild_hashes_match": (
                independent_match
            ),
        }

        if len(hard_checks) != 20:
            raise RuntimeError(
                "EXP-020 hard-check count changed."
            )

        fallback_count = int(
            main_comparison[0][
                "calendar_fallback_count"
            ]
        )
        classification = final_classification(
            hard_checks=hard_checks,
            fallback_count=fallback_count,
        )
        completed_at = datetime.now(
            timezone.utc
        ).isoformat()

        summary = {
            "schema_version": 1,
            "experiment_id": "EXP-020",
            "classification": classification,
            "started_at_utc": started_at,
            "completed_at_utc": completed_at,
            "repository": {
                "head": preflight["head"],
                "implementation_commit": preflight[
                    "implementation_commit"
                ],
                "authorization_commit": preflight[
                    "authorization_commit"
                ],
                "corrected_implementation_commit": preflight[
                    "corrected_implementation_commit"
                ],
                "correction_authorization_commit": preflight[
                    "correction_authorization_commit"
                ],
            },
            "source": {
                "experiment_id": "EXP-019",
                "contract_count": EXPECTED_CONTRACT_COUNT,
                "record_count": EXPECTED_RECORD_COUNT,
                "archive_sha256": EXPECTED_ARCHIVE_SHA256,
                "known_provider_warning_windows": len(
                    KNOWN_PROVIDER_WARNING_CONTRACTS
                ),
                "archive_modified": not source_unchanged,
            },
            "construction": {
                "primary_method": PRIMARY_METHOD,
                "benchmark_method": CALENDAR_METHOD,
                "series_count": 4,
                "transition_count_per_method": (
                    EXPECTED_TRANSITION_COUNT
                ),
                "independent_rebuild": True,
                "strategy_run": False,
                "databento_api_calls": 0,
            },
            "method_comparison": main_comparison,
            "hard_checks": hard_checks,
            "semantic_hashes": main_semantic,
            "core_output_sha256": main_hashes,
            "interpretation": {
                "dataset_qualification_only": True,
                "exchange_accuracy_verified": False,
                "best_vendor_selected": False,
                "strategy_edge_tested": False,
                "strategy_use_authorized": False,
                "paper_trading_authorized": False,
                "live_trading_authorized": False,
            },
        }

        atomic_write_json(
            PARTIAL_OUTPUT_DIR
            / "construction_summary.json",
            summary,
        )
        atomic_write_text(
            PARTIAL_OUTPUT_DIR / "report.md",
            build_report(summary),
        )

        shutil.rmtree(VERIFICATION_OUTPUT_DIR)

        output_hashes = {
            path.name: sha256_file(path)
            for path in sorted(
                PARTIAL_OUTPUT_DIR.iterdir()
            )
            if path.is_file()
        }
        atomic_write_json(
            PARTIAL_OUTPUT_DIR / "output_hashes.json",
            {
                "schema_version": 1,
                "experiment_id": "EXP-020",
                "files": output_hashes,
            },
        )
        output_hashes["output_hashes.json"] = (
            sha256_file(
                PARTIAL_OUTPUT_DIR
                / "output_hashes.json"
            )
        )

        completion = {
            "schema_version": 1,
            "experiment_id": "EXP-020",
            "classification": classification,
            "completed_at_utc": completed_at,
            "hard_failure_count": sum(
                not value
                for value in hard_checks.values()
            ),
            "calendar_fallback_count": fallback_count,
            "output_hashes": output_hashes,
            "construction_complete": True,
            "construction_rerun_authorized": False,
            "strategy_run": False,
            "strategy_use_authorized": False,
            "paper_trading_authorized": False,
            "live_trading_authorized": False,
        }
        atomic_write_json(
            PARTIAL_OUTPUT_DIR
            / "CONSTRUCTION_COMPLETE.json",
            completion,
        )

        if OUTPUT_DIR.exists():
            raise RuntimeError(
                "Final EXP-020 output appeared during "
                "construction."
            )
        os.replace(PARTIAL_OUTPUT_DIR, OUTPUT_DIR)
        return summary

    except Exception:
        if VERIFICATION_OUTPUT_DIR.exists():
            print(
                "Verification output retained for diagnosis.",
                file=sys.stderr,
            )
        if PARTIAL_OUTPUT_DIR.exists():
            print(
                "Partial output retained for diagnosis.",
                file=sys.stderr,
            )
        raise


def print_preflight(
    preflight: dict[str, Any],
) -> None:
    print("EXP-020 construction preflight passed.")
    print("Repository HEAD:        " + preflight["head"])
    print(
        "Implementation commit:  "
        + preflight["implementation_commit"]
    )
    print(
        "Authorization commit:   "
        + preflight["authorization_commit"]
    )
    print(
        "Corrected implementation: "
        + preflight["corrected_implementation_commit"]
    )
    print(
        "Correction authorization: "
        + preflight["correction_authorization_commit"]
    )
    print(
        "Source contracts:       "
        + str(len(preflight["source_snapshot"]))
    )
    print(
        "Source records:         "
        + str(EXPECTED_RECORD_COUNT)
    )
    print(
        "Free bytes:             "
        + str(preflight["free_bytes"])
    )
    print("Databento API calls:    0")
    print("Construction run:       False")
    print("Strategy run:           False")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Protected EXP-020 local "
            "continuous-series constructor."
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
        print_preflight(repository_preflight())
        return

    if not args.confirm_one_time_construction:
        raise RuntimeError(
            "--construct requires "
            "--confirm-one-time-construction."
        )

    summary = run_construction()
    print("EXP-020 construction complete.")
    print(
        "Classification:         "
        + summary["classification"]
    )
    print(
        "Source contracts:       "
        + str(EXPECTED_CONTRACT_COUNT)
    )
    print(
        "Source records:         "
        + str(EXPECTED_RECORD_COUNT)
    )
    print(
        "Hard checks passed:     "
        + str(sum(summary["hard_checks"].values()))
        + "/20"
    )
    print("Databento API calls:    0")
    print("Strategy run:           False")
    print("Construction rerun:     Prohibited")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(
            f"ERROR: {exc}",
            file=sys.stderr,
        )
        raise SystemExit(1)
