from __future__ import annotations

from typing import TypedDict


class DecisionRecord(TypedDict):
    status: str
    reason: str


ALLOWED_STATUSES = {
    "PLANNED",
    "RUNNING",
    "REVIEW",
    "ACCEPTED",
    "REJECTED",
}


# This file is the single place where final research decisions are stored.
# The dashboard never invents a pass/fail decision from performance alone.
EXPERIMENT_DECISIONS: dict[str, DecisionRecord] = {
    "EXP-001": {
        "status": "REJECTED",
        "reason": (
            "Weak and borderline in-sample evidence, MCPT p-value "
            "0.0529, negative fixed out-of-sample performance and "
            "worse walk-forward results."
        ),
    },
    "EXP-002": {
        "status": "REJECTED",
        "reason": (
            "Best in-sample Profit Factor was below 1.0. Both fixed "
            "and walk-forward versions lost money, with large "
            "negative-skew tail losses."
        ),
    },
}


def get_experiment_decision(
    experiment_id: str,
) -> DecisionRecord:
    record = EXPERIMENT_DECISIONS.get(
        experiment_id,
        {
            "status": "REVIEW",
            "reason": (
                "No final research decision has been recorded yet."
            ),
        },
    )

    status = record["status"].upper()

    if status not in ALLOWED_STATUSES:
        raise ValueError(
            f"Invalid status '{status}' for {experiment_id}. "
            f"Allowed values: {sorted(ALLOWED_STATUSES)}"
        )

    return {
        "status": status,
        "reason": record["reason"],
    }


if __name__ == "__main__":
    print("Recorded experiment decisions")
    print("-----------------------------")

    for experiment_id, record in sorted(
        EXPERIMENT_DECISIONS.items()
    ):
        print(
            f"{experiment_id}: "
            f"{record['status']} — "
            f"{record['reason']}"
        )
