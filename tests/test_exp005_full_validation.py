from __future__ import annotations

import unittest

from exp005_full_validation import (
    evaluate_exp005_full_validation,
)


PASSING = {
    "nq_trade_profit_factor": 1.06,
    "mnq_trade_profit_factor": 1.01,
    "nq_net_profit_usd": 1.0,
    "mnq_net_profit_usd": 1.0,
    "nq_mcpt_p_value": 0.05,
    "nq_completed_trades": 500,
    "profitable_nq_calendar_years": 2,
    "included_invalid_sessions": 0,
    "included_roll_switch_sessions": 0,
}


class Exp005FullValidationGateTests(
    unittest.TestCase
):
    def test_all_locked_gates_pass(
        self,
    ) -> None:
        result = evaluate_exp005_full_validation(
            **PASSING
        )
        self.assertTrue(result.passed)
        self.assertEqual(
            result.decision,
            "PASS_TO_REVIEW",
        )
        self.assertEqual(result.failed_gates, ())

    def test_any_failed_gate_rejects(
        self,
    ) -> None:
        values = dict(PASSING)
        values["nq_mcpt_p_value"] = 0.051
        result = evaluate_exp005_full_validation(
            **values
        )
        self.assertFalse(result.passed)
        self.assertEqual(result.decision, "REJECT")
        self.assertIn(
            "nq_mcpt_p_value",
            result.failed_gates,
        )

    def test_profit_factor_thresholds_are_strict(
        self,
    ) -> None:
        values = dict(PASSING)
        values["nq_trade_profit_factor"] = 1.05
        values["mnq_trade_profit_factor"] = 1.00
        result = evaluate_exp005_full_validation(
            **values
        )
        self.assertFalse(
            result.gates[
                "nq_trade_profit_factor"
            ]["passed"]
        )
        self.assertFalse(
            result.gates[
                "mnq_trade_profit_factor"
            ]["passed"]
        )

    def test_net_profit_thresholds_are_strict(
        self,
    ) -> None:
        values = dict(PASSING)
        values["nq_net_profit_usd"] = 0.0
        values["mnq_net_profit_usd"] = 0.0
        result = evaluate_exp005_full_validation(
            **values
        )
        self.assertFalse(
            result.gates[
                "nq_net_profit_usd"
            ]["passed"]
        )
        self.assertFalse(
            result.gates[
                "mnq_net_profit_usd"
            ]["passed"]
        )

    def test_mcpt_trade_and_year_boundaries_are_inclusive(
        self,
    ) -> None:
        result = evaluate_exp005_full_validation(
            **PASSING
        )
        self.assertTrue(
            result.gates[
                "nq_mcpt_p_value"
            ]["passed"]
        )
        self.assertTrue(
            result.gates[
                "nq_completed_trades"
            ]["passed"]
        )
        self.assertTrue(
            result.gates[
                "profitable_nq_calendar_years"
            ]["passed"]
        )

    def test_invalid_or_roll_switch_session_rejects(
        self,
    ) -> None:
        values = dict(PASSING)
        values["included_invalid_sessions"] = 1
        values["included_roll_switch_sessions"] = 1
        result = evaluate_exp005_full_validation(
            **values
        )
        self.assertFalse(
            result.gates[
                "included_invalid_sessions"
            ]["passed"]
        )
        self.assertFalse(
            result.gates[
                "included_roll_switch_sessions"
            ]["passed"]
        )


if __name__ == "__main__":
    unittest.main()
