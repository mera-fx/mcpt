from __future__ import annotations

import unittest

from exp011_bootstrap import paired_sizing_bootstrap
from tests.exp011_test_data import make_sized_results


class Exp011BootstrapTests(unittest.TestCase):
    def test_bootstrap_is_deterministic_and_paired(self) -> None:
        results = make_sized_results()
        baseline = results[
            ("opening_drive_0p5_time", "fixed_one_nq")
        ]
        comparison = results[
            ("opening_drive_0p5_time", "fractional_nq_equal_risk")
        ]
        first = paired_sizing_bootstrap(
            baseline, comparison, resamples=100, seed=5111
        )
        second = paired_sizing_bootstrap(
            baseline, comparison, resamples=100, seed=5111
        )
        self.assertEqual(first, second)
        self.assertTrue(first["paired_by_session"])
        self.assertFalse(first["decision_gate"])
        self.assertFalse(first["signal_edge_confirmation"])

    def test_integer_mnq_can_be_scaled_to_nq_dollars(self) -> None:
        results = make_sized_results()
        diagnostic = paired_sizing_bootstrap(
            results[("opening_drive_0p5_time", "fixed_one_nq")],
            results[
                ("opening_drive_0p5_time", "integer_mnq_equal_risk")
            ],
            comparison_scale_to_nq=10.0,
            resamples=50,
        )
        self.assertEqual(diagnostic["comparison_scale_to_nq"], 10.0)
        self.assertEqual(diagnostic["evaluation_sessions"], 5)

    def test_different_signals_cannot_be_paired(self) -> None:
        results = make_sized_results()
        with self.assertRaisesRegex(ValueError, "same signal"):
            paired_sizing_bootstrap(
                results[
                    ("opening_drive_0p5_time", "fixed_one_nq")
                ],
                results[
                    (
                        "opening_drive_0p5_1p5r",
                        "fractional_nq_equal_risk",
                    )
                ],
                resamples=10,
            )


if __name__ == "__main__":
    unittest.main()
