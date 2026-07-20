from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from exp013_preregistration import validate_exp013_preregistration


PROJECT_DIR = Path(__file__).resolve().parent
RESULT_DIR = (
    PROJECT_DIR / "results" / "EXP-013" / "extended_context_validation"
)
VALIDATION_FILE = RESULT_DIR / "validation_result.json"
CANDIDATE_FILE = RESULT_DIR / "candidate_measurements.csv"
WALK_FORWARD_FILE = RESULT_DIR / "anchored_walk_forward.csv"
BOOTSTRAP_FILE = RESULT_DIR / "bootstrap_diagnostics.json"
COST_FILE = RESULT_DIR / "cost_sensitivity.csv"
MCPT_FILE = RESULT_DIR / "mcpt_results.csv"

EXPECTED_VALIDATION_CANONICAL_SHA256 = (
    "6509b0151c1c9e977bf90311b521e05b5ae38119f1cec1491601fa8c6a1d1f16"
)
EXPECTED_CANDIDATE_CANONICAL_SHA256 = (
    "7190e5f26a185658f6f03a132de1a94bdb62c7a15b30f81499ab79d567b10d72"
)
EXPECTED_WALK_FORWARD_CANONICAL_SHA256 = (
    "5ad6b8f116fdc8bafa22fa80362230ae2e3f1b6b5f145ed9897aae213e7b32a5"
)
EXPECTED_BOOTSTRAP_CANONICAL_SHA256 = (
    "fb693ad8629a207201f7bf7c4790a3511355cace28bda356494de11af01b389d"
)
EXPECTED_COST_CANONICAL_SHA256 = (
    "d96e3031a82d2797071b7b20f3179732aa8f7b68a59a0027fa94d7b8302750e5"
)
EXPECTED_MCPT_CANONICAL_SHA256 = (
    "913cb5e6c50ebed393f622020850b5ca3edfa9771a989a059e6b09a69886a7ba"
)
EXPECTED_IMPLEMENTATION_COMMIT = (
    "226b54c491bf4510d856499298074ec5f884ed2c"
)


def _json_default(value: Any) -> Any:
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.bool_):
        return bool(value)
    raise TypeError(f"Unsupported canonical value: {type(value)!r}")


def canonical_object_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
        default=_json_default,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def canonical_dataframe_sha256(frame: pd.DataFrame) -> str:
    normalized = frame.astype(object).where(pd.notna(frame), None)
    return canonical_object_sha256(normalized.to_dict(orient="records"))


