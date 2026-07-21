from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import shutil
import subprocess
from typing import Any, Mapping

import numpy as np
import pandas as pd

from exp012_engine import (
    get_exp012_candidate,
    prepare_exp012_arrays,
    run_exp012_candidate,
)
from exp013_validation_result import (
    load_candidate_measurements,
    verify_local_exp013_validation_result,
)
from exp014_implementation import validate_exp014_implementation
from exp014_measurements import (
    behaviour_breakdowns,
    concentration_measurements,
    drawdown_diagnostics,
    enrich_trade_ledger,
    monthly_measurements,
    overlap_measurements,
    period_comparison,
    rolling_trade_measurements,
    session_pnl_table,
    session_regime_table,
    sleeve_pair_measurements,
)
from exp014_preregistration import (
    FINALIST_IDS,
    validate_exp014_preregistration,
)
from exp014_report import DISPLAY_NAMES, build_exp014_report
from experiment_lifecycle import get_experiment_lifecycle
from extended_session_data import OUTPUT_FILES
from extended_session_data_result import (
    EXPECTED_OUTPUTS,
    verify_extended_session_data_result,
)


PROJECT_DIR = Path(__file__).resolve().parent
RESULT_DIR = (
    PROJECT_DIR / "results" / "EXP-014" / "finalist_behaviour"
)
REPORT_DIR = PROJECT_DIR / "reports" / "EXP-014-research-lab"
STAGING_RESULT_DIR = (
    PROJECT_DIR / "results" / "EXP-014" / ".finalist_behaviour_staging"
)
STAGING_REPORT_DIR = (
    PROJECT_DIR / "reports" / ".EXP-014-research-lab-staging"
)
RESULT_FILE = RESULT_DIR / "study_result.json"


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
        "working_tree_clean": not bool(_run_git("status", "--porcelain")),
    }


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, np.ndarray):
        return [_json_safe(item) for item in value.tolist()]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return number if math.isfinite(number) else None
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    if isinstance(value, pd.Period):
        return str(value)
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
        "EXP-013": "REVIEW",
        "EXP-014": "PRE_REGISTERED",
    }
    for experiment_id, stage in expected.items():
        actual = get_experiment_lifecycle(experiment_id).stage
        if actual != stage:
            raise RuntimeError(
                f"{experiment_id} must remain {stage}; found {actual}."
            )


def protected_preflight() -> tuple[dict[str, Any], dict[str, Any]]:
    validate_exp014_preregistration()
    validate_exp014_implementation()
    _verify_lifecycle()
    frozen_exp013 = verify_local_exp013_validation_result()
    verify_extended_session_data_result()
    git = git_provenance()
    if not git["working_tree_clean"]:
        raise RuntimeError(
            "Commit the EXP-014 implementation before preflight or results."
        )
    if RESULT_FILE.exists():
        raise RuntimeError(
            "EXP-014 already has a frozen result. Do not rerun it."
        )
    if RESULT_DIR.exists() and any(
        path.is_file() for path in RESULT_DIR.rglob("*")
    ):
        raise RuntimeError("Unexpected partial EXP-014 result output exists.")
    if REPORT_DIR.exists() and any(
        path.is_file() for path in REPORT_DIR.rglob("*")
    ):
        raise RuntimeError(
            "An EXP-014 report already exists without a frozen result."
        )

    print()
    print("EXP-014 IMPLEMENTATION PREFLIGHT")
    print("================================")
    print("Lifecycle:          PRE_REGISTERED")
    print("Implementation:     IMPLEMENTED_NOT_RUN")
    print("Finalists:          3 unchanged EXP-013 strategies")
    print("Research pairs:     2 fixed one-contract-per-sleeve pairs")
    print("Sessions:           1,331 aligned 2020-2025 sessions")
    print("Historical focus:   2025 versus 2020-2024 and 2022-2024")
    print("Regime inputs:      prior 20 completed sessions only")
    print("Rolling windows:    20 and 50 trades")
    print("Parameter search:   False")
    print("Weight search:      False")
    print("Regime filters:     False")
    print("EXP-013 MCPT rerun: False")
    print("Bootstrap rerun:    False")
    print("Walk-forward rerun: False")
    print(f"Git commit:         {git['short_commit']}")
    print("Git clean:          True")
    print("EXP-013 hash-verified: True")
    print("Results:            not calculated")
    print("================================")
    return git, frozen_exp013


def _load_nq_arrays() -> Any:
    nq = pd.read_parquet(OUTPUT_FILES["NQ_1m"])
    arrays = prepare_exp012_arrays(
        nq, require_production_session_count=True
    )
    if arrays.session_count != 1331:
        raise RuntimeError(
            f"EXP-014 expected 1,331 sessions; found {arrays.session_count}."
        )
    return arrays


