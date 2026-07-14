from __future__ import annotations

from pathlib import Path
import unittest

from build_research_dashboard import build_dashboard_html


def sample_record() -> dict:
    return {
        "experiment_id": "EXP-005",
        "experiment_name": "NQ/MNQ ORB",
        "hypothesis": "Test hypothesis.",
        "market_name": "NQ / MNQ futures",
        "timeframe": "5 minutes",
        "strategy_name": "opening_range_breakout",
        "status": "REVIEW",
        "status_label": "Review",
        "stage_reason": "Passed validation.",
        "next_action": "Review the result.",
        "artifacts": [],
        "primary_report": None,
        "metrics": {
            "profit_factor": 1.18,
            "net_profit_usd": 116715.0,
            "win_rate_percent": 43.37,
            "max_drawdown_usd": -36175.0,
            "max_drawdown_percent": float("nan"),
            "drawdown_percent_note": "No locked capital basis.",
            "total_trades": 724,
            "mcpt_p_value": 0.037962,
            "result_decision": "PASS_TO_REVIEW",
            "review_decision": "ACCEPT_FOR_PAPER_TESTING",
        },
    }


class ResearchDashboardCompactTests(unittest.TestCase):
    def test_experiments_are_collapsed_by_default(self) -> None:
        markup = build_dashboard_html([sample_record()], Path('.'))
        self.assertIn(
            '<details class="experiment-section experiment-details"',
            markup,
        )
        self.assertNotIn('<details open>', markup)

    def test_file_library_is_collapsed_by_default(self) -> None:
        markup = build_dashboard_html([sample_record()], Path('.'))
        self.assertIn('<details class="library" id="all-files">', markup)
        self.assertNotIn('<details class="library" id="all-files" open>', markup)

    def test_expand_and_collapse_controls_exist(self) -> None:
        markup = build_dashboard_html([sample_record()], Path('.'))
        self.assertIn('id="expand-all"', markup)
        self.assertIn('id="collapse-all"', markup)
        self.assertIn('openHashTarget', markup)


if __name__ == '__main__':
    unittest.main()
