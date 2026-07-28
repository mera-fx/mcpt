from __future__ import annotations

import os
from pathlib import Path
import subprocess
from typing import Any

from exp026_runner import (
    inspect_parquet_metadata,
    verify_frozen_series_bytes,
)
from exp027_core import (
    exp027_control_ids,
    exp027_candidate_ids,
    exp027_reported_ids,
    primary_cohort_ids,
    validate_exp027_population,
)
from exp027_preregistration import (
    EXPECTED_EXP027_PREREGISTRATION_SHA256,
    canonical_record_hash,
    get_exp027_preregistration,
    validate_exp027_preregistration,
)
from exp027_runner import (
    AUTHORIZATION_PATHS,
    IMPLEMENTATION_PATHS,
    LOCKED_EXP026_IMPLEMENTATION_COMMIT,
    LOCKED_PREREGISTRATION_COMMIT,
    OUTPUT_DIR,
    PARTIAL_DIR,
    PREREGISTRATION_PATHS,
    PROJECT_DIR,
    changed_paths,
    latest_commit,
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


def implementation_preflight() -> dict[str, Any]:
    if os.environ.get(
        "DATABENTO_API_KEY",
        "",
    ).strip():
        raise RuntimeError(
            "DATABENTO_API_KEY must be unset for "
            "EXP-027 implementation preflight."
        )
    if run_git(
        "status",
        "--porcelain",
    ).stdout.strip():
        raise RuntimeError(
            "Repository must be clean before "
            "EXP-027 implementation preflight."
        )
    branch = run_git(
        "branch",
        "--show-current",
    ).stdout.strip()
    if branch != "main":
        raise RuntimeError(
            f"EXP-027 preflight requires main, found {branch!r}."
        )
    head = run_git(
        "rev-parse",
        "HEAD",
    ).stdout.strip()
    origin = run_git(
        "rev-parse",
        "origin/main",
    ).stdout.strip()
    if head != origin:
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
            "Locked EXP-027 preregistration is not an ancestor."
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
            "Locked EXP-027 preregistration files changed."
        )

    commits = {
        latest_commit(path)
        for path in IMPLEMENTATION_PATHS
    }
    if len(commits) != 1:
        raise RuntimeError(
            "EXP-027 implementation files lack one shared commit."
        )
    implementation_commit = next(iter(commits))
    if implementation_commit != head:
        raise RuntimeError(
            "EXP-027 implementation commit must equal HEAD."
        )
    if changed_paths(
        LOCKED_PREREGISTRATION_COMMIT,
        implementation_commit,
    ) != set(IMPLEMENTATION_PATHS):
        raise RuntimeError(
            "EXP-027 implementation commit scope changed."
        )

    exp026_core_commit = latest_commit(
        "exp026_core.py"
    )
    if (
        exp026_core_commit
        != LOCKED_EXP026_IMPLEMENTATION_COMMIT
    ):
        raise RuntimeError(
            "Frozen EXP-026 execution engine changed."
        )

    validate_exp027_preregistration()
    record = get_exp027_preregistration()
    if (
        canonical_record_hash(record)
        != EXPECTED_EXP027_PREREGISTRATION_SHA256
    ):
        raise RuntimeError(
            "EXP-027 preregistration hash changed."
        )
    validate_exp027_population()

    for relative_path in AUTHORIZATION_PATHS:
        if (
            PROJECT_DIR / relative_path
        ).exists():
            raise RuntimeError(
                "No EXP-027 authorization file may exist "
                "during implementation preflight."
            )
    if OUTPUT_DIR.exists() or PARTIAL_DIR.exists():
        raise RuntimeError(
            "EXP-027 result output exists before authorization."
        )

    try:
        import matplotlib
        import pyarrow
    except ImportError as exc:
        raise RuntimeError(
            "EXP-027 requires installed matplotlib and pyarrow."
        ) from exc

    frozen = verify_frozen_series_bytes()
    metadata = inspect_parquet_metadata()

    return {
        "branch": branch,
        "head": head,
        "origin_main": origin,
        "preregistration_commit": (
            LOCKED_PREREGISTRATION_COMMIT
        ),
        "implementation_commit": implementation_commit,
        "exp026_core_commit": exp026_core_commit,
        "preregistration_sha256": (
            EXPECTED_EXP027_PREREGISTRATION_SHA256
        ),
        "strategy_candidates": len(
            exp027_candidate_ids()
        ),
        "fixed_controls": len(
            exp027_control_ids()
        ),
        "reported_series": len(
            exp027_reported_ids()
        ),
        "primary_cohort": len(
            primary_cohort_ids()
        ),
        "series_verified": len(
            frozen["series_snapshot"]
        ),
        "series_rows_each": tuple(
            metadata[key]["row_count"]
            for key in (
                "BACKWARD_ADJUSTED",
                "UNADJUSTED",
            )
        ),
        "matplotlib_version": getattr(
            matplotlib,
            "__version__",
            "unknown",
        ),
        "pyarrow_version": getattr(
            pyarrow,
            "__version__",
            "unknown",
        ),
        "market_values_materialized": False,
        "protected_2026_accessed": False,
        "historical_market_values_accessed": False,
        "strategy_results_calculated": False,
        "execution_authorized": False,
        "databento_api_calls": 0,
        "paper_trading_authorized": False,
        "live_trading_authorized": False,
    }


def main() -> None:
    result = implementation_preflight()
    print("EXP-027 IMPLEMENTATION PREFLIGHT PASSED")
    print(
        "Branch:                         "
        f"{result['branch']}"
    )
    print(
        "HEAD:                           "
        f"{result['head']}"
    )
    print(
        "Preregistration commit:         "
        f"{result['preregistration_commit']}"
    )
    print(
        "Implementation commit:          "
        f"{result['implementation_commit']}"
    )
    print(
        "Frozen EXP-026 engine commit:   "
        f"{result['exp026_core_commit']}"
    )
    print(
        "Strategy candidates:            "
        f"{result['strategy_candidates']}"
    )
    print(
        "Fixed controls:                 "
        f"{result['fixed_controls']}"
    )
    print(
        "Reported canonical series:      "
        f"{result['reported_series']}"
    )
    print(
        "Primary cohort:                 "
        f"{result['primary_cohort']}"
    )
    print(
        "Frozen series verified:         "
        f"{result['series_verified']}"
    )
    print(
        "Rows per frozen series:         "
        f"{result['series_rows_each'][0]:,}"
    )
    print("Market values materialized:     False")
    print("Protected 2026 accessed:        False")
    print("Historical values accessed:     False")
    print("Strategy results calculated:    False")
    print("Execution authorized:           False")
    print("Databento API calls:            0")
    print("Paper/live trading:             False")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(
            f"ERROR: {exc}",
            file=__import__("sys").stderr,
        )
        raise SystemExit(1)
