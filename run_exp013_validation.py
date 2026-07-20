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
    get_exp012_candidate,
    prepare_exp012_arrays,
    run_exp012_candidate,
)
from exp012_measurements import calculate_exp012_candidate_measurements
from exp012_tournament_result import verify_local_exp012_tournament_result
from exp013_bootstrap import bootstrap_exp013_trade_metrics
from exp013_evaluation import evaluate_exp013_evidence
from exp013_implementation import validate_exp013_implementation
from exp013_preregistration import (
    get_exp013_preregistration,
    validate_exp013_preregistration,
)
from exp013_report import build_exp013_report
from exp013_selection import (
    FINALIST_IDS,
    locked_exp013_candidates,
    select_exp013_measurement_leader,
    selected_exp013_row,
)
from exp013_selection_mcpt import run_exp013_discovery_mcpt
from exp013_walk_forward import run_exp013_anchored_walk_forward
from experiment_lifecycle import get_experiment_lifecycle
from extended_session_data import OUTPUT_FILES
from extended_session_data_result import (
    EXPECTED_OUTPUTS,
    verify_extended_session_data_result,
)


PROJECT_DIR = Path(__file__).resolve().parent
RESULT_DIR = (
    PROJECT_DIR / "results" / "EXP-013" / "extended_context_validation"
)
REPORT_DIR = PROJECT_DIR / "reports" / "EXP-013-research-lab"
STAGING_RESULT_DIR = (
    PROJECT_DIR
    / "results"
    / "EXP-013"
    / ".extended_context_validation_staging"
)
STAGING_REPORT_DIR = (
    PROJECT_DIR / "reports" / ".EXP-013-research-lab-staging"
)
RESULT_FILE = RESULT_DIR / "validation_result.json"
CHECKPOINT_FILE = RESULT_DIR / "mcpt_checkpoint.json"


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
    return {
        "commit": commit,
        "short_commit": commit[:7],
        "working_tree_clean": not bool(
            _run_git("status", "--porcelain")
        ),
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
        "EXP-012": "REVIEW",
        "EXP-013": "PRE_REGISTERED",
    }
    for experiment_id, stage in expected.items():
        actual = get_experiment_lifecycle(experiment_id).stage
        if actual != stage:
            raise RuntimeError(
                f"{experiment_id} must remain {stage}; found {actual}."
            )


def protected_preflight() -> tuple[dict[str, Any], dict[str, Any]]:
    validate_exp013_preregistration()
    validate_exp013_implementation()
    _verify_lifecycle()
    frozen_exp012 = verify_local_exp012_tournament_result()
    verify_extended_session_data_result()
    git = git_provenance()
    if not git["working_tree_clean"]:
        raise RuntimeError(
            "Commit the EXP-013 implementation before preflight or results."
        )
    if RESULT_FILE.exists():
        raise RuntimeError(
            "EXP-013 already has a frozen result. Do not rerun it."
        )
    unexpected = []
    if RESULT_DIR.exists():
        unexpected = [
            path
            for path in RESULT_DIR.rglob("*")
            if path.is_file() and path != CHECKPOINT_FILE
        ]
    if unexpected:
        raise RuntimeError(
            "Unexpected partial EXP-013 output exists: "
            + ", ".join(str(path) for path in unexpected)
        )
    if REPORT_DIR.exists() and any(
        path.is_file() for path in REPORT_DIR.rglob("*")
    ):
        raise RuntimeError(
            "An EXP-013 report already exists without a frozen result."
        )
    print()
    print("EXP-013 IMPLEMENTATION PREFLIGHT")
    print("================================")
    print("Lifecycle:       PRE_REGISTERED")
    print("Implementation:  IMPLEMENTED_NOT_RUN")
    print("Finalists:       3 locked EXP-012 review candidates")
    print("Source search:   24 candidates inside every primary MCPT")
    print("Sessions:        1,331 aligned 2020-2025 sessions")
    print("Walk-forward:    4 anchored annual folds")
    print("Bootstrap:       10,000 resamples per finalist")
    print("NQ MCPT:         1,000 discovery-wide permutations")
    print("Permutation:     1,320 exact extended-session minute slots")
    print(f"Git commit:      {git['short_commit']}")
    print("Git clean:       True")
    print("EXP-012 hash-verified: True")
    print("Results:         not calculated")
    print("================================")
    return git, frozen_exp012


