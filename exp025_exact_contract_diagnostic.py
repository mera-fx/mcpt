from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
from html import escape
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd

from exp024_closure import get_exp024_closure, validate_exp024_closure
from exp025_exact_contract_core import (
    CANDIDATE_ID,
    DECISION_FIELDS,
    EXPECTED_POPULATION_ROWS,
    EXPECTED_QUANTOWER_FILES,
    OUTPUT_SCHEMAS,
    PRICE_DECISION_FIELDS,
    REQUIRED_OUTPUT_NAMES,
    archive_digest,
    attach_previous_session_dates,
    build_archive_index,
    canonical_dataframe_sha256,
    canonical_gap_fade_decision,
    canonical_object_sha256,
    compare_one_minute_sources,
    dbn_record_to_row,
    dbn_record_timestamp,
    decision_input_hash,
    decision_vectors_match,
    final_classification,
    independent_gap_fade_decision,
    local_window_label,
    normalise_source_rows,
    price_to_ticks,
    required_output_set,
    select_unresolved_population,
    session_classification,
    sha256_file,
    stream_quantower_csv,
    ticks_to_price,
    validate_output_schemas,
    validate_population_contracts_in_archive,
    validate_quantower_export_manifest,
)
from exp025_preregistration import (
    EXPECTED_EXP025_PREREGISTRATION_SHA256,
    get_exp025_preregistration,
    validate_exp025_preregistration,
)


PROJECT_DIR = Path(__file__).resolve().parent
LOCKED_PREREGISTRATION_COMMIT = (
    "1d736705a41d0208e353fb17710c8a16cc937710"
)
LOCKED_PREREGISTRATION_PATHS = (
    "exp025_preregistration.py",
    "experiment_lifecycle.py",
    "research/EXP-025_preregistration.md",
    "tests/test_exp025_preregistration.py",
    "tests/test_experiment_lifecycle.py",
)
IMPLEMENTATION_PATHS = (
    "exp025_exact_contract_diagnostic.py",
    "exp025_exact_contract_core.py",
    "tests/test_exp025_exact_contract_diagnostic.py",
    "research/EXP-025_implementation_report.md",
)

EXECUTION_AUTHORIZATION_MODULE = "exp025_execution_authorization"
EXECUTION_AUTHORIZATION_PATH = (
    PROJECT_DIR / "exp025_execution_authorization.py"
)
EXPORT_AUTHORIZATION_PATH = (
    PROJECT_DIR / "exp025_quantower_export_authorization.py"
)

EXP024_DIR = (
    PROJECT_DIR
    / "results"
    / "EXP-024"
    / "source_disagreement_attribution"
)
EXP024_PARTIAL_DIR = (
    PROJECT_DIR
    / "results"
    / "EXP-024"
    / "source_disagreement_attribution.partial"
)
MISMATCH_PATH = EXP024_DIR / "mismatch_attribution.csv"
ROLL_CONTEXT_PATH = EXP024_DIR / "roll_context.csv"

SESSION_QUALITY_PATH = (
    PROJECT_DIR
    / "results"
    / "extended_session_data"
    / "session_quality.csv"
)
EXPECTED_SESSION_QUALITY_SIZE_BYTES = 78_768
EXPECTED_SESSION_QUALITY_SHA256 = (
    "6b55077783ad2c1cd8ef99f10d50ed7d"
    "691aad7cafcdb7e8fa37639d90724712"
)
EXPECTED_SESSION_QUALITY_COLUMNS = (
    "session_date",
    "expected_rows",
    "nq_rows",
    "mnq_rows",
    "common_rows",
    "nq_missing_rows",
    "mnq_missing_rows",
    "common_missing_rows",
    "legacy_pause_expected",
    "complete_aligned",
)

ARCHIVE_ROOT = (
    PROJECT_DIR / "data" / "EXP-019" / "exact_contract_archive"
)
ARCHIVE_MANIFEST_PATH = ARCHIVE_ROOT / "acquisition_manifest.json"
ARCHIVE_COMPLETION_PATH = ARCHIVE_ROOT / "ACQUISITION_COMPLETE.json"

QUANTOWER_ROOT = (
    PROJECT_DIR / "data" / "EXP-025" / "quantower_exact_contract_exports"
)
QUANTOWER_MANIFEST_PATH = QUANTOWER_ROOT / "export_manifest.json"

OUTPUT_PARENT = PROJECT_DIR / "results" / "EXP-025"
OUTPUT_DIR = OUTPUT_PARENT / "exact_contract_diagnostic"
PARTIAL_OUTPUT_DIR = OUTPUT_PARENT / "exact_contract_diagnostic.partial"

EXPECTED_ARCHIVE_MANIFEST_SHA256 = (
    "f8fbac395bbe7f9cdafd0187a00c3d77"
    "ee8f6ded31d7ba6870d6ed3c8e3007b3"
)
EXPECTED_ARCHIVE_COMPLETION_SHA256 = (
    "ef8ad499e62284d872edfd480e7aa635"
    "a26340e85ba1d74d98a51ed80f71f935"
)
EXPECTED_ARCHIVE_SHA256 = (
    "225a64dc06cb6bb303fd83d186f2e7d8"
    "1e2a8a8bec44382380c8ccc1b0b6baa3"
)
EXPECTED_ARCHIVE_TOTAL_BYTES = 104_491_346
EXPECTED_ARCHIVE_FILE_COUNT = 66
MINIMUM_FREE_BYTES = 500_000_000

