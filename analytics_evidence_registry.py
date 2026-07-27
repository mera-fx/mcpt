from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable

from exp009_preregistration import EXP009_CANDIDATES
from exp010_preregistration import OPENING_DRIVE_CANDIDATES
from exp011_preregistration import SIGNAL_VARIANTS, SIZING_METHODS
from exp012_preregistration import EXP012_CANDIDATES
from exp013_preregistration import FINALIST_CANDIDATES
from exp014_preregistration import FINALIST_IDS
from experiment_lifecycle import EXPERIMENT_LIFECYCLE


NOT_AVAILABLE_MESSAGE = (
    "Not available from this experiment’s frozen evidence"
)
NOT_APPLICABLE_MESSAGE = (
    "Not applicable — data-source qualification experiment"
)


NONCANONICAL_DIAGNOSTIC_MESSAGE = (
    "Frozen diagnostic or closure evidence is available, but it is not "
    "exposed as canonical strategy-series analytics"
)


class AvailabilityStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    NOT_AVAILABLE = "NOT_AVAILABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class MetricFamily(str, Enum):
    PERFORMANCE_SUMMARY = "performance_summary"
    TOTAL_TRADE_ANALYSIS = "total_trade_analysis"
    PERFORMANCE_RATIOS = "performance_ratios"
    TIME_AND_EXPOSURE = "time_and_exposure"
    EQUITY_AND_DRAWDOWN = "equity_and_drawdown"
    WIN_LOSS_DISTRIBUTIONS = "win_loss_distributions"
    STREAK_AND_TRADE_SERIES = "streak_and_trade_series"
    OUTLIER_ANALYSIS = "outlier_analysis"
    MAE_AND_MFE = "mae_and_mfe"
    MONTHLY_AND_ANNUAL = "monthly_and_annual"
    BENCHMARK_AND_VALUE_ADDED = "benchmark_and_value_added"
    EXISTING_ROBUSTNESS = "existing_robustness"


class AnalyticsKind(str, Enum):
    STRATEGY = "STRATEGY"
    DATA_SOURCE_QUALIFICATION = "DATA_SOURCE_QUALIFICATION"


DATA_SOURCE_OR_ENGINEERING_EXPERIMENT_IDS = frozenset(
    f"EXP-{number:03d}"
    for number in range(15, 23)
)

NONCANONICAL_STRATEGY_DIAGNOSTIC_EVIDENCE = {
    "EXP-023": (
        Path(
            "results/EXP-023/transfer_qualification/"
            "transfer_summary.json"
        ),
        Path(
            "results/EXP-023/transfer_qualification/"
            "candidate_transfer_metrics.csv"
        ),
        Path(
            "results/EXP-023/transfer_qualification/"
            "report.html"
        ),
    ),
    "EXP-024": (
        Path(
            "results/EXP-024/source_disagreement_attribution/"
            "attribution_summary.json"
        ),
        Path(
            "results/EXP-024/source_disagreement_attribution/"
            "mismatch_attribution.csv"
        ),
        Path(
            "results/EXP-024/source_disagreement_attribution/"
            "report.html"
        ),
    ),
    "EXP-025": (
        Path(
            "research/EXP-025_closure.md"
        ),
        Path(
            "research/HISTORICAL_DATA_POLICY.md"
        ),
        Path(
            "research/EXP-025_quantower_export_authorization.md"
        ),
    ),
}


class TradeSchema(str, Enum):
    BTC_HOURLY = "BTC_HOURLY"
    QQQ_QUICK_SCREEN = "QQQ_QUICK_SCREEN"
    FUTURES_ORB = "FUTURES_ORB"
    FUTURES_CANDIDATE = "FUTURES_CANDIDATE"
    FUTURES_SIZING = "FUTURES_SIZING"
    FUTURES_ENRICHED = "FUTURES_ENRICHED"


class EquitySchema(str, Enum):
    BTC_HOURLY = "BTC_HOURLY"
    SESSION_EQUITY = "SESSION_EQUITY"
    CANDIDATE_EQUITY = "CANDIDATE_EQUITY"
    SESSION_PNL_MATRIX = "SESSION_PNL_MATRIX"


