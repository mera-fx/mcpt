from __future__ import annotations

import unittest

from exp006_orb import prepare_orb_arrays
from exp006_walk_forward import (
    run_anchored_walk_forward,
)
from tests.exp006_test_data import (
    make_five_minute_data,
)


class Exp006WalkForwardTests(unittest.TestCase):
    def test_five_anchored_folds_run(self) -> None:
        session_dates = []
        for year in range(2019, 2026):
            session_dates.extend(
                [f"{year}-01-03", f"{year}-06-03"]
            )
        nq = prepare_orb_arrays(
            make_five_minute_data(
                session_dates,
                pattern="long",
            )
        )
        mnq = prepare_orb_arrays(
            make_five_minute_data(
                session_dates,
                pattern="long",
            )
        )
        result = run_anchored_walk_forward(nq, mnq)
        self.assertEqual(len(result.folds), 5)
        self.assertEqual(
            sorted(result.folds["test_start"].str[:4].tolist()),
            ["2021", "2022", "2023", "2024", "2025"],
        )
        self.assertTrue(
            result.folds["nq_test_profitable"].all()
        )

    def test_training_ends_before_test_starts(self) -> None:
        session_dates = []
        for year in range(2019, 2026):
            session_dates.extend(
                [f"{year}-01-03", f"{year}-06-03"]
            )
        arrays = prepare_orb_arrays(
            make_five_minute_data(session_dates)
        )
        result = run_anchored_walk_forward(
            arrays,
            arrays,
        )
        for row in result.folds.itertuples(index=False):
            self.assertLess(row.train_end, row.test_start)


if __name__ == "__main__":
    unittest.main()
