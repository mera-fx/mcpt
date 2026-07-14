from __future__ import annotations

import unittest

import pandas as pd

from exp005_research_report import (
    DEFAULT_REFERENCE_CAPITAL,
    Exp005SavedResults,
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
                "completed_trades": 724,
                "long_trades": 367,
                "short_trades": 357,
                "gross_pnl_usd": 127575.0,
                "transaction_costs_usd": 10860.0,
                "net_profit_usd": 116715.0,
                "gross_profit_usd": 761100.0,
                "gross_loss_usd": 644385.0,
                "trade_profit_factor": 1.181126,
                "win_rate_percent": 43.37,
                "average_trade_usd": 161.21,
                "median_trade_usd": -667.5,
                "maximum_drawdown_usd": -36175.0,
                "slippage_ticks_per_side": 1.0,
                "round_trip_cost_usd": 15.0,
            },
            {
                "symbol": "MNQ",
                "included_sessions": 733,
                "completed_trades": 724,
                "long_trades": 368,
                "short_trades": 356,
                "gross_pnl_usd": 12779.5,
                "transaction_costs_usd": 2172.0,
                "net_profit_usd": 10607.5,
                "gross_profit_usd": 75743.5,
                "gross_loss_usd": 65136.0,
                "trade_profit_factor": 1.162852,
                "win_rate_percent": 43.23,
                "average_trade_usd": 14.65,
                "median_trade_usd": -67.5,
                "maximum_drawdown_usd": -3674.0,
                "slippage_ticks_per_side": 1.0,
                "round_trip_cost_usd": 3.0,
            },
        ]
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
            "NQ": {
                "trade_profit_factor": 1.181126,
                "net_profit_usd": 116715.0,
                "completed_trades": 724,
                "win_rate_percent": 43.37,
            },
            "MNQ": {
                "trade_profit_factor": 1.162852,
                "net_profit_usd": 10607.5,
                "completed_trades": 724,
                "win_rate_percent": 43.23,
            },
            "profitable_nq_calendar_years": 3,
        },
        "mcpt": {
            "permutations": 1000,
            "p_value": 0.037962,
        },
    }
    review = {
        "evaluation": {
            "decision": "ACCEPT_FOR_PAPER_TESTING",
            "checks": {
                "data_integrity": {
                    "passed": True,
                    "operator": "all required",
                }
            },
        }
    }
    quick = {
        "results": {
            "NQ": {
                "trade_profit_factor": 1.134,
                "net_profit_usd": 94660.0,
                "completed_trades": 884,
                "win_rate_percent": 45.8,
            },
            "MNQ": {
                "trade_profit_factor": 1.120,
                "net_profit_usd": 8549.5,
                "completed_trades": 884,
                "win_rate_percent": 45.7,
            },
        }
    }
    equity = pd.DataFrame(
        {
            "session_date": ["2025-01-02"],
            "cumulative_net_pnl_usd": [100.0],
            "drawdown_usd": [0.0],
        }
    )
    trades = pd.DataFrame(
        {
            "direction": ["long", "short"],
            "net_pnl_usd": [100.0, -50.0],
            "bars_held": [2, 3],
        }
    )
    yearly = pd.DataFrame(
        [
            {
                "symbol": "NQ",
                "year": 2025,
                "completed_trades": 2,
                "net_profit_usd": 50.0,
                "trade_profit_factor": 2.0,
                "win_rate_percent": 50.0,
                "average_trade_usd": 25.0,
            },
            {
                "symbol": "MNQ",
                "year": 2025,
                "completed_trades": 2,
                "net_profit_usd": 5.0,
                "trade_profit_factor": 2.0,
                "win_rate_percent": 50.0,
                "average_trade_usd": 2.5,
            },
        ]
    )
    cost = pd.DataFrame(
        [
            {
                "symbol": "NQ",
                "slippage_ticks_per_side": 1.0,
                "round_trip_cost_usd": 15.0,
                "net_profit_usd": 116715.0,
                "trade_profit_factor": 1.18,
                "maximum_drawdown_usd": -36175.0,
            },
            {
                "symbol": "MNQ",
                "slippage_ticks_per_side": 1.0,
                "round_trip_cost_usd": 3.0,
                "net_profit_usd": 10607.5,
                "trade_profit_factor": 1.16,
                "maximum_drawdown_usd": -3674.0,
            },
        ]
    )
    mcpt = pd.DataFrame(
        {
            "trade_profit_factor": [1.0, 1.1],
        }
    )
    return Exp005SavedResults(
        decision=decision,
        review=review,
        quick=quick,
        summary=summary_frame(),
        yearly=yearly,
        cost_sensitivity=cost,
        nq_equity=equity,
        mnq_equity=equity,
        nq_trades=trades,
        mnq_trades=trades,
        mcpt=mcpt,
        confirmation_audit={},
    )


class Exp005ResearchReportTests(unittest.TestCase):
    def test_reference_percentage_is_explicit(self) -> None:
        self.assertAlmostEqual(
            percentage(116715.0, 100000.0),
            116.715,
        )
        self.assertAlmostEqual(
            percentage(-36175.0, 100000.0),
            -36.175,
        )

    def test_enriched_summary_has_usd_and_percent_drawdown(self) -> None:
        frame = enriched_summary(
            summary_frame(),
            DEFAULT_REFERENCE_CAPITAL,
        )
        nq = frame.loc[frame["symbol"].eq("NQ")].iloc[0]
        mnq = frame.loc[frame["symbol"].eq("MNQ")].iloc[0]
        self.assertEqual(nq["maximum_drawdown_usd"], -36175.0)
        self.assertAlmostEqual(
            nq["maximum_drawdown_percent"],
            -36.175,
        )
        self.assertAlmostEqual(
            mnq["maximum_drawdown_percent"],
            -36.74,
        )

    def test_report_has_research_lab_sections(self) -> None:
        saved = saved_results()
        summary = enriched_summary(
            saved.summary,
            DEFAULT_REFERENCE_CAPITAL,
        )
        charts = {
            "nq_return": "assets/nq_return.png",
            "nq_drawdown": "assets/nq_drawdown.png",
            "mnq_return": "assets/mnq_return.png",
            "mnq_drawdown": "assets/mnq_drawdown.png",
            "yearly": "assets/yearly.png",
            "cost": "assets/cost.png",
            "mcpt": "assets/mcpt.png",
        }
        markup = build_report_html(
            saved,
            summary,
            charts,
            DEFAULT_REFERENCE_CAPITAL,
        )
        self.assertIn("NQ confirmation overview", markup)
        self.assertIn("NQ max drawdown", markup)
        self.assertIn("-36.18%", markup)
        self.assertIn("Cross-period replication", markup)
        self.assertIn("Formal operational review", markup)
        self.assertIn("No protected research workflow was rerun", markup)


if __name__ == "__main__":
    unittest.main()
