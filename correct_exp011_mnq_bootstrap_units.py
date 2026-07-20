from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
from typing import Any

import numpy as np
import pandas as pd

from exp006_data import load_exp006_frozen_data
from exp009_engine import prepare_exp009_arrays
from exp011_bootstrap import paired_sizing_bootstrap
from exp011_measurements import SIGNAL_IDS
from exp011_report import build_exp011_report
from exp011_sizing import Exp011Calibration, Exp011SizedResult


PROJECT_DIR = Path(__file__).resolve().parent
RESULT_DIR = PROJECT_DIR / "results" / "EXP-011" / "position_sizing"
REPORT_DIR = PROJECT_DIR / "reports" / "EXP-011-research-lab"
RESULT_FILE = RESULT_DIR / "sizing_result.json"
BOOTSTRAP_FILE = RESULT_DIR / "paired_bootstrap.json"
MEASUREMENT_FILE = RESULT_DIR / "measurement_summary.csv"
CALIBRATION_FILE = RESULT_DIR / "calibration.json"
CORRECTION_FILE = RESULT_DIR / "mnq_bootstrap_unit_correction.json"
AUDIT_DIR = RESULT_DIR / "audit" / "original_double_scaled_bootstrap"

EXPECTED_ORIGINAL_RESULT_SHA256 = (
    "7f7b896cfa8a7f7c24b8a663ed89c22133dfe133945703b0408f785eff03fee4"
)
EXPECTED_ORIGINAL_BOOTSTRAP_SHA256 = (
    "d6f2ca65a752d902bb8150e9c66867f2f479b69a9d6807cf2d836e9063bbe7da"
)
EXPECTED_MEASUREMENT_SHA256 = (
    "9310f1dd4de6b8b5f4927910b61c0a4be7ddabd319ba93971be4c18d028d82c6"
)
EXPECTED_RESULT_IMPLEMENTATION_COMMIT = (
    "82a1503d90ee15e35cc6adac58099fad024d62c1"
)


def _raw_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return number if math.isfinite(number) else None
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    return value


def _atomic_json(payload: dict[str, Any], path: Path) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(_json_safe(payload), indent=2, allow_nan=False),
        encoding="utf-8",
    )
    temporary.replace(path)


def validate_original_double_scaled_bootstrap(
    result: dict[str, Any],
    bootstrap: dict[str, Any],
) -> None:
    if (
        result.get("schema_version") != 1
        or result.get("experiment_id") != "EXP-011"
        or result.get("result_status")
        != "MEASURED_POSITION_SIZING_STUDY"
        or result["git"]["commit"] != EXPECTED_RESULT_IMPLEMENTATION_COMMIT
        or result["calibration"]["target_dollar_risk_usd"] != 1005.0
        or len(result["results"]) != 6
    ):
        raise ValueError("Original EXP-011 result identity changed.")
    result_diagnostics = result.get("paired_bootstrap", [])
    file_diagnostics = bootstrap.get("diagnostics", [])
    if result_diagnostics != file_diagnostics or len(file_diagnostics) != 4:
        raise ValueError("Original EXP-011 bootstrap records changed.")
    for diagnostic in file_diagnostics:
        sizing_id = diagnostic["comparison_sizing_id"]
        scale = float(diagnostic["comparison_scale_to_nq"])
        if sizing_id == "integer_mnq_equal_risk" and scale != 10.0:
            raise ValueError("Original MNQ double-scale evidence changed.")
        if sizing_id == "fractional_nq_equal_risk" and scale != 1.0:
            raise ValueError("Original fractional NQ evidence changed.")


def _git_clean() -> tuple[str, bool]:
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=PROJECT_DIR,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=PROJECT_DIR,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()
    return commit, not bool(status)


