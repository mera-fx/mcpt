from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
from typing import Any, Mapping

import pandas as pd

from exp025_exact_contract_core import (
    EXPECTED_QUANTOWER_FILES,
    QUANTOWER_REQUIRED_COLUMNS,
)
from exp025_exact_contract_diagnostic import (
    EXECUTION_AUTHORIZATION_PATH,
    OUTPUT_DIR,
    PARTIAL_OUTPUT_DIR,
    PROJECT_DIR,
    QUANTOWER_ROOT,
    load_population,
    repository_state_preflight,
    verify_archive_bytes,
    verify_exp024_outputs,
    verify_session_quality_metadata,
)
from exp025_quantower_export_authorization import (
    get_exp025_quantower_export_authorization,
    validate_exp025_quantower_export_authorization,
)


PLAN_PATH = (
    PROJECT_DIR
    / "research"
    / "EXP-025_quantower_export_plan.csv"
)
STAGING_ROOT = (
    PROJECT_DIR
    / "data"
    / "EXP-025"
    / "quantower_export_staging"
)

AUTHORIZATION_PATHS = (
    "exp025_quantower_export_authorization.py",
    "exp025_quantower_export_preflight.py",
    "research/EXP-025_quantower_export_plan.csv",
    "research/EXP-025_quantower_export_authorization.md",
    "tests/test_exp025_quantower_export_authorization.py",
)

PLAN_COLUMNS = (
    "sequence",
    "session_date",
    "previous_session_date",
    "explicit_contract_symbol",
    "previous_window_start_new_york",
    "previous_window_end_new_york",
    "current_window_start_new_york",
    "current_window_end_new_york",
    "previous_export_path",
    "current_export_path",
    "final_relative_path",
    "source",
    "resolution",
    "timestamp_timezone",
    "required_columns",
    "pretrimmed_to_allowed_windows",
)


