from __future__ import annotations

from pathlib import Path
import unittest

from analytics_evidence_registry import (
    AnalyticsKind,
    AvailabilityStatus,
    MetricFamily,
    NOT_APPLICABLE_MESSAGE,
    NOT_AVAILABLE_MESSAGE,
    all_series,
    build_analytics_evidence_registry,
    metric_availability,
    validate_analytics_evidence_registry,
)


PROJECT_DIR = Path(__file__).resolve().parents[1]


class AnalyticsEvidenceRegistryTests(unittest.TestCase):
    def test_registry_contains_all_experiments(self) -> None:
        registry = build_analytics_evidence_registry()
        self.assertEqual(
            set(registry),
            {f"EXP-{number:03d}" for number in range(1, 19)},
        )

    def test_registry_has_134_separate_strategy_series(self) -> None:
        registry = validate_analytics_evidence_registry(
            PROJECT_DIR,
            require_files=False,
        )
        self.assertEqual(len(all_series(registry)), 134)
        self.assertEqual(len(registry["EXP-009"].series), 48)
        self.assertEqual(len(registry["EXP-011"].series), 6)
        self.assertEqual(len(registry["EXP-012"].series), 48)

    def test_only_exp014_supports_mae_mfe(self) -> None:
        registry = build_analytics_evidence_registry()
        supporting_ids = {
            item.experiment_id
            for item in all_series(registry)
            if item.supports_mae_mfe
        }
        self.assertEqual(supporting_ids, {"EXP-014"})
        self.assertEqual(
            len(
                [
                    item
                    for item in registry["EXP-014"].series
                    if item.supports_mae_mfe
                ]
            ),
            3,
        )
        unavailable = metric_availability(
            registry["EXP-013"],
            MetricFamily.MAE_AND_MFE,
        )
        self.assertEqual(
            unavailable.status,
            AvailabilityStatus.NOT_AVAILABLE,
        )
        self.assertEqual(unavailable.message, NOT_AVAILABLE_MESSAGE)

    def test_exp004_benchmark_is_explicitly_unavailable(self) -> None:
        registry = build_analytics_evidence_registry()
        availability = metric_availability(
            registry["EXP-004"],
            MetricFamily.BENCHMARK_AND_VALUE_ADDED,
        )
        self.assertEqual(
            availability.status,
            AvailabilityStatus.NOT_AVAILABLE,
        )
        self.assertEqual(
            availability.message,
            NOT_AVAILABLE_MESSAGE,
        )

    def test_data_source_experiments_are_not_strategy_series(self) -> None:
        registry = build_analytics_evidence_registry()
        for number in range(15, 19):
            experiment = registry[f"EXP-{number:03d}"]
            self.assertEqual(
                experiment.analytics_kind,
                AnalyticsKind.DATA_SOURCE_QUALIFICATION,
            )
            self.assertEqual(experiment.series, ())
            for family in MetricFamily:
                availability = metric_availability(
                    experiment,
                    family,
                )
                self.assertEqual(
                    availability.status,
                    AvailabilityStatus.NOT_APPLICABLE,
                )
                self.assertEqual(
                    availability.message,
                    NOT_APPLICABLE_MESSAGE,
                )

    def test_no_series_points_at_generated_report_html(self) -> None:
        for series in all_series():
            for path in series.source_paths():
                self.assertNotIn("reports", path.parts)
                self.assertFalse(path.is_absolute())

    def test_series_specific_availability_rejects_mismatch(self) -> None:
        registry = build_analytics_evidence_registry()
        with self.assertRaisesRegex(
            ValueError,
            "does not belong",
        ):
            metric_availability(
                registry["EXP-005"],
                MetricFamily.PERFORMANCE_SUMMARY,
                registry["EXP-006"].series[0],
            )

    def test_reference_capital_matches_frozen_equity_design(self) -> None:
        registry = build_analytics_evidence_registry()
        ten_thousand_mnq_experiments = {
            "EXP-005",
            "EXP-006",
            "EXP-007",
            "EXP-008",
            "EXP-009",
            "EXP-010",
            "EXP-012",
            "EXP-013",
        }
        for experiment_id in ten_thousand_mnq_experiments:
            for series in registry[experiment_id].series:
                expected = (
                    10_000.0
                    if series.market == "MNQ"
                    else 100_000.0
                )
                self.assertEqual(
                    series.reference_capital_usd,
                    expected,
                )

        for series in registry["EXP-011"].series:
            self.assertEqual(
                series.reference_capital_usd,
                100_000.0,
            )


if __name__ == "__main__":
    unittest.main()