def _run_locked_candidates(arrays: Any) -> dict[str, Any]:
    return {
        candidate_id: run_exp012_candidate(
            arrays,
            get_exp012_candidate(candidate_id),
            symbol="NQ",
            slippage_ticks_per_side=1,
        )
        for candidate_id in FINALIST_IDS
    }


def _assert_close(
    actual: Any,
    expected: Any,
    *,
    candidate_id: str,
    field: str,
) -> None:
    if not np.isclose(
        float(actual),
        float(expected),
        atol=1e-12,
        rtol=0.0,
    ):
        raise RuntimeError(
            f"EXP-014 reconstruction mismatch for {candidate_id} "
            f"{field}: expected {expected}, got {actual}."
        )


def _verify_reconstruction(
    results: Mapping[str, Any],
    frozen_exp013: Mapping[str, Any],
) -> pd.DataFrame:
    frozen_summaries = frozen_exp013["results"]["all_finalist_NQ"]
    frozen_table = load_candidate_measurements()
    if set(frozen_summaries) != set(FINALIST_IDS):
        raise RuntimeError("EXP-013 frozen finalist set changed.")
    if set(frozen_table["candidate_id"]) != set(FINALIST_IDS):
        raise RuntimeError("EXP-013 frozen candidate table changed.")

    integer_fields = (
        "completed_trades",
        "long_trades",
        "short_trades",
    )
    numeric_fields = (
        "trade_profit_factor",
        "win_rate",
        "average_trade_usd",
        "net_profit_usd",
        "maximum_drawdown_usd",
        "net_profit_to_drawdown",
    )
    for candidate_id in FINALIST_IDS:
        actual = results[candidate_id].summary
        expected = frozen_summaries[candidate_id]
        for field in integer_fields:
            if int(actual[field]) != int(expected[field]):
                raise RuntimeError(
                    f"EXP-014 reconstruction mismatch for {candidate_id} "
                    f"{field}: expected {expected[field]}, "
                    f"got {actual[field]}."
                )
        for field in numeric_fields:
            _assert_close(
                actual[field],
                expected[field],
                candidate_id=candidate_id,
                field=field,
            )

    order = {candidate_id: index for index, candidate_id in enumerate(FINALIST_IDS)}
    standalone = frozen_table.copy()
    standalone = standalone.loc[
        standalone["candidate_id"].isin(FINALIST_IDS)
    ].copy()
    standalone["_order"] = standalone["candidate_id"].map(order)
    standalone = standalone.sort_values("_order").drop(columns="_order")
    standalone["reconstruction_match"] = True
    standalone["strategy_rules_changed"] = False
    return standalone.reset_index(drop=True)


def _plain_english_summary(
    standalone: pd.DataFrame,
    periods: pd.DataFrame,
    pairs: pd.DataFrame,
) -> str:
    indexed = standalone.set_index("candidate_id")
    sentences: list[str] = []
    for candidate_id in FINALIST_IDS:
        row = indexed.loc[candidate_id]
        sentences.append(
            f"{DISPLAY_NAMES[candidate_id]} produced "
            f"{int(row['completed_trades'])} trades, Profit Factor "
            f"{float(row['trade_profit_factor']):.3f}, net profit "
            f"${float(row['net_profit_usd']):,.0f}, win rate "
            f"{100 * float(row['win_rate']):.1f}% and maximum drawdown "
            f"${abs(float(row['maximum_drawdown_usd'])):,.0f}"
        )
    recent = periods.loc[periods["period"].eq("2025")].set_index(
        "candidate_id"
    )
    recent_text = "; ".join(
        f"{DISPLAY_NAMES[candidate_id]} "
        f"${float(recent.loc[candidate_id, 'net_profit_usd']):,.0f}"
        for candidate_id in FINALIST_IDS
    )
    pair_text = "; ".join(
        f"{DISPLAY_NAMES[str(row.pair_id)]} maximum drawdown "
        f"${abs(float(row.maximum_drawdown_usd)):,.0f}"
        for row in pairs.itertuples()
    )
    return (
        ". ".join(sentences)
        + f". In 2025 the individual net results were: {recent_text}. "
        + f"The fixed arithmetic pair drawdowns were: {pair_text}. "
        + "These figures describe trade-offs and complementarity; "
        + "they do not select a winner or authorize trading."
    )


