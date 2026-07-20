from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from exp010_validation_result import (
    canonical_dataframe_sha256,
    canonical_object_sha256,
)
from exp011_preregistration import validate_exp011_preregistration


PROJECT_DIR = Path(__file__).resolve().parent
RESULT_DIR = PROJECT_DIR / "results" / "EXP-011" / "position_sizing"
RESULT_FILE = RESULT_DIR / "sizing_result.json"
CORRECTION_FILE = RESULT_DIR / "mnq_bootstrap_unit_correction.json"
EXPECTED_MANIFEST_SHA256 = (
    "36ba1dcd8d8cfc12095df3eb011970e9e6b0f5582b19a5f9b6a2899df99a023b"
)
EXPECTED_IMPLEMENTATION_COMMIT = (
    "82a1503d90ee15e35cc6adac58099fad024d62c1"
)
EXPECTED_CORRECTION_COMMIT = (
    "421bf36535dbeda8b1ce66dc3bc5889b47fdac10"
)


EXPECTED_MEASUREMENTS: dict[tuple[str, str], dict[str, float | int]] = {
    ("opening_drive_0p5_time", "fixed_one_nq"): {
        "completed_trades": 594,
        "skipped_zero_size_trades": 0,
        "net_profit_usd": 197970.0,
        "trade_profit_factor": 1.3870002932264687,
        "win_rate": 0.4983164983164983,
        "maximum_drawdown_usd": -25280.0,
        "average_initial_risk_usd": 2156.9949494949497,
        "initial_risk_coefficient_of_variation": 0.5147799295752222,
    },
    ("opening_drive_0p5_time", "fractional_nq_equal_risk"): {
        "completed_trades": 594,
        "skipped_zero_size_trades": 0,
        "net_profit_usd": 95871.09573111619,
        "trade_profit_factor": 1.372143691861657,
        "win_rate": 0.4983164983164983,
        "maximum_drawdown_usd": -9715.635393039913,
        "average_initial_risk_usd": 1004.5622895622896,
        "initial_risk_coefficient_of_variation": 0.009642698016466719,
    },
    ("opening_drive_0p5_time", "integer_mnq_equal_risk"): {
        "completed_trades": 596,
        "skipped_zero_size_trades": 1,
        "net_profit_usd": 80339.5,
        "trade_profit_factor": 1.34432370229572,
        "win_rate": 0.4966442953020134,
        "maximum_drawdown_usd": -9162.5,
        "average_initial_risk_usd": 899.5813758389262,
        "initial_risk_coefficient_of_variation": 0.09019547366758074,
    },
    ("opening_drive_0p5_1p5r", "fixed_one_nq"): {
        "completed_trades": 594,
        "skipped_zero_size_trades": 0,
        "net_profit_usd": 177245.0,
        "trade_profit_factor": 1.355724363541489,
        "win_rate": 0.5218855218855218,
        "maximum_drawdown_usd": -24930.0,
        "average_initial_risk_usd": 2156.9949494949497,
        "initial_risk_coefficient_of_variation": 0.5147799295752222,
    },
    ("opening_drive_0p5_1p5r", "fractional_nq_equal_risk"): {
        "completed_trades": 594,
        "skipped_zero_size_trades": 0,
        "net_profit_usd": 79260.50125726298,
        "trade_profit_factor": 1.3194934337301982,
        "win_rate": 0.5218855218855218,
        "maximum_drawdown_usd": -9715.635393039913,
        "average_initial_risk_usd": 1004.5622895622896,
        "initial_risk_coefficient_of_variation": 0.009642698016466719,
    },
    ("opening_drive_0p5_1p5r", "integer_mnq_equal_risk"): {
        "completed_trades": 596,
        "skipped_zero_size_trades": 1,
        "net_profit_usd": 67727.5,
        "trade_profit_factor": 1.3020171638413292,
        "win_rate": 0.5218120805369127,
        "maximum_drawdown_usd": -9162.5,
        "average_initial_risk_usd": 899.5813758389262,
        "initial_risk_coefficient_of_variation": 0.09019547366758074,
    },
}


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def load_exp011_sizing_result(
    path: Path = RESULT_FILE,
) -> dict[str, Any]:
    return _load_json(path)


def build_exp011_result_manifest(
    result_dir: Path = RESULT_DIR,
) -> dict[str, str]:
    manifest: dict[str, str] = {}
    for path in sorted(result_dir.rglob("*")):
        if not path.is_file() or "audit" in path.parts:
            continue
        relative = path.relative_to(result_dir).as_posix()
        if path.suffix == ".json":
            manifest[relative] = canonical_object_sha256(
                _load_json(path)
            )
        elif path.suffix == ".csv":
            manifest[relative] = canonical_dataframe_sha256(
                pd.read_csv(path)
            )
    return manifest


def _assert_close(actual: Any, expected: float, label: str) -> None:
    if not np.isclose(float(actual), expected, atol=1e-10, rtol=0.0):
        raise ValueError(
            f"EXP-011 {label} changed: expected {expected}, got {actual}."
        )


