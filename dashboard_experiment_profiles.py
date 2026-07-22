from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from dashboard_strategy_adapters import load_strategy_adapter
from research_dashboard_library import ResearchArtifact


STRATEGY_EXPERIMENT_MAX = 14
DATA_SOURCE_EXPERIMENT_MIN = 15

STRATEGY_METRIC_FIELDS = (
    "profit_factor",
    "net_profit_usd",
    "win_rate_percent",
    "max_drawdown_usd",
    "max_drawdown_percent",
    "total_return_percent",
    "total_trades",
    "mcpt_p_value",
)

DATA_RESULT_NAME_PRIORITY = (
    "audit_result.json",
    "catalog_result.json",
    "source_qualification_result.json",
    "result.json",
)


@dataclass(frozen=True)
class DashboardProfile:
    experiment_id: str
    experiment_name: str
    research_type: str
    research_type_label: str
    stage: str
    stage_reason: str
    next_action: str
    market_name: str
    timeframe: str
    strategy_name: str
    hypothesis: str
    preregistration_file: str
    artifact_count: int
    primary_report_path: str
    result_state: str
    result_state_source: str
    metrics: dict[str, Any]
    strategy_context: dict[str, Any]
    data_measurements: dict[str, Any]
    missing_items: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "experiment_name": self.experiment_name,
            "research_type": self.research_type,
            "research_type_label": self.research_type_label,
            "stage": self.stage,
            "stage_reason": self.stage_reason,
            "next_action": self.next_action,
            "market_name": self.market_name,
            "timeframe": self.timeframe,
            "strategy_name": self.strategy_name,
            "hypothesis": self.hypothesis,
            "preregistration_file": self.preregistration_file,
            "artifact_count": self.artifact_count,
            "primary_report_path": self.primary_report_path,
            "result_state": self.result_state,
            "result_state_source": self.result_state_source,
            "metrics": self.metrics,
            "strategy_context": self.strategy_context,
            "data_measurements": self.data_measurements,
            "missing_items": list(self.missing_items),
        }


def experiment_number(experiment_id: str) -> int:
    cleaned = experiment_id.strip().upper()
    if not cleaned.startswith("EXP-"):
        raise ValueError(f"Unsupported experiment ID: {experiment_id}")
    return int(cleaned.split("-", 1)[1])


def research_type_for(experiment_id: str) -> str:
    return (
        "data_source"
        if experiment_number(experiment_id) >= DATA_SOURCE_EXPERIMENT_MIN
        else "strategy"
    )


def _finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def populated_strategy_metric_count(metrics: dict[str, Any]) -> int:
    return sum(_finite(metrics.get(field)) for field in STRATEGY_METRIC_FIELDS)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _nested(payload: dict[str, Any], *keys: str) -> Any:
    current: Any = payload
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def _first_present(payload: dict[str, Any], candidates: Iterable[tuple[str, ...]]) -> Any:
    for path in candidates:
        value = _nested(payload, *path)
        if value is not None:
            return value
    return None


def _data_result_candidates(
    project_dir: Path,
    experiment_id: str,
    artifacts: Iterable[ResearchArtifact],
) -> list[Path]:
    direct = [
        project_dir / "results" / experiment_id / "source_qualification" / name
        for name in DATA_RESULT_NAME_PRIORITY
    ]
    artifact_json = [
        artifact.path
        for artifact in artifacts
        if artifact.experiment_id == experiment_id
        and artifact.extension == ".json"
    ]
    unique: list[Path] = []
    seen: set[Path] = set()
    for path in direct + artifact_json:
        resolved = Path(path).resolve()
        if resolved in seen or not resolved.is_file():
            continue
        seen.add(resolved)
        unique.append(resolved)
    return unique


def _classification_from_payload(payload: dict[str, Any]) -> str:
    value = _first_present(
        payload,
        (
            ("classification",),
            ("assessment", "classification"),
            ("result", "classification"),
            ("evaluation", "classification"),
            ("status",),
            ("result_phase",),
        ),
    )
    return str(value).strip() if value not in (None, "") else ""


