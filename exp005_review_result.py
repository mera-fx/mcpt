from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

PROJECT_DIR = Path(__file__).resolve().parent
TRACKED_RESULT_FILE = PROJECT_DIR / "research" / "EXP-005_review_result.json"
LOCAL_DECISION_FILE = (
    PROJECT_DIR / "results" / "EXP-005" / "review" / "review_decision.json"
)
EXPECTED_FILE_SHA256 = "3ac6538b1645f674174bb2716a893eb3ec8e1a131c64d05de438db5d12829751"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_exp005_review_result(record: dict[str, Any]) -> None:
    if (
        record.get("schema_version") != 1
        or record.get("experiment_id") != "EXP-005"
        or record.get("stage") != "REVIEW"
    ):
        raise ValueError("EXP-005 review result identity changed.")

    git = record["git"]
    if (
        git["commit"] != "5888a0bf54fa0f87fe76a71914b62d6a9e20bf10"
        or git["short_commit"] != "5888a0b"
        or git["working_tree_clean"] is not True
    ):
        raise ValueError("EXP-005 review Git provenance changed.")

    source = record["source_full_validation"]
    if (
        source["decision"] != "PASS_TO_REVIEW"
        or source["implementation_commit"]
        != "1dc8b32f2eba1b19e19d3162d5f0acd2f820593e"
        or source["included_sessions"] != 733
        or source["nq_mcpt_permutations"] != 1000
        or abs(float(source["nq_mcpt_p_value"]) - 0.03796203796203796) > 1e-15
    ):
        raise ValueError("EXP-005 review source evidence changed.")

    evaluation = record["evaluation"]
    if (
        evaluation["decision"] != "ACCEPT_FOR_PAPER_TESTING"
        or evaluation["passed"] is not True
        or evaluation["failed_checks"] != []
        or len(evaluation["checks"]) != 12
        or not all(item["passed"] is True for item in evaluation["checks"].values())
    ):
        raise ValueError("EXP-005 review acceptance changed.")

    expected_checks = {
        "full_validation_integrity",
        "fixed_rule_integrity",
        "data_integrity",
        "cross_period_replication",
        "all_confirmation_years_profitable",
        "two_tick_cost_resilience",
        "average_trade_cost_buffer",
        "drawdown_efficiency",
        "contract_implementation_consistency",
        "direction_balance",
        "tail_loss_concentration",
        "largest_loss_drawdown_share",
    }
    if set(evaluation["checks"]) != expected_checks:
        raise ValueError("EXP-005 review check set changed.")

    for field in (
        "strategy_rerun",
        "mcpt_rerun",
        "parameter_change",
        "cost_change",
        "data_change",
        "quick_transfer_rerun",
        "automatic_lifecycle_source_edit",
    ):
        if record[field] is not False:
            raise ValueError(f"EXP-005 review protection changed: {field}.")

    if record["next_stage_if_passed"] != "ACCEPTED_FOR_PAPER_TESTING":
        raise ValueError("EXP-005 review next stage changed.")


def load_tracked_review_result() -> dict[str, Any]:
    if not TRACKED_RESULT_FILE.exists():
        raise FileNotFoundError(
            f"Tracked EXP-005 review result is missing: {TRACKED_RESULT_FILE}"
        )
    if sha256_file(TRACKED_RESULT_FILE) != EXPECTED_FILE_SHA256:
        raise ValueError("Tracked EXP-005 review-result hash changed.")
    result = json.loads(TRACKED_RESULT_FILE.read_text(encoding="utf-8"))
    validate_exp005_review_result(result)
    return result


def get_exp005_review_result() -> dict[str, Any]:
    return deepcopy(load_tracked_review_result())


def verify_local_exp005_review_decision() -> dict[str, Any]:
    tracked = load_tracked_review_result()
    if not LOCAL_DECISION_FILE.exists():
        raise FileNotFoundError(
            f"The original local EXP-005 review decision is missing: "
            f"{LOCAL_DECISION_FILE}"
        )
    if sha256_file(LOCAL_DECISION_FILE) != EXPECTED_FILE_SHA256:
        raise ValueError(
            "The local EXP-005 review decision does not match the frozen hash."
        )
    local = json.loads(LOCAL_DECISION_FILE.read_text(encoding="utf-8"))
    validate_exp005_review_result(local)
    if local != tracked:
        raise ValueError("Local and tracked EXP-005 review decisions differ.")
    return local


if __name__ == "__main__":
    verify_local_exp005_review_decision()
    print("EXP-005 review acceptance is frozen and valid.")
