from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import shutil
import subprocess
from typing import Any

import numpy as np
import pandas as pd

from exp012_engine import (
    context_feature_table,
    locked_exp012_candidates,
    prepare_exp012_arrays,
    run_exp012_candidate,
)
from exp012_implementation import validate_exp012_implementation
from exp012_measurements import (
    add_pareto_context,
    calculate_exp012_candidate_measurements,
    family_measurement_summary,
    rolling_trade_measurements,
)
from exp012_preregistration import (
    get_exp012_preregistration,
    validate_exp012_preregistration,
)
from exp012_report import build_exp012_report
from experiment_lifecycle import get_experiment_lifecycle
from extended_session_data import OUTPUT_FILES
from extended_session_data_result import (
    EXPECTED_YEAR_COUNTS,
    verify_extended_session_data_result,
)


PROJECT_DIR = Path(__file__).resolve().parent
RESULT_DIR = (
    PROJECT_DIR / "results" / "EXP-012" / "extended_context_tournament"
)
REPORT_DIR = PROJECT_DIR / "reports" / "EXP-012-research-lab"
STAGING_RESULT_DIR = (
    PROJECT_DIR
    / "results"
    / "EXP-012"
    / ".extended_context_tournament_staging"
)
STAGING_REPORT_DIR = (
    PROJECT_DIR / "reports" / ".EXP-012-research-lab-staging"
)


def _run_git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=PROJECT_DIR,
        text=True,
        capture_output=True,
        check=True,
    )
    return completed.stdout.strip()


def git_provenance() -> dict[str, Any]:
    commit = _run_git("rev-parse", "HEAD")
    dirty = bool(_run_git("status", "--porcelain"))
    return {
        "commit": commit,
        "short_commit": commit[:7],
        "working_tree_clean": not dirty,
    }


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return number if math.isfinite(number) else None
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    return value


def _atomic_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(_json_safe(payload), indent=2, allow_nan=False),
        encoding="utf-8",
    )
    temporary.replace(path)


def _verify_lifecycle() -> None:
    expected = {
        "EXP-005": "ACCEPTED_FOR_PAPER_TESTING",
        "EXP-006": "REJECTED",
        "EXP-007": "REJECTED",
        "EXP-008": "REJECTED",
        "EXP-009": "REVIEW",
        "EXP-010": "REVIEW",
        "EXP-011": "REVIEW",
        "EXP-012": "PRE_REGISTERED",
    }
    for experiment_id, stage in expected.items():
        actual = get_experiment_lifecycle(experiment_id).stage
        if actual != stage:
            raise RuntimeError(
                f"{experiment_id} must remain {stage}; found {actual}."
            )


def protected_preflight() -> tuple[dict[str, Any], dict[str, Any]]:
    validate_exp012_preregistration()
    validate_exp012_implementation()
    _verify_lifecycle()
    data_result = verify_extended_session_data_result()

    git = git_provenance()
    if not git["working_tree_clean"]:
        raise RuntimeError(
            "Commit the EXP-012 implementation before preflight or results."
        )
    if RESULT_DIR.exists() and any(
        path.is_file() for path in RESULT_DIR.rglob("*")
    ):
        raise RuntimeError(
            "EXP-012 discovery results already exist. Do not rerun them."
        )

    sessions = sum(
        EXPECTED_YEAR_COUNTS[year]["complete_aligned"]
        for year in range(2020, 2026)
    )
    if sessions != 1331:
        raise RuntimeError(
            f"EXP-012 expected 1,331 frozen sessions; found {sessions:,}."
        )

    print()
    print("EXP-012 IMPLEMENTATION PREFLIGHT")
    print("================================")
    print("Lifecycle:       PRE_REGISTERED")
    print("Implementation:  IMPLEMENTED_NOT_RUN")
    print("Purpose:         extended-context discovery measurement")
    print("Families:        6")
    print("Candidates:      24 locked configurations")
    print("Markets:         NQ primary / MNQ implementation comparison")
    print("Sessions:        1,331 aligned 2020-2025 sessions")
    print(
        "Data foundation: "
        f"{data_result['complete_aligned_sessions']:,} frozen sessions"
    )
    print("Context:         overnight, premarket and opening gap")
    print("Entries:         cash session only")
    print("Execution:       5-minute signals / 1-minute sequencing")
    print("Position size:   fixed one contract")
    print("NQ costs:        0, 1 and 2 ticks per side")
    print("Automatic winner: False")
    print("Formal gates:     False")
    print("MCPT/bootstrap/walk-forward: deferred")
    print(f"Git commit:       {git['short_commit']}")
    print("Git clean:        True")
    print("Frozen data changed: False")
    print("Prior experiments changed: False")
    print("Results:          not calculated")
    print("================================")
    return git, data_result


