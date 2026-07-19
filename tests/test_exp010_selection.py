from __future__ import annotations

import unittest

import pandas as pd

from exp009_tournament_result import load_candidate_measurements
from exp010_selection import (
    OPENING_DRIVE_IDS,
    locked_opening_drive_candidates,
    select_opening_drive_candidate,
)


def selection_grid() -> pd.DataFrame:
    rows = []
    for index, candidate_id in enumerate(OPENING_DRIVE_IDS):
        rows.append(
            {
                "candidate_id": candidate_id,
                "completed_trades": 200,
                "trade_profit_factor": 1.1 + 0.05 * index,
                "net_profit_usd": 10_000.0 + index,
                "net_profit_to_drawdown": 2.0 + index,
            }
        )
    return pd.DataFrame.from_records(rows)


class Exp010SelectionTests(unittest.TestCase):
    def test_locked_family_contains_exactly_four_candidates(self) -> None:
        candidates = locked_opening_drive_candidates()
        self.assertEqual(len(candidates), 4)
        self.assertEqual(
            {item.candidate_id for item in candidates},
            set(OPENING_DRIVE_IDS),
        )

    def test_highest_eligible_profit_factor_is_selected(self) -> None:
        result = select_opening_drive_candidate(selection_grid())
        self.assertEqual(
            result.selected_candidate.candidate_id,
            "opening_drive_0p75_1p5r",
        )
        self.assertEqual(result.eligible_count, 4)
        self.assertEqual(int(result.scored_candidates["selected"].sum()), 1)

    def test_ineligible_high_profit_factor_is_not_selected(self) -> None:
        grid = selection_grid()
        grid.loc[3, "completed_trades"] = 99
        result = select_opening_drive_candidate(grid)
        self.assertEqual(
            result.selected_candidate.candidate_id,
            "opening_drive_0p75_time",
        )

    def test_tie_break_uses_drawdown_efficiency(self) -> None:
        grid = selection_grid()
        grid["trade_profit_factor"] = 1.2
        result = select_opening_drive_candidate(grid)
        self.assertEqual(
            result.selected_candidate.candidate_id,
            "opening_drive_0p75_1p5r",
        )

    def test_no_eligible_candidate_is_preserved(self) -> None:
        grid = selection_grid()
        grid["net_profit_usd"] = -1.0
        result = select_opening_drive_candidate(grid)
        self.assertIsNone(result.selected_candidate)
        self.assertEqual(result.eligible_count, 0)
        self.assertFalse(result.scored_candidates["selected"].any())

    def test_missing_candidate_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "all four"):
            select_opening_drive_candidate(selection_grid().iloc[:-1])

    def test_frozen_exp009_measurements_select_time_exit_leader(
        self,
    ) -> None:
        frozen = load_candidate_measurements()
        opening_drive = frozen.loc[
            frozen["family_id"].eq("opening_drive_continuation")
        ]
        result = select_opening_drive_candidate(opening_drive)
        self.assertEqual(
            result.selected_candidate.candidate_id,
            "opening_drive_0p5_time",
        )


if __name__ == "__main__":
    unittest.main()