def validate_exp011_sizing_result(
    record: dict[str, Any],
    *,
    verify_hashes: bool = False,
) -> None:
    validate_exp011_preregistration()
    if (
        record.get("schema_version") != 1
        or record.get("experiment_id") != "EXP-011"
        or record.get("result_status")
        != "MEASURED_POSITION_SIZING_STUDY"
        or record["git"]["commit"] != EXPECTED_IMPLEMENTATION_COMMIT
        or record["git"]["working_tree_clean"] is not True
    ):
        raise ValueError("EXP-011 result identity or provenance changed.")
    data = record["data"]
    if (
        data["included_sessions"] != 1639
        or data["calibration_period"]
        != "2019-05-06 through 2020-12-31"
        or data["evaluation_period"]
        != "2021-01-04 through 2025-12-31"
        or data["new_data_cleaning_decisions"] != 0
    ):
        raise ValueError("EXP-011 frozen data context changed.")
    calibration = record["calibration"]
    if (
        calibration["signal_candidate_id"]
        != "opening_drive_0p5_time"
        or calibration["market"] != "NQ"
        or calibration["trade_count"] != 181
    ):
        raise ValueError("EXP-011 calibration identity changed.")
    _assert_close(
        calibration["target_dollar_risk_usd"],
        1005.0,
        "target dollar risk",
    )

    rows = {
        (row["signal_candidate_id"], row["sizing_id"]): row
        for row in record["results"]
    }
    if set(rows) != set(EXPECTED_MEASUREMENTS):
        raise ValueError("EXP-011 six-row measurement identity changed.")
    for key, expected in EXPECTED_MEASUREMENTS.items():
        row = rows[key]
        if (
            row["automatic_winner"] is not False
            or row["pass_fail_gate"] is not False
            or row["pass_fail_decision"] != "NOT_APPLICABLE"
        ):
            raise ValueError(f"EXP-011 decision boundary changed for {key}.")
        for field, expected_value in expected.items():
            if isinstance(expected_value, int):
                if int(row[field]) != expected_value:
                    raise ValueError(
                        f"EXP-011 {key} {field} changed."
                    )
            else:
                _assert_close(
                    row[field],
                    expected_value,
                    f"{key} {field}",
                )

    diagnostics = record["paired_bootstrap"]
    if len(diagnostics) != 4:
        raise ValueError("EXP-011 paired bootstrap count changed.")
    for diagnostic in diagnostics:
        if (
            diagnostic["comparison_scale_to_nq"] != 1.0
            or diagnostic["resamples"] != 10000
            or diagnostic["random_seed"] != 5111
            or diagnostic["paired_by_session"] is not True
            or diagnostic["decision_gate"] is not False
            or diagnostic["signal_edge_confirmation"] is not False
        ):
            raise ValueError(
                "EXP-011 corrected paired bootstrap changed."
            )
    correction = record["unit_correction"]
    if (
        correction["correction_type"]
        != "MNQ_BOOTSTRAP_UNIT_DOUBLE_SCALING"
        or correction["original_mnq_scale"] != 10.0
        or correction["corrected_mnq_scale"] != 1.0
        or correction["strategy_calculation_rerun"] is not False
        or correction["calibration_rerun"] is not False
        or correction["sizing_measurement_rerun"] is not False
        or correction["measurement_summary_unchanged"] is not True
    ):
        raise ValueError("EXP-011 unit-correction audit changed.")
    interpretation = record["research_interpretation"]
    if (
        interpretation["automatic_sizing_winner"] is not False
        or interpretation["pass_fail_gate"] is not False
        or interpretation["new_signal_edge_test"] is not False
        or interpretation["new_mcpt"] is not False
        or interpretation["independent_confirmation"] is not False
        or record["paper_trading_authorized"] is not False
        or record["live_trading_authorized"] is not False
    ):
        raise ValueError("EXP-011 research boundary changed.")

    correction_record = _load_json(CORRECTION_FILE)
    if (
        correction_record["correction_status"]
        != "CORRECTED_AND_AUDITED"
        or correction_record["correction_implementation_commit"]
        != EXPECTED_CORRECTION_COMMIT
        or correction_record["context"][
            "measurement_summary_unchanged"
        ]
        is not True
    ):
        raise ValueError("EXP-011 correction record changed.")

    if verify_hashes:
        manifest = build_exp011_result_manifest()
        digest = canonical_object_sha256(manifest)
        if digest != EXPECTED_MANIFEST_SHA256:
            raise ValueError(
                "Local EXP-011 result manifest does not match the "
                "frozen corrected result."
            )


def verify_local_exp011_sizing_result() -> None:
    validate_exp011_sizing_result(
        load_exp011_sizing_result(),
        verify_hashes=True,
    )


def get_expected_exp011_measurements() -> dict[
    tuple[str, str], dict[str, float | int]
]:
    return deepcopy(EXPECTED_MEASUREMENTS)


if __name__ == "__main__":
    verify_local_exp011_sizing_result()
    print("Local EXP-011 corrected sizing result is frozen and valid.")
