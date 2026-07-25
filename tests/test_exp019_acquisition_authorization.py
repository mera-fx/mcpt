from __future__ import annotations

import unittest

from exp019_acquisition_authorization import (
    get_exp019_acquisition_authorization,
    validate_exp019_acquisition_authorization,
)


class Exp019AcquisitionAuthorizationTests(
    unittest.TestCase
):
    def test_authorization_is_valid(self):
        validate_exp019_acquisition_authorization()

    def test_exact_quote_and_cap_are_locked(self):
        record = get_exp019_acquisition_authorization()
        estimate = record["cost_estimate"]

        self.assertEqual(
            estimate["contract_count"],
            66,
        )
        self.assertEqual(
            estimate["quoted_total_usd"],
            22.914098,
        )
        self.assertEqual(
            estimate["maximum_total_cost_usd"],
            35.0,
        )
        self.assertTrue(
            estimate["within_locked_cap"]
        )

    def test_explicit_acquisition_is_authorized(self):
        record = get_exp019_acquisition_authorization()
        authorization = record[
            "authorized_acquisition"
        ]

        self.assertTrue(
            authorization[
                "explicit_user_approval"
            ]
        )
        self.assertTrue(
            authorization[
                "exact_locked_windows_only"
            ]
        )
        self.assertEqual(
            authorization[
                "maximum_successful_downloads"
            ],
            66,
        )

    def test_retries_and_overwrites_are_blocked(self):
        record = get_exp019_acquisition_authorization()

        self.assertTrue(
            record["authorized_acquisition"][
                "automatic_retry_prohibited"
            ]
        )
        self.assertTrue(
            record["authorized_acquisition"][
                "stop_on_first_error"
            ]
        )
        self.assertTrue(
            record["prohibited_actions"][
                "overwrite_completed_file"
            ]
        )

    def test_archive_remains_unqualified(self):
        boundary = (
            get_exp019_acquisition_authorization()[
                "post_acquisition_boundary"
            ]
        )

        self.assertFalse(
            boundary["archive_qualified"]
        )
        self.assertTrue(
            boundary[
                "audit_required_before_use"
            ]
        )
        self.assertFalse(
            boundary[
                "strategy_use_authorized"
            ]
        )

    def test_quote_hashes_are_recorded(self):
        estimate = (
            get_exp019_acquisition_authorization()[
                "cost_estimate"
            ]
        )

        self.assertEqual(
            len(
                estimate[
                    "cost_json_sha256"
                ]
            ),
            64,
        )
        self.assertEqual(
            len(
                estimate[
                    "cost_csv_sha256"
                ]
            ),
            64,
        )

    def test_mutation_is_rejected(self):
        record = get_exp019_acquisition_authorization()

        record["authorized_acquisition"][
            "maximum_total_cost_usd"
        ] = 40.0

        with self.assertRaisesRegex(
            ValueError,
            "authorization",
        ):
            validate_exp019_acquisition_authorization(
                record
            )


if __name__ == "__main__":
    unittest.main()
