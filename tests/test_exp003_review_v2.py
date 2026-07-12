from __future__ import annotations

import unittest

import pandas as pd

from exp003_review import (
    evaluate_exp003_review,
)


def summary_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "total_return_percent": [
                31.1,
                37.3,
                89.1,
            ],
            "max_drawdown_percent": [
                -28.0,
                -24.8,
                -67.3,
            ],
            "total_trades": [
                128,
                81,
                1,
            ],
            "trade_profit_factor": [
                1.16,
                1.31,
                float("inf"),
            ],
        },
        index=[
            "Fixed parameters",
            "Walk-forward",
            "Buy and Hold",
        ],
    )


def diagnostic_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "payoff_ratio": [
                2.36,
                2.36,
            ],
            "largest_loss_percent": [
                -8.27,
                -8.27,
            ],
            "top_5_loss_share_percent": [
                16.38,
                24.23,
            ],
        },
        index=[
            "Fixed parameters",
            "Walk-forward",
        ],
    )


class Exp003ReviewV2SchemaTests(
    unittest.TestCase
):
    def test_real_parameter_schema_passes(
        self,
    ) -> None:
        evaluation = evaluate_exp003_review(
            full_validation_decision={
                "decision": "PASS_TO_REVIEW",
                "passed": True,
            },
            summary=summary_frame(),
            diagnostics=diagnostic_frame(),
            parameter_stability={
                "break_even_count": 27,
                "total_combinations": 27,
                "edge_assessment": (
                    "BROAD_IN_SAMPLE_EDGE"
                ),
            },
            profitable_calendar_years=3,
        )

        self.assertTrue(evaluation.passed)
        self.assertEqual(
            evaluation.decision,
            "ACCEPT_FOR_PAPER_TESTING",
        )

        broad_support = (
            evaluation.checks[
                "broad_parameter_support"
            ]
        )

        self.assertEqual(
            broad_support["actual"],
            [27, 27],
        )

        self.assertTrue(
            broad_support["passed"]
        )

    def test_legacy_field_still_supported(
        self,
    ) -> None:
        evaluation = evaluate_exp003_review(
            full_validation_decision={
                "decision": "PASS_TO_REVIEW",
                "passed": True,
            },
            summary=summary_frame(),
            diagnostics=diagnostic_frame(),
            parameter_stability={
                "pf_ge_1_count": 27,
                "total_combinations": 27,
            },
            profitable_calendar_years=3,
        )

        self.assertTrue(
            evaluation.checks[
                "broad_parameter_support"
            ]["passed"]
        )


if __name__ == "__main__":
    unittest.main()
