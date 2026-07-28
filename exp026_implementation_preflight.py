from __future__ import annotations

# EXP-026-I1: pre-result authorization-lifecycle compatibility correction.

import os
from pathlib import Path
import subprocess
from typing import Any

from exp026_core import (
    ALL_CANDIDATE_IDS,
    CONTROL_CANDIDATE_IDS,
    DEVELOPMENT_CANDIDATE_IDS,
    validate_candidate_specs,
)
from exp026_preregistration import (
    EXPECTED_EXP026_PREREGISTRATION_SHA256,
    canonical_record_hash,
    get_exp026_preregistration,
    validate_exp026_preregistration,
)
from exp026_runner import (
    IMPLEMENTATION_PATHS,
    LOCKED_PREREGISTRATION_COMMIT,
    PHASE_AUTHORIZATION_MODULES,
    PHASE_COMPLETION_MODULES,
    PHASE_OUTPUT_DIRS,
    PHASE_PARTIAL_DIRS,
    PREREGISTRATION_PATHS,
    PROJECT_DIR,
    REPRESENTATION_FILES,
    changed_paths,
    inspect_parquet_metadata,
    latest_commit,
    verify_frozen_series_bytes,
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
            "DATABENTO_API_KEY must not be set for "
            "EXP-026 implementation preflight."
        )
    if run_git(
        "status",
        "--porcelain",
    ).stdout.strip():
        raise RuntimeError(
            "Repository must be clean before "
            "EXP-026 implementation preflight."
        )
    branch = run_git(
        "branch",
        "--show-current",
    ).stdout.strip()
    if branch != "main":
        raise RuntimeError(
            f"EXP-026 preflight requires main, "
            f"found {branch!r}."
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

    commits = {
        latest_commit(path)
        for path in IMPLEMENTATION_PATHS
    }
    if len(commits) != 1:
        raise RuntimeError(
            "EXP-026 implementation files lack one "
            "shared commit."
        )
    implementation_commit = next(iter(commits))
    if implementation_commit != head:
        raise RuntimeError(
            "EXP-026 implementation commit must equal HEAD."
        )
    if changed_paths(
        LOCKED_PREREGISTRATION_COMMIT,
        implementation_commit,
    ) != set(IMPLEMENTATION_PATHS):
        raise RuntimeError(
            "EXP-026 implementation scope changed."
        )

    validate_exp026_preregistration()
    record = get_exp026_preregistration()
    if (
        canonical_record_hash(record)
        != EXPECTED_EXP026_PREREGISTRATION_SHA256
    ):
        raise RuntimeError(
            "EXP-026 preregistration hash changed."
        )
    validate_candidate_specs()

    for module_name in (
        *PHASE_AUTHORIZATION_MODULES.values(),
        *PHASE_COMPLETION_MODULES.values(),
    ):
        if (
            PROJECT_DIR / (module_name + ".py")
        ).exists():
            raise RuntimeError(
                "No EXP-026 phase authorization or "
                "completion module may exist during "
                "implementation preflight."
            )
    for path in (
        *PHASE_OUTPUT_DIRS.values(),
        *PHASE_PARTIAL_DIRS.values(),
    ):
        if path.exists():
            raise RuntimeError(
                "EXP-026 output unexpectedly exists "
                "before phase authorization."
            )

    try:
        import matplotlib
        import pyarrow
    except ImportError as exc:
        raise RuntimeError(
            "EXP-026 requires installed matplotlib "
            "and pyarrow."
        ) from exc

    frozen = verify_frozen_series_bytes()
    metadata = inspect_parquet_metadata()

    return {
        "branch": branch,
        "head": head,
        "origin_main": origin_main,
        "preregistration_commit": (
            LOCKED_PREREGISTRATION_COMMIT
        ),
        "implementation_commit": (
            implementation_commit
        ),
        "preregistration_sha256": (
            EXPECTED_EXP026_PREREGISTRATION_SHA256
        ),
        "development_candidates": len(
            DEVELOPMENT_CANDIDATE_IDS
        ),
        "fixed_controls": len(
            CONTROL_CANDIDATE_IDS
        ),
        "reported_candidates": len(
            ALL_CANDIDATE_IDS
        ),
        "series_verified": len(
            frozen["series_snapshot"]
        ),
        "series_rows_each": tuple(
            metadata[
                representation_id
            ]["row_count"]
            for representation_id in (
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
        "phase_a_authorized": False,
        "phase_b_authorized": False,
        "phase_c_authorized": False,
        "protected_2026_accessed": False,
        "databento_api_calls": 0,
        "strategy_results_calculated": False,
        "paper_trading_authorized": False,
        "live_trading_authorized": False,
    }


def main() -> None:
    result = implementation_preflight()
    print(
        "EXP-026 IMPLEMENTATION PREFLIGHT PASSED"
    )
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
        "Development candidates:         "
        f"{result['development_candidates']}"
    )
    print(
        "Fixed controls:                 "
        f"{result['fixed_controls']}"
    )
    print(
        "Reported candidates:            "
        f"{result['reported_candidates']}"
    )
    print(
        "Frozen series verified:         "
        f"{result['series_verified']}"
    )
    print(
        "Rows per series:                "
        f"{result['series_rows_each'][0]:,}"
    )
    print(
        "Market values materialized:     False"
    )
    print(
        "Phase A execution authorized:   False"
    )
    print(
        "Protected 2026 accessed:        False"
    )
    print(
        "Databento API calls:            0"
    )
    print(
        "Strategy results calculated:    False"
    )
    print(
        "Paper/live trading:             False"
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
