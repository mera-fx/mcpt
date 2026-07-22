from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Any, Callable

import pandas as pd


@dataclass(frozen=True)
class StrategyAdapterResult:
    metrics: dict[str, Any]
    context: dict[str, Any]
    source: str
    adapter_id: str


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def _nested(payload: dict[str, Any], *keys: str) -> Any:
    current: Any = payload
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def _first(payload: dict[str, Any], *paths: tuple[str, ...]) -> Any:
    for path in paths:
        value = _nested(payload, *path)
        if value is not None:
            return value
    return None


def _finite(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return number if math.isfinite(number) else float("nan")


def _clean(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, str)):
        return value
    number = _finite(value)
    return None if math.isnan(number) else number


def _win_rate_percent(row: dict[str, Any]) -> float:
    value = _finite(
        row.get(
            "win_rate_percent",
            row.get("win_rate"),
        )
    )
    if math.isnan(value):
        return value
    return value * 100.0 if abs(value) <= 1.0 else value


def _drawdown_percent(row: dict[str, Any]) -> float:
    value = _finite(
        row.get(
            "maximum_drawdown_percent",
            row.get("max_drawdown_percent"),
        )
    )
    if math.isnan(value):
        return value
    if abs(value) <= 1.0:
        return -abs(value) * 100.0
    return -abs(value)


def _standard_metrics(
    row: dict[str, Any],
    *,
    metric_source: str,
    metric_scope: str,
    headline_name: str,
    mcpt_p_value: Any = None,
    result_decision: str = "",
    adapter_id: str,
) -> dict[str, Any]:
    total_return = _finite(
        row.get(
            "total_return_percent",
            row.get("strategy_return_percent"),
        )
    )
    return {
        "metric_source": metric_source,
        "metric_scope": metric_scope,
        "headline_name": headline_name,
        "adapter_id": adapter_id,
        "primary_symbol": str(row.get("symbol", "NQ") or "NQ"),
        "profit_factor": _finite(
            row.get(
                "trade_profit_factor",
                row.get("profit_factor"),
            )
        ),
        "net_profit_usd": _finite(
            row.get(
                "net_profit_usd",
                row.get("net_profit"),
            )
        ),
        "win_rate_percent": _win_rate_percent(row),
        "max_drawdown_usd": _finite(
            row.get(
                "maximum_drawdown_usd",
                row.get("max_drawdown_usd"),
            )
        ),
        "max_drawdown_percent": _drawdown_percent(row),
        "total_return_percent": total_return,
        "total_trades": _finite(
            row.get(
                "completed_trades",
                row.get("total_trades"),
            )
        ),
        "mcpt_p_value": _finite(mcpt_p_value),
        "average_trade_usd": _finite(row.get("average_trade_usd")),
        "net_profit_to_drawdown": _finite(
            row.get(
                "net_profit_to_drawdown",
                row.get("net_profit_to_maximum_drawdown"),
            )
        ),
        "result_decision": result_decision,
    }


def _summary(label: str, value: Any) -> dict[str, str]:
    if value is None:
        text = "—"
    elif isinstance(value, bool):
        text = "Yes" if value else "No"
    elif isinstance(value, float) and math.isnan(value):
        text = "—"
    elif isinstance(value, (list, tuple)):
        text = ", ".join(str(item) for item in value) if value else "None"
    else:
        text = str(value)
    return {"label": label, "value": text}


def _comparison_row(
    row: dict[str, Any],
    *,
    name: str,
    role: str = "",
    note: str = "",
) -> dict[str, Any]:
    return {
        "name": name,
        "role": role,
        "family": str(row.get("family_id", "") or ""),
        "completed_trades": _clean(
            row.get(
                "completed_trades",
                row.get("total_trades"),
            )
        ),
        "profit_factor": _clean(
            row.get(
                "trade_profit_factor",
                row.get("profit_factor"),
            )
        ),
        "win_rate_percent": _clean(_win_rate_percent(row)),
        "average_trade_usd": _clean(row.get("average_trade_usd")),
        "net_profit_usd": _clean(row.get("net_profit_usd")),
        "maximum_drawdown_usd": _clean(
            row.get(
                "maximum_drawdown_usd",
                row.get("max_drawdown_usd"),
            )
        ),
        "net_profit_to_drawdown": _clean(
            row.get(
                "net_profit_to_drawdown",
                row.get("net_profit_to_maximum_drawdown"),
            )
        ),
        "profitable_years": _clean(row.get("profitable_years")),
        "trading_years": _clean(row.get("trading_years")),
        "two_tick_net_profit_usd": _clean(
            row.get("two_tick_net_profit_usd")
        ),
        "selected": bool(row.get("selected", False)),
        "note": note,
    }


