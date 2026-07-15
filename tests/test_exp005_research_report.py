from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import pandas as pd

import exp005_research_report as report
from exp005_research_report import (
    DEFAULT_REFERENCE_CAPITAL,
    Exp005SavedResults,
    _performance_summary_html,
    build_report_html,
    enriched_summary,
    percentage,
)


def summary_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "symbol": "NQ",
                "included_sessions": 733,
                "completed_trades": 4,
                "long_trades": 2,
                "short_trades": 2,
                "gross_pnl_usd": 170.0,
                "transaction_costs_usd": 60.0,
                "net_profit_usd": 110.0,
                "gross_profit_usd": 260.0,
                "gross_loss_usd": 150.0,
                "trade_profit_factor": 1.733333,
                "win_rate_percent": 50.0,
                "average_trade_usd": 27.5,
                "median_trade_usd": 15.0,
                "maximum_drawdown_usd": -100.0,
                "slippage_ticks_per_side": 1.0,
                "round_trip_cost_usd": 15.0,
            },
            {
                "symbol": "MNQ",
                "included_sessions": 733,
                "completed_trades": 4,
                "long_trades": 2,
                "short_trades": 2,
                "gross_pnl_usd": 17.0,
                "transaction_costs_usd": 12.0,
                "net_profit_usd": 5.0,
                "gross_profit_usd": 20.0,
                "gross_loss_usd": 15.0,
                "trade_profit_factor": 1.333333,
                "win_rate_percent": 50.0,
                "average_trade_usd": 1.25,
                "median_trade_usd": 1.0,
                "maximum_drawdown_usd": -10.0,
                "slippage_ticks_per_side": 1.0,
                "round_trip_cost_usd": 3.0,
            },
        ]
    )


def trades(scale: float = 1.0) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "direction": ["long", "short", "long", "short"],
            "net_pnl_usd": [200.0 * scale, -100.0 * scale, 60.0 * scale, -50.0 * scale],
            "bars_held": [2, 3, 4, 1],
        }
    )


def saved_results() -> Exp005SavedResults:
    decision = {
        "experiment_id": "EXP-005",
        "stage": "FULL_VALIDATION",
        "evaluation": {
            "decision": "PASS_TO_REVIEW",
            "passed": True,
            "failed_gates": [],
            "gates": {
                "nq_pf": {
                    "actual": 1.18,
                    "operator": ">",
                    "threshold": 1.05,
                    "passed": True,
                }
            },
        },
        "data": {
            "included_sessions": 733,
            "included_invalid_sessions": 0,
            "included_roll_switch_sessions": 0,
            "provider_unavailable_sessions_excluded": 2,
            "potential_front_month_mismatch_sessions_excluded": 9,
        },
        "results": {
            "NQ": {"trade_profit_factor": 1.18, "net_profit_usd": 110.0},
            "MNQ": {"trade_profit_factor": 1.33, "net_profit_usd": 5.0},
            "profitable_nq_calendar_years": 3,
        },
        "mcpt": {"permutations": 1000, "p_value": 0.037962},
    }
    review = {
        "evaluation": {
            "decision": "ACCEPT_FOR_PAPER_TESTING",
            "checks": {
                "data_integrity": {"passed": True, "operator": "all required"}
            },
        }
    }
    quick = {
        "results": {
            "NQ": {"trade_profit_factor": 1.13, "net_profit_usd": 90.0, "completed_trades": 4, "win_rate_percent": 50.0},
            "MNQ": {"trade_profit_factor": 1.12, "net_profit_usd": 9.0, "completed_trades": 4, "win_rate_percent": 50.0},
        }
    }
    equity = pd.DataFrame(
        {
            "session_date": ["2025-01-02", "2025-01-03", "2025-01-06"],
            "cumulative_net_pnl_usd": [20.0, -10.0, 50.0],
            "drawdown_usd": [0.0, -30.0, 0.0],
        }
    )
    yearly = pd.DataFrame(
        [
            {"symbol": "NQ", "year": 2025, "completed_trades": 4, "net_profit_usd": 110.0, "trade_profit_factor": 1.7, "win_rate_percent": 50.0, "average_trade_usd": 27.5},
            {"symbol": "MNQ", "year": 2025, "completed_trades": 4, "net_profit_usd": 5.0, "trade_profit_factor": 1.3, "win_rate_percent": 50.0, "average_trade_usd": 1.25},
        ]
    )
    cost = pd.DataFrame(
        [
            {"symbol": "NQ", "slippage_ticks_per_side": 1.0, "round_trip_cost_usd": 15.0, "net_profit_usd": 110.0, "trade_profit_factor": 1.7, "maximum_drawdown_usd": -100.0},
            {"symbol": "MNQ", "slippage_ticks_per_side": 1.0, "round_trip_cost_usd": 3.0, "net_profit_usd": 5.0, "trade_profit_factor": 1.3, "maximum_drawdown_usd": -10.0},
        ]
    )
    mcpt = pd.DataFrame({"trade_profit_factor": [1.0, 1.1]})
    return Exp005SavedResults(
        decision=decision,
        review=review,
        quick=quick,
        summary=summary_frame(),
        yearly=yearly,
        cost_sensitivity=cost,
        nq_equity=equity,
        mnq_equity=equity.copy(),
        nq_trades=trades(),
        mnq_trades=trades(0.1),
        mcpt=mcpt,
        confirmation_audit={},
    )


