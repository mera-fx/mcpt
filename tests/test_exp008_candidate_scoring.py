from __future__ import annotations

import unittest

import pandas as pd

from exp008_candidate_scoring import (
    BASELINE,
    add_neighbor_stability,
    parameter_neighbors,
    select_candidate,
)
from exp008_orb import (
    locked_exp008_parameters,
)


def make_grid() -> pd.DataFrame:
    rows = []
    for parameters in (
        locked_exp008_parameters()
    ):
        rows.append(
            {
                **parameters.to_dict(),
                "nq_trade_profit_factor": 1.10,
                "nq_net_profit_usd": 10_000.0,
                "nq_average_trade_usd": 20.0,
                "nq_maximum_drawdown_usd": -5_000.0,
                "nq_maximum_drawdown_percent": -5.0,
                "nq_net_profit_to_drawdown": 2.0,
                "nq_average_trade_to_cost": 1.33,
                "nq_completed_trades": 200,
                "nq_profitable_calendar_years": 5,
                "nq_win_rate_percent": 52.0,
            }
        )
    return pd.DataFrame(rows)


class Exp008CandidateScoringTests(
    unittest.TestCase
):
    def test_baseline_has_six_immediate_neighbors(
        self,
    ) -> None:
        neighbors = parameter_neighbors(
            BASELINE
        )
        self.assertEqual(
            len(neighbors),
            6,
        )
        self.assertEqual(
            len(
                {
                    item.key
                    for item in neighbors
                }
            ),
            6,
        )

    def test_corner_has_three_immediate_neighbors(
        self,
    ) -> None:
        parameters = (
            locked_exp008_parameters()[0]
        )
        self.assertEqual(
            len(
                parameter_neighbors(
                    parameters
                )
            ),
            3,
        )

    def test_neighbor_stability_requires_share_and_median(
        self,
    ) -> None:
        grid = make_grid()
        scored = (
            add_neighbor_stability(
                grid
            )
        )
        baseline = scored.loc[
            scored[
                "parameter_key"
            ].eq(BASELINE.key)
        ].iloc[0]
        self.assertTrue(
            baseline[
                "neighbor_stable"
            ]
        )
        self.assertEqual(
            baseline[
                "profitable_neighbor_fraction"
            ],
            1.0,
        )
        self.assertAlmostEqual(
            baseline[
                "neighbor_median_nq_trade_profit_factor"
            ],
            1.10,
        )

    def test_highest_stable_pf_is_selected(
        self,
    ) -> None:
        grid = make_grid()
        target_key = (
            "or45_target1p5_flat1555"
        )
        grid.loc[
            grid[
                "parameter_key"
            ].eq(target_key),
            "nq_trade_profit_factor",
        ] = 1.30

        selection = select_candidate(
            grid
        )
        self.assertIsNotNone(
            selection.selected_parameters
        )
        self.assertEqual(
            selection.selected_key,
            target_key,
        )

    def test_unstable_peak_is_not_selected(
        self,
    ) -> None:
        grid = make_grid()
        target_key = BASELINE.key
        grid.loc[
            grid[
                "parameter_key"
            ].eq(target_key),
            "nq_trade_profit_factor",
        ] = 2.0

        for neighbor in parameter_neighbors(
            BASELINE
        ):
            mask = grid[
                "parameter_key"
            ].eq(neighbor.key)
            grid.loc[
                mask,
                "nq_trade_profit_factor",
            ] = 0.9
            grid.loc[
                mask,
                "nq_net_profit_usd",
            ] = -100.0

        selection = select_candidate(
            grid
        )
        row = selection.scored_grid.loc[
            selection.scored_grid[
                "parameter_key"
            ].eq(target_key)
        ].iloc[0]
        self.assertFalse(
            row["neighbor_stable"]
        )
        self.assertNotEqual(
            selection.selected_key,
            target_key,
        )

    def test_tie_break_uses_net_profit_to_drawdown(
        self,
    ) -> None:
        grid = make_grid()
        first = (
            "or15_target0p5_flat1200"
        )
        second = (
            "or15_target0p5_flat1400"
        )
        grid.loc[
            grid[
                "parameter_key"
            ].isin(
                [
                    first,
                    second,
                ]
            ),
            "nq_trade_profit_factor",
        ] = 1.30
        grid.loc[
            grid[
                "parameter_key"
            ].eq(first),
            "nq_net_profit_to_drawdown",
        ] = 2.1
        grid.loc[
            grid[
                "parameter_key"
            ].eq(second),
            "nq_net_profit_to_drawdown",
        ] = 3.0

        selection = select_candidate(
            grid
        )
        self.assertEqual(
            selection.selected_key,
            second,
        )

    def test_no_eligible_candidate_returns_none(
        self,
    ) -> None:
        grid = make_grid()
        grid[
            "nq_trade_profit_factor"
        ] = 0.95
        grid[
            "nq_net_profit_usd"
        ] = -1.0

        selection = select_candidate(
            grid
        )
        self.assertIsNone(
            selection.selected_parameters
        )
        self.assertEqual(
            selection.eligible_count,
            0,
        )
        self.assertEqual(
            selection.stable_eligible_count,
            0,
        )


if __name__ == "__main__":
    unittest.main()
