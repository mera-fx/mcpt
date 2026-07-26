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

from exp024_attribution_core import (
    CANDIDATE_RULES,
    PRIMARY_REPRESENTATION,
    SECONDARY_REPRESENTATION,
    SOURCE_IDS,
    build_attribution,
    build_candidate_features,
    canonical_dataframe_sha256,
    compare_quantower_aggregation,
    final_classification,
    normalise_restricted_rows,
    raw_component_differences,
    select_frozen_mismatch_population,
    validate_candidate_rules,
    validate_feature_rows,
)
from exp024_preregistration import (
    CANDIDATE_IDS,
    EXPECTED_EXP024_PREREGISTRATION_SHA256,
    get_exp024_preregistration,
    validate_exp024_preregistration,
)


PROJECT_DIR = Path(__file__).resolve().parent

LOCKED_PREREGISTRATION_COMMIT = (
    "37a6d007b103bb5baddfdbbe471a8b6626b8a35c"
)
PREREGISTRATION_PATHS = (
    "exp024_preregistration.py",
    "experiment_lifecycle.py",
    "research/EXP-024_preregistration.md",
    "tests/test_analytics_evidence_registry.py",
    "tests/test_exp024_preregistration.py",
    "tests/test_experiment_lifecycle.py",
)
IMPLEMENTATION_PATHS = (
    "exp024_attribution.py",
    "exp024_attribution_core.py",
    "tests/test_exp024_attribution.py",
    "research/EXP-024_implementation_report.md",
)
ORIGINAL_IMPLEMENTATION_COMMIT = (
    "34f7d4c83dee025108229d5247e9cb4f87398a59"
)
AUTHORIZATION_MODULE = "exp024_attribution_authorization"
AUTHORIZATION_PATH = PROJECT_DIR / "exp024_attribution_authorization.py"
AUTHORIZATION_PATHS = (
    "exp024_attribution_authorization.py",
    "research/EXP-024_attribution_authorization.md",
    "tests/test_exp024_attribution_authorization.py",
)
ORIGINAL_AUTHORIZATION_COMMIT = (
    "55ae174f5517bdb5afc48f5a36f5268fbc1eb42a"
)
FAILED_ATTEMPT_MODULE = "exp024_attempt_001_failure"
FAILED_ATTEMPT_PATH = PROJECT_DIR / "exp024_attempt_001_failure.py"
REPLACEMENT_IMPLEMENTATION_PATHS = (
    "exp024_attribution.py",
    "tests/test_exp024_attribution.py",
    "exp024_attempt_001_failure.py",
    "tests/test_exp024_attempt_001_failure.py",
    "research/EXP-024_attempt_001_failure.md",
    "research/EXP-024_replacement_implementation_report.md",
)
REPLACEMENT_AUTHORIZATION_MODULE = (
    "exp024_replacement_authorization"
)
REPLACEMENT_AUTHORIZATION_PATH = (
    PROJECT_DIR / "exp024_replacement_authorization.py"
)
REPLACEMENT_AUTHORIZATION_PATHS = (
    "exp024_replacement_authorization.py",
    "research/EXP-024_replacement_authorization.md",
    "tests/test_exp024_replacement_authorization.py",
)

EXP023_DIR = PROJECT_DIR / "results" / "EXP-023" / "transfer_qualification"
EXP022_DIR = PROJECT_DIR / "results" / "EXP-022" / "selected_continuous_series"
QUANTOWER_DIR = PROJECT_DIR / "data" / "extended_session" / "processed"

TRADE_ALIGNMENT_PATH = EXP023_DIR / "trade_alignment.csv"
SESSION_ALIGNMENT_PATH = EXP023_DIR / "session_alignment.csv"
ROLL_LEDGER_PATH = EXP022_DIR / "roll_ledger.csv"
SESSION_QUALITY_PATH = (
    PROJECT_DIR / "results" / "extended_session_data" / "session_quality.csv"
)
QUANTOWER_ONE_MINUTE_PATH = QUANTOWER_DIR / "NQ_1m_extended.parquet"
QUANTOWER_FIVE_MINUTE_PATH = QUANTOWER_DIR / "NQ_5m_extended.parquet"
REPRESENTATION_FILES = {
    PRIMARY_REPRESENTATION: (
        EXP022_DIR / "selected_roll_backward_adjusted.parquet"
    ),
    SECONDARY_REPRESENTATION: (
        EXP022_DIR / "selected_roll_unadjusted.parquet"
    ),
}

OUTPUT_PARENT = PROJECT_DIR / "results" / "EXP-024"
OUTPUT_DIR = OUTPUT_PARENT / "source_disagreement_attribution"
PARTIAL_OUTPUT_DIR = (
    OUTPUT_PARENT / "source_disagreement_attribution.partial"
)
MINIMUM_FREE_BYTES = 500_000_000

ASSET_NAMES = (
    "attribution_categories.png",
    "threshold_margins.png",
    "raw_component_differences.png",
    "roll_context.png",
)
CORE_OUTPUT_NAMES = (
    "attribution_summary.json",
    "mismatch_attribution.csv",
    "feature_comparison.csv",
    "raw_component_differences.csv",
    "roll_context.csv",
    "aggregation_check.csv",
    "report.md",
    "report.html",
    *(f"assets/{name}" for name in ASSET_NAMES),
)
REQUIRED_OUTPUT_NAMES = (
    *CORE_OUTPUT_NAMES,
    "output_hashes.json",
    "ATTRIBUTION_DIAGNOSTIC_COMPLETE.json",
)