def _frame_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return [
        {
            str(key): value
            for key, value in record.items()
        }
        for record in frame.to_dict(orient="records")
    ]


def _exp004(project_dir: Path) -> StrategyAdapterResult | None:
    path = (
        project_dir
        / "results"
        / "EXP-004"
        / "quick_screen"
        / "quick_screen_decision.json"
    )
    payload = _read_json(path)
    if not payload:
        return None

    fixed = dict(payload.get("fixed_in_sample_summary", {}))
    best = dict(payload.get("best_in_sample_summary", {}))
    fixed_parameters = dict(payload.get("fixed_parameters", {}))
    best_parameters = dict(payload.get("best_parameters", {}))

    if "net_profit_usd" not in fixed:
        fixed["net_profit_usd"] = (
            _finite(fixed.get("ending_equity"))
            - _finite(fixed.get("starting_capital"))
        )
    if "net_profit_usd" not in best:
        best["net_profit_usd"] = (
            _finite(best.get("ending_equity"))
            - _finite(best.get("starting_capital"))
        )

    fixed_name = (
        f"{fixed_parameters.get('opening_range_minutes', '—')}-minute "
        f"{fixed_parameters.get('direction_mode', '—')}"
    )
    best_name = (
        f"{best_parameters.get('opening_range_minutes', '—')}-minute "
        f"{best_parameters.get('direction_mode', '—')}"
    )
    adapter_id = "exp004_quick_screen_v1"
    metrics = _standard_metrics(
        fixed,
        metric_source=path.relative_to(project_dir).as_posix(),
        metric_scope=(
            "Fixed preregistered in-sample candidate; the best grid row is "
            "shown separately and is not substituted for the fixed rules."
        ),
        headline_name=fixed_name,
        mcpt_p_value=payload.get("quick_mcpt_p_value"),
        result_decision=str(payload.get("decision", "")),
        adapter_id=adapter_id,
    )

    context = {
        "adapter_type": "quick_screen",
        "adapter_id": adapter_id,
        "comparison_title": "Fixed rules versus descriptive in-sample grid leader",
        "comparison_note": (
            "Both rows are in-sample. The protected decision used the locked "
            "gates and did not authorize OOS disclosure."
        ),
        "summary_rows": [
            _summary("Protected decision", payload.get("decision")),
            _summary("Failed gates", payload.get("failed_gates", [])),
            _summary("OOS disclosure", payload.get("out_of_sample_disclosure")),
            _summary(
                "Grid combinations with PF ≥ 1",
                payload.get("parameter_combinations_pf_ge_1"),
            ),
            _summary("Quick MCPT permutations", payload.get("quick_mcpt_permutations")),
            _summary("Quick MCPT p-value", payload.get("quick_mcpt_p_value")),
        ],
        "comparison_rows": [
            _comparison_row(
                fixed,
                name=fixed_name,
                role="Fixed preregistered rules",
            ),
            _comparison_row(
                best,
                name=best_name,
                role="Best in-sample grid row",
                note="Descriptive only",
            ),
        ],
        "source_files": [path.relative_to(project_dir).as_posix()],
    }
    return StrategyAdapterResult(metrics, context, context["source_files"][0], adapter_id)


