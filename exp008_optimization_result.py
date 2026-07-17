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
    / "EXP-008_optimization_result.json"
)
LOCAL_DECISION_FILE = (
    PROJECT_DIR
    / "results"
    / "EXP-008"
    / "exit_geometry"
    / "optimization_decision.json"
)

EXPECTED_CANONICAL_SHA256 = (
    "37195ffb723da317eff28fd9c39eb02cb96fb0b2b0027f863423ea3b94ebde6f"
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


def validate_exp008_result(
    record: dict[str, Any],
) -> None:
    if (
        record.get("schema_version") != 1
        or record.get("experiment_id") != "EXP-008"
        or record.get("stage")
        != "STRUCTURED_EXIT_GEOMETRY_OPTIMIZATION"
    ):
        raise ValueError(
            "EXP-008 result identity changed."
        )

    git = record["git"]
    if (
        git["commit"]
        != "34c03901bb0fc68ea33caef9b0d458dbd688e8c5"
        or git["working_tree_clean"] is not True
    ):
        raise ValueError(
            "EXP-008 implementation provenance changed."
        )

    data = record["data"]
    if (
        data["included_sessions"] != 1639
        or data["one_minute_rows_per_symbol"] != 639210
        or data["five_minute_rows_per_symbol"] != 127842
        or data["new_data_cleaning_decisions"] != 0
    ):
        raise ValueError(
            "EXP-008 frozen data evidence changed."
        )

    grid = record["grid"]
    if (
        grid["combination_count"] != 27
        or grid["eligible_candidates"] != 27
        or grid["stable_eligible_candidates"] != 27
        or grid["exp007_baseline_parameter_key"]
        != "or30_target1p0_flat1400"
        or grid["selected_parameter_key"]
        != "or45_target1p5_flat1555"
    ):
        raise ValueError(
            "EXP-008 grid or selected candidate changed."
        )

    selected = grid["selected_parameters"]
    if (
        selected["opening_range_minutes"] != 45
        or selected["reward_to_risk"] != 1.5
        or selected["forced_flat_time_new_york"]
        != "15:55"
    ):
        raise ValueError(
            "EXP-008 selected parameters changed."
        )

    selected_row = grid["selected_grid_row"]
    if (
        selected_row["neighbor_stable"] is not True
        or selected_row["profitable_neighbor_count"] != 3
        or selected_row["neighbor_count"] != 3
        or abs(
            float(
                selected_row[
                    "neighbor_median_nq_trade_profit_factor"
                ]
            )
            - 1.1162966353856718
        ) > 1e-12
    ):
        raise ValueError(
            "EXP-008 neighbor evidence changed."
        )

    nq = record["results"]["NQ"]
    if (
        nq["completed_trades"] != 994
        or abs(
            float(nq["net_profit_usd"])
            - 102802.5
        ) > 1e-12
        or abs(
            float(nq["trade_profit_factor"])
            - 1.156583426626151
        ) > 1e-12
        or abs(
            float(nq["maximum_drawdown_usd"])
            - (-26640.0)
        ) > 1e-12
    ):
        raise ValueError(
            "EXP-008 NQ result changed."
        )

    mnq = record["results"]["MNQ"]
    if (
        mnq["completed_trades"] != 994
        or abs(
            float(mnq["net_profit_usd"])
            - 8729.25
        ) > 1e-12
        or abs(
            float(mnq["trade_profit_factor"])
            - 1.1313745851863557
        ) > 1e-12
    ):
        raise ValueError(
            "EXP-008 MNQ result changed."
        )

    walk_forward = record["walk_forward"]
    if (
        walk_forward["fold_count"] != 5
        or walk_forward["profitable_test_folds"] != 4
        or abs(
            float(
                walk_forward[
                    "combined_test_net_profit_usd"
                ]
            )
            - 59132.5
        ) > 1e-12
    ):
        raise ValueError(
            "EXP-008 walk-forward evidence changed."
        )

    annual = record[
        "final_candidate_annual_evaluation"
    ]
    if (
        annual["profitable_nq_years"] != 4
        or abs(
            float(
                annual[
                    "combined_2021_2025_nq_net_profit_usd"
                ]
            )
            - 89640.0
        ) > 1e-12
    ):
        raise ValueError(
            "EXP-008 annual evidence changed."
        )

    two_tick_nq = next(
        item
        for item in record["cost_sensitivity"]
        if (
            item["symbol"] == "NQ"
            and item["slippage_ticks_per_side"] == 2.0
        )
    )
    if abs(
        float(two_tick_nq["net_profit_usd"])
        - 92862.5
    ) > 1e-12:
        raise ValueError(
            "EXP-008 two-tick stress changed."
        )

    bootstrap = record["bootstrap"]
    if (
        bootstrap["resamples"] != 10000
        or bootstrap["random_seed"] != 4801
        or bootstrap["decision_gate"] is not False
        or abs(
            float(
                bootstrap[
                    "average_trade_probability_above_zero"
                ]
            )
            - 0.9621
        ) > 1e-12
    ):
        raise ValueError(
            "EXP-008 bootstrap evidence changed."
        )

    mcpt = record["mcpt"]
    if (
        mcpt["permutations"] != 1000
        or mcpt["base_seed"] != 48
        or mcpt["permutations_at_least_real"] != 138
        or abs(
            float(mcpt["p_value"])
            - 0.13886113886113885
        ) > 1e-12
        or mcpt[
            "all_27_candidates_inside_each_permutation"
        ] is not True
        or mcpt[
            "selection_inside_each_permutation"
        ] is not True
    ):
        raise ValueError(
            "EXP-008 MCPT evidence changed."
        )

    comparison = record["baseline_comparison"]
    if (
        comparison["exp007_parameter_key"]
        != "or30_target1p0_flat1400"
        or abs(
            float(
                comparison[
                    "exp007_frozen_nq_trade_profit_factor"
                ]
            )
            - 1.1168167521220216
        ) > 1e-12
        or abs(
            float(
                comparison[
                    "absolute_profit_factor_difference"
                ]
            )
            - 0.03976667450412941
        ) > 1e-12
        or comparison["strict_improvement_required"]
        is not True
        or comparison[
            "fixed_minimum_improvement_amount"
        ] is not None
    ):
        raise ValueError(
            "EXP-008 baseline comparison changed."
        )

    evaluation = record["evaluation"]
    if (
        evaluation["decision"]
        != "REJECT_EXP008_PRESERVE_AS_NEGATIVE_RESULT"
        or evaluation["passed"] is not False
        or evaluation["failed_gates"]
        != ["selection_aware_nq_mcpt_p_value"]
    ):
        raise ValueError(
            "EXP-008 rejection decision changed."
        )

    failed = evaluation["gates"][
        "selection_aware_nq_mcpt_p_value"
    ]
    if (
        abs(
            float(failed["actual"])
            - 0.13886113886113885
        ) > 1e-12
        or abs(
            float(failed["threshold"])
            - 0.05
        ) > 1e-12
        or failed["passed"] is not False
    ):
        raise ValueError(
            "EXP-008 failed gate changed."
        )

    if (
        record["exp005_control_changed"]
        is not False
        or record["exp006_result_changed"]
        is not False
        or record["exp007_result_changed"]
        is not False
        or record["live_trading_authorized"]
        is not False
        or evaluation["live_trading_authorized"]
        is not False
    ):
        raise ValueError(
            "EXP-008 safety fields changed."
        )


def _load_and_verify(
    path: Path,
    *,
    description: str,
) -> dict[str, Any]:
    record = load_json_object(path)
    validate_exp008_result(record)

    actual_hash = canonical_record_sha256(
        record
    )
    if (
        actual_hash
        != EXPECTED_CANONICAL_SHA256
    ):
        raise ValueError(
            f"{description} canonical EXP-008 "
            "result hash changed. "
            f"Expected {EXPECTED_CANONICAL_SHA256}, "
            f"got {actual_hash}."
        )

    return record


def load_tracked_exp008_optimization_result(
) -> dict[str, Any]:
    return _load_and_verify(
        TRACKED_RESULT_FILE,
        description="Tracked",
    )


def get_exp008_optimization_result(
) -> dict[str, Any]:
    return deepcopy(
        load_tracked_exp008_optimization_result()
    )


def verify_local_exp008_optimization_decision(
) -> dict[str, Any]:
    tracked = (
        load_tracked_exp008_optimization_result()
    )
    local = _load_and_verify(
        LOCAL_DECISION_FILE,
        description="Local",
    )

    if local != tracked:
        raise ValueError(
            "Local and tracked EXP-008 results differ."
        )

    return local


if __name__ == "__main__":
    verify_local_exp008_optimization_decision()
    print(
        "EXP-008 rejected optimization result is "
        "frozen and valid."
    )