def load_json_object(path: Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def load_validation_result(
    path: Path = VALIDATION_FILE,
) -> dict[str, Any]:
    return load_json_object(path)


def load_candidate_measurements(
    path: Path = CANDIDATE_FILE,
) -> pd.DataFrame:
    return pd.read_csv(path).sort_values(
        "candidate_id", kind="stable"
    ).reset_index(drop=True)


def load_walk_forward(
    path: Path = WALK_FORWARD_FILE,
) -> pd.DataFrame:
    return pd.read_csv(path).sort_values(
        "fold", kind="stable"
    ).reset_index(drop=True)


def load_bootstrap(
    path: Path = BOOTSTRAP_FILE,
) -> dict[str, Any]:
    return load_json_object(path)


def load_cost_sensitivity(
    path: Path = COST_FILE,
) -> pd.DataFrame:
    return pd.read_csv(path).sort_values(
        ["candidate_id", "slippage_ticks_per_side"],
        kind="stable",
    ).reset_index(drop=True)


def load_mcpt(
    path: Path = MCPT_FILE,
) -> pd.DataFrame:
    return pd.read_csv(path).sort_values(
        "permutation", kind="stable"
    ).reset_index(drop=True)


def _assert_close(actual: Any, expected: float, *, label: str) -> None:
    if not np.isclose(float(actual), expected, atol=1e-12, rtol=0.0):
        raise ValueError(
            f"EXP-013 {label} changed: expected {expected}, got {actual}."
        )


def _validate_candidate_measurements(
    candidates: pd.DataFrame,
) -> None:
    expected = {
        "gap_fade_0p50_1r": {
            "completed_trades": 186,
            "trade_profit_factor": 1.530923511019599,
            "win_rate": 0.5967741935483871,
            "net_profit_usd": 34810.0,
            "maximum_drawdown_usd": -5080.0,
            "net_profit_to_drawdown": 6.852362204724409,
            "mnq_profit_factor": 1.4843807695148068,
            "two_tick_net_profit_usd": 32950.0,
            "low_sample": False,
            "measurement_leader": False,
        },
        "premarket_continuation_0p50_time": {
            "completed_trades": 291,
            "trade_profit_factor": 1.7363738499377523,
            "win_rate": 0.27835051546391754,
            "net_profit_usd": 121255.0,
            "maximum_drawdown_usd": -20695.0,
            "net_profit_to_drawdown": 5.859144720947088,
            "mnq_profit_factor": 1.670737975027965,
            "two_tick_net_profit_usd": 118345.0,
            "low_sample": False,
            "measurement_leader": False,
        },
        "premarket_continuation_0p75_time": {
            "completed_trades": 88,
            "trade_profit_factor": 2.0237378415933303,
            "win_rate": 0.3181818181818182,
            "net_profit_usd": 44205.0,
            "maximum_drawdown_usd": -5540.0,
            "net_profit_to_drawdown": 7.979241877256317,
            "mnq_profit_factor": 2.0982798165137613,
            "two_tick_net_profit_usd": 43325.0,
            "low_sample": True,
            "measurement_leader": True,
        },
    }
    if (
        len(candidates) != 3
        or candidates["candidate_id"].nunique() != 3
        or set(candidates["candidate_id"]) != set(expected)
        or int(candidates["eligible"].sum()) != 3
        or int(candidates["measurement_leader"].sum()) != 1
    ):
        raise ValueError("EXP-013 finalist measurement set changed.")

    indexed = candidates.set_index("candidate_id")
    for candidate_id, fields in expected.items():
        row = indexed.loc[candidate_id]
        for field, expected_value in fields.items():
            actual = row[field]
            if isinstance(expected_value, bool):
                if bool(actual) is not expected_value:
                    raise ValueError(
                        f"EXP-013 {candidate_id} {field} changed."
                    )
            elif isinstance(expected_value, int):
                if int(actual) != expected_value:
                    raise ValueError(
                        f"EXP-013 {candidate_id} {field} changed."
                    )
            else:
                _assert_close(
                    actual,
                    expected_value,
                    label=f"{candidate_id} {field}",
                )


def _validate_supporting_files() -> None:
    candidates = load_candidate_measurements()
    _validate_candidate_measurements(candidates)

    walk_forward = load_walk_forward()
    if (
        len(walk_forward) != 4
        or list(walk_forward["test_year"]) != [2022, 2023, 2024, 2025]
        or int(walk_forward["test_profitable"].sum()) != 3
        or set(walk_forward["selected_candidate_id"])
        != {"premarket_continuation_0p75_time"}
    ):
        raise ValueError("EXP-013 walk-forward rows changed.")
    _assert_close(
        walk_forward["test_net_profit_usd"].sum(),
        26295.0,
        label="walk-forward combined net profit",
    )

    bootstrap = load_bootstrap()
    diagnostics = bootstrap.get("diagnostics")
    if (
        not isinstance(diagnostics, list)
        or len(diagnostics) != 3
        or {item["candidate_id"] for item in diagnostics}
        != set(candidates["candidate_id"])
        or any(item["resamples"] != 10000 for item in diagnostics)
        or any(item["random_seed"] != 5301 for item in diagnostics)
        or any(item["decision_gate"] is not False for item in diagnostics)
        or any(
            item["average_trade_probability_above_zero"] < 0.99
            for item in diagnostics
        )
        or any(
            item["profit_factor_probability_above_one"] < 0.99
            for item in diagnostics
        )
    ):
        raise ValueError("EXP-013 bootstrap evidence changed.")

    costs = load_cost_sensitivity()
    if (
        len(costs) != 9
        or set(costs["candidate_id"]) != set(candidates["candidate_id"])
        or set(costs["slippage_ticks_per_side"]) != {0, 1, 2}
        or int((costs["net_profit_usd"] > 0.0).sum()) != 9
    ):
        raise ValueError("EXP-013 cost-sensitivity evidence changed.")

    mcpt = load_mcpt()
    if (
        len(mcpt) != 1000
        or mcpt["permutation"].nunique() != 1000
        or int(mcpt["maximum_ge_real"].sum()) != 3
        or int(mcpt["fixed_gap_fade_0p50_1r_ge_real"].sum()) != 1
        or int(
            mcpt[
                "fixed_premarket_continuation_0p50_time_ge_real"
            ].sum()
        )
        != 0
        or int(
            mcpt[
                "fixed_premarket_continuation_0p75_time_ge_real"
            ].sum()
        )
        != 0
    ):
        raise ValueError("EXP-013 permutation evidence changed.")


def validate_exp013_validation_result(
    record: dict[str, Any],
    *,
    verify_hashes: bool = True,
) -> None:
    validate_exp013_preregistration()

    if (
        record.get("schema_version") != 1
        or record.get("experiment_id") != "EXP-013"
        or record.get("result_status")
        != "MEASURED_HISTORICAL_VALIDATION"
    ):
        raise ValueError("EXP-013 result identity changed.")

    git = record["git"]
    if (
        git["commit"] != EXPECTED_IMPLEMENTATION_COMMIT
        or git["short_commit"] != "226b54c"
        or git["working_tree_clean"] is not True
    ):
        raise ValueError("EXP-013 implementation provenance changed.")

    data = record["data"]
    if (
        data["source_experiment"] != "EXP-012"
        or data["included_sessions"] != 1331
        or data["historical_start"] != "2020-01-03"
        or data["historical_end"] != "2025-12-31"
        or data["new_data_cleaning_decisions"] != 0
    ):
        raise ValueError("EXP-013 frozen data evidence changed.")

    selection = record["selection"]
    if (
        selection["candidate_count"] != 3
        or selection["eligible_candidates"] != 3
        or selection["measurement_leader_id"]
        != "premarket_continuation_0p75_time"
        or selection["automatic_trading_winner"] is not False
        or selection["post_exp012_human_shortlist"] is not True
    ):
        raise ValueError("EXP-013 selection context changed.")

    selected = record["results"]["measurement_leader_NQ"]
    if (
        selected["candidate_id"]
        != "premarket_continuation_0p75_time"
        or selected["completed_trades"] != 88
        or selected["long_trades"] != 44
        or selected["short_trades"] != 44
    ):
        raise ValueError("EXP-013 measurement-leader counts changed.")
    _assert_close(
        selected["trade_profit_factor"],
        2.0237378415933303,
        label="measurement-leader NQ Profit Factor",
    )
    _assert_close(
        selected["net_profit_usd"],
        44205.0,
        label="measurement-leader NQ net profit",
    )
    _assert_close(
        selected["maximum_drawdown_usd"],
        -5540.0,
        label="measurement-leader NQ maximum drawdown",
    )

    selected_mnq = record["results"]["measurement_leader_MNQ"]
    if selected_mnq["completed_trades"] != 89:
        raise ValueError("EXP-013 measurement-leader MNQ count changed.")
    _assert_close(
        selected_mnq["trade_profit_factor"],
        2.0982798165137613,
        label="measurement-leader MNQ Profit Factor",
    )
    _assert_close(
        selected_mnq["net_profit_usd"],
        4788.5,
        label="measurement-leader MNQ net profit",
    )

    walk_forward = record["walk_forward"]
    if (
        walk_forward["fold_count"] != 4
        or walk_forward["profitable_test_folds"] != 3
    ):
        raise ValueError("EXP-013 walk-forward fold evidence changed.")
    _assert_close(
        walk_forward["combined_test_net_profit_usd"],
        26295.0,
        label="walk-forward combined net profit",
    )

    bootstrap = record["bootstrap"]
    if (
        len(bootstrap) != 3
        or any(item["resamples"] != 10000 for item in bootstrap)
        or any(item["random_seed"] != 5301 for item in bootstrap)
        or any(item["decision_gate"] is not False for item in bootstrap)
    ):
        raise ValueError("EXP-013 bootstrap evidence changed.")

    mcpt = record["mcpt"]
    if (
        mcpt["permutations"] != 1000
        or mcpt["base_seed"] != 53
        or mcpt["source_candidate_count"] != 24
        or mcpt["permutations_at_least_real"] != 3
        or mcpt["all_24_candidates_inside_every_permutation"] is not True
        or mcpt["does_not_erase_post_result_human_selection"] is not True
    ):
        raise ValueError("EXP-013 discovery-wide MCPT evidence changed.")
    _assert_close(
        mcpt["discovery_wide_p_value"],
        4 / 1001,
        label="discovery-wide MCPT p-value",
    )

    evaluation = record["evaluation"]
    if (
        evaluation["classification"] != "STRONG_HISTORICAL_EVIDENCE"
        or evaluation["classification_is_secondary"] is not True
        or evaluation["measurement_first"] is not True
        or evaluation["profitable_walk_forward_folds"] != 3
        or evaluation["lifecycle_accept_reject_decision"] is not None
        or evaluation["paper_trading_authorized"] is not False
        or evaluation["live_trading_authorized"] is not False
        or not all(evaluation["strong_context_checks"].values())
    ):
        raise ValueError("EXP-013 evidence classification changed.")

    if (
        record["historical_status"]
        != "EXPLORATORY_DEEP_VALIDATION_BECAUSE_EXP012_RESULTS_AND_FINALIST_SELECTION_WERE_ALREADY_VIEWED"
        or record["independent_confirmation"] is not False
        or record["paper_trading_authorized"] is not False
        or record["live_trading_authorized"] is not False
        or record["automatic_lifecycle_source_edit"] is not False
    ):
        raise ValueError("EXP-013 research boundary changed.")

    _validate_supporting_files()

    if verify_hashes:
        hashes = {
            "validation": canonical_object_sha256(record),
            "candidates": canonical_dataframe_sha256(
                load_candidate_measurements()
            ),
            "walk_forward": canonical_dataframe_sha256(
                load_walk_forward()
            ),
            "bootstrap": canonical_object_sha256(load_bootstrap()),
            "cost": canonical_dataframe_sha256(
                load_cost_sensitivity()
            ),
            "mcpt": canonical_dataframe_sha256(load_mcpt()),
        }
        expected = {
            "validation": EXPECTED_VALIDATION_CANONICAL_SHA256,
            "candidates": EXPECTED_CANDIDATE_CANONICAL_SHA256,
            "walk_forward": EXPECTED_WALK_FORWARD_CANONICAL_SHA256,
            "bootstrap": EXPECTED_BOOTSTRAP_CANONICAL_SHA256,
            "cost": EXPECTED_COST_CANONICAL_SHA256,
            "mcpt": EXPECTED_MCPT_CANONICAL_SHA256,
        }
        if hashes != expected:
            raise ValueError("EXP-013 frozen result hashes changed.")


def verify_local_exp013_validation_result() -> dict[str, Any]:
    record = load_validation_result()
    validate_exp013_validation_result(record)
    return deepcopy(record)


if __name__ == "__main__":
    verify_local_exp013_validation_result()
    print("EXP-013 extended-context validation is frozen and valid.")