def _extract_data_measurements(payload: dict[str, Any]) -> dict[str, Any]:
    measurements = {
        "classification": _classification_from_payload(payload),
        "result_phase": _first_present(
            payload,
            (
                ("result_phase",),
                ("status",),
            ),
        ),
        "classification_scope": _first_present(
            payload,
            (
                ("classification_scope",),
                ("assessment", "classification_scope"),
            ),
        ),
        "client_version": _first_present(
            payload,
            (
                ("client_probe", "version"),
                ("source", "client_version"),
            ),
        ),
        "dataset": _first_present(
            payload,
            (
                ("source", "dataset"),
                ("catalog", "category_requested"),
            ),
        ),
        "schema": _first_present(
            payload,
            (
                ("source", "schema"),
                ("methodology", "schema"),
            ),
        ),
        "contract_type": _first_present(
            payload,
            (
                ("methodology", "contract_type"),
                ("contract_type",),
            ),
        ),
        "continuous_series_method": _first_present(
            payload,
            (
                ("methodology", "continuous_series_method"),
                ("continuous_series_method",),
            ),
        ),
        "roll_method": _first_present(
            payload,
            (
                ("methodology", "roll_method"),
                ("roll_method",),
            ),
        ),
        "price_adjustment": _first_present(
            payload,
            (
                ("methodology", "price_adjustment"),
                ("price_adjustment",),
            ),
        ),
        "volume_semantics": _first_present(
            payload,
            (
                ("methodology", "volume_semantics"),
                ("volume_semantics",),
            ),
        ),
        "initial_windows_measured": _first_present(
            payload,
            (
                ("initial_windows_measured",),
                ("windows_measured",),
                ("observed", "initial_windows_measured"),
            ),
        ),
        "repeatability_windows_measured": _first_present(
            payload,
            (
                ("repeatability_windows_measured",),
                ("repeat_windows_measured",),
                ("observed", "repeatability_windows_measured"),
            ),
        ),
        "regular_trade_minute_coverage": _first_present(
            payload,
            (
                ("observed", "minimum_regular_trade_minute_coverage"),
                ("minimum_regular_trade_minute_coverage",),
                ("regular_trade_minute_coverage",),
            ),
        ),
        "extended_trade_minute_coverage": _first_present(
            payload,
            (
                ("observed", "minimum_extended_trade_minute_coverage"),
                ("minimum_extended_trade_minute_coverage",),
                ("extended_trade_minute_coverage",),
            ),
        ),
        "estimated_cost_usd": _first_present(
            payload,
            (
                ("total_estimated_cost_usd",),
                ("estimated_cost_usd",),
                ("observed", "total_estimated_cost_usd"),
            ),
        ),
        "identity_mismatch_rows": _first_present(
            payload,
            (
                ("observed", "identity_mismatch_rows"),
                ("identity_mismatch_rows",),
            ),
        ),
        "duplicate_timestamp_rows": _first_present(
            payload,
            (
                ("observed", "duplicate_timestamp_rows"),
                ("duplicate_timestamp_rows",),
                ("duplicate_timestamp_count",),
            ),
        ),
        "invalid_ohlc_rows": _first_present(
            payload,
            (
                ("observed", "invalid_ohlc_rows"),
                ("invalid_ohlc_rows",),
            ),
        ),
        "negative_volume_rows": _first_present(
            payload,
            (
                ("observed", "negative_volume_rows"),
                ("negative_volume_rows",),
            ),
        ),
        "nonfinite_ohlcv_rows": _first_present(
            payload,
            (
                ("observed", "nonfinite_ohlcv_rows"),
                ("nonfinite_ohlcv_rows",),
            ),
        ),
        "off_tick_ohlc_values": _first_present(
            payload,
            (
                ("observed", "off_tick_ohlc_values"),
                ("off_tick_ohlc_values",),
            ),
        ),
        "futures_rows": _first_present(
            payload,
            (
                ("assessment", "futures_catalog_rows"),
                ("futures_rows",),
                ("observed", "futures_rows"),
            ),
        ),
        "nq_candidates": _first_present(
            payload,
            (
                ("assessment", "nq_candidate_count"),
                ("nq_candidates",),
                ("observed", "nq_candidates"),
            ),
        ),
        "mnq_candidates": _first_present(
            payload,
            (
                ("assessment", "mnq_candidate_count"),
                ("mnq_candidates",),
                ("observed", "mnq_candidates"),
            ),
        ),
        "history_downloaded": _first_present(
            payload,
            (
                ("history_downloaded",),
                ("boundaries", "history_downloaded"),
                ("boundaries", "full_history_download"),
            ),
        ),
        "history_download_authorized": _first_present(
            payload,
            (
                ("assessment", "history_download_authorized"),
                ("history_download_authorized",),
            ),
        ),
        "nq_identified": _first_present(
            payload,
            (
                ("assessment", "nq_identified"),
                ("nq_identified",),
            ),
        ),
        "mnq_identified": _first_present(
            payload,
            (
                ("assessment", "mnq_identified"),
                ("mnq_identified",),
            ),
        ),
        "contract_method_resolved": _first_present(
            payload,
            (
                ("assessment", "contract_method_resolved"),
                ("contract_method_resolved",),
            ),
        ),
        "roll_method_resolved": _first_present(
            payload,
            (
                ("assessment", "roll_method_resolved"),
                ("roll_method_resolved",),
            ),
        ),
        "price_adjustment_resolved": _first_present(
            payload,
            (
                ("assessment", "price_adjustment_resolved"),
                ("price_adjustment_resolved",),
            ),
        ),
        "sample_windows": _first_present(
            payload,
            (
                ("sample_windows",),
                ("observed", "sample_windows"),
            ),
        ),
        "exchange_accuracy_claim": _first_present(
            payload,
            (
                ("boundaries", "exchange_accuracy_claim"),
                ("exchange_accuracy_claim",),
            ),
        ),
        "strategy_run": _first_present(
            payload,
            (
                ("boundaries", "strategy_run"),
                ("research_boundary", "strategy_run"),
                ("strategy_run",),
            ),
        ),
        "optimization_run": _first_present(
            payload,
            (
                ("research_boundary", "optimization_run"),
                ("optimization_run",),
            ),
        ),
        "primary_source_qualified": _first_present(
            payload,
            (
                ("research_boundary", "primary_source_qualified"),
                ("primary_source_qualified",),
            ),
        ),
        "quantower_replaced": _first_present(
            payload,
            (
                ("research_boundary", "quantower_replaced"),
                ("quantower_replaced",),
            ),
        ),
        "paper_trading_authorized": _first_present(
            payload,
            (
                ("boundaries", "paper_trading_authorized"),
                ("research_boundary", "paper_trading_authorized"),
                ("assessment", "paper_trading_authorized"),
                ("paper_trading_authorized",),
            ),
        ),
        "live_trading_authorized": _first_present(
            payload,
            (
                ("boundaries", "live_trading_authorized"),
                ("research_boundary", "live_trading_authorized"),
                ("assessment", "live_trading_authorized"),
                ("live_trading_authorized",),
            ),
        ),
    }
    return {
        key: value
        for key, value in measurements.items()
        if value is not None and value != ""
    }



