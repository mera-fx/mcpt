from __future__ import annotations

import unittest

import pandas as pd

from exp003_full_validation import (
    calculate_profitable_calendar_years,
    evaluate_exp003_full_validation,
)


def passing_summary() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "test": "Fixed parameters",
                "total_return_percent": 12.0,
                "max_drawdown_percent": -30.0,
                "total_trades": 40,
                "trade_profit_factor": 1.20,
            },
            {
                "test": "Walk-forward",
                "total_return_percent": 7.0,
                "max_drawdown_percent": -35.0,
                "total_trades": 42,
                "trade_profit_factor": 1.10,
            },
        ]
    ).set_index("test")


class CalendarYearTests(unittest.TestCase):
    def test_profitable_years_use_prior_year_end(
        self,
    ) -> None:
        index = pd.to_datetime(
            [
                "2022-01-05",
                "2022-12-31",
                "2023-12-31",
                "2024-12-31",
            ]
        )

        equity = pd.DataFrame(
            {
                "equity": [
                    100_000,
                    110_000,
                    99_000,
                    120_000,
                ]
            },
            index=index,
        )

        count, table = (
            calculate_profitable_calendar_years(
                equity,
                starting_capital=100_000,
            )
        )

        self.assertEqual(count, 2)

        self.assertEqual(
            table["profitable"].tolist(),
            [True, False, True],
        )


class FullValidationGateTests(unittest.TestCase):
    def test_all_gates_pass(
        self,
    ) -> None:
        evaluation = (
            evaluate_exp003_full_validation(
                summary=passing_summary(),
                mcpt_p_value=0.04,
                mcpt_permutations=1000,
                mcpt_source="full_run",
                profitable_calendar_years=2,
            )
        )

        self.assertTrue(evaluation.passed)
        self.assertEqual(
            evaluation.decision,
            "PASS_TO_REVIEW",
        )
        self.assertEqual(
            evaluation.failed_gates,
            [],
        )

    def test_any_failed_gate_rejects(
        self,
    ) -> None:
        summary = passing_summary()
        summary.loc[
            "Walk-forward",
            "trade_profit_factor",
        ] = 0.99

        evaluation = (
            evaluate_exp003_full_validation(
                summary=summary,
                mcpt_p_value=0.04,
                mcpt_permutations=1000,
                mcpt_source="full_run",
                profitable_calendar_years=2,
            )
        )

        self.assertFalse(evaluation.passed)
        self.assertEqual(
            evaluation.decision,
            "REJECT",
        )
        self.assertIn(
            "walkforward_trade_profit_factor",
            evaluation.failed_gates,
        )

    def test_full_mcpt_must_use_1000_permutations(
        self,
    ) -> None:
        evaluation = (
            evaluate_exp003_full_validation(
                summary=passing_summary(),
                mcpt_p_value=0.04,
                mcpt_permutations=25,
                mcpt_source="quick_run",
                profitable_calendar_years=2,
            )
        )

        self.assertFalse(evaluation.passed)
        self.assertIn(
            "full_mcpt_permutations",
            evaluation.failed_gates,
        )
        self.assertIn(
            "full_mcpt_source",
            evaluation.failed_gates,
        )

    def test_return_and_profit_factor_are_strict(
        self,
    ) -> None:
        summary = passing_summary()
        summary.loc[
            "Fixed parameters",
            "total_return_percent",
        ] = 0.0
        summary.loc[
            "Fixed parameters",
            "trade_profit_factor",
        ] = 1.0

        evaluation = (
            evaluate_exp003_full_validation(
                summary=summary,
                mcpt_p_value=0.04,
                mcpt_permutations=1000,
                mcpt_source="full_run",
                profitable_calendar_years=2,
            )
        )

        self.assertFalse(evaluation.passed)
        self.assertIn(
            "fixed_oos_total_return_percent",
            evaluation.failed_gates,
        )
        self.assertIn(
            "fixed_oos_trade_profit_factor",
            evaluation.failed_gates,
        )


if __name__ == "__main__":
    unittest.main()
