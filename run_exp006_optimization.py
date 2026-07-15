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

from exp006_candidate_scoring import (
    BASELINE,
    evaluate_candidate_grid,
    select_candidate,
)
from exp006_data import load_exp006_frozen_data
from exp006_evaluation import evaluate_exp006
from exp006_implementation import (
    validate_exp006_implementation,
)
from exp006_orb import (
    OrbParameters,
    prepare_orb_arrays,
    run_parameterized_orb,
)
from exp006_preregistration import (
    validate_exp006_preregistration,
)
from exp006_report import build_exp006_report
from exp006_selection_mcpt import (
    FORMAL_BASE_SEED,
    FORMAL_MINIMUM_TRADES,
    FORMAL_PERMUTATIONS,
    best_nq_selection_statistic,
    run_selection_aware_mcpt,
)
from exp006_walk_forward import (
    run_anchored_walk_forward,
)
from experiment_lifecycle import (
    get_experiment_lifecycle,
)

PROJECT_DIR = Path(__file__).resolve().parent
RESULT_ROOT = (
    PROJECT_DIR
    / "results"
    / "EXP-006"
    / "optimization"
)
REPORT_ROOT = (
    PROJECT_DIR
    / "reports"
    / "EXP-006-research-lab"
)
DECISION_FILE = RESULT_ROOT / "optimization_decision.json"
MCPT_CHECKPOINT = RESULT_ROOT / "mcpt_checkpoint_1000.json"


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the protected EXP-006 structured "
            "27-candidate ORB optimization."
        )
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=0,
        help=(
            "Selection-aware MCPT worker count. "
            "Use 0 for automatic selection."
        ),
    )
    parser.add_argument(
        "--preflight",
        action="store_true",
        help=(
            "Verify the frozen workflow and data "
            "without calculating EXP-006 results."
        ),
    )
    return parser.parse_args()


