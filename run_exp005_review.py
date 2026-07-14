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

from exp005_full_validation_result import verify_local_full_validation_decision
from exp005_quick_transfer_result import verify_local_quick_transfer_decision
from exp005_review import evaluate_exp005_review
from exp005_review_implementation import validate_exp005_review_implementation
from experiment_lifecycle import get_experiment_lifecycle


PROJECT_DIR = Path(__file__).resolve().parent
FULL_ROOT = PROJECT_DIR / "results" / "EXP-005" / "full_validation"
REVIEW_ROOT = PROJECT_DIR / "results" / "EXP-005" / "review"
DECISION_FILE = REVIEW_ROOT / "review_decision.json"

SOURCE_FILES = {
    "decision_model_summary": FULL_ROOT / "decision_model_summary.csv",
    "nq_trades": FULL_ROOT / "nq_trades.csv",
    "mnq_trades": FULL_ROOT / "mnq_trades.csv",
    "cost_sensitivity": FULL_ROOT / "cost_sensitivity.csv",
    "yearly_results": FULL_ROOT / "yearly_results.csv",
}


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the protected read-only EXP-005 operational review."
    )
    parser.add_argument(
        "--preflight",
        action="store_true",
        help="Verify frozen inputs without calculating a review decision.",
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
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        value = float(value)
    if isinstance(value, float):
        if math.isnan(value):
            return None
        if math.isinf(value):
            return "Infinity" if value > 0 else "-Infinity"
        return value
    return value


def _atomic_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(_json_safe(payload), indent=2, allow_nan=False),
        encoding="utf-8",
    )
    temporary.replace(path)


def _atomic_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    frame.to_csv(temporary, index=False)
    temporary.replace(path)


def load_review_inputs(full_result: dict[str, Any]) -> dict[str, pd.DataFrame]:
    missing = [str(path) for path in SOURCE_FILES.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "Required frozen full-validation outputs are missing: "
            + ", ".join(missing)
        )
    frames = {name: pd.read_csv(path) for name, path in SOURCE_FILES.items()}
    nq = full_result["results"]["NQ"]
    mnq = full_result["results"]["MNQ"]

    for symbol, frame, expected in (
        ("NQ", frames["nq_trades"], nq),
        ("MNQ", frames["mnq_trades"], mnq),
    ):
        if len(frame) != int(expected["completed_trades"]):
            raise RuntimeError(f"{symbol} frozen trade count changed.")
        net = float(frame["net_pnl_usd"].astype(float).sum())
        if not np.isclose(
            net,
            float(expected["net_profit_usd"]),
            atol=1e-9,
            rtol=0.0,
        ):
            raise RuntimeError(f"{symbol} frozen trade P&L changed.")
        long_count = int(
            frame["direction"].astype(str).str.lower().eq("long").sum()
        )
        short_count = int(
            frame["direction"].astype(str).str.lower().eq("short").sum()
        )
        if (
            long_count != int(expected["long_trades"])
            or short_count != int(expected["short_trades"])
        ):
            raise RuntimeError(f"{symbol} frozen direction counts changed.")

    yearly = frames["yearly_results"]
    nq_yearly = yearly.loc[
        yearly["symbol"].astype(str).str.upper().eq("NQ")
    ]
    if (
        sorted(nq_yearly["year"].astype(int).tolist()) != [2023, 2024, 2025]
        or not np.isclose(
            nq_yearly["net_profit_usd"].astype(float).sum(),
            float(nq["net_profit_usd"]),
            atol=1e-9,
            rtol=0.0,
        )
    ):
        raise RuntimeError("Frozen NQ yearly results changed.")
    return frames


def preflight() -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, pd.DataFrame],
]:
    validate_exp005_review_implementation()
    full_result = verify_local_full_validation_decision()
    quick_result = verify_local_quick_transfer_decision()
    lifecycle = get_experiment_lifecycle("EXP-005")
    if lifecycle.stage != "REVIEW":
        raise RuntimeError(
            "EXP-005 review may run only while the lifecycle stage is REVIEW. "
            f"Current stage: {lifecycle.stage}"
        )
    if DECISION_FILE.exists():
        raise RuntimeError(
            "The EXP-005 review decision already exists. Do not rerun it: "
            f"{DECISION_FILE}"
        )
    git = git_state()
    if not git["working_tree_clean"]:
        raise RuntimeError(
            "Commit and push the review implementation before formal review. "
            "Git must be clean."
        )
    frames = load_review_inputs(full_result)
    return git, full_result, quick_result, frames