def _exp006(project_dir: Path) -> StrategyAdapterResult | None:
    path = (
        project_dir
        / "results"
        / "strategy_measurements"
        / "EXP-006"
        / "measurement_summary.json"
    )
    payload = _read_json(path)
    if not payload:
        return None

    adapter_id = "exp006_measurement_summary_v1"
    metrics = _standard_metrics(
        payload,
        metric_source=path.relative_to(project_dir).as_posix(),
        metric_scope=(
            "Selected structured-optimization candidate measured on the saved "
            "full period. The formal decision remains the locked gate result."
        ),
        headline_name=str(payload.get("parameters", "Selected EXP-006 candidate")),
        mcpt_p_value=payload.get("mcpt_p_value"),
        result_decision=str(payload.get("formal_decision", "")),
        adapter_id=adapter_id,
    )

    context = {
        "adapter_type": "structured_optimization",
        "adapter_id": adapter_id,
        "comparison_title": "",
        "comparison_note": "",
        "summary_rows": [
            _summary("Formal decision", payload.get("formal_decision")),
            _summary("Failed gates", payload.get("failed_gates")),
            _summary(
                "Walk-forward profitable folds",
                (
                    f"{payload.get('walk_forward_profitable_folds', '—')}/"
                    f"{payload.get('walk_forward_fold_count', '—')}"
                ),
            ),
            _summary(
                "Walk-forward net profit",
                payload.get("walk_forward_net_profit_usd"),
            ),
            _summary("MNQ Profit Factor", payload.get("mnq_profit_factor")),
            _summary("Two-tick NQ net profit", payload.get("two_tick_nq_net_profit_usd")),
            _summary("NQ benchmark return %", payload.get("benchmark_return_percent")),
            _summary("Excess return %", payload.get("excess_return_percent")),
        ],
        "comparison_rows": [],
        "source_files": [path.relative_to(project_dir).as_posix()],
    }
    return StrategyAdapterResult(metrics, context, context["source_files"][0], adapter_id)


def _tournament_adapter(
    project_dir: Path,
    *,
    experiment_id: str,
    folder_name: str,
    manifest_name: str,
    adapter_id: str,
) -> StrategyAdapterResult | None:
    root = project_dir / "results" / experiment_id / folder_name
    measurements_path = root / "candidate_measurements.csv"
    manifest_path = root / manifest_name
    frame = _read_csv(measurements_path)
    manifest = _read_json(manifest_path)
    if frame.empty:
        return None

    frame = frame.copy()
    frame["net_profit_usd"] = pd.to_numeric(
        frame["net_profit_usd"],
        errors="coerce",
    )
    ranked = frame.sort_values(
        ["net_profit_usd", "trade_profit_factor"],
        ascending=[False, False],
    )
    headline = ranked.iloc[0].to_dict()
    headline_name = str(headline.get("candidate_id", "Measured candidate"))
    metric_scope = (
        "Highest measured NQ net profit among the saved tournament rows. "
        "This is a descriptive dashboard headline, not an automatic winner "
        "or edge confirmation."
    )
    metrics = _standard_metrics(
        headline,
        metric_source=measurements_path.relative_to(project_dir).as_posix(),
        metric_scope=metric_scope,
        headline_name=headline_name,
        mcpt_p_value=None,
        result_decision=str(
            manifest.get(
                "result_status",
                "MEASURED_AWAITING_USER_REVIEW",
            )
        ),
        adapter_id=adapter_id,
    )

    profitable = int((pd.to_numeric(frame["net_profit_usd"], errors="coerce") > 0).sum())
    two_tick = (
        int(
            (
                pd.to_numeric(
                    frame["two_tick_net_profit_usd"],
                    errors="coerce",
                )
                > 0
            ).sum()
        )
        if "two_tick_net_profit_usd" in frame
        else None
    )
    pareto = (
        int(frame["pareto_nondominated"].fillna(False).astype(bool).sum())
        if "pareto_nondominated" in frame
        else None
    )
    family_count = int(frame["family_id"].nunique()) if "family_id" in frame else None

    comparison_rows = [
        _comparison_row(
            row,
            name=str(row.get("candidate_id", "")),
            role=(
                "Descriptive net-profit leader"
                if index == 0
                else "Measured candidate"
            ),
        )
        for index, row in enumerate(_frame_records(ranked.head(6)))
    ]

    context = {
        "adapter_type": "discovery_tournament",
        "adapter_id": adapter_id,
        "comparison_title": "Top six measured candidates by NQ net profit",
        "comparison_note": (
            "The ordering is a dashboard view only. It does not replace the "
            "experiment's measurement-first interpretation or create a winner."
        ),
        "summary_rows": [
            _summary("Result status", manifest.get("result_status")),
            _summary("Candidates measured", len(frame)),
            _summary("Families measured", family_count),
            _summary("Profitable NQ candidates", profitable),
            _summary("Profitable under two-tick stress", two_tick),
            _summary("Pareto-nondominated candidates", pareto),
            _summary("Automatic winner", manifest.get("automatic_winner")),
            _summary("Formal pass/fail gates", manifest.get("formal_accept_reject_gates")),
            _summary("MCPT run", manifest.get("mcpt_run")),
            _summary("Paper trading authorized", manifest.get("paper_trading_authorized")),
        ],
        "comparison_rows": comparison_rows,
        "source_files": [
            measurements_path.relative_to(project_dir).as_posix(),
            manifest_path.relative_to(project_dir).as_posix(),
        ],
    }
    return StrategyAdapterResult(metrics, context, context["source_files"][0], adapter_id)