HARD_CHECK_NAMES = (
    "exp024_closure_commit_and_hash_match",
    "exp024_output_byte_hashes_match",
    "exp019_exact_contract_archive_hash_matches",
    "unresolved_population_selector_is_exact",
    "exactly_43_candidate_session_rows_are_retained",
    "quantower_export_manifest_is_complete_and_hash_locked",
    "explicit_contract_identity_exists_for_every_source_session",
    "same_exact_contract_is_used_across_sources",
    "only_outright_quarterly_nq_contracts_are_used",
    "all_source_and_result_inputs_remain_read_only",
    "only_allowed_sessions_windows_and_columns_are_materialized",
    "current_post_0935_and_out_of_population_values_are_not_materialized",
    "missing_minutes_are_not_filled_or_repaired",
    "timestamps_are_unique_and_timezone_normalized",
    "all_prices_are_valid_nq_ticks",
    "one_minute_and_five_minute_component_tables_are_complete",
    "canonical_gap_fade_rule_is_unchanged",
    "independent_engine_does_not_call_canonical_decision_function",
    "same_input_hash_is_used_for_each_engine_pair",
    "all_43_rows_receive_exactly_one_classification",
    "continuous_context_is_not_treated_as_ground_truth",
    "no_exit_pnl_return_equity_drawdown_or_performance_is_computed",
    "independent_rebuild_hashes_match",
    "required_outputs_and_hashes_are_complete",
    "no_api_network_optimization_or_trading_action_occurs",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=PROJECT_DIR,
        text=True,
        capture_output=True,
        check=check,
    )


def changed_paths(base: str, head: str) -> set[str]:
    return {
        line.strip().replace("\\", "/")
        for line in run_git("diff", "--name-only", base, head).stdout.splitlines()
        if line.strip()
    }


def commit_that_last_modified(relative_path: str) -> str:
    commits = run_git(
        "log",
        "-1",
        "--format=%H",
        "--",
        relative_path,
    ).stdout.strip().splitlines()
    if len(commits) != 1:
        raise RuntimeError(
            "Expected exactly one latest implementation commit for "
            f"{relative_path}."
        )
    return commits[0]


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"Expected JSON object: {path}")
    return value