class Exp005ResearchReportTests(unittest.TestCase):
    def test_reference_percentage_is_explicit(self) -> None:
        self.assertAlmostEqual(percentage(-36175.0, 100000.0), -36.175)

    def test_enriched_summary_has_usd_and_percent_drawdown(self) -> None:
        frame = enriched_summary(summary_frame(), DEFAULT_REFERENCE_CAPITAL)
        nq = frame.loc[frame["symbol"].eq("NQ")].iloc[0]
        self.assertAlmostEqual(nq["maximum_drawdown_percent"], -0.1)

    def test_performance_summary_runs_top_to_bottom(self) -> None:
        frame = summary_frame()
        markup = _performance_summary_html(
            symbol="NQ",
            summary_row=frame.loc[frame["symbol"].eq("NQ")].iloc[0],
            trades=trades(),
            capital=100000.0,
        )
        self.assertIn("All trades", markup)
        self.assertIn("Long trades", markup)
        self.assertIn("Short trades", markup)
        self.assertLess(markup.index("Net profit"), markup.index("Profit Factor"))
        self.assertLess(markup.index("Profit Factor"), markup.index("Total trades"))

    def test_report_uses_left_navigation_and_single_column_sections(self) -> None:
        saved = saved_results()
        summary = enriched_summary(saved.summary, DEFAULT_REFERENCE_CAPITAL)
        charts = {
            "nq_total_equity": "assets/nq_total.png",
            "nq_drawdown": "assets/nq_dd.png",
            "mnq_total_equity": "assets/mnq_total.png",
            "mnq_drawdown": "assets/mnq_dd.png",
            "normalized_equity": "assets/normalized.png",
            "yearly": "assets/yearly.png",
            "cost": "assets/cost.png",
            "mcpt": "assets/mcpt.png",
        }
        markup = build_report_html(saved, summary, charts, DEFAULT_REFERENCE_CAPITAL)
        self.assertIn('class="side-nav"', markup)
        self.assertIn("NQ Strategy Performance Summary", markup)
        self.assertIn("MNQ Strategy Performance Summary", markup)
        self.assertIn("Total Equity Curve and Drawdown", markup)
        self.assertIn("report-stack", markup)
        self.assertNotIn("metric-grid", markup)
        self.assertNotIn("chart-grid", markup)

    def test_chart_builder_creates_total_equity_assets(self) -> None:
        saved = saved_results()
        with tempfile.TemporaryDirectory() as temporary:
            original = report.ASSET_ROOT
            report.ASSET_ROOT = Path(temporary)
            try:
                charts = report._write_charts(saved, DEFAULT_REFERENCE_CAPITAL)
            finally:
                report.ASSET_ROOT = original
        self.assertIn("nq_total_equity", charts)
        self.assertIn("mnq_total_equity", charts)
        self.assertIn("normalized_equity", charts)


if __name__ == "__main__":
    unittest.main()
