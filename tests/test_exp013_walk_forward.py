from __future__ import annotations

from unittest.mock import patch
import unittest

import numpy as np
import pandas as pd

from exp013_selection import FINALIST_IDS
from exp013_walk_forward import run_exp013_anchored_walk_forward
from tests.exp012_test_data import make_exp012_arrays


def _arrays():
    arrays = make_exp012_arrays(6)
    dates = np.array(
        [
            "2020-06-01",
            "2021-06-01",
            "2022-06-01",
            "2023-06-01",
            "2024-06-03",
            "2025-06-02",
        ],
        dtype=object,
    )
    arrays.cash.session_dates[:] = dates
    arrays.cash.years[:] = pd.to_datetime(dates).year.to_numpy(dtype=int)
    return arrays


def _grid(*args, **kwargs):
    return pd.DataFrame(
        [
            {
                "candidate_id": candidate_id,
                "completed_trades": 25,
                "trade_profit_factor": 1.3 - index * 0.05,
                "net_profit_usd": 1000.0,
                "net_profit_to_drawdown": 2.0,
            }
            for index, candidate_id in enumerate(FINALIST_IDS)
        ]
    )


class Exp013WalkForwardTests(unittest.TestCase):
    def test_four_anchored_folds_reselect_and_measure(self) -> None:
        fake = type(
            "FakeResult",
            (),
            {
                "summary": {
                    "completed_trades": 10,
                    "trade_profit_factor": 1.1,
                    "net_profit_usd": 100.0,
                    "average_trade_usd": 10.0,
                }
            },
        )()
        with (
            patch(
                "exp013_walk_forward.evaluate_exp013_finalists",
                side_effect=_grid,
            ) as evaluate,
            patch(
                "exp013_walk_forward.run_exp012_candidate",
                return_value=fake,
            ),
        ):
            result = run_exp013_anchored_walk_forward(_arrays())
        self.assertEqual(len(result.folds), 4)
        self.assertEqual(result.profitable_test_folds, 4)
        self.assertEqual(result.combined_test_net_profit_usd, 400.0)
        self.assertEqual(evaluate.call_count, 4)
        for row in result.folds.itertuples():
            self.assertLess(
                pd.Timestamp(row.training_end),
                pd.Timestamp(row.test_start),
            )

    def test_no_eligible_candidate_is_preserved(self) -> None:
        def ineligible(*args, **kwargs):
            frame = _grid()
            frame["net_profit_usd"] = -1.0
            return frame

        with patch(
            "exp013_walk_forward.evaluate_exp013_finalists",
            side_effect=ineligible,
        ):
            result = run_exp013_anchored_walk_forward(_arrays())
        self.assertTrue(result.folds["selected_candidate_id"].eq("").all())
        self.assertTrue(result.folds["test_completed_trades"].eq(0).all())


if __name__ == "__main__":
    unittest.main()
