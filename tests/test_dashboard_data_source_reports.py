from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from dashboard_data_source_reports import build_data_source_reports
from dashboard_experiment_profiles import DashboardProfile


class DashboardDataSourceReportTests(unittest.TestCase):
    def test_exp017_closure_report_is_generated_from_saved_context(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            research = root / "research"
            research.mkdir()
            (research / "EXP-017_closure.md").write_text(
                "# EXP-017 closure\n\nClassification: ACCESS_INCOMPLETE\n",
                encoding="utf-8",
            )
            profile = DashboardProfile(
                experiment_id="EXP-017",
                experiment_name="Exact NQ Contract Data Benchmark",
                research_type="data_source",
                research_type_label="Data-source qualification",
                stage="REVIEW",
                stage_reason=(
                    "Only one accessible exact-contract source was available."
                ),
                next_action="Preserve closure.",
                market_name="NQ futures",
                timeframe="1 minute",
                strategy_name="Exact-contract source benchmark",
                hypothesis="Two sources may be accessible.",
                preregistration_file="",
                artifact_count=1,
                primary_report_path="",
                result_state="ACCESS_INCOMPLETE",
                result_state_source="Lifecycle registry",
                metrics={},
                strategy_context={},
                data_measurements={
                    "classification": "ACCESS_INCOMPLETE",
                },
                missing_items=(
                    "No dedicated visual data-quality report",
                ),
            )
            written = build_data_source_reports(
                root,
                [profile],
            )
            report = written["EXP-017"]
            self.assertTrue(report.exists())
            page = report.read_text(encoding="utf-8")
            self.assertIn("ACCESS_INCOMPLETE", page)
            self.assertIn("No market-data request", page)
            self.assertIn("EXP-017_closure.md", page)


if __name__ == "__main__":
    unittest.main()