def _write_candidate_outputs(
    *,
    result_root: Path,
    candidate_id: str,
    nq_result: Any,
    mnq_result: Any,
    zero_result: Any,
    two_result: Any,
) -> None:
    directory = result_root / "candidates" / candidate_id
    directory.mkdir(parents=True, exist_ok=True)
    nq_result.trades.to_csv(directory / "nq_trades.csv", index=False)
    nq_result.equity_curve.to_csv(
        directory / "nq_equity_curve.csv", index=False
    )
    nq_result.yearly_results.to_csv(
        directory / "nq_yearly_results.csv", index=False
    )
    rolling_trade_measurements(nq_result.trades).to_csv(
        directory / "nq_rolling_100_trades.csv", index=False
    )
    mnq_result.trades.to_csv(directory / "mnq_trades.csv", index=False)
    mnq_result.equity_curve.to_csv(
        directory / "mnq_equity_curve.csv", index=False
    )
    pd.DataFrame(
        [
            {
                **zero_result.summary,
                "slippage_ticks_per_side": 0.0,
            },
            {
                **nq_result.summary,
                "slippage_ticks_per_side": 1.0,
            },
            {
                **two_result.summary,
                "slippage_ticks_per_side": 2.0,
            },
        ]
    ).to_csv(directory / "nq_cost_sensitivity.csv", index=False)


def _load_arrays() -> tuple[Any, Any]:
    nq = pd.read_parquet(OUTPUT_FILES["NQ_1m"])
    mnq = pd.read_parquet(OUTPUT_FILES["MNQ_1m"])
    nq_arrays = prepare_exp012_arrays(
        nq, require_production_session_count=True
    )
    mnq_arrays = prepare_exp012_arrays(
        mnq, require_production_session_count=True
    )
    if not np.array_equal(
        nq_arrays.session_dates, mnq_arrays.session_dates
    ):
        raise RuntimeError("EXP-012 NQ/MNQ session alignment changed.")
    return nq_arrays, mnq_arrays


