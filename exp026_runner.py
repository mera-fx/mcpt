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
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd

from exp026_core import (
    ALL_CANDIDATE_IDS,
    BASE_ROUND_TRIP_COST_USD,
    CANDIDATE_SPEC_BY_ID,
    CONTROL_CANDIDATE_IDS,
    DECISION_COLUMNS,
    DEVELOPMENT_CANDIDATE_IDS,
    DIRECTION_ALL,
    METRIC_COLUMNS,
    REPRESENTATION_IDS,
    SOURCE_COLUMNS,
    TRADE_COLUMNS,
    annual_results,
    candidate_metrics,
    candidate_registry_frame,
    canonical_dataframe_sha256,
    canonical_object_sha256,
    cost_sensitivity,
    mirrored_trade_outcomes,
    monthly_results,
    parameter_stability,
    replay_candidates,
    select_phase_a_survivors,
    select_phase_b_finalists,
    validate_candidate_specs,
)
from exp026_preregistration import (
    EXPECTED_EXP026_PREREGISTRATION_SHA256,
    get_exp026_preregistration,
    validate_exp026_preregistration,
)
from exp026_statistics import (
    anchored_walk_forward,
    bootstrap_session_blocks,
    build_session_outcome_matrices,
    selection_aware_market_mcpt,
)


PROJECT_DIR = Path(__file__).resolve().parent
LOCKED_PREREGISTRATION_COMMIT = (
    "ce661c7785fa6d8d409378ee2ad63a00f0e0a9b9"
)

PREREGISTRATION_PATHS = (
    "exp026_preregistration.py",
    "research/EXP-026_preregistration.md",
    "tests/test_exp026_preregistration.py",
    "experiment_lifecycle.py",
    "tests/test_experiment_lifecycle.py",
)

IMPLEMENTATION_PATHS = (
    "exp026_core.py",
    "exp026_statistics.py",
    "exp026_runner.py",
    "exp026_implementation_preflight.py",
    "research/EXP-026_implementation_report.md",
    "tests/test_exp026_core.py",
    "tests/test_exp026_implementation.py",
)

EXP022_OUTPUT_DIR = (
    PROJECT_DIR
    / "results"
    / "EXP-022"
    / "selected_continuous_series"
)
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

OUTPUT_PARENT = PROJECT_DIR / "results" / "EXP-026"
PHASE_OUTPUT_DIRS = {
    "A": OUTPUT_PARENT / "phase_a_development",
    "B": OUTPUT_PARENT / "phase_b_internal_validation",
    "C": OUTPUT_PARENT / "phase_c_known_comparison",
}
PHASE_PARTIAL_DIRS = {
    phase: path.with_name(path.name + ".partial")
    for phase, path in PHASE_OUTPUT_DIRS.items()
}

PHASE_AUTHORIZATION_MODULES = {
    "A": "exp026_phase_a_authorization",
    "B": "exp026_phase_b_authorization",
    "C": "exp026_phase_c_authorization",
}
PHASE_AUTHORIZATION_PATHS = {
    "A": (
        "exp026_phase_a_authorization.py",
        "research/EXP-026_phase_a_authorization.md",
        "tests/test_exp026_phase_a_authorization.py",
    ),
    "B": (
        "exp026_phase_b_authorization.py",
        "research/EXP-026_phase_b_authorization.md",
        "tests/test_exp026_phase_b_authorization.py",
    ),
    "C": (
        "exp026_phase_c_authorization.py",
        "research/EXP-026_phase_c_authorization.md",
        "tests/test_exp026_phase_c_authorization.py",
    ),
}
PHASE_COMPLETION_MODULES = {
    "A": "exp026_phase_a_completion",
    "B": "exp026_phase_b_completion",
}
PHASE_COMPLETION_PATHS = {
    "A": (
        "exp026_phase_a_completion.py",
        "research/EXP-026_phase_a_completion.md",
        "tests/test_exp026_phase_a_completion.py",
    ),
    "B": (
        "exp026_phase_b_completion.py",
        "research/EXP-026_phase_b_completion.md",
        "tests/test_exp026_phase_b_completion.py",
    ),
}

PHASE_REQUIRED_OUTPUTS = {
    "A": (
        "development_summary.json",
        "candidate_registry.csv",
        "development_metrics.csv",
        "development_annual_results.csv",
        "phase_a_survivors.json",
        "output_hashes.json",
        "report.md",
        "PHASE_A_COMPLETE.json",
    ),
    "B": (
        "internal_validation_summary.json",
        "internal_validation_metrics.csv",
        "selected_finalists.json",
        "walk_forward_results.csv",
        "bootstrap_summary.csv",
        "mcpt_summary.json",
        "parameter_stability.csv",
        "output_hashes.json",
        "report.md",
        "report.html",
        "PHASE_B_COMPLETE.json",
    ),
    "C": (
        "known_comparison_summary.json",
        "known_comparison_metrics.csv",
        "annual_results.csv",
        "monthly_results.csv",
        "cost_sensitivity.csv",
        "representation_sensitivity.csv",
        "trade_distribution.csv",
        "drawdown_episodes.csv",
        "output_hashes.json",
        "report.md",
        "report.html",
        "PHASE_C_COMPLETE.json",
    ),
}

MINIMUM_FREE_BYTES = 4_000_000_000


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


def latest_commit(relative_path: str) -> str:
    value = run_git(
        "log",
        "-1",
        "--format=%H",
        "--",
        relative_path,
    ).stdout.strip()
    if not value:
        raise RuntimeError(
            f"No commit found for EXP-026 path: {relative_path}."
        )
    return value


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


def atomic_write_text(
    path: Path,
    value: str,
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
        return [
            _json_safe(current)
            for current in value
        ]
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer, int)) and not isinstance(
        value,
        bool,
    ):
        return int(value)
    if isinstance(value, (np.floating, float)):
        numeric = float(value)
        return (
            numeric
            if np.isfinite(numeric)
            else None
        )
    if isinstance(
        value,
        (pd.Timestamp, datetime, date),
    ):
        return value.isoformat()
    return value


def atomic_write_json(
    path: Path,
    value: Mapping[str, Any],
) -> None:
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


def write_csv(
    path: Path,
    frame: pd.DataFrame,
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
            f"Temporary CSV already exists: {temporary}"
        )
    frame.to_csv(
        temporary,
        index=False,
        quoting=csv.QUOTE_MINIMAL,
        lineterminator="\n",
    )
    os.replace(temporary, path)


def snapshot_paths(
    paths: Mapping[str, Path],
) -> dict[str, dict[str, Any]]:
    snapshot: dict[str, dict[str, Any]] = {}
    for name, path in paths.items():
        if not path.is_file():
            raise RuntimeError(
                f"Missing frozen EXP-026 evidence: {path}"
            )
        snapshot[name] = {
            "path": str(
                path.relative_to(PROJECT_DIR)
            ).replace("\\", "/"),
            "size_bytes": int(
                path.stat().st_size
            ),
            "sha256": sha256_file(path),
        }
    return snapshot