def main() -> None:
    arguments = parse_arguments()
    git, full_result, quick_result, frames = preflight()

    print()
    print("============= EXP-005 FORMAL REVIEW =============")
    print("Review type: read-only operational quality")
    print("Strategy rerun: DISABLED")
    print("MCPT rerun: DISABLED")
    print(f"Review Git commit: {git['short_commit']}")
    print()

    if arguments.preflight:
        print("Preflight passed. No review decision was calculated.")
        return

    evaluation = evaluate_exp005_review(
        full_result=full_result,
        quick_result=quick_result,
        cost_sensitivity=frames["cost_sensitivity"],
        yearly_results=frames["yearly_results"],
        nq_trades=frames["nq_trades"],
        mnq_trades=frames["mnq_trades"],
    )
    decision = {
        "schema_version": 1,
        "experiment_id": "EXP-005",
        "stage": "REVIEW",
        "calculated_at_utc": datetime.now(timezone.utc).isoformat(
            timespec="seconds"
        ),
        "git": git,
        "review_type": "READ_ONLY_OPERATIONAL_QUALITY_REVIEW",
        "source_full_validation": {
            "decision": full_result["evaluation"]["decision"],
            "implementation_commit": full_result["git"]["commit"],
            "included_sessions": full_result["data"]["included_sessions"],
            "nq_mcpt_permutations": full_result["mcpt"]["permutations"],
            "nq_mcpt_p_value": full_result["mcpt"]["p_value"],
        },
        "evaluation": evaluation.to_dict(),
        "strategy_rerun": False,
        "mcpt_rerun": False,
        "parameter_change": False,
        "cost_change": False,
        "data_change": False,
        "quick_transfer_rerun": False,
        "automatic_lifecycle_source_edit": False,
        "next_stage_if_passed": "ACCEPTED_FOR_PAPER_TESTING",
    }
    checks = pd.DataFrame(
        [
            {
                "check": name,
                "passed": item["passed"],
                "operator": item["operator"],
                "actual": json.dumps(_json_safe(item["actual"]), sort_keys=True),
                "threshold": json.dumps(
                    _json_safe(item["threshold"]),
                    sort_keys=True,
                ),
            }
            for name, item in evaluation.checks.items()
        ]
    )
    review_lines = [
        "# EXP-005 Formal Review",
        "",
        f"**Decision:** {evaluation.decision}",
        "",
        "This review read only frozen result files. It did not rerun the "
        "strategy, MCPT, data import or optimization.",
        "",
        "## Checks",
        "",
    ]
    for name, item in evaluation.checks.items():
        status = "PASS" if item["passed"] else "FAIL"
        review_lines.append(f"- **{status} — {name}**")
    review_lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "Acceptance permits only a separately implemented paper-only "
            "simulator using the unchanged fixed EXP-005 rules and locked "
            "cost assumptions. It does not authorize live capital, leverage "
            "or post-result rule changes.",
        ]
    )

    REVIEW_ROOT.mkdir(parents=True, exist_ok=True)
    _atomic_csv(checks, REVIEW_ROOT / "review_checks.csv")
    report_path = REVIEW_ROOT / "review_report.md"
    temporary_report = report_path.with_suffix(".md.tmp")
    temporary_report.write_text(
        "\n".join(review_lines),
        encoding="utf-8",
    )
    temporary_report.replace(report_path)

    # Decision is written last as the one-time immutable completion marker.
    _atomic_json(decision, DECISION_FILE)

    print(f"Decision: {evaluation.decision}")
    for name, item in evaluation.checks.items():
        status = "PASS" if item["passed"] else "FAIL"
        print(f"{status} | {name}")
    print()
    print(
        "Failed checks: "
        + (
            ", ".join(evaluation.failed_checks)
            if evaluation.failed_checks
            else "None"
        )
    )
    print(f"Decision file: {DECISION_FILE.resolve()}")
    print(f"Review report: {report_path.resolve()}")
    print("=================================================")


if __name__ == "__main__":
    main()
