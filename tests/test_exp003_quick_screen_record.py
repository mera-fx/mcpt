from __future__ import annotations

import unittest

from exp003_quick_screen_record import (
    get_exp003_quick_screen_record,
    validate_exp003_quick_screen_record,
)


class Exp003QuickScreenRecordTests(
    unittest.TestCase
):
    def test_tracked_record_is_valid(
        self,
    ) -> None:
        validate_exp003_quick_screen_record()

    def test_every_quick_gate_passed(
        self,
    ) -> None:
        record = get_exp003_quick_screen_record()

        self.assertTrue(record["passed"])
        self.assertEqual(
            record["failed_gates"],
            [],
        )

        self.assertTrue(
            all(
                gate["passed"]
                for gate
                in record["gates"].values()
            )
        )

    def test_record_advances_to_full_validation(
        self,
    ) -> None:
        record = get_exp003_quick_screen_record()

        self.assertEqual(
            record["decision"],
            "PASS_TO_FULL_VALIDATION",
        )


if __name__ == "__main__":
    unittest.main()
