from __future__ import annotations

from copy import deepcopy
import unittest

from exp005_quick_transfer_result import (
    EXPECTED_FILE_SHA256,
    get_exp005_quick_transfer_result,
    load_tracked_result,
    sha256_file,
    TRACKED_RESULT_FILE,
    validate_exp005_quick_transfer_result,
)


class Exp005QuickTransferResultTests(
    unittest.TestCase
):
    def test_frozen_record_is_valid(
        self,
    ) -> None:
        validate_exp005_quick_transfer_result()

    def test_tracked_json_hash_is_frozen(
        self,
    ) -> None:
        self.assertEqual(
            sha256_file(TRACKED_RESULT_FILE),
            EXPECTED_FILE_SHA256,
        )
        load_tracked_result()

    def test_metric_change_is_rejected(
        self,
    ) -> None:
        changed = get_exp005_quick_transfer_result()
        changed["results"]["NQ"][
            "net_profit_usd"
        ] += 1.0

        with self.assertRaisesRegex(
            ValueError,
            "net_profit_usd changed",
        ):
            validate_exp005_quick_transfer_result(
                changed
            )

    def test_confirmation_access_change_is_rejected(
        self,
    ) -> None:
        changed = get_exp005_quick_transfer_result()
        changed[
            "confirmation_period_accessed"
        ] = True

        with self.assertRaisesRegex(
            ValueError,
            "access protections changed",
        ):
            validate_exp005_quick_transfer_result(
                changed
            )


if __name__ == "__main__":
    unittest.main()
