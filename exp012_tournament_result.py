from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from exp012_preregistration import (
    EXP012_CANDIDATES,
    validate_exp012_preregistration,
)


PROJECT_DIR = Path(__file__).resolve().parent
RESULT_DIR = (
    PROJECT_DIR / "results" / "EXP-012" / "extended_context_tournament"
)
CANDIDATE_FILE = RESULT_DIR / "candidate_measurements.csv"
FAMILY_FILE = RESULT_DIR / "family_measurements.csv"
MANIFEST_FILE = RESULT_DIR / "tournament_manifest.json"

EXPECTED_CANDIDATE_CANONICAL_SHA256 = (
    "2c406a5ef819c25d5d152be84006da2a4df3d89d7f7a0105c1ee77d40e3bf126"
)
EXPECTED_FAMILY_CANONICAL_SHA256 = (
    "0e76b7d22a00f1f9ab263eadcc0fa9a0bcacae3b4dbce604e229f554eb38cfe7"
)
EXPECTED_MANIFEST_CANONICAL_SHA256 = (
    "ba399e41d0ffe23dec33b10409a0578387255b8da4b4681a1d86f7ea60078255"
)
EXPECTED_IMPLEMENTATION_COMMIT = (
    "4a595110b11b376f7ff7e0db2255a1741808e879"
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


def _canonical_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    normalized = frame.astype(object).where(pd.notna(frame), None)
    return normalized.to_dict(orient="records")


def canonical_dataframe_sha256(frame: pd.DataFrame) -> str:
    return canonical_object_sha256(_canonical_records(frame))


def load_manifest(path: Path = MANIFEST_FILE) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("EXP-012 manifest must be a JSON object.")
    return value


def load_candidate_measurements(
    path: Path = CANDIDATE_FILE,
) -> pd.DataFrame:
    return pd.read_csv(path).sort_values(
        "candidate_id", kind="stable"
    ).reset_index(drop=True)


def load_family_measurements(
    path: Path = FAMILY_FILE,
) -> pd.DataFrame:
    return pd.read_csv(path).sort_values(
        "family_id", kind="stable"
    ).reset_index(drop=True)


def _assert_close(actual: Any, expected: float, *, label: str) -> None:
    if not np.isclose(float(actual), expected, atol=1e-12, rtol=0.0):
        raise ValueError(
            f"EXP-012 {label} changed: expected {expected}, got {actual}."
        )


def validate_exp012_tournament_result(
    *,
    manifest: dict[str, Any],
    candidates: pd.DataFrame,
    families: pd.DataFrame,
    verify_hashes: bool = True,
) -> None:
    validate_exp012_preregistration()

    if (
        manifest.get("experiment_id") != "EXP-012"
        or manifest.get("result_status")
        != "MEASURED_AWAITING_USER_REVIEW"
        or manifest.get("included_sessions") != 1331
        or manifest.get("candidate_count") != 24
        or manifest.get("family_count") != 6
        or manifest.get("maximum_later_finalists") != 3
    ):
        raise ValueError("EXP-012 manifest identity or scope changed.")

    git = manifest["git"]
    if (
        git["commit"] != EXPECTED_IMPLEMENTATION_COMMIT
        or git["short_commit"] != "4a59511"
        or git["working_tree_clean"] is not True
    ):
        raise ValueError("EXP-012 implementation provenance changed.")

    for field in (
        "automatic_winner",
        "formal_accept_reject_gates",
        "mcpt_run",
        "bootstrap_run",
        "walk_forward_run",
        "family_optimization_run",
        "overnight_entries",
        "paper_trading_authorized",
        "live_trading_authorized",
    ):
        if manifest[field] is not False:
            raise ValueError(f"EXP-012 safety field changed: {field}.")

    interpretation = manifest["preregistration_interpretation"]
    if (
        interpretation["lifecycle_result_after_measurement"] != "REVIEW"
        or interpretation["measurement_first"] is not True
        or interpretation["no_single_pass_fail_decision"] is not True
        or interpretation["no_automatic_winner"] is not True
        or interpretation["candidate_measurement_does_not_confirm_edge"]
        is not True
        or interpretation["future_deep_validation_requires_new_experiment_id"]
        is not True
        or interpretation["paper_trading_authorized"] is not False
        or interpretation["live_trading_authorized"] is not False
    ):
        raise ValueError("EXP-012 interpretation boundary changed.")

    expected_ids = {
        str(record["candidate_id"]) for record in EXP012_CANDIDATES
    }
    expected_families = {
        str(record["family_id"]) for record in EXP012_CANDIDATES
    }
    if (
        len(candidates) != 24
        or candidates["candidate_id"].nunique() != 24
        or set(candidates["candidate_id"]) != expected_ids
        or candidates["family_id"].nunique() != 6
        or set(candidates["family_id"]) != expected_families
        or len(families) != 6
        or set(families["family_id"]) != expected_families
        or any(
            int(count) != 4
            for count in candidates.groupby("family_id").size()
        )
    ):
        raise ValueError("EXP-012 complete candidate/family set changed.")

    if (
        int((candidates["net_profit_usd"] > 0).sum()) != 18
        or int((candidates["trade_profit_factor"] > 1.0).sum()) != 18
        or int((candidates["two_tick_net_profit_usd"] > 0).sum()) != 18
        or int(candidates["pareto_nondominated"].sum()) != 3
        or int((candidates["reliability_flag_count"] == 0).sum()) != 10
        or int(candidates["mnq_divergence"].sum()) != 5
    ):
        raise ValueError("EXP-012 tournament aggregate measurements changed.")

    expected_finalist_context = {
        "gap_fade_0p50_1r": {
            "completed_trades": 186,
            "trade_profit_factor": 1.530923511019599,
            "win_rate": 0.5967741935483871,
            "average_trade_usd": 187.1505376344086,
            "net_profit_usd": 34810.0,
            "maximum_drawdown_usd": -5080.0,
            "net_profit_to_drawdown": 6.852362204724409,
            "mnq_profit_factor": 1.4843807695148068,
            "two_tick_net_profit_usd": 32950.0,
            "profitable_years": 6,
            "reliability_flag_count": 0,
            "pareto_nondominated": True,
        },
        "premarket_continuation_0p50_time": {
            "completed_trades": 291,
            "trade_profit_factor": 1.7363738499377523,
            "win_rate": 0.27835051546391754,
            "average_trade_usd": 416.68384879725085,
            "net_profit_usd": 121255.0,
            "maximum_drawdown_usd": -20695.0,
            "net_profit_to_drawdown": 5.859144720947088,
            "mnq_profit_factor": 1.670737975027965,
            "two_tick_net_profit_usd": 118345.0,
            "profitable_years": 5,
            "reliability_flag_count": 0,
            "pareto_nondominated": False,
        },
        "premarket_continuation_0p75_time": {
            "completed_trades": 88,
            "trade_profit_factor": 2.0237378415933303,
            "win_rate": 0.3181818181818182,
            "average_trade_usd": 502.32954545454544,
            "net_profit_usd": 44205.0,
            "maximum_drawdown_usd": -5540.0,
            "net_profit_to_drawdown": 7.979241877256317,
            "mnq_profit_factor": 2.0982798165137613,
            "two_tick_net_profit_usd": 43325.0,
            "profitable_years": 5,
            "reliability_flag_count": 1,
            "pareto_nondominated": True,
        },
    }
    indexed = candidates.set_index("candidate_id")
    for candidate_id, expected in expected_finalist_context.items():
        row = indexed.loc[candidate_id]
        for field, value in expected.items():
            if isinstance(value, bool):
                if bool(row[field]) is not value:
                    raise ValueError(
                        f"EXP-012 {candidate_id} {field} changed."
                    )
            elif isinstance(value, int):
                if int(row[field]) != value:
                    raise ValueError(
                        f"EXP-012 {candidate_id} {field} changed."
                    )
            else:
                _assert_close(
                    row[field],
                    value,
                    label=f"{candidate_id} {field}",
                )

    family_indexed = families.set_index("family_id")
    gap_fade = family_indexed.loc["gap_fade"]
    premarket = family_indexed.loc["premarket_momentum_continuation"]
    if (
        int(gap_fade["profitable_candidate_count"]) != 4
        or int(gap_fade["nondominated_candidate_count"]) != 2
        or int(gap_fade["reliability_flags"]) != 0
        or int(premarket["profitable_candidate_count"]) != 4
        or int(premarket["nondominated_candidate_count"]) != 1
    ):
        raise ValueError("EXP-012 leading family summary changed.")
    _assert_close(
        gap_fade["median_profit_factor"],
        1.364207396189291,
        label="gap-fade median Profit Factor",
    )
    _assert_close(
        premarket["median_profit_factor"],
        1.433440596530959,
        label="premarket median Profit Factor",
    )

    if verify_hashes:
        if (
            canonical_dataframe_sha256(candidates)
            != EXPECTED_CANDIDATE_CANONICAL_SHA256
            or canonical_dataframe_sha256(families)
            != EXPECTED_FAMILY_CANONICAL_SHA256
            or canonical_object_sha256(manifest)
            != EXPECTED_MANIFEST_CANONICAL_SHA256
        ):
            raise ValueError("EXP-012 canonical result hash changed.")


def verify_local_exp012_tournament_result() -> dict[str, Any]:
    manifest = load_manifest()
    candidates = load_candidate_measurements()
    families = load_family_measurements()
    validate_exp012_tournament_result(
        manifest=manifest,
        candidates=candidates,
        families=families,
    )
    return {
        "manifest": deepcopy(manifest),
        "candidates": candidates.copy(),
        "families": families.copy(),
    }


if __name__ == "__main__":
    verify_local_exp012_tournament_result()
    print("EXP-012 extended-context result is frozen and valid.")