def _exp013_context(frozen_exp013: Mapping[str, Any]) -> dict[str, Any]:
    bootstrap = frozen_exp013["bootstrap"]
    return {
        "classification": frozen_exp013["evaluation"]["classification"],
        "walk_forward_profitable_folds": frozen_exp013["walk_forward"][
            "profitable_test_folds"
        ],
        "walk_forward_total_folds": frozen_exp013["walk_forward"][
            "fold_count"
        ],
        "walk_forward_net_profit_usd": frozen_exp013["walk_forward"][
            "combined_test_net_profit_usd"
        ],
        "discovery_wide_mcpt_p_value": frozen_exp013["mcpt"][
            "discovery_wide_p_value"
        ],
        "mcpt_candidate_count": frozen_exp013["mcpt"][
            "source_candidate_count"
        ],
        "bootstrap_resamples_per_finalist": int(bootstrap[0]["resamples"]),
        "bootstrap_candidate_count": len(bootstrap),
        "reused_not_rerun": True,
    }


def _prepare_staging() -> None:
    for staging in (STAGING_RESULT_DIR, STAGING_REPORT_DIR):
        resolved = staging.resolve()
        if PROJECT_DIR.resolve() not in resolved.parents:
            raise RuntimeError("EXP-014 staging path escaped the project.")
        if staging.exists():
            shutil.rmtree(staging)
    STAGING_RESULT_DIR.mkdir(parents=True, exist_ok=False)


def _write_outputs(
    *,
    decision: dict[str, Any],
    standalone: pd.DataFrame,
    ledgers: Mapping[str, pd.DataFrame],
    behaviour: pd.DataFrame,
    periods: pd.DataFrame,
    monthly: pd.DataFrame,
    rolling: pd.DataFrame,
    drawdowns: pd.DataFrame,
    concentration: pd.DataFrame,
    overlap: pd.DataFrame,
    pair_measurements: pd.DataFrame,
    session_pnl: pd.DataFrame,
    pair_session_pnl: pd.DataFrame,
    regimes: pd.DataFrame,
    arrays: Any,
) -> Path:
    _prepare_staging()
    for candidate_id in FINALIST_IDS:
        directory = STAGING_RESULT_DIR / "candidates" / candidate_id
        directory.mkdir(parents=True, exist_ok=True)
        ledgers[candidate_id].to_csv(
            directory / "nq_enriched_trades.csv", index=False
        )

    outputs = {
        "standalone_measurements.csv": standalone,
        "behaviour_breakdowns.csv": behaviour,
        "period_comparison.csv": periods,
        "monthly_measurements.csv": monthly,
        "rolling_measurements.csv": rolling,
        "drawdown_diagnostics.csv": drawdowns,
        "concentration_measurements.csv": concentration,
        "overlap_measurements.csv": overlap,
        "sleeve_pair_measurements.csv": pair_measurements,
        "session_pnl.csv": session_pnl,
        "pair_session_pnl.csv": pair_session_pnl,
        "regime_context.csv": regimes,
    }
    for filename, frame in outputs.items():
        frame.to_csv(STAGING_RESULT_DIR / filename, index=False)
    _atomic_json(decision, STAGING_RESULT_DIR / "study_result.json")

    report = build_exp014_report(
        decision=_json_safe(decision),
        candidate_table=standalone,
        arrays=arrays,
        ledgers=ledgers,
        behaviour=behaviour,
        periods=periods,
        monthly=monthly,
        rolling=rolling,
        drawdown_diagnostics=drawdowns,
        concentration=concentration,
        overlap=overlap,
        pair_measurements=pair_measurements,
        session_pnl=session_pnl,
        pair_session_pnl=pair_session_pnl,
        output_dir=STAGING_REPORT_DIR,
    )

    if RESULT_DIR.exists():
        if any(path.is_file() for path in RESULT_DIR.rglob("*")):
            raise RuntimeError("EXP-014 final result path is not empty.")
        shutil.rmtree(RESULT_DIR)
    if REPORT_DIR.exists():
        if any(path.is_file() for path in REPORT_DIR.rglob("*")):
            raise RuntimeError("EXP-014 report already exists.")
        shutil.rmtree(REPORT_DIR)
    STAGING_RESULT_DIR.replace(RESULT_DIR)
    STAGING_REPORT_DIR.replace(REPORT_DIR)
    return REPORT_DIR / report.name


