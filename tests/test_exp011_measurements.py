from __future__ import annotations

import unittest

from exp011_measurements import (
    build_exp011_annual_table,
    build_exp011_measurement_table,
    build_exp011_monthly_table,
)
from tests.exp011_test_data import make_sized_results


class Exp011MeasurementTests(unittest.TestCase):
    def test_all_six_rows_are_visible_without_winner(self) -> None:
        table = build_exp011_measurement_table(make_sized_results())
        self.assertEqual(len(table), 6)
        self.assertFalse(table["automatic_winner"].any())
        self.assertTrue(table["composite_score"].isna().all())
        self.assertTrue(
            table["pass_fail_decision"].eq("NOT_APPLICABLE").all()
        )

    def test_missing_row_is_rejected(self) -> None:
        results = make_sized_results()
        results.pop(("opening_drive_0p5_time", "fixed_one_nq"))
        with self.assertRaisesRegex(ValueError, "all six rows"):
            build_exp011_measurement_table(results)

    def test_annual_and_monthly_tables_keep_identity(self) -> None:
        results = make_sized_results()
        annual = build_exp011_annual_table(results)
        monthly = build_exp011_monthly_table(results)
        self.assertEqual(annual["signal_candidate_id"].nunique(), 2)
        self.assertEqual(annual["sizing_id"].nunique(), 3)
        self.assertEqual(monthly["signal_candidate_id"].nunique(), 2)
        self.assertEqual(monthly["sizing_id"].nunique(), 3)


if __name__ == "__main__":
    unittest.main()
