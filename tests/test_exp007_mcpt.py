from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from exp005_session_mcpt import build_permutation_components
from exp007_mcpt import (
    _run_exp007_mcpt_engine,
    exp007_mcpt_signature,
    reconstruct_permuted_exp007_arrays,
    run_exp007_mcpt,
    run_one_exp007_permutation,
)
from tests.exp007_test_data import make_exp007_one_minute_data


class Exp007McptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data = make_exp007_one_minute_data(
            ["2024-01-03", "2024-01-04", "2024-01-05", "2024-01-08"],
            outcomes=["target", "stop", "time", "target"],
        )

    def test_same_seed_is_exact(self) -> None:
        components = build_permutation_components(self.data)
        first = reconstruct_permuted_exp007_arrays(components, seed=123)
        second = reconstruct_permuted_exp007_arrays(components, seed=123)
        self.assertTrue((first.open == second.open).all())
        self.assertTrue((first.close == second.close).all())

    def test_one_permutation_is_deterministic(self) -> None:
        components = build_permutation_components(self.data)
        first = run_one_exp007_permutation(
            components,
            zero_based_permutation=0,
            base_seed=47,
        )
        second = run_one_exp007_permutation(
            components,
            zero_based_permutation=0,
            base_seed=47,
        )
        self.assertEqual(first, second)

    def test_serial_parallel_results_match(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            serial, serial_p, _ = _run_exp007_mcpt_engine(
                self.data,
                real_trade_profit_factor=1.1,
                permutations=2,
                base_seed=47,
                requested_workers=1,
                checkpoint_file=Path(directory) / "serial.json",
                one_minute_fingerprint="synthetic",
                enforce_locked=False,
            )
            parallel, parallel_p, _ = _run_exp007_mcpt_engine(
                self.data,
                real_trade_profit_factor=1.1,
                permutations=2,
                base_seed=47,
                requested_workers=2,
                checkpoint_file=Path(directory) / "parallel.json",
                one_minute_fingerprint="synthetic",
                enforce_locked=False,
            )
        self.assertEqual(serial.to_dict("records"), parallel.to_dict("records"))
        self.assertEqual(serial_p, parallel_p)

    def test_production_count_is_locked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "1,000"):
                run_exp007_mcpt(
                    self.data,
                    real_trade_profit_factor=1.1,
                    permutations=25,
                    checkpoint_file=Path(directory) / "mcpt.json",
                )

    def test_signature_is_data_specific(self) -> None:
        first = exp007_mcpt_signature(
            one_minute_fingerprint="a",
            permutations=1000,
            base_seed=47,
        )
        second = exp007_mcpt_signature(
            one_minute_fingerprint="b",
            permutations=1000,
            base_seed=47,
        )
        self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
