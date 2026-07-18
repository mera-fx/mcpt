from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import pandas as pd

from strategy_comparison_dashboard import build_strategy_comparison_section


class StrategyComparisonDashboardTests(unittest.TestCase):
    def test_missing_measurements_show_build_instruction(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            dashboard = project / "reports" / "research_dashboard"
            dashboard.mkdir(parents=True)
            markup = build_strategy_comparison_section(project, dashboard)
        self.assertIn("Strategy measurement comparison", markup)
        self.assertIn("rebuild_strategy_measurement_reports.py", markup)

    def test_comparison_section_contains_vertical_measurement_table(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            results = project / "results" / "strategy_measurements"
            dashboard = project / "reports" / "research_dashboard"
            results.mkdir(parents=True)
            dashboard.mkdir(parents=True)
            pd.DataFrame(
                [
                    {
                        "experiment_id": "EXP-007",
                        "formal_decision": "REJECTED",
                        "parameters": "30-minute OR",
                        "start_date": "2019-05-07",
                        "end_date": "2025-12-31",
                        "completed_trades": 988,
                        "profit_factor": 1.1168,
                        "win_rate_percent": 54.25,
                        "average_trade_usd": 68.60,
                        "net_profit_usd": 67780.0,
                        "maximum_drawdown_usd": -26020.0,
                        "maximum_drawdown_percent": -26.02,
                        "net_profit_to_drawdown": 2.60,
                        "average_trade_to_cost": 4.57,
                        "max_consecutive_losses": 7,
                        "median_holding_minutes": 110.0,
                        "profitable_months_percent": 55.0,
                        "longest_drawdown_sessions": 210,
                        "session_participation_percent": 60.0,
                        "trades_per_year": 152.0,
                        "strategy_return_percent": 67.78,
                        "benchmark_return_percent": 120.0,
                        "excess_return_percent": -52.22,
                        "two_tick_nq_net_profit_usd": 57900.0,
                        "walk_forward_profitable_folds": float("nan"),
                        "walk_forward_fold_count": float("nan"),
                        "walk_forward_net_profit_usd": float("nan"),
                        "mcpt_p_value": 0.05594,
                        "mcpt_percentile": 94.5,
                        "failed_gates": "selection_aware_nq_mcpt_p_value",
                    }
                ]
            ).to_csv(results / "strategy_comparison.csv", index=False)
            exp = results / "EXP-007"
            exp.mkdir()
            pd.DataFrame(
                {
                    "session_date": ["2024-01-02", "2024-01-03"],
                    "strategy_equity": [100000.0, 101000.0],
                    "benchmark_equity": [100000.0, 102000.0],
                    "strategy_drawdown_percent": [0.0, 0.0],
                }
            ).to_csv(exp / "comparison_timeseries.csv", index=False)
            markup = build_strategy_comparison_section(project, dashboard)
            self.assertIn("strategy-comparison-table", markup)
            self.assertIn("Profit Factor", markup)
            self.assertIn("EXP-007", markup)
            self.assertTrue(
                (dashboard / "strategy_comparison_assets" / "normalized_equity_comparison.png").exists()
            )


if __name__ == "__main__":
    unittest.main()
