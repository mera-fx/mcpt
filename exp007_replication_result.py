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
    / "EXP-007_replication_result.json"
)
LOCAL_DECISION_FILE = (
    PROJECT_DIR
    / "results"
    / "EXP-007"
    / "fixed_replication"
    / "replication_decision.json"
)

EXPECTED_CANONICAL_SHA256 = (
    "1af47620015d74b59d11124d31f08b905644f0012128d3cbca61e17d1def61e0"
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


def validate_exp007_result(
    record: dict[str, Any],
) -> None:
    if (
        record.get("schema_version") != 1
        or record.get("experiment_id") != "EXP-007"
        or record.get("stage")
        != "FIXED_HISTORICAL_REPLICATION"
    ):
        raise ValueError(
            "EXP-007 result identity changed."
        )

    git = record["git"]
    if (
        git["commit"]
        != "6802211a1f743042eb45e3fec49dd7e18024018f"
        or git["working_tree_clean"] is not True
    ):
        raise ValueError(
            "EXP-007 implementation provenance changed."
        )

    data = record["data"]
    if (
        data["included_sessions"] != 1639
        or data["one_minute_rows_per_symbol"] != 639210
        or data["five_minute_rows_per_symbol"] != 127842
        or data["new_data_cleaning_decisions"] != 0
    ):
        raise ValueError(
            "EXP-007 frozen data evidence changed."
        )

    fixed = record["fixed_rules"]
    if (
        fixed["optimization_enabled"] is not False
        or fixed["parameter_combinations"] != 1
        or fixed["direction_mode"] != "long_only"
        or fixed["opening_range_minutes"] != 30
        or fixed["reward_to_risk"] != 1.0
        or fixed["forced_flat_time_new_york"] != "14:00"
        or fixed["short_entries"] is not False
    ):
        raise ValueError(
            "EXP-007 fixed rules changed."
        )

    nq = record["results"]["NQ"]
    if (
        nq["completed_trades"] != 988
        or abs(
            float(nq["net_profit_usd"])
            - 67780.0
        ) > 1e-12
        or abs(
            float(nq["trade_profit_factor"])
            - 1.1168167521220216
        ) > 1e-12
        or abs(
            float(nq["maximum_drawdown_usd"])
            - (-26020.0)
        ) > 1e-12
    ):
        raise ValueError(
            "EXP-007 NQ result changed."
        )

    mnq = record["results"]["MNQ"]
    if (
        mnq["completed_trades"] != 985
        or abs(
            float(mnq["net_profit_usd"])
            - 5649.5
        ) > 1e-12
        or abs(
            float(mnq["trade_profit_factor"])
            - 1.0964457039452344
        ) > 1e-12
    ):
        raise ValueError(
            "EXP-007 MNQ result changed."
        )

    annual = record["annual_evaluation"]
    if (
        annual["profitable_nq_blocks"] != 4
        or abs(
            float(
                annual[
                    "combined_2021_2025_nq_net_profit_usd"
                ]
            )
            - 70880.0
        ) > 1e-12
    ):
        raise ValueError(
            "EXP-007 annual evidence changed."
        )

    bootstrap = record["bootstrap"]
    if (
        bootstrap["resamples"] != 10000
        or bootstrap["random_seed"] != 4701
        or bootstrap["decision_gate"] is not False
        or abs(
            float(
                bootstrap[
                    "average_trade_probability_above_zero"
                ]
            )
            - 0.9079
        ) > 1e-12
    ):
        raise ValueError(
            "EXP-007 bootstrap evidence changed."
        )

    mcpt = record["mcpt"]
    if (
        mcpt["permutations"] != 1000
        or mcpt["permutations_at_least_real"] != 55
        or abs(
            float(mcpt["p_value"])
            - 0.055944055944055944
        ) > 1e-12
        or mcpt[
            "optimization_inside_permutation"
        ] is not False
    ):
        raise ValueError(
            "EXP-007 MCPT evidence changed."
        )

    evaluation = record["evaluation"]
    if (
        evaluation["decision"]
        != "REJECT_EXP007_PRESERVE_AS_NEGATIVE_RESULT"
        or evaluation["passed"] is not False
        or evaluation["failed_gates"]
        != ["nq_session_aware_mcpt_p_value"]
    ):
        raise ValueError(
            "EXP-007 rejection decision changed."
        )

    failed = evaluation["gates"][
        "nq_session_aware_mcpt_p_value"
    ]
    if (
        abs(
            float(failed["actual"])
            - 0.055944055944055944
        ) > 1e-12
        or abs(
            float(failed["threshold"])
            - 0.05
        ) > 1e-12
        or failed["passed"] is not False
    ):
        raise ValueError(
            "EXP-007 failed gate changed."
        )

    if (
        record["exp005_control_changed"]
        is not False
        or record["exp006_result_changed"]
        is not False
        or record["live_trading_authorized"]
        is not False
        or evaluation["live_trading_authorized"]
        is not False
    ):
        raise ValueError(
            "EXP-007 safety fields changed."
        )


def _load_and_verify(
    path: Path,
    *,
    description: str,
) -> dict[str, Any]:
    record = load_json_object(path)
    validate_exp007_result(record)

    actual_hash = canonical_record_sha256(
        record
    )
    if (
        actual_hash
        != EXPECTED_CANONICAL_SHA256
    ):
        raise ValueError(
            f"{description} canonical EXP-007 "
            "result hash changed. "
            f"Expected {EXPECTED_CANONICAL_SHA256}, "
            f"got {actual_hash}."
        )

    return record


def load_tracked_exp007_replication_result(
) -> dict[str, Any]:
    return _load_and_verify(
        TRACKED_RESULT_FILE,
        description="Tracked",
    )


def get_exp007_replication_result(
) -> dict[str, Any]:
    return deepcopy(
        load_tracked_exp007_replication_result()
    )


def verify_local_exp007_replication_decision(
) -> dict[str, Any]:
    tracked = (
        load_tracked_exp007_replication_result()
    )
    local = _load_and_verify(
        LOCAL_DECISION_FILE,
        description="Local",
    )

    if local != tracked:
        raise ValueError(
            "Local and tracked EXP-007 results differ."
        )

    return local


if __name__ == "__main__":
    verify_local_exp007_replication_decision()
    print(
        "EXP-007 rejected replication is frozen "
        "and valid."
    )