class BenchmarkSchema(str, Enum):
    NONE = "NONE"
    INLINE_CLOSE = "INLINE_CLOSE"
    NORMALIZED_COMPARISON = "NORMALIZED_COMPARISON"
    MARKET_PARQUET = "MARKET_PARQUET"


@dataclass(frozen=True)
class MetricAvailability:
    status: AvailabilityStatus
    message: str
    evidence_paths: tuple[Path, ...] = ()


@dataclass(frozen=True)
class AnalyticsSeriesSpec:
    series_id: str
    experiment_id: str
    display_name: str
    market: str
    variant_id: str
    candidate_id: str | None
    family_id: str | None
    trades_path: Path
    equity_path: Path
    trade_schema: TradeSchema
    equity_schema: EquitySchema
    benchmark_schema: BenchmarkSchema
    benchmark_paths: tuple[Path, ...] = ()
    benchmark_column: str | None = None
    equity_value_column: str | None = None
    reference_capital_usd: float = 100_000.0
    annualization_periods: int = 252
    eligible_minutes_per_session: int | None = 390
    timezone: str = "America/New_York"
    analysis_start: str | None = None
    analysis_end: str | None = None
    supports_mae_mfe: bool = False
    dense_session_equity: bool = False

    def source_paths(self) -> tuple[Path, ...]:
        return (
            self.trades_path,
            self.equity_path,
            *self.benchmark_paths,
        )


@dataclass(frozen=True)
class ExperimentEvidenceSpec:
    experiment_id: str
    experiment_name: str
    analytics_kind: AnalyticsKind
    series: tuple[AnalyticsSeriesSpec, ...]


def _series(
    *,
    experiment_id: str,
    variant_id: str,
    display_name: str,
    market: str,
    trades_path: str,
    equity_path: str,
    trade_schema: TradeSchema,
    equity_schema: EquitySchema,
    candidate_id: str | None = None,
    family_id: str | None = None,
    benchmark_schema: BenchmarkSchema = BenchmarkSchema.NONE,
    benchmark_paths: Iterable[str] = (),
    benchmark_column: str | None = None,
    equity_value_column: str | None = None,
    reference_capital_usd: float = 100_000.0,
    annualization_periods: int = 252,
    eligible_minutes_per_session: int | None = 390,
    timezone: str = "America/New_York",
    analysis_start: str | None = None,
    analysis_end: str | None = None,
    supports_mae_mfe: bool = False,
    dense_session_equity: bool = False,
) -> AnalyticsSeriesSpec:
    return AnalyticsSeriesSpec(
        series_id=f"{experiment_id}:{variant_id}:{market}",
        experiment_id=experiment_id,
        display_name=display_name,
        market=market,
        variant_id=variant_id,
        candidate_id=candidate_id,
        family_id=family_id,
        trades_path=Path(trades_path),
        equity_path=Path(equity_path),
        trade_schema=trade_schema,
        equity_schema=equity_schema,
        benchmark_schema=benchmark_schema,
        benchmark_paths=tuple(Path(path) for path in benchmark_paths),
        benchmark_column=benchmark_column,
        equity_value_column=equity_value_column,
        reference_capital_usd=reference_capital_usd,
        annualization_periods=annualization_periods,
        eligible_minutes_per_session=eligible_minutes_per_session,
        timezone=timezone,
        analysis_start=analysis_start,
        analysis_end=analysis_end,
        supports_mae_mfe=supports_mae_mfe,
        dense_session_equity=dense_session_equity,
    )


def _btc_series(experiment_id: str) -> tuple[AnalyticsSeriesSpec, ...]:
    benchmark_path = (
        f"results/{experiment_id}/fixed_equity.csv"
        if experiment_id == "EXP-001"
        else f"results/{experiment_id}/buy_hold_equity.csv"
    )
    labels = {
        "EXP-001": "BTCUSDT Donchian breakout",
        "EXP-002": "BTCUSDT z-score mean reversion",
        "EXP-003": "BTCUSDT volatility-compression breakout",
    }
    return tuple(
        _series(
            experiment_id=experiment_id,
            variant_id=variant,
            display_name=f"{labels[experiment_id]} — {variant}",
            market="BTCUSDT",
            trades_path=f"results/{experiment_id}/{variant}_trades.csv",
            equity_path=f"results/{experiment_id}/{variant}_equity.csv",
            trade_schema=TradeSchema.BTC_HOURLY,
            equity_schema=EquitySchema.BTC_HOURLY,
            benchmark_schema=BenchmarkSchema.INLINE_CLOSE,
            benchmark_paths=(benchmark_path,),
            annualization_periods=365,
            eligible_minutes_per_session=None,
            timezone="UTC",
        )
        for variant in ("fixed", "walkforward")
    )


