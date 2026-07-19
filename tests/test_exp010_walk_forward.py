from __future__ import annotations

from unittest.mock import patch
import unittest

import numpy as np
import pandas as pd

from exp010_selection import select_opening_drive_candidate
from exp010_walk_forward import run_exp010_anchored_walk_forward
from tests.exp009_test_data import make_exp009_arrays


def make_yearly_arrays():
    arrays = make_exp009_arrays(7)
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
    arrays.session_dates[:] = dates
    arrays.years[:] = pd.to_datetime(dates).year.to_numpy(dtype=int)
    return arrays


def fake_grid(*args, **kwargs):
    ids = [
        "opening_drive_0p5_time",
        "opening_drive_0p5_1p5r",
        "opening_drive_0p75_time",
        "opening_drive_0p75_1p5r",
    ]
    return pd.DataFrame(
        [
            {
                "candidate_id": candidate_id,
                "completed_trades": 150,
                "trade_profit_factor": 1.3 - index * 0.01,
                "net_profit_usd": 1000.0,
                "net_profit_to_drawdown": 2.0,
            }
            for index, candidate_id in enumerate(ids)
        ]
    )


class Exp010WalkForwardTests(unittest.TestCase):
    def test_five_anchored_folds_run(self) -> None:
        fake_result = type(
            "FakeResult",
            (),
            {
                "summary": {
                    "completed_trades": 25,
                    "trade_profit_factor": 1.1,
                    "net_profit_usd": 500.0,
                    "average_trade_usd": 20.0,
                }
            },
        )()
        with (
            patch(
                "exp010_walk_forward.evaluate_opening_drive_grid",
                side_effect=fake_grid,
            ) as evaluate,
            patch(
                "exp010_walk_forward.select_opening_drive_candidate",
                side_effect=select_opening_drive_candidate,
            ) as select,
            patch(
                "exp010_walk_forward.run_exp009_candidate",
                return_value=fake_result,
            ),
        ):
            result = run_exp010_anchored_walk_forward(
                make_yearly_arrays()
            )
        self.assertEqual(len(result.folds), 5)
        self.assertEqual(result.profitable_test_folds, 5)
        self.assertEqual(result.combined_test_net_profit_usd, 2500.0)
        self.assertEqual(evaluate.call_count, 5)
        self.assertEqual(select.call_count, 5)

    def test_training_always_ends_before_test(self) -> None:
        fake_result = type(
            "FakeResult",
            (),
            {
                "summary": {
                    "completed_trades": 1,
                    "trade_profit_factor": 1.1,
                    "net_profit_usd": 1.0,
                    "average_trade_usd": 1.0,
                }
            },
        )()
        with (
            patch(
                "exp010_walk_forward.evaluate_opening_drive_grid",
                side_effect=fake_grid,
            ),
            patch(
                "exp010_walk_forward.run_exp009_candidate",
                return_value=fake_result,
            ),
        ):
            result = run_exp010_anchored_walk_forward(
                make_yearly_arrays()
            )
        for row in result.folds.itertuples():
            self.assertLess(
                pd.Timestamp(row.training_end),
                pd.Timestamp(row.test_start),
            )

    def test_no_eligible_fold_is_recorded_not_hidden(self) -> None:
        def ineligible(*args, **kwargs):
            grid = fake_grid()
            grid["net_profit_usd"] = -1.0
            return grid

        with patch(
            "exp010_walk_forward.evaluate_opening_drive_grid",
            side_effect=ineligible,
        ):
            result = run_exp010_anchored_walk_forward(
                make_yearly_arrays()
            )
        self.assertTrue(result.folds["selected_candidate_id"].eq("").all())
        self.assertTrue(result.folds["test_completed_trades"].eq(0).all())


if __name__ == "__main__":
    unittest.main()