def _exp010(project_dir: Path) -> StrategyAdapterResult | None:
    root = project_dir / "results" / "EXP-010" / "opening_drive_validation"
    result_path = root / "validation_result.json"
    measurements_path = root / "candidate_measurements.csv"
    payload = _read_json(result_path)
    frame = _read_csv(measurements_path)
    if not payload:
        return None

    selected_id = str(
        _first(
            payload,
            ("selection", "selected_candidate_id"),
        )
        or ""
    )
    selected_row = dict(
        _first(
            payload,
            ("selection", "selected_candidate_row"),
        )
        or {}
    )
    if not frame.empty and selected_id:
        match = frame.loc[
            frame["candidate_id"].astype(str) == selected_id
        ]
        if not match.empty:
            selected_row = match.iloc[0].to_dict()

    adapter_id = "exp010_deep_validation_v1"
    classification = str(
        _first(
            payload,
            ("evaluation", "classification"),
        )
        or payload.get("result_status", "")
    )
    mcpt_p = _first(
        payload,
        ("mcpt", "selection_aware_p_value"),
        ("evaluation", "selection_aware_mcpt_p_value"),
    )
    metrics = _standard_metrics(
        selected_row,
        metric_source=result_path.relative_to(project_dir).as_posix(),
        metric_scope=(
            "Protected selected opening-drive candidate. The selection-aware "
            "MCPT and anchored walk-forward context remain visible alongside "
            "the headline row."
        ),
        headline_name=selected_id or "Selected opening-drive candidate",
        mcpt_p_value=mcpt_p,
        result_decision=classification,
        adapter_id=adapter_id,
    )

    comparison_rows: list[dict[str, Any]] = []
    if not frame.empty:
        ordered = frame.copy()
        if "selected" in ordered:
            ordered["_selected_order"] = (
                ordered["selected"].fillna(False).astype(bool).map({True: 0, False: 1})
            )
            ordered = ordered.sort_values(
                ["_selected_order", "net_profit_usd"],
                ascending=[True, False],
            )
        for row in _frame_records(ordered):
            is_selected = str(row.get("candidate_id")) == selected_id
            row["selected"] = is_selected
            comparison_rows.append(
                _comparison_row(
                    row,
                    name=str(row.get("candidate_id", "")),
                    role="Selected candidate" if is_selected else "Validated candidate",
                )
            )

    context = {
        "adapter_type": "candidate_validation",
        "adapter_id": adapter_id,
        "comparison_title": "Four opening-drive candidates",
        "comparison_note": (
            "The selected row is the protected historical selection. "
            "The experiment did not authorize paper or live trading."
        ),
        "summary_rows": [
            _summary("Classification", classification),
            _summary(
                "Eligible candidates",
                _first(payload, ("selection", "eligible_candidates")),
            ),
            _summary(
                "Walk-forward profitable folds",
                (
                    f"{_first(payload, ('walk_forward', 'profitable_test_folds'))}/"
                    f"{_first(payload, ('walk_forward', 'fold_count'))}"
                ),
            ),
            _summary(
                "Combined walk-forward net profit",
                _first(payload, ("walk_forward", "combined_test_net_profit_usd")),
            ),
            _summary("Selection-aware MCPT p-value", mcpt_p),
            _summary(
                "Fixed reference MCPT p-value",
                _first(payload, ("mcpt", "fixed_reference_p_value")),
            ),
            _summary("Independent confirmation", payload.get("independent_confirmation")),
            _summary("Paper trading authorized", payload.get("paper_trading_authorized")),
        ],
        "comparison_rows": comparison_rows,
        "source_files": [
            result_path.relative_to(project_dir).as_posix(),
            measurements_path.relative_to(project_dir).as_posix(),
        ],
    }
    return StrategyAdapterResult(metrics, context, context["source_files"][0], adapter_id)


