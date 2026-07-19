from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from exp009_preregistration import (
    EXP009_CANDIDATES,
    validate_exp009_preregistration,
)


PROJECT_DIR = Path(__file__).resolve().parent
RESULT_DIR = (
    PROJECT_DIR / "results" / "EXP-009" / "discovery_tournament"
)
CANDIDATE_FILE = RESULT_DIR / "candidate_measurements.csv"
FAMILY_FILE = RESULT_DIR / "family_measurements.csv"
MANIFEST_FILE = RESULT_DIR / "tournament_manifest.json"

EXPECTED_CANDIDATE_CANONICAL_SHA256 = (
    "dc1e81c62536ffc03b2ca66772c409d3582a5c2e28b4e68ffa31d7345f3566b0"
)
EXPECTED_FAMILY_CANONICAL_SHA256 = (
    "fc471c64f24d9344a0d04d29c87108884adf358515e14f7b72b4fef12c24577d"
)
EXPECTED_MANIFEST_CANONICAL_SHA256 = (
    "1ea51cd118c0b037bdda8943d6b1385385858faabdaf4c94ab10a3acbf03f6fb"
)
EXPECTED_IMPLEMENTATION_COMMIT = (
    "254d6d038d1b75dcadeee5cd264184864902875c"
)


def _json_default(value: Any) -> Any:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.bool_,)):
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


def load_manifest(path: Path = MANIFEST_FILE) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("EXP-009 manifest must be a JSON object.")
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


def canonical_dataframe_sha256(frame: pd.DataFrame) -> str:
    return canonical_object_sha256(frame.to_dict(orient="records"))


def _assert_close(
    actual: Any,
    expected: float,
    *,
    label: str,
) -> None:
    if not np.isclose(float(actual), expected, atol=1e-12, rtol=0.0):
        raise ValueError(
            f"EXP-009 {label} changed: expected {expected}, got {actual}."
        )


