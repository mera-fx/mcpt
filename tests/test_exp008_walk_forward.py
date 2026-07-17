from __future__ import annotations

from unittest.mock import patch
import unittest

import numpy as np
import pandas as pd

from exp008_candidate_scoring import (
    CandidateSelection,
)
from exp008_orb import (
    Exp008Arrays,
    Exp008Parameters,
)
from exp008_walk_forward import (
    run_exp008_anchored_walk_forward,
)


def make_arrays() -> Exp008Arrays:
    dates = np.array(
        [
            "2019-06-03",
            "2020-06-03",
            "2021-06-03",
            "2022-06-03",
            "2023-06-05",
            "2024-06-03",
            "2025-06-02",
        ],
        dtype=object,
    )
    shape = (
        len(dates),
        390,
    )
    base = np.full(
        shape,
        100.0,
    )
    return Exp008Arrays(
        session_dates=dates,
        years=pd.to_datetime(
            dates
        ).year.to_numpy(dtype=int),
        open=base.copy(),
        high=base.copy(),
        low=base.copy(),
        close=base.copy(),
        volume=np.ones(shape),
        index_ns=None,
    )


def fake_selection(
    grid: pd.DataFrame,
) -> CandidateSelection:
    parameters = Exp008Parameters(
        30,
        1.0,
        "14:00",
    )
    scored = grid.copy()
    scored["eligible"] = True
    scored["neighbor_stable"] = True
    scored["selected"] = (
        scored[
            "parameter_key"
        ].eq(parameters.key)
    )
    return CandidateSelection(
        selected_parameters=parameters,
        scored_grid=scored,
        eligible_count=1,
        stable_eligible_count=1,
    )


class Exp008WalkForwardTests(
    unittest.TestCase
):
    def setUp(self) -> None:
        self.arrays = make_arrays()
        self.grid = pd.DataFrame(
            [
                {
                    "parameter_key": (
                        "or30_target1p0_flat1400"
                    ),
                    "opening_range_minutes": 30,
                    "reward_to_risk": 1.0,
                    "forced_flat_time_new_york": (
                        "14:00"
                    ),
                    "nq_trade_profit_factor": 1.2,
                    "nq_net_profit_usd": 1000.0,
                    "nq_net_profit_to_drawdown": 2.0,
                    "nq_completed_trades": 100,
                }
            ]
        )

    def test_five_anchored_folds_run(
        self,
    ) -> None:
        with (
            patch(
                "exp008_walk_forward.evaluate_nq_grid",
                return_value=self.grid,
            ),
            patch(
                "exp008_walk_forward.select_candidate",
                side_effect=fake_selection,
            ),
            patch(
                "exp008_walk_forward.run_candidate_summary",
                return_value={
                    "completed_trades": 25,
                    "trade_profit_factor": 1.1,
                    "net_profit_usd": 500.0,
                    "average_trade_usd": 20.0,
                },
            ),
        ):
            result = (
                run_exp008_anchored_walk_forward(
                    self.arrays
                )
            )

        self.assertEqual(
            len(result.folds),
            5,
        )
        self.assertEqual(
            result.profitable_test_folds,
            5,
        )
        self.assertEqual(
            result.combined_test_net_profit_usd,
            2500.0,
        )

    def test_training_end_precedes_test_start(
        self,
    ) -> None:
        with (
            patch(
                "exp008_walk_forward.evaluate_nq_grid",
                return_value=self.grid,
            ),
            patch(
                "exp008_walk_forward.select_candidate",
                side_effect=fake_selection,
            ),
            patch(
                "exp008_walk_forward.run_candidate_summary",
                return_value={
                    "completed_trades": 25,
                    "trade_profit_factor": 1.1,
                    "net_profit_usd": 500.0,
                    "average_trade_usd": 20.0,
                },
            ),
        ):
            result = (
                run_exp008_anchored_walk_forward(
                    self.arrays
                )
            )

        for row in result.folds.itertuples():
            self.assertLess(
                pd.Timestamp(
                    row.train_end
                ),
                pd.Timestamp(
                    row.test_start
                ),
            )

    def test_selection_is_repeated_per_fold(
        self,
    ) -> None:
        with (
            patch(
                "exp008_walk_forward.evaluate_nq_grid",
                return_value=self.grid,
            ) as evaluate,
            patch(
                "exp008_walk_forward.select_candidate",
                side_effect=fake_selection,
            ) as select,
            patch(
                "exp008_walk_forward.run_candidate_summary",
                return_value={
                    "completed_trades": 25,
                    "trade_profit_factor": 1.1,
                    "net_profit_usd": 500.0,
                    "average_trade_usd": 20.0,
                },
            ),
        ):
            run_exp008_anchored_walk_forward(
                self.arrays
            )

        self.assertEqual(
            evaluate.call_count,
            5,
        )
        self.assertEqual(
            select.call_count,
            5,
        )


if __name__ == "__main__":
    unittest.main()