def _exp011(project_dir: Path) -> StrategyAdapterResult | None:
    root = project_dir / "results" / "EXP-011" / "position_sizing"
    summary_path = root / "measurement_summary.csv"
    result_path = root / "sizing_result.json"
    frame = _read_csv(summary_path)
    payload = _read_json(result_path)
    if frame.empty:
        return None

    preferred = frame.loc[
        (frame["signal_candidate_id"].astype(str) == "opening_drive_0p5_time")
        & (frame["sizing_id"].astype(str) == "fixed_one_nq")
    ]
    headline = (
        preferred.iloc[0].to_dict()
        if not preferred.empty
        else frame.iloc[0].to_dict()
    )
    headline_name = (
        f"{headline.get('signal_candidate_id', '')} / "
        f"{headline.get('sizing_id', '')}"
    ).strip(" /")
    adapter_id = "exp011_position_sizing_v1"
    metrics = _standard_metrics(
        headline,
        metric_source=summary_path.relative_to(project_dir).as_posix(),
        metric_scope=(
            "Fixed-one-NQ reference row from the six-row sizing study. "
            "This headline is a measurement anchor, not a sizing winner or "
            "a new signal-edge test."
        ),
        headline_name=headline_name,
        mcpt_p_value=None,
        result_decision=str(payload.get("result_status", "MEASURED_POSITION_SIZING_STUDY")),
        adapter_id=adapter_id,
    )

    comparison_rows = []
    ordered = frame.sort_values(
        ["signal_candidate_id", "sizing_id"]
    )
    for row in _frame_records(ordered):
        name = f"{row.get('signal_candidate_id', '')} / {row.get('sizing_id', '')}"
        comparison_rows.append(
            _comparison_row(
                row,
                name=name,
                role=str(row.get("implementation_status", "")),
                note=str(row.get("measurement_role", "")),
            )
        )

    calibration = dict(payload.get("calibration", {}))
    correction = dict(payload.get("unit_correction", {}))
    context = {
        "adapter_type": "position_sizing_study",
        "adapter_id": adapter_id,
        "comparison_title": "Six measured signal-and-sizing rows",
        "comparison_note": (
            "Rows compare fixed one NQ, fractional NQ equal-risk and integer "
            "MNQ equal-risk implementations. No automatic winner or pass/fail "
            "decision was used."
        ),
        "summary_rows": [
            _summary("Result status", payload.get("result_status")),
            _summary("Target dollar risk", calibration.get("target_dollar_risk_usd")),
            _summary("Calibration trades", calibration.get("trade_count")),
            _summary("Evaluation period", _first(payload, ("data", "evaluation_period"))),
            _summary(
                "Automatic sizing winner",
                _first(payload, ("research_interpretation", "automatic_sizing_winner")),
            ),
            _summary(
                "Pass/fail gate",
                _first(payload, ("research_interpretation", "pass_fail_gate")),
            ),
            _summary(
                "New signal-edge test",
                _first(payload, ("research_interpretation", "new_signal_edge_test")),
            ),
            _summary(
                "MNQ unit correction applied",
                bool(correction) and correction.get("identified_after_initial_report"),
            ),
            _summary(
                "Strategy calculation rerun",
                correction.get("strategy_calculation_rerun"),
            ),
        ],
        "comparison_rows": comparison_rows,
        "source_files": [
            summary_path.relative_to(project_dir).as_posix(),
            result_path.relative_to(project_dir).as_posix(),
        ],
    }
    return StrategyAdapterResult(metrics, context, context["source_files"][0], adapter_id)


