from __future__ import annotations

from dataclasses import replace
import json
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
            strategy_context={},
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
        self.assertIn("Strategy research", page)
        self.assertIn("Data-source research · EXP-015 through EXP-018", page)
        self.assertIn("REPEATABILITY_PENDING", page)
        self.assertIn("Dashboard coverage gaps", page)
        self.assertIn("No market-data request", page)
        self.assertIn(
            '../../results/analytics_expansion/index.html',
            page,
        )

    def test_experiments_start_collapsed(self) -> None:
        page = build_html(
            [
                self._profile(
                    "EXP-003",
                    "strategy",
                ),
                self._profile(
                    "EXP-018",
                    "data_source",
                ),
            ],
            [],
            {},
        )

        self.assertNotRegex(
            page,
            r'<details class="experiment"'
            r'[^>]*\sopen(?:\s|>)',
        )

    def test_watchlist_is_local_persistent_and_has_previews(
        self,
    ) -> None:
        page = build_html(
            [
                self._profile("EXP-014", "strategy"),
                self._profile("EXP-018", "data_source"),
            ],
            [],
            {},
        )

        self.assertIn('id="watchlist"', page)
        self.assertIn('id="watchlist-grid"', page)
        self.assertIn(
            "mcpt-research-dashboard-watchlist-v1",
            page,
        )
        self.assertIn("window.localStorage", page)
        self.assertIn(
            "stored only in this browser and never changes "
            "research evidence",
            page,
        )
        self.assertEqual(
            page.count('data-watch-id="EXP-014"'),
            2,
        )
        self.assertEqual(
            page.count('data-watch-id="EXP-018"'),
            2,
        )

        payload_text = page.split(
            '<script id="watchlist-data" '
            'type="application/json">',
            1,
        )[1].split("</script>", 1)[0]
        payload = json.loads(payload_text)
        self.assertEqual(
            set(payload),
            {"EXP-014", "EXP-018"},
        )
        self.assertEqual(
            len(payload["EXP-014"]["preview_metrics"]),
            4,
        )
        self.assertEqual(
            payload["EXP-018"]["experiment_href"],
            "#exp-018",
        )

    def test_watchlist_payload_escapes_script_boundaries(
        self,
    ) -> None:
        profile = replace(
            self._profile("EXP-014", "strategy"),
            experiment_name="Unsafe </script><script>",
        )
        page = build_html([profile], [], {})
        payload_text = page.split(
            '<script id="watchlist-data" '
            'type="application/json">',
            1,
        )[1].split("</script>", 1)[0]

        self.assertNotIn("</script>", payload_text)
        self.assertIn("\\u003c/script\\u003e", payload_text)
        payload = json.loads(payload_text)
        self.assertEqual(
            payload["EXP-014"]["experiment_name"],
            "Unsafe </script><script>",
        )


if __name__ == "__main__":
    unittest.main()