def validate_exp009_tournament_result(
    *,
    manifest: dict[str, Any],
    candidates: pd.DataFrame,
    families: pd.DataFrame,
    verify_hashes: bool = True,
) -> None:
    validate_exp009_preregistration()

    if (
        manifest.get("experiment_id") != "EXP-009"
        or manifest.get("result_status")
        != "MEASURED_AWAITING_USER_REVIEW"
        or manifest.get("included_sessions") != 1639
        or manifest.get("candidate_count") != 24
        or manifest.get("family_count") != 6
        or manifest.get("maximum_later_finalists") != 3
    ):
        raise ValueError("EXP-009 manifest identity or scope changed.")

    git = manifest["git"]
    if (
        git["commit"] != EXPECTED_IMPLEMENTATION_COMMIT
        or git["short_commit"] != "254d6d0"
        or git["working_tree_clean"] is not True
    ):
        raise ValueError("EXP-009 implementation provenance changed.")

    for field in (
        "automatic_winner",
        "formal_accept_reject_gates",
        "mcpt_run",
        "bootstrap_run",
        "family_optimization_run",
        "paper_trading_authorized",
        "live_trading_authorized",
    ):
        if manifest[field] is not False:
            raise ValueError(f"EXP-009 safety field changed: {field}.")

    interpretation = manifest["preregistration_interpretation"]
    if (
        interpretation["lifecycle_result_after_measurement"] != "REVIEW"
        or interpretation["no_single_pass_fail_decision"] is not True
        or interpretation["no_automatic_winner"] is not True
        or interpretation["candidate_measurement_does_not_confirm_edge"]
        is not True
        or interpretation["live_trading_authorized"] is not False
        or interpretation["paper_testing_authorized"] is not False
    ):
        raise ValueError("EXP-009 interpretation boundary changed.")

    expected_ids = {
        str(record["candidate_id"]) for record in EXP009_CANDIDATES
    }
    expected_families = {
        str(record["family_id"]) for record in EXP009_CANDIDATES
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
        raise ValueError("EXP-009 complete candidate/family set changed.")

    if (
        int((candidates["net_profit_usd"] > 0).sum()) != 12
        or int((candidates["trade_profit_factor"] > 1.0).sum()) != 12
        or int((candidates["two_tick_net_profit_usd"] > 0).sum()) != 10
        or int(candidates["pareto_nondominated"].sum()) != 5
        or int((candidates["reliability_flag_count"] == 0).sum()) != 9
    ):
        raise ValueError("EXP-009 tournament aggregate measurements changed.")

    expected_opening_drive = {
        "opening_drive_0p5_time": {
            "completed_trades": 775,
            "trade_profit_factor": 1.3500728278480598,
            "win_rate": 0.49290322580645163,
            "net_profit_usd": 213905.0,
            "maximum_drawdown_usd": -25280.0,
            "two_tick_net_profit_usd": 206155.0,
            "mnq_profit_factor": 1.3321549899867842,
            "profitable_year_fraction": 6 / 7,
        },
        "opening_drive_0p5_1p5r": {
            "completed_trades": 775,
            "trade_profit_factor": 1.3158469945355191,
            "win_rate": 0.52,
            "net_profit_usd": 187850.0,
            "maximum_drawdown_usd": -24930.0,
            "two_tick_net_profit_usd": 180100.0,
            "mnq_profit_factor": 1.3100124248463572,
            "profitable_year_fraction": 1.0,
        },
        "opening_drive_0p75_time": {
            "completed_trades": 312,
            "trade_profit_factor": 1.3004864782042442,
            "win_rate": 0.5096153846153846,
            "net_profit_usd": 78445.0,
            "maximum_drawdown_usd": -19050.0,
            "two_tick_net_profit_usd": 75325.0,
            "mnq_profit_factor": 1.2918533007334962,
            "profitable_year_fraction": 6 / 7,
        },
        "opening_drive_0p75_1p5r": {
            "completed_trades": 312,
            "trade_profit_factor": 1.2422740186699137,
            "win_rate": 0.5160256410256411,
            "net_profit_usd": 62677.5,
            "maximum_drawdown_usd": -14975.0,
            "two_tick_net_profit_usd": 59557.5,
            "mnq_profit_factor": 1.2491904592662797,
            "profitable_year_fraction": 5 / 7,
        },
    }
    indexed = candidates.set_index("candidate_id")
    for candidate_id, expected in expected_opening_drive.items():
        row = indexed.loc[candidate_id]
        if (
            str(row["family_id"]) != "opening_drive_continuation"
            or bool(row["pareto_nondominated"]) is not True
            or int(row["reliability_flag_count"]) != 0
        ):
            raise ValueError(
                f"EXP-009 opening-drive context changed: {candidate_id}."
            )
        for field, value in expected.items():
            if field == "completed_trades":
                if int(row[field]) != value:
                    raise ValueError(
                        f"EXP-009 {candidate_id} trade count changed."
                    )
            else:
                _assert_close(
                    row[field],
                    value,
                    label=f"{candidate_id} {field}",
                )

    opening_family = families.set_index("family_id").loc[
        "opening_drive_continuation"
    ]
    if (
        int(opening_family["candidate_count"]) != 4
        or int(opening_family["profitable_candidate_count"]) != 4
        or int(opening_family["nondominated_candidate_count"]) != 4
        or int(opening_family["reliability_flags"]) != 0
    ):
        raise ValueError("EXP-009 opening-drive family summary changed.")
    _assert_close(
        opening_family["median_profit_factor"],
        1.3081667363698817,
        label="opening-drive median Profit Factor",
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
            raise ValueError("EXP-009 canonical result hash changed.")


def verify_local_exp009_tournament_result() -> dict[str, Any]:
    manifest = load_manifest()
    candidates = load_candidate_measurements()
    families = load_family_measurements()
    validate_exp009_tournament_result(
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
    verify_local_exp009_tournament_result()
    print("EXP-009 discovery result is frozen and valid.")
