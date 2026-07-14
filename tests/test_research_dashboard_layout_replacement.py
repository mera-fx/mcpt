from __future__ import annotations

from pathlib import Path
import unittest


PROJECT_DIR = Path(__file__).resolve().parents[1]
DASHBOARD_BUILDER = (
    PROJECT_DIR / "build_research_dashboard.py"
)


class ResearchDashboardLayoutReplacementTests(
    unittest.TestCase
):
    def source(self) -> str:
        return DASHBOARD_BUILDER.read_text(
            encoding="utf-8"
        )

    def test_alignment_version_is_installed(
        self,
    ) -> None:
        self.assertIn(
            "compact-layout-alignment-v1",
            self.source(),
        )

    def test_arrow_is_removed_from_grid_flow(
        self,
    ) -> None:
        source = self.source()
        self.assertIn(
            ".experiment-summary::before {{",
            source,
        )
        self.assertIn(
            "position: absolute;",
            source,
        )
        self.assertIn(
            "left: 18px;",
            source,
        )

    def test_summary_regions_have_fixed_columns(
        self,
    ) -> None:
        source = self.source()
        self.assertIn(
            ".summary-main {{\n  grid-column: 1;",
            source,
        )
        self.assertIn(
            ".compact-metrics {{\n  grid-column: 2;",
            source,
        )
        self.assertIn(
            ".summary-side {{\n  grid-column: 3;",
            source,
        )

    def test_drawdown_uses_percent_then_usd_fallback(
        self,
    ) -> None:
        source = self.source()
        self.assertIn(
            'metrics.get("max_drawdown_percent")',
            source,
        )
        self.assertIn(
            "compact_drawdown_value = format_percent(",
            source,
        )
        self.assertIn(
            "compact_drawdown_value = format_currency(",
            source,
        )


if __name__ == "__main__":
    unittest.main()
