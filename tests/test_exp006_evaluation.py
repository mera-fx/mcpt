from __future__ import annotations

import unittest

import pandas as pd

from exp006_evaluation import evaluate_exp006
from exp006_orb import OrbParameters
from exp006_walk_forward import WalkForwardResult


class Exp006EvaluationTests(unittest.TestCase):
    def rows(self) -> tuple[pd.Series, pd.Series]:
        selected = pd.Series(
            {
                "eligible": True,
                "neighbor_stable": True,
                "profitable_neighbor_share": 0.75,
                "nq_trade_profit_factor": 1.25,
                "nq_maximum_drawdown_usd": -11000.0,
                "mnq_trade_profit_factor": 1.15,
            }
        )
        baseline = pd.Series(
            {
                "nq_trade_profit_factor": 1.18,
                "nq_maximum_drawdown_usd": -10000.0,
            }
        )
        return selected, baseline

    def walk_forward(self) -> WalkForwardResult:
        return WalkForwardResult(
            folds=pd.DataFrame(),
            profitable_nq_test_folds=4,
            total_nq_net_profit_usd=10000.0,
            total_mnq_net_profit_usd=1000.0,
        )

    def test_all_gates_pass(self) -> None:
        selected, baseline = self.rows()
        result = evaluate_exp006(
            selected_parameters=OrbParameters(
                5,
                "10:30",
                "long",
            ),
            selected_row=selected,
            baseline_row=baseline,
            walk_forward=self.walk_forward(),
            selection_mcpt_p_value=0.04,
        )
        self.assertTrue(result.passed)
        self.assertEqual(
            result.decision,
            "LOCK_CANDIDATE_FOR_FORWARD_PAPER_COMPARISON",
        )

    def test_baseline_candidate_fails(self) -> None:
        selected, baseline = self.rows()
        result = evaluate_exp006(
            selected_parameters=OrbParameters(
                15,
                "12:00",
                "both",
            ),
            selected_row=selected,
            baseline_row=baseline,
            walk_forward=self.walk_forward(),
            selection_mcpt_p_value=0.04,
        )
        self.assertIn(
            "selected_candidate_differs_from_exp005",
            result.failed_gates,
        )

    def test_mcpt_boundary_is_inclusive(self) -> None:
        selected, baseline = self.rows()
        result = evaluate_exp006(
            selected_parameters=OrbParameters(
                5,
                "10:30",
                "long",
            ),
            selected_row=selected,
            baseline_row=baseline,
            walk_forward=self.walk_forward(),
            selection_mcpt_p_value=0.05,
        )
        self.assertTrue(
            result.gates[
                "selection_aware_mcpt_p_value"
            ]["passed"]
        )


if __name__ == "__main__":
    unittest.main()
