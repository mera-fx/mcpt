from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import subprocess
from typing import Any

import numpy as np
import pandas as pd

from exp006_data import load_exp006_frozen_data
from exp009_engine import (
    Exp009Result,
    get_exp009_candidate,
    prepare_exp009_arrays,
    run_exp009_candidate,
)
from exp009_measurements import calculate_candidate_measurements
from exp009_tournament_result import verify_local_exp009_tournament_result
from exp010_bootstrap import bootstrap_exp010_trade_metrics
from exp010_evaluation import evaluate_exp010_evidence
from exp010_implementation import validate_exp010_implementation
from exp010_preregistration import (
    get_exp010_preregistration,
    validate_exp010_preregistration,
)
from exp010_report import build_exp010_report
from exp010_selection import (
    locked_opening_drive_candidates,
    select_opening_drive_candidate,
    selected_candidate_row,
)
from exp010_selection_mcpt import run_exp010_selection_mcpt
from exp010_walk_forward import run_exp010_anchored_walk_forward
from experiment_lifecycle import get_experiment_lifecycle


PROJECT_DIR = Path(__file__).resolve().parent
RESULT_DIR = PROJECT_DIR / "results" / "EXP-010" / "opening_drive_validation"
REPORT_DIR = PROJECT_DIR / "reports" / "EXP-010-research-lab"
RESULT_FILE = RESULT_DIR / "validation_result.json"
CHECKPOINT_FILE = RESULT_DIR / "mcpt_checkpoint.json"
USER_REFERENCE_ID = "opening_drive_0p5_1p5r"


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
        "EXP-010": "PRE_REGISTERED",
    }
    for experiment_id, stage in expected.items():
        actual = get_experiment_lifecycle(experiment_id).stage
        if actual != stage:
            raise RuntimeError(
                f"{experiment_id} must remain {stage}; found {actual}."
            )


def protected_preflight() -> tuple[dict[str, Any], Any]:
    validate_exp010_preregistration()
    validate_exp010_implementation()
    _verify_lifecycle()
    verify_local_exp009_tournament_result()
    git = git_provenance()
    if not git["working_tree_clean"]:
        raise RuntimeError(
            "Commit the EXP-010 implementation before preflight or results."
        )
    if RESULT_FILE.exists():
        raise RuntimeError(
            "EXP-010 already has a frozen result. Do not rerun it."
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
            "Unexpected partial EXP-010 output exists: "
            + ", ".join(str(path) for path in unexpected)
        )

    frozen = load_exp006_frozen_data()
    if int(frozen.audit["included_sessions"]) != 1639:
        raise RuntimeError("EXP-010 frozen session count changed.")

    print()
    print("EXP-010 IMPLEMENTATION PREFLIGHT")
    print("================================")
    print("Lifecycle:       PRE_REGISTERED")
    print("Implementation:  IMPLEMENTED_NOT_RUN")
    print("Family:          opening-drive continuation")
    print("Candidates:      4 locked EXP-009 candidates")
    print(f"User reference:  {USER_REFERENCE_ID}")
    print("Sessions:        1,639 frozen EXP-005 sessions")
    print("Walk-forward:    5 anchored annual folds")
    print("NQ MCPT:         1,000 four-candidate permutations")
    print("Selection inside every permutation: True")
    print("Prior six-family selection corrected: False")
    print("Bootstrap:       10,000 resamples")
    print(f"Git commit:      {git['short_commit']}")
    print("Git clean:       True")
    print("EXP-009 hash-verified: True")
    print("Results:         not calculated")
    print("================================")
    return git, frozen


