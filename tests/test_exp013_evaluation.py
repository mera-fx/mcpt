from __future__ import annotations

import unittest

import pandas as pd

from exp013_evaluation import evaluate_exp013_evidence


class Exp013EvaluationTests(unittest.TestCase):
    def _evaluate(self, p_value: float, profitable: int):
        values = [100.0] * profitable + [-10.0] * (4 - profitable)
        return evaluate_exp013_evidence(
            nq_summary={"trade_profit_factor": 1.2},
            mnq_summary={"trade_profit_factor": 1.1},
            nq_two_tick_summary={"net_profit_usd": 1000.0},
            walk_forward=pd.DataFrame(
                {"test_net_profit_usd": values}
            ),
            discovery_wide_mcpt_p_value=p_value,
        )

    def test_strong_and_promising_contexts_are_distinct(self) -> None:
        self.assertEqual(
            self._evaluate(0.05, 3)["classification"],
            "STRONG_HISTORICAL_EVIDENCE",
        )
        self.assertEqual(
            self._evaluate(0.09, 2)["classification"],
            "PROMISING_BUT_UNCERTAIN",
        )

    def test_classification_never_authorizes_trading(self) -> None:
        result = self._evaluate(0.01, 4)
        self.assertIsNone(result["lifecycle_accept_reject_decision"])
        self.assertFalse(result["paper_trading_authorized"])
        self.assertFalse(result["live_trading_authorized"])
        self.assertTrue(result["measurement_first"])


if __name__ == "__main__":
    unittest.main()
