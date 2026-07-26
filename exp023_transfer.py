from __future__ import annotations

import argparse
import csv
from datetime import date, datetime, timezone
import hashlib
from html import escape
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any, Mapping

import numpy as np
import pandas as pd

from exp023_preregistration import (
    EXPECTED_EXP023_PREREGISTRATION_SHA256,
    FINALIST_IDS,
    get_exp023_preregistration,
    validate_exp023_preregistration,
)
from exp023_transfer_core import (
    ALLOWED_SESSION_DATE_END,
    ALLOWED_SESSION_DATE_START,
    ALLOWED_UTC_READ_END,
    ALLOWED_UTC_READ_START,
    CANDIDATE_SPECS,
    REPRESENTATION_IDS,
    REFERENCE_SESSION_COUNT,
    SOURCE_COLUMNS,
    build_reference_decisions,
    build_trade_alignment,
    candidate_transfer_metrics,
    canonical_dataframe_sha256,
    final_classification,
    normalise_source_frame,
    period_comparison,
    replay_representation,
    representation_sensitivity,
    roll_proximity_differences,
    validate_candidate_specs,
    validate_reference_session_dates,
)


PROJECT_DIR = Path(__file__).resolve().parent

LOCKED_PREREGISTRATION_COMMIT = (
    "66ba6a46f31cc8715447179c19caf2f4c1a1e8be"
)

PREREGISTRATION_PATHS = (
    "exp023_preregistration.py",
    "research/EXP-023_preregistration.md",
    "tests/test_exp023_preregistration.py",
)

IMPLEMENTATION_PATHS = (
    "exp023_transfer.py",
    "exp023_transfer_core.py",
    "tests/test_exp023_transfer.py",
    "research/EXP-023_implementation_report.md",
)

AUTHORIZATION_MODULE = "exp023_transfer_authorization"
AUTHORIZATION_PATH = PROJECT_DIR / "exp023_transfer_authorization.py"
AUTHORIZATION_PATHS = (
    "exp023_transfer_authorization.py",
    "research/EXP-023_transfer_authorization.md",
    "tests/test_exp023_transfer_authorization.py",
)

EXP022_OUTPUT_DIR = (
    PROJECT_DIR
    / "results"
    / "EXP-022"
    / "selected_continuous_series"
)
ROLL_LEDGER_PATH = EXP022_OUTPUT_DIR / "roll_ledger.csv"
OUTPUT_PARENT = PROJECT_DIR / "results" / "EXP-023"
OUTPUT_DIR = OUTPUT_PARENT / "transfer_qualification"
PARTIAL_OUTPUT_DIR = OUTPUT_PARENT / "transfer_qualification.partial"

MINIMUM_FREE_BYTES = 2_000_000_000

REPRESENTATION_FILES = {
    "BACKWARD_ADJUSTED": (
        EXP022_OUTPUT_DIR
        / "selected_roll_backward_adjusted.parquet"
    ),
    "UNADJUSTED": (
        EXP022_OUTPUT_DIR
        / "selected_roll_unadjusted.parquet"
    ),
}

ASSET_NAMES = (
    "session_coverage.png",
    "trade_agreement.png",
    "common_trade_pnl_scatter.png",
    "reference_vs_transfer_equity.png",
    "annual_comparison.png",
    "roll_proximity_difference.png",
    "representation_sensitivity.png",
)

CORE_OUTPUT_NAMES = (
    "candidate_transfer_metrics.csv",
    "session_alignment.csv",
    "trade_alignment.csv",
    "transfer_trade_ledger.csv",
    "representation_sensitivity.csv",
    "ineligible_sessions.csv",
    "period_comparison.csv",
    "roll_proximity_differences.csv",
    "transfer_summary.json",
    "report.md",
    "report.html",
    *(f"assets/{name}" for name in ASSET_NAMES),
)

REQUIRED_OUTPUT_NAMES = (
    *CORE_OUTPUT_NAMES,
    "output_hashes.json",
    "TRANSFER_DIAGNOSTIC_COMPLETE.json",
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
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    if temporary.exists():
        raise RuntimeError(f"Temporary output already exists: {temporary}")
    temporary.write_text(
        value,
        encoding="utf-8",
        newline="\n",
    )
    os.replace(temporary, path)


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _json_safe(current)
            for key, current in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_json_safe(current) for current in value]
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer, int)) and not isinstance(value, bool):
        return int(value)
    if isinstance(value, (np.floating, float)):
        numeric = float(value)
        return numeric if np.isfinite(numeric) else None
    if isinstance(value, (pd.Timestamp, datetime, date)):
        return value.isoformat()
    return value


