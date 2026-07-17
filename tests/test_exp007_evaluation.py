from __future__ import annotations

import unittest

import pandas as pd

from exp007_evaluation import (
    FAIL_DECISION,
    PASS_DECISION,
    evaluate_exp007,
)


def summary(*, pf: float = 1.2, net: float = 1000.0) -> dict:
    return {
        "trade_profit_factor": pf,
        "net_profit_usd": net,
        "average_trade_usd": 10.0,
        "completed_trades": 600,
    }


def annual() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "year": [2021, 2022, 2023, 2024, 2025],
            "net_profit_usd": [100.0, -50.0, 100.0, 100.0, -25.0],
        }
    )


class Exp007EvaluationTests(unittest.TestCase):
    def test_all_absolute_gates_pass(self) -> None:
        result = evaluate_exp007(
            nq_summary=summary(),
            mnq_summary=summary(),
            nq_yearly_results=annual(),
            nq_two_tick_summary=summary(),
            mcpt_p_value=0.05,
        )
        self.assertTrue(result["passed"])
        self.assertEqual(result["decision"], PASS_DECISION)
        self.assertEqual(result["failed_gates"], [])

    def test_any_failed_gate_rejects(self) -> None:
        result = evaluate_exp007(
            nq_summary=summary(pf=1.0),
            mnq_summary=summary(),
            nq_yearly_results=annual(),
            nq_two_tick_summary=summary(),
            mcpt_p_value=0.05,
        )
        self.assertFalse(result["passed"])
        self.assertEqual(result["decision"], FAIL_DECISION)
        self.assertIn("nq_trade_profit_factor", result["failed_gates"])

    def test_profit_factor_is_strict(self) -> None:
        result = evaluate_exp007(
            nq_summary=summary(pf=1.0),
            mnq_summary=summary(pf=1.0),
            nq_yearly_results=annual(),
            nq_two_tick_summary=summary(),
            mcpt_p_value=0.05,
        )
        self.assertFalse(result["gates"]["nq_trade_profit_factor"]["passed"])
        self.assertFalse(result["gates"]["mnq_trade_profit_factor"]["passed"])

    def test_no_exp005_improvement_gate_exists(self) -> None:
        result = evaluate_exp007(
            nq_summary=summary(),
            mnq_summary=summary(),
            nq_yearly_results=annual(),
            nq_two_tick_summary=summary(),
            mcpt_p_value=0.05,
        )
        self.assertFalse(
            result["profit_factor_improvement_vs_exp005_required"]
        )
        self.assertNotIn(
            "nq_profit_factor_improvement",
            result["gates"],
        )


if __name__ == "__main__":
    unittest.main()
