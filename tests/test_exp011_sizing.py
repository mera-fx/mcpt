from __future__ import annotations

import unittest

import numpy as np

from exp011_sizing import (
    apply_locked_sizing,
    calibrate_target_dollar_risk,
)
from tests.exp011_test_data import (
    EVALUATION_SESSIONS,
    make_base_result,
)


class Exp011SizingTests(unittest.TestCase):
    def test_calibration_uses_old_primary_nq_trades_only(self) -> None:
        calibration = calibrate_target_dollar_risk(make_base_result())
        self.assertEqual(calibration.trade_count, 3)
        self.assertEqual(calibration.target_dollar_risk_usd, 1515.0)
        self.assertEqual(calibration.calibration_end, "2020-12-31")

    def test_reference_signal_cannot_set_target(self) -> None:
        with self.assertRaisesRegex(ValueError, "opening_drive_0p5_time"):
            calibrate_target_dollar_risk(
                make_base_result(
                    signal_id="opening_drive_0p5_1p5r"
                )
            )

    def test_fixed_nq_is_one_contract_and_evaluation_only(self) -> None:
        result = apply_locked_sizing(
            make_base_result(),
            sizing_id="fixed_one_nq",
            target_dollar_risk_usd=1515.0,
            evaluation_session_dates=EVALUATION_SESSIONS,
        )
        self.assertEqual(len(result.signals), 4)
        self.assertTrue(result.signals["contracts"].eq(1.0).all())
        self.assertTrue(
            (result.signals["session_date"] >= "2021-01-04").all()
        )
        self.assertEqual(len(result.equity_curve), 5)

    def test_fractional_nq_caps_and_scales_costs(self) -> None:
        result = apply_locked_sizing(
            make_base_result(),
            sizing_id="fractional_nq_equal_risk",
            target_dollar_risk_usd=1515.0,
            evaluation_session_dates=EVALUATION_SESSIONS,
        )
        self.assertAlmostEqual(result.signals.loc[0, "contracts"], 2.0)
        self.assertAlmostEqual(result.signals.loc[1, "contracts"], 1.0)
        self.assertAlmostEqual(
            result.signals.loc[1, "transaction_cost_usd"], 15.0
        )
        expected = 1515.0 / 3015.0
        self.assertAlmostEqual(
            result.signals.loc[2, "contracts"], expected
        )
        self.assertAlmostEqual(
            result.signals.loc[2, "transaction_cost_usd"],
            15.0 * expected,
        )

    def test_integer_mnq_floors_caps_and_records_zero(self) -> None:
        result = apply_locked_sizing(
            make_base_result(symbol="MNQ"),
            sizing_id="integer_mnq_equal_risk",
            target_dollar_risk_usd=1515.0,
            evaluation_session_dates=EVALUATION_SESSIONS,
        )
        self.assertEqual(
            result.signals["contracts"].tolist(),
            [20.0, 9.0, 5.0, 0.0],
        )
        self.assertEqual(result.summary["skipped_zero_size_trades"], 1)
        self.assertEqual(result.summary["completed_trades"], 3)
        self.assertEqual(
            result.signals.loc[3, "skip_reason"],
            "TARGET_RISK_BELOW_ONE_MNQ_CONTRACT",
        )

    def test_equal_risk_reduces_risk_dispersion(self) -> None:
        fixed = apply_locked_sizing(
            make_base_result(),
            sizing_id="fixed_one_nq",
            target_dollar_risk_usd=1515.0,
            evaluation_session_dates=EVALUATION_SESSIONS,
        )
        fractional = apply_locked_sizing(
            make_base_result(),
            sizing_id="fractional_nq_equal_risk",
            target_dollar_risk_usd=1515.0,
            evaluation_session_dates=EVALUATION_SESSIONS,
        )
        self.assertLess(
            fractional.summary[
                "initial_risk_coefficient_of_variation"
            ],
            fixed.summary["initial_risk_coefficient_of_variation"],
        )
        self.assertTrue(
            np.isfinite(
                fractional.summary["maximum_initial_risk_usd"]
            )
        )

    def test_wrong_market_for_sizing_method_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires MNQ"):
            apply_locked_sizing(
                make_base_result(),
                sizing_id="integer_mnq_equal_risk",
                target_dollar_risk_usd=1515.0,
                evaluation_session_dates=EVALUATION_SESSIONS,
            )

    def test_signal_outside_frozen_session_set_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "absent"):
            apply_locked_sizing(
                make_base_result(),
                sizing_id="fixed_one_nq",
                target_dollar_risk_usd=1515.0,
                evaluation_session_dates=EVALUATION_SESSIONS[:2],
            )


if __name__ == "__main__":
    unittest.main()