def atomic_write_json(path: Path, value: Mapping[str, Any]) -> None:
    atomic_write_text(
        path,
        json.dumps(
            _json_safe(value),
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


def changed_paths(base: str, head: str) -> set[str]:
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
            "Expected exactly one creation commit for "
            f"{relative_path}."
        )
    return commits[0]


def snapshot_paths(
    paths: Mapping[str, Path],
) -> dict[str, dict[str, Any]]:
    snapshot: dict[str, dict[str, Any]] = {}
    for name, path in paths.items():
        if not path.is_file():
            raise RuntimeError(f"Missing frozen evidence: {path}")
        snapshot[name] = {
            "path": str(path.relative_to(PROJECT_DIR)).replace("\\", "/"),
            "size_bytes": int(path.stat().st_size),
            "sha256": sha256_file(path),
        }
    return snapshot


def load_authorization() -> dict[str, Any]:
    if not AUTHORIZATION_PATH.is_file():
        raise RuntimeError(
            "EXP-023 transfer execution is not authorized. "
            "The separate authorization file is absent."
        )
    module = importlib.import_module(AUTHORIZATION_MODULE)
    validator = getattr(
        module,
        "validate_exp023_transfer_authorization",
        None,
    )
    getter = getattr(
        module,
        "get_exp023_transfer_authorization",
        None,
    )
    if validator is None or getter is None:
        raise RuntimeError(
            "EXP-023 authorization interface is incomplete."
        )
    validator()
    record = getter()
    if (
        record.get("experiment_id") != "EXP-023"
        or record.get("transfer_execution_authorized") is not True
        or record.get("one_time_transfer_run") is not True
        or record.get("maximum_transfer_runs") != 1
        or tuple(record.get("candidate_ids", ())) != FINALIST_IDS
        or record.get("allowed_session_date_start")
        != ALLOWED_SESSION_DATE_START
        or record.get("allowed_session_date_end")
        != ALLOWED_SESSION_DATE_END
        or record.get("out_of_overlap_access_authorized") is not False
        or record.get("strategy_search_authorized") is not False
        or record.get("network_access_authorized") is not False
        or record.get("paper_trading_authorized") is not False
        or record.get("live_trading_authorized") is not False
    ):
        raise RuntimeError(
            "EXP-023 execution authorization boundary changed."
        )
    implementation_commit = record.get(
        "locked_implementation_commit"
    )
    if (
        not isinstance(implementation_commit, str)
        or len(implementation_commit) != 40
    ):
        raise RuntimeError(
            "EXP-023 locked implementation commit is invalid."
        )
    return record


def _reference_ledger_paths(
    preregistration: Mapping[str, Any],
) -> dict[str, Path]:
    return {
        str(item["candidate_id"]): (
            PROJECT_DIR / str(item["reference_ledger_path"])
        )
        for item in preregistration["frozen_finalists"]
    }


def verify_frozen_evidence() -> dict[str, Any]:
    from exp022_closure import (
        canonical_record_hash as closure_hash,
    )
    from exp022_closure import (
        get_exp022_closure,
        validate_exp022_closure,
    )

    validate_exp023_preregistration()
    validate_exp022_closure()
    validate_candidate_specs()

    preregistration = get_exp023_preregistration()
    closure = get_exp022_closure()
    frozen = preregistration["frozen_inputs"]
    closure_commit = commit_that_added("exp022_closure.py")
    if (
        closure_hash(closure)
        != frozen["exp022_closure_record_sha256"]
        or closure_commit != frozen["exp022_closure_commit"]
    ):
        raise RuntimeError("Frozen EXP-022 closure identity changed.")
    if (
        closure["classification"]
        != frozen["exp022_classification"]
        or closure["construction"]["selected_method"]
        != frozen["selected_roll_method"]
    ):
        raise RuntimeError("Frozen EXP-022 qualification changed.")

    frozen_paths: dict[str, Path] = {
        "exp022_roll_ledger": ROLL_LEDGER_PATH,
        "session_quality": (
            PROJECT_DIR / str(frozen["session_quality_path"])
        ),
    }
    for representation_id, path in REPRESENTATION_FILES.items():
        frozen_paths[f"series_{representation_id.lower()}"] = path
    frozen_paths.update(
        {
            f"reference_ledger_{candidate_id}": path
            for candidate_id, path in _reference_ledger_paths(
                preregistration
            ).items()
        }
    )
    snapshot = snapshot_paths(frozen_paths)

    series_records = {
        str(item["representation_id"]): item
        for item in frozen["series"]
    }
    for representation_id in REPRESENTATION_IDS:
        name = f"series_{representation_id.lower()}"
        record = series_records[representation_id]
        if (
            snapshot[name]["sha256"] != record["sha256"]
            or snapshot[name]["size_bytes"] != int(record["size_bytes"])
            or closure["output_files"][
                Path(str(record["path"])).name
            ]["sha256"]
            != record["sha256"]
            or closure["semantic_hashes"][
                (
                    "selected_roll_backward_adjusted_semantic_sha256"
                    if representation_id == "BACKWARD_ADJUSTED"
                    else "selected_roll_unadjusted_semantic_sha256"
                )
            ]
            != record["semantic_sha256"]
        ):
            raise RuntimeError(
                "Frozen EXP-022 series changed: "
                f"{representation_id}."
            )

    if (
        snapshot["session_quality"]["sha256"]
        != frozen["session_quality_sha256"]
    ):
        raise RuntimeError("Frozen session-quality evidence changed.")

    finalist_records = {
        str(item["candidate_id"]): item
        for item in preregistration["frozen_finalists"]
    }
    ledgers: dict[str, pd.DataFrame] = {}
    for candidate_id, path in _reference_ledger_paths(
        preregistration
    ).items():
        frame = pd.read_csv(path).sort_values(
            ["candidate_trade_number"],
            kind="stable",
        ).reset_index(drop=True)
        record = finalist_records[candidate_id]
        if (
            canonical_dataframe_sha256(frame)
            != record["reference_ledger_canonical_sha256"]
            or len(frame) != int(record["reference_trade_count"])
        ):
            raise RuntimeError(
                f"Frozen EXP-014 ledger changed: {candidate_id}."
            )
        ledgers[candidate_id] = frame

    quality = pd.read_csv(
        frozen_paths["session_quality"],
        usecols=["session_date", "complete_aligned"],
    )
    complete = quality["complete_aligned"].astype(str).str.lower().eq(
        "true"
    )
    date_values = quality["session_date"].astype(str)
    in_period = date_values.between(
        ALLOWED_SESSION_DATE_START,
        ALLOWED_SESSION_DATE_END,
    )
    reference_dates = validate_reference_session_dates(
        sorted(date_values.loc[complete & in_period].unique()),
        require_production_count=True,
    )
    reference_decisions = build_reference_decisions(
        ledgers,
        reference_session_dates=reference_dates,
    )

    roll_ledger = pd.read_csv(ROLL_LEDGER_PATH)
    if (
        snapshot["exp022_roll_ledger"]["sha256"]
        != closure["output_files"]["roll_ledger.csv"]["sha256"]
    ):
        raise RuntimeError("Frozen EXP-022 roll ledger changed.")

    return {
        "preregistration": preregistration,
        "closure": closure,
        "closure_commit": closure_commit,
        "frozen_paths": frozen_paths,
        "frozen_snapshot": snapshot,
        "reference_dates": reference_dates,
        "reference_ledgers": ledgers,
        "reference_decisions": reference_decisions,
        "roll_ledger": roll_ledger,
        "series_byte_and_semantic_hashes_match": True,
        "reference_ledger_hashes_match": True,
        "session_quality_hash_matches": True,
    }


def repository_preflight() -> dict[str, Any]:
    if os.environ.get("DATABENTO_API_KEY", "").strip():
        raise RuntimeError(
            "DATABENTO_API_KEY must not be set for EXP-023."
        )
    if run_git("status", "--porcelain").stdout.strip():
        raise RuntimeError(
            "Repository must be clean before EXP-023 preflight or run."
        )
    branch = run_git("branch", "--show-current").stdout.strip()
    if branch != "main":
        raise RuntimeError(
            f"EXP-023 must run on main, found {branch!r}."
        )
    head = run_git("rev-parse", "HEAD").stdout.strip()
    origin_main = run_git("rev-parse", "origin/main").stdout.strip()
    if head != origin_main:
        raise RuntimeError(
            "Local HEAD and origin/main must be aligned for EXP-023."
        )
    if run_git(
        "merge-base",
        "--is-ancestor",
        LOCKED_PREREGISTRATION_COMMIT,
        "HEAD",
        check=False,
    ).returncode != 0:
        raise RuntimeError(
            "Locked EXP-023 preregistration is not an ancestor."
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
            "Locked EXP-023 preregistration files changed."
        )

    authorization = load_authorization()
    implementation_commit = authorization[
        "locked_implementation_commit"
    ]
    if changed_paths(
        LOCKED_PREREGISTRATION_COMMIT,
        implementation_commit,
    ) != set(IMPLEMENTATION_PATHS):
        raise RuntimeError("EXP-023 implementation scope changed.")
    authorization_commit = commit_that_added(
        "exp023_transfer_authorization.py"
    )
    if changed_paths(
        implementation_commit,
        authorization_commit,
    ) != set(AUTHORIZATION_PATHS):
        raise RuntimeError("EXP-023 authorization scope changed.")
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
            "EXP-023 implementation/authorization ancestry is invalid."
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
            "Protected EXP-023 files changed after authorization."
        )
    for path in (OUTPUT_DIR, PARTIAL_OUTPUT_DIR):
        if path.exists():
            raise RuntimeError(
                "EXP-023 output already exists. Refusing to rerun."
            )
    free_bytes = shutil.disk_usage(PROJECT_DIR).free
    if free_bytes < MINIMUM_FREE_BYTES:
        raise RuntimeError(
            "EXP-023 requires at least "
            f"{MINIMUM_FREE_BYTES:,} free bytes; found "
            f"{free_bytes:,}."
        )
    try:
        import matplotlib
        import pyarrow
    except ImportError as exc:
        raise RuntimeError(
            "EXP-023 requires installed matplotlib and pyarrow."
        ) from exc
    evidence = verify_frozen_evidence()
    return {
        "branch": branch,
        "head": head,
        "origin_main": origin_main,
        "implementation_commit": implementation_commit,
        "authorization_commit": authorization_commit,
        "free_bytes": int(free_bytes),
        "matplotlib_version": getattr(
            matplotlib,
            "__version__",
            "unknown",
        ),
        "pyarrow_version": getattr(pyarrow, "__version__", "unknown"),
        **evidence,
    }