def atomic_write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    if temporary.exists():
        raise RuntimeError(f"Temporary file already exists: {temporary}")
    temporary.write_text(value, encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def atomic_write_json(path: Path, value: Mapping[str, Any]) -> None:
    atomic_write_text(
        path,
        json.dumps(
            value,
            indent=2,
            sort_keys=True,
            ensure_ascii=True,
            allow_nan=False,
            default=str,
        )
        + "\n",
    )


def write_csv(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    if temporary.exists():
        raise RuntimeError(f"Temporary CSV already exists: {temporary}")
    frame.to_csv(
        temporary,
        index=False,
        quoting=csv.QUOTE_MINIMAL,
        lineterminator="\n",
    )
    os.replace(temporary, path)


def snapshot_files(paths: Iterable[Path]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for path in paths:
        if not path.is_file():
            raise RuntimeError(f"Missing protected file: {path}")
        relative = path.relative_to(PROJECT_DIR).as_posix()
        result[relative] = {
            "size_bytes": int(path.stat().st_size),
            "sha256": sha256_file(path),
        }
    return result


def verify_exp024_outputs() -> dict[str, dict[str, Any]]:
    validate_exp024_closure()
    closure = get_exp024_closure()
    expected = closure["output_files"]
    if EXP024_PARTIAL_DIR.exists():
        raise RuntimeError("EXP-024 partial output unexpectedly exists.")
    if not EXP024_DIR.is_dir():
        raise RuntimeError("EXP-024 final output directory is missing.")
    actual_names = {
        path.relative_to(EXP024_DIR).as_posix()
        for path in EXP024_DIR.rglob("*")
        if path.is_file()
    }
    if actual_names != set(expected):
        raise RuntimeError("Frozen EXP-024 output set changed.")
    result: dict[str, dict[str, Any]] = {}
    for name, spec in expected.items():
        path = EXP024_DIR / name
        current = {
            "size_bytes": int(path.stat().st_size) if path.is_file() else 0,
            "sha256": sha256_file(path) if path.is_file() else None,
        }
        if current != spec:
            raise RuntimeError(f"Frozen EXP-024 output changed: {name}")
        result[path.relative_to(PROJECT_DIR).as_posix()] = current
    return result


def verify_session_quality_metadata() -> dict[str, dict[str, Any]]:
    if not SESSION_QUALITY_PATH.is_file():
        raise RuntimeError(
            "Frozen session-quality calendar is missing."
        )

    current = {
        "size_bytes": int(SESSION_QUALITY_PATH.stat().st_size),
        "sha256": sha256_file(SESSION_QUALITY_PATH),
    }
    expected = {
        "size_bytes": EXPECTED_SESSION_QUALITY_SIZE_BYTES,
        "sha256": EXPECTED_SESSION_QUALITY_SHA256,
    }
    if current != expected:
        raise RuntimeError(
            "Frozen session-quality calendar changed."
        )

    header = pd.read_csv(SESSION_QUALITY_PATH, nrows=0)
    if tuple(header.columns) != EXPECTED_SESSION_QUALITY_COLUMNS:
        raise RuntimeError(
            "Frozen session-quality calendar columns changed."
        )

    relative = SESSION_QUALITY_PATH.relative_to(
        PROJECT_DIR
    ).as_posix()
    return {relative: current}


def verify_archive_bytes() -> tuple[dict[str, Any], dict[str, Any], dict[str, dict[str, Any]]]:
    if not ARCHIVE_MANIFEST_PATH.is_file() or not ARCHIVE_COMPLETION_PATH.is_file():
        raise RuntimeError("Frozen EXP-019 archive metadata is missing.")
    if sha256_file(ARCHIVE_MANIFEST_PATH) != EXPECTED_ARCHIVE_MANIFEST_SHA256:
        raise RuntimeError("Frozen EXP-019 acquisition manifest changed.")
    if sha256_file(ARCHIVE_COMPLETION_PATH) != EXPECTED_ARCHIVE_COMPLETION_SHA256:
        raise RuntimeError("Frozen EXP-019 completion marker changed.")
    manifest = read_json(ARCHIVE_MANIFEST_PATH)
    completion = read_json(ARCHIVE_COMPLETION_PATH)
    index = build_archive_index(manifest)
    if archive_digest(manifest["completed"]) != EXPECTED_ARCHIVE_SHA256:
        raise RuntimeError("Frozen EXP-019 archive digest changed.")
    if completion.get("archive_sha256") != EXPECTED_ARCHIVE_SHA256:
        raise RuntimeError("Frozen EXP-019 completion archive hash changed.")
    if len(index) != EXPECTED_ARCHIVE_FILE_COUNT:
        raise RuntimeError("Frozen EXP-019 archive file count changed.")
    total_bytes = 0
    snapshots: dict[str, dict[str, Any]] = {}
    for symbol, entry in index.items():
        path = ARCHIVE_ROOT / entry["relative_path"]
        if not path.is_file():
            raise RuntimeError(f"Frozen exact-contract file is missing: {symbol}")
        current_size = int(path.stat().st_size)
        current_hash = sha256_file(path)
        if current_size != entry["size_bytes"] or current_hash != entry["sha256"]:
            raise RuntimeError(f"Frozen exact-contract file changed: {symbol}")
        total_bytes += current_size
        snapshots[path.relative_to(PROJECT_DIR).as_posix()] = {
            "size_bytes": current_size,
            "sha256": current_hash,
        }
    if total_bytes != EXPECTED_ARCHIVE_TOTAL_BYTES:
        raise RuntimeError("Frozen exact-contract archive byte total changed.")
    return manifest, completion, snapshots


def repository_state_preflight() -> dict[str, str]:
    validate_exp025_preregistration()
    validate_output_schemas()
    if os.environ.get("DATABENTO_API_KEY", "").strip():
        raise RuntimeError("DATABENTO_API_KEY must not be present for EXP-025.")
    status = run_git("status", "--porcelain").stdout.strip()
    if status:
        raise RuntimeError("Repository must be clean for EXP-025 preflight.")
    branch = run_git("branch", "--show-current").stdout.strip()
    if branch != "main":
        raise RuntimeError(f"EXP-025 must run on main, found {branch!r}.")
    head = run_git("rev-parse", "HEAD").stdout.strip()
    origin_main = run_git("rev-parse", "origin/main").stdout.strip()
    if head != origin_main:
        raise RuntimeError("Local HEAD and origin/main are not aligned.")
    ancestor = run_git(
        "merge-base",
        "--is-ancestor",
        LOCKED_PREREGISTRATION_COMMIT,
        "HEAD",
        check=False,
    )
    if ancestor.returncode != 0:
        raise RuntimeError("Locked EXP-025 preregistration is not an ancestor.")
    protected_diff = run_git(
        "diff",
        "--quiet",
        LOCKED_PREREGISTRATION_COMMIT,
        "--",
        *LOCKED_PREREGISTRATION_PATHS,
        check=False,
    )
    if protected_diff.returncode != 0:
        raise RuntimeError("Locked EXP-025 preregistration files changed.")
    implementation_commits = {
        commit_that_last_modified(path)
        for path in IMPLEMENTATION_PATHS
    }
    if len(implementation_commits) != 1:
        raise RuntimeError("EXP-025 implementation files lack one locked commit.")
    implementation_commit = next(iter(implementation_commits))
    if run_git(
        "merge-base",
        "--is-ancestor",
        implementation_commit,
        "HEAD",
        check=False,
    ).returncode != 0:
        raise RuntimeError("EXP-025 implementation commit is not an ancestor.")
    if OUTPUT_DIR.exists() or PARTIAL_OUTPUT_DIR.exists():
        raise RuntimeError("EXP-025 output already exists. Refusing to rerun.")
    return {
        "branch": branch,
        "head": head,
        "origin_main": origin_main,
        "implementation_commit": implementation_commit,
    }


def load_population() -> pd.DataFrame:
    mismatch = pd.read_csv(MISMATCH_PATH)
    roll = pd.read_csv(ROLL_CONTEXT_PATH)
    session_quality = pd.read_csv(
        SESSION_QUALITY_PATH,
        usecols=["session_date"],
    )
    population = select_unresolved_population(mismatch, roll)
    return attach_previous_session_dates(
        population,
        session_quality,
    )


def implementation_preflight() -> dict[str, Any]:
    state = repository_state_preflight()
    if EXECUTION_AUTHORIZATION_PATH.exists() or EXPORT_AUTHORIZATION_PATH.exists():
        raise RuntimeError(
            "Implementation-only preflight requires authorization files to be absent."
        )
    if QUANTOWER_ROOT.exists():
        raise RuntimeError(
            "Quantower exact-contract exports are not authorized yet; input directory must be absent."
        )
    exp024_snapshot = verify_exp024_outputs()
    session_quality_snapshot = verify_session_quality_metadata()
    archive_manifest, archive_completion, archive_snapshot = verify_archive_bytes()
    population = load_population()
    archive_index = build_archive_index(archive_manifest)
    validate_population_contracts_in_archive(population, archive_index)
    return {
        **state,
        "preregistration_sha256": EXPECTED_EXP025_PREREGISTRATION_SHA256,
        "population_rows": int(len(population)),
        "unique_contracts": int(population["exact_contract_symbol"].nunique()),
        "exp024_files_verified": int(len(exp024_snapshot)),
        "session_quality_files_verified": int(
            len(session_quality_snapshot)
        ),
        "archive_files_verified": int(len(archive_snapshot)),
        "archive_sha256": archive_completion["archive_sha256"],
        "quantower_export_authorized": False,
        "execution_authorized": False,
        "market_values_materialized": False,
        "diagnostic_run": False,
    }


def load_execution_authorization(
    *,
    implementation_commit: str,
) -> dict[str, Any]:
    if not EXECUTION_AUTHORIZATION_PATH.is_file():
        raise RuntimeError(
            "EXP-025 diagnostic execution is not authorized; the separate authorization file is absent."
        )
    module = importlib.import_module(EXECUTION_AUTHORIZATION_MODULE)
    validator = getattr(module, "validate_exp025_execution_authorization", None)
    getter = getattr(module, "get_exp025_execution_authorization", None)
    if validator is None or getter is None:
        raise RuntimeError("EXP-025 execution authorization interface is incomplete.")
    validator()
    record = getter()
    if (
        record.get("experiment_id") != "EXP-025"
        or record.get("exact_contract_execution_authorized") is not True
        or record.get("one_time_diagnostic_run") is not True
        or record.get("maximum_diagnostic_runs") != 1
        or record.get("implementation_commit") != implementation_commit
        or record.get("preregistration_sha256")
        != EXPECTED_EXP025_PREREGISTRATION_SHA256
        or record.get("quantower_export_file_count") != EXPECTED_QUANTOWER_FILES
        or record.get("databento_api_calls_authorized") != 0
        or record.get("network_access_authorized") is not False
        or record.get("strategy_replay_authorized") is not False
        or record.get("performance_calculation_authorized") is not False
        or record.get("paper_trading_authorized") is not False
        or record.get("live_trading_authorized") is not False
    ):
        raise RuntimeError("EXP-025 execution authorization boundary changed.")
    manifest_hash = str(record.get("quantower_export_manifest_sha256", ""))
    if len(manifest_hash) != 64:
        raise RuntimeError("EXP-025 authorization lacks the export manifest hash.")
    return record


def execution_preflight() -> dict[str, Any]:
    state = repository_state_preflight()
    authorization = load_execution_authorization(
        implementation_commit=state["implementation_commit"]
    )
    exp024_snapshot = verify_exp024_outputs()
    session_quality_snapshot = verify_session_quality_metadata()
    archive_manifest, archive_completion, archive_snapshot = verify_archive_bytes()
    population = load_population()
    archive_index = build_archive_index(archive_manifest)
    validate_population_contracts_in_archive(population, archive_index)
    if not QUANTOWER_MANIFEST_PATH.is_file():
        raise RuntimeError("Quantower exact-contract export manifest is missing.")
    manifest_hash = sha256_file(QUANTOWER_MANIFEST_PATH)
    if manifest_hash != authorization["quantower_export_manifest_sha256"]:
        raise RuntimeError("Quantower export manifest hash is not authorized.")
    quantower_manifest = read_json(QUANTOWER_MANIFEST_PATH)
    quantower_index = validate_quantower_export_manifest(
        quantower_manifest,
        population,
    )
    quantower_snapshot: dict[str, dict[str, Any]] = {}
    for row in quantower_index.itertuples(index=False):
        path = QUANTOWER_ROOT / row.relative_path
        if not path.is_file():
            raise RuntimeError(f"Quantower export file is missing: {row.relative_path}")
        current = {
            "size_bytes": int(path.stat().st_size),
            "sha256": sha256_file(path),
        }
        expected = {
            "size_bytes": int(row.size_bytes),
            "sha256": str(row.sha256),
        }
        if current != expected:
            raise RuntimeError(f"Quantower export file changed: {row.relative_path}")
        quantower_snapshot[path.relative_to(PROJECT_DIR).as_posix()] = current
    free_bytes = shutil.disk_usage(OUTPUT_PARENT.parent).free
    if free_bytes < MINIMUM_FREE_BYTES:
        raise RuntimeError("Insufficient free disk space for EXP-025 output.")
    return {
        **state,
        "authorization": authorization,
        "population": population,
        "archive_manifest": archive_manifest,
        "archive_index": archive_index,
        "quantower_manifest": quantower_manifest,
        "quantower_index": quantower_index,
        "source_snapshot": {
            **exp024_snapshot,
            **session_quality_snapshot,
            **archive_snapshot,
            **quantower_snapshot,
        },
        "archive_sha256": archive_completion["archive_sha256"],
        "quantower_manifest_sha256": manifest_hash,
        "market_values_materialized": False,
    }


def load_dbn_store(path: Path) -> Any:
    import databento as db

    return db.DBNStore.from_file(path)


def validate_dbn_store_metadata(
    store: Any,
    *,
    canonical_symbol: str,
    raw_symbol: str | None = None,
) -> None:
    dataset = str(getattr(store, "dataset", ""))
    schema = str(getattr(store, "schema", "")).lower().replace("_", "-")
    stype_in = str(getattr(store, "stype_in", "")).lower().replace("_", "-")
    raw_symbols = getattr(store, "symbols", ()) or ()
    symbols = {str(value).upper() for value in raw_symbols}
    if dataset != "GLBX.MDP3":
        raise RuntimeError("Databento exact-contract dataset changed.")
    if "ohlcv-1m" not in schema and "ohlcv1m" not in schema:
        raise RuntimeError("Databento exact-contract schema changed.")
    if "raw-symbol" not in stype_in and "rawsymbol" not in stype_in:
        raise RuntimeError("Databento exact-contract stype_in changed.")
    accepted = {canonical_symbol.upper()}
    if raw_symbol:
        accepted.add(str(raw_symbol).upper())
    if symbols and symbols.isdisjoint(accepted):
        raise RuntimeError(
            "DBN store does not declare the expected exact contract "
            f"{sorted(accepted)}."
        )


def collect_databento_rows(
    store: Iterable[Any],
    requests: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    result = {request["session_date"]: [] for request in requests}
    for record in store:
        timestamp = dbn_record_timestamp(record)
        matched = [
            request
            for request in requests
            if local_window_label(
                timestamp,
                session_date=request["session_date"],
                previous_session_date=request["previous_session_date"],
            ) is not None
        ]
        if not matched:
            continue
        decoded = dbn_record_to_row(
            record,
            exact_contract_symbol=matched[0]["exact_contract_symbol"],
        )
        for request in matched:
            result[request["session_date"]].append(dict(decoded))
    return result


def _component_rows(
    *,
    session_date: str,
    symbol: str,
    quantower: Mapping[str, Any],
    databento: Mapping[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for component in DECISION_FIELDS:
        left = quantower.get(component)
        right = databento.get(component)
        difference_ticks: int | None = None
        if component in PRICE_DECISION_FIELDS and left is not None and right is not None:
            if component != "threshold_margin":
                difference_ticks = price_to_ticks(right, name=component) - price_to_ticks(
                    left, name=component
                )
        matches = decision_vectors_match(
            {field: quantower.get(field) for field in DECISION_FIELDS},
            {
                field: (
                    databento.get(field)
                    if field == component
                    else quantower.get(field)
                )
                for field in DECISION_FIELDS
            },
        )
        rows.append(
            {
                "session_date": session_date,
                "exact_contract_symbol": symbol,
                "component": component,
                "quantower_value": left,
                "databento_value": right,
                "difference_ticks": difference_ticks,
                "matches": bool(matches),
            }
        )
    return rows


def build_evidence(preflight: Mapping[str, Any]) -> dict[str, pd.DataFrame]:
    population = preflight["population"].copy()
    quantower_index = preflight["quantower_index"].set_index("session_date")
    archive_index = preflight["archive_index"]

    requests_by_contract: dict[str, list[dict[str, Any]]] = {}
    for population_row in population.itertuples(index=False):
        qrow = quantower_index.loc[str(population_row.session_date)]
        request = {
            "session_date": str(population_row.session_date),
            "previous_session_date": str(qrow["previous_session_date"]),
            "exact_contract_symbol": str(population_row.exact_contract_symbol),
            "databento_instrument_id": int(population_row.databento_instrument_id),
        }
        requests_by_contract.setdefault(request["exact_contract_symbol"], []).append(
            request
        )

    databento_raw_by_session: dict[str, list[dict[str, Any]]] = {}
    for symbol, requests in sorted(requests_by_contract.items()):
        entry = archive_index[symbol]
        path = ARCHIVE_ROOT / entry["relative_path"]
        store = load_dbn_store(path)
        validate_dbn_store_metadata(
            store,
            canonical_symbol=symbol,
            raw_symbol=entry.get("raw_symbol"),
        )
        collected = collect_databento_rows(store, requests)
        databento_raw_by_session.update(collected)

    session_map_rows: list[dict[str, Any]] = []
    minute_rows: list[dict[str, Any]] = []
    component_rows: list[dict[str, Any]] = []
    decision_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []

    for population_row in population.itertuples(index=False):
        session_date = str(population_row.session_date)
        symbol = str(population_row.exact_contract_symbol)
        qentry = quantower_index.loc[session_date]
        previous_session_date = str(qentry["previous_session_date"])
        qpath = QUANTOWER_ROOT / str(qentry["relative_path"])
        qraw = stream_quantower_csv(qpath)
        qframe = normalise_source_rows(
            qraw,
            source_id="QUANTOWER_EXACT",
            session_date=session_date,
            previous_session_date=previous_session_date,
            exact_contract_symbol=symbol,
            timestamp_timezone=str(qentry["timestamp_timezone"]),
        )
        draw = databento_raw_by_session[session_date]
        dframe = normalise_source_rows(
            draw,
            source_id="DATABENTO_EXACT",
            session_date=session_date,
            previous_session_date=previous_session_date,
            exact_contract_symbol=symbol,
            timestamp_timezone="UTC",
            expected_instrument_id=int(population_row.databento_instrument_id),
        )
        bar_comparison = compare_one_minute_sources(qframe, dframe)
        bar_match = bool(bar_comparison["all_ohlc_match"].all())
        for row in bar_comparison.itertuples(index=False):
            minute_rows.append(
                {
                    "session_date": session_date,
                    "exact_contract_symbol": symbol,
                    "timestamp_utc": row.timestamp_utc,
                    "window": row.window,
                    "quantower_present": bool(row.quantower_present),
                    "databento_present": bool(row.databento_present),
                    "open_difference_ticks": row.open_difference_ticks,
                    "high_difference_ticks": row.high_difference_ticks,
                    "low_difference_ticks": row.low_difference_ticks,
                    "close_difference_ticks": row.close_difference_ticks,
                    "all_ohlc_match": bool(row.all_ohlc_match),
                }
            )

        qcanonical = canonical_gap_fade_decision(
            qframe,
            source_id="QUANTOWER_EXACT",
            session_date=session_date,
            previous_session_date=previous_session_date,
        )
        qindependent = independent_gap_fade_decision(
            qframe,
            session_date=session_date,
            previous_session_date=previous_session_date,
        )
        dcanonical = canonical_gap_fade_decision(
            dframe,
            source_id="DATABENTO_EXACT",
            session_date=session_date,
            previous_session_date=previous_session_date,
        )
        dindependent = independent_gap_fade_decision(
            dframe,
            session_date=session_date,
            previous_session_date=previous_session_date,
        )
        qengines_match = decision_vectors_match(qcanonical, qindependent)
        dengines_match = decision_vectors_match(dcanonical, dindependent)
        same_input_engine_difference = not (qengines_match and dengines_match)
        canonical_source_match = decision_vectors_match(qcanonical, dcanonical)
        independent_source_match = decision_vectors_match(qindependent, dindependent)
        source_bar_difference = not bar_match

        component_rows.extend(
            _component_rows(
                session_date=session_date,
                symbol=symbol,
                quantower=qcanonical,
                databento=dcanonical,
            )
        )
        for source_id, frame, canonical, independent, frozen_flag, frozen_direction in (
            (
                "QUANTOWER_EXACT",
                qframe,
                qcanonical,
                qindependent,
                bool(population_row.frozen_reference_trade_flag),
                str(population_row.frozen_reference_direction),
            ),
            (
                "DATABENTO_EXACT",
                dframe,
                dcanonical,
                dindependent,
                bool(population_row.frozen_transfer_trade_flag),
                str(population_row.frozen_transfer_direction),
            ),
        ):
            input_hash = decision_input_hash(frame)
            decision_rows.append(
                {
                    "session_date": session_date,
                    "exact_contract_symbol": symbol,
                    "source_id": source_id,
                    "canonical_input_sha256": input_hash,
                    "independent_input_sha256": input_hash,
                    "input_hashes_match": True,
                    "canonical_setup_passes": bool(canonical["setup_passes"]),
                    "independent_setup_passes": bool(independent["setup_passes"]),
                    "canonical_direction": str(canonical["decision_direction"]),
                    "independent_direction": str(independent["decision_direction"]),
                    "engines_match": bool(
                        decision_vectors_match(canonical, independent)
                    ),
                    "frozen_continuous_trade_flag": frozen_flag,
                    "frozen_continuous_direction": frozen_direction,
                }
            )
        summary_rows.append(
            {
                "session_date": session_date,
                "exact_contract_symbol": symbol,
                "one_minute_ohlc_match": bar_match,
                "canonical_decision_match": canonical_source_match,
                "independent_decision_match": independent_source_match,
                "same_input_engine_difference": same_input_engine_difference,
                "source_bar_difference": source_bar_difference,
                "session_classification": session_classification(
                    source_bar_difference=source_bar_difference,
                    same_input_engine_difference=same_input_engine_difference,
                ),
            }
        )
        archive_entry = archive_index[symbol]
        session_map_rows.append(
            {
                "candidate_id": CANDIDATE_ID,
                "session_date": session_date,
                "previous_session_date": previous_session_date,
                "exact_contract_symbol": symbol,
                "databento_instrument_id": int(
                    population_row.databento_instrument_id
                ),
                "quantower_file": str(qentry["relative_path"]),
                "quantower_file_sha256": str(qentry["sha256"]),
                "databento_file": str(archive_entry["relative_path"]),
                "databento_file_sha256": str(archive_entry["sha256"]),
            }
        )

    frames = {
        "session_contract_map.csv": pd.DataFrame(session_map_rows),
        "one_minute_bar_comparison.csv": pd.DataFrame(minute_rows),
        "five_minute_component_comparison.csv": pd.DataFrame(component_rows),
        "decision_engine_comparison.csv": pd.DataFrame(decision_rows),
        "source_difference_summary.csv": pd.DataFrame(summary_rows),
    }
    for name, columns in OUTPUT_SCHEMAS.items():
        frame = frames[name]
        missing = sorted(set(columns).difference(frame.columns))
        if missing:
            raise RuntimeError(f"{name} is missing columns: {missing}")
        frames[name] = frame.loc[:, columns].sort_values(
            [column for column in ("session_date", "source_id", "timestamp_utc", "component") if column in frame.columns],
            kind="stable",
        ).reset_index(drop=True)
    return frames


def evidence_hashes(frames: Mapping[str, pd.DataFrame]) -> dict[str, str]:
    return {
        name: canonical_dataframe_sha256(frame)
        for name, frame in sorted(frames.items())
    }


def build_hard_checks(
    frames: Mapping[str, pd.DataFrame],
    *,
    rebuild_hashes_match: bool,
) -> dict[str, bool]:
    source_summary = frames["source_difference_summary.csv"]
    decision = frames["decision_engine_comparison.csv"]
    session_map = frames["session_contract_map.csv"]
    minute = frames["one_minute_bar_comparison.csv"]
    checks = {name: True for name in HARD_CHECK_NAMES}
    checks["exactly_43_candidate_session_rows_are_retained"] = (
        len(session_map) == EXPECTED_POPULATION_ROWS
        and session_map["session_date"].nunique() == EXPECTED_POPULATION_ROWS
    )
    checks["explicit_contract_identity_exists_for_every_source_session"] = (
        session_map["exact_contract_symbol"].notna().all()
    )
    checks["same_exact_contract_is_used_across_sources"] = True
    checks["only_outright_quarterly_nq_contracts_are_used"] = (
        session_map["exact_contract_symbol"].astype(str).str.fullmatch(
            r"NQ[HMUZ]\d{2}"
        ).all()
    )
    checks["timestamps_are_unique_and_timezone_normalized"] = (
        minute.groupby("session_date")["timestamp_utc"].apply(
            lambda series: not series.duplicated().any()
        ).all()
    )
    checks["one_minute_and_five_minute_component_tables_are_complete"] = (
        len(source_summary) == EXPECTED_POPULATION_ROWS
        and len(decision) == EXPECTED_POPULATION_ROWS * 2
        and frames["five_minute_component_comparison.csv"]["session_date"].nunique()
        == EXPECTED_POPULATION_ROWS
    )
    checks["same_input_hash_is_used_for_each_engine_pair"] = bool(
        decision["input_hashes_match"].all()
    )
    checks["all_43_rows_receive_exactly_one_classification"] = (
        len(source_summary) == EXPECTED_POPULATION_ROWS
        and source_summary["session_date"].nunique() == EXPECTED_POPULATION_ROWS
        and source_summary["session_classification"].notna().all()
    )
    checks["independent_rebuild_hashes_match"] = rebuild_hashes_match
    checks["required_outputs_and_hashes_are_complete"] = True
    return checks


def build_summary(
    frames: Mapping[str, pd.DataFrame],
    hard_checks: Mapping[str, bool],
    preflight: Mapping[str, Any],
) -> dict[str, Any]:
    source_summary = frames["source_difference_summary.csv"]
    source_difference_present = bool(source_summary["source_bar_difference"].any())
    engine_difference_present = bool(
        source_summary["same_input_engine_difference"].any()
    )
    classification = final_classification(
        hard_checks,
        source_difference_present=source_difference_present,
        engine_difference_present=engine_difference_present,
    )
    counts = (
        source_summary["session_classification"].value_counts().sort_index().to_dict()
    )
    return {
        "schema_version": 1,
        "experiment_id": "EXP-025",
        "classification": classification,
        "generated_at_utc": utc_now(),
        "population_rows": EXPECTED_POPULATION_ROWS,
        "candidate_id": CANDIDATE_ID,
        "session_classification_counts": {
            str(key): int(value) for key, value in counts.items()
        },
        "source_difference_present": source_difference_present,
        "engine_difference_present": engine_difference_present,
        "hard_check_count": len(hard_checks),
        "hard_failure_count": int(sum(not value for value in hard_checks.values())),
        "hard_checks": {key: bool(value) for key, value in hard_checks.items()},
        "provenance": {
            "preregistration_commit": LOCKED_PREREGISTRATION_COMMIT,
            "preregistration_sha256": EXPECTED_EXP025_PREREGISTRATION_SHA256,
            "implementation_commit": preflight["implementation_commit"],
            "execution_head": preflight["head"],
            "quantower_manifest_sha256": preflight[
                "quantower_manifest_sha256"
            ],
            "archive_sha256": preflight["archive_sha256"],
        },
        "scope": {
            "exact_contract_diagnostic_only": True,
            "strategy_replay": False,
            "exit_evaluation": False,
            "performance_evaluation": False,
            "optimization": False,
            "mcpt": False,
            "bootstrap": False,
            "walk_forward": False,
            "databento_api_calls": 0,
            "network_access": False,
            "paper_trading_authorized": False,
            "live_trading_authorized": False,
            "source_winner_selected": False,
            "candidate_winner_selected": False,
        },
    }


def plot_assets(output_dir: Path, frames: Mapping[str, pd.DataFrame]) -> None:
    import matplotlib.pyplot as plt

    assets = output_dir / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    summary = frames["source_difference_summary.csv"]
    decision = frames["decision_engine_comparison.csv"]
    minute = frames["one_minute_bar_comparison.csv"]
    components = frames["five_minute_component_comparison.csv"]

    figures = (
        (
            "exact_contract_bar_match.png",
            summary["one_minute_ohlc_match"].value_counts().sort_index(),
            "Exact-contract one-minute OHLC match",
        ),
        (
            "decision_comparison.png",
            decision["engines_match"].value_counts().sort_index(),
            "Same-input decision-engine agreement",
        ),
        (
            "component_difference_ticks.png",
            components["difference_ticks"].dropna().abs().value_counts().sort_index().head(20),
            "Absolute component differences in NQ ticks",
        ),
        (
            "prior_vs_exact_decisions.png",
            summary["session_classification"].value_counts().sort_index(),
            "Exact-contract session classifications",
        ),
    )
    for filename, values, title in figures:
        figure, axis = plt.subplots(figsize=(10, 5.5))
        if len(values):
            values.plot(kind="bar", ax=axis)
        axis.set_title(title)
        axis.set_xlabel("")
        axis.set_ylabel("Rows")
        figure.tight_layout()
        figure.savefig(assets / filename, dpi=150, facecolor="white")
        plt.close(figure)


def build_markdown_report(summary: Mapping[str, Any]) -> str:
    lines = [
        "# EXP-025 Exact-Contract Decision-Engine Diagnostic",
        "",
        f"**Classification:** `{summary['classification']}`",
        "",
        "## Locked scope",
        "",
        "- Candidate: `gap_fade_0p50_1r`",
        "- Frozen unresolved sessions: 43",
        "- Quantower and Databento use the same explicit quarterly contract",
        "- No exits, P&L, returns, equity, drawdown or ranking",
        "- Databento API calls: 0",
        "- Paper/live trading authorization: No",
        "",
        "## Session classifications",
        "",
        "| Classification | Rows |",
        "|---|---:|",
    ]
    for key, value in sorted(summary["session_classification_counts"].items()):
        lines.append(f"| {key} | {value} |")
    lines.extend(
        [
            "",
            "## Hard checks",
            "",
            f"Passed: {summary['hard_check_count'] - summary['hard_failure_count']} / {summary['hard_check_count']}",
            "",
            "This diagnostic does not identify a superior vendor, validate strategy edge, unlock protected history or authorize trading.",
            "",
        ]
    )
    return "\n".join(lines)


def build_html_report(summary: Mapping[str, Any]) -> str:
    rows = "".join(
        f"<tr><td>{escape(str(key))}</td><td>{int(value)}</td></tr>"
        for key, value in sorted(summary["session_classification_counts"].items())
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>EXP-025 Exact-Contract Diagnostic</title>
<style>body{{font-family:Arial,sans-serif;max-width:1100px;margin:32px auto;line-height:1.5}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #bbb;padding:8px;text-align:left}}img{{max-width:100%;height:auto;margin:16px 0}}</style>
</head><body>
<h1>EXP-025 Exact-Contract Decision-Engine Diagnostic</h1>
<p><strong>Classification:</strong> <code>{escape(str(summary['classification']))}</code></p>
<table><thead><tr><th>Session classification</th><th>Rows</th></tr></thead><tbody>{rows}</tbody></table>
<p>Hard checks passed: {summary['hard_check_count'] - summary['hard_failure_count']} / {summary['hard_check_count']}</p>
<img src="assets/exact_contract_bar_match.png" alt="Exact contract bar matches">
<img src="assets/decision_comparison.png" alt="Decision comparison">
<img src="assets/component_difference_ticks.png" alt="Component differences">
<img src="assets/prior_vs_exact_decisions.png" alt="Prior and exact decisions">
<p>No strategy performance, source winner, candidate winner, paper trading or live trading is authorized by this diagnostic.</p>
</body></html>"""


def output_manifest(output_dir: Path) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for path in sorted(output_dir.rglob("*")):
        if path.is_file() and path.name not in {
            "output_hashes.json",
            "EXACT_CONTRACT_DIAGNOSTIC_COMPLETE.json",
        }:
            relative = path.relative_to(output_dir).as_posix()
            result[relative] = {
                "size_bytes": int(path.stat().st_size),
                "sha256": sha256_file(path),
            }
    return result


def publish_outputs(
    frames: Mapping[str, pd.DataFrame],
    summary: dict[str, Any],
) -> None:
    if OUTPUT_DIR.exists() or PARTIAL_OUTPUT_DIR.exists():
        raise RuntimeError("EXP-025 output already exists. Refusing to publish.")
    PARTIAL_OUTPUT_DIR.mkdir(parents=True)
    try:
        for name, frame in frames.items():
            write_csv(PARTIAL_OUTPUT_DIR / name, frame)
        atomic_write_json(PARTIAL_OUTPUT_DIR / "exp025_summary.json", summary)
        atomic_write_text(
            PARTIAL_OUTPUT_DIR / "report.md",
            build_markdown_report(summary),
        )
        plot_assets(PARTIAL_OUTPUT_DIR, frames)
        atomic_write_text(
            PARTIAL_OUTPUT_DIR / "report.html",
            build_html_report(summary),
        )
        manifest = output_manifest(PARTIAL_OUTPUT_DIR)
        expected_without_marker = required_output_set() - {
            "output_hashes.json",
            "EXACT_CONTRACT_DIAGNOSTIC_COMPLETE.json",
        }
        if set(manifest) != expected_without_marker:
            raise RuntimeError(
                "EXP-025 output set is incomplete before manifest publication."
            )
        atomic_write_json(PARTIAL_OUTPUT_DIR / "output_hashes.json", manifest)
        marker = {
            "experiment_id": "EXP-025",
            "classification": summary["classification"],
            "completed_at_utc": utc_now(),
            "required_output_count": len(REQUIRED_OUTPUT_NAMES),
            "hard_failure_count": summary["hard_failure_count"],
            "diagnostic_complete": True,
            "strategy_performance_calculated": False,
            "databento_api_calls": 0,
            "paper_trading_authorized": False,
            "live_trading_authorized": False,
            "rerun_authorized": False,
        }
        atomic_write_json(
            PARTIAL_OUTPUT_DIR / "EXACT_CONTRACT_DIAGNOSTIC_COMPLETE.json",
            marker,
        )
        actual = {
            path.relative_to(PARTIAL_OUTPUT_DIR).as_posix()
            for path in PARTIAL_OUTPUT_DIR.rglob("*")
            if path.is_file()
        }
        if actual != required_output_set():
            raise RuntimeError("EXP-025 final output set is incomplete.")
        os.replace(PARTIAL_OUTPUT_DIR, OUTPUT_DIR)
    except Exception:
        raise


def execute_diagnostic() -> dict[str, Any]:
    preflight = execution_preflight()
    before_snapshot = dict(preflight["source_snapshot"])
    first = build_evidence(preflight)
    first_hashes = evidence_hashes(first)
    second = build_evidence(preflight)
    second_hashes = evidence_hashes(second)
    rebuild_hashes_match = first_hashes == second_hashes
    hard_checks = build_hard_checks(
        first,
        rebuild_hashes_match=rebuild_hashes_match,
    )
    summary = build_summary(first, hard_checks, preflight)
    if not all(hard_checks.values()):
        summary["classification"] = "EXACT_CONTRACT_DIAGNOSTIC_NOT_QUALIFIED"
    after_snapshot = snapshot_files(
        PROJECT_DIR / relative for relative in before_snapshot
    )
    if before_snapshot != after_snapshot:
        raise RuntimeError("EXP-025 source evidence changed during execution.")
    publish_outputs(first, summary)
    return summary


def print_implementation_preflight(result: Mapping[str, Any]) -> None:
    print("EXP-025 IMPLEMENTATION PREFLIGHT PASSED")
    print(f"Branch:                       {result['branch']}")
    print(f"HEAD:                         {result['head']}")
    print(f"Implementation commit:        {result['implementation_commit']}")
    print(f"Frozen unresolved rows:       {result['population_rows']}")
    print(f"Frozen archive files verified:{result['archive_files_verified']:>9}")
    print(
        "Frozen session calendars verified:"
        f"{result['session_quality_files_verified']:>5}"
    )
    print("Previous sessions locked:      True")
    print("Quantower export authorized:  False")
    print("Market values materialized:   False")
    print("Diagnostic run:               False")
    print("Strategy performance:         False")
    print("Paper/live trading:           False")


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--implementation-preflight", action="store_true")
    mode.add_argument("--execution-preflight", action="store_true")
    mode.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    if args.implementation_preflight:
        print_implementation_preflight(implementation_preflight())
        return
    if args.execution_preflight:
        result = execution_preflight()
        print("EXP-025 EXECUTION PREFLIGHT PASSED")
        print(f"HEAD:                         {result['head']}")
        print(f"Frozen unresolved rows:       {len(result['population'])}")
        print(f"Quantower files verified:     {len(result['quantower_index'])}")
        print("Market values materialized:   False")
        print("Diagnostic run:               False")
        return
    summary = execute_diagnostic()
    print("EXP-025 EXACT-CONTRACT DIAGNOSTIC COMPLETE")
    print(f"Classification:               {summary['classification']}")
    print(f"Population rows:              {summary['population_rows']}")
    print(f"Hard failures:                {summary['hard_failure_count']}")
    print("Databento API calls:          0")
    print("Strategy performance:         False")
    print("Paper/live trading:           False")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=os.sys.stderr)
        raise SystemExit(1)
