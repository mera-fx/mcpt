from __future__ import annotations

import unittest
import pandas as pd

from exp003_review import evaluate_exp003_review


def data():
    summary = pd.DataFrame([
        {"test":"Fixed parameters","total_return_percent":31.1,"max_drawdown_percent":-28.1,"total_trades":128,"trade_profit_factor":1.17},
        {"test":"Walk-forward","total_return_percent":37.4,"max_drawdown_percent":-24.9,"total_trades":81,"trade_profit_factor":1.32},
        {"test":"Buy and Hold","total_return_percent":89.2,"max_drawdown_percent":-67.4,"total_trades":1,"trade_profit_factor":float("inf")},
    ]).set_index("test")
    diagnostics = pd.DataFrame([
        {"test":"Fixed parameters","payoff_ratio":2.37,"largest_loss_percent":-8.28,"top_5_loss_share_percent":16.38},
        {"test":"Walk-forward","payoff_ratio":2.37,"largest_loss_percent":-8.28,"top_5_loss_share_percent":24.24},
    ]).set_index("test")
    full = {"decision":"PASS_TO_REVIEW","passed":True}
    stability = {"combinations_at_or_above_one":27,"total_combinations":27}
    return full, summary, diagnostics, stability


class Exp003ReviewTests(unittest.TestCase):
    def test_passing_review_accepts_for_paper_testing(self) -> None:
        full, summary, diagnostics, stability = data()
        result = evaluate_exp003_review(
            full_validation_decision=full,
            summary=summary,
            diagnostics=diagnostics,
            parameter_stability=stability,
            profitable_calendar_years=3,
        )
        self.assertTrue(result.passed)
        self.assertEqual(result.decision, "ACCEPT_FOR_PAPER_TESTING")

    def test_failed_full_validation_rejects(self) -> None:
        full, summary, diagnostics, stability = data()
        full["decision"] = "REJECT"
        full["passed"] = False
        result = evaluate_exp003_review(
            full_validation_decision=full,
            summary=summary,
            diagnostics=diagnostics,
            parameter_stability=stability,
            profitable_calendar_years=3,
        )
        self.assertFalse(result.passed)
        self.assertIn("full_validation_passed", result.failed_checks)

    def test_weak_payoff_rejects(self) -> None:
        full, summary, diagnostics, stability = data()
        diagnostics.loc["Fixed parameters", "payoff_ratio"] = 1.2
        result = evaluate_exp003_review(
            full_validation_decision=full,
            summary=summary,
            diagnostics=diagnostics,
            parameter_stability=stability,
            profitable_calendar_years=3,
        )
        self.assertFalse(result.passed)
        self.assertIn("payoff_ratio_quality", result.failed_checks)

    def test_drawdown_context_is_required(self) -> None:
        full, summary, diagnostics, stability = data()
        summary.loc["Buy and Hold", "max_drawdown_percent"] = -40.0
        result = evaluate_exp003_review(
            full_validation_decision=full,
            summary=summary,
            diagnostics=diagnostics,
            parameter_stability=stability,
            profitable_calendar_years=3,
        )
        self.assertFalse(result.passed)
        self.assertIn("drawdown_improvement_vs_buy_hold", result.failed_checks)


if __name__ == "__main__":
    unittest.main()