def _exp013(project_dir: Path) -> StrategyAdapterResult | None:
    root = project_dir / "results" / "EXP-013" / "extended_context_validation"
    result_path = root / "validation_result.json"
    measurements_path = root / "candidate_measurements.csv"
    payload = _read_json(result_path)
    frame = _read_csv(measurements_path)
    if not payload:
        return None

    leader_id = str(
        _first(payload, ("selection", "measurement_leader_id"))
        or ""
    )
    leader_row = dict(
        _first(payload, ("selection", "measurement_leader_row"))
        or {}
    )
    if not frame.empty and leader_id:
        match = frame.loc[frame["candidate_id"].astype(str) == leader_id]
        if not match.empty:
            leader_row = match.iloc[0].to_dict()

    classification = str(
        _first(payload, ("evaluation", "classification"))
        or payload.get("result_status", "")
    )
    mcpt_p = _first(payload, ("mcpt", "discovery_wide_p_value"))
    adapter_id = "exp013_extended_context_validation_v1"
    metrics = _standard_metrics(
        leader_row,
        metric_source=result_path.relative_to(project_dir).as_posix(),
        metric_scope=(
            "Measurement leader among the three frozen finalists. The "
            "discovery-wide MCPT and low-sample context remain part of the "
            "interpretation and this row is not a trading authorization."
        ),
        headline_name=leader_id or "Measurement leader",
        mcpt_p_value=mcpt_p,
        result_decision=classification,
        adapter_id=adapter_id,
    )

    comparison_rows = []
    if not frame.empty:
        ordered = frame.copy()
        if "measurement_leader" in ordered:
            ordered["_leader_order"] = (
                ordered["measurement_leader"]
                .fillna(False)
                .astype(bool)
                .map({True: 0, False: 1})
            )
            ordered = ordered.sort_values(
                ["_leader_order", "net_profit_usd"],
                ascending=[True, False],
            )
        for row in _frame_records(ordered):
            is_leader = str(row.get("candidate_id")) == leader_id
            comparison_rows.append(
                _comparison_row(
                    row,
                    name=str(row.get("candidate_id", "")),
                    role="Measurement leader" if is_leader else "Frozen finalist",
                    note="Low sample" if bool(row.get("low_sample", False)) else "",
                )
            )

    context = {
        "adapter_type": "candidate_validation",
        "adapter_id": adapter_id,
        "comparison_title": "Three frozen extended-context finalists",
        "comparison_note": (
            "All three remain visible. The measurement leader is not an "
            "automatic trading winner."
        ),
        "summary_rows": [
            _summary("Classification", classification),
            _summary(
                "Strong context checks",
                _first(payload, ("evaluation", "strong_context_checks")),
            ),
            _summary(
                "Promising context checks",
                _first(payload, ("evaluation", "promising_context_checks")),
            ),
            _summary(
                "Walk-forward profitable folds",
                (
                    f"{_first(payload, ('walk_forward', 'profitable_test_folds'))}/"
                    f"{_first(payload, ('walk_forward', 'fold_count'))}"
                ),
            ),
            _summary(
                "Combined walk-forward net profit",
                _first(payload, ("walk_forward", "combined_test_net_profit_usd")),
            ),
            _summary("Discovery-wide MCPT p-value", mcpt_p),
            _summary(
                "MCPT source candidate count",
                _first(payload, ("mcpt", "source_candidate_count")),
            ),
            _summary("Independent confirmation", payload.get("independent_confirmation")),
            _summary("Paper trading authorized", payload.get("paper_trading_authorized")),
        ],
        "comparison_rows": comparison_rows,
        "source_files": [
            result_path.relative_to(project_dir).as_posix(),
            measurements_path.relative_to(project_dir).as_posix(),
        ],
    }
    return StrategyAdapterResult(metrics, context, context["source_files"][0], adapter_id)


