from __future__ import annotations

import unittest

import pandas as pd

from exp008_evaluation import (
    EXP007_BASELINE_NQ_PF,
    FAIL_DECISION,
    PASS_DECISION,
    evaluate_exp008,
)


def yearly(
    net_values: list[float] | None = None,
) -> pd.DataFrame:
    if net_values is None:
        net_values = [
            1000.0,
            1000.0,
            1000.0,
            1000.0,
            1000.0,
        ]
    return pd.DataFrame(
        {
            "year": [
                2021,
                2022,
                2023,
                2024,
                2025,
            ],
            "net_profit_usd": net_values,
        }
    )


def walk_forward(
    net_values: list[float] | None = None,
) -> pd.DataFrame:
    if net_values is None:
        net_values = [
            500.0,
            500.0,
            500.0,
            500.0,
            500.0,
        ]
    return pd.DataFrame(
        {
            "fold": [
                1,
                2,
                3,
                4,
                5,
            ],
            "test_net_profit_usd": (
                net_values
            ),
        }
    )


def nq_summary(
    *,
    pf: float = 1.20,
) -> dict[str, float | int]:
    return {
        "trade_profit_factor": pf,
        "net_profit_usd": 50_000.0,
        "average_trade_usd": 50.0,
        "completed_trades": 800,
    }


class Exp008EvaluationTests(
    unittest.TestCase
):
    def test_all_locked_gates_pass(
        self,
    ) -> None:
        result = evaluate_exp008(
            selected_row={
                "neighbor_stable": True
            },
            nq_summary=nq_summary(),
            mnq_summary={
                "trade_profit_factor": 1.10,
                "net_profit_usd": 5_000.0,
            },
            nq_yearly_results=yearly(),
            walk_forward_results=(
                walk_forward()
            ),
            nq_two_tick_summary={
                "net_profit_usd": 30_000.0
            },
            mcpt_p_value=0.05,
        )
        self.assertTrue(
            result["passed"]
        )
        self.assertEqual(
            result["decision"],
            PASS_DECISION,
        )
        self.assertEqual(
            result["failed_gates"],
            [],
        )

    def test_profit_factor_improvement_is_strict(
        self,
    ) -> None:
        result = evaluate_exp008(
            selected_row={
                "neighbor_stable": True
            },
            nq_summary=nq_summary(
                pf=(
                    EXP007_BASELINE_NQ_PF
                )
            ),
            mnq_summary={
                "trade_profit_factor": 1.10,
                "net_profit_usd": 5_000.0,
            },
            nq_yearly_results=yearly(),
            walk_forward_results=(
                walk_forward()
            ),
            nq_two_tick_summary={
                "net_profit_usd": 30_000.0
            },
            mcpt_p_value=0.04,
        )
        gate = result["gates"][
            "selected_nq_trade_profit_factor"
        ]
        self.assertFalse(
            gate["passed"]
        )
        self.assertEqual(
            gate["operator"],
            ">",
        )

    def test_any_failed_gate_rejects(
        self,
    ) -> None:
        result = evaluate_exp008(
            selected_row={
                "neighbor_stable": True
            },
            nq_summary=nq_summary(),
            mnq_summary={
                "trade_profit_factor": 1.10,
                "net_profit_usd": 5_000.0,
            },
            nq_yearly_results=yearly(),
            walk_forward_results=(
                walk_forward()
            ),
            nq_two_tick_summary={
                "net_profit_usd": 30_000.0
            },
            mcpt_p_value=0.050001,
        )
        self.assertFalse(
            result["passed"]
        )
        self.assertEqual(
            result["decision"],
            FAIL_DECISION,
        )
        self.assertIn(
            "selection_aware_nq_mcpt_p_value",
            result["failed_gates"],
        )

    def test_no_selected_candidate_rejects(
        self,
    ) -> None:
        result = evaluate_exp008(
            selected_row=None,
            nq_summary=None,
            mnq_summary=None,
            nq_yearly_results=yearly(
                [
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                ]
            ),
            walk_forward_results=(
                walk_forward(
                    [
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                    ]
                )
            ),
            nq_two_tick_summary=None,
            mcpt_p_value=1.0,
        )
        self.assertFalse(
            result[
                "selected_candidate_exists"
            ]
        )
        self.assertIn(
            "selected_candidate_neighbor_stable",
            result["failed_gates"],
        )

    def test_three_profitable_folds_are_enough(
        self,
    ) -> None:
        result = evaluate_exp008(
            selected_row={
                "neighbor_stable": True
            },
            nq_summary=nq_summary(),
            mnq_summary={
                "trade_profit_factor": 1.10,
                "net_profit_usd": 5_000.0,
            },
            nq_yearly_results=yearly(),
            walk_forward_results=(
                walk_forward(
                    [
                        1000.0,
                        1000.0,
                        1000.0,
                        -100.0,
                        -100.0,
                    ]
                )
            ),
            nq_two_tick_summary={
                "net_profit_usd": 30_000.0
            },
            mcpt_p_value=0.04,
        )
        self.assertTrue(
            result["gates"][
                "profitable_anchored_test_folds"
            ]["passed"]
        )


if __name__ == "__main__":
    unittest.main()