def _fixed_futures_pair(
    *,
    experiment_id: str,
    base_dir: str,
    trade_names: dict[str, str],
    equity_names: dict[str, str],
    label: str,
    benchmark_paths: tuple[str, ...],
) -> tuple[AnalyticsSeriesSpec, ...]:
    return tuple(
        _series(
            experiment_id=experiment_id,
            variant_id="primary",
            display_name=f"{label} — {market}",
            market=market,
            trades_path=f"{base_dir}/{trade_names[market]}",
            equity_path=f"{base_dir}/{equity_names[market]}",
            trade_schema=TradeSchema.FUTURES_ORB,
            equity_schema=EquitySchema.SESSION_EQUITY,
            benchmark_schema=BenchmarkSchema.MARKET_PARQUET,
            benchmark_paths=benchmark_paths,
            reference_capital_usd=(
                10_000.0 if market == "MNQ" else 100_000.0
            ),
        )
        for market in ("NQ", "MNQ")
    )


def _candidate_pair_series(
    *,
    experiment_id: str,
    base_dir: str,
    candidates: Iterable[dict[str, object]],
    benchmark_path: str,
    analysis_start: str,
    analysis_end: str,
) -> tuple[AnalyticsSeriesSpec, ...]:
    specs: list[AnalyticsSeriesSpec] = []
    for candidate in candidates:
        candidate_id = str(candidate["candidate_id"])
        family_id = str(
            candidate.get("family_id", "opening_drive_continuation")
        )
        for market in ("NQ", "MNQ"):
            specs.append(
                _series(
                    experiment_id=experiment_id,
                    variant_id=candidate_id,
                    candidate_id=candidate_id,
                    family_id=family_id,
                    display_name=f"{candidate_id} — {market}",
                    market=market,
                    trades_path=(
                        f"{base_dir}/candidates/{candidate_id}/"
                        f"{market.lower()}_trades.csv"
                    ),
                    equity_path=(
                        f"{base_dir}/candidates/{candidate_id}/"
                        f"{market.lower()}_equity_curve.csv"
                    ),
                    trade_schema=TradeSchema.FUTURES_CANDIDATE,
                    equity_schema=EquitySchema.CANDIDATE_EQUITY,
                    benchmark_schema=(
                        BenchmarkSchema.NORMALIZED_COMPARISON
                    ),
                    benchmark_paths=(benchmark_path,),
                    benchmark_column="nq_normalized_price_benchmark",
                    reference_capital_usd=(
                        10_000.0 if market == "MNQ" else 100_000.0
                    ),
                    analysis_start=analysis_start,
                    analysis_end=analysis_end,
                    dense_session_equity=True,
                )
            )
    return tuple(specs)


def _exp011_series() -> tuple[AnalyticsSeriesSpec, ...]:
    specs: list[AnalyticsSeriesSpec] = []
    benchmark_path = (
        "results/EXP-009/discovery_tournament/"
        "normalized_equity_comparison.csv"
    )
    for signal in SIGNAL_VARIANTS:
        candidate_id = str(signal["candidate_id"])
        for sizing in SIZING_METHODS:
            sizing_id = str(sizing["sizing_id"])
            market = str(sizing["instrument"])
            specs.append(
                _series(
                    experiment_id="EXP-011",
                    variant_id=f"{candidate_id}/{sizing_id}",
                    candidate_id=candidate_id,
                    family_id="opening_drive_continuation",
                    display_name=f"{candidate_id} / {sizing_id}",
                    market=market,
                    trades_path=(
                        "results/EXP-011/position_sizing/rows/"
                        f"{candidate_id}/{sizing_id}/trades.csv"
                    ),
                    equity_path=(
                        "results/EXP-011/position_sizing/rows/"
                        f"{candidate_id}/{sizing_id}/equity_curve.csv"
                    ),
                    trade_schema=TradeSchema.FUTURES_SIZING,
                    equity_schema=EquitySchema.CANDIDATE_EQUITY,
                    benchmark_schema=(
                        BenchmarkSchema.NORMALIZED_COMPARISON
                    ),
                    benchmark_paths=(benchmark_path,),
                    benchmark_column="nq_normalized_price_benchmark",
                    analysis_start="2021-01-04",
                    analysis_end="2025-12-31",
                    dense_session_equity=True,
                )
            )
    return tuple(specs)


