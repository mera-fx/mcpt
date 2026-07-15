from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

import numpy as np

from exp005_session_mcpt import build_permutation_components
from exp006_selection_mcpt import (
    best_nq_selection_statistic,
    mcpt_signature,
    run_one_selection_permutation,
    run_selection_aware_mcpt,
)
from tests.exp006_test_data import make_one_minute_data


class Exp006SelectionMcptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data = make_one_minute_data(
            [
                "2024-01-03",
                "2024-01-04",
                "2024-01-05",
                "2024-01-08",
            ]
        )
        self.components = build_permutation_components(
            self.data
        )

    def test_same_seed_is_exact(self) -> None:
        first = run_one_selection_permutation(
            self.components,
            zero_based_permutation=0,
            base_seed=46,
            minimum_trades=0,
        )
        second = run_one_selection_permutation(
            self.components,
            zero_based_permutation=0,
            base_seed=46,
            minimum_trades=0,
        )
        self.assertEqual(first, second)

    def test_signature_is_data_specific(self) -> None:
        first = mcpt_signature(
            one_minute_fingerprint="abc",
            permutations=1000,
            base_seed=46,
            minimum_trades=1000,
        )
        second = mcpt_signature(
            one_minute_fingerprint="def",
            permutations=1000,
            base_seed=46,
            minimum_trades=1000,
        )
        self.assertNotEqual(first, second)

    def test_serial_parallel_results_match(self) -> None:
        with tempfile.TemporaryDirectory() as first_temp, tempfile.TemporaryDirectory() as second_temp:
            serial, serial_p, _ = run_selection_aware_mcpt(
                self.data,
                real_selection_statistic=0.0,
                permutations=2,
                base_seed=46,
                requested_workers=1,
                checkpoint_file=Path(first_temp) / "checkpoint.json",
                one_minute_fingerprint="test",
                minimum_trades=0,
            )
            parallel, parallel_p, _ = run_selection_aware_mcpt(
                self.data,
                real_selection_statistic=0.0,
                permutations=2,
                base_seed=46,
                requested_workers=2,
                checkpoint_file=Path(second_temp) / "checkpoint.json",
                one_minute_fingerprint="test",
                minimum_trades=0,
            )
        self.assertEqual(serial.to_dict("records"), parallel.to_dict("records"))
        self.assertEqual(serial_p, parallel_p)

    def test_small_serial_run_uses_plus_one_p_value(self) -> None:
        market = __import__(
            "exp005_session_mcpt"
        ).reconstruct_permuted_five_minute_data(
            self.components,
            seed=123,
        )
        real, _, _ = best_nq_selection_statistic(
            market,
            minimum_trades=0,
        )
        with tempfile.TemporaryDirectory() as temp:
            frame, p_value, _ = run_selection_aware_mcpt(
                self.data,
                real_selection_statistic=real,
                permutations=2,
                base_seed=46,
                requested_workers=1,
                checkpoint_file=Path(temp) / "checkpoint.json",
                one_minute_fingerprint="test",
                minimum_trades=0,
            )
        exceedances = int(
            frame["permutation_ge_real"].sum()
        )
        self.assertTrue(
            np.isclose(
                p_value,
                (exceedances + 1) / 3,
            )
        )


if __name__ == "__main__":
    unittest.main()