def run_study() -> None:
    git, frozen_exp013 = protected_preflight()
    arrays = _load_nq_arrays()
    print()
    print("========== EXP-014 FINALIST BEHAVIOUR STUDY ==========")
    print("Reconstructing three unchanged EXP-013 finalists...")
    results = _run_locked_candidates(arrays)
    standalone = _verify_reconstruction(results, frozen_exp013)
    print("Exact EXP-013 headline reconstruction: passed")

    regimes, volatility_boundary = session_regime_table(arrays)
    ledgers = {
        candidate_id: enrich_trade_ledger(
            arrays, results[candidate_id], regimes
        )
        for candidate_id in FINALIST_IDS
    }
    behaviour = behaviour_breakdowns(ledgers)
    periods = period_comparison(ledgers)
    session_pnl = session_pnl_table(arrays, ledgers)
    monthly = monthly_measurements(session_pnl, ledgers)
    rolling = rolling_trade_measurements(ledgers)
    concentration = concentration_measurements(ledgers)
    overlap = overlap_measurements(session_pnl, ledgers)
    pair_measurements, pair_session_pnl = sleeve_pair_measurements(
        session_pnl, ledgers
    )
    drawdowns = drawdown_diagnostics(session_pnl, pair_session_pnl)

    summary = _plain_english_summary(
        standalone, periods, pair_measurements
    )
    decision = {
        "schema_version": 1,
        "experiment_id": "EXP-014",
        "result_status": "MEASURED_BEHAVIOUR_REVIEW",
        "calculated_at_utc": datetime.now(timezone.utc).isoformat(),
        "git": git,
        "data": {
            "source_experiment": "EXP-012",
            "included_sessions": int(arrays.session_count),
            "historical_start": str(arrays.session_dates[0]),
            "historical_end": str(arrays.session_dates[-1]),
            "nq_extended_fingerprint": EXPECTED_OUTPUTS["NQ_1m"]["sha256"],
            "new_data_cleaning_decisions": 0,
        },
        "reconstruction": {
            "source_experiment": "EXP-013",
            "candidate_count": 3,
            "candidate_ids": list(FINALIST_IDS),
            "headline_fields_verified": [
                "completed_trades",
                "long_trades",
                "short_trades",
                "trade_profit_factor",
                "win_rate",
                "average_trade_usd",
                "net_profit_usd",
                "maximum_drawdown_usd",
                "net_profit_to_drawdown",
            ],
            "all_candidates_match": True,
            "strategy_rules_changed": False,
            "parameters_changed": False,
            "costs_changed": False,
            "position_sizing_changed": False,
        },
        "regime_context": {
            "volatility_boundary": volatility_boundary,
            "calibration_start": "2020-01-03",
            "calibration_end": "2021-12-31",
            "current_session_excluded": True,
            "diagnostic_not_filter": True,
        },
        "exp013_context": _exp013_context(frozen_exp013),
        "standalone_results": standalone.to_dict(orient="records"),
        "period_2025": periods.loc[
            periods["period"].eq("2025")
        ].to_dict(orient="records"),
        "overlap_results": overlap.to_dict(orient="records"),
        "sleeve_pair_results": pair_measurements.to_dict(orient="records"),
        "drawdown_diagnostics": drawdowns.to_dict(orient="records"),
        "plain_english_summary": summary,
        "interpretation": {
            "measurement_first": True,
            "no_pass_fail_gates": True,
            "no_composite_score": True,
            "no_automatic_winner": True,
            "no_strategy_parameter_selection": True,
            "no_regime_filter_selection": True,
            "arithmetic_pairs_not_executable_portfolios": True,
            "expected_lifecycle_after_measurement": "REVIEW",
            "independent_confirmation": False,
            "paper_trading_authorized": False,
            "live_trading_authorized": False,
        },
        "automatic_lifecycle_source_edit": False,
    }

    report = _write_outputs(
        decision=decision,
        standalone=standalone,
        ledgers=ledgers,
        behaviour=behaviour,
        periods=periods,
        monthly=monthly,
        rolling=rolling,
        drawdowns=drawdowns,
        concentration=concentration,
        overlap=overlap,
        pair_measurements=pair_measurements,
        session_pnl=session_pnl,
        pair_session_pnl=pair_session_pnl,
        regimes=regimes,
        arrays=arrays,
    )

    print()
    print("EXP-014 study completed.")
    print("Three exact finalist reconstructions: passed")
    print("Parameter or weight optimization: False")
    print(f"Result: {RESULT_FILE}")
    print(f"Report: {report}")
    print("No paper or live trading is authorized.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Protected EXP-014 finalist behaviour study."
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
        help="Run the one-time protected historical study.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.preflight:
        protected_preflight()
        print()
        print(
            "Preflight passed. No EXP-014 finalist, behaviour, overlap, "
            "regime, sleeve-pair, classification or report result was "
            "calculated."
        )
        return
    run_study()


if __name__ == "__main__":
    main()