def _exp014_series() -> tuple[AnalyticsSeriesSpec, ...]:
    family_by_candidate = {
        str(candidate["candidate_id"]): str(candidate["family_id"])
        for candidate in FINALIST_CANDIDATES
    }
    benchmark_path = (
        "results/EXP-012/extended_context_tournament/"
        "normalized_equity_comparison.csv"
    )
    return tuple(
        _series(
            experiment_id="EXP-014",
            variant_id=candidate_id,
            candidate_id=candidate_id,
            family_id=family_by_candidate[candidate_id],
            display_name=f"{candidate_id} — NQ enriched",
            market="NQ",
            trades_path=(
                "results/EXP-014/finalist_behaviour/candidates/"
                f"{candidate_id}/nq_enriched_trades.csv"
            ),
            equity_path=(
                "results/EXP-014/finalist_behaviour/session_pnl.csv"
            ),
            trade_schema=TradeSchema.FUTURES_ENRICHED,
            equity_schema=EquitySchema.SESSION_PNL_MATRIX,
            equity_value_column=candidate_id,
            benchmark_schema=BenchmarkSchema.NORMALIZED_COMPARISON,
            benchmark_paths=(benchmark_path,),
            benchmark_column="nq_normalized_price_benchmark",
            analysis_start="2020-01-03",
            analysis_end="2025-12-31",
            supports_mae_mfe=True,
            dense_session_equity=True,
        )
        for candidate_id in FINALIST_IDS
    )