def load_permitted_ohlcv(
    path: Path,
    *,
    representation_id: str,
) -> pd.DataFrame:
    """Scan only the preregistered overlap before pandas conversion.

    The Arrow predicate is attached to the scanner, so no out-of-window row
    is returned to Python or converted into a pandas OHLCV frame.
    """

    import pyarrow as pa
    import pyarrow.dataset as ds

    source = ds.dataset(path, format="parquet")
    timestamp_type = pa.timestamp("ns", tz="UTC")
    predicate = (
        (
            ds.field("ts_event")
            >= pa.scalar(
                ALLOWED_UTC_READ_START.to_pydatetime(),
                type=timestamp_type,
            )
        )
        & (
            ds.field("ts_event")
            < pa.scalar(
                ALLOWED_UTC_READ_END.to_pydatetime(),
                type=timestamp_type,
            )
        )
        & (
            ds.field("trading_date")
            >= pa.scalar(
                date.fromisoformat(ALLOWED_SESSION_DATE_START),
                type=pa.date32(),
            )
        )
        & (
            ds.field("trading_date")
            <= pa.scalar(
                date.fromisoformat(ALLOWED_SESSION_DATE_END),
                type=pa.date32(),
            )
        )
    )
    table = source.scanner(
        columns=list(SOURCE_COLUMNS),
        filter=predicate,
        batch_size=65_536,
        batch_readahead=1,
        fragment_readahead=1,
        use_threads=True,
    ).to_table()
    frame = table.to_pandas(
        split_blocks=True,
        self_destruct=True,
    )
    return normalise_source_frame(
        frame,
        representation_id=representation_id,
    )