def _load_data() -> tuple[pd.DataFrame, Any, Any]:
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
        raise RuntimeError("EXP-013 NQ/MNQ session alignment changed.")
    return nq, nq_arrays, mnq_arrays


def _run_candidate_bundle(
    nq_arrays: Any,
    mnq_arrays: Any,
) -> tuple[
    pd.DataFrame,
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    pd.DataFrame,
]:
    measurements = []
    nq_results: dict[str, Any] = {}
    mnq_results: dict[str, Any] = {}
    two_tick_results: dict[str, Any] = {}
    cost_rows = []
    for candidate in locked_exp013_candidates():
        base = run_exp012_candidate(
            nq_arrays, candidate, symbol="NQ", slippage_ticks_per_side=1
        )
        mnq = run_exp012_candidate(
            mnq_arrays, candidate, symbol="MNQ", slippage_ticks_per_side=1
        )
        zero = run_exp012_candidate(
            nq_arrays, candidate, symbol="NQ", slippage_ticks_per_side=0
        )
        two = run_exp012_candidate(
            nq_arrays, candidate, symbol="NQ", slippage_ticks_per_side=2
        )
        measurements.append(
            calculate_exp012_candidate_measurements(
                base,
                mnq,
                nq_zero_tick_result=zero,
                nq_two_tick_result=two,
                included_session_count=nq_arrays.session_count,
            )
        )
        nq_results[candidate.candidate_id] = base
        mnq_results[candidate.candidate_id] = mnq
        two_tick_results[candidate.candidate_id] = two
        for ticks, result in ((0, zero), (1, base), (2, two)):
            cost_rows.append(
                {
                    "candidate_id": candidate.candidate_id,
                    "slippage_ticks_per_side": ticks,
                    "completed_trades": int(
                        result.summary["completed_trades"]
                    ),
                    "trade_profit_factor": float(
                        result.summary["trade_profit_factor"]
                    ),
                    "net_profit_usd": float(
                        result.summary["net_profit_usd"]
                    ),
                    "average_trade_usd": float(
                        result.summary["average_trade_usd"]
                    ),
                    "maximum_drawdown_usd": float(
                        result.summary["maximum_drawdown_usd"]
                    ),
                }
            )
    selection = select_exp013_measurement_leader(
        pd.DataFrame.from_records(measurements)
    )
    return (
        selection.scored_candidates,
        nq_results,
        mnq_results,
        two_tick_results,
        pd.DataFrame.from_records(cost_rows),
    )


def _write_candidate_outputs(
    root: Path,
    candidate_id: str,
    *,
    nq_result: Any,
    mnq_result: Any,
) -> None:
    directory = root / "candidates" / candidate_id
    directory.mkdir(parents=True, exist_ok=True)
    nq_result.trades.to_csv(directory / "nq_trades.csv", index=False)
    nq_result.equity_curve.to_csv(
        directory / "nq_equity_curve.csv", index=False
    )
    nq_result.yearly_results.to_csv(
        directory / "nq_yearly_results.csv", index=False
    )
    mnq_result.trades.to_csv(directory / "mnq_trades.csv", index=False)
    mnq_result.equity_curve.to_csv(
        directory / "mnq_equity_curve.csv", index=False
    )


