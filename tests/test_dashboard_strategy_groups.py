from __future__ import annotations

import re
import unittest

from build_research_dashboard_v2 import (
    STRATEGY_RESEARCH_GROUPS,
    build_html,
)
from dashboard_experiment_profiles import DashboardProfile


class DashboardStrategyGroupTests(unittest.TestCase):
    def _profile(self, experiment_id: str) -> DashboardProfile:
        return DashboardProfile(
            experiment_id=experiment_id,
            experiment_name=f"Test {experiment_id}",
            research_type="strategy",
            research_type_label="Strategy research",
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
            result_state="REVIEW",
            result_state_source="Lifecycle registry",
            metrics={},
            strategy_context={},
            data_measurements={},
            missing_items=(),
        )

    def test_groups_cover_all_strategy_experiments_once(self) -> None:
        experiment_ids = [
            experiment_id
            for group in STRATEGY_RESEARCH_GROUPS
            for experiment_id in group["experiment_ids"]
        ]
        self.assertEqual(
            experiment_ids,
            [f"EXP-{number:03d}" for number in range(1, 15)],
        )
        self.assertEqual(len(experiment_ids), len(set(experiment_ids)))

    def test_html_renders_collapsed_lineage_groups(self) -> None:
        page = build_html(
            [self._profile(f"EXP-{number:03d}") for number in range(1, 15)],
            [],
            {},
        )

        for title in (
            "BTCUSDT Hourly Strategy Ideas",
            "ORB Locked-Transfer Lineage",
            "Long-Only ORB Exit-Geometry Lineage",
            "Multi-Strategy Discovery and Opening-Drive Lineage",
            "Extended-Hours Context Lineage",
        ):
            self.assertIn(title, page)

        self.assertIn("Research group", page)
        self.assertIn("EXP-004 QQQ quick screen → EXP-005", page)
        self.assertNotRegex(
            page,
            re.compile(r'<details class="research-group"[^>]*\sopen(?:\s|>)'),
        )

    def test_overview_links_open_nested_experiment(self) -> None:
        page = build_html([self._profile("EXP-010")], [], {})
        self.assertIn('const researchGroups = Array.from', page)
        self.assertIn('const group = target.closest(".research-group")', page)
        self.assertIn("if (group) group.open = true", page)
        self.assertIn("target.open = true", page)


if __name__ == "__main__":
    unittest.main()
