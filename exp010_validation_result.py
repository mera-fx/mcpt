from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from exp010_preregistration import validate_exp010_preregistration


PROJECT_DIR = Path(__file__).resolve().parent
RESULT_DIR = (
    PROJECT_DIR / "results" / "EXP-010" / "opening_drive_validation"
)
VALIDATION_FILE = RESULT_DIR / "validation_result.json"
CANDIDATE_FILE = RESULT_DIR / "candidate_measurements.csv"
WALK_FORWARD_FILE = RESULT_DIR / "anchored_walk_forward.csv"
BOOTSTRAP_FILE = RESULT_DIR / "bootstrap_diagnostics.json"
COST_FILE = RESULT_DIR / "cost_sensitivity.csv"
MCPT_FILE = RESULT_DIR / "mcpt_results.csv"

EXPECTED_VALIDATION_CANONICAL_SHA256 = (
    "a45281d6056a8ccb76104abfb954f0c1f952ef15a23d85d82ee3b04cb17fed4d"
)
EXPECTED_CANDIDATE_CANONICAL_SHA256 = (
    "c9988048d7a7c15ddc2242150ff53c80d342941b78f661e8e9c512d5f557a45d"
)
EXPECTED_WALK_FORWARD_CANONICAL_SHA256 = (
    "261023c56c1f806551414c2be2a17ee49c78d3d163c562638ed244dbfed8c8dc"
)
EXPECTED_BOOTSTRAP_CANONICAL_SHA256 = (
    "dfc43e3ca88fb1d03d4c5e14ea8db82a6ab2b69c04bc71d4e32d08e2b6b02674"
)
EXPECTED_COST_CANONICAL_SHA256 = (
    "617edf19de21a06417073d5135eba4cf5b06250695500e76ad0d2d5e5774d9c1"
)
EXPECTED_MCPT_CANONICAL_SHA256 = (
    "52ce1d277400721907125ce032f50470b3996ef54482d0cbb104a1cf6aee0f1f"
)
EXPECTED_IMPLEMENTATION_COMMIT = (
    "aedbf1ff30a97ae3dccba0a510e9fafd9a9db1bb"
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
        ["candidate_id", "symbol", "slippage_ticks_per_side"],
        kind="stable",
    ).reset_index(drop=True)


def load_mcpt(
    path: Path = MCPT_FILE,
) -> pd.DataFrame:
    return pd.read_csv(path).sort_values(
        "permutation", kind="stable"
    ).reset_index(drop=True)


def _assert_close(actual: Any, expected: float, label: str) -> None:
    if not np.isclose(float(actual), expected, atol=1e-12, rtol=0.0):
        raise ValueError(
            f"EXP-010 {label} changed: expected {expected}, got {actual}."
        )