def verify_frozen_series_bytes() -> dict[str, Any]:
    validate_exp026_preregistration()
    preregistration = (
        get_exp026_preregistration()
    )
    frozen = preregistration["frozen_inputs"]
    series_records = {
        str(item["representation_id"]): item
        for item in frozen["series"]
    }
    snapshot = snapshot_paths(
        {
            representation_id: path
            for representation_id, path
            in REPRESENTATION_FILES.items()
        }
    )
    for representation_id in REPRESENTATION_IDS:
        expected = series_records[
            representation_id
        ]
        actual = snapshot[
            representation_id
        ]
        if (
            actual["size_bytes"]
            != int(expected["size_bytes"])
            or actual["sha256"]
            != str(expected["sha256"])
        ):
            raise RuntimeError(
                "Frozen EXP-022 series changed: "
                f"{representation_id}."
            )
    return {
        "preregistration": preregistration,
        "series_snapshot": snapshot,
    }


def inspect_parquet_metadata() -> dict[str, Any]:
    import pyarrow as pa
    import pyarrow.parquet as pq

    preregistration = (
        get_exp026_preregistration()
    )
    expected_rows = int(
        preregistration["frozen_inputs"][
            "series_row_count"
        ]
    )
    result: dict[str, Any] = {}
    for representation_id, path in (
        REPRESENTATION_FILES.items()
    ):
        parquet = pq.ParquetFile(path)
        schema = parquet.schema_arrow
        missing = sorted(
            set(SOURCE_COLUMNS).difference(
                schema.names
            )
        )
        if missing:
            raise RuntimeError(
                "EXP-026 Parquet schema is missing: "
                + ", ".join(missing)
            )
        if parquet.metadata.num_rows != expected_rows:
            raise RuntimeError(
                f"EXP-026 {representation_id} row count changed."
            )
        trading_date_type = schema.field(
            "trading_date"
        ).type
        if not pa.types.is_date32(
            trading_date_type
        ):
            raise RuntimeError(
                "EXP-026 requires date32 trading_date "
                "for protected predicate pushdown."
            )
        timestamp_type = schema.field(
            "ts_event"
        ).type
        if (
            not pa.types.is_timestamp(timestamp_type)
            or timestamp_type.tz != "UTC"
        ):
            raise RuntimeError(
                "EXP-026 requires UTC ts_event timestamps."
            )
        result[representation_id] = {
            "row_count": int(
                parquet.metadata.num_rows
            ),
            "row_group_count": int(
                parquet.metadata.num_row_groups
            ),
            "schema_names": tuple(schema.names),
            "trading_date_type": str(
                trading_date_type
            ),
            "ts_event_type": str(
                timestamp_type
            ),
        }
    return result


