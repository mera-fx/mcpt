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

from exp005_quantower_import import dataframe_sha256
from exp006_data import load_exp006_frozen_data
from exp006_optimization_result import (
    verify_local_exp006_optimization_decision,
)
from exp007_bootstrap import bootstrap_trade_metrics
from exp007_evaluation import evaluate_exp007
from exp007_implementation import validate_exp007_implementation
from exp007_mcpt import run_exp007_mcpt
from exp007_orb import run_exp007_orb
from exp007_preregistration import (
    get_exp007_preregistration,
    validate_exp007_preregistration,
)
from exp007_report import build_exp007_report
from experiment_lifecycle import get_experiment_lifecycle


PROJECT_DIR = Path(__file__).resolve().parent
RESULT_DIR = PROJECT_DIR / "results" / "EXP-007" / "fixed_replication"
REPORT_DIR = PROJECT_DIR / "reports" / "EXP-007-research-lab"
DECISION_FILE = RESULT_DIR / "replication_decision.json"
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
    exp005 = get_experiment_lifecycle("EXP-005")
    exp006 = get_experiment_lifecycle("EXP-006")
    exp007 = get_experiment_lifecycle("EXP-007")
    if exp005.stage != "ACCEPTED_FOR_PAPER_TESTING":
        raise RuntimeError("EXP-005 accepted control stage changed.")
    if exp006.stage != "REJECTED":
        raise RuntimeError("EXP-006 rejection stage changed.")
    if exp007.stage != "PRE_REGISTERED":
        raise RuntimeError("EXP-007 must remain PRE_REGISTERED before running.")
    frozen_exp006 = verify_local_exp006_optimization_decision()
    if (
        frozen_exp006["evaluation"]["decision"]
        != "REJECT_EXP006_KEEP_EXP005_CONTROL"
    ):
        raise RuntimeError("The frozen EXP-006 decision changed.")


def protected_preflight() -> tuple[dict[str, Any], Any]:
    validate_exp007_preregistration()
    validate_exp007_implementation()
    _verify_lifecycle()

    git = git_provenance()
    if not git["working_tree_clean"]:
        raise RuntimeError(
            "Commit the EXP-007 implementation before preflight or results."
        )
    if DECISION_FILE.exists():
        raise RuntimeError(
            "EXP-007 already has a frozen decision. Do not rerun it."
        )

    frozen = load_exp006_frozen_data()
    if int(frozen.audit["included_sessions"]) != 1639:
        raise RuntimeError("EXP-007 frozen session count changed.")

    print()
    print("EXP-007 IMPLEMENTATION PREFLIGHT")
    print("================================")
    print("Lifecycle:       PRE_REGISTERED")
    print("Implementation:  IMPLEMENTED_NOT_RUN")
    print("Strategy:        fixed 30m long-only ORB")
    print("Target:          1R")
    print("Forced flat:     14:00 New York")
    print("Sessions:        1,639")
    print("Optimization:    disabled")
    print("NQ MCPT:         1,000 fixed-strategy permutations")
    print(f"Git commit:      {git['short_commit']}")
    print("Git clean:       True")
    print("EXP-005 changed: False")
    print("EXP-006 changed: False")
    print("Results:         not calculated")
    print("================================")
    return git, frozen


def _combined_yearly(
    nq_yearly: pd.DataFrame,
    mnq_yearly: pd.DataFrame,
) -> pd.DataFrame:
    nq = nq_yearly.copy()
    nq.insert(0, "symbol", "NQ")
    mnq = mnq_yearly.copy()
    mnq.insert(0, "symbol", "MNQ")
    return pd.concat([nq, mnq], ignore_index=True)