def run_validation(*, workers: int) -> None:
    git, frozen_exp012 = protected_preflight()
    nq_frame, nq_arrays, mnq_arrays = _load_data()
    print()
    print("========== EXP-013 THREE-FINALIST VALIDATION ==========")
    print("Running three locked finalist measurements...")
    (
        candidate_table,
        nq_results,
        mnq_results,
        two_tick_results,
        cost_sensitivity,
    ) = _run_candidate_bundle(nq_arrays, mnq_arrays)
    frozen_table = frozen_exp012["candidates"].set_index("candidate_id")
    for candidate_id in FINALIST_IDS:
        row = candidate_table.loc[
            candidate_table["candidate_id"].eq(candidate_id)
        ].iloc[0]
        if not np.isclose(
            float(row["trade_profit_factor"]),
            float(frozen_table.loc[candidate_id, "trade_profit_factor"]),
            atol=1e-12,
            rtol=0,
        ):
            raise RuntimeError(
                f"EXP-013 {candidate_id} no longer matches EXP-012."
            )
    selection = select_exp013_measurement_leader(candidate_table)
    selected = selected_exp013_row(selection)
    if selection.selected_candidate_id is None or selected is None:
        raise RuntimeError("EXP-013 unexpectedly found no eligible finalist.")
    selected_id = selection.selected_candidate_id
    print(f"Measurement leader: {selected_id}")
    print("Running four anchored walk-forward folds...")
    walk_forward = run_exp013_anchored_walk_forward(nq_arrays)
    print("Running 10,000-resample bootstrap for all three finalists...")
    bootstrap = [
        bootstrap_exp013_trade_metrics(
            nq_results[candidate_id].trades,
            candidate_id=candidate_id,
        )
        for candidate_id in FINALIST_IDS
    ]
    real_maximum = float(
        frozen_exp012["candidates"]["trade_profit_factor"].max()
    )
    real_fixed = {
        candidate_id: float(
            nq_results[candidate_id].summary["trade_profit_factor"]
        )
        for candidate_id in FINALIST_IDS
    }
    print("Running locked 24-candidate discovery-wide MCPT...")
    mcpt, primary_p, fixed_p, mcpt_info = run_exp013_discovery_mcpt(
        nq_frame,
        real_maximum_profit_factor=real_maximum,
        real_fixed_profit_factors=real_fixed,
        requested_workers=workers,
        checkpoint_file=CHECKPOINT_FILE,
        one_minute_fingerprint=EXPECTED_OUTPUTS["NQ_1m"]["sha256"],
    )
    evaluation = evaluate_exp013_evidence(
        nq_summary=nq_results[selected_id].summary,
        mnq_summary=mnq_results[selected_id].summary,
        nq_two_tick_summary=two_tick_results[selected_id].summary,
        walk_forward=walk_forward.folds,
        discovery_wide_mcpt_p_value=primary_p,
    )
    selected_summary = nq_results[selected_id].summary
    plain_summary = (
        f"The measurement leader was {selected_id}, with "
        f"{int(selected_summary['completed_trades'])} NQ trades, Profit "
        f"Factor {float(selected_summary['trade_profit_factor']):.4f}, "
        f"net profit ${float(selected_summary['net_profit_usd']):,.2f}, "
        f"win rate {100 * float(selected_summary['win_rate']):.2f}% and "
        f"maximum drawdown "
        f"${abs(float(selected_summary['maximum_drawdown_usd'])):,.2f}. "
        f"{walk_forward.profitable_test_folds} of 4 anchored test years "
        f"were profitable. The discovery-wide MCPT p-value was "
        f"{primary_p:.6f}; this repeats the entire 24-candidate search."
    )
    decision = {
        "schema_version": 1,
        "experiment_id": "EXP-013",
        "result_status": "MEASURED_HISTORICAL_VALIDATION",
        "calculated_at_utc": datetime.now(timezone.utc).isoformat(),
        "git": git,
        "data": {
            "source_experiment": "EXP-012",
            "included_sessions": int(nq_arrays.session_count),
            "historical_start": str(nq_arrays.session_dates[0]),
            "historical_end": str(nq_arrays.session_dates[-1]),
            "nq_extended_fingerprint": (
                EXPECTED_OUTPUTS["NQ_1m"]["sha256"]
            ),
            "new_data_cleaning_decisions": 0,
        },
        "selection": {
            "candidate_count": 3,
            "eligible_candidates": selection.eligible_count,
            "measurement_leader_id": selected_id,
            "measurement_leader_row": selected.to_dict(),
            "automatic_trading_winner": False,
            "post_exp012_human_shortlist": True,
        },
        "results": {
            "measurement_leader_NQ": nq_results[selected_id].summary,
            "measurement_leader_MNQ": mnq_results[selected_id].summary,
            "all_finalist_NQ": {
                value: nq_results[value].summary for value in FINALIST_IDS
            },
            "all_finalist_MNQ": {
                value: mnq_results[value].summary for value in FINALIST_IDS
            },
        },
        "walk_forward": {
            "fold_count": 4,
            "profitable_test_folds": (
                walk_forward.profitable_test_folds
            ),
            "combined_test_net_profit_usd": (
                walk_forward.combined_test_net_profit_usd
            ),
            "folds": walk_forward.folds.to_dict(orient="records"),
        },
        "bootstrap": bootstrap,
        "mcpt": {
            "permutations": 1000,
            "base_seed": 53,
            "source_candidate_count": 24,
            "real_maximum_trade_profit_factor": real_maximum,
            "permutations_at_least_real": int(
                mcpt["maximum_ge_real"].sum()
            ),
            "discovery_wide_p_value": primary_p,
            "real_fixed_candidate_profit_factors": real_fixed,
            "fixed_candidate_p_values": fixed_p,
            "all_24_candidates_inside_every_permutation": True,
            "does_not_erase_post_result_human_selection": True,
            "run_info": mcpt_info.to_dict(),
        },
        "evaluation": evaluation,
        "plain_english_summary": plain_summary,
        "historical_status": get_exp013_preregistration()[
            "relationship_to_exp012"
        ]["historical_status"],
        "independent_confirmation": False,
        "paper_trading_authorized": False,
        "live_trading_authorized": False,
        "automatic_lifecycle_source_edit": False,
    }

    for staging in (STAGING_RESULT_DIR, STAGING_REPORT_DIR):
        resolved = staging.resolve()
        if PROJECT_DIR.resolve() not in resolved.parents:
            raise RuntimeError("EXP-013 staging path escaped the project.")
        if staging.exists():
            shutil.rmtree(staging)
    STAGING_RESULT_DIR.mkdir(parents=True, exist_ok=False)
    for candidate_id in FINALIST_IDS:
        _write_candidate_outputs(
            STAGING_RESULT_DIR,
            candidate_id,
            nq_result=nq_results[candidate_id],
            mnq_result=mnq_results[candidate_id],
        )
    candidate_table.to_csv(
        STAGING_RESULT_DIR / "candidate_measurements.csv", index=False
    )
    cost_sensitivity.to_csv(
        STAGING_RESULT_DIR / "cost_sensitivity.csv", index=False
    )
    walk_forward.folds.to_csv(
        STAGING_RESULT_DIR / "anchored_walk_forward.csv", index=False
    )
    mcpt.to_csv(STAGING_RESULT_DIR / "mcpt_results.csv", index=False)
    _atomic_json(
        {"diagnostics": bootstrap},
        STAGING_RESULT_DIR / "bootstrap_diagnostics.json",
    )
    _atomic_json(decision, STAGING_RESULT_DIR / "validation_result.json")
    report = build_exp013_report(
        decision=_json_safe(decision),
        candidate_table=candidate_table,
        nq_results=nq_results,
        nq_arrays=nq_arrays,
        walk_forward=walk_forward.folds,
        cost_sensitivity=cost_sensitivity,
        mcpt=mcpt,
        bootstrap=bootstrap,
        output_dir=STAGING_REPORT_DIR,
    )

    if CHECKPOINT_FILE.exists():
        CHECKPOINT_FILE.replace(
            STAGING_RESULT_DIR / "mcpt_checkpoint.json"
        )
    if RESULT_DIR.exists():
        if any(path.is_file() for path in RESULT_DIR.rglob("*")):
            raise RuntimeError("EXP-013 final result path is not empty.")
        RESULT_DIR.rmdir()
    if REPORT_DIR.exists():
        raise RuntimeError("EXP-013 report already exists.")
    STAGING_RESULT_DIR.replace(RESULT_DIR)
    STAGING_REPORT_DIR.replace(REPORT_DIR)
    report = REPORT_DIR / report.name

    print()
    print("EXP-013 validation completed.")
    print(f"Evidence context: {evaluation['classification']}")
    print(f"Measurement leader: {selected_id}")
    print(
        "Selected NQ Profit Factor: "
        f"{float(selected_summary['trade_profit_factor']):.6f}"
    )
    print(
        "Walk-forward profitable folds: "
        f"{walk_forward.profitable_test_folds}/4"
    )
    print(f"Discovery-wide MCPT p-value: {primary_p:.6f}")
    print(f"Result: {RESULT_FILE}")
    print(f"Report: {report}")
    print("No paper or live trading is authorized.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Protected EXP-013 extended-context validation."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--preflight",
        action="store_true",
        help="Verify the committed implementation without results.",
    )
    mode.add_argument(
        "--run",
        action="store_true",
        help="Run the one-time protected historical validation.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=0,
        help="0 selects up to eight logical-worker processes.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.preflight:
        protected_preflight()
        print()
        print(
            "Preflight passed. No EXP-013 finalist, walk-forward, "
            "bootstrap, MCPT, classification or report result was "
            "calculated."
        )
        return
    run_validation(workers=int(args.workers))


if __name__ == "__main__":
    main()