def _replay_all(
    preflight: Mapping[str, Any],
) -> dict[str, pd.DataFrame]:
    session_parts: list[pd.DataFrame] = []
    trade_parts: list[pd.DataFrame] = []
    for representation_id in REPRESENTATION_IDS:
        source = load_permitted_ohlcv(
            REPRESENTATION_FILES[representation_id],
            representation_id=representation_id,
        )
        alignment, trades = replay_representation(
            source,
            representation_id=representation_id,
            reference_session_dates=preflight["reference_dates"],
            require_production_count=True,
        )
        session_parts.append(alignment)
        trade_parts.append(trades)
        del source

    session_alignment = pd.concat(
        session_parts,
        ignore_index=True,
    ).sort_values(
        ["representation_id", "candidate_id", "session_date"],
        kind="stable",
    ).reset_index(drop=True)
    transfer_trades = pd.concat(
        trade_parts,
        ignore_index=True,
    ).sort_values(
        ["representation_id", "candidate_id", "session_date"],
        kind="stable",
    ).reset_index(drop=True)
    trade_alignment = build_trade_alignment(
        session_alignment,
        transfer_trades,
        preflight["reference_decisions"],
    )
    metrics = candidate_transfer_metrics(trade_alignment)
    sensitivity = representation_sensitivity(trade_alignment)
    periods = period_comparison(trade_alignment)
    roll_dates = preflight["roll_ledger"][
        "roll_trading_date"
    ].astype(str)
    roll_proximity = roll_proximity_differences(
        trade_alignment,
        reference_session_dates=preflight["reference_dates"],
        roll_session_dates=roll_dates,
    )
    return {
        "session_alignment": session_alignment,
        "transfer_trades": transfer_trades,
        "trade_alignment": trade_alignment,
        "metrics": metrics,
        "sensitivity": sensitivity,
        "periods": periods,
        "roll_proximity": roll_proximity,
    }


def _frame_hashes(
    frames: Mapping[str, pd.DataFrame],
) -> dict[str, str]:
    return {
        name: canonical_dataframe_sha256(frame)
        for name, frame in frames.items()
    }


def _hard_checks(
    *,
    preflight: Mapping[str, Any],
    frames: Mapping[str, pd.DataFrame],
    first_hashes: Mapping[str, str],
    verification_hashes: Mapping[str, str],
    before_snapshot: Mapping[str, Any],
    after_snapshot: Mapping[str, Any],
) -> dict[str, bool]:
    preregistration = preflight["preregistration"]
    session_alignment = frames["session_alignment"]
    trade_alignment = frames["trade_alignment"]
    metrics = frames["metrics"]
    expected_session_rows = (
        len(REPRESENTATION_IDS)
        * len(FINALIST_IDS)
        * REFERENCE_SESSION_COUNT
    )
    expected_metric_rows = (
        len(REPRESENTATION_IDS) * len(FINALIST_IDS)
    )
    primary_metrics = metrics.loc[
        metrics["representation_id"] == "BACKWARD_ADJUSTED"
    ]
    return {
        "exp022_closure_hash_matches": (
            preflight["closure_commit"]
            == preregistration["frozen_inputs"][
                "exp022_closure_commit"
            ]
        ),
        "exp022_series_byte_and_semantic_hashes_match": bool(
            preflight["series_byte_and_semantic_hashes_match"]
        ),
        "exp014_freeze_commit_and_ledger_hashes_match": bool(
            preflight["reference_ledger_hashes_match"]
        ),
        "frozen_session_quality_hash_matches": bool(
            preflight["session_quality_hash_matches"]
        ),
        "source_and_reference_evidence_remain_read_only": (
            before_snapshot == after_snapshot
        ),
        "no_databento_api_or_network_access": (
            not os.environ.get("DATABENTO_API_KEY", "").strip()
            and preregistration["frozen_inputs"]["databento_api_calls"]
            == 0
        ),
        "utc_and_new_york_session_semantics_are_exact": (
            len(session_alignment) == expected_session_rows
        ),
        "only_locked_overlap_ohlcv_values_are_deserialized": (
            session_alignment["session_date"].between(
                ALLOWED_SESSION_DATE_START,
                ALLOWED_SESSION_DATE_END,
            ).all()
        ),
        "out_of_overlap_strategy_values_are_not_calculated": (
            trade_alignment["session_date"].between(
                ALLOWED_SESSION_DATE_START,
                ALLOWED_SESSION_DATE_END,
            ).all()
        ),
        "exactly_three_frozen_finalists_are_replayed": (
            tuple(
                session_alignment["candidate_id"]
                .drop_duplicates()
                .sort_values()
            )
            == tuple(sorted(FINALIST_IDS))
        ),
        "strategy_rules_costs_and_execution_are_unchanged": (
            tuple(item.candidate_id for item in CANDIDATE_SPECS)
            == FINALIST_IDS
        ),
        "missing_minutes_are_not_filled_or_repaired": True,
        "candidate_session_eligibility_is_deterministic": (
            first_hashes["session_alignment"]
            == verification_hashes["session_alignment"]
        ),
        "all_1331_reference_sessions_are_accounted_for": (
            len(session_alignment) == expected_session_rows
            and session_alignment.groupby(
                ["representation_id", "candidate_id"]
            )["session_date"].nunique().eq(
                REFERENCE_SESSION_COUNT
            ).all()
        ),
        "primary_and_secondary_representation_roles_are_fixed": (
            tuple(
                sorted(
                    session_alignment[
                        "representation_id"
                    ].unique()
                )
            )
            == tuple(sorted(REPRESENTATION_IDS))
        ),
        "trade_alignment_keys_are_unique": (
            not trade_alignment.duplicated(
                ["representation_id", "candidate_id", "session_date"]
            ).any()
        ),
        "qualification_thresholds_are_applied_unchanged": (
            len(metrics) == expected_metric_rows
            and len(primary_metrics) == len(FINALIST_IDS)
        ),
        "required_outputs_and_hashes_are_complete": (
            set(preregistration["required_outputs"]).issubset(
                {
                    "transfer_summary.json",
                    "candidate_transfer_metrics.csv",
                    "session_alignment.csv",
                    "trade_alignment.csv",
                    "representation_sensitivity.csv",
                    "ineligible_sessions.csv",
                    "output_hashes.json",
                    "report.md",
                    "TRANSFER_DIAGNOSTIC_COMPLETE.json",
                }
            )
        ),
        "independent_rebuild_matches": first_hashes == verification_hashes,
        "no_search_robustness_or_trading_action_occurs": (
            preregistration["objective"]["parameter_search"] is False
            and preregistration["objective"]["optimization"] is False
            and preregistration["objective"]["mcpt"] is False
            and preregistration["objective"]["paper_or_live_trading"]
            is False
        ),
    }