def run_tournament() -> None:
    git, _ = protected_preflight()
    nq_arrays, mnq_arrays = _load_arrays()
    candidates = locked_exp012_candidates()

    measurements: list[dict[str, Any]] = []
    nq_results: dict[str, Any] = {}
    bundles: dict[str, tuple[Any, Any, Any, Any]] = {}

    print()
    print("========== EXP-012 EXTENDED-CONTEXT TOURNAMENT ==========")
    print("Running all 24 candidates under the locked common standard.")
    print("No automatic winner, validation claim, MCPT or bootstrap.")
    print()

    for index, candidate in enumerate(candidates, start=1):
        print(
            f"[{index:02d}/24] {candidate.family_id}: "
            f"{candidate.candidate_id}"
        )
        nq_result = run_exp012_candidate(
            nq_arrays,
            candidate,
            symbol="NQ",
            slippage_ticks_per_side=1.0,
        )
        mnq_result = run_exp012_candidate(
            mnq_arrays,
            candidate,
            symbol="MNQ",
            slippage_ticks_per_side=1.0,
        )
        zero_result = run_exp012_candidate(
            nq_arrays,
            candidate,
            symbol="NQ",
            slippage_ticks_per_side=0.0,
        )
        two_result = run_exp012_candidate(
            nq_arrays,
            candidate,
            symbol="NQ",
            slippage_ticks_per_side=2.0,
        )
        measurements.append(
            calculate_exp012_candidate_measurements(
                nq_result,
                mnq_result,
                nq_zero_tick_result=zero_result,
                nq_two_tick_result=two_result,
                included_session_count=nq_arrays.session_count,
            )
        )
        nq_results[candidate.candidate_id] = nq_result
        bundles[candidate.candidate_id] = (
            nq_result,
            mnq_result,
            zero_result,
            two_result,
        )

    candidate_table = add_pareto_context(
        pd.DataFrame.from_records(measurements)
    )
    family_table = family_measurement_summary(candidate_table)

    for staging in (STAGING_RESULT_DIR, STAGING_REPORT_DIR):
        resolved = staging.resolve()
        if PROJECT_DIR.resolve() not in resolved.parents:
            raise RuntimeError("EXP-012 staging path escaped the project.")
        if staging.exists():
            shutil.rmtree(staging)
    STAGING_RESULT_DIR.mkdir(parents=True, exist_ok=False)

    for candidate_id, bundle in bundles.items():
        _write_candidate_outputs(
            result_root=STAGING_RESULT_DIR,
            candidate_id=candidate_id,
            nq_result=bundle[0],
            mnq_result=bundle[1],
            zero_result=bundle[2],
            two_result=bundle[3],
        )

    candidate_table.to_csv(
        STAGING_RESULT_DIR / "candidate_measurements.csv", index=False
    )
    family_table.to_csv(
        STAGING_RESULT_DIR / "family_measurements.csv", index=False
    )
    context_feature_table(nq_arrays).to_csv(
        STAGING_RESULT_DIR / "nq_extended_context_features.csv",
        index=False,
    )
    context_feature_table(mnq_arrays).to_csv(
        STAGING_RESULT_DIR / "mnq_extended_context_features.csv",
        index=False,
    )

    benchmark = pd.DataFrame(
        {
            "session_date": nq_arrays.session_dates,
            "nq_normalized_price_benchmark": (
                100_000.0
                * nq_arrays.cash.close[:, -1]
                / nq_arrays.cash.close[0, -1]
            ),
        }
    )
    for candidate_id, result in nq_results.items():
        session_pnl = (
            result.trades.groupby("session_date")["net_pnl_usd"].sum()
            if not result.trades.empty
            else pd.Series(dtype=float)
        )
        benchmark[candidate_id] = (
            100_000.0
            + pd.Series(nq_arrays.session_dates)
            .map(session_pnl)
            .fillna(0.0)
            .cumsum()
            .to_numpy(dtype=float)
        )
    benchmark.to_csv(
        STAGING_RESULT_DIR / "normalized_equity_comparison.csv",
        index=False,
    )

    prereg = get_exp012_preregistration()
    metadata = {
        "experiment_id": "EXP-012",
        "completed_utc": datetime.now(timezone.utc).isoformat(),
        "git": git,
        "included_sessions": nq_arrays.session_count,
        "candidate_count": len(candidate_table),
        "family_count": int(candidate_table["family_id"].nunique()),
        "automatic_winner": False,
        "formal_accept_reject_gates": False,
        "mcpt_run": False,
        "bootstrap_run": False,
        "walk_forward_run": False,
        "family_optimization_run": False,
        "overnight_entries": False,
        "maximum_later_finalists": 3,
        "result_status": "MEASURED_AWAITING_USER_REVIEW",
        "paper_trading_authorized": False,
        "live_trading_authorized": False,
        "candidate_ids": list(candidate_table["candidate_id"]),
        "preregistration_interpretation": prereg["interpretation"],
    }
    report = build_exp012_report(
        candidate_table=candidate_table,
        nq_results=nq_results,
        arrays=nq_arrays,
        report_dir=STAGING_REPORT_DIR,
        metadata=metadata,
    )
    _atomic_json(
        metadata, STAGING_RESULT_DIR / "tournament_manifest.json"
    )

    if RESULT_DIR.exists() or REPORT_DIR.exists():
        raise RuntimeError(
            "EXP-012 final output path appeared during the protected run."
        )
    STAGING_RESULT_DIR.replace(RESULT_DIR)
    STAGING_REPORT_DIR.replace(REPORT_DIR)
    report = REPORT_DIR / report.name

    print()
    print("EXP-012 extended-context discovery completed.")
    print("Status: MEASURED_AWAITING_USER_REVIEW")
    print("Candidates measured: 24/24")
    print("Families measured: 6/6")
    print("Automatic winner selected: False")
    print("MCPT/bootstrap/walk-forward run: False")
    print(f"Measurements: {RESULT_DIR / 'candidate_measurements.csv'}")
    print(f"Report: {report}")
    print("No paper or live trading is authorized.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Protected EXP-012 extended-context tournament."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--preflight",
        action="store_true",
        help="Validate the committed implementation without results.",
    )
    mode.add_argument(
        "--run",
        action="store_true",
        help="Run the one-time protected discovery measurement.",
    )
    args = parser.parse_args()
    if args.preflight:
        protected_preflight()
        print(
            "Preflight passed. No EXP-012 strategy, candidate, cost, "
            "comparison or report result was calculated."
        )
    else:
        run_tournament()


if __name__ == "__main__":
    main()