def _run_candidate_bundle(
    nq_arrays: Any,
    mnq_arrays: Any,
) -> tuple[
    pd.DataFrame,
    dict[str, Exp009Result],
    dict[str, Exp009Result],
    dict[str, Exp009Result],
    pd.DataFrame,
]:
    measurements = []
    nq_results: dict[str, Exp009Result] = {}
    mnq_results: dict[str, Exp009Result] = {}
    two_tick_results: dict[str, Exp009Result] = {}
    cost_rows = []
    for candidate in locked_opening_drive_candidates():
        base_nq = run_exp009_candidate(
            nq_arrays,
            candidate,
            symbol="NQ",
            slippage_ticks_per_side=1.0,
        )
        base_mnq = run_exp009_candidate(
            mnq_arrays,
            candidate,
            symbol="MNQ",
            slippage_ticks_per_side=1.0,
        )
        zero_nq = run_exp009_candidate(
            nq_arrays,
            candidate,
            symbol="NQ",
            slippage_ticks_per_side=0.0,
        )
        two_nq = run_exp009_candidate(
            nq_arrays,
            candidate,
            symbol="NQ",
            slippage_ticks_per_side=2.0,
        )
        measurement = calculate_candidate_measurements(
            base_nq,
            base_mnq,
            nq_zero_tick_result=zero_nq,
            nq_two_tick_result=two_nq,
            included_session_count=nq_arrays.session_count,
        )
        measurement["minimum_drive_fraction"] = float(
            candidate.parameters["minimum_drive_fraction"]
        )
        measurement["exit_mode"] = str(candidate.parameters["exit_mode"])
        measurements.append(measurement)
        nq_results[candidate.candidate_id] = base_nq
        mnq_results[candidate.candidate_id] = base_mnq
        two_tick_results[candidate.candidate_id] = two_nq

        for ticks, result in (
            (0.0, zero_nq),
            (1.0, base_nq),
            (2.0, two_nq),
        ):
            cost_rows.append(
                {
                    "candidate_id": candidate.candidate_id,
                    "symbol": "NQ",
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
    table = pd.DataFrame.from_records(measurements)
    selection = select_opening_drive_candidate(table)
    table = selection.scored_candidates
    return (
        table,
        nq_results,
        mnq_results,
        two_tick_results,
        pd.DataFrame.from_records(cost_rows),
    )


def _write_candidate_outputs(
    candidate_id: str,
    *,
    nq_result: Exp009Result,
    mnq_result: Exp009Result,
) -> None:
    directory = RESULT_DIR / "candidates" / candidate_id
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
    git, frozen = protected_preflight()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    nq_arrays = prepare_exp009_arrays(frozen.nq_1m)
    mnq_arrays = prepare_exp009_arrays(frozen.mnq_1m)

    print()
    print("========== EXP-010 OPENING-DRIVE DEEP VALIDATION ==========")
    print("Running all four locked candidates under the common standard.")
    print("No automatic trading winner and no live authorization.")
    print()
    (
        candidate_table,
        nq_results,
        mnq_results,
        two_tick_results,
        cost_sensitivity,
    ) = _run_candidate_bundle(nq_arrays, mnq_arrays)
    selection = select_opening_drive_candidate(candidate_table)
    selected_row = selected_candidate_row(selection)
    if selection.selected_candidate is None or selected_row is None:
        raise RuntimeError(
            "The hash-verified EXP-009 data unexpectedly produced no "
            "eligible EXP-010 candidate."
        )
    selected_id = selection.selected_candidate.candidate_id
    reference_id = USER_REFERENCE_ID
    selected_nq = nq_results[selected_id]
    selected_mnq = mnq_results[selected_id]
    selected_two_tick = two_tick_results[selected_id]
    reference_nq = nq_results[reference_id]

    print(f"Measurement leader: {selected_id}")
    print("Running five anchored walk-forward folds...")
    walk_forward = run_exp010_anchored_walk_forward(nq_arrays)
    print("Running two locked bootstrap diagnostics...")
    bootstrap_ids = list(dict.fromkeys((selected_id, reference_id)))
    bootstrap = [
        bootstrap_exp010_trade_metrics(
            nq_results[candidate_id].trades,
            candidate_id=candidate_id,
        )
        for candidate_id in bootstrap_ids
    ]

    print("Running locked selection-aware and fixed-reference MCPT...")
    (
        mcpt,
        selection_p_value,
        fixed_reference_p_value,
        mcpt_info,
    ) = run_exp010_selection_mcpt(
        frozen.nq_1m,
        real_selected_trade_profit_factor=float(
            selected_nq.summary["trade_profit_factor"]
        ),
        real_fixed_reference_trade_profit_factor=float(
            reference_nq.summary["trade_profit_factor"]
        ),
        requested_workers=workers,
        checkpoint_file=CHECKPOINT_FILE,
        one_minute_fingerprint=frozen.audit["fingerprints"]["NQ_1m"],
    )
    evaluation = evaluate_exp010_evidence(
        nq_summary=selected_nq.summary,
        mnq_summary=selected_mnq.summary,
        nq_two_tick_summary=selected_two_tick.summary,
        walk_forward=walk_forward.folds,
        selection_aware_mcpt_p_value=selection_p_value,
    )
    reference_row = candidate_table.loc[
        candidate_table["candidate_id"].eq(reference_id)
    ].iloc[0]
    preregistration = get_exp010_preregistration()
    decision = {
        "schema_version": 1,
        "experiment_id": "EXP-010",
        "result_status": "MEASURED_DEEP_VALIDATION",
        "calculated_at_utc": datetime.now(timezone.utc).isoformat(),
        "git": git,
        "data": {
            "source_experiment": "EXP-005",
            "included_sessions": int(nq_arrays.session_count),
            "historical_start": "2019-05-06",
            "historical_end": "2025-12-31",
            "fingerprints": frozen.audit["fingerprints"],
            "new_data_cleaning_decisions": 0,
        },
        "selection": {
            "candidate_count": 4,
            "eligible_candidates": selection.eligible_count,
            "selected_candidate_id": selected_id,
            "selected_candidate_row": selected_row.to_dict(),
            "user_reference_candidate_id": reference_id,
            "user_reference_candidate_row": reference_row.to_dict(),
            "user_reference_is_independent_preselection": False,
            "automatic_trading_winner": False,
        },
        "results": {
            "selected_NQ": selected_nq.summary,
            "selected_MNQ": selected_mnq.summary,
            "user_reference_NQ": reference_nq.summary,
        },
        "walk_forward": {
            "fold_count": 5,
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
            "base_seed": 50,
            "real_selected_trade_profit_factor": float(
                selected_nq.summary["trade_profit_factor"]
            ),
            "real_fixed_reference_trade_profit_factor": float(
                reference_nq.summary["trade_profit_factor"]
            ),
            "selected_permutations_at_least_real": int(
                mcpt["selected_ge_real"].sum()
            ),
            "fixed_reference_permutations_at_least_real": int(
                mcpt["fixed_reference_ge_real"].sum()
            ),
            "selection_aware_p_value": selection_p_value,
            "fixed_reference_p_value": fixed_reference_p_value,
            "all_four_candidates_inside_every_permutation": True,
            "selection_inside_every_permutation": True,
            "prior_six_family_selection_corrected": False,
            "run_info": mcpt_info.to_dict(),
        },
        "evaluation": evaluation,
        "historical_status": preregistration[
            "relationship_to_exp009"
        ]["historical_status"],
        "independent_confirmation": False,
        "paper_trading_authorized": False,
        "live_trading_authorized": False,
        "automatic_lifecycle_source_edit": False,
    }

    candidate_table.to_csv(
        RESULT_DIR / "candidate_measurements.csv", index=False
    )
    cost_sensitivity.to_csv(
        RESULT_DIR / "cost_sensitivity.csv", index=False
    )
    walk_forward.folds.to_csv(
        RESULT_DIR / "anchored_walk_forward.csv", index=False
    )
    mcpt.to_csv(RESULT_DIR / "mcpt_results.csv", index=False)
    _atomic_json(
        {"diagnostics": bootstrap},
        RESULT_DIR / "bootstrap_diagnostics.json",
    )
    for candidate_id in nq_results:
        _write_candidate_outputs(
            candidate_id,
            nq_result=nq_results[candidate_id],
            mnq_result=mnq_results[candidate_id],
        )
    report = build_exp010_report(
        decision=_json_safe(decision),
        candidate_table=candidate_table,
        nq_results=nq_results,
        nq_arrays=nq_arrays,
        walk_forward=walk_forward.folds,
        cost_sensitivity=cost_sensitivity,
        mcpt=mcpt,
        bootstrap=bootstrap,
        output_dir=REPORT_DIR,
    )
    _atomic_json(decision, RESULT_FILE)

    print()
    print("EXP-010 deep validation completed.")
    print(f"Evidence context: {evaluation['classification']}")
    print(f"Measurement leader: {selected_id}")
    print(
        "Selected NQ Profit Factor: "
        f"{float(selected_nq.summary['trade_profit_factor']):.6f}"
    )
    print(
        "Selected NQ net profit: "
        f"${float(selected_nq.summary['net_profit_usd']):,.2f}"
    )
    print(
        "Walk-forward profitable folds: "
        f"{walk_forward.profitable_test_folds}/5"
    )
    print(f"Selection-aware MCPT p-value: {selection_p_value:.6f}")
    print(f"Fixed-reference MCPT p-value: {fixed_reference_p_value:.6f}")
    print(f"Result: {RESULT_FILE}")
    print(f"Report: {report}")
    print("No paper or live trading is authorized.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Protected EXP-010 opening-drive deep validation."
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
        help="Run the one-time protected deep validation.",
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
            "Preflight passed. No EXP-010 candidate, walk-forward, "
            "bootstrap or MCPT result was calculated."
        )
        return
    run_validation(workers=int(args.workers))


if __name__ == "__main__":
    main()
