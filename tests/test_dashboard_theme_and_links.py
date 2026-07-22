from __future__ import annotations

import re
import unittest

from build_research_dashboard_v2 import build_html
from dashboard_experiment_profiles import DashboardProfile


class DashboardThemeAndLinkTests(unittest.TestCase):
    def _profile(self) -> DashboardProfile:
        return DashboardProfile(
            experiment_id="EXP-010",
            experiment_name="Opening-drive test",
            research_type="strategy",
            research_type_label="Strategy research",
            stage="REVIEW",
            stage_reason="Saved evidence.",
            next_action="Preserve and review.",
            market_name="NQ / MNQ futures",
            timeframe="5-minute signal / 1-minute execution",
            strategy_name="opening_drive_deep_validation",
            hypothesis="Test hypothesis.",
            preregistration_file="research/EXP-010_preregistration.md",
            artifact_count=1,
            primary_report_path="reports/EXP-010-research-lab/report.html",
            result_state="REVIEW",
            result_state_source="Lifecycle registry",
            metrics={},
            strategy_context={},
            data_measurements={},
            missing_items=(),
        )

    def test_primary_report_opens_in_new_tab_safely(self) -> None:
        page = build_html([self._profile()], [], {})
        self.assertRegex(
            page,
            re.compile(
                r'<a class="button" href="[^"]+" '
                r'target="_blank" rel="noopener noreferrer">'
                r'Open primary report</a>'
            ),
        )

    def test_dashboard_uses_monochrome_warm_reference_theme(self) -> None:
        page = build_html([self._profile()], [], {})
        for expected in (
            "--bg: #070707;",
            "--panel: #111113;",
            "--panel2: #18181b;",
            "--text: #f1efeb;",
            "--muted: #9c968e;",
            "--line: #343436;",
            "--accent: #c6a06a;",
            "--grid: rgba(255, 255, 255, 0.026);",
            "background-size: 72px 72px;",
            "linear-gradient(90deg, var(--grid) 1px, transparent 1px)",
            "background: rgba(198, 160, 106, 0.07);",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, page)

        for removed_blue in (
            "#0a1020",
            "#111a2e",
            "#15213a",
            "#86d7ff",
            "#0d2840",
            "rgba(134, 215, 255",
        ):
            with self.subTest(removed_blue=removed_blue):
                self.assertNotIn(removed_blue, page)


if __name__ == "__main__":
    unittest.main()