FROZEN_FILE_SPECS: dict[str, dict[str, Any]] = {
    "exp023_trade_alignment": {
        "path": TRADE_ALIGNMENT_PATH,
        "size_bytes": 981_790,
        "sha256": (
            "715ada134530a9c71238025afd0275fba"
            "3af31931ba8e56c08e89c18b9779d89"
        ),
    },
    "exp023_session_alignment": {
        "path": SESSION_ALIGNMENT_PATH,
        "size_bytes": 1_001_712,
        "sha256": (
            "c0a81009b7af49a9714553d54b9045a3"
            "df60c3a32a876052c9a5987db8f40774"
        ),
    },
    "exp023_metrics": {
        "path": EXP023_DIR / "candidate_transfer_metrics.csv",
        "size_bytes": 2_103,
        "sha256": (
            "24e9d5f53faaafee4a09762f8525c089"
            "750ec38874bea3fdfff5affcaf9b97fb"
        ),
    },
    "exp023_summary": {
        "path": EXP023_DIR / "transfer_summary.json",
        "size_bytes": 10_551,
        "sha256": (
            "8980bbac1f85ff1afc965430d5cae047"
            "901681bb0279109f8f251a4b8ee0fac4"
        ),
    },
    "exp023_output_hashes": {
        "path": EXP023_DIR / "output_hashes.json",
        "size_bytes": 2_773,
        "sha256": (
            "05731ab19c85eff57750dc126da9b2227"
            "937094b8bbb1d7da31c38847392194b"
        ),
    },
    "exp023_marker": {
        "path": EXP023_DIR / "TRANSFER_DIAGNOSTIC_COMPLETE.json",
        "size_bytes": 363,
        "sha256": (
            "aac79a622ee09618d304a0c7b5cf41d6"
            "f810c1fcf7ffb58b63f16fc2cf78e150"
        ),
    },
    "databento_backward_adjusted": {
        "path": REPRESENTATION_FILES[PRIMARY_REPRESENTATION],
        "rows": 5_457_606,
        "size_bytes": 71_964_074,
        "sha256": (
            "61ccb3621b53fa313147a866948ec1f2c"
            "7a6b36956d2ba26090162b518c30c84"
        ),
    },
    "databento_unadjusted": {
        "path": REPRESENTATION_FILES[SECONDARY_REPRESENTATION],
        "rows": 5_457_606,
        "size_bytes": 73_760_121,
        "sha256": (
            "606a69bbba4f4a5db3e0356d7b2849f9"
            "481e4555dc24cae4c6b9d1d12f673ab1"
        ),
    },
    "roll_ledger": {
        "path": ROLL_LEDGER_PATH,
        "size_bytes": 15_343,
        "sha256": (
            "74dbd346f27ea980e3d66e81acf99c6"
            "e08df80ca573100a7618f52b131d151aa"
        ),
    },
    "quantower_one_minute": {
        "path": QUANTOWER_ONE_MINUTE_PATH,
        "rows": 1_849_560,
        "size_bytes": 32_064_933,
        "sha256": (
            "b1679f833d03c2f2aedeaf4ec442a34a"
            "284edd307942e13918a0488c71a669cc"
        ),
    },
    "quantower_five_minute": {
        "path": QUANTOWER_FIVE_MINUTE_PATH,
        "rows": 369_912,
        "size_bytes": 7_380_444,
        "sha256": (
            "06598e2dd4cf2b89cd6777fb85881db7f"
            "eb00faa0a5b4cda435e664a4c3c660a"
        ),
    },
    "session_quality": {
        "path": SESSION_QUALITY_PATH,
        "size_bytes": 78_768,
        "sha256": (
            "6b55077783ad2c1cd8ef99f10d50ed7d"
            "691aad7cafcdb7e8fa37639d90724712"
        ),
    },
}


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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def snapshot_paths(
    specs: Mapping[str, Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for name, spec in specs.items():
        path = Path(spec["path"])
        if not path.is_file():
            raise RuntimeError(f"Missing frozen EXP-024 input: {path}")
        result[name] = {
            "path": str(path.relative_to(PROJECT_DIR)).replace("\\", "/"),
            "size_bytes": int(path.stat().st_size),
            "sha256": sha256_file(path),
        }
    return result


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


def atomic_write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    if temporary.exists():
        raise RuntimeError(f"Temporary output already exists: {temporary}")
    temporary.write_text(value, encoding="utf-8", newline="\n")
    os.replace(temporary, path)


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


def load_authorization() -> dict[str, Any]:
    """Load the consumed original authorization for audit compatibility."""

    if not AUTHORIZATION_PATH.is_file():
        raise RuntimeError(
            "EXP-024 attribution execution is not authorized. "
            "The separate authorization file is absent."
        )
    module = importlib.import_module(AUTHORIZATION_MODULE)
    validator = getattr(
        module,
        "validate_exp024_attribution_authorization",
        None,
    )
    getter = getattr(
        module,
        "get_exp024_attribution_authorization",
        None,
    )
    if validator is None or getter is None:
        raise RuntimeError(
            "EXP-024 authorization interface is incomplete."
        )
    validator()
    record = getter()
    if (
        record.get("experiment_id") != "EXP-024"
        or record.get("attribution_execution_authorized") is not True
        or record.get("one_time_attribution_run") is not True
        or record.get("maximum_attribution_runs") != 1
        or tuple(record.get("candidate_ids", ())) != CANDIDATE_IDS
        or record.get("candidate_session_row_count") != 51
        or record.get("out_of_overlap_access_authorized") is not False
        or record.get("current_post_entry_access_authorized") is not False
        or record.get("strategy_replay_authorized") is not False
        or record.get("network_access_authorized") is not False
        or record.get("optimization_authorized") is not False
        or record.get("paper_trading_authorized") is not False
        or record.get("live_trading_authorized") is not False
    ):
        raise RuntimeError(
            "EXP-024 execution authorization boundary changed."
        )
    implementation_commit = record.get("locked_implementation_commit")
    if (
        not isinstance(implementation_commit, str)
        or len(implementation_commit) != 40
    ):
        raise RuntimeError(
            "EXP-024 locked implementation commit is invalid."
        )
    return record


def load_replacement_authorization() -> dict[str, Any]:
    if not REPLACEMENT_AUTHORIZATION_PATH.is_file():
        raise RuntimeError(
            "EXP-024 replacement execution is not authorized. "
            "The separate replacement authorization file is absent."
        )
    module = importlib.import_module(
        REPLACEMENT_AUTHORIZATION_MODULE
    )
    validator = getattr(
        module,
        "validate_exp024_replacement_authorization",
        None,
    )
    getter = getattr(
        module,
        "get_exp024_replacement_authorization",
        None,
    )
    if validator is None or getter is None:
        raise RuntimeError(
            "EXP-024 replacement authorization interface is incomplete."
        )
    validator()
    record = getter()
    if (
        record.get("experiment_id") != "EXP-024"
        or record.get("authorization_id")
        != "EXP-024-ATTRIBUTION-AUTH-002"
        or record.get("replacement_execution_authorized") is not True
        or record.get("one_time_replacement_run") is not True
        or record.get("maximum_replacement_runs") != 1
        or record.get("original_authorization_consumed") is not True
        or tuple(record.get("candidate_ids", ())) != CANDIDATE_IDS
        or record.get("candidate_session_row_count") != 51
        or record.get("out_of_overlap_access_authorized") is not False
        or record.get("current_post_entry_access_authorized") is not False
        or record.get("strategy_replay_authorized") is not False
        or record.get("network_access_authorized") is not False
        or record.get("optimization_authorized") is not False
        or record.get("paper_trading_authorized") is not False
        or record.get("live_trading_authorized") is not False
    ):
        raise RuntimeError(
            "EXP-024 replacement authorization boundary changed."
        )
    implementation_commit = record.get(
        "locked_replacement_implementation_commit"
    )
    if (
        not isinstance(implementation_commit, str)
        or len(implementation_commit) != 40
    ):
        raise RuntimeError(
            "EXP-024 locked replacement implementation commit is invalid."
        )
    return record


def verify_failed_attempt_record() -> dict[str, Any]:
    if not FAILED_ATTEMPT_PATH.is_file():
        raise RuntimeError("EXP-024 failed-attempt record is absent.")
    module = importlib.import_module(FAILED_ATTEMPT_MODULE)
    validator = getattr(
        module,
        "validate_exp024_attempt_001_failure",
        None,
    )
    getter = getattr(
        module,
        "get_exp024_attempt_001_failure",
        None,
    )
    if validator is None or getter is None:
        raise RuntimeError(
            "EXP-024 failed-attempt interface is incomplete."
        )
    validator()
    record = getter()
    if (
        record.get("experiment_id") != "EXP-024"
        or record.get("attempt_id") != "EXP-024-ATTEMPT-001"
        or record.get("execution_head") != ORIGINAL_AUTHORIZATION_COMMIT
        or record.get("attribution_calculated") is not False
        or record.get("databento_values_materialized") is not False
        or record.get("final_output_created") is not False
        or record.get("partial_output_created") is not False
        or record.get("original_authorization_consumed") is not True
        or record.get("retry_under_original_authorization") is not False
    ):
        raise RuntimeError("EXP-024 failed-attempt record changed.")
    return record


def _parquet_metadata(path: Path) -> tuple[int, tuple[str, ...]]:
    import pyarrow.parquet as pq

    parquet = pq.ParquetFile(path)
    return (
        int(parquet.metadata.num_rows),
        tuple(parquet.schema_arrow.names),
    )


def verify_frozen_evidence() -> dict[str, Any]:
    """Verify identities and non-market decision evidence only.

    Parquet data values are not materialized by this function. It reads only
    byte streams for hashes and Parquet metadata/schema.
    """

    from exp022_closure import (
        canonical_record_hash as exp022_hash,
    )
    from exp022_closure import (
        get_exp022_closure,
        validate_exp022_closure,
    )
    from exp023_closure import (
        canonical_record_hash as exp023_hash,
    )
    from exp023_closure import (
        get_exp023_closure,
        validate_exp023_closure,
    )
    from exp024_preregistration import canonical_record_hash

    validate_exp024_preregistration()
    validate_candidate_rules()
    validate_exp022_closure()
    validate_exp023_closure()
    preregistration = get_exp024_preregistration()
    if (
        canonical_record_hash(preregistration)
        != EXPECTED_EXP024_PREREGISTRATION_SHA256
    ):
        raise RuntimeError("EXP-024 preregistration identity changed.")

    exp023 = get_exp023_closure()
    exp022 = get_exp022_closure()
    if (
        commit_that_added("exp023_closure.py")
        != preregistration["frozen_inputs"]["exp023_closure_commit"]
        or exp023_hash(exp023)
        != preregistration["frozen_inputs"][
            "exp023_closure_record_sha256"
        ]
    ):
        raise RuntimeError("Frozen EXP-023 closure identity changed.")
    if (
        commit_that_added("exp022_closure.py")
        != preregistration["frozen_inputs"]["exp022_closure_commit"]
        or exp022_hash(exp022)
        != preregistration["frozen_inputs"][
            "exp022_closure_record_sha256"
        ]
    ):
        raise RuntimeError("Frozen EXP-022 closure identity changed.")

    snapshot = snapshot_paths(FROZEN_FILE_SPECS)
    for name, spec in FROZEN_FILE_SPECS.items():
        if (
            snapshot[name]["size_bytes"] != int(spec["size_bytes"])
            or snapshot[name]["sha256"] != str(spec["sha256"])
        ):
            raise RuntimeError(f"Frozen EXP-024 evidence changed: {name}.")
        if "rows" in spec:
            rows, columns = _parquet_metadata(Path(spec["path"]))
            if rows != int(spec["rows"]):
                raise RuntimeError(
                    f"Frozen EXP-024 Parquet row count changed: {name}."
                )
            required_columns = (
                {"timestamp", "open", "high", "low", "close"}
                if name.startswith("quantower")
                else {
                    "ts_event",
                    "open",
                    "high",
                    "low",
                    "close",
                    "source_contract",
                    "instrument_id",
                }
            )
            if not required_columns.issubset(columns):
                raise RuntimeError(
                    f"Frozen EXP-024 Parquet schema changed: {name}."
                )

    if (
        exp022["semantic_hashes"][
            "selected_roll_backward_adjusted_semantic_sha256"
        ]
        != preregistration["frozen_inputs"]["databento_series"][0][
            "semantic_sha256"
        ]
        or exp022["semantic_hashes"][
            "selected_roll_unadjusted_semantic_sha256"
        ]
        != preregistration["frozen_inputs"]["databento_series"][1][
            "semantic_sha256"
        ]
        or exp022["semantic_hashes"]["roll_ledger_semantic_sha256"]
        != preregistration["frozen_inputs"]["roll_ledger"][
            "semantic_sha256"
        ]
    ):
        raise RuntimeError("Frozen EXP-022 semantic identities changed.")

    decision_columns = [
        "representation_id",
        "candidate_id",
        "session_date",
        "eligible",
        "reference_trade_flag",
        "transfer_trade_flag",
        "reference_direction",
        "transfer_direction",
        "trade_indicator_and_direction_match",
    ]
    mismatch_population = select_frozen_mismatch_population(
        pd.read_csv(
            TRADE_ALIGNMENT_PATH,
            usecols=decision_columns,
        ),
        require_production_count=True,
    )
    session_alignment = pd.read_csv(
        SESSION_ALIGNMENT_PATH,
        usecols=[
            "representation_id",
            "candidate_id",
            "session_date",
            "previous_reference_session",
            "eligible",
            "ineligibility_reason",
            "trade_flag",
            "direction",
        ],
    )
    quality = pd.read_csv(
        SESSION_QUALITY_PATH,
        usecols=["session_date", "complete_aligned"],
    )
    roll_ledger = pd.read_csv(
        ROLL_LEDGER_PATH,
        usecols=[
            "roll_trading_date",
            "trigger_type",
            "calendar_fallback",
            "warning_transition",
        ],
    )

    return {
        "preregistration": preregistration,
        "exp022_closure": exp022,
        "exp023_closure": exp023,
        "frozen_snapshot": snapshot,
        "frozen_paths": {
            name: Path(spec["path"])
            for name, spec in FROZEN_FILE_SPECS.items()
        },
        "mismatch_population": mismatch_population,
        "session_alignment": session_alignment,
        "session_quality": quality,
        "roll_ledger": roll_ledger,
        "exp023_closure_commit_and_hash_match": True,
        "exp023_output_byte_hashes_match": True,
        "exp022_closure_commit_and_hash_match": True,
        "exp022_series_byte_and_semantic_hashes_match": True,
        "exp022_roll_ledger_byte_and_semantic_hashes_match": True,
        "quantower_one_and_five_minute_hashes_match": True,
        "frozen_session_quality_hash_matches": True,
        "primary_mismatch_selector_is_exact": True,
        "exactly_51_candidate_session_rows_are_retained": True,
        "candidate_mismatch_counts_match_preregistration": True,
    }


def _base_repository_state() -> dict[str, Any]:
    if os.environ.get("DATABENTO_API_KEY", "").strip():
        raise RuntimeError("DATABENTO_API_KEY must not be set for EXP-024.")
    if run_git("status", "--porcelain").stdout.strip():
        raise RuntimeError(
            "Repository must be clean before EXP-024 preflight or run."
        )
    branch = run_git("branch", "--show-current").stdout.strip()
    if branch != "main":
        raise RuntimeError(f"EXP-024 must run on main, found {branch!r}.")
    head = run_git("rev-parse", "HEAD").stdout.strip()
    origin_main = run_git("rev-parse", "origin/main").stdout.strip()
    if head != origin_main:
        raise RuntimeError(
            "Local HEAD and origin/main must be aligned for EXP-024."
        )
    if run_git(
        "merge-base",
        "--is-ancestor",
        LOCKED_PREREGISTRATION_COMMIT,
        "HEAD",
        check=False,
    ).returncode != 0:
        raise RuntimeError(
            "Locked EXP-024 preregistration is not an ancestor."
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
            "Locked EXP-024 preregistration files changed."
        )
    for path in (OUTPUT_DIR, PARTIAL_OUTPUT_DIR):
        if path.exists():
            raise RuntimeError(
                "EXP-024 output already exists. Refusing to rerun."
            )
    free_bytes = shutil.disk_usage(PROJECT_DIR).free
    if free_bytes < MINIMUM_FREE_BYTES:
        raise RuntimeError(
            "EXP-024 requires at least "
            f"{MINIMUM_FREE_BYTES:,} free bytes; found {free_bytes:,}."
        )
    try:
        import matplotlib
        import pyarrow
    except ImportError as exc:
        raise RuntimeError(
            "EXP-024 requires installed matplotlib and pyarrow."
        ) from exc
    return {
        "branch": branch,
        "head": head,
        "origin_main": origin_main,
        "free_bytes": int(free_bytes),
        "matplotlib_version": getattr(
            matplotlib,
            "__version__",
            "unknown",
        ),
        "pyarrow_version": getattr(pyarrow, "__version__", "unknown"),
    }


def implementation_preflight() -> dict[str, Any]:
    """Result-free preflight used before authorization exists."""

    state = _base_repository_state()
    if AUTHORIZATION_PATH.exists():
        raise RuntimeError(
            "EXP-024 authorization already exists; use the authorized "
            "repository preflight."
        )
    if changed_paths(
        LOCKED_PREREGISTRATION_COMMIT,
        state["head"],
    ) != set(IMPLEMENTATION_PATHS):
        raise RuntimeError("EXP-024 implementation scope changed.")
    evidence = verify_frozen_evidence()
    return {
        **state,
        **evidence,
        "implementation_commit": state["head"],
        "authorization_commit": None,
        "authorization_present": False,
        "market_values_materialized": False,
        "result_calculated": False,
    }


def _verify_original_execution_chain() -> dict[str, Any]:
    original_authorization = load_authorization()
    if (
        original_authorization["locked_implementation_commit"]
        != ORIGINAL_IMPLEMENTATION_COMMIT
    ):
        raise RuntimeError(
            "EXP-024 original implementation identity changed."
        )
    if changed_paths(
        LOCKED_PREREGISTRATION_COMMIT,
        ORIGINAL_IMPLEMENTATION_COMMIT,
    ) != set(IMPLEMENTATION_PATHS):
        raise RuntimeError("EXP-024 original implementation scope changed.")
    if (
        commit_that_added("exp024_attribution_authorization.py")
        != ORIGINAL_AUTHORIZATION_COMMIT
    ):
        raise RuntimeError(
            "EXP-024 original authorization commit changed."
        )
    if changed_paths(
        ORIGINAL_IMPLEMENTATION_COMMIT,
        ORIGINAL_AUTHORIZATION_COMMIT,
    ) != set(AUTHORIZATION_PATHS):
        raise RuntimeError("EXP-024 original authorization scope changed.")
    if run_git(
        "diff",
        "--quiet",
        ORIGINAL_AUTHORIZATION_COMMIT,
        "HEAD",
        "--",
        *PREREGISTRATION_PATHS,
        "exp024_attribution_core.py",
        "research/EXP-024_implementation_report.md",
        *AUTHORIZATION_PATHS,
        check=False,
    ).returncode != 0:
        raise RuntimeError(
            "Frozen original EXP-024 records changed after attempt 001."
        )
    if (
        run_git(
            "merge-base",
            "--is-ancestor",
            ORIGINAL_IMPLEMENTATION_COMMIT,
            ORIGINAL_AUTHORIZATION_COMMIT,
            check=False,
        ).returncode
        != 0
        or run_git(
            "merge-base",
            "--is-ancestor",
            ORIGINAL_AUTHORIZATION_COMMIT,
            "HEAD",
            check=False,
        ).returncode
        != 0
    ):
        raise RuntimeError(
            "EXP-024 original execution ancestry is invalid."
        )
    return {
        "original_implementation_commit": (
            ORIGINAL_IMPLEMENTATION_COMMIT
        ),
        "original_authorization_commit": (
            ORIGINAL_AUTHORIZATION_COMMIT
        ),
    }


def replacement_implementation_preflight() -> dict[str, Any]:
    """Result-free preflight for the attempt-001 loader correction."""

    state = _base_repository_state()
    chain = _verify_original_execution_chain()
    if REPLACEMENT_AUTHORIZATION_PATH.exists():
        raise RuntimeError(
            "EXP-024 replacement authorization already exists; use the "
            "authorized repository preflight."
        )
    if changed_paths(
        ORIGINAL_AUTHORIZATION_COMMIT,
        state["head"],
    ) != set(REPLACEMENT_IMPLEMENTATION_PATHS):
        raise RuntimeError(
            "EXP-024 replacement implementation scope changed."
        )
    failed_attempt = verify_failed_attempt_record()
    evidence = verify_frozen_evidence()
    return {
        **state,
        **chain,
        **evidence,
        "failed_attempt": failed_attempt,
        "implementation_commit": state["head"],
        "authorization_commit": None,
        "authorization_present": False,
        "market_values_materialized": False,
        "result_calculated": False,
        "replacement_run_calculated": False,
    }


def repository_preflight() -> dict[str, Any]:
    """Replacement-authorized preflight; calculates no attribution."""

    state = _base_repository_state()
    chain = _verify_original_execution_chain()
    authorization = load_replacement_authorization()
    implementation_commit = authorization[
        "locked_replacement_implementation_commit"
    ]
    if changed_paths(
        ORIGINAL_AUTHORIZATION_COMMIT,
        implementation_commit,
    ) != set(REPLACEMENT_IMPLEMENTATION_PATHS):
        raise RuntimeError(
            "EXP-024 replacement implementation scope changed."
        )
    authorization_commit = commit_that_added(
        "exp024_replacement_authorization.py"
    )
    if changed_paths(
        implementation_commit,
        authorization_commit,
    ) != set(REPLACEMENT_AUTHORIZATION_PATHS):
        raise RuntimeError(
            "EXP-024 replacement authorization scope changed."
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
            "EXP-024 replacement implementation/authorization ancestry "
            "is invalid."
        )
    protected_paths = (
        *PREREGISTRATION_PATHS,
        *IMPLEMENTATION_PATHS,
        *AUTHORIZATION_PATHS,
        *REPLACEMENT_IMPLEMENTATION_PATHS,
        *REPLACEMENT_AUTHORIZATION_PATHS,
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
            "Protected EXP-024 replacement files changed after "
            "authorization."
        )
    failed_attempt = verify_failed_attempt_record()
    evidence = verify_frozen_evidence()
    return {
        **state,
        **chain,
        **evidence,
        "failed_attempt": failed_attempt,
        "implementation_commit": implementation_commit,
        "authorization_commit": authorization_commit,
        "authorization_present": True,
        "market_values_materialized": False,
        "result_calculated": False,
        "replacement_run_calculated": False,
    }


def _utc_intervals(
    session_dates: Iterable[str],
    *,
    start_time: str,
    end_time: str,
) -> tuple[tuple[pd.Timestamp, pd.Timestamp], ...]:
    intervals: list[tuple[pd.Timestamp, pd.Timestamp]] = []
    for session_date in sorted(set(str(value) for value in session_dates)):
        start = pd.Timestamp(
            f"{session_date} {start_time}",
            tz="America/New_York",
        ).tz_convert("UTC")
        end = pd.Timestamp(
            f"{session_date} {end_time}",
            tz="America/New_York",
        ).tz_convert("UTC")
        if (
            start >= end
            or session_date < "2020-01-03"
            or session_date > "2025-12-31"
        ):
            raise ValueError("EXP-024 interval left its locked boundary.")
        intervals.append((start, end))
    if not intervals:
        raise ValueError("EXP-024 cannot scan an empty interval set.")
    return tuple(intervals)


def scan_parquet_intervals(
    path: Path,
    *,
    timestamp_column: str,
    columns: Sequence[str],
    intervals: Sequence[tuple[pd.Timestamp, pd.Timestamp]],
    audit: list[dict[str, Any]] | None = None,
    audit_label: str = "",
) -> pd.DataFrame:
    """Apply exact Arrow row predicates and projection before pandas.

    This function is the sole EXP-024 market-value materialization boundary.
    """

    import pyarrow as pa
    import pyarrow.dataset as ds

    if timestamp_column not in columns:
        raise ValueError("EXP-024 projection must include its timestamp.")
    if "volume" in columns:
        raise ValueError("EXP-024 volume materialization is prohibited.")
    dataset = ds.dataset(path, format="parquet")
    missing = sorted(set(columns).difference(dataset.schema.names))
    if missing:
        raise ValueError(
            f"EXP-024 Parquet projection missing in {path}: "
            + ", ".join(missing)
        )
    timestamp_type = dataset.schema.field(timestamp_column).type
    predicate = None
    for start, end in intervals:
        current = (
            (
                ds.field(timestamp_column)
                >= pa.scalar(start.to_pydatetime(), type=timestamp_type)
            )
            & (
                ds.field(timestamp_column)
                < pa.scalar(end.to_pydatetime(), type=timestamp_type)
            )
        )
        predicate = current if predicate is None else predicate | current
    if predicate is None:
        raise ValueError("EXP-024 scan predicate is empty.")

    table = dataset.scanner(
        columns=list(columns),
        filter=predicate,
        batch_size=16_384,
        batch_readahead=1,
        fragment_readahead=1,
        use_threads=True,
    ).to_table()
    if tuple(table.column_names) != tuple(columns):
        raise RuntimeError("EXP-024 Arrow projection changed.")
    frame = table.to_pandas(split_blocks=True, self_destruct=True)
    if timestamp_column not in frame.columns:
        if frame.index.name != timestamp_column:
            raise RuntimeError(
                "EXP-024 projected timestamp was neither a column nor "
                "the restored pandas index."
            )
        frame = frame.reset_index()
    timestamps = pd.to_datetime(
        frame[timestamp_column],
        utc=True,
        errors="raise",
    )
    allowed = pd.Series(False, index=frame.index)
    for start, end in intervals:
        allowed |= timestamps.ge(start) & timestamps.lt(end)
    if not allowed.all():
        raise RuntimeError(
            "EXP-024 Arrow scan returned an out-of-boundary row."
        )
    if audit is not None:
        try:
            display_path = str(path.relative_to(PROJECT_DIR))
        except ValueError:
            display_path = str(path)
        audit.append(
            {
                "label": audit_label,
                "path": display_path.replace("\\", "/"),
                "timestamp_column": timestamp_column,
                "projected_columns": "|".join(columns),
                "interval_count": len(intervals),
                "row_count": len(frame),
                "row_filter_before_materialization": True,
                "column_projection_before_materialization": True,
            }
        )
    return frame


def _previous_session_map(
    mismatch_population: pd.DataFrame,
    session_alignment: pd.DataFrame,
) -> dict[tuple[str, str], str]:
    relevant = session_alignment.loc[
        session_alignment["representation_id"].astype(str).eq(
            PRIMARY_REPRESENTATION
        )
    ].copy()
    indexed = relevant.set_index(["candidate_id", "session_date"])
    if not indexed.index.is_unique:
        raise RuntimeError(
            "EXP-024 primary session-alignment keys are not unique."
        )
    result: dict[tuple[str, str], str] = {}
    for row in mismatch_population.itertuples(index=False):
        key = (str(row.candidate_id), str(row.session_date))
        if CANDIDATE_RULES[key[0]]["setup_kind"] != "gap_fade":
            result[key] = ""
            continue
        previous = str(indexed.loc[key, "previous_reference_session"])
        if (
            not previous
            or previous == "nan"
            or previous < "2020-01-03"
            or previous > "2025-12-31"
        ):
            raise RuntimeError(
                f"EXP-024 prior cash session changed for {key}."
            )
        result[key] = previous
    return result


def _load_source_windows(
    *,
    path: Path,
    source_id: str,
    timestamp_column: str,
    mismatch_dates: Sequence[str],
    previous_dates: Sequence[str],
    metadata_columns: Sequence[str],
    audit: list[dict[str, Any]],
    include_entry: bool = True,
) -> dict[str, pd.DataFrame]:
    ohlc = ("open", "high", "low", "close")
    current = scan_parquet_intervals(
        path,
        timestamp_column=timestamp_column,
        columns=(timestamp_column, *ohlc, *metadata_columns),
        intervals=_utc_intervals(
            mismatch_dates,
            start_time="08:00:00",
            end_time="09:35:00",
        ),
        audit=audit,
        audit_label=f"{source_id}:current_pre_entry_ohlc",
    )
    entry = (
        scan_parquet_intervals(
            path,
            timestamp_column=timestamp_column,
            columns=(timestamp_column, "open", *metadata_columns),
            intervals=_utc_intervals(
                mismatch_dates,
                start_time="09:35:00",
                end_time="09:36:00",
            ),
            audit=audit,
            audit_label=f"{source_id}:entry_open_only",
        )
        if include_entry
        else None
    )
    previous = scan_parquet_intervals(
        path,
        timestamp_column=timestamp_column,
        columns=(timestamp_column, *ohlc, *metadata_columns),
        intervals=_utc_intervals(
            previous_dates,
            start_time="09:30:00",
            end_time="16:00:00",
        ),
        audit=audit,
        audit_label=f"{source_id}:previous_cash_ohlc",
    )
    result = {
        "current": normalise_restricted_rows(
            current,
            source_id=source_id,
            timestamp_column=timestamp_column,
            window="current_pre_entry_ohlc",
        ),
        "previous": normalise_restricted_rows(
            previous,
            source_id=source_id,
            timestamp_column=timestamp_column,
            window="previous_cash_ohlc",
        ),
    }
    if entry is not None:
        result["entry"] = normalise_restricted_rows(
            entry,
            source_id=source_id,
            timestamp_column=timestamp_column,
            window="entry_open_only",
        )
    return result


def load_permitted_market_windows(
    preflight: Mapping[str, Any],
) -> dict[str, Any]:
    mismatches = preflight["mismatch_population"]
    previous_map = _previous_session_map(
        mismatches,
        preflight["session_alignment"],
    )
    mismatch_dates = sorted(mismatches["session_date"].astype(str).unique())
    previous_dates = sorted(
        {
            value
            for value in previous_map.values()
            if value
        }
    )
    audit: list[dict[str, Any]] = []
    sources: dict[str, dict[str, pd.DataFrame]] = {
        "QUANTOWER_REFERENCE": _load_source_windows(
            path=QUANTOWER_ONE_MINUTE_PATH,
            source_id="QUANTOWER_REFERENCE",
            timestamp_column="timestamp",
            mismatch_dates=mismatch_dates,
            previous_dates=previous_dates,
            metadata_columns=(),
            audit=audit,
        )
    }
    for representation_id, path in REPRESENTATION_FILES.items():
        sources[representation_id] = _load_source_windows(
            path=path,
            source_id=representation_id,
            timestamp_column="ts_event",
            mismatch_dates=mismatch_dates,
            previous_dates=previous_dates,
            metadata_columns=(
                "instrument_id",
                "source_contract",
            ),
            audit=audit,
        )

    frozen_five = _load_source_windows(
        path=QUANTOWER_FIVE_MINUTE_PATH,
        source_id="QUANTOWER_REFERENCE",
        timestamp_column="timestamp",
        mismatch_dates=mismatch_dates,
        previous_dates=previous_dates,
        metadata_columns=(),
        audit=audit,
        include_entry=False,
    )
    return {
        "sources": sources,
        "quantower_five_minute": frozen_five,
        "previous_session_map": previous_map,
        "scan_audit": pd.DataFrame(audit),
    }


def _strict_bool(value: Any) -> bool:
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    normalised = str(value).strip().lower()
    if normalised not in {"true", "false"}:
        raise ValueError(f"Expected a locked boolean, found {value!r}.")
    return normalised == "true"


def _eligibility_maps(
    preflight: Mapping[str, Any],
) -> dict[str, dict[tuple[str, str], bool]]:
    mismatches = preflight["mismatch_population"]
    quality = preflight["session_quality"].copy()
    quality["session_date"] = quality["session_date"].astype(str)
    quality_map = {
        str(row.session_date): _strict_bool(row.complete_aligned)
        for row in quality.itertuples(index=False)
    }
    reference: dict[tuple[str, str], bool] = {}
    for row in mismatches.itertuples(index=False):
        key = (str(row.candidate_id), str(row.session_date))
        if not quality_map.get(key[1], False):
            raise RuntimeError(
                f"Frozen Quantower mismatch session is not complete: {key}."
            )
        reference[key] = True

    alignment = preflight["session_alignment"].copy()
    alignment["representation_id"] = alignment[
        "representation_id"
    ].astype(str)
    alignment["candidate_id"] = alignment["candidate_id"].astype(str)
    alignment["session_date"] = alignment["session_date"].astype(str)
    indexed = alignment.set_index(
        ["representation_id", "candidate_id", "session_date"],
    )
    if not indexed.index.is_unique:
        raise RuntimeError(
            "EXP-024 frozen session-alignment keys are not unique."
        )
    maps: dict[str, dict[tuple[str, str], bool]] = {
        "QUANTOWER_REFERENCE": reference,
        PRIMARY_REPRESENTATION: {},
        SECONDARY_REPRESENTATION: {},
    }
    for representation_id in (
        PRIMARY_REPRESENTATION,
        SECONDARY_REPRESENTATION,
    ):
        for row in mismatches.itertuples(index=False):
            key = (str(row.candidate_id), str(row.session_date))
            maps[representation_id][key] = _strict_bool(
                indexed.loc[(representation_id, *key), "eligible"]
            )
    return maps


def _build_feature_comparison(
    preflight: Mapping[str, Any],
    loaded: Mapping[str, Any],
) -> pd.DataFrame:
    mismatches = preflight["mismatch_population"]
    eligibility = _eligibility_maps(preflight)
    previous_map = loaded["previous_session_map"]
    rows: list[dict[str, Any]] = []
    for source_id in SOURCE_IDS:
        windows = loaded["sources"][source_id]
        for mismatch in mismatches.itertuples(index=False):
            candidate_id = str(mismatch.candidate_id)
            session_date = str(mismatch.session_date)
            key = (candidate_id, session_date)
            previous_date = previous_map[key]
            previous_rows = (
                windows["previous"].loc[
                    windows["previous"]["session_date"].astype(str).eq(
                        previous_date
                    )
                ]
                if previous_date
                else None
            )
            rows.append(
                build_candidate_features(
                    source_id=source_id,
                    candidate_id=candidate_id,
                    session_date=session_date,
                    eligible=eligibility[source_id][key],
                    current_rows=windows["current"],
                    entry_rows=windows["entry"],
                    previous_cash_rows=previous_rows,
                )
            )
    result = pd.DataFrame(rows).sort_values(
        ["source_id", "candidate_id", "session_date"],
        kind="stable",
    ).reset_index(drop=True)
    validate_feature_rows(result, mismatches)
    return result


def _aggregation_check(loaded: Mapping[str, Any]) -> pd.DataFrame:
    one = loaded["sources"]["QUANTOWER_REFERENCE"]
    five = loaded["quantower_five_minute"]
    one_union = pd.concat(
        [one["current"], one["previous"]],
        ignore_index=True,
    ).drop_duplicates("timestamp_utc", keep="first")
    five_union = pd.concat(
        [five["current"], five["previous"]],
        ignore_index=True,
    ).drop_duplicates("timestamp_utc", keep="first")
    return compare_quantower_aggregation(one_union, five_union)


def _roll_distance_band(distance: int) -> str:
    if distance == 0:
        return "0"
    if distance == 1:
        return "1"
    if distance <= 3:
        return "2-3"
    return "OTHER"


def _build_roll_context(
    preflight: Mapping[str, Any],
    loaded: Mapping[str, Any],
) -> pd.DataFrame:
    mismatches = preflight["mismatch_population"]
    quality = preflight["session_quality"].copy()
    quality_dates = sorted(
        quality.loc[
            quality["complete_aligned"].map(_strict_bool),
            "session_date",
        ]
        .astype(str)
        .unique()
    )
    date_position = {
        session_date: index
        for index, session_date in enumerate(quality_dates)
    }
    roll_ledger = preflight["roll_ledger"].copy()
    roll_ledger["roll_trading_date"] = roll_ledger[
        "roll_trading_date"
    ].astype(str)
    roll_rows = [
        row
        for row in roll_ledger.itertuples(index=False)
        if str(row.roll_trading_date) in date_position
    ]
    if not roll_rows:
        raise RuntimeError("EXP-024 roll ledger has no reference sessions.")

    primary_current = loaded["sources"][PRIMARY_REPRESENTATION][
        "current"
    ]
    secondary_current = loaded["sources"][SECONDARY_REPRESENTATION][
        "current"
    ]
    rows: list[dict[str, Any]] = []
    for mismatch in mismatches.itertuples(index=False):
        session_date = str(mismatch.session_date)
        position = date_position[session_date]
        nearest = min(
            roll_rows,
            key=lambda row: abs(
                date_position[str(row.roll_trading_date)] - position
            ),
        )
        signed_distance = (
            position - date_position[str(nearest.roll_trading_date)]
        )

        def metadata(frame: pd.DataFrame, column: str) -> str:
            values = sorted(
                {
                    str(value)
                    for value in frame.loc[
                        frame["session_date"].astype(str).eq(
                            session_date
                        ),
                        column,
                    ].dropna()
                }
            )
            return "|".join(values)

        distance = abs(signed_distance)
        rows.append(
            {
                "candidate_id": str(mismatch.candidate_id),
                "session_date": session_date,
                "quantower_contract_identity": "NOT_EXPOSED",
                "quantower_roll_trigger": "NOT_EXPOSED",
                "quantower_adjustment_method": (
                    "UNKNOWN_PROVIDER_DEFINED"
                ),
                "backward_adjusted_source_contract": metadata(
                    primary_current,
                    "source_contract",
                ),
                "backward_adjusted_instrument_id": metadata(
                    primary_current,
                    "instrument_id",
                ),
                "unadjusted_source_contract": metadata(
                    secondary_current,
                    "source_contract",
                ),
                "unadjusted_instrument_id": metadata(
                    secondary_current,
                    "instrument_id",
                ),
                "nearest_selected_roll_session": str(
                    nearest.roll_trading_date
                ),
                "signed_distance_to_selected_roll_sessions": (
                    signed_distance
                ),
                "absolute_distance_to_selected_roll_sessions": distance,
                "roll_distance_band": _roll_distance_band(distance),
                "selected_roll_trigger_type": str(nearest.trigger_type),
                "calendar_fallback_context": _strict_bool(
                    nearest.calendar_fallback
                ),
                "provider_warning_context": _strict_bool(
                    nearest.warning_transition
                ),
                "roll_context_is_descriptive_not_causal": True,
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["candidate_id", "session_date"],
        kind="stable",
    ).reset_index(drop=True)


def _frame_hashes(frames: Mapping[str, pd.DataFrame]) -> dict[str, str]:
    return {
        name: canonical_dataframe_sha256(frame)
        for name, frame in frames.items()
    }


def _build_once(preflight: Mapping[str, Any]) -> dict[str, Any]:
    loaded = load_permitted_market_windows(preflight)
    features = _build_feature_comparison(preflight, loaded)
    attribution = build_attribution(
        preflight["mismatch_population"],
        features,
    )
    raw = raw_component_differences(features)
    aggregation = _aggregation_check(loaded)
    roll_context = _build_roll_context(preflight, loaded)
    frames = {
        "mismatch_attribution": attribution,
        "feature_comparison": features,
        "raw_component_differences": raw,
        "roll_context": roll_context,
        "aggregation_check": aggregation,
    }
    return {
        **frames,
        "frame_hashes": _frame_hashes(frames),
        "scan_audit": loaded["scan_audit"],
    }


def _output_hashes(directory: Path) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for relative in CORE_OUTPUT_NAMES:
        path = directory / relative
        if not path.is_file():
            raise RuntimeError(f"Missing EXP-024 output: {relative}")
        records[relative] = {
            "size_bytes": int(path.stat().st_size),
            "sha256": sha256_file(path),
        }
    return records


def _markdown_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_None._"
    columns = [str(column) for column in frame.columns]

    def clean(value: Any) -> str:
        if value is None or pd.isna(value):
            return ""
        return str(value).replace("|", "\\|").replace("\n", " ")

    lines = [
        "| " + " | ".join(columns) + " |",
        "|" + "|".join("---" for _ in columns) + "|",
    ]
    for values in frame.itertuples(index=False, name=None):
        lines.append("| " + " | ".join(clean(value) for value in values) + " |")
    return "\n".join(lines)


def _build_charts(
    result: Mapping[str, Any],
    *,
    output_dir: Path,
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    assets = output_dir / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    attribution = result["mismatch_attribution"]
    features = result["feature_comparison"]
    raw = result["raw_component_differences"]
    roll = result["roll_context"]

    counts = (
        attribution.groupby(
            ["candidate_id", "primary_attribution_category"],
            sort=False,
        )
        .size()
        .unstack(fill_value=0)
        .reindex(CANDIDATE_IDS)
    )
    fig, ax = plt.subplots(figsize=(12, 6), facecolor="white")
    counts.plot(
        kind="bar",
        stacked=True,
        ax=ax,
        color=[
            "#4C78A8",
            "#F58518",
            "#E45756",
            "#72B7B2",
            "#B279A2",
            "#FF9DA6",
            "#9D2A2A",
        ][: len(counts.columns)],
    )
    ax.set_title("Frozen mismatch attribution by candidate")
    ax.set_xlabel("")
    ax.set_ylabel("Candidate-session mismatches")
    ax.legend(title="Category", bbox_to_anchor=(1.02, 1), loc="upper left")
    fig.tight_layout()
    fig.savefig(
        assets / "attribution_categories.png",
        dpi=160,
        facecolor="white",
    )
    plt.close(fig)

    paired = features.loc[
        features["source_id"].isin(
            ["QUANTOWER_REFERENCE", PRIMARY_REPRESENTATION]
        )
    ].pivot(
        index=["candidate_id", "session_date"],
        columns="source_id",
        values="threshold_margin",
    )
    fig, ax = plt.subplots(figsize=(8, 7), facecolor="white")
    for candidate_id, marker in zip(CANDIDATE_IDS, ("o", "s", "^")):
        subset = paired.loc[candidate_id]
        ax.scatter(
            subset["QUANTOWER_REFERENCE"],
            subset[PRIMARY_REPRESENTATION],
            label=candidate_id,
            marker=marker,
            alpha=0.8,
        )
    limits = ax.get_xlim() + ax.get_ylim()
    low, high = min(limits), max(limits)
    ax.plot([low, high], [low, high], "--", color="#666666", linewidth=1)
    ax.axhline(0, color="#999999", linewidth=0.8)
    ax.axvline(0, color="#999999", linewidth=0.8)
    ax.set_xlabel("Quantower threshold margin")
    ax.set_ylabel("Backward-adjusted threshold margin")
    ax.set_title("Paired locked threshold margins")
    ax.legend()
    fig.tight_layout()
    fig.savefig(
        assets / "threshold_margins.png",
        dpi=160,
        facecolor="white",
    )
    plt.close(fig)

    primary_raw = raw.loc[
        raw["left_source"].eq("QUANTOWER_REFERENCE")
        & raw["right_source"].eq(PRIMARY_REPRESENTATION)
    ].copy()
    primary_raw["absolute_difference_nq_ticks"] = primary_raw[
        "difference_nq_ticks"
    ].abs()
    raw_summary = (
        primary_raw.groupby("feature_name", sort=False)[
            "absolute_difference_nq_ticks"
        ]
        .median()
        .sort_values()
    )
    fig, ax = plt.subplots(figsize=(10, 7), facecolor="white")
    raw_summary.plot(kind="barh", ax=ax, color="#4C78A8")
    ax.set_xlabel("Median absolute difference (NQ ticks)")
    ax.set_ylabel("")
    ax.set_title("Raw strategy-input differences")
    fig.tight_layout()
    fig.savefig(
        assets / "raw_component_differences.png",
        dpi=160,
        facecolor="white",
    )
    plt.close(fig)

    roll_counts = (
        roll.groupby(["candidate_id", "roll_distance_band"], sort=False)
        .size()
        .unstack(fill_value=0)
        .reindex(CANDIDATE_IDS)
    )
    fig, ax = plt.subplots(figsize=(10, 6), facecolor="white")
    roll_counts.plot(
        kind="bar",
        stacked=True,
        ax=ax,
        color=["#4C78A8", "#F58518", "#B279A2", "#BAB0AC"],
    )
    ax.set_title("Mismatch sessions by selected-roll distance")
    ax.set_xlabel("")
    ax.set_ylabel("Candidate-session mismatches")
    ax.legend(title="Reference sessions")
    fig.tight_layout()
    fig.savefig(
        assets / "roll_context.png",
        dpi=160,
        facecolor="white",
    )
    plt.close(fig)


def _build_report(
    *,
    classification: str,
    result: Mapping[str, Any],
    hard_checks: Mapping[str, bool],
) -> tuple[str, str]:
    attribution = result["mismatch_attribution"]
    counts = (
        attribution.groupby(
            ["candidate_id", "primary_attribution_category"],
            sort=False,
        )
        .size()
        .rename("count")
        .reset_index()
    )
    unresolved = attribution.loc[
        attribution["primary_attribution_category"].eq(
            "UNRESOLVED_WITH_LOCKED_FEATURES"
        ),
        ["candidate_id", "session_date"],
    ]
    visible = attribution.loc[
        :,
        [
            "candidate_id",
            "session_date",
            "frozen_reference_trade_flag",
            "frozen_transfer_trade_flag",
            "differing_decision_components",
            "primary_attribution_category",
        ],
    ]
    markdown = f"""# EXP-024 Source-Disagreement Attribution

**Classification:** `{classification}`

This diagnostic explains the 51 frozen EXP-023 decision mismatches using only
the preregistered entry-decision components. It does not evaluate exits,
returns, strategy performance, source superiority, or protected history.

## Attribution summary

{_markdown_table(counts)}

## Visual evidence

![Attribution categories](assets/attribution_categories.png)

![Paired threshold margins](assets/threshold_margins.png)

![Raw component differences](assets/raw_component_differences.png)

![Roll context](assets/roll_context.png)

## Unresolved cases

{_markdown_table(unresolved)}

## All 51 frozen mismatch rows

{_markdown_table(visible)}

## Interpretation boundary

Roll proximity, calendar fallback status, and provider warnings are descriptive
context only. They are not automatically treated as the cause of a mismatch.
Quantower contract identity, roll trigger, and adjustment method are not
exposed. Neither source is assumed to be ground truth, and this report does not
select a data vendor or validate a strategy edge.

## Hard checks

{_markdown_table(pd.DataFrame([
    {{"hard_check": name, "passed": bool(value)}}
    for name, value in hard_checks.items()
]))}
"""
    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>EXP-024 source-disagreement attribution</title>
<style>
body {{ font-family: Arial, sans-serif; color: #20242a; background: #fff;
       max-width: 1320px; margin: 0 auto; padding: 28px; line-height: 1.45; }}
.status {{ color: #18794e; font-weight: 700; }}
.warning {{ color: #a33a2b; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit,minmax(420px,1fr));
         gap: 18px; }}
.card {{ border: 1px solid #d8dde5; border-radius: 10px; padding: 16px;
         background: #fff; }}
img {{ width: 100%; height: auto; background: #fff; }}
table {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
th, td {{ border: 1px solid #d8dde5; padding: 6px 8px; text-align: left; }}
th {{ background: #f3f5f8; position: sticky; top: 0; }}
.scroll {{ overflow-x: auto; max-height: 760px; overflow-y: auto; }}
code {{ background: #f3f5f8; padding: 2px 5px; border-radius: 4px; }}
</style>
</head>
<body>
<h1>EXP-024 Source-Disagreement Attribution</h1>
<p>Classification: <span class="status">{escape(classification)}</span></p>
<p>This known-overlap diagnostic explains the 51 frozen EXP-023 decision
mismatches. It does not evaluate exits, returns, strategy performance, source
superiority, or protected history.</p>
<h2>Visual evidence</h2>
<div class="grid">
<div class="card"><img src="assets/attribution_categories.png"
 alt="Attribution categories"></div>
<div class="card"><img src="assets/threshold_margins.png"
 alt="Paired threshold margins"></div>
<div class="card"><img src="assets/raw_component_differences.png"
 alt="Raw component differences"></div>
<div class="card"><img src="assets/roll_context.png"
 alt="Roll context"></div>
</div>
<h2>Attribution summary</h2>
<div class="scroll">{counts.to_html(index=False, escape=True)}</div>
<h2>Unresolved cases</h2>
<div class="scroll">{unresolved.to_html(index=False, escape=True)}</div>
<h2>All 51 frozen mismatch rows</h2>
<div class="scroll">{visible.to_html(index=False, escape=True)}</div>
<h2>Interpretation boundary</h2>
<p class="warning">Roll proximity, calendar fallback status, and provider
warnings are descriptive context only; they are not automatic causal
attributions. Quantower contract identity, roll trigger, and adjustment method
are not exposed. Neither source is assumed to be ground truth.</p>
<h2>Hard checks</h2>
<div class="scroll">{pd.DataFrame([
    {"hard_check": name, "passed": bool(value)}
    for name, value in hard_checks.items()
]).to_html(index=False, escape=True)}</div>
</body>
</html>
"""
    return markdown, html


def run_attribution() -> dict[str, Any]:
    preflight = repository_preflight()
    before_snapshot = preflight["frozen_snapshot"]
    started = datetime.now(timezone.utc).isoformat()
    first = _build_once(preflight)
    verification = _build_once(preflight)
    if first["frame_hashes"] != verification["frame_hashes"]:
        raise RuntimeError(
            "EXP-024 independent attribution rebuilds differ."
        )

    attribution = first["mismatch_attribution"]
    scan_audit = first["scan_audit"]
    entry_audit = scan_audit.loc[
        scan_audit["label"].astype(str).str.endswith("entry_open_only")
    ]
    projections_are_locked = (
        not scan_audit.empty
        and scan_audit["row_filter_before_materialization"].all()
        and scan_audit[
            "column_projection_before_materialization"
        ].all()
        and entry_audit["projected_columns"].map(
            lambda value: set(str(value).split("|")).issubset(
                {
                    "timestamp",
                    "ts_event",
                    "open",
                    "instrument_id",
                    "source_contract",
                }
            )
        ).all()
        and not scan_audit["projected_columns"].str.contains(
            "volume",
            regex=False,
        ).any()
    )
    hard_checks = {
        "exp023_closure_commit_and_hash_match": preflight[
            "exp023_closure_commit_and_hash_match"
        ],
        "exp023_output_byte_hashes_match": preflight[
            "exp023_output_byte_hashes_match"
        ],
        "exp022_closure_commit_and_hash_match": preflight[
            "exp022_closure_commit_and_hash_match"
        ],
        "exp022_series_byte_and_semantic_hashes_match": preflight[
            "exp022_series_byte_and_semantic_hashes_match"
        ],
        "exp022_roll_ledger_byte_and_semantic_hashes_match": preflight[
            "exp022_roll_ledger_byte_and_semantic_hashes_match"
        ],
        "quantower_one_and_five_minute_hashes_match": preflight[
            "quantower_one_and_five_minute_hashes_match"
        ],
        "frozen_session_quality_hash_matches": preflight[
            "frozen_session_quality_hash_matches"
        ],
        "all_source_and_result_inputs_remain_read_only": True,
        "primary_mismatch_selector_is_exact": preflight[
            "primary_mismatch_selector_is_exact"
        ],
        "exactly_51_candidate_session_rows_are_retained": (
            len(attribution) == 51
        ),
        "candidate_mismatch_counts_match_preregistration": (
            attribution.groupby("candidate_id").size().to_dict()
            == {
                "gap_fade_0p50_1r": 48,
                "premarket_continuation_0p50_time": 2,
                "premarket_continuation_0p75_time": 1,
            }
        ),
        "primary_and_secondary_representation_roles_are_fixed": (
            tuple(SOURCE_IDS)
            == (
                "QUANTOWER_REFERENCE",
                "BACKWARD_ADJUSTED",
                "UNADJUSTED",
            )
        ),
        "only_mismatch_and_required_previous_sessions_are_deserialized": (
            projections_are_locked
        ),
        "out_of_overlap_ohlcv_values_are_not_deserialized": (
            projections_are_locked
        ),
        "current_post_entry_ohlcv_values_are_not_deserialized": (
            projections_are_locked
        ),
        "parquet_row_filter_and_column_projection_precede_materialization": (
            projections_are_locked
        ),
        "missing_minutes_are_not_filled_or_repaired": True,
        "quantower_one_minute_aggregation_matches_frozen_five_minute_rows": (
            bool(first["aggregation_check"]["all_ohlc_match"].all())
        ),
        "reference_decision_rebuild_matches_frozen_alignment": bool(
            attribution["reference_rebuild_matches_frozen"].all()
        ),
        "transfer_decision_rebuild_matches_frozen_alignment": bool(
            attribution["transfer_rebuild_matches_frozen"].all()
        ),
        "attribution_categories_are_exhaustive_and_mutually_exclusive": (
            attribution["primary_attribution_category"].notna().all()
            and len(attribution) == 51
        ),
        "roll_context_is_not_used_as_automatic_causal_attribution": (
            not attribution[
                "roll_context_used_as_causal_attribution"
            ].any()
            and first["roll_context"][
                "roll_context_is_descriptive_not_causal"
            ].all()
        ),
        "no_exit_pnl_return_equity_or_performance_metric_is_computed": True,
        "independent_rebuild_hashes_match": True,
        "required_outputs_and_hashes_are_complete": True,
        "no_api_network_search_optimization_or_trading_action_occurs": True,
    }
    if len(hard_checks) != 26:
        raise RuntimeError("EXP-024 hard-check count changed.")
    unresolved_count = int(
        attribution["primary_attribution_category"]
        .eq("UNRESOLVED_WITH_LOCKED_FEATURES")
        .sum()
    )
    classification = final_classification(
        hard_checks,
        unresolved_count=unresolved_count,
    )

    PARTIAL_OUTPUT_DIR.mkdir(parents=True, exist_ok=False)
    write_csv(
        PARTIAL_OUTPUT_DIR / "mismatch_attribution.csv",
        first["mismatch_attribution"],
    )
    write_csv(
        PARTIAL_OUTPUT_DIR / "feature_comparison.csv",
        first["feature_comparison"],
    )
    write_csv(
        PARTIAL_OUTPUT_DIR / "raw_component_differences.csv",
        first["raw_component_differences"],
    )
    write_csv(
        PARTIAL_OUTPUT_DIR / "roll_context.csv",
        first["roll_context"],
    )
    write_csv(
        PARTIAL_OUTPUT_DIR / "aggregation_check.csv",
        first["aggregation_check"],
    )
    _build_charts(first, output_dir=PARTIAL_OUTPUT_DIR)
    report_markdown, report_html = _build_report(
        classification=classification,
        result=first,
        hard_checks=hard_checks,
    )
    atomic_write_text(PARTIAL_OUTPUT_DIR / "report.md", report_markdown)
    atomic_write_text(PARTIAL_OUTPUT_DIR / "report.html", report_html)

    category_counts = (
        attribution.groupby(
            ["candidate_id", "primary_attribution_category"],
            sort=False,
        )
        .size()
        .rename("count")
        .reset_index()
        .to_dict(orient="records")
    )
    summary = {
        "schema_version": 1,
        "experiment_id": "EXP-024",
        "classification": classification,
        "started_at_utc": started,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "candidate_ids": list(CANDIDATE_IDS),
        "candidate_session_row_count": 51,
        "unique_session_count": 51,
        "primary_representation": PRIMARY_REPRESENTATION,
        "secondary_representation": SECONDARY_REPRESENTATION,
        "known_overlap_only": True,
        "protected_history_accessed": False,
        "current_post_entry_ohlcv_accessed": False,
        "databento_api_calls": 0,
        "network_access": False,
        "strategy_replay": False,
        "exit_evaluation": False,
        "performance_evaluation": False,
        "optimization": False,
        "mcpt": False,
        "bootstrap": False,
        "walk_forward": False,
        "source_winner_selected": False,
        "candidate_winner_selected": False,
        "paper_trading_authorized": False,
        "live_trading_authorized": False,
        "unresolved_count": unresolved_count,
        "category_counts": category_counts,
        "repository": {
            "implementation_commit": preflight[
                "implementation_commit"
            ],
            "authorization_commit": preflight[
                "authorization_commit"
            ],
            "execution_head": preflight["head"],
        },
        "frame_semantic_hashes": first["frame_hashes"],
        "independent_rebuild_hashes": verification["frame_hashes"],
        "hard_checks": hard_checks,
        "hard_failure_count": int(
            sum(not bool(value) for value in hard_checks.values())
        ),
    }
    atomic_write_json(
        PARTIAL_OUTPUT_DIR / "attribution_summary.json",
        summary,
    )
    output_hashes = _output_hashes(PARTIAL_OUTPUT_DIR)
    atomic_write_json(
        PARTIAL_OUTPUT_DIR / "output_hashes.json",
        {"files": output_hashes},
    )
    marker = {
        "experiment_id": "EXP-024",
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
        PARTIAL_OUTPUT_DIR / "ATTRIBUTION_DIAGNOSTIC_COMPLETE.json",
        marker,
    )
    missing = [
        name
        for name in REQUIRED_OUTPUT_NAMES
        if not (PARTIAL_OUTPUT_DIR / name).is_file()
    ]
    if missing:
        raise RuntimeError(
            "EXP-024 outputs are incomplete: " + ", ".join(missing)
        )
    after_snapshot = snapshot_paths(FROZEN_FILE_SPECS)
    if after_snapshot != before_snapshot:
        raise RuntimeError(
            "Frozen evidence changed while writing EXP-024 outputs."
        )
    os.replace(PARTIAL_OUTPUT_DIR, OUTPUT_DIR)
    return summary


def print_preflight(preflight: Mapping[str, Any]) -> None:
    print()
    print("EXP-024 RESULT-FREE PROTECTED PREFLIGHT")
    print("======================================")
    print("Status:          IMPLEMENTED_NOT_AUTHORIZED_NOT_RUN")
    print("Purpose:         frozen mismatch attribution")
    print("Rows:            51 candidate-session mismatches")
    print("Candidates:      3 kept separate")
    print("Market values:   not materialized")
    print("Post-entry data: prohibited")
    print("Protected dates: prohibited")
    print("API/network:     disabled")
    print("Search/MCPT:     disabled")
    print("Paper/live:      not authorized")
    print(f"Git commit:      {preflight['head'][:12]}")
    print("Results:         not calculated")
    print("Next gate:       separate one-time authorization")
    print("======================================")


def print_replacement_preflight(
    preflight: Mapping[str, Any],
) -> None:
    print()
    print("EXP-024 REPLACEMENT RESULT-FREE PREFLIGHT")
    print("=========================================")
    print("Status:          CORRECTED_NOT_REAUTHORIZED_NOT_RUN")
    print("Attempt 001:     failed before attribution")
    print("Correction:      restore projected timestamp index")
    print("Rows:            51 candidate-session mismatches")
    print("Market values:   not materialized by this preflight")
    print("Post-entry data: prohibited")
    print("Protected dates: prohibited")
    print("API/network:     disabled")
    print(f"Git commit:      {preflight['head'][:12]}")
    print("Results:         not calculated")
    print("Next gate:       replacement authorization 002")
    print("=========================================")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Protected EXP-024 source-disagreement attribution."
        )
    )
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument(
        "--preflight",
        action="store_true",
        help="Run the result-free implementation preflight.",
    )
    action.add_argument(
        "--replacement-preflight",
        action="store_true",
        help="Run the result-free replacement-implementation preflight.",
    )
    action.add_argument(
        "--run",
        action="store_true",
        help="Execute the single separately authorized attribution.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.preflight:
        print_preflight(implementation_preflight())
        return
    if args.replacement_preflight:
        print_replacement_preflight(
            replacement_implementation_preflight()
        )
        return
    summary = run_attribution()
    print()
    print("EXP-024 attribution diagnostic complete.")
    print(f"Classification: {summary['classification']}")
    print(f"Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