def build_analytics_evidence_registry() -> dict[
    str,
    ExperimentEvidenceSpec,
]:
    quick_nq = "data/EXP-005/processed/NQ_1m_quick.parquet"
    confirmation_nq = (
        "data/EXP-005/confirmation/processed/"
        "NQ_1m_confirmation.parquet"
    )
    exp009_benchmark = (
        "results/EXP-009/discovery_tournament/"
        "normalized_equity_comparison.csv"
    )
    exp012_benchmark = (
        "results/EXP-012/extended_context_tournament/"
        "normalized_equity_comparison.csv"
    )

    series_by_experiment: dict[
        str,
        tuple[AnalyticsSeriesSpec, ...],
    ] = {
        "EXP-001": _btc_series("EXP-001"),
        "EXP-002": _btc_series("EXP-002"),
        "EXP-003": _btc_series("EXP-003"),
        "EXP-004": (
            _series(
                experiment_id="EXP-004",
                variant_id="fixed_in_sample",
                display_name="QQQ fixed in-sample ORB",
                market="QQQ",
                trades_path=(
                    "results/EXP-004/quick_screen/"
                    "fixed_in_sample_trades.csv"
                ),
                equity_path=(
                    "results/EXP-004/quick_screen/"
                    "fixed_in_sample_equity.csv"
                ),
                trade_schema=TradeSchema.QQQ_QUICK_SCREEN,
                equity_schema=EquitySchema.SESSION_EQUITY,
            ),
        ),
        "EXP-005": _fixed_futures_pair(
            experiment_id="EXP-005",
            base_dir="results/EXP-005/full_validation",
            trade_names={
                "NQ": "nq_trades.csv",
                "MNQ": "mnq_trades.csv",
            },
            equity_names={
                "NQ": "nq_equity_curve.csv",
                "MNQ": "mnq_equity_curve.csv",
            },
            label="Locked ORB transfer",
            benchmark_paths=(confirmation_nq,),
        ),
        "EXP-006": _fixed_futures_pair(
            experiment_id="EXP-006",
            base_dir="results/EXP-006/optimization",
            trade_names={
                "NQ": "selected_nq_trades.csv",
                "MNQ": "selected_mnq_trades.csv",
            },
            equity_names={
                "NQ": "selected_nq_equity.csv",
                "MNQ": "selected_mnq_equity.csv",
            },
            label="Selected structured ORB",
            benchmark_paths=(quick_nq, confirmation_nq),
        ),
        "EXP-007": _fixed_futures_pair(
            experiment_id="EXP-007",
            base_dir="results/EXP-007/fixed_replication",
            trade_names={
                "NQ": "nq_trades.csv",
                "MNQ": "mnq_trades.csv",
            },
            equity_names={
                "NQ": "nq_equity_curve.csv",
                "MNQ": "mnq_equity_curve.csv",
            },
            label="Fixed 30-minute long-only ORB",
            benchmark_paths=(quick_nq, confirmation_nq),
        ),
        "EXP-008": _fixed_futures_pair(
            experiment_id="EXP-008",
            base_dir="results/EXP-008/exit_geometry",
            trade_names={
                "NQ": "nq_trades.csv",
                "MNQ": "mnq_trades.csv",
            },
            equity_names={
                "NQ": "nq_equity_curve.csv",
                "MNQ": "mnq_equity_curve.csv",
            },
            label="Selected long-only exit geometry",
            benchmark_paths=(quick_nq, confirmation_nq),
        ),
        "EXP-009": _candidate_pair_series(
            experiment_id="EXP-009",
            base_dir="results/EXP-009/discovery_tournament",
            candidates=EXP009_CANDIDATES,
            benchmark_path=exp009_benchmark,
            analysis_start="2019-05-07",
            analysis_end="2025-12-31",
        ),
        "EXP-010": _candidate_pair_series(
            experiment_id="EXP-010",
            base_dir="results/EXP-010/opening_drive_validation",
            candidates=OPENING_DRIVE_CANDIDATES,
            benchmark_path=exp009_benchmark,
            analysis_start="2019-05-07",
            analysis_end="2025-12-31",
        ),
        "EXP-011": _exp011_series(),
        "EXP-012": _candidate_pair_series(
            experiment_id="EXP-012",
            base_dir="results/EXP-012/extended_context_tournament",
            candidates=EXP012_CANDIDATES,
            benchmark_path=exp012_benchmark,
            analysis_start="2020-01-03",
            analysis_end="2025-12-31",
        ),
        "EXP-013": _candidate_pair_series(
            experiment_id="EXP-013",
            base_dir="results/EXP-013/extended_context_validation",
            candidates=FINALIST_CANDIDATES,
            benchmark_path=exp012_benchmark,
            analysis_start="2020-01-03",
            analysis_end="2025-12-31",
        ),
        "EXP-014": _exp014_series(),
    }

    registry: dict[str, ExperimentEvidenceSpec] = {}
    for experiment_id, lifecycle in EXPERIMENT_LIFECYCLE.items():
        kind = (
            AnalyticsKind.DATA_SOURCE_QUALIFICATION
            if experiment_id
            in DATA_SOURCE_OR_ENGINEERING_EXPERIMENT_IDS
            else AnalyticsKind.STRATEGY
        )
        registry[experiment_id] = ExperimentEvidenceSpec(
            experiment_id=experiment_id,
            experiment_name=lifecycle.experiment_name,
            analytics_kind=kind,
            series=series_by_experiment.get(experiment_id, ()),
        )
    return registry