def load_permitted_ohlcv(
    path: Path,
    *,
    representation_id: str,
    allowed_session_start: str,
    allowed_session_end: str,
) -> pd.DataFrame:
    """Materialise only the registered trading-date interval.

    The Arrow predicate is attached to the scanner before a table is produced.
    Protected 2026 rows therefore are not returned to Python or converted into
    a pandas OHLCV frame.
    """

    import pyarrow as pa
    import pyarrow.dataset as ds

    if allowed_session_end > "2025-12-31":
        raise RuntimeError(
            "EXP-026 cannot materialise protected 2026 rows."
        )
    source = ds.dataset(
        path,
        format="parquet",
    )
    trading_date_type = source.schema.field(
        "trading_date"
    ).type
    if not pa.types.is_date32(
        trading_date_type
    ):
        raise RuntimeError(
            "EXP-026 protected loader requires date32 trading_date."
        )

    predicate = (
        ds.field("trading_date")
        >= pa.scalar(
            date.fromisoformat(
                allowed_session_start
            ),
            type=pa.date32(),
        )
    ) & (
        ds.field("trading_date")
        <= pa.scalar(
            date.fromisoformat(
                allowed_session_end
            ),
            type=pa.date32(),
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

    # The replay core performs a second independent bound check.
    from exp026_core import (
        normalise_source_frame,
    )

    return normalise_source_frame(
        frame,
        representation_id=representation_id,
        allowed_session_start=(
            allowed_session_start
        ),
        allowed_session_end=(
            allowed_session_end
        ),
    )


def _authorization_interface(
    phase: str,
) -> tuple[str, str]:
    lower = phase.lower()
    return (
        f"validate_exp026_phase_{lower}_authorization",
        f"get_exp026_phase_{lower}_authorization",
    )


def load_phase_authorization(
    phase: str,
) -> dict[str, Any]:
    phase = phase.upper()
    if phase not in PHASE_AUTHORIZATION_MODULES:
        raise ValueError(
            f"Unknown EXP-026 phase: {phase}."
        )
    module_name = PHASE_AUTHORIZATION_MODULES[
        phase
    ]
    module_path = PROJECT_DIR / (
        module_name + ".py"
    )
    if not module_path.is_file():
        raise RuntimeError(
            f"EXP-026 Phase {phase} is not authorized. "
            "The separate authorization module is absent."
        )
    module = importlib.import_module(
        module_name
    )
    validate_name, get_name = (
        _authorization_interface(phase)
    )
    validator = getattr(
        module,
        validate_name,
        None,
    )
    getter = getattr(
        module,
        get_name,
        None,
    )
    if validator is None or getter is None:
        raise RuntimeError(
            f"EXP-026 Phase {phase} authorization "
            "interface is incomplete."
        )
    validator()
    record = getter()
    if (
        record.get("experiment_id")
        != "EXP-026"
        or record.get("phase") != phase
        or record.get(
            "execution_authorized"
        ) is not True
        or record.get("one_time_run")
        is not True
        or record.get("maximum_runs") != 1
        or record.get(
            "preregistration_sha256"
        )
        != EXPECTED_EXP026_PREREGISTRATION_SHA256
        or record.get(
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
        raise RuntimeError(
            f"EXP-026 Phase {phase} authorization "
            "boundary changed."
        )
    implementation_commit = record.get(
        "locked_implementation_commit"
    )
    if (
        not isinstance(
            implementation_commit,
            str,
        )
        or len(implementation_commit) != 40
    ):
        raise RuntimeError(
            "EXP-026 locked implementation commit "
            "is invalid."
        )
    return record


def load_phase_completion(
    phase: str,
) -> dict[str, Any]:
    phase = phase.upper()
    if phase not in PHASE_COMPLETION_MODULES:
        raise ValueError(
            "Only EXP-026 Phase A or B has a "
            "downstream completion interface."
        )
    module_name = PHASE_COMPLETION_MODULES[
        phase
    ]
    module_path = PROJECT_DIR / (
        module_name + ".py"
    )
    if not module_path.is_file():
        raise RuntimeError(
            f"EXP-026 Phase {phase} completion "
            "record is absent."
        )
    module = importlib.import_module(
        module_name
    )
    lower = phase.lower()
    validator = getattr(
        module,
        f"validate_exp026_phase_{lower}_completion",
        None,
    )
    getter = getattr(
        module,
        f"get_exp026_phase_{lower}_completion",
        None,
    )
    if validator is None or getter is None:
        raise RuntimeError(
            f"EXP-026 Phase {phase} completion "
            "interface is incomplete."
        )
    validator()
    record = getter()
    if (
        record.get("experiment_id")
        != "EXP-026"
        or record.get("phase") != phase
        or record.get("completed") is not True
        or record.get(
            "protected_2026_accessed"
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
        raise RuntimeError(
            f"EXP-026 Phase {phase} completion "
            "boundary changed."
        )
    return record


def _phase_authorization_commit(
    phase: str,
) -> str:
    commits = {
        latest_commit(path)
        for path in PHASE_AUTHORIZATION_PATHS[
            phase
        ]
    }
    if len(commits) != 1:
        raise RuntimeError(
            f"EXP-026 Phase {phase} authorization "
            "files lack one shared commit."
        )
    return next(iter(commits))


def repository_state_preflight(
    phase: str,
) -> dict[str, Any]:
    phase = phase.upper()
    if phase not in {"A", "B", "C"}:
        raise ValueError(
            f"Unknown EXP-026 phase: {phase}."
        )
    if os.environ.get(
        "DATABENTO_API_KEY",
        "",
    ).strip():
        raise RuntimeError(
            "DATABENTO_API_KEY must not be set for EXP-026."
        )
    if run_git(
        "status",
        "--porcelain",
    ).stdout.strip():
        raise RuntimeError(
            "Repository must be clean before an EXP-026 run."
        )
    branch = run_git(
        "branch",
        "--show-current",
    ).stdout.strip()
    if branch != "main":
        raise RuntimeError(
            f"EXP-026 must run on main, found {branch!r}."
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
            "Local HEAD and origin/main must be aligned."
        )
    if run_git(
        "merge-base",
        "--is-ancestor",
        LOCKED_PREREGISTRATION_COMMIT,
        "HEAD",
        check=False,
    ).returncode != 0:
        raise RuntimeError(
            "Locked EXP-026 preregistration is not an ancestor."
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
            "Locked EXP-026 preregistration files changed."
        )

    authorization = load_phase_authorization(
        phase
    )
    implementation_commit = authorization[
        "locked_implementation_commit"
    ]
    if changed_paths(
        LOCKED_PREREGISTRATION_COMMIT,
        implementation_commit,
    ) != set(IMPLEMENTATION_PATHS):
        raise RuntimeError(
            "EXP-026 implementation scope changed."
        )
    authorization_commit = (
        _phase_authorization_commit(phase)
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
            "EXP-026 implementation/authorization "
            "ancestry is invalid."
        )

    if phase == "A":
        if authorization_commit != head:
            raise RuntimeError(
                "Phase A authorization commit must equal HEAD."
            )
    elif phase == "B":
        phase_a_completion = (
            load_phase_completion("A")
        )
        completion_commit = (
            phase_a_completion[
                "completion_commit"
            ]
        )
        if run_git(
            "merge-base",
            "--is-ancestor",
            completion_commit,
            authorization_commit,
            check=False,
        ).returncode != 0:
            raise RuntimeError(
                "Phase A completion must precede "
                "Phase B authorization."
            )
        if authorization_commit != head:
            raise RuntimeError(
                "Phase B authorization commit must equal HEAD."
            )
    else:
        phase_b_completion = (
            load_phase_completion("B")
        )
        completion_commit = (
            phase_b_completion[
                "completion_commit"
            ]
        )
        if run_git(
            "merge-base",
            "--is-ancestor",
            completion_commit,
            authorization_commit,
            check=False,
        ).returncode != 0:
            raise RuntimeError(
                "Phase B completion must precede "
                "Phase C authorization."
            )
        if authorization_commit != head:
            raise RuntimeError(
                "Phase C authorization commit must equal HEAD."
            )

    output_dir = PHASE_OUTPUT_DIRS[phase]
    partial_dir = PHASE_PARTIAL_DIRS[phase]
    if output_dir.exists() or partial_dir.exists():
        raise RuntimeError(
            f"EXP-026 Phase {phase} output already exists. "
            "Refusing to rerun."
        )

    for later_phase in (
        {"A": ("B", "C"), "B": ("C",), "C": ()}
    )[phase]:
        if (
            PHASE_OUTPUT_DIRS[
                later_phase
            ].exists()
            or PHASE_PARTIAL_DIRS[
                later_phase
            ].exists()
        ):
            raise RuntimeError(
                "A later EXP-026 phase already exists."
            )

    free_bytes = shutil.disk_usage(
        PROJECT_DIR
    ).free
    if free_bytes < MINIMUM_FREE_BYTES:
        raise RuntimeError(
            "EXP-026 requires at least "
            f"{MINIMUM_FREE_BYTES:,} free bytes; "
            f"found {free_bytes:,}."
        )

    verify = verify_frozen_series_bytes()
    metadata = inspect_parquet_metadata()
    return {
        "phase": phase,
        "branch": branch,
        "head": head,
        "origin_main": origin_main,
        "implementation_commit": (
            implementation_commit
        ),
        "authorization_commit": (
            authorization_commit
        ),
        "authorization": authorization,
        "free_bytes": int(free_bytes),
        **verify,
        "parquet_metadata": metadata,
    }


def _phase_a_computation(
    source: pd.DataFrame,
) -> dict[str, Any]:
    decisions, trades = replay_candidates(
        source,
        representation_id="BACKWARD_ADJUSTED",
        allowed_session_start="2010-06-07",
        allowed_session_end="2017-12-31",
    )
    metrics = candidate_metrics(
        trades,
        candidate_ids=ALL_CANDIDATE_IDS,
        period_start="2010-06-07",
        period_end="2017-12-31",
    )
    annual = annual_results(
        trades,
        candidate_ids=ALL_CANDIDATE_IDS,
        start_year=2010,
        end_year=2017,
    )
    survivors = select_phase_a_survivors(
        metrics,
        maximum_per_family=2,
    )
    return {
        "decisions": decisions,
        "trades": trades,
        "metrics": metrics,
        "annual": annual,
        "survivors": survivors,
        "registry": candidate_registry_frame(),
    }


def _phase_b_computation(
    source: pd.DataFrame,
    *,
    locked_survivor_ids: Sequence[str],
) -> dict[str, Any]:
    decisions, trades = replay_candidates(
        source,
        representation_id="BACKWARD_ADJUSTED",
        allowed_session_start="2010-06-07",
        allowed_session_end="2019-12-31",
    )
    validation_candidate_ids = tuple(
        locked_survivor_ids
    ) + CONTROL_CANDIDATE_IDS
    development_metrics = candidate_metrics(
        trades,
        candidate_ids=DEVELOPMENT_CANDIDATE_IDS,
        period_start="2010-06-07",
        period_end="2017-12-31",
    )
    validation_metrics = candidate_metrics(
        trades,
        candidate_ids=validation_candidate_ids,
        period_start="2018-01-01",
        period_end="2019-12-31",
    )
    validation_annual = annual_results(
        trades.loc[
            trades["session_date"].astype(
                str
            ).between(
                "2018-01-01",
                "2019-12-31",
            )
        ],
        candidate_ids=(
            DEVELOPMENT_CANDIDATE_IDS
        ),
        start_year=2018,
        end_year=2019,
    )
    finalists = select_phase_b_finalists(
        development_metrics,
        candidate_metrics(
            trades,
            candidate_ids=(
                DEVELOPMENT_CANDIDATE_IDS
            ),
            period_start="2018-01-01",
            period_end="2019-12-31",
        ),
        validation_annual,
        phase_a_candidate_ids=(
            locked_survivor_ids
        ),
        maximum_per_family=1,
    )
    finalist_ids = tuple(
        finalists["candidate_id"].astype(
            str
        )
    )
    walk_forward = anchored_walk_forward(
        trades,
    )
    stability = parameter_stability(
        candidate_metrics(
            trades,
            candidate_ids=(
                DEVELOPMENT_CANDIDATE_IDS
            ),
            period_start="2018-01-01",
            period_end="2019-12-31",
        )
    )

    development_trades = trades.loc[
        trades["candidate_id"].isin(
            DEVELOPMENT_CANDIDATE_IDS
        )
    ]
    mirrored = mirrored_trade_outcomes(
        source,
        development_trades,
        representation_id="BACKWARD_ADJUSTED",
        allowed_session_start="2010-06-07",
        allowed_session_end="2019-12-31",
    )
    session_dates = tuple(
        sorted(
            decisions["session_date"].unique()
        )
    )
    matrices = build_session_outcome_matrices(
        development_trades,
        mirrored,
        session_dates=session_dates,
        candidate_ids=(
            DEVELOPMENT_CANDIDATE_IDS
        ),
    )
    mcpt_summary, mcpt_distribution = (
        selection_aware_market_mcpt(
            matrices,
            permutations=1_000,
            random_seed=26_026,
        )
    )

    validation_dates = tuple(
        value
        for value in session_dates
        if "2018-01-01"
        <= value
        <= "2019-12-31"
    )
    validation_trades = trades.loc[
        trades["session_date"].astype(
            str
        ).between(
            "2018-01-01",
            "2019-12-31",
        )
    ]
    bootstrap = bootstrap_session_blocks(
        validation_trades,
        candidate_ids=finalist_ids,
        session_dates=validation_dates,
        resamples=10_000,
        random_seed=26_027,
        confidence_level=0.95,
    )
    return {
        "decisions": decisions,
        "trades": trades,
        "development_metrics": (
            development_metrics
        ),
        "validation_metrics": (
            validation_metrics
        ),
        "validation_annual": (
            validation_annual
        ),
        "finalists": finalists,
        "walk_forward": walk_forward,
        "bootstrap": bootstrap,
        "mcpt_summary": mcpt_summary,
        "mcpt_distribution": (
            mcpt_distribution
        ),
        "stability": stability,
        "mirrored": mirrored,
    }


def _trade_distribution(
    trades: pd.DataFrame,
    *,
    candidate_ids: Iterable[str],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for candidate_id in candidate_ids:
        current = trades.loc[
            trades["candidate_id"]
            == candidate_id
        ].sort_values(
            ["session_date", "entry_timestamp_utc"],
            kind="stable",
        )
        values = current[
            "net_pnl_usd"
        ].to_numpy(dtype=float)
        positive_total = float(
            values[values > 0].sum()
        )
        sorted_positive = np.sort(
            values[values > 0]
        )[::-1]
        for count in (1, 5, 10):
            share = (
                float(
                    sorted_positive[:count].sum()
                    / positive_total
                )
                if positive_total > 0
                else np.nan
            )
            rows.append(
                {
                    "candidate_id": candidate_id,
                    "measure": (
                        f"top_{count}_trade_profit_share"
                    ),
                    "value": share,
                }
            )
        rows.extend(
            [
                {
                    "candidate_id": candidate_id,
                    "measure": "p05_net_pnl_usd",
                    "value": (
                        float(np.quantile(values, 0.05))
                        if len(values)
                        else np.nan
                    ),
                },
                {
                    "candidate_id": candidate_id,
                    "measure": "median_net_pnl_usd",
                    "value": (
                        float(np.median(values))
                        if len(values)
                        else np.nan
                    ),
                },
                {
                    "candidate_id": candidate_id,
                    "measure": "p95_net_pnl_usd",
                    "value": (
                        float(np.quantile(values, 0.95))
                        if len(values)
                        else np.nan
                    ),
                },
            ]
        )
    return pd.DataFrame(rows)


def _drawdown_episodes(
    trades: pd.DataFrame,
    *,
    candidate_ids: Iterable[str],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for candidate_id in candidate_ids:
        current = trades.loc[
            trades["candidate_id"]
            == candidate_id
        ].sort_values(
            ["session_date", "entry_timestamp_utc"],
            kind="stable",
        )
        if current.empty:
            continue
        values = current[
            "net_pnl_usd"
        ].to_numpy(dtype=float)
        equity = np.cumsum(values)
        running = np.maximum.accumulate(
            np.concatenate(([0.0], equity))
        )[1:]
        drawdown = equity - running
        underwater = drawdown < 0
        start: int | None = None
        episode_number = 0
        for index, active in enumerate(
            underwater
        ):
            if active and start is None:
                start = index
            if (
                start is not None
                and (
                    not active
                    or index == len(underwater) - 1
                )
            ):
                end = (
                    index - 1
                    if not active
                    else index
                )
                episode_number += 1
                segment = drawdown[
                    start : end + 1
                ]
                trough_offset = int(
                    np.argmin(segment)
                )
                trough = start + trough_offset
                rows.append(
                    {
                        "candidate_id": candidate_id,
                        "episode_number": int(
                            episode_number
                        ),
                        "start_session_date": str(
                            current.iloc[start][
                                "session_date"
                            ]
                        ),
                        "trough_session_date": str(
                            current.iloc[trough][
                                "session_date"
                            ]
                        ),
                        "end_session_date": str(
                            current.iloc[end][
                                "session_date"
                            ]
                        ),
                        "depth_usd": float(
                            segment.min()
                        ),
                        "duration_trades": int(
                            end - start + 1
                        ),
                        "recovered": bool(
                            not active
                        ),
                    }
                )
                start = None
    return pd.DataFrame(rows)


def _phase_c_computation(
    backward_source: pd.DataFrame,
    unadjusted_source: pd.DataFrame,
    *,
    finalist_ids: Sequence[str],
) -> dict[str, Any]:
    candidate_ids = tuple(
        finalist_ids
    ) + CONTROL_CANDIDATE_IDS
    backward_decisions, backward_trades = (
        replay_candidates(
            backward_source,
            representation_id=(
                "BACKWARD_ADJUSTED"
            ),
            allowed_session_start=(
                "2019-12-01"
            ),
            allowed_session_end=(
                "2025-12-31"
            ),
            candidate_ids=candidate_ids,
        )
    )
    unadjusted_decisions, unadjusted_trades = (
        replay_candidates(
            unadjusted_source,
            representation_id="UNADJUSTED",
            allowed_session_start=(
                "2019-12-01"
            ),
            allowed_session_end=(
                "2025-12-31"
            ),
            candidate_ids=candidate_ids,
        )
    )

    period_start = "2020-01-03"
    period_end = "2025-12-31"
    backward_trades = backward_trades.loc[
        backward_trades[
            "session_date"
        ].astype(str).between(
            period_start,
            period_end,
        )
    ].reset_index(drop=True)
    unadjusted_trades = unadjusted_trades.loc[
        unadjusted_trades[
            "session_date"
        ].astype(str).between(
            period_start,
            period_end,
        )
    ].reset_index(drop=True)

    metrics = candidate_metrics(
        backward_trades,
        candidate_ids=candidate_ids,
        period_start=period_start,
        period_end=period_end,
    )
    annual = annual_results(
        backward_trades,
        candidate_ids=candidate_ids,
        start_year=2020,
        end_year=2025,
    )
    monthly = monthly_results(
        backward_trades,
        candidate_ids=candidate_ids,
        start_month="2020-01",
        end_month="2025-12",
    )
    costs = cost_sensitivity(
        backward_trades,
        candidate_ids=candidate_ids,
        period_start=period_start,
        period_end=period_end,
    )
    unadjusted_metrics = candidate_metrics(
        unadjusted_trades,
        candidate_ids=candidate_ids,
        period_start=period_start,
        period_end=period_end,
    )
    primary_all = metrics.loc[
        metrics["segment"] == DIRECTION_ALL
    ]
    secondary_all = unadjusted_metrics.loc[
        unadjusted_metrics["segment"]
        == DIRECTION_ALL
    ]
    sensitivity = primary_all.merge(
        secondary_all,
        on=[
            "candidate_id",
            "family_id",
            "candidate_role",
            "segment",
        ],
        suffixes=(
            "_backward_adjusted",
            "_unadjusted",
        ),
        how="outer",
        validate="one_to_one",
    )
    distribution = _trade_distribution(
        backward_trades,
        candidate_ids=candidate_ids,
    )
    drawdowns = _drawdown_episodes(
        backward_trades,
        candidate_ids=candidate_ids,
    )
    return {
        "backward_decisions": (
            backward_decisions
        ),
        "unadjusted_decisions": (
            unadjusted_decisions
        ),
        "backward_trades": backward_trades,
        "unadjusted_trades": (
            unadjusted_trades
        ),
        "metrics": metrics,
        "annual": annual,
        "monthly": monthly,
        "costs": costs,
        "sensitivity": sensitivity,
        "distribution": distribution,
        "drawdowns": drawdowns,
    }


def _frame_hashes(
    frames: Mapping[str, pd.DataFrame],
) -> dict[str, str]:
    return {
        name: canonical_dataframe_sha256(
            frame
        )
        for name, frame in frames.items()
    }


def _build_equity_assets(
    trades: pd.DataFrame,
    *,
    candidate_ids: Sequence[str],
    output_dir: Path,
) -> tuple[str, str]:
    import matplotlib.pyplot as plt

    asset_dir = output_dir / "assets"
    asset_dir.mkdir(
        parents=True,
        exist_ok=True,
    )
    equity_path = asset_dir / (
        "equity_curves.png"
    )
    drawdown_path = asset_dir / (
        "drawdown_curves.png"
    )

    figure = plt.figure(
        figsize=(14, 7),
        facecolor="white",
    )
    axis = figure.add_subplot(111)
    for candidate_id in candidate_ids:
        current = trades.loc[
            trades["candidate_id"]
            == candidate_id
        ].sort_values(
            ["session_date", "entry_timestamp_utc"],
            kind="stable",
        )
        if current.empty:
            continue
        equity = current[
            "net_pnl_usd"
        ].cumsum()
        axis.plot(
            pd.to_datetime(
                current["session_date"]
            ),
            equity,
            label=candidate_id,
        )
    axis.set_title("Total equity by candidate")
    axis.set_xlabel("Session date")
    axis.set_ylabel("Cumulative net P&L (USD)")
    axis.grid(True, alpha=0.25)
    axis.legend(
        loc="best",
        fontsize=8,
    )
    figure.tight_layout()
    figure.savefig(
        equity_path,
        dpi=150,
        facecolor="white",
        transparent=False,
    )
    plt.close(figure)

    figure = plt.figure(
        figsize=(14, 7),
        facecolor="white",
    )
    axis = figure.add_subplot(111)
    for candidate_id in candidate_ids:
        current = trades.loc[
            trades["candidate_id"]
            == candidate_id
        ].sort_values(
            ["session_date", "entry_timestamp_utc"],
            kind="stable",
        )
        if current.empty:
            continue
        equity = current[
            "net_pnl_usd"
        ].cumsum().to_numpy(dtype=float)
        running = np.maximum.accumulate(
            np.concatenate(([0.0], equity))
        )[1:]
        drawdown = equity - running
        axis.plot(
            pd.to_datetime(
                current["session_date"]
            ),
            drawdown,
            label=candidate_id,
        )
    axis.set_title("Drawdown by candidate")
    axis.set_xlabel("Session date")
    axis.set_ylabel("Drawdown (USD)")
    axis.grid(True, alpha=0.25)
    axis.legend(
        loc="best",
        fontsize=8,
    )
    figure.tight_layout()
    figure.savefig(
        drawdown_path,
        dpi=150,
        facecolor="white",
        transparent=False,
    )
    plt.close(figure)

    return (
        "assets/equity_curves.png",
        "assets/drawdown_curves.png",
    )


def _metrics_markdown(
    metrics: pd.DataFrame,
) -> str:
    display_columns = [
        "candidate_id",
        "segment",
        "completed_trades",
        "net_profit_usd",
        "trade_profit_factor",
        "win_rate",
        "maximum_drawdown_usd",
        "net_profit_to_drawdown",
        "maximum_consecutive_losses",
    ]
    return metrics.loc[
        :,
        display_columns,
    ].to_markdown(index=False)


def _html_table(
    frame: pd.DataFrame,
    *,
    maximum_rows: int = 300,
) -> str:
    current = frame.head(
        maximum_rows
    ).copy()
    return current.to_html(
        index=False,
        border=0,
        classes="data-table",
        float_format=lambda value: (
            f"{value:,.6f}"
        ),
    )


def _phase_report_text(
    *,
    phase: str,
    title: str,
    metrics: pd.DataFrame,
    selection: Sequence[str],
    notes: Sequence[str],
) -> str:
    lines = [
        f"# {title}",
        "",
        f"**Phase:** {phase}",
        "",
        "**Protected 2026 market values materialised:** No",
        "",
        "**Databento API calls:** 0",
        "",
        "## Selection",
        "",
        (
            ", ".join(selection)
            if selection
            else "No candidate selected."
        ),
        "",
        "## All / Long / Short metrics",
        "",
        _metrics_markdown(metrics),
        "",
        "## Interpretation notes",
        "",
    ]
    lines.extend(
        f"- {value}"
        for value in notes
    )
    return "\n".join(lines) + "\n"


def _phase_report_html(
    *,
    title: str,
    metrics: pd.DataFrame,
    selection: Sequence[str],
    notes: Sequence[str],
    include_assets: bool,
) -> str:
    images = ""
    if include_assets:
        images = """
<section>
  <h2>Total equity</h2>
  <img src="assets/equity_curves.png" alt="Total equity curves">
</section>
<section>
  <h2>Drawdown</h2>
  <img src="assets/drawdown_curves.png" alt="Drawdown curves">
</section>
"""
    note_items = "".join(
        f"<li>{escape(value)}</li>"
        for value in notes
    )
    selection_text = (
        ", ".join(selection)
        if selection
        else "No candidate selected."
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{escape(title)}</title>
<style>
body {{
  font-family: Arial, sans-serif;
  margin: 0 auto;
  max-width: 1500px;
  padding: 28px;
  color: #1f2937;
  background: #ffffff;
}}
section {{
  width: 100%;
  margin: 0 0 34px 0;
}}
img {{
  width: 100%;
  height: auto;
  display: block;
  background: #ffffff;
}}
.data-table {{
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}}
.data-table th, .data-table td {{
  border: 1px solid #d1d5db;
  padding: 7px;
  text-align: right;
}}
.data-table th:first-child,
.data-table td:first-child {{
  text-align: left;
}}
.status {{
  font-weight: 700;
}}
.adverse {{
  color: #b91c1c;
}}
</style>
</head>
<body>
<h1>{escape(title)}</h1>
<section>
  <p><strong>Selection:</strong> {escape(selection_text)}</p>
  <p><strong>Protected 2026 accessed:</strong> No</p>
  <p><strong>Databento API calls:</strong> 0</p>
</section>
<section>
  <h2>All / Long / Short metrics</h2>
  {_html_table(metrics)}
</section>
{images}
<section>
  <h2>Interpretation notes</h2>
  <ul>{note_items}</ul>
</section>
</body>
</html>
"""


def _write_output_manifest(
    output_dir: Path,
    *,
    marker_name: str,
    phase: str,
    summary: Mapping[str, Any],
) -> None:
    files = {
        str(path.relative_to(output_dir)).replace(
            "\\",
            "/",
        ): {
            "size_bytes": int(
                path.stat().st_size
            ),
            "sha256": sha256_file(path),
        }
        for path in sorted(
            output_dir.rglob("*")
        )
        if path.is_file()
        and path.name not in {
            "output_hashes.json",
            marker_name,
        }
    }
    manifest = {
        "experiment_id": "EXP-026",
        "phase": phase,
        "files": files,
    }
    atomic_write_json(
        output_dir / "output_hashes.json",
        manifest,
    )
    marker = {
        "experiment_id": "EXP-026",
        "phase": phase,
        "completed": True,
        "completed_at_utc": (
            datetime.now(timezone.utc).isoformat()
        ),
        "output_manifest_sha256": sha256_file(
            output_dir / "output_hashes.json"
        ),
        "required_output_names": (
            PHASE_REQUIRED_OUTPUTS[phase]
        ),
        "protected_2026_accessed": False,
        "databento_api_calls": 0,
        "network_access": False,
        "paper_trading_authorized": False,
        "live_trading_authorized": False,
        "summary": dict(summary),
    }
    atomic_write_json(
        output_dir / marker_name,
        marker,
    )


def _verify_required_outputs(
    output_dir: Path,
    *,
    phase: str,
) -> None:
    missing = [
        name
        for name in PHASE_REQUIRED_OUTPUTS[
            phase
        ]
        if not (
            output_dir / name
        ).is_file()
    ]
    if missing:
        raise RuntimeError(
            f"EXP-026 Phase {phase} outputs are missing: "
            + ", ".join(missing)
        )


def run_phase_a() -> dict[str, Any]:
    preflight = repository_state_preflight(
        "A"
    )
    source = load_permitted_ohlcv(
        REPRESENTATION_FILES[
            "BACKWARD_ADJUSTED"
        ],
        representation_id="BACKWARD_ADJUSTED",
        allowed_session_start="2010-06-07",
        allowed_session_end="2017-12-31",
    )
    first = _phase_a_computation(source)
    second = _phase_a_computation(source)

    frame_names = (
        "decisions",
        "trades",
        "metrics",
        "annual",
        "survivors",
        "registry",
    )
    first_hashes = _frame_hashes(
        {
            name: first[name]
            for name in frame_names
        }
    )
    second_hashes = _frame_hashes(
        {
            name: second[name]
            for name in frame_names
        }
    )
    if first_hashes != second_hashes:
        raise RuntimeError(
            "EXP-026 Phase A independent rebuild differed."
        )

    output_dir = PHASE_PARTIAL_DIRS["A"]
    output_dir.mkdir(
        parents=True,
        exist_ok=False,
    )
    try:
        write_csv(
            output_dir / "candidate_registry.csv",
            first["registry"],
        )
        write_csv(
            output_dir / "development_metrics.csv",
            first["metrics"],
        )
        write_csv(
            output_dir
            / "development_annual_results.csv",
            first["annual"],
        )
        survivor_ids = tuple(
            first["survivors"][
                "candidate_id"
            ].astype(str)
        )
        atomic_write_json(
            output_dir
            / "phase_a_survivors.json",
            {
                "experiment_id": "EXP-026",
                "phase": "A",
                "candidate_ids": survivor_ids,
                "maximum_per_family": 2,
                "selection_rank": (
                    "profit_factor",
                    "net_profit_to_drawdown",
                    "net_profit",
                    "completed_trades",
                    "candidate_id",
                ),
                "no_minimum_profit_gate": True,
                "protected_2026_accessed": False,
            },
        )
        summary = {
            "source_session_start": (
                "2010-06-07"
            ),
            "source_session_end": (
                "2017-12-31"
            ),
            "reported_candidate_count": 24,
            "development_candidate_count": 22,
            "control_candidate_count": 2,
            "decision_rows": int(
                len(first["decisions"])
            ),
            "trade_rows": int(
                len(first["trades"])
            ),
            "survivor_count": int(
                len(survivor_ids)
            ),
            "survivor_ids": survivor_ids,
            "independent_rebuild": True,
            "protected_2026_accessed": False,
            "databento_api_calls": 0,
        }
        atomic_write_json(
            output_dir
            / "development_summary.json",
            summary,
        )
        atomic_write_text(
            output_dir / "report.md",
            _phase_report_text(
                phase="A",
                title=(
                    "EXP-026 Phase A Development"
                ),
                metrics=first["metrics"],
                selection=survivor_ids,
                notes=(
                    "Selection is exploratory and "
                    "does not validate an edge.",
                    "The two ORB controls were "
                    "reported but were not eligible "
                    "for selection.",
                    "Phase B remains inaccessible "
                    "until a separate Phase A "
                    "completion record and Phase B "
                    "authorization are committed.",
                ),
            ),
        )
        _write_output_manifest(
            output_dir,
            marker_name=(
                "PHASE_A_COMPLETE.json"
            ),
            phase="A",
            summary=summary,
        )
        _verify_required_outputs(
            output_dir,
            phase="A",
        )
        os.replace(
            output_dir,
            PHASE_OUTPUT_DIRS["A"],
        )
    except Exception:
        raise

    return {
        **preflight,
        **summary,
        "output_dir": str(
            PHASE_OUTPUT_DIRS["A"]
        ),
    }


def _locked_phase_a_survivors(
    completion: Mapping[str, Any],
) -> tuple[str, ...]:
    values = tuple(
        str(value)
        for value in completion[
            "survivor_candidate_ids"
        ]
    )
    if (
        len(values) > 6
        or len(set(values)) != len(values)
        or not set(values).issubset(
            DEVELOPMENT_CANDIDATE_IDS
        )
    ):
        raise RuntimeError(
            "Locked Phase A survivor population is invalid."
        )
    family_counts = {
        family_id: sum(
            CANDIDATE_SPEC_BY_ID[
                candidate_id
            ].family_id == family_id
            for candidate_id in values
        )
        for family_id in (
            "gap_fade",
            "premarket_momentum_continuation",
            "opening_drive_continuation",
        )
    }
    if any(
        count > 2
        for count in family_counts.values()
    ):
        raise RuntimeError(
            "Locked Phase A survivors exceed two per family."
        )
    return values


def run_phase_b() -> dict[str, Any]:
    preflight = repository_state_preflight(
        "B"
    )
    phase_a_completion = (
        load_phase_completion("A")
    )
    survivor_ids = (
        _locked_phase_a_survivors(
            phase_a_completion
        )
    )
    source = load_permitted_ohlcv(
        REPRESENTATION_FILES[
            "BACKWARD_ADJUSTED"
        ],
        representation_id="BACKWARD_ADJUSTED",
        allowed_session_start="2010-06-07",
        allowed_session_end="2019-12-31",
    )
    first = _phase_b_computation(
        source,
        locked_survivor_ids=survivor_ids,
    )
    second = _phase_b_computation(
        source,
        locked_survivor_ids=survivor_ids,
    )

    frame_names = (
        "decisions",
        "trades",
        "development_metrics",
        "validation_metrics",
        "validation_annual",
        "finalists",
        "walk_forward",
        "bootstrap",
        "mcpt_distribution",
        "stability",
        "mirrored",
    )
    first_hashes = _frame_hashes(
        {
            name: first[name]
            for name in frame_names
        }
    )
    second_hashes = _frame_hashes(
        {
            name: second[name]
            for name in frame_names
        }
    )
    if (
        first_hashes != second_hashes
        or canonical_object_sha256(
            first["mcpt_summary"]
        )
        != canonical_object_sha256(
            second["mcpt_summary"]
        )
    ):
        raise RuntimeError(
            "EXP-026 Phase B independent rebuild differed."
        )

    output_dir = PHASE_PARTIAL_DIRS["B"]
    output_dir.mkdir(
        parents=True,
        exist_ok=False,
    )
    try:
        finalist_ids = tuple(
            first["finalists"][
                "candidate_id"
            ].astype(str)
        )
        write_csv(
            output_dir
            / "internal_validation_metrics.csv",
            first["validation_metrics"],
        )
        write_csv(
            output_dir
            / "walk_forward_results.csv",
            first["walk_forward"],
        )
        write_csv(
            output_dir
            / "bootstrap_summary.csv",
            first["bootstrap"],
        )
        write_csv(
            output_dir
            / "parameter_stability.csv",
            first["stability"],
        )
        atomic_write_json(
            output_dir
            / "selected_finalists.json",
            {
                "experiment_id": "EXP-026",
                "phase": "B",
                "candidate_ids": finalist_ids,
                "maximum_per_family": 1,
                "phase_a_survivors": (
                    survivor_ids
                ),
                "known_2020_2025_not_used_for_selection": True,
                "protected_2026_accessed": False,
            },
        )
        atomic_write_json(
            output_dir
            / "mcpt_summary.json",
            first["mcpt_summary"],
        )
        summary = {
            "internal_validation_start": (
                "2018-01-01"
            ),
            "internal_validation_end": (
                "2019-12-31"
            ),
            "phase_a_survivor_ids": (
                survivor_ids
            ),
            "finalist_count": int(
                len(finalist_ids)
            ),
            "finalist_ids": finalist_ids,
            "walk_forward_fold_count": 6,
            "bootstrap_resamples": 10_000,
            "mcpt_permutations": 1_000,
            "mcpt_plus_one_p_value": (
                first["mcpt_summary"][
                    "plus_one_p_value"
                ]
            ),
            "independent_rebuild": True,
            "known_2020_2025_accessed": False,
            "protected_2026_accessed": False,
            "databento_api_calls": 0,
        }
        atomic_write_json(
            output_dir
            / "internal_validation_summary.json",
            summary,
        )
        _build_equity_assets(
            first["trades"].loc[
                first["trades"][
                    "candidate_id"
                ].isin(
                    finalist_ids
                    + CONTROL_CANDIDATE_IDS
                )
                & first["trades"][
                    "session_date"
                ].astype(str).between(
                    "2018-01-01",
                    "2019-12-31",
                )
            ],
            candidate_ids=(
                finalist_ids
                + CONTROL_CANDIDATE_IDS
            ),
            output_dir=output_dir,
        )
        notes = (
            "Selection-aware MCPT uses one "
            "session-shared post-entry path sign "
            "choice across all 22 candidates.",
            "The null is conditional on the "
            "entry-known setup schedule.",
            "Bootstrap, walk-forward and MCPT "
            "are context measurements and are "
            "not pass/fail gates.",
            "The known 2020-2025 comparison "
            "period remains inaccessible until "
            "Phase B completion and Phase C "
            "authorization are committed.",
        )
        atomic_write_text(
            output_dir / "report.md",
            _phase_report_text(
                phase="B",
                title=(
                    "EXP-026 Phase B "
                    "Internal Validation"
                ),
                metrics=first[
                    "validation_metrics"
                ],
                selection=finalist_ids,
                notes=notes,
            ),
        )
        atomic_write_text(
            output_dir / "report.html",
            _phase_report_html(
                title=(
                    "EXP-026 Phase B "
                    "Internal Validation"
                ),
                metrics=first[
                    "validation_metrics"
                ],
                selection=finalist_ids,
                notes=notes,
                include_assets=True,
            ),
        )
        _write_output_manifest(
            output_dir,
            marker_name=(
                "PHASE_B_COMPLETE.json"
            ),
            phase="B",
            summary=summary,
        )
        _verify_required_outputs(
            output_dir,
            phase="B",
        )
        os.replace(
            output_dir,
            PHASE_OUTPUT_DIRS["B"],
        )
    except Exception:
        raise

    return {
        **preflight,
        **summary,
        "output_dir": str(
            PHASE_OUTPUT_DIRS["B"]
        ),
    }


def _locked_phase_b_finalists(
    completion: Mapping[str, Any],
) -> tuple[str, ...]:
    values = tuple(
        str(value)
        for value in completion[
            "finalist_candidate_ids"
        ]
    )
    if (
        len(values) > 3
        or len(set(values)) != len(values)
        or not set(values).issubset(
            DEVELOPMENT_CANDIDATE_IDS
        )
    ):
        raise RuntimeError(
            "Locked Phase B finalist population is invalid."
        )
    family_counts = {
        family_id: sum(
            CANDIDATE_SPEC_BY_ID[
                candidate_id
            ].family_id == family_id
            for candidate_id in values
        )
        for family_id in (
            "gap_fade",
            "premarket_momentum_continuation",
            "opening_drive_continuation",
        )
    }
    if any(
        count > 1
        for count in family_counts.values()
    ):
        raise RuntimeError(
            "Locked Phase B finalists exceed one per family."
        )
    return values


def run_phase_c() -> dict[str, Any]:
    preflight = repository_state_preflight(
        "C"
    )
    phase_b_completion = (
        load_phase_completion("B")
    )
    finalist_ids = (
        _locked_phase_b_finalists(
            phase_b_completion
        )
    )
    backward_source = load_permitted_ohlcv(
        REPRESENTATION_FILES[
            "BACKWARD_ADJUSTED"
        ],
        representation_id="BACKWARD_ADJUSTED",
        allowed_session_start="2019-12-01",
        allowed_session_end="2025-12-31",
    )
    unadjusted_source = load_permitted_ohlcv(
        REPRESENTATION_FILES[
            "UNADJUSTED"
        ],
        representation_id="UNADJUSTED",
        allowed_session_start="2019-12-01",
        allowed_session_end="2025-12-31",
    )
    first = _phase_c_computation(
        backward_source,
        unadjusted_source,
        finalist_ids=finalist_ids,
    )
    second = _phase_c_computation(
        backward_source,
        unadjusted_source,
        finalist_ids=finalist_ids,
    )
    frame_names = tuple(first)
    first_hashes = _frame_hashes(
        {
            name: first[name]
            for name in frame_names
        }
    )
    second_hashes = _frame_hashes(
        {
            name: second[name]
            for name in frame_names
        }
    )
    if first_hashes != second_hashes:
        raise RuntimeError(
            "EXP-026 Phase C independent rebuild differed."
        )

    output_dir = PHASE_PARTIAL_DIRS["C"]
    output_dir.mkdir(
        parents=True,
        exist_ok=False,
    )
    try:
        write_csv(
            output_dir
            / "known_comparison_metrics.csv",
            first["metrics"],
        )
        write_csv(
            output_dir / "annual_results.csv",
            first["annual"],
        )
        write_csv(
            output_dir / "monthly_results.csv",
            first["monthly"],
        )
        write_csv(
            output_dir
            / "cost_sensitivity.csv",
            first["costs"],
        )
        write_csv(
            output_dir
            / "representation_sensitivity.csv",
            first["sensitivity"],
        )
        write_csv(
            output_dir
            / "trade_distribution.csv",
            first["distribution"],
        )
        write_csv(
            output_dir
            / "drawdown_episodes.csv",
            first["drawdowns"],
        )
        candidate_ids = (
            finalist_ids
            + CONTROL_CANDIDATE_IDS
        )
        summary = {
            "known_comparison_start": (
                "2020-01-03"
            ),
            "known_comparison_end": (
                "2025-12-31"
            ),
            "finalist_ids": finalist_ids,
            "control_ids": (
                CONTROL_CANDIDATE_IDS
            ),
            "candidate_reselection": False,
            "parameter_changes": False,
            "known_period_is_confirmation": False,
            "independent_rebuild": True,
            "protected_2026_accessed": False,
            "databento_api_calls": 0,
        }
        atomic_write_json(
            output_dir
            / "known_comparison_summary.json",
            summary,
        )
        _build_equity_assets(
            first["backward_trades"],
            candidate_ids=candidate_ids,
            output_dir=output_dir,
        )
        notes = (
            "Finalist identity was frozen before "
            "the known 2020-2025 period was read.",
            "The period is a disclosed comparison, "
            "not independent confirmation.",
            "The unadjusted representation is a "
            "post-selection sensitivity only and "
            "cannot alter finalist identity.",
            "The protected 2026 confirmation "
            "remains inaccessible to EXP-026.",
        )
        atomic_write_text(
            output_dir / "report.md",
            _phase_report_text(
                phase="C",
                title=(
                    "EXP-026 Phase C "
                    "Known 2020-2025 Comparison"
                ),
                metrics=first["metrics"],
                selection=finalist_ids,
                notes=notes,
            ),
        )
        atomic_write_text(
            output_dir / "report.html",
            _phase_report_html(
                title=(
                    "EXP-026 Phase C "
                    "Known 2020-2025 Comparison"
                ),
                metrics=first["metrics"],
                selection=finalist_ids,
                notes=notes,
                include_assets=True,
            ),
        )
        _write_output_manifest(
            output_dir,
            marker_name=(
                "PHASE_C_COMPLETE.json"
            ),
            phase="C",
            summary=summary,
        )
        _verify_required_outputs(
            output_dir,
            phase="C",
        )
        os.replace(
            output_dir,
            PHASE_OUTPUT_DIRS["C"],
        )
    except Exception:
        raise

    return {
        **preflight,
        **summary,
        "output_dir": str(
            PHASE_OUTPUT_DIRS["C"]
        ),
    }


def run_phase(
    phase: str,
) -> dict[str, Any]:
    phase = phase.upper()
    if phase == "A":
        return run_phase_a()
    if phase == "B":
        return run_phase_b()
    if phase == "C":
        return run_phase_c()
    raise ValueError(
        f"Unknown EXP-026 phase: {phase}."
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run one separately authorized EXP-026 phase."
        )
    )
    parser.add_argument(
        "--phase",
        required=True,
        choices=("A", "B", "C"),
    )
    arguments = parser.parse_args()
    result = run_phase(
        arguments.phase
    )
    phase = arguments.phase.upper()
    print(
        f"EXP-026 PHASE {phase} COMPLETE"
    )
    print(
        "Implementation commit: ",
        result["implementation_commit"],
    )
    print(
        "Authorization commit:  ",
        result["authorization_commit"],
    )
    print(
        "Output directory:      ",
        result["output_dir"],
    )
    print(
        "Protected 2026 accessed:",
        False,
    )
    print(
        "Databento API calls:    ",
        0,
    )
    print(
        "Paper/live trading:     ",
        False,
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(
            f"ERROR: {exc}",
            file=__import__("sys").stderr,
        )
        raise SystemExit(1)