def run_git(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=PROJECT_DIR,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def latest_commit(relative_path: str) -> str:
    value = run_git(
        "log",
        "-1",
        "--format=%H",
        "--",
        relative_path,
    )
    if not value:
        raise RuntimeError(
            f"No commit found for authorization file: {relative_path}"
        )
    return value


def verify_plan(
    population: pd.DataFrame,
    authorization: Mapping[str, Any],
) -> pd.DataFrame:
    if not PLAN_PATH.is_file():
        raise RuntimeError("EXP-025 Quantower export plan is missing.")

    if sha256_file(PLAN_PATH) != authorization["export_plan_sha256"]:
        raise RuntimeError("EXP-025 Quantower export plan hash changed.")

    plan = pd.read_csv(
        PLAN_PATH,
        dtype=str,
        keep_default_na=False,
    )

    if tuple(plan.columns) != PLAN_COLUMNS:
        raise RuntimeError("EXP-025 export-plan columns changed.")
    if len(plan) != EXPECTED_QUANTOWER_FILES:
        raise RuntimeError(
            f"EXP-025 requires 43 export-plan rows, found {len(plan)}."
        )
    if plan["session_date"].nunique() != EXPECTED_QUANTOWER_FILES:
        raise RuntimeError("EXP-025 export-plan sessions are not unique.")

    sequences = [int(value) for value in plan["sequence"]]
    if sequences != list(range(1, EXPECTED_QUANTOWER_FILES + 1)):
        raise RuntimeError("EXP-025 export-plan sequence changed.")

    expected = population.loc[
        :,
        [
            "session_date",
            "previous_session_date",
            "exact_contract_symbol",
        ],
    ].copy()
    expected = expected.rename(
        columns={
            "exact_contract_symbol": "explicit_contract_symbol",
        }
    )
    expected = expected.astype(str).reset_index(drop=True)

    actual = plan.loc[
        :,
        [
            "session_date",
            "previous_session_date",
            "explicit_contract_symbol",
        ],
    ].reset_index(drop=True)

    if not actual.equals(expected):
        raise RuntimeError(
            "EXP-025 export plan no longer matches the frozen population."
        )

    required_columns = "|".join(QUANTOWER_REQUIRED_COLUMNS)

    for row in plan.itertuples(index=False):
        sequence = int(row.sequence)
        basename = (
            f"{sequence:02d}_{row.session_date}_"
            f"{row.explicit_contract_symbol}"
        )

        expected_values = {
            "previous_window_start_new_york": (
                f"{row.previous_session_date} 09:30:00"
            ),
            "previous_window_end_new_york": (
                f"{row.previous_session_date} 15:59:00"
            ),
            "current_window_start_new_york": (
                f"{row.session_date} 09:30:00"
            ),
            "current_window_end_new_york": (
                f"{row.session_date} 09:35:00"
            ),
            "previous_export_path": (
                "data/EXP-025/quantower_export_staging/"
                f"{basename}_previous.csv"
            ),
            "current_export_path": (
                "data/EXP-025/quantower_export_staging/"
                f"{basename}_current.csv"
            ),
            "final_relative_path": f"raw/{basename}.csv",
            "source": (
                "Lucid/Rithmic via Quantower History Exporter"
            ),
            "resolution": "1 minute",
            "timestamp_timezone": "America/New_York",
            "required_columns": required_columns,
            "pretrimmed_to_allowed_windows": "true",
        }

        for field, expected_value in expected_values.items():
            if str(getattr(row, field)) != expected_value:
                raise RuntimeError(
                    "EXP-025 export-plan field changed: "
                    f"{field} for {row.session_date}."
                )

    return plan


def export_preflight() -> dict[str, Any]:
    state = repository_state_preflight()

    validate_exp025_quantower_export_authorization()
    authorization = (
        get_exp025_quantower_export_authorization()
    )

    if (
        state["implementation_commit"]
        != authorization["implementation_commit"]
    ):
        raise RuntimeError(
            "EXP-025 export authorization targets the wrong "
            "implementation commit."
        )

    authorization_commits = {
        latest_commit(path) for path in AUTHORIZATION_PATHS
    }
    if len(authorization_commits) != 1:
        raise RuntimeError(
            "EXP-025 export authorization files lack one shared commit."
        )

    authorization_commit = next(iter(authorization_commits))
    if authorization_commit != state["head"]:
        raise RuntimeError(
            "EXP-025 export authorization commit must equal HEAD."
        )

    if EXECUTION_AUTHORIZATION_PATH.exists():
        raise RuntimeError(
            "EXP-025 diagnostic execution authorization must be absent."
        )
    if QUANTOWER_ROOT.exists():
        raise RuntimeError(
            "Quantower evidence directory already exists before "
            "export preflight."
        )
    if STAGING_ROOT.exists():
        raise RuntimeError(
            "Quantower staging directory already exists before "
            "export preflight."
        )
    if OUTPUT_DIR.exists() or PARTIAL_OUTPUT_DIR.exists():
        raise RuntimeError(
            "EXP-025 diagnostic output unexpectedly exists."
        )

    exp024_snapshot = verify_exp024_outputs()
    session_snapshot = verify_session_quality_metadata()
    _, _, archive_snapshot = verify_archive_bytes()

    population = load_population()
    plan = verify_plan(population, authorization)

    return {
        **state,
        "authorization_commit": authorization_commit,
        "population_rows": int(len(population)),
        "unique_contracts": int(
            plan["explicit_contract_symbol"].nunique()
        ),
        "authorized_window_exports": int(
            authorization["authorized_window_export_count"]
        ),
        "authorized_final_files": int(
            authorization["authorized_final_file_count"]
        ),
        "exp024_files_verified": int(len(exp024_snapshot)),
        "session_calendars_verified": int(len(session_snapshot)),
        "archive_files_verified": int(len(archive_snapshot)),
        "market_values_materialized": False,
        "diagnostic_execution_authorized": False,
        "strategy_performance_calculated": False,
        "paper_trading_authorized": False,
        "live_trading_authorized": False,
    }


def main() -> None:
    result = export_preflight()

    print("EXP-025 QUANTOWER EXPORT PREFLIGHT PASSED")
    print(f"Branch:                         {result['branch']}")
    print(f"HEAD:                           {result['head']}")
    print(
        "Implementation commit:          "
        f"{result['implementation_commit']}"
    )
    print(
        "Export authorization commit:    "
        f"{result['authorization_commit']}"
    )
    print(
        "Frozen unresolved sessions:     "
        f"{result['population_rows']}"
    )
    print(
        "Unique exact contracts:          "
        f"{result['unique_contracts']}"
    )
    print(
        "Authorized window exports:       "
        f"{result['authorized_window_exports']}"
    )
    print(
        "Required final evidence files:   "
        f"{result['authorized_final_files']}"
    )
    print(
        "Frozen archive files verified:  "
        f"{result['archive_files_verified']}"
    )
    print(
        "Frozen session calendars verified:"
        f"{result['session_calendars_verified']:>4}"
    )
    print("Market values materialized:     False")
    print("Diagnostic execution authorized:False")
    print("Strategy performance:           False")
    print("Paper/live trading:             False")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=__import__("sys").stderr)
        raise SystemExit(1)
