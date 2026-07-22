from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Any, Iterable

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
                ("futures_rows",),
                ("observed", "futures_rows"),
            ),
        ),
        "nq_candidates": _first_present(
            payload,
            (
                ("nq_candidates",),
                ("observed", "nq_candidates"),
            ),
        ),
        "mnq_candidates": _first_present(
            payload,
            (
                ("mnq_candidates",),
                ("observed", "mnq_candidates"),
            ),
        ),
        "history_downloaded": _first_present(
            payload,
            (
                ("history_downloaded",),
                ("boundaries", "history_downloaded"),
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
                ("strategy_run",),
            ),
        ),
        "paper_trading_authorized": _first_present(
            payload,
            (
                ("boundaries", "paper_trading_authorized"),
                ("paper_trading_authorized",),
            ),
        ),
        "live_trading_authorized": _first_present(
            payload,
            (
                ("boundaries", "live_trading_authorized"),
                ("live_trading_authorized",),
            ),
        ),
    }
    return {
        key: value
        for key, value in measurements.items()
        if value is not None and value != ""
    }


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
    return best, source


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
    data_measurements: dict[str, Any] = {}
    result_state = ""
    result_source = ""

    if research_type == "strategy":
        metric_count = populated_strategy_metric_count(metrics)
        if metric_count == 0:
            missing.append("Strategy headline metrics need an experiment-specific adapter")
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
        data_measurements=data_measurements,
        missing_items=tuple(missing),
    )