def _exp014(project_dir: Path) -> StrategyAdapterResult | None:
    root = project_dir / "results" / "EXP-014" / "finalist_behaviour"
    result_path = root / "study_result.json"
    measurements_path = root / "standalone_measurements.csv"
    pair_path = root / "sleeve_pair_measurements.csv"
    payload = _read_json(result_path)
    frame = _read_csv(measurements_path)
    pairs = _read_csv(pair_path)
    if frame.empty:
        return None

    ranked = frame.sort_values(
        ["net_profit_usd", "trade_profit_factor"],
        ascending=[False, False],
    )
    headline = ranked.iloc[0].to_dict()
    headline_name = str(headline.get("candidate_id", "Standalone finalist"))
    adapter_id = "exp014_behaviour_review_v1"
    metrics = _standard_metrics(
        headline,
        metric_source=measurements_path.relative_to(project_dir).as_posix(),
        metric_scope=(
            "Highest standalone NQ net profit among the three reconstructed "
            "finalists. This descriptive headline does not create a winner, "
            "change parameters or turn arithmetic sleeves into portfolios."
        ),
        headline_name=headline_name,
        mcpt_p_value=_first(payload, ("exp013_context", "discovery_wide_mcpt_p_value")),
        result_decision=str(payload.get("result_status", "MEASURED_BEHAVIOUR_REVIEW")),
        adapter_id=adapter_id,
    )

    comparison_rows = [
        _comparison_row(
            row,
            name=str(row.get("candidate_id", "")),
            role="Standalone finalist",
            note="Low sample" if bool(row.get("low_sample", False)) else "",
        )
        for row in _frame_records(ranked)
    ]

    pair_rows: list[dict[str, Any]] = []
    if not pairs.empty:
        for row in _frame_records(pairs):
            pair_rows.append(
                {
                    "name": str(row.get("pair_id", "")),
                    "components": (
                        f"{row.get('first_candidate_id', '')} + "
                        f"{row.get('second_candidate_id', '')}"
                    ),
                    "net_profit_usd": _clean(row.get("net_profit_usd")),
                    "maximum_drawdown_usd": _clean(row.get("maximum_drawdown_usd")),
                    "net_profit_to_drawdown": _clean(row.get("net_profit_to_drawdown")),
                    "profitable_years": _clean(row.get("profitable_years")),
                    "total_years": _clean(row.get("total_years")),
                    "worst_year_usd": _clean(row.get("worst_year_usd")),
                    "diagnostic_not_executable_portfolio": bool(
                        row.get("diagnostic_not_executable_portfolio", False)
                    ),
                }
            )

    reconstruction = dict(payload.get("reconstruction", {}))
    interpretation = dict(payload.get("interpretation", {}))
    context = {
        "adapter_type": "behaviour_review",
        "adapter_id": adapter_id,
        "comparison_title": "Standalone behaviour of the three finalists",
        "comparison_note": (
            "The table preserves all finalists. The headline ordering is "
            "descriptive and does not replace the behaviour review."
        ),
        "summary_rows": [
            _summary("Result status", payload.get("result_status")),
            _summary("Reconstructed candidates", reconstruction.get("candidate_count")),
            _summary("All reconstructions match", reconstruction.get("all_candidates_match")),
            _summary("Strategy rules changed", reconstruction.get("strategy_rules_changed")),
            _summary(
                "EXP-013 classification",
                _first(payload, ("exp013_context", "classification")),
            ),
            _summary(
                "EXP-013 walk-forward folds",
                (
                    f"{_first(payload, ('exp013_context', 'walk_forward_profitable_folds'))}/"
                    f"{_first(payload, ('exp013_context', 'walk_forward_total_folds'))}"
                ),
            ),
            _summary("Pass/fail gates", not bool(interpretation.get("no_pass_fail_gates", True))),
            _summary("Automatic winner", not bool(interpretation.get("no_automatic_winner", True))),
            _summary(
                "Arithmetic pairs executable",
                not bool(
                    interpretation.get(
                        "arithmetic_pairs_not_executable_portfolios",
                        True,
                    )
                ),
            ),
            _summary(
                "Paper trading authorized",
                interpretation.get("paper_trading_authorized"),
            ),
        ],
        "comparison_rows": comparison_rows,
        "pair_rows": pair_rows,
        "pair_title": "Arithmetic sleeve diagnostics",
        "pair_note": (
            "These rows are arithmetic diagnostics only and are not executable "
            "portfolio authorizations."
        ),
        "source_files": [
            measurements_path.relative_to(project_dir).as_posix(),
            result_path.relative_to(project_dir).as_posix(),
            pair_path.relative_to(project_dir).as_posix(),
        ],
    }
    return StrategyAdapterResult(metrics, context, context["source_files"][0], adapter_id)


ADAPTERS: dict[str, Callable[[Path], StrategyAdapterResult | None]] = {
    "EXP-004": _exp004,
    "EXP-006": _exp006,
    "EXP-009": lambda project_dir: _tournament_adapter(
        project_dir,
        experiment_id="EXP-009",
        folder_name="discovery_tournament",
        manifest_name="tournament_manifest.json",
        adapter_id="exp009_discovery_tournament_v1",
    ),
    "EXP-010": _exp010,
    "EXP-011": _exp011,
    "EXP-012": lambda project_dir: _tournament_adapter(
        project_dir,
        experiment_id="EXP-012",
        folder_name="extended_context_tournament",
        manifest_name="tournament_manifest.json",
        adapter_id="exp012_extended_context_tournament_v1",
    ),
    "EXP-013": _exp013,
    "EXP-014": _exp014,
}


def load_strategy_adapter(
    project_dir: Path,
    experiment_id: str,
) -> StrategyAdapterResult | None:
    loader = ADAPTERS.get(experiment_id.strip().upper())
    if loader is None:
        return None
    return loader(Path(project_dir))
