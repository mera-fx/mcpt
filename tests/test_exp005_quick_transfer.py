from __future__ import annotations

import unittest

from exp005_quick_transfer import (
    evaluate_exp005_quick_transfer,
)


def passing_evaluation(
    **overrides,
):
    values = {
        "nq_trade_profit_factor": 1.06,
        "mnq_trade_profit_factor": 1.01,
        "nq_net_profit_usd": 1.0,
        "mnq_net_profit_usd": 1.0,
        "nq_mcpt_p_value": 0.20,
        "nq_completed_trades": 700,
        "nq_long_trades": 150,
        "nq_short_trades": 150,
        "included_invalid_sessions": 0,
        "included_roll_switch_sessions": 0,
    }
    values.update(overrides)
    return evaluate_exp005_quick_transfer(
        **values
    )


class Exp005QuickTransferGateTests(
    unittest.TestCase
):
    def test_all_locked_gates_pass(
        self,
    ) -> None:
        result = passing_evaluation()

        self.assertTrue(result.passed)
        self.assertEqual(
            result.decision,
            "PASS_TO_FULL_VALIDATION",
        )

    def test_profit_factor_thresholds_are_strict(
        self,
    ) -> None:
        nq = passing_evaluation(
            nq_trade_profit_factor=1.05
        )
        mnq = passing_evaluation(
            mnq_trade_profit_factor=1.00
        )

        self.assertFalse(nq.passed)
        self.assertFalse(mnq.passed)

    def test_net_profit_thresholds_are_strict(
        self,
    ) -> None:
        result = passing_evaluation(
            nq_net_profit_usd=0.0
        )

        self.assertFalse(result.passed)
        self.assertIn(
            "nq_net_profit_usd",
            result.failed_gates,
        )

    def test_mcpt_boundary_is_inclusive(
        self,
    ) -> None:
        result = passing_evaluation(
            nq_mcpt_p_value=0.20
        )

        self.assertTrue(result.passed)

    def test_any_failed_gate_rejects(
        self,
    ) -> None:
        result = passing_evaluation(
            nq_completed_trades=699
        )

        self.assertEqual(
            result.decision,
            "REJECT",
        )


if __name__ == "__main__":
    unittest.main()
