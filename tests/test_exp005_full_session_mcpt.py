from __future__ import annotations

import unittest

import numpy as np

from exp005_full_session_mcpt import (
    FULL_PERMUTATIONS,
    LOCKED_BASE_SEED,
    full_mcpt_p_value,
    full_mcpt_signature,
    validate_full_mcpt_request,
)


class Exp005FullSessionMcptTests(
    unittest.TestCase
):
    def test_request_is_locked_to_1000_and_seed_45(
        self,
    ) -> None:
        validate_full_mcpt_request(
            permutations=FULL_PERMUTATIONS,
            base_seed=LOCKED_BASE_SEED,
        )

        with self.assertRaisesRegex(
            ValueError,
            "1,000",
        ):
            validate_full_mcpt_request(
                permutations=999,
                base_seed=45,
            )

        with self.assertRaisesRegex(
            ValueError,
            "seed",
        ):
            validate_full_mcpt_request(
                permutations=1000,
                base_seed=46,
            )

    def test_p_value_uses_locked_plus_one_formula(
        self,
    ) -> None:
        values = np.zeros(
            FULL_PERMUTATIONS,
            dtype=float,
        )
        values[:49] = 2.0

        p_value, exceedances, flags = (
            full_mcpt_p_value(
                permutation_profit_factors=values,
                real_trade_profit_factor=1.0,
            )
        )

        self.assertEqual(exceedances, 49)
        self.assertEqual(int(flags.sum()), 49)
        self.assertAlmostEqual(
            p_value,
            50.0 / 1001.0,
        )

    def test_equal_permutation_counts_as_exceedance(
        self,
    ) -> None:
        values = np.zeros(
            FULL_PERMUTATIONS,
            dtype=float,
        )
        values[0] = 1.05

        p_value, exceedances, _ = (
            full_mcpt_p_value(
                permutation_profit_factors=values,
                real_trade_profit_factor=1.05,
            )
        )

        self.assertEqual(exceedances, 1)
        self.assertAlmostEqual(
            p_value,
            2.0 / 1001.0,
        )

    def test_signature_is_stable_and_data_specific(
        self,
    ) -> None:
        first = full_mcpt_signature(
            one_minute_fingerprint="abc",
        )
        second = full_mcpt_signature(
            one_minute_fingerprint="abc",
        )
        changed = full_mcpt_signature(
            one_minute_fingerprint="def",
        )

        self.assertEqual(first, second)
        self.assertNotEqual(first, changed)


if __name__ == "__main__":
    unittest.main()
