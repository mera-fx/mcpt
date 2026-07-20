from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from exp013_selection import FINALIST_IDS
from exp013_selection_mcpt import (
    _run_exp013_mcpt_engine,
    build_exp013_permutation_components,
    exp013_mcpt_signature,
    reconstruct_permuted_exp013_arrays,
    run_one_exp013_permutation,
)
from tests.exp012_test_data import make_extended_frame


class Exp013SelectionMcptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dates = [
            "2024-01-03",
            "2024-01-04",
            "2024-01-05",
        ]
        self.data = make_extended_frame(self.dates)

    def test_components_cover_all_1320_exact_slots(self) -> None:
        components = build_exp013_permutation_components(
            self.data, calendar_session_dates=self.dates
        )
        self.assertEqual(components.open_gap.shape, (3, 1320))
        self.assertEqual(components.volume.shape, (3, 1320))

    def test_same_seed_reconstructs_identical_extended_arrays(self) -> None:
        components = build_exp013_permutation_components(
            self.data, calendar_session_dates=self.dates
        )
        first = reconstruct_permuted_exp013_arrays(components, seed=123)
        second = reconstruct_permuted_exp013_arrays(components, seed=123)
        self.assertTrue((first.cash.open == second.cash.open).all())
        self.assertTrue((first.premarket_high == second.premarket_high).all())
        self.assertEqual(first.cash.open.shape, (3, 390))

    def test_one_permutation_runs_full_search_and_fixed_candidates(self) -> None:
        components = build_exp013_permutation_components(
            self.data, calendar_session_dates=self.dates
        )
        first = run_one_exp013_permutation(
            components, zero_based_permutation=0, base_seed=53
        )
        second = run_one_exp013_permutation(
            components, zero_based_permutation=0, base_seed=53
        )
        self.assertEqual(first, second)
        self.assertIn("maximum_trade_profit_factor", first)
        for candidate_id in FINALIST_IDS:
            self.assertIn(
                f"fixed_{candidate_id}_profit_factor", first
            )

    def test_serial_parallel_results_match_exactly(self) -> None:
        real_fixed = {value: 100.0 for value in FINALIST_IDS}
        with tempfile.TemporaryDirectory() as directory:
            serial = _run_exp013_mcpt_engine(
                self.data,
                real_maximum_profit_factor=100.0,
                real_fixed_profit_factors=real_fixed,
                requested_workers=1,
                checkpoint_file=Path(directory) / "serial.json",
                one_minute_fingerprint="synthetic",
                permutations=2,
                base_seed=53,
                calendar_session_dates=self.dates,
            )
            parallel = _run_exp013_mcpt_engine(
                self.data,
                real_maximum_profit_factor=100.0,
                real_fixed_profit_factors=real_fixed,
                requested_workers=2,
                checkpoint_file=Path(directory) / "parallel.json",
                one_minute_fingerprint="synthetic",
                permutations=2,
                base_seed=53,
                calendar_session_dates=self.dates,
            )
        self.assertEqual(
            serial[0].to_dict("records"),
            parallel[0].to_dict("records"),
        )
        self.assertEqual(serial[1], parallel[1])
        self.assertEqual(serial[2], parallel[2])

    def test_plus_one_formula_and_signature(self) -> None:
        real_fixed = {value: 100.0 for value in FINALIST_IDS}
        with tempfile.TemporaryDirectory() as directory:
            frame, primary, fixed, _ = _run_exp013_mcpt_engine(
                self.data,
                real_maximum_profit_factor=100.0,
                real_fixed_profit_factors=real_fixed,
                requested_workers=1,
                checkpoint_file=Path(directory) / "formula.json",
                one_minute_fingerprint="synthetic",
                permutations=2,
                base_seed=53,
                calendar_session_dates=self.dates,
            )
        self.assertEqual(int(frame["maximum_ge_real"].sum()), 0)
        self.assertEqual(primary, 1 / 3)
        self.assertTrue(all(value == 1 / 3 for value in fixed.values()))
        self.assertNotEqual(
            exp013_mcpt_signature(
                one_minute_fingerprint="a",
                permutations=1000,
                base_seed=53,
            ),
            exp013_mcpt_signature(
                one_minute_fingerprint="b",
                permutations=1000,
                base_seed=53,
            ),
        )


if __name__ == "__main__":
    unittest.main()