def _load_calibration() -> Exp011Calibration:
    record = _load_json(CALIBRATION_FILE)
    return Exp011Calibration(
        signal_candidate_id=str(record["signal_candidate_id"]),
        market=str(record["market"]),
        calibration_start=str(record["calibration_start"]),
        calibration_end=str(record["calibration_end"]),
        trade_count=int(record["trade_count"]),
        target_dollar_risk_usd=float(
            record["target_dollar_risk_usd"]
        ),
        median_one_contract_risk_usd=float(
            record["median_one_contract_risk_usd"]
        ),
        minimum_one_contract_risk_usd=float(
            record["minimum_one_contract_risk_usd"]
        ),
        maximum_one_contract_risk_usd=float(
            record["maximum_one_contract_risk_usd"]
        ),
    )


def _load_sized_results(
    result_record: dict[str, Any],
) -> dict[tuple[str, str], Exp011SizedResult]:
    summaries = {
        (
            str(row["signal_candidate_id"]),
            str(row["sizing_id"]),
        ): row
        for row in result_record["results"]
    }
    results: dict[tuple[str, str], Exp011SizedResult] = {}
    for key, summary in summaries.items():
        signal_id, sizing_id = key
        directory = RESULT_DIR / "rows" / signal_id / sizing_id
        results[key] = Exp011SizedResult(
            signal_candidate_id=signal_id,
            sizing_id=sizing_id,
            symbol=str(summary["symbol"]),
            target_dollar_risk_usd=float(
                summary["target_dollar_risk_usd"]
            ),
            summary=summary,
            signals=pd.read_csv(directory / "signals.csv"),
            trades=pd.read_csv(directory / "trades.csv"),
            equity_curve=pd.read_csv(directory / "equity_curve.csv"),
            yearly_results=pd.read_csv(directory / "yearly_results.csv"),
            monthly_results=pd.read_csv(directory / "monthly_results.csv"),
        )
    if len(results) != 6:
        raise ValueError("EXP-011 corrected report requires all six rows.")
    return results


def _corrected_bootstrap(
    results: dict[tuple[str, str], Exp011SizedResult],
) -> list[dict[str, Any]]:
    diagnostics: list[dict[str, Any]] = []
    for signal_id in SIGNAL_IDS:
        fixed = results[(signal_id, "fixed_one_nq")]
        diagnostics.append(
            paired_sizing_bootstrap(
                fixed,
                results[(signal_id, "fractional_nq_equal_risk")],
                comparison_scale_to_nq=1.0,
            )
        )
        diagnostics.append(
            paired_sizing_bootstrap(
                fixed,
                results[(signal_id, "integer_mnq_equal_risk")],
                comparison_scale_to_nq=1.0,
            )
        )
    return diagnostics