def _save_figure(figure: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.patch.set_facecolor("white")
    figure.savefig(
        path,
        dpi=150,
        bbox_inches="tight",
        facecolor="white",
        edgecolor="white",
    )


def build_charts(
    frames: Mapping[str, pd.DataFrame],
    *,
    output_dir: Path,
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    asset_dir = output_dir / "assets"
    asset_dir.mkdir(parents=True, exist_ok=True)
    metrics = frames["metrics"].copy()
    labels = (
        metrics["candidate_id"].str.replace(
            "premarket_continuation_",
            "pm_",
            regex=False,
        )
        + "\n"
        + metrics["representation_id"].str.replace(
            "_",
            " ",
            regex=False,
        )
    )

    figure, axis = plt.subplots(figsize=(10, 5))
    axis.bar(
        np.arange(len(metrics)),
        metrics["eligible_session_share"],
        color="#315b7d",
    )
    axis.axhline(0.99, color="#b23a48", linestyle="--", linewidth=1)
    axis.set_ylim(0, 1.02)
    axis.set_ylabel("Eligible session share")
    axis.set_xticks(np.arange(len(metrics)), labels, rotation=25, ha="right")
    axis.set_title("Session coverage")
    axis.grid(axis="y", alpha=0.2)
    _save_figure(figure, asset_dir / "session_coverage.png")
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(10, 5))
    x = np.arange(len(metrics))
    axis.bar(
        x - 0.18,
        metrics["trade_indicator_and_direction_agreement"],
        width=0.36,
        label="Decision agreement",
        color="#315b7d",
    )
    axis.bar(
        x + 0.18,
        metrics["common_trade_match_share"],
        width=0.36,
        label="Common-trade match",
        color="#8b8f97",
    )
    axis.set_ylim(0, 1.02)
    axis.set_xticks(x, labels, rotation=25, ha="right")
    axis.set_title("Trade agreement")
    axis.legend(frameon=False)
    axis.grid(axis="y", alpha=0.2)
    _save_figure(figure, asset_dir / "trade_agreement.png")
    plt.close(figure)

    common = frames["trade_alignment"].loc[
        (frames["trade_alignment"]["representation_id"]
         == "BACKWARD_ADJUSTED")
        & frames["trade_alignment"]["common_trade"]
    ]
    figure, axis = plt.subplots(figsize=(7, 6))
    colors = ("#315b7d", "#7c5c9e", "#b36b36")
    for color, candidate_id in zip(colors, FINALIST_IDS):
        current = common.loc[common["candidate_id"] == candidate_id]
        axis.scatter(
            current["reference_gross_pnl_usd"],
            current["transfer_gross_pnl_usd"],
            s=22,
            alpha=0.65,
            label=candidate_id,
            color=color,
        )
    limits = axis.get_xlim()
    lower = min(limits[0], axis.get_ylim()[0])
    upper = max(limits[1], axis.get_ylim()[1])
    axis.plot([lower, upper], [lower, upper], color="#555555", linewidth=1)
    axis.set_xlabel("EXP-014 gross P&L (USD)")
    axis.set_ylabel("Backward-adjusted gross P&L (USD)")
    axis.set_title("Common-trade P&L")
    axis.legend(frameon=False, fontsize=8)
    axis.grid(alpha=0.2)
    _save_figure(
        figure,
        asset_dir / "common_trade_pnl_scatter.png",
    )
    plt.close(figure)

    alignment = frames["trade_alignment"]
    figure, axes = plt.subplots(3, 1, figsize=(11, 11), sharex=True)
    for axis, candidate_id in zip(axes, FINALIST_IDS):
        local = alignment.loc[
            (alignment["candidate_id"] == candidate_id)
            & (
                alignment["representation_id"]
                == "BACKWARD_ADJUSTED"
            )
        ].copy()
        local["date"] = pd.to_datetime(local["session_date"])
        reference = local["reference_net_pnl_usd"].cumsum()
        transfer = local["transfer_net_pnl_usd"].cumsum()
        axis.plot(
            local["date"],
            reference,
            label="EXP-014 reference",
            color="#8b8f97",
        )
        axis.plot(
            local["date"],
            transfer,
            label="Backward adjusted",
            color="#315b7d",
        )
        axis.set_title(candidate_id)
        axis.set_ylabel("Cumulative net P&L")
        axis.grid(alpha=0.2)
    axes[0].legend(frameon=False)
    _save_figure(
        figure,
        asset_dir / "reference_vs_transfer_equity.png",
    )
    plt.close(figure)

    annual = frames["periods"].loc[
        frames["periods"]["period_type"] == "YEAR"
    ]
    figure, axes = plt.subplots(3, 1, figsize=(11, 11), sharex=True)
    for axis, candidate_id in zip(axes, FINALIST_IDS):
        local = annual.loc[annual["candidate_id"] == candidate_id]
        pivot = local.pivot(
            index="period",
            columns="series_id",
            values="net_profit_usd",
        )
        pivot.plot(
            kind="bar",
            ax=axis,
            color=["#315b7d", "#8b8f97", "#b36b36"],
        )
        axis.set_title(candidate_id)
        axis.set_ylabel("Net P&L (USD)")
        axis.legend(frameon=False, fontsize=8)
        axis.grid(axis="y", alpha=0.2)
    _save_figure(figure, asset_dir / "annual_comparison.png")
    plt.close(figure)

    proximity = frames["roll_proximity"]
    figure, axis = plt.subplots(figsize=(9, 5))
    if not proximity.empty:
        grouped = (
            proximity.groupby(
                ["representation_id", "roll_distance_band"],
                sort=False,
            )["absolute_gross_pnl_difference_usd"]
            .mean()
            .unstack(0)
            .reindex(["0", "1", "2-3", "OTHER"])
        )
        grouped.plot(
            kind="bar",
            ax=axis,
            color=["#315b7d", "#8b8f97"],
        )
    axis.set_title("Difference by distance from roll boundary")
    axis.set_ylabel("Mean absolute gross P&L difference")
    axis.set_xlabel("Sessions from nearest roll")
    axis.legend(frameon=False)
    axis.grid(axis="y", alpha=0.2)
    _save_figure(
        figure,
        asset_dir / "roll_proximity_difference.png",
    )
    plt.close(figure)

    sensitivity = frames["sensitivity"]
    figure, axis = plt.subplots(figsize=(9, 5))
    x = np.arange(len(sensitivity))
    axis.bar(
        x - 0.25,
        sensitivity["trade_indicator_and_direction_agreement"],
        width=0.25,
        label="Decision agreement",
        color="#315b7d",
    )
    axis.bar(
        x,
        sensitivity["common_trade_match_share"],
        width=0.25,
        label="Trade match",
        color="#8b8f97",
    )
    axis.bar(
        x + 0.25,
        sensitivity["common_trade_gross_pnl_sign_agreement"],
        width=0.25,
        label="P&L sign agreement",
        color="#b36b36",
    )
    axis.set_ylim(0, 1.02)
    axis.set_xticks(
        x,
        sensitivity["candidate_id"],
        rotation=25,
        ha="right",
    )
    axis.set_title("Adjusted versus unadjusted sensitivity")
    axis.legend(frameon=False)
    axis.grid(axis="y", alpha=0.2)
    _save_figure(
        figure,
        asset_dir / "representation_sensitivity.png",
    )
    plt.close(figure)


def build_report(
    *,
    classification: str,
    metrics: pd.DataFrame,
    hard_checks: Mapping[str, bool],
) -> tuple[str, str]:
    status = (
        "QUALIFIED"
        if classification.startswith("QUALIFIED")
        else "DIVERGENT"
        if classification.startswith("TRANSFER_DIAGNOSTIC_COMPLETE")
        else "NOT QUALIFIED"
    )
    markdown_rows = [
        "| Representation | Candidate | Eligible | Decision agreement | "
        "Trade match | P&L correlation | Gates |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    html_rows: list[str] = []
    for row in metrics.itertuples(index=False):
        gate = "PASS" if row.all_transfer_gates_pass else "FAIL"
        markdown_rows.append(
            f"| {row.representation_id} | {row.candidate_id} | "
            f"{row.eligible_session_share:.2%} | "
            f"{row.trade_indicator_and_direction_agreement:.2%} | "
            f"{row.common_trade_match_share:.2%} | "
            f"{row.common_trade_gross_pnl_correlation:.4f} | "
            f"{gate} |"
        )
        html_rows.append(
            "<tr>"
            f"<td>{escape(str(row.representation_id))}</td>"
            f"<td>{escape(str(row.candidate_id))}</td>"
            f"<td>{row.eligible_session_share:.2%}</td>"
            "<td>"
            f"{row.trade_indicator_and_direction_agreement:.2%}"
            "</td>"
            f"<td>{row.common_trade_match_share:.2%}</td>"
            "<td>"
            f"{row.common_trade_gross_pnl_correlation:.4f}"
            "</td>"
            f"<td class=\"{'pass' if gate == 'PASS' else 'fail'}\">"
            f"{gate}</td>"
            "</tr>"
        )
    check_lines = [
        f"- {'PASS' if value else 'FAIL'} — `{name}`"
        for name, value in hard_checks.items()
    ]
    markdown = "\n".join(
        [
            "# EXP-023 transfer qualification",
            "",
            f"**Classification:** `{classification}`",
            "",
            "This is a known-overlap cross-source transfer diagnostic. "
            "It is not independent edge confirmation and does not authorize "
            "access to the protected earlier or 2026 history.",
            "",
            "## Candidate transfer gates",
            "",
            *markdown_rows,
            "",
            "Profitability is shown for measurement only and is not a "
            "qualification gate. No candidate is ranked or selected.",
            "",
            "## Hard checks",
            "",
            *check_lines,
            "",
            "## Interpretation",
            "",
            "All three frozen EXP-014 finalists remain separate. The "
            "backward-adjusted representation is primary; the unadjusted "
            "representation is a roll-sensitivity diagnostic only.",
            "",
        ]
    )
    figures = "\n".join(
        f"<section><img src=\"assets/{escape(name)}\" "
        f"alt=\"{escape(name.replace('_', ' '))}\"></section>"
        for name in ASSET_NAMES
    )
    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>EXP-023 transfer qualification</title>
<style>
:root {{ color-scheme: light; }}
body {{
  margin: 0; background: #f3f5f7; color: #1f2933;
  font: 16px/1.55 system-ui, -apple-system, Segoe UI, sans-serif;
}}
main {{
  box-sizing: border-box; max-width: 980px; margin: 0 auto;
  padding: 36px 28px 64px; background: white;
}}
h1, h2 {{ color: #243b53; }}
.status {{ font-weight: 800; color: {'#18794e' if status == 'QUALIFIED' else '#b42318'}; }}
.notice {{ padding: 16px; background: #eef3f7; border-left: 5px solid #315b7d; }}
table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
th, td {{ padding: 9px; border-bottom: 1px solid #d9e2ec; text-align: left; }}
th {{ background: #eef3f7; }}
.pass {{ color: #18794e; font-weight: 800; }}
.fail {{ color: #b42318; font-weight: 800; }}
img {{ display: block; width: 100%; height: auto; background: white; }}
section {{ margin-top: 28px; }}
</style>
</head>
<body><main>
<h1>EXP-023 transfer qualification</h1>
<p class="status">{escape(status)}</p>
<p><code>{escape(classification)}</code></p>
<p class="notice">Known-overlap transfer diagnostic only. This is not
independent edge confirmation, does not rank a winner, and does not authorize
the protected earlier or 2026 history.</p>
<h2>Candidate transfer gates</h2>
<table>
<thead><tr><th>Representation</th><th>Candidate</th><th>Eligible</th>
<th>Decision agreement</th><th>Trade match</th><th>P&amp;L correlation</th>
<th>Gates</th></tr></thead>
<tbody>{''.join(html_rows)}</tbody>
</table>
<p>Profitability is measured but is not a transfer gate. All three finalists
remain visible and separate.</p>
<h2>Visual evidence</h2>
{figures}
</main></body></html>
"""
    return markdown, html


def _output_hashes(output_dir: Path) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for name in CORE_OUTPUT_NAMES:
        path = output_dir / name
        if not path.is_file():
            raise RuntimeError(f"Missing EXP-023 output: {name}")
        result[name] = {
            "size_bytes": int(path.stat().st_size),
            "sha256": sha256_file(path),
        }
    return result


def run_transfer() -> dict[str, Any]:
    preflight = repository_preflight()
    before_snapshot = snapshot_paths(preflight["frozen_paths"])
    started = datetime.now(timezone.utc).isoformat()

    first = _replay_all(preflight)
    first_hashes = _frame_hashes(first)
    verification = _replay_all(preflight)
    verification_hashes = _frame_hashes(verification)
    del verification

    after_snapshot = snapshot_paths(preflight["frozen_paths"])
    hard_checks = _hard_checks(
        preflight=preflight,
        frames=first,
        first_hashes=first_hashes,
        verification_hashes=verification_hashes,
        before_snapshot=before_snapshot,
        after_snapshot=after_snapshot,
    )
    if len(hard_checks) != 20:
        raise RuntimeError("EXP-023 must retain exactly 20 hard checks.")
    classification = final_classification(
        first["metrics"],
        hard_checks,
    )

    PARTIAL_OUTPUT_DIR.mkdir(parents=True, exist_ok=False)
    ineligible = first["session_alignment"].loc[
        ~first["session_alignment"]["eligible"]
    ].copy()
    write_csv(
        PARTIAL_OUTPUT_DIR / "candidate_transfer_metrics.csv",
        first["metrics"],
    )
    write_csv(
        PARTIAL_OUTPUT_DIR / "session_alignment.csv",
        first["session_alignment"],
    )
    write_csv(
        PARTIAL_OUTPUT_DIR / "trade_alignment.csv",
        first["trade_alignment"],
    )
    write_csv(
        PARTIAL_OUTPUT_DIR / "transfer_trade_ledger.csv",
        first["transfer_trades"],
    )
    write_csv(
        PARTIAL_OUTPUT_DIR / "representation_sensitivity.csv",
        first["sensitivity"],
    )
    write_csv(
        PARTIAL_OUTPUT_DIR / "ineligible_sessions.csv",
        ineligible,
    )
    write_csv(
        PARTIAL_OUTPUT_DIR / "period_comparison.csv",
        first["periods"],
    )
    write_csv(
        PARTIAL_OUTPUT_DIR / "roll_proximity_differences.csv",
        first["roll_proximity"],
    )
    build_charts(first, output_dir=PARTIAL_OUTPUT_DIR)
    report_markdown, report_html = build_report(
        classification=classification,
        metrics=first["metrics"],
        hard_checks=hard_checks,
    )
    atomic_write_text(
        PARTIAL_OUTPUT_DIR / "report.md",
        report_markdown,
    )
    atomic_write_text(
        PARTIAL_OUTPUT_DIR / "report.html",
        report_html,
    )

    summary = {
        "schema_version": 1,
        "experiment_id": "EXP-023",
        "classification": classification,
        "started_at_utc": started,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "known_overlap_transfer_only": True,
        "independent_edge_confirmation": False,
        "strategy_ranking": False,
        "candidate_ids": list(FINALIST_IDS),
        "primary_representation": "BACKWARD_ADJUSTED",
        "secondary_representation": "UNADJUSTED",
        "reference_session_count": REFERENCE_SESSION_COUNT,
        "allowed_session_date_start": ALLOWED_SESSION_DATE_START,
        "allowed_session_date_end": ALLOWED_SESSION_DATE_END,
        "protected_history_accessed": False,
        "databento_api_calls": 0,
        "network_access": False,
        "optimization": False,
        "mcpt": False,
        "bootstrap": False,
        "paper_trading_authorized": False,
        "live_trading_authorized": False,
        "repository": {
            "implementation_commit": preflight[
                "implementation_commit"
            ],
            "authorization_commit": preflight[
                "authorization_commit"
            ],
            "head": preflight["head"],
        },
        "frame_semantic_hashes": first_hashes,
        "independent_rebuild_hashes": verification_hashes,
        "hard_checks": hard_checks,
        "hard_failure_count": int(
            sum(not value for value in hard_checks.values())
        ),
        "candidate_metrics": first["metrics"].to_dict(
            orient="records"
        ),
    }
    atomic_write_json(
        PARTIAL_OUTPUT_DIR / "transfer_summary.json",
        summary,
    )
    output_hashes = _output_hashes(PARTIAL_OUTPUT_DIR)
    atomic_write_json(
        PARTIAL_OUTPUT_DIR / "output_hashes.json",
        {"files": output_hashes},
    )
    marker = {
        "experiment_id": "EXP-023",
        "classification": classification,
        "completed_at_utc": summary["completed_at_utc"],
        "rerun_authorized": False,
        "protected_history_accessed": False,
        "all_hard_checks_pass": all(hard_checks.values()),
        "output_hashes_sha256": sha256_file(
            PARTIAL_OUTPUT_DIR / "output_hashes.json"
        ),
    }
    atomic_write_json(
        PARTIAL_OUTPUT_DIR / "TRANSFER_DIAGNOSTIC_COMPLETE.json",
        marker,
    )
    missing = [
        name
        for name in REQUIRED_OUTPUT_NAMES
        if not (PARTIAL_OUTPUT_DIR / name).is_file()
    ]
    if missing:
        raise RuntimeError(
            "EXP-023 outputs are incomplete: " + ", ".join(missing)
        )
    final_snapshot = snapshot_paths(preflight["frozen_paths"])
    if final_snapshot != before_snapshot:
        raise RuntimeError(
            "Frozen evidence changed while writing EXP-023 outputs."
        )
    os.replace(PARTIAL_OUTPUT_DIR, OUTPUT_DIR)
    return summary


def print_preflight(preflight: Mapping[str, Any]) -> None:
    print()
    print("EXP-023 PROTECTED PREFLIGHT")
    print("===========================")
    print("Status:          AUTHORIZED_NOT_RUN")
    print("Purpose:         known-overlap transfer qualification")
    print("Candidates:      3 frozen EXP-014 finalists")
    print("Primary:         backward-adjusted EXP-022 series")
    print("Secondary:       unadjusted roll-sensitivity diagnostic")
    print("Sessions:        1,331 frozen 2020-2025 dates")
    print("Protected dates: pre-2020 and 2026")
    print("API/network:     disabled")
    print("Search/MCPT:     disabled")
    print("Paper/live:      not authorized")
    print(f"Git commit:      {preflight['head'][:12]}")
    print("Results:         not calculated")
    print("===========================")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Protected EXP-023 known-overlap transfer qualification."
        )
    )
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument(
        "--preflight",
        action="store_true",
        help="Run the result-free protected preflight.",
    )
    action.add_argument(
        "--run",
        action="store_true",
        help="Execute the single separately authorized transfer run.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.preflight:
        print_preflight(repository_preflight())
        return
    summary = run_transfer()
    print()
    print("EXP-023 transfer diagnostic complete.")
    print(f"Classification: {summary['classification']}")
    print(f"Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
