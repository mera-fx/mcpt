from __future__ import annotations

from dataclasses import replace
import unittest

from analytics_evidence_registry import (
    AnalyticsKind,
    ExperimentEvidenceSpec,
    MetricFamily,
    NOT_APPLICABLE_MESSAGE,
)
from analytics_metrics import compute_series_analytics
from analytics_reporting import (
    render_experiment_report,
    render_series_report,
    series_slug,
)
from tests.test_analytics_metrics import (
    canonical_frames,
    series_spec,
)


class AnalyticsReportingTests(unittest.TestCase):
    def test_series_report_renders_every_metric_family(self) -> None:
        trades, equity, benchmark = canonical_frames()
        result = compute_series_analytics(
            trades,
            equity,
            series_spec(),
            benchmark=benchmark,
        )
        markup = render_series_report(result)
        for family in MetricFamily:
            self.assertIn(f'id="{family.value}"', markup)
        self.assertIn("All</th><th>Long</th><th>Short", markup)
        self.assertIn("No strategy", markup)
        self.assertIn("Trade/equity reconciliation", markup)
        self.assertIn("Return on max drawdown", markup)
        self.assertNotIn(">Excess return<", markup)
        self.assertIn(
            "Strategy minus buy-and-hold return",
            markup,
        )
        self.assertIn("Maximum contracts held", markup)
        self.assertIn("Annual rate of return", markup)
        self.assertIn("Monthly rate of return", markup)
        self.assertIn("Buy-and-hold return (USD)", markup)
        self.assertIn('class="side-nav"', markup)
        self.assertIn('href="#performance_summary"', markup)
        self.assertIn(
            'href="#equity-curve-comparison"',
            markup,
        )
        self.assertIn('href="#evidence-manifest"', markup)
        self.assertIn("position: sticky", markup)
        self.assertIn("@media (max-width: 980px)", markup)
        self.assertEqual(
            markup.count('<a href="#'),
            len(MetricFamily) + 3,
        )
        self.assertIn(
            "Equity curve and buy-and-hold",
            markup,
        )
        self.assertIn("Strategy equity", markup)
        self.assertIn("Buy-and-hold equity", markup)
        self.assertIn(
            "Both panels use the same USD scale",
            markup,
        )
        self.assertEqual(markup.count('class="curve-panel"'), 2)
        self.assertEqual(markup.count("<svg "), 2)
        self.assertNotIn(
            "<h3>Equity curve</h3>",
            markup,
        )
        self.assertIn(
            'class="negative">($75.00)</td>',
            markup,
        )

    def test_series_report_keeps_strategy_curve_when_benchmark_is_missing(
        self,
    ) -> None:
        trades, equity, _ = canonical_frames()
        without_benchmark = replace(
            series_spec(),
            benchmark_paths=(),
            benchmark_column=None,
        )
        result = compute_series_analytics(
            trades,
            equity,
            without_benchmark,
            benchmark=None,
        )
        markup = render_series_report(result)
        self.assertIn("Strategy equity", markup)
        self.assertIn(
            "Buy-and-hold curve is not available from this "
            "experiment’s frozen evidence.",
            markup,
        )
        self.assertEqual(markup.count("<svg "), 1)

    def test_data_source_experiment_is_not_applicable(self) -> None:
        experiment = ExperimentEvidenceSpec(
            experiment_id="EXP-999",
            experiment_name="Source qualification",
            analytics_kind=(
                AnalyticsKind.DATA_SOURCE_QUALIFICATION
            ),
            series=(),
        )
        markup = render_experiment_report(experiment, ())
        self.assertIn(NOT_APPLICABLE_MESSAGE, markup)
        self.assertEqual(
            markup.count("Not applicable</td>"),
            len(MetricFamily),
        )

    def test_series_slug_is_stable_and_path_safe(self) -> None:
        current = replace(
            series_spec(),
            series_id="EXP-011:candidate/sizing:MNQ",
        )
        self.assertEqual(
            series_slug(current.series_id),
            "exp-011--candidate--sizing--mnq",
        )


if __name__ == "__main__":
    unittest.main()
