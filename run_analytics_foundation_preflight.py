from __future__ import annotations

from collections import Counter
from pathlib import Path

from analytics_evidence_registry import (
    AnalyticsKind,
    MetricFamily,
    all_series,
    metric_availability,
    validate_analytics_evidence_registry,
)


PROJECT_DIR = Path(__file__).resolve().parent


def main() -> None:
    registry = validate_analytics_evidence_registry(
        PROJECT_DIR,
        require_files=True,
    )
    series = all_series(registry)
    counts = Counter(item.experiment_id for item in series)
    mae_series = sum(item.supports_mae_mfe for item in series)
    unavailable_benchmarks = [
        experiment_id
        for experiment_id, experiment in registry.items()
        if experiment.analytics_kind == AnalyticsKind.STRATEGY
        and metric_availability(
            experiment,
            MetricFamily.BENCHMARK_AND_VALUE_ADDED,
        ).status.value
        != "AVAILABLE"
    ]

    print("\nANALYTICS FOUNDATION PREFLIGHT")
    print("=" * 39)
    print(f"Experiments registered:  {len(registry)}")
    print(f"Strategy experiments:   {sum(bool(item.series) for item in registry.values())}")
    print(f"Strategy series:        {len(series)}")
    print(f"MAE/MFE series:         {mae_series}")
    print(
        "Benchmark unavailable: "
        + ", ".join(unavailable_benchmarks)
    )
    print("Data-source experiments: EXP-015 to EXP-018")
    print("Strategy rerun:         disabled")
    print("Optimization rerun:     disabled")
    print("MCPT/bootstrap rerun:   disabled")
    print("Market-data download:   disabled")
    print("Report output written:  none")
    print("=" * 39)
    for experiment_id in sorted(counts):
        print(f"{experiment_id}: {counts[experiment_id]} series")
    print(
        "\nPreflight passed. Frozen evidence was read only; "
        "no analytics or report output was written."
    )


if __name__ == "__main__":
    main()