def git_state() -> dict[str, Any]:
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=PROJECT_DIR,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    short_commit = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=PROJECT_DIR,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=PROJECT_DIR,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return {
        "commit": commit,
        "short_commit": short_commit,
        "working_tree_clean": not bool(status),
    }


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): _json_safe(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        value = float(value)
    if isinstance(value, float):
        if math.isnan(value):
            return None
        if math.isinf(value):
            return (
                "Infinity"
                if value > 0
                else "-Infinity"
            )
        return value
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


def _atomic_json(
    payload: dict[str, Any],
    path: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(
            _json_safe(payload),
            indent=2,
            allow_nan=False,
        ),
        encoding="utf-8",
    )
    temporary.replace(path)


def _atomic_csv(
    frame: pd.DataFrame,
    path: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    frame.to_csv(temporary, index=False)
    temporary.replace(path)


def preflight() -> tuple[
    dict[str, Any],
    Any,
]:
    validate_exp006_preregistration()
    validate_exp006_implementation()
    lifecycle = get_experiment_lifecycle("EXP-006")
    if lifecycle.stage != "PRE_REGISTERED":
        raise RuntimeError(
            "EXP-006 optimization may run only while "
            "the lifecycle stage is PRE_REGISTERED."
        )
    exp005 = get_experiment_lifecycle("EXP-005")
    if exp005.stage != "ACCEPTED_FOR_PAPER_TESTING":
        raise RuntimeError(
            "EXP-005 must remain the accepted frozen control."
        )
    if DECISION_FILE.exists():
        raise RuntimeError(
            "The EXP-006 optimization decision already exists. "
            "Do not rerun or overwrite it: "
            f"{DECISION_FILE}"
        )
    git = git_state()
    if not git["working_tree_clean"]:
        raise RuntimeError(
            "Commit and push the EXP-006 implementation "
            "before running results. Git must be clean."
        )
    frozen = load_exp006_frozen_data()
    return git, frozen


def _selected_row(
    grid: pd.DataFrame,
) -> pd.Series | None:
    selected = grid.loc[grid["selected"]]
    if selected.empty:
        return None
    if len(selected) != 1:
        raise RuntimeError(
            "EXP-006 selected more than one candidate."
        )
    return selected.iloc[0]


def _parameters_from_row(
    row: pd.Series,
) -> OrbParameters:
    return OrbParameters(
        opening_range_minutes=int(
            row["opening_range_minutes"]
        ),
        final_entry_time_new_york=str(
            row["final_entry_time_new_york"]
        ),
        direction_mode=str(row["direction_mode"]),
    )


def _cost_sensitivity(
    *,
    data: pd.DataFrame,
    parameters: OrbParameters,
    symbol: str,
) -> pd.DataFrame:
    rows = []
    for ticks in (0.0, 1.0, 2.0):
        result = run_parameterized_orb(
            data,
            parameters=parameters,
            symbol=symbol,
            slippage_ticks_per_side=ticks,
        )
        rows.append(
            {
                "symbol": symbol,
                "slippage_ticks_per_side": ticks,
                "round_trip_cost_usd": (
                    result.contract.round_trip_cost_usd
                ),
                "completed_trades": result.summary[
                    "completed_trades"
                ],
                "net_profit_usd": result.summary[
                    "net_profit_usd"
                ],
                "trade_profit_factor": result.summary[
                    "trade_profit_factor"
                ],
                "maximum_drawdown_usd": result.summary[
                    "maximum_drawdown_usd"
                ],
                "maximum_drawdown_percent": result.summary[
                    "maximum_drawdown_percent"
                ],
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    arguments = parse_arguments()
    git, frozen = preflight()

    print()
    print("========== EXP-006 STRUCTURED ORB OPTIMIZATION ==========")
    print("Grid:         27 locked combinations")
    print("Data:         frozen EXP-005 2019-2025 sessions")
    print("Walk-forward: 5 anchored annual folds")
    print("NQ MCPT:      1,000 selection-aware permutations")
    print(f"Sessions:     {frozen.audit['included_sessions']:,}")
    print(f"Git commit:   {git['short_commit']}")
    print("EXP-005:      frozen control, unchanged")
    print()

    if arguments.preflight:
        print(
            "Preflight passed. No EXP-006 strategy, grid, "
            "walk-forward or MCPT result was calculated."
        )
        return

    nq_arrays = prepare_orb_arrays(frozen.nq_5m)
    mnq_arrays = prepare_orb_arrays(frozen.mnq_5m)

    print("Evaluating all 27 locked NQ/MNQ candidates...")
    raw_grid = evaluate_candidate_grid(
        nq_arrays,
        mnq_arrays,
    )
    selection = select_candidate(raw_grid)
    grid = selection.scored_grid
    selected_parameters = selection.selected_parameters
    selected_row = _selected_row(grid)
    baseline_row = grid.loc[
        grid["parameter_key"].eq(BASELINE.key())
    ].iloc[0]

    print("Running five anchored walk-forward folds...")
    walk_forward = run_anchored_walk_forward(
        nq_arrays,
        mnq_arrays,
    )

    print("Calculating the real selection-aware statistic...")
    (
        real_statistic,
        real_statistic_parameter,
        real_statistic_table,
    ) = best_nq_selection_statistic(
        frozen.nq_5m,
        minimum_trades=FORMAL_MINIMUM_TRADES,
    )

    mcpt, p_value, mcpt_info = (
        run_selection_aware_mcpt(
            frozen.nq_1m,
            real_selection_statistic=(
                real_statistic
            ),
            permutations=FORMAL_PERMUTATIONS,
            base_seed=FORMAL_BASE_SEED,
            requested_workers=arguments.workers,
            checkpoint_file=MCPT_CHECKPOINT,
            one_minute_fingerprint=(
                frozen.audit["fingerprints"][
                    "NQ_1m"
                ]
            ),
            minimum_trades=FORMAL_MINIMUM_TRADES,
        )
    )

    evaluation = evaluate_exp006(
        selected_parameters=selected_parameters,
        selected_row=selected_row,
        baseline_row=baseline_row,
        walk_forward=walk_forward,
        selection_mcpt_p_value=p_value,
    )

    selected_nq = None
    selected_mnq = None
    cost_sensitivity = pd.DataFrame()
    if selected_parameters is not None:
        selected_nq = run_parameterized_orb(
            frozen.nq_5m,
            parameters=selected_parameters,
            symbol="NQ",
        )
        selected_mnq = run_parameterized_orb(
            frozen.mnq_5m,
            parameters=selected_parameters,
            symbol="MNQ",
        )
        cost_sensitivity = pd.concat(
            [
                _cost_sensitivity(
                    data=frozen.nq_5m,
                    parameters=selected_parameters,
                    symbol="NQ",
                ),
                _cost_sensitivity(
                    data=frozen.mnq_5m,
                    parameters=selected_parameters,
                    symbol="MNQ",
                ),
            ],
            ignore_index=True,
        )

    decision = {
        "schema_version": 1,
        "experiment_id": "EXP-006",
        "stage": "STRUCTURED_OPTIMIZATION",
        "calculated_at_utc": datetime.now(
            timezone.utc
        ).isoformat(timespec="seconds"),
        "git": git,
        "data": frozen.audit,
        "grid": {
            "parameter_combinations": 27,
            "eligible_candidates": (
                selection.eligible_count
            ),
            "stable_eligible_candidates": (
                selection.stable_eligible_count
            ),
            "baseline_parameter_key": BASELINE.key(),
            "selected_parameters": (
                selected_parameters.to_dict()
                if selected_parameters is not None
                else None
            ),
        },
        "walk_forward": walk_forward.to_dict(),
        "mcpt": {
            "market": "NQ",
            "permutations": FORMAL_PERMUTATIONS,
            "base_seed": FORMAL_BASE_SEED,
            "real_selection_statistic": (
                real_statistic
            ),
            "real_statistic_best_parameter_key": (
                real_statistic_parameter
            ),
            "p_value": p_value,
            "permutations_at_least_real": int(
                mcpt["permutation_ge_real"].sum()
            ),
            "run_info": mcpt_info.to_dict(),
        },
        "selected_results": {
            "NQ": (
                selected_nq.summary
                if selected_nq is not None
                else None
            ),
            "MNQ": (
                selected_mnq.summary
                if selected_mnq is not None
                else None
            ),
        },
        "evaluation": evaluation.to_dict(),
        "interpretation": (
            "Historical result is exploratory because "
            "2019-2025 was already viewed. A pass may "
            "lock one candidate for new forward paper "
            "comparison only."
        ),
        "exp005_control_changed": False,
        "live_trading_authorized": False,
        "automatic_lifecycle_source_edit": False,
    }

    RESULT_ROOT.mkdir(parents=True, exist_ok=True)
    _atomic_csv(grid, RESULT_ROOT / "candidate_grid.csv")
    _atomic_csv(
        walk_forward.folds,
        RESULT_ROOT / "walk_forward_folds.csv",
    )
    _atomic_csv(mcpt, RESULT_ROOT / "selection_mcpt.csv")
    _atomic_csv(
        real_statistic_table,
        RESULT_ROOT / "real_mcpt_candidate_statistics.csv",
    )
    _atomic_csv(
        cost_sensitivity,
        RESULT_ROOT / "selected_cost_sensitivity.csv",
    )

    nq_equity = None
    mnq_equity = None
    if selected_nq is not None and selected_mnq is not None:
        _atomic_csv(
            selected_nq.trades,
            RESULT_ROOT / "selected_nq_trades.csv",
        )
        _atomic_csv(
            selected_mnq.trades,
            RESULT_ROOT / "selected_mnq_trades.csv",
        )
        _atomic_csv(
            selected_nq.equity_curve,
            RESULT_ROOT / "selected_nq_equity.csv",
        )
        _atomic_csv(
            selected_mnq.equity_curve,
            RESULT_ROOT / "selected_mnq_equity.csv",
        )
        _atomic_csv(
            selected_nq.yearly_results,
            RESULT_ROOT / "selected_nq_yearly.csv",
        )
        _atomic_csv(
            selected_mnq.yearly_results,
            RESULT_ROOT / "selected_mnq_yearly.csv",
        )
        nq_equity = selected_nq.equity_curve
        mnq_equity = selected_mnq.equity_curve

    report = build_exp006_report(
        report_root=REPORT_ROOT,
        decision=decision,
        grid=grid,
        walk_forward=walk_forward.folds,
        mcpt=mcpt,
        selected_nq_equity=nq_equity,
        selected_mnq_equity=mnq_equity,
    )

    # The immutable decision marker is written last.
    _atomic_json(decision, DECISION_FILE)

    print()
    print("EXP-006 optimization completed.")
    print(f"Decision: {evaluation.decision}")
    if selected_parameters is not None:
        print(
            "Selected: "
            f"OR {selected_parameters.opening_range_minutes}m, "
            f"entry {selected_parameters.final_entry_time_new_york}, "
            f"{selected_parameters.direction_mode}"
        )
    else:
        print("Selected: None")
    print(f"Selection-aware MCPT p-value: {p_value:.6f}")
    print(
        "Failed gates: "
        + (
            ", ".join(evaluation.failed_gates)
            if evaluation.failed_gates
            else "None"
        )
    )
    print("EXP-005 control changed: False")
    print(f"Decision: {DECISION_FILE.resolve()}")
    print(f"Report:   {report.resolve()}")
    print("========================================================")


if __name__ == "__main__":
    main()
