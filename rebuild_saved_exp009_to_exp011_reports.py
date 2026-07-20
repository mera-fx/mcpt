from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from correct_exp011_mnq_bootstrap_units import (
    _load_calibration,
    _load_sized_results,
)
from exp006_data import load_exp006_frozen_data
from exp009_engine import (
    Exp009Result,
    get_exp009_candidate,
    prepare_exp009_arrays,
)
from exp009_report import build_exp009_report
from exp009_tournament_result import (
    RESULT_DIR as EXP009_RESULT_DIR,
    verify_local_exp009_tournament_result,
)
from exp010_report import build_exp010_report
from exp010_validation_result import (
    RESULT_DIR as EXP010_RESULT_DIR,
    load_bootstrap as load_exp010_bootstrap,
    load_candidate_measurements as load_exp010_candidates,
    load_cost_sensitivity as load_exp010_costs,
    load_mcpt as load_exp010_mcpt,
    load_walk_forward as load_exp010_walk_forward,
    verify_local_exp010_validation_result,
)
from exp011_report import build_exp011_report
from exp011_sizing_result import (
    RESULT_DIR as EXP011_RESULT_DIR,
    load_exp011_sizing_result,
    verify_local_exp011_sizing_result,
)


PROJECT_DIR = Path(__file__).resolve().parent
REPORT_ROOT = PROJECT_DIR / "reports"


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def _load_nq_result(
    *,
    result_root: Path,
    candidate_id: str,
    summary: dict[str, Any],
) -> Exp009Result:
    directory = result_root / "candidates" / candidate_id
    required = (
        directory / "nq_trades.csv",
        directory / "nq_equity_curve.csv",
        directory / "nq_yearly_results.csv",
    )
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            "Missing saved report inputs: " + ", ".join(missing)
        )
    return Exp009Result(
        candidate=get_exp009_candidate(candidate_id),
        symbol="NQ",
        summary=summary,
        trades=pd.read_csv(required[0]),
        equity_curve=pd.read_csv(required[1]),
        yearly_results=pd.read_csv(required[2]),
    )


def _rebuild_exp009(nq_arrays: Any) -> Path:
    frozen = verify_local_exp009_tournament_result()
    candidates = frozen["candidates"]
    results = {
        str(row["candidate_id"]): _load_nq_result(
            result_root=EXP009_RESULT_DIR,
            candidate_id=str(row["candidate_id"]),
            summary=dict(row),
        )
        for row in candidates.to_dict(orient="records")
    }
    return build_exp009_report(
        candidate_table=candidates,
        nq_results=results,
        arrays=nq_arrays,
        report_dir=REPORT_ROOT / "EXP-009-research-lab",
        metadata=frozen["manifest"],
    )


def _rebuild_exp010(nq_arrays: Any) -> Path:
    decision = verify_local_exp010_validation_result()
    candidates = load_exp010_candidates()
    results = {
        str(row["candidate_id"]): _load_nq_result(
            result_root=EXP010_RESULT_DIR,
            candidate_id=str(row["candidate_id"]),
            summary=dict(row),
        )
        for row in candidates.to_dict(orient="records")
    }
    return build_exp010_report(
        decision=decision,
        candidate_table=candidates,
        nq_results=results,
        nq_arrays=nq_arrays,
        walk_forward=load_exp010_walk_forward(),
        cost_sensitivity=load_exp010_costs(),
        mcpt=load_exp010_mcpt(),
        bootstrap=load_exp010_bootstrap()["diagnostics"],
        output_dir=REPORT_ROOT / "EXP-010-research-lab",
    )


def _rebuild_exp011(nq_arrays: Any) -> Path:
    verify_local_exp011_sizing_result()
    decision = load_exp011_sizing_result()
    bootstrap = _load_json(
        EXP011_RESULT_DIR / "paired_bootstrap.json"
    )["diagnostics"]
    return build_exp011_report(
        decision=decision,
        calibration=_load_calibration(),
        results=_load_sized_results(decision),
        measurement_table=pd.read_csv(
            EXP011_RESULT_DIR / "measurement_summary.csv"
        ),
        bootstrap=bootstrap,
        nq_arrays=nq_arrays,
        output_dir=REPORT_ROOT / "EXP-011-research-lab",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Rebuild EXP-009 through EXP-011 reports from frozen saved "
            "measurements without running a strategy or statistical test."
        )
    )
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()

    verify_local_exp009_tournament_result()
    verify_local_exp010_validation_result()
    verify_local_exp011_sizing_result()
    if args.preflight:
        print("Saved EXP-009, EXP-010 and EXP-011 inputs are frozen and valid.")
        print("Preflight passed. No report file was written.")
        return

    frozen = load_exp006_frozen_data()
    nq_arrays = prepare_exp009_arrays(frozen.nq_1m)
    paths = (
        _rebuild_exp009(nq_arrays),
        _rebuild_exp010(nq_arrays),
        _rebuild_exp011(nq_arrays),
    )
    print("Rebuilt saved reports with opaque white chart canvases:")
    for path in paths:
        print(path)
    print("No strategy, optimization, MCPT or bootstrap was rerun.")


if __name__ == "__main__":
    main()