def _read_csv_safe(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def _numeric_sum(frame: pd.DataFrame, column: str) -> float | None:
    if column not in frame:
        return None
    values = pd.to_numeric(frame[column], errors="coerce")
    if values.notna().sum() == 0:
        return None
    return float(values.sum())


def _numeric_min(frame: pd.DataFrame, column: str) -> float | None:
    if column not in frame:
        return None
    values = pd.to_numeric(frame[column], errors="coerce")
    if values.notna().sum() == 0:
        return None
    return float(values.min())


def _augment_data_source_measurements(
    project_dir: Path,
    experiment_id: str,
    measurements: dict[str, Any],
) -> dict[str, Any]:
    output = dict(measurements)

    if experiment_id == "EXP-016":
        root = (
            project_dir
            / "results"
            / "EXP-016"
            / "source_qualification"
        )
        structural = _read_csv_safe(
            root / "structural_measurements.csv"
        )
        cross = _read_csv_safe(
            root / "cross_source_measurements.csv"
        )

        if not structural.empty:
            output["structural_windows"] = int(len(structural))
            for target, column in (
                ("total_vendor_rows", "raw_rows"),
                ("duplicate_timestamp_rows", "duplicate_timestamp_count"),
                ("invalid_ohlc_rows", "invalid_ohlc_rows"),
                ("negative_volume_rows", "negative_volume_rows"),
                ("nonfinite_ohlcv_rows", "nonfinite_ohlcv_rows"),
            ):
                value = _numeric_sum(structural, column)
                if value is not None:
                    output[target] = int(round(value))

        if not cross.empty:
            for target, column in (
                (
                    "minimum_expected_minute_completeness",
                    "expected_minute_completeness",
                ),
                (
                    "minimum_matched_timestamp_share",
                    "matched_timestamp_share",
                ),
                (
                    "minimum_close_within_one_tick_share",
                    "close_within_one_tick_share",
                ),
            ):
                value = _numeric_min(cross, column)
                if value is not None:
                    output[target] = value

    elif experiment_id == "EXP-018":
        root = (
            project_dir
            / "results"
            / "EXP-018"
            / "source_qualification"
        )
        windows = _read_csv_safe(
            root / "window_measurements.csv"
        )
        if not windows.empty:
            output["structural_windows"] = int(len(windows))
            for target, column in (
                ("total_vendor_rows", "row_count"),
                ("identity_mismatch_rows", "identity_mismatch_rows"),
                ("duplicate_timestamp_rows", "duplicate_timestamp_rows"),
                ("invalid_ohlc_rows", "invalid_ohlc_rows"),
                ("negative_volume_rows", "negative_volume_rows"),
                ("nonfinite_ohlcv_rows", "nonfinite_ohlcv_rows"),
                ("off_tick_ohlc_values", "off_tick_ohlc_values"),
            ):
                value = _numeric_sum(windows, column)
                if value is not None:
                    output[target] = int(round(value))

            regular = _numeric_min(
                windows,
                "regular_trade_minute_coverage",
            )
            extended = _numeric_min(
                windows,
                "extended_trade_minute_coverage",
            )
            if regular is not None:
                output["regular_trade_minute_coverage"] = regular
            if extended is not None:
                output["extended_trade_minute_coverage"] = extended

    return output


def load_data_source_measurements(
    project_dir: Path,
    experiment_id: str,
    artifacts: Iterable[ResearchArtifact],
) -> tuple[dict[str, Any], str]:
    best: dict[str, Any] = {}
    source = ""
    for path in _data_result_candidates(project_dir, experiment_id, artifacts):
        payload = _read_json(path)
        if not payload:
            continue
        measurements = _extract_data_measurements(payload)
        score = len(measurements)
        if score > len(best):
            best = measurements
            source = path.relative_to(project_dir).as_posix()
    return (
        _augment_data_source_measurements(
            Path(project_dir),
            experiment_id,
            best,
        ),
        source,
    )


def _lifecycle_classification(experiment_id: str, stage_reason: str) -> str:
    text = stage_reason.upper()
    known = (
        "ACCESS_INCOMPLETE",
        "IDENTITY_UNRESOLVED",
        "NOT_QUALIFIED",
        "REPEATABILITY_PENDING",
        "QUALIFIED_AS_ACCESSIBLE_EXACT_CONTRACT_SOURCE",
    )
    for value in known:
        if value in text:
            return value
    return ""


def build_dashboard_profile(
    *,
    project_dir: Path,
    lifecycle: Any,
    artifacts: list[ResearchArtifact],
    primary_report: ResearchArtifact | None,
    metrics: dict[str, Any],
) -> DashboardProfile:
    experiment_id = lifecycle.experiment_id
    research_type = research_type_for(experiment_id)
    research_type_label = (
        "Data-source qualification"
        if research_type == "data_source"
        else "Strategy research"
    )
    experiment_artifacts = [
        artifact for artifact in artifacts
        if artifact.experiment_id == experiment_id
    ]
    missing: list[str] = []
    strategy_context: dict[str, Any] = {}
    data_measurements: dict[str, Any] = {}
    result_state = ""
    result_source = ""

    if research_type == "strategy":
        adapter = load_strategy_adapter(
            Path(project_dir),
            experiment_id,
        )
        if adapter is not None:
            adapted_metrics = dict(metrics)
            adapted_metrics.update(adapter.metrics)
            metrics = adapted_metrics
            strategy_context = dict(adapter.context)

        metric_count = populated_strategy_metric_count(metrics)
        if metric_count == 0:
            missing.append(
                "Strategy headline metrics need an experiment-specific adapter"
            )
        if primary_report is None:
            missing.append("No primary visual report")
        result_state = lifecycle.stage
        result_source = "Lifecycle registry"
    else:
        data_measurements, result_source = load_data_source_measurements(
            project_dir,
            experiment_id,
            experiment_artifacts,
        )
        result_state = str(data_measurements.get("classification", "")).strip()
        if not result_state:
            result_state = _lifecycle_classification(
                experiment_id,
                lifecycle.stage_reason,
            )
            if result_state:
                result_source = "Lifecycle registry"
        if not result_state:
            result_state = lifecycle.stage
            result_source = "Lifecycle registry"
            missing.append("No saved data-qualification classification was parsed")
        if primary_report is None:
            missing.append("No dedicated visual data-quality report")

    if not experiment_artifacts:
        missing.append("No linked research artifacts")

    preregistration = (
        str(lifecycle.preregistration_file)
        if lifecycle.preregistration_file is not None
        else ""
    )

    return DashboardProfile(
        experiment_id=experiment_id,
        experiment_name=lifecycle.experiment_name,
        research_type=research_type,
        research_type_label=research_type_label,
        stage=lifecycle.stage,
        stage_reason=lifecycle.stage_reason,
        next_action=lifecycle.next_action,
        market_name=lifecycle.market_name,
        timeframe=lifecycle.timeframe,
        strategy_name=lifecycle.strategy_name,
        hypothesis=lifecycle.hypothesis,
        preregistration_file=preregistration,
        artifact_count=len(experiment_artifacts),
        primary_report_path=(
            primary_report.project_relative_path
            if primary_report is not None
            else ""
        ),
        result_state=result_state,
        result_state_source=result_source,
        metrics=dict(metrics),
        strategy_context=strategy_context,
        data_measurements=data_measurements,
        missing_items=tuple(missing),
    )
