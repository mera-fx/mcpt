from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

import pandas as pd

from dashboard_strategy_adapters import load_strategy_adapter


class DashboardStrategyAdapterTests(unittest.TestCase):
    def test_exp004_uses_fixed_rules_and_preserves_grid_leader(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = (
                root
                / "results"
                / "EXP-004"
                / "quick_screen"
                / "quick_screen_decision.json"
            )
            path.parent.mkdir(parents=True)
            path.write_text(
                json.dumps(
                    {
                        "decision": "REJECT",
                        "failed_gates": ["quick_mcpt_p_value"],
                        "out_of_sample_disclosure": "BLOCKED",
                        "quick_mcpt_permutations": 25,
                        "quick_mcpt_p_value": 0.307692,
                        "parameter_combinations_pf_ge_1": 3,
                        "fixed_parameters": {
                            "opening_range_minutes": 15,
                            "direction_mode": "both",
                        },
                        "best_parameters": {
                            "opening_range_minutes": 30,
                            "direction_mode": "long_only",
                        },
                        "fixed_in_sample_summary": {
                            "starting_capital": 100000,
                            "ending_equity": 106000,
                            "trade_profit_factor": 1.02,
                            "win_rate_percent": 48,
                            "max_drawdown_percent": -12,
                            "total_return_percent": 6,
                            "completed_trades": 900,
                        },
                        "best_in_sample_summary": {
                            "starting_capital": 100000,
                            "ending_equity": 108000,
                            "trade_profit_factor": 1.05,
                            "win_rate_percent": 51,
                            "max_drawdown_percent": -11,
                            "total_return_percent": 8,
                            "completed_trades": 500,
                        },
                    }
                ),
                encoding="utf-8",
            )
            adapter = load_strategy_adapter(root, "EXP-004")
            self.assertIsNotNone(adapter)
            assert adapter is not None
            self.assertEqual(adapter.metrics["headline_name"], "15-minute both")
            self.assertEqual(adapter.metrics["net_profit_usd"], 6000)
            self.assertEqual(len(adapter.context["comparison_rows"]), 2)

    def test_exp009_tournament_uses_descriptive_leader_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result_root = (
                root
                / "results"
                / "EXP-009"
                / "discovery_tournament"
            )
            result_root.mkdir(parents=True)
            pd.DataFrame(
                [
                    {
                        "candidate_id": "candidate_a",
                        "family_id": "family_a",
                        "completed_trades": 100,
                        "net_profit_usd": 1000,
                        "trade_profit_factor": 1.1,
                        "win_rate": 0.5,
                        "maximum_drawdown_usd": -500,
                        "maximum_drawdown_percent": 0.005,
                        "net_profit_to_drawdown": 2,
                        "two_tick_net_profit_usd": 800,
                        "pareto_nondominated": True,
                    },
                    {
                        "candidate_id": "candidate_b",
                        "family_id": "family_b",
                        "completed_trades": 120,
                        "net_profit_usd": 2000,
                        "trade_profit_factor": 1.2,
                        "win_rate": 0.45,
                        "maximum_drawdown_usd": -700,
                        "maximum_drawdown_percent": 0.007,
                        "net_profit_to_drawdown": 2.85,
                        "two_tick_net_profit_usd": 1500,
                        "pareto_nondominated": True,
                    },
                ]
            ).to_csv(
                result_root / "candidate_measurements.csv",
                index=False,
            )
            (result_root / "tournament_manifest.json").write_text(
                json.dumps(
                    {
                        "result_status": "MEASURED_AWAITING_USER_REVIEW",
                        "automatic_winner": False,
                        "formal_accept_reject_gates": False,
                        "mcpt_run": False,
                        "paper_trading_authorized": False,
                    }
                ),
                encoding="utf-8",
            )
            adapter = load_strategy_adapter(root, "EXP-009")
            self.assertIsNotNone(adapter)
            assert adapter is not None
            self.assertEqual(adapter.metrics["headline_name"], "candidate_b")
            self.assertIn("not an automatic winner", adapter.metrics["metric_scope"])
            summary = {
                row["label"]: row["value"]
                for row in adapter.context["summary_rows"]
            }
            self.assertEqual(summary["Automatic winner"], "No")

    def test_exp011_preserves_all_sizing_rows(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result_root = (
                root
                / "results"
                / "EXP-011"
                / "position_sizing"
            )
            result_root.mkdir(parents=True)
            frame = pd.DataFrame(
                [
                    {
                        "signal_candidate_id": "opening_drive_0p5_time",
                        "sizing_id": "fixed_one_nq",
                        "symbol": "NQ",
                        "implementation_status": "IMPLEMENTABLE",
                        "completed_trades": 100,
                        "net_profit_usd": 10000,
                        "trade_profit_factor": 1.3,
                        "win_rate": 0.5,
                        "average_trade_usd": 100,
                        "maximum_drawdown_usd": -2000,
                        "net_profit_to_maximum_drawdown": 5,
                        "measurement_role": "PRIMARY_SIGNAL",
                    },
                    {
                        "signal_candidate_id": "opening_drive_0p5_time",
                        "sizing_id": "integer_mnq_equal_risk",
                        "symbol": "MNQ",
                        "implementation_status": "IMPLEMENTABLE",
                        "completed_trades": 95,
                        "net_profit_usd": 9000,
                        "trade_profit_factor": 1.25,
                        "win_rate": 0.49,
                        "average_trade_usd": 94,
                        "maximum_drawdown_usd": -1800,
                        "net_profit_to_maximum_drawdown": 5,
                        "measurement_role": "PRIMARY_SIGNAL",
                    },
                ]
            )
            frame.to_csv(
                result_root / "measurement_summary.csv",
                index=False,
            )
            (result_root / "sizing_result.json").write_text(
                json.dumps(
                    {
                        "result_status": "MEASURED_POSITION_SIZING_STUDY",
                        "data": {"evaluation_period": "2021 through 2025"},
                        "calibration": {
                            "target_dollar_risk_usd": 1005,
                            "trade_count": 181,
                        },
                        "research_interpretation": {
                            "automatic_sizing_winner": False,
                            "pass_fail_gate": False,
                            "new_signal_edge_test": False,
                        },
                    }
                ),
                encoding="utf-8",
            )
            adapter = load_strategy_adapter(root, "EXP-011")
            self.assertIsNotNone(adapter)
            assert adapter is not None
            self.assertEqual(len(adapter.context["comparison_rows"]), 2)
            self.assertIn("not a sizing winner", adapter.metrics["metric_scope"])

    def test_exp013_uses_measurement_leader_and_discovery_wide_mcpt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result_root = (
                root
                / "results"
                / "EXP-013"
                / "extended_context_validation"
            )
            result_root.mkdir(parents=True)
            pd.DataFrame(
                [
                    {
                        "candidate_id": "leader",
                        "family_id": "family",
                        "symbol": "NQ",
                        "completed_trades": 88,
                        "net_profit_usd": 44000,
                        "trade_profit_factor": 2.0,
                        "win_rate": 0.32,
                        "average_trade_usd": 500,
                        "maximum_drawdown_usd": -5500,
                        "maximum_drawdown_percent": 0.055,
                        "net_profit_to_drawdown": 8,
                        "measurement_leader": True,
                        "low_sample": True,
                    }
                ]
            ).to_csv(
                result_root / "candidate_measurements.csv",
                index=False,
            )
            (result_root / "validation_result.json").write_text(
                json.dumps(
                    {
                        "result_status": "MEASURED_HISTORICAL_VALIDATION",
                        "selection": {
                            "measurement_leader_id": "leader",
                            "measurement_leader_row": {},
                        },
                        "mcpt": {
                            "discovery_wide_p_value": 0.04,
                            "source_candidate_count": 24,
                        },
                        "walk_forward": {
                            "profitable_test_folds": 3,
                            "fold_count": 4,
                            "combined_test_net_profit_usd": 10000,
                        },
                        "evaluation": {
                            "classification": "PROMISING_CONTEXT",
                        },
                        "paper_trading_authorized": False,
                    }
                ),
                encoding="utf-8",
            )
            adapter = load_strategy_adapter(root, "EXP-013")
            self.assertIsNotNone(adapter)
            assert adapter is not None
            self.assertEqual(adapter.metrics["headline_name"], "leader")
            self.assertEqual(adapter.metrics["mcpt_p_value"], 0.04)
            self.assertEqual(
                adapter.context["comparison_rows"][0]["note"],
                "Low sample",
            )


if __name__ == "__main__":
    unittest.main()
