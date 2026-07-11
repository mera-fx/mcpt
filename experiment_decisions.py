from __future__ import annotations

from typing import TypedDict

from experiment_lifecycle import (
    get_experiment_lifecycle,
)


class DecisionRecord(TypedDict):
    status: str
    reason: str


ALLOWED_STATUSES = {
    "REVIEW",
    "ACCEPTED",
    "REJECTED",
}


def get_experiment_decision(
    experiment_id: str,
) -> DecisionRecord:
    lifecycle = get_experiment_lifecycle(
        experiment_id
    )

    if lifecycle.stage == "REJECTED":
        status = "REJECTED"
    elif (
        lifecycle.stage
        == "ACCEPTED_FOR_PAPER_TESTING"
    ):
        status = "ACCEPTED"
    else:
        status = "REVIEW"

    return {
        "status": status,
        "reason": lifecycle.stage_reason,
    }


if __name__ == "__main__":
    for experiment_id in (
        "EXP-001",
        "EXP-002",
        "EXP-003",
    ):
        decision = get_experiment_decision(
            experiment_id
        )

        print(
            f"{experiment_id}: "
            f"{decision['status']} — "
            f"{decision['reason']}"
        )
