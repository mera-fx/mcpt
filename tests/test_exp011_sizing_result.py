from __future__ import annotations

from copy import deepcopy
import unittest

from exp011_sizing_result import (
    EXPECTED_MANIFEST_SHA256,
    build_exp011_result_manifest,
    get_expected_exp011_measurements,
    load_exp011_sizing_result,
    validate_exp011_sizing_result,
    verify_local_exp011_sizing_result,
)
from exp010_validation_result import canonical_object_sha256


class Exp011SizingResultTests(unittest.TestCase):
    def test_local_corrected_result_is_valid(self) -> None:
        verify_local_exp011_sizing_result()

    def test_result_manifest_is_frozen(self) -> None:
        self.assertEqual(
            canonical_object_sha256(build_exp011_result_manifest()),
            EXPECTED_MANIFEST_SHA256,
        )

    def test_all_six_measurements_are_frozen(self) -> None:
        expected = get_expected_exp011_measurements()
        self.assertEqual(len(expected), 6)
        self.assertIn(
            ("opening_drive_0p5_time", "fixed_one_nq"),
            expected,
        )
        self.assertIn(
            (
                "opening_drive_0p5_1p5r",
                "integer_mnq_equal_risk",
            ),
            expected,
        )

    def test_unit_correction_and_no_trading_are_frozen(self) -> None:
        record = load_exp011_sizing_result()
        self.assertEqual(
            record["unit_correction"]["corrected_mnq_scale"], 1.0
        )
        self.assertFalse(record["paper_trading_authorized"])
        self.assertFalse(record["live_trading_authorized"])

    def test_measurement_mutation_is_rejected(self) -> None:
        changed = deepcopy(load_exp011_sizing_result())
        changed["results"][0]["net_profit_usd"] += 1.0
        with self.assertRaisesRegex(ValueError, "net_profit"):
            validate_exp011_sizing_result(changed)


if __name__ == "__main__":
    unittest.main()