def metric_availability(
    experiment: ExperimentEvidenceSpec,
    metric_family: MetricFamily,
    series: AnalyticsSeriesSpec | None = None,
) -> MetricAvailability:
    if experiment.analytics_kind == (
        AnalyticsKind.DATA_SOURCE_QUALIFICATION
    ):
        return MetricAvailability(
            AvailabilityStatus.NOT_APPLICABLE,
            NOT_APPLICABLE_MESSAGE,
        )

    if series is None:
        if not experiment.series:
            diagnostic_paths = (
                NONCANONICAL_STRATEGY_DIAGNOSTIC_EVIDENCE.get(
                    experiment.experiment_id
                )
            )
            if diagnostic_paths is not None:
                return MetricAvailability(
                    AvailabilityStatus.NOT_AVAILABLE,
                    NONCANONICAL_DIAGNOSTIC_MESSAGE,
                    diagnostic_paths,
                )
            return MetricAvailability(
                AvailabilityStatus.NOT_AVAILABLE,
                NOT_AVAILABLE_MESSAGE,
            )
        if metric_family == MetricFamily.MAE_AND_MFE:
            supported = tuple(
                item
                for item in experiment.series
                if item.supports_mae_mfe
            )
            if not supported:
                return MetricAvailability(
                    AvailabilityStatus.NOT_AVAILABLE,
                    NOT_AVAILABLE_MESSAGE,
                )
            return MetricAvailability(
                AvailabilityStatus.AVAILABLE,
                "Available for the enriched frozen trade ledgers.",
                tuple(item.trades_path for item in supported),
            )
        if metric_family == (
            MetricFamily.BENCHMARK_AND_VALUE_ADDED
        ):
            supported = tuple(
                item
                for item in experiment.series
                if item.benchmark_schema != BenchmarkSchema.NONE
            )
            if not supported:
                return MetricAvailability(
                    AvailabilityStatus.NOT_AVAILABLE,
                    NOT_AVAILABLE_MESSAGE,
                )
            return MetricAvailability(
                AvailabilityStatus.AVAILABLE,
                "Available from aligned frozen benchmark evidence.",
                tuple(
                    path
                    for item in supported
                    for path in item.benchmark_paths
                ),
            )
        paths = tuple(
            path
            for item in experiment.series
            for path in (item.trades_path, item.equity_path)
        )
        return MetricAvailability(
            AvailabilityStatus.AVAILABLE,
            "Available from frozen trade and equity evidence.",
            paths,
        )

    if series.experiment_id != experiment.experiment_id:
        raise ValueError(
            "Series does not belong to the supplied experiment."
        )
    if metric_family == MetricFamily.MAE_AND_MFE:
        if not series.supports_mae_mfe:
            return MetricAvailability(
                AvailabilityStatus.NOT_AVAILABLE,
                NOT_AVAILABLE_MESSAGE,
            )
        return MetricAvailability(
            AvailabilityStatus.AVAILABLE,
            "Available from frozen pre-exit MAE/MFE fields.",
            (series.trades_path,),
        )
    if metric_family == (
        MetricFamily.BENCHMARK_AND_VALUE_ADDED
    ):
        if series.benchmark_schema == BenchmarkSchema.NONE:
            return MetricAvailability(
                AvailabilityStatus.NOT_AVAILABLE,
                NOT_AVAILABLE_MESSAGE,
            )
        return MetricAvailability(
            AvailabilityStatus.AVAILABLE,
            "Available from aligned frozen benchmark evidence.",
            series.benchmark_paths,
        )
    return MetricAvailability(
        AvailabilityStatus.AVAILABLE,
        "Available from frozen trade and equity evidence.",
        (series.trades_path, series.equity_path),
    )


def all_series(
    registry: dict[str, ExperimentEvidenceSpec] | None = None,
) -> tuple[AnalyticsSeriesSpec, ...]:
    current = registry or build_analytics_evidence_registry()
    return tuple(
        series
        for experiment in current.values()
        for series in experiment.series
    )


def resolve_source_paths(
    project_dir: Path,
    series: AnalyticsSeriesSpec,
) -> tuple[Path, ...]:
    return tuple(
        project_dir / path
        for path in series.source_paths()
    )