def validate_exp010_validation_result(
    record: dict[str, Any],
    *,
    verify_hashes: bool = True,
) -> None:
    validate_exp010_preregistration()

    if (
        record.get("schema_version") != 1
        or record.get("experiment_id") != "EXP-010"
        or record.get("result_status") != "MEASURED_DEEP_VALIDATION"
    ):
        raise ValueError("EXP-010 result identity changed.")

    git = record["git"]
    if (
        git["commit"] != EXPECTED_IMPLEMENTATION_COMMIT
        or git["short_commit"] != "aedbf1f"
        or git["working_tree_clean"] is not True
    ):
        raise ValueError("EXP-010 implementation provenance changed.")

    data = record["data"]
    if (
        data["source_experiment"] != "EXP-005"
        or data["included_sessions"] != 1639
        or data["historical_start"] != "2019-05-06"
        or data["historical_end"] != "2025-12-31"
        or data["new_data_cleaning_decisions"] != 0
    ):
        raise ValueError("EXP-010 frozen data evidence changed.")

    selection = record["selection"]
    if (
        selection["candidate_count"] != 4
        or selection["eligible_candidates"] != 4
        or selection["selected_candidate_id"]
        != "opening_drive_0p5_time"
        or selection["user_reference_candidate_id"]
        != "opening_drive_0p5_1p5r"
        or selection["user_reference_is_independent_preselection"] is not False
        or selection["automatic_trading_winner"] is not False
    ):
        raise ValueError("EXP-010 selection context changed.")

    selected = record["results"]["selected_NQ"]
    if (
        selected["completed_trades"] != 775
        or selected["long_trades"] != 426
        or selected["short_trades"] != 349
    ):
        raise ValueError("EXP-010 selected NQ trade counts changed.")
    _assert_close(
        selected["trade_profit_factor"],
        1.3500728278480598,
        "selected NQ Profit Factor",
    )
    _assert_close(
        selected["win_rate"],
        0.49290322580645163,
        "selected NQ win rate",
    )
    _assert_close(
        selected["net_profit_usd"],
        213905.0,
        "selected NQ net profit",
    )
    _assert_close(
        selected["maximum_drawdown_usd"],
        -25280.0,
        "selected NQ maximum drawdown",
    )

    selected_mnq = record["results"]["selected_MNQ"]
    if selected_mnq["completed_trades"] != 773:
        raise ValueError("EXP-010 selected MNQ trade count changed.")
    _assert_close(
        selected_mnq["trade_profit_factor"],
        1.3321549899867842,
        "selected MNQ Profit Factor",
    )
    _assert_close(
        selected_mnq["net_profit_usd"],
        20483.5,
        "selected MNQ net profit",
    )

    reference = record["results"]["user_reference_NQ"]
    if reference["completed_trades"] != 775:
        raise ValueError("EXP-010 reference trade count changed.")
    _assert_close(
        reference["trade_profit_factor"],
        1.3158469945355191,
        "reference NQ Profit Factor",
    )
    _assert_close(
        reference["win_rate"],
        0.52,
        "reference NQ win rate",
    )
    _assert_close(
        reference["net_profit_usd"],
        187850.0,
        "reference NQ net profit",
    )
    _assert_close(
        reference["maximum_drawdown_usd"],
        -24930.0,
        "reference NQ maximum drawdown",
    )

    walk_forward = record["walk_forward"]
    if (
        walk_forward["fold_count"] != 5
        or walk_forward["profitable_test_folds"] != 4
    ):
        raise ValueError("EXP-010 walk-forward fold evidence changed.")
    _assert_close(
        walk_forward["combined_test_net_profit_usd"],
        114695.0,
        "walk-forward combined net profit",
    )

    bootstrap = record["bootstrap"]
    if (
        len(bootstrap) != 2
        or any(item["resamples"] != 10000 for item in bootstrap)
        or any(item["random_seed"] != 5001 for item in bootstrap)
        or any(item["decision_gate"] is not False for item in bootstrap)
    ):
        raise ValueError("EXP-010 bootstrap evidence changed.")

    mcpt = record["mcpt"]
    if (
        mcpt["permutations"] != 1000
        or mcpt["base_seed"] != 50
        or mcpt["selected_permutations_at_least_real"] != 25
        or mcpt["fixed_reference_permutations_at_least_real"] != 0
        or mcpt["all_four_candidates_inside_every_permutation"] is not True
        or mcpt["selection_inside_every_permutation"] is not True
        or mcpt["prior_six_family_selection_corrected"] is not False
    ):
        raise ValueError("EXP-010 MCPT evidence changed.")
    _assert_close(
        mcpt["selection_aware_p_value"],
        0.025974025974025976,
        "selection-aware MCPT p-value",
    )
    _assert_close(
        mcpt["fixed_reference_p_value"],
        0.000999000999000999,
        "fixed-reference MCPT p-value",
    )

    evaluation = record["evaluation"]
    if (
        evaluation["classification"] != "STRONG_HISTORICAL_EVIDENCE"
        or evaluation["classification_is_secondary"] is not True
        or evaluation["measurement_first"] is not True
        or evaluation["profitable_walk_forward_folds"] != 4
        or evaluation["lifecycle_accept_reject_decision"] is not None
        or evaluation["paper_trading_authorized"] is not False
        or evaluation["live_trading_authorized"] is not False
        or not all(evaluation["strong_context_checks"].values())
    ):
        raise ValueError("EXP-010 evidence classification changed.")

    if (
        record["historical_status"]
        != "EXPLORATORY_DEEP_VALIDATION_BECAUSE_THE_FAMILY_AND_2019_2025_RESULTS_WERE_ALREADY_VIEWED"
        or record["independent_confirmation"] is not False
        or record["paper_trading_authorized"] is not False
        or record["live_trading_authorized"] is not False
        or record["automatic_lifecycle_source_edit"] is not False
    ):
        raise ValueError("EXP-010 research boundary changed.")

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
            raise ValueError("EXP-010 frozen result hashes changed.")


def verify_local_exp010_validation_result() -> dict[str, Any]:
    record = load_validation_result()
    validate_exp010_validation_result(record)
    return deepcopy(record)
