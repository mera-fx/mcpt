from __future__ import annotations

import unittest

import pandas as pd

from exp013_selection import (
    FINALIST_IDS,
    locked_exp013_candidates,
    select_exp013_measurement_leader,
    selected_exp013_row,
)


def _table() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "candidate_id": candidate_id,
                "completed_trades": 100 - index,
                "trade_profit_factor": 1.2 + index * 0.1,
                "net_profit_usd": 1000.0 + index,
                "net_profit_to_drawdown": 2.0,
            }
            for index, candidate_id in enumerate(FINALIST_IDS)
        ]
    )


class Exp013SelectionTests(unittest.TestCase):
    def test_exact_three_finalists_are_locked(self) -> None:
        candidates = locked_exp013_candidates()
        self.assertEqual(
            tuple(value.candidate_id for value in candidates),
            FINALIST_IDS,
        )

    def test_rank_selects_highest_eligible_profit_factor(self) -> None:
        selection = select_exp013_measurement_leader(_table())
        self.assertEqual(selection.eligible_count, 3)
        self.assertEqual(selection.selected_candidate_id, FINALIST_IDS[-1])
        self.assertEqual(
            selected_exp013_row(selection)["candidate_id"],
            FINALIST_IDS[-1],
        )

    def test_minimum_twenty_trades_is_enforced(self) -> None:
        table = _table()
        table.loc[
            table["candidate_id"].eq(FINALIST_IDS[-1]),
            "completed_trades",
        ] = 19
        selection = select_exp013_measurement_leader(table)
        self.assertEqual(selection.eligible_count, 2)
        self.assertNotEqual(selection.selected_candidate_id, FINALIST_IDS[-1])

    def test_incomplete_shortlist_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "all three"):
            select_exp013_measurement_leader(_table().iloc[:-1])


if __name__ == "__main__":
    unittest.main()
