from __future__ import annotations

from pathlib import Path
import unittest

from build_research_dashboard import build_dashboard_html


def sample_record() -> dict:
    return {
        "experiment_id": "EXP-008",
        "experiment_name": "ORB exit geometry",
        "hypothesis": "Measure structured exit geometry.",
        "market_name": "NQ / MNQ futures",
        "timeframe": "5-minute signal / 1-minute execution",
        "strategy_name": "long_only_orb_exit_geometry",
        "status": "REJECTED",
        "status_label": "Rejected",
        "stage_reason": "The MCPT threshold failed.",
        "next_action": "Preserve the result.",
        "artifacts": [],
        "primary_report": None,
        "metrics": {
            "profit_factor": 1.156583,
            "net_profit_usd": 102802.5,
            "win_rate_percent": 55.33,
            "max_drawdown_usd": -26640.0,
            "max_drawdown_percent": -26.64,
            "drawdown_percent_note": "",
            "total_trades": 994,
            "mcpt_p_value": 0.138861,
            "result_decision": "REJECT_EXP008_PRESERVE_AS_NEGATIVE_RESULT",
            "review_decision": "",
        },
    }


class ResearchDashboardStrategyTabTests(unittest.TestCase):
    def test_comparison_is_a_separate_navigation_tab(self) -> None:
        markup = build_dashboard_html(
            [sample_record()],
            Path("."),
        )
        self.assertIn(
            'href="strategy_comparison.html"',
            markup,
        )
        self.assertIn('target="_blank"', markup)
        self.assertNotIn(
            '<section class="strategy-comparison"',
            markup,
        )

    def test_main_metrics_use_colour_tones(self) -> None:
        markup = build_dashboard_html(
            [sample_record()],
            Path("."),
        )
        self.assertIn("tone-positive", markup)
        self.assertIn("tone-negative", markup)


if __name__ == "__main__":
    unittest.main()
