from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parent
TRACKED_RESULT_FILE = (
    PROJECT_DIR
    / "research"
    / "EXP-006_optimization_result.json"
)
LOCAL_DECISION_FILE = (
    PROJECT_DIR
    / "results"
    / "EXP-006"
    / "optimization"
    / "optimization_decision.json"
)

# SHA-256 of the canonical JSON serialization used by
# run_exp006_optimization.py:
#
# json.dumps(record, indent=2, allow_nan=False)
#
# This deliberately ignores Windows CRLF versus LF byte
# encoding while preserving the complete JSON content.
EXPECTED_SHA256 = (
    "f7b1c87e29024562feef0d0b212a2df9"
    "75ed5d805e5a2edf787a3739f0744025"
)


def canonical_json_bytes(
    record: dict[str, Any],
) -> bytes:
    return json.dumps(
        record,
        indent=2,
        allow_nan=False,
    ).encode("utf-8")


def canonical_record_sha256(
    record: dict[str, Any],
) -> str:
    return hashlib.sha256(
        canonical_json_bytes(record)
    ).hexdigest()


def load_json_object(
    path: Path,
) -> dict[str, Any]:
    if not Path(path).exists():
        raise FileNotFoundError(path)

    value = json.loads(
        Path(path).read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(value, dict):
        raise ValueError(
            f"Expected a JSON object: {path}"
        )

    return value


def validate_exp006_result(
    record: dict[str, Any],
) -> None:
    if (
        record.get("experiment_id") != "EXP-006"
        or record.get("stage")
        != "STRUCTURED_OPTIMIZATION"
    ):
        raise ValueError(
            "EXP-006 result identity changed."
        )

    evaluation = record["evaluation"]
    if (
        evaluation["decision"]
        != "REJECT_EXP006_KEEP_EXP005_CONTROL"
        or evaluation["passed"] is not False
        or evaluation["failed_gates"]
        != ["nq_profit_factor_improvement"]
    ):
        raise ValueError(
            "EXP-006 rejection decision changed."
        )

    gate = evaluation["gates"][
        "nq_profit_factor_improvement"
    ]
    if (
        abs(
            float(gate["actual"])
            - 0.017995047063277925
        ) > 1e-12
        or abs(
            float(gate["threshold"])
            - 0.02
        ) > 1e-12
        or gate["passed"] is not False
    ):
        raise ValueError(
            "EXP-006 failed gate changed."
        )

    selected = record["grid"][
        "selected_parameters"
    ]
    if (
        selected["parameter_key"]
        != "or15_entry1030_both"
    ):
        raise ValueError(
            "EXP-006 selected candidate changed."
        )

    mcpt = record["mcpt"]
    if (
        mcpt["permutations"] != 1000
        or abs(
            float(mcpt["p_value"])
            - 0.024975024975024976
        ) > 1e-12
    ):
        raise ValueError(
            "EXP-006 MCPT evidence changed."
        )

    if (
        record["exp005_control_changed"]
        is not False
        or record["live_trading_authorized"]
        is not False
    ):
        raise ValueError(
            "EXP-006 safety fields changed."
        )


def _load_and_verify(
    path: Path,
    *,
    description: str,
) -> dict[str, Any]:
    record = load_json_object(path)
    validate_exp006_result(record)

    actual_hash = canonical_record_sha256(
        record
    )
    if actual_hash != EXPECTED_SHA256:
        raise ValueError(
            f"{description} canonical EXP-006 "
            "result hash changed. "
            f"Expected {EXPECTED_SHA256}, "
            f"got {actual_hash}."
        )

    return record


def load_tracked_exp006_optimization_result(
) -> dict[str, Any]:
    return _load_and_verify(
        TRACKED_RESULT_FILE,
        description="Tracked",
    )


def get_exp006_optimization_result(
) -> dict[str, Any]:
    return deepcopy(
        load_tracked_exp006_optimization_result()
    )


def verify_local_exp006_optimization_decision(
) -> dict[str, Any]:
    tracked = (
        load_tracked_exp006_optimization_result()
    )
    local = _load_and_verify(
        LOCAL_DECISION_FILE,
        description="Local",
    )

    if local != tracked:
        raise ValueError(
            "Local and tracked EXP-006 results differ."
        )

    return local


if __name__ == "__main__":
    verify_local_exp006_optimization_decision()
    print(
        "EXP-006 rejection is frozen and valid."
    )
