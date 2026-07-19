from __future__ import annotations

import unittest

import pandas as pd

from exp010_evaluation import evaluate_exp010_evidence


def folds(profitable: int) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "test_net_profit_usd": [
                100.0 if index < profitable else -10.0
                for index in range(5)
            ]
        }
    )


class Exp010EvaluationTests(unittest.TestCase):
    def test_strong_historical_context(self) -> None:
        result = evaluate_exp010_evidence(
            nq_summary={"trade_profit_factor": 1.2},
            mnq_summary={"trade_profit_factor": 1.1},
            nq_two_tick_summary={"net_profit_usd": 1000.0},
            walk_forward=folds(4),
            selection_aware_mcpt_p_value=0.05,
        )
        self.assertEqual(
            result["classification"], "STRONG_HISTORICAL_EVIDENCE"
        )

    def test_promising_context(self) -> None:
        result = evaluate_exp010_evidence(
            nq_summary={"trade_profit_factor": 1.2},
            mnq_summary={"trade_profit_factor": 0.9},
            nq_two_tick_summary={"net_profit_usd": 1000.0},
            walk_forward=folds(3),
            selection_aware_mcpt_p_value=0.10,
        )
        self.assertEqual(
            result["classification"], "PROMISING_BUT_UNCERTAIN"
        )

    def test_weak_context_keeps_measurements(self) -> None:
        result = evaluate_exp010_evidence(
            nq_summary={"trade_profit_factor": 1.2},
            mnq_summary={"trade_profit_factor": 1.1},
            nq_two_tick_summary={"net_profit_usd": 1000.0},
            walk_forward=folds(2),
            selection_aware_mcpt_p_value=0.20,
        )
        self.assertEqual(
            result["classification"],
            "WEAK_OR_INCONCLUSIVE_HISTORICAL_EVIDENCE",
        )
        self.assertTrue(result["measurement_first"])

    def test_no_classification_authorizes_trading(self) -> None:
        result = evaluate_exp010_evidence(
            nq_summary={"trade_profit_factor": 2.0},
            mnq_summary={"trade_profit_factor": 2.0},
            nq_two_tick_summary={"net_profit_usd": 1000.0},
            walk_forward=folds(5),
            selection_aware_mcpt_p_value=0.001,
        )
        self.assertIsNone(result["lifecycle_accept_reject_decision"])
        self.assertFalse(result["paper_trading_authorized"])
        self.assertFalse(result["live_trading_authorized"])


if __name__ == "__main__":
    unittest.main()
