from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from exp005_session_mcpt import build_permutation_components
from exp010_selection_mcpt import (
    _run_exp010_mcpt_engine,
    exp010_mcpt_signature,
    reconstruct_permuted_exp010_arrays,
    run_exp010_selection_mcpt,
    run_one_exp010_permutation,
)
from tests.exp009_test_data import make_exp009_one_minute_data


class Exp010SelectionMcptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data = make_exp009_one_minute_data(
            [
                "2024-01-03",
                "2024-01-04",
                "2024-01-05",
                "2024-01-08",
            ]
        )

    def test_same_seed_reconstructs_exact_arrays(self) -> None:
        components = build_permutation_components(self.data)
        first = reconstruct_permuted_exp010_arrays(components, seed=123)
        second = reconstruct_permuted_exp010_arrays(components, seed=123)
        self.assertTrue((first.open == second.open).all())
        self.assertTrue((first.close == second.close).all())
        self.assertEqual(first.open_5m.shape, (4, 78))

    def test_one_permutation_runs_all_four_candidates(self) -> None:
        components = build_permutation_components(self.data)
        first = run_one_exp010_permutation(
            components,
            zero_based_permutation=0,
            base_seed=50,
        )
        second = run_one_exp010_permutation(
            components,
            zero_based_permutation=0,
            base_seed=50,
        )
        self.assertEqual(first, second)
        self.assertIn("selected_trade_profit_factor", first)
        self.assertIn("fixed_reference_trade_profit_factor", first)
        self.assertIn("eligible_candidates", first)

    def test_serial_parallel_results_match(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            serial = _run_exp010_mcpt_engine(
                self.data,
                real_selected_trade_profit_factor=1.1,
                real_fixed_reference_trade_profit_factor=1.1,
                permutations=2,
                base_seed=50,
                requested_workers=1,
                checkpoint_file=Path(directory) / "serial.json",
                one_minute_fingerprint="synthetic",
                enforce_locked=False,
            )
            parallel = _run_exp010_mcpt_engine(
                self.data,
                real_selected_trade_profit_factor=1.1,
                real_fixed_reference_trade_profit_factor=1.1,
                permutations=2,
                base_seed=50,
                requested_workers=2,
                checkpoint_file=Path(directory) / "parallel.json",
                one_minute_fingerprint="synthetic",
                enforce_locked=False,
            )
        self.assertEqual(
            serial[0].to_dict("records"),
            parallel[0].to_dict("records"),
        )
        self.assertEqual(serial[1:3], parallel[1:3])

    def test_production_count_is_locked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "1,000"):
                run_exp010_selection_mcpt(
                    self.data,
                    real_selected_trade_profit_factor=1.1,
                    real_fixed_reference_trade_profit_factor=1.1,
                    permutations=25,
                    checkpoint_file=Path(directory) / "mcpt.json",
                )

    def test_signature_is_data_specific(self) -> None:
        first = exp010_mcpt_signature(
            one_minute_fingerprint="a",
            permutations=1000,
            base_seed=50,
        )
        second = exp010_mcpt_signature(
            one_minute_fingerprint="b",
            permutations=1000,
            base_seed=50,
        )
        self.assertNotEqual(first, second)

    def test_both_p_values_use_plus_one_formula(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            frame, selected_p, fixed_p, _ = _run_exp010_mcpt_engine(
                self.data,
                real_selected_trade_profit_factor=100.0,
                real_fixed_reference_trade_profit_factor=100.0,
                permutations=2,
                base_seed=50,
                requested_workers=1,
                checkpoint_file=Path(directory) / "formula.json",
                one_minute_fingerprint="synthetic",
                enforce_locked=False,
            )
        self.assertEqual(int(frame["selected_ge_real"].sum()), 0)
        self.assertEqual(int(frame["fixed_reference_ge_real"].sum()), 0)
        self.assertEqual(selected_p, 1.0 / 3.0)
        self.assertEqual(fixed_p, 1.0 / 3.0)


if __name__ == "__main__":
    unittest.main()