def validate_analytics_evidence_registry(
    project_dir: Path,
    *,
    require_files: bool = True,
) -> dict[str, ExperimentEvidenceSpec]:
    registry = build_analytics_evidence_registry()
    expected_ids = set(
        EXPERIMENT_LIFECYCLE
    )
    actual_ids = set(registry)

    if actual_ids != expected_ids:
        missing = sorted(
            expected_ids - actual_ids
        )
        unexpected = sorted(
            actual_ids - expected_ids
        )
        raise ValueError(
            "Analytics registry experiment IDs do not match "
            "the lifecycle registry. "
            f"Missing: {missing}; "
            f"unexpected: {unexpected}."
        )

    data_ids = (
        expected_ids
        & DATA_SOURCE_OR_ENGINEERING_EXPERIMENT_IDS
    )
    strategy_ids = expected_ids - data_ids
    diagnostic_ids = set(
        NONCANONICAL_STRATEGY_DIAGNOSTIC_EVIDENCE
    )
    if not diagnostic_ids.issubset(strategy_ids):
        raise ValueError(
            "Noncanonical strategy diagnostics must be registered "
            "strategy experiments."
        )
    for experiment_id in strategy_ids:
        experiment = registry[experiment_id]
        if experiment.analytics_kind != AnalyticsKind.STRATEGY:
            raise ValueError(
                f"{experiment_id} must be a strategy experiment."
            )
        lifecycle = EXPERIMENT_LIFECYCLE[
            experiment_id
        ]
        if (
            not experiment.series
            and lifecycle.stage
            not in {"IDEA", "PRE_REGISTERED"}
            and experiment_id not in diagnostic_ids
        ):
            raise ValueError(
                f"{experiment_id} has no registered strategy series."
            )
    for experiment_id in diagnostic_ids:
        experiment = registry[experiment_id]
        lifecycle = EXPERIMENT_LIFECYCLE[experiment_id]
        if lifecycle.stage != "REVIEW":
            raise ValueError(
                f"{experiment_id} noncanonical diagnostic is not closed."
            )
        if experiment.series:
            raise ValueError(
                f"{experiment_id} noncanonical diagnostic must not "
                "expose canonical strategy series."
            )
    for experiment_id in data_ids:
        experiment = registry[experiment_id]
        if experiment.analytics_kind != (
            AnalyticsKind.DATA_SOURCE_QUALIFICATION
        ):
            raise ValueError(
                f"{experiment_id} must be data-source qualification."
            )
        if experiment.series:
            raise ValueError(
                f"{experiment_id} must not expose strategy series."
            )

    series = all_series(registry)
    expected_counts = {
        "EXP-001": 2,
        "EXP-002": 2,
        "EXP-003": 2,
        "EXP-004": 1,
        "EXP-005": 2,
        "EXP-006": 2,
        "EXP-007": 2,
        "EXP-008": 2,
        "EXP-009": 48,
        "EXP-010": 8,
        "EXP-011": 6,
        "EXP-012": 48,
        "EXP-013": 6,
        "EXP-014": 3,
    }
    for experiment_id, expected_count in expected_counts.items():
        actual_count = len(registry[experiment_id].series)
        if actual_count != expected_count:
            raise ValueError(
                f"{experiment_id} series count changed: "
                f"{actual_count} != {expected_count}."
            )
    if len(series) != 134:
        raise ValueError(
            f"Expected 134 strategy series, found {len(series)}."
        )
    series_ids = [item.series_id for item in series]
    if len(series_ids) != len(set(series_ids)):
        raise ValueError("Analytics series IDs must be unique.")

    for item in series:
        if item.supports_mae_mfe != (
            item.trade_schema == TradeSchema.FUTURES_ENRICHED
        ):
            raise ValueError(
                f"{item.series_id} has inconsistent MAE/MFE support."
            )
        for relative_path in item.source_paths():
            if relative_path.is_absolute():
                raise ValueError(
                    "Analytics evidence paths must remain project-relative."
                )
            if relative_path.parts[0] not in {"results", "data"}:
                raise ValueError(
                    f"Unsupported evidence root: {relative_path}."
                )
            if require_files and not (
                project_dir / relative_path
            ).is_file():
                raise FileNotFoundError(
                    f"Missing analytics evidence: "
                    f"{project_dir / relative_path}"
                )

    exp004 = registry["EXP-004"]
    if metric_availability(
        exp004,
        MetricFamily.BENCHMARK_AND_VALUE_ADDED,
    ).status != AvailabilityStatus.NOT_AVAILABLE:
        raise ValueError("EXP-004 benchmark must remain unavailable.")
    for experiment_id in data_ids:
        for metric_family in MetricFamily:
            availability = metric_availability(
                registry[experiment_id],
                metric_family,
            )
            if availability.status != (
                AvailabilityStatus.NOT_APPLICABLE
            ):
                raise ValueError(
                    f"{experiment_id} strategy analytics must be "
                    "not applicable."
                )
    return registry