def main() -> None:
    if CORRECTION_FILE.exists():
        raise RuntimeError(
            "EXP-011 MNQ unit correction already exists. Do not rerun it."
        )
    required = [
        RESULT_FILE,
        BOOTSTRAP_FILE,
        MEASUREMENT_FILE,
        CALIBRATION_FILE,
        REPORT_DIR / "report.html",
    ]
    missing = [path for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            "Missing EXP-011 correction inputs: "
            + ", ".join(str(path) for path in missing)
        )
    commit, clean = _git_clean()
    if not clean:
        raise RuntimeError(
            "Commit the EXP-011 unit-correction implementation first."
        )
    original_hashes = {
        "sizing_result_json": _raw_sha256(RESULT_FILE),
        "paired_bootstrap_json": _raw_sha256(BOOTSTRAP_FILE),
        "measurement_summary_csv": _raw_sha256(MEASUREMENT_FILE),
    }
    expected_hashes = {
        "sizing_result_json": EXPECTED_ORIGINAL_RESULT_SHA256,
        "paired_bootstrap_json": EXPECTED_ORIGINAL_BOOTSTRAP_SHA256,
        "measurement_summary_csv": EXPECTED_MEASUREMENT_SHA256,
    }
    if original_hashes != expected_hashes:
        raise ValueError("Original EXP-011 output hashes changed.")

    original_result = _load_json(RESULT_FILE)
    original_bootstrap = _load_json(BOOTSTRAP_FILE)
    validate_original_double_scaled_bootstrap(
        original_result, original_bootstrap
    )

    AUDIT_DIR.mkdir(parents=True, exist_ok=False)
    shutil.copy2(RESULT_FILE, AUDIT_DIR / "sizing_result.json")
    shutil.copy2(
        BOOTSTRAP_FILE, AUDIT_DIR / "paired_bootstrap.json"
    )
    shutil.copy2(
        REPORT_DIR / "report.html", AUDIT_DIR / "report.html"
    )

    results = _load_sized_results(original_result)
    corrected_bootstrap = _corrected_bootstrap(results)
    correction_context = {
        "correction_type": "MNQ_BOOTSTRAP_UNIT_DOUBLE_SCALING",
        "identified_after_initial_report": True,
        "original_mnq_scale": 10.0,
        "corrected_mnq_scale": 1.0,
        "reason": (
            "The dynamically sized MNQ ledger already applied the whole "
            "contract count and recorded actual US-dollar P&L and risk. "
            "Multiplying those completed-position dollars by ten again "
            "double-counted the NQ/MNQ multiplier difference."
        ),
        "strategy_calculation_rerun": False,
        "calibration_rerun": False,
        "sizing_measurement_rerun": False,
        "bootstrap_recomputed_from_frozen_session_ledgers": True,
        "measurement_summary_unchanged": True,
        "decision_gate": False,
    }
    corrected_result = deepcopy(original_result)
    corrected_result["paired_bootstrap"] = corrected_bootstrap
    corrected_result["unit_correction"] = correction_context
    corrected_bootstrap_file = {
        "diagnostics": corrected_bootstrap,
        "unit_correction": correction_context,
    }

    frozen = load_exp006_frozen_data()
    nq_arrays = prepare_exp009_arrays(frozen.nq_1m)
    measurement_table = pd.read_csv(MEASUREMENT_FILE)
    calibration = _load_calibration()
    build_exp011_report(
        decision=corrected_result,
        calibration=calibration,
        results=results,
        measurement_table=measurement_table,
        bootstrap=corrected_bootstrap,
        nq_arrays=nq_arrays,
        output_dir=REPORT_DIR,
    )
    _atomic_json(corrected_bootstrap_file, BOOTSTRAP_FILE)
    _atomic_json(corrected_result, RESULT_FILE)

    corrected_hashes = {
        "sizing_result_json": _raw_sha256(RESULT_FILE),
        "paired_bootstrap_json": _raw_sha256(BOOTSTRAP_FILE),
        "measurement_summary_csv": _raw_sha256(MEASUREMENT_FILE),
        "report_html": _raw_sha256(REPORT_DIR / "report.html"),
    }
    record = {
        "schema_version": 1,
        "experiment_id": "EXP-011",
        "correction_status": "CORRECTED_AND_AUDITED",
        "corrected_at_utc": datetime.now(timezone.utc).isoformat(),
        "correction_implementation_commit": commit,
        "original_result_implementation_commit": (
            EXPECTED_RESULT_IMPLEMENTATION_COMMIT
        ),
        "original_hashes": original_hashes,
        "corrected_hashes": corrected_hashes,
        "audit_directory": str(AUDIT_DIR.relative_to(PROJECT_DIR)),
        "context": correction_context,
        "paper_trading_authorized": False,
        "live_trading_authorized": False,
    }
    _atomic_json(record, CORRECTION_FILE)

    print()
    print("EXP-011 MNQ bootstrap unit correction completed.")
    print("Original double-scaled output preserved in the audit directory.")
    print("All six strategy and sizing measurements remained unchanged.")
    print("Only paired bootstrap diagnostics and report context changed.")
    print("Corrected MNQ comparison scale: 1.0 actual US dollars.")
    print("No strategy, calibration or sizing measurement was rerun.")
    print(f"Correction record: {CORRECTION_FILE}")


if __name__ == "__main__":
    main()