def _cost_sensitivity(frozen: Any) -> tuple[pd.DataFrame, dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    two_tick_nq: dict[str, Any] | None = None
    for ticks in (0.0, 1.0, 2.0):
        for symbol, data in (
            ("NQ", frozen.nq_1m),
            ("MNQ", frozen.mnq_1m),
        ):
            result = run_exp007_orb(
                data,
                symbol=symbol,
                slippage_ticks_per_side=ticks,
            )
            summary = result.summary
            row = {
                "symbol": symbol,
                "slippage_ticks_per_side": float(ticks),
                "round_trip_cost_usd": float(
                    summary["round_trip_cost_usd"]
                ),
                "completed_trades": int(summary["completed_trades"]),
                "trade_profit_factor": float(
                    summary["trade_profit_factor"]
                ),
                "net_profit_usd": float(summary["net_profit_usd"]),
                "average_trade_usd": float(
                    summary["average_trade_usd"]
                ),
                "maximum_drawdown_usd": float(
                    summary["maximum_drawdown_usd"]
                ),
            }
            rows.append(row)
            if symbol == "NQ" and ticks == 2.0:
                two_tick_nq = row
    if two_tick_nq is None:
        raise RuntimeError("EXP-007 two-tick NQ stress result is missing.")
    return pd.DataFrame(rows), two_tick_nq


def run_replication(*, workers: int) -> None:
    git, frozen = protected_preflight()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    print()
    print("========== EXP-007 FIXED ORB REPLICATION ==========")
    print("Rule set:     one fixed 30m long-only 1R strategy")
    print("Data:         frozen EXP-005 2019-2025 sessions")
    print("Optimization: none")
    print("NQ MCPT:      1,000 session-aware permutations")
    print("Sessions:     1,639")
    print(f"Git commit:   {git['short_commit']}")
    print("EXP-005/006:  frozen, unchanged")
    print()

    print("Running fixed NQ result...")
    nq_result = run_exp007_orb(frozen.nq_1m, symbol="NQ")
    print("Running fixed MNQ implementation check...")
    mnq_result = run_exp007_orb(frozen.mnq_1m, symbol="MNQ")
    print("Running locked cost sensitivity...")
    cost_sensitivity, nq_two_tick = _cost_sensitivity(frozen)
    print("Running diagnostic 10,000-resample bootstrap...")
    bootstrap = bootstrap_trade_metrics(nq_result.trades)

    print("Running locked session-aware MCPT...")
    mcpt_frame, mcpt_p_value, mcpt_info = run_exp007_mcpt(
        frozen.nq_1m,
        real_trade_profit_factor=float(
            nq_result.summary["trade_profit_factor"]
        ),
        requested_workers=workers,
        checkpoint_file=CHECKPOINT_FILE,
        one_minute_fingerprint=frozen.audit["fingerprints"]["NQ_1m"],
    )

    evaluation = evaluate_exp007(
        nq_summary=nq_result.summary,
        mnq_summary=mnq_result.summary,
        nq_yearly_results=nq_result.yearly_results,
        nq_two_tick_summary=nq_two_tick,
        mcpt_p_value=mcpt_p_value,
    )
    yearly = _combined_yearly(
        nq_result.yearly_results,
        mnq_result.yearly_results,
    )
    exceedances = int(mcpt_frame["permutation_ge_real"].sum())
    finite_pf = mcpt_frame["trade_profit_factor"].replace(
        [np.inf, -np.inf], np.nan
    ).dropna()

    preregistration = get_exp007_preregistration()
    decision = {
        "schema_version": 1,
        "experiment_id": "EXP-007",
        "stage": "FIXED_HISTORICAL_REPLICATION",
        "calculated_at_utc": datetime.now(timezone.utc).isoformat(
            timespec="seconds"
        ),
        "git": git,
        "data": {
            "source_experiment": "EXP-005",
            "included_sessions": 1639,
            "one_minute_rows_per_symbol": 639210,
            "five_minute_rows_per_symbol": 127842,
            "fingerprints": frozen.audit["fingerprints"],
            "new_data_cleaning_decisions": 0,
        },
        "fixed_rules": preregistration["fixed_strategy_rules"],
        "results": {
            "NQ": nq_result.summary,
            "MNQ": mnq_result.summary,
        },
        "annual_evaluation": {
            "years": [2021, 2022, 2023, 2024, 2025],
            "profitable_nq_blocks": evaluation[
                "profitable_nq_annual_blocks"
            ],
            "combined_2021_2025_nq_net_profit_usd": evaluation[
                "combined_2021_2025_nq_net_profit_usd"
            ],
        },
        "cost_sensitivity": cost_sensitivity.to_dict(orient="records"),
        "bootstrap": bootstrap,
        "mcpt": {
            "market": "NQ",
            "permutations": 1000,
            "base_seed": 47,
            "test_statistic": "trade_profit_factor",
            "real_trade_profit_factor": nq_result.summary[
                "trade_profit_factor"
            ],
            "permutations_at_least_real": exceedances,
            "p_value": mcpt_p_value,
            "permutation_pf_median": (
                float(finite_pf.median()) if len(finite_pf) else None
            ),
            "permutation_pf_maximum": (
                float(finite_pf.max()) if len(finite_pf) else None
            ),
            "run_info": mcpt_info.to_dict(),
            "optimization_inside_permutation": False,
        },
        "evaluation": evaluation,
        "historical_status": (
            "EXPLORATORY_BECAUSE_2019_2025_WAS_ALREADY_VIEWED"
        ),
        "best_possible_pass_action": (
            "FIXED_CANDIDATE_FOR_NEW_FORWARD_PAPER_COMPARISON"
        ),
        "exp005_control_changed": False,
        "exp006_result_changed": False,
        "live_trading_authorized": False,
        "automatic_lifecycle_source_edit": False,
    }

    nq_result.trades.to_csv(RESULT_DIR / "nq_trades.csv", index=False)
    mnq_result.trades.to_csv(RESULT_DIR / "mnq_trades.csv", index=False)
    nq_result.equity_curve.to_csv(
        RESULT_DIR / "nq_equity_curve.csv", index=False
    )
    mnq_result.equity_curve.to_csv(
        RESULT_DIR / "mnq_equity_curve.csv", index=False
    )
    yearly.to_csv(RESULT_DIR / "yearly_results.csv", index=False)
    cost_sensitivity.to_csv(
        RESULT_DIR / "cost_sensitivity.csv", index=False
    )
    mcpt_frame.to_csv(RESULT_DIR / "mcpt_results.csv", index=False)
    _atomic_json(bootstrap, RESULT_DIR / "bootstrap_diagnostics.json")
    _atomic_json(decision, DECISION_FILE)

    report = build_exp007_report(
        decision=_json_safe(decision),
        nq_equity=nq_result.equity_curve,
        mnq_equity=mnq_result.equity_curve,
        yearly=yearly,
        cost_sensitivity=cost_sensitivity,
        mcpt=mcpt_frame,
        output_dir=REPORT_DIR,
    )

    print()
    print("EXP-007 fixed replication completed.")
    print(f"Decision: {evaluation['decision']}")
    print(
        "NQ Profit Factor: "
        f"{float(nq_result.summary['trade_profit_factor']):.6f}"
    )
    print(
        "NQ net profit: "
        f"${float(nq_result.summary['net_profit_usd']):,.2f}"
    )
    print(f"NQ completed trades: {nq_result.summary['completed_trades']}")
    print(f"MCPT p-value: {mcpt_p_value:.6f}")
    print(
        "Failed gates: "
        + (
            ", ".join(evaluation["failed_gates"])
            if evaluation["failed_gates"]
            else "none"
        )
    )
    print(f"Decision file: {DECISION_FILE}")
    print(f"Report: {report}")
    print("No live trading is authorized.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Protected EXP-007 fixed ORB replication."
    )
    parser.add_argument(
        "--preflight",
        action="store_true",
        help="Verify the committed implementation without calculating results.",
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
            "Preflight passed. No EXP-007 strategy, annual, cost, "
            "bootstrap or MCPT result was calculated."
        )
        return
    run_replication(workers=int(args.workers))


if __name__ == "__main__":
    main()
