from __future__ import annotations

import unittest

from build_research_dashboard_v2 import build_html
from dashboard_experiment_profiles import DashboardProfile


class BuildResearchDashboardV2Tests(unittest.TestCase):
    def _profile(self, experiment_id: str, research_type: str) -> DashboardProfile:
        return DashboardProfile(
            experiment_id=experiment_id,
            experiment_name="Test",
            research_type=research_type,
            research_type_label=(
                "Data-source qualification"
                if research_type == "data_source"
                else "Strategy research"
            ),
            stage="REVIEW",
            stage_reason="Saved evidence.",
            next_action="Preserve and review.",
            market_name="NQ",
            timeframe="1 minute",
            strategy_name="test",
            hypothesis="Test hypothesis.",
            preregistration_file="",
            artifact_count=0,
            primary_report_path="",
            result_state=(
                "REPEATABILITY_PENDING"
                if research_type == "data_source"
                else "REVIEW"
            ),
            result_state_source="Lifecycle registry",
            metrics={},
            data_measurements={},
            missing_items=("No primary visual report",),
        )

    def test_html_has_separate_research_sections(self) -> None:
        page = build_html(
            [
                self._profile("EXP-014", "strategy"),
                self._profile("EXP-018", "data_source"),
            ],
            [],
            {},
        )
        self.assertIn("Strategy research · EXP-001 through EXP-014", page)
        self.assertIn("Data-source research · EXP-015 through EXP-018", page)
        self.assertIn("REPEATABILITY_PENDING", page)
        self.assertIn("Dashboard coverage gaps", page)
        self.assertIn("No market-data request", page)


if __name__ == "__main__":
    unittest.main()
