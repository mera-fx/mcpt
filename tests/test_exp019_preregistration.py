from __future__ import annotations

from datetime import date
import re
import unittest

from exp019_preregistration import (
    CONTRACT_PLAN,
    get_exp019_preregistration,
    validate_exp019_preregistration,
)


class Exp019PreregistrationTests(
    unittest.TestCase
):
    def test_valid(self):
        validate_exp019_preregistration()

    def test_identity_and_stage(self):
        record = get_exp019_preregistration()

        self.assertEqual(
            record["experiment_id"],
            "EXP-019",
        )
        self.assertEqual(
            record["research_status"],
            "PRE_REGISTERED",
        )
        self.assertEqual(
            record["implementation_status"],
            "NOT_IMPLEMENTED",
        )
        self.assertEqual(
            record["ohlcv_bar_values_viewed"],
            "NONE",
        )

    def test_contract_plan_boundaries(self):
        self.assertEqual(
            len(CONTRACT_PLAN),
            66,
        )
        self.assertEqual(
            CONTRACT_PLAN[0][0],
            "NQM10",
        )
        self.assertEqual(
            CONTRACT_PLAN[-1][0],
            "NQU26",
        )
        self.assertEqual(
            CONTRACT_PLAN[0][2],
            "2010-06-06",
        )
        self.assertEqual(
            CONTRACT_PLAN[-1][3],
            "2026-07-24",
        )

    def test_contract_plan_is_quarterly(self):
        canonical_pattern = re.compile(
            r"^NQ[HMUZ][0-9]{2}$"
        )
        raw_pattern = re.compile(
            r"^NQ[HMUZ][0-9]$"
        )

        for (
            canonical,
            raw,
            start,
            end,
            expiration,
        ) in CONTRACT_PLAN:
            self.assertRegex(
                canonical,
                canonical_pattern,
            )
            self.assertRegex(
                raw,
                raw_pattern,
            )
            self.assertLess(
                date.fromisoformat(start),
                date.fromisoformat(end),
            )
            self.assertLessEqual(
                date.fromisoformat(start),
                date.fromisoformat(expiration),
            )

    def test_no_bar_or_download_authority(self):
        record = get_exp019_preregistration()

        estimate = record["cost_estimation"]
        acquisition = record[
            "acquisition_boundary"
        ]

        self.assertTrue(
            estimate["metadata_get_cost_only"]
        )
        self.assertFalse(
            estimate["bar_records_requested"]
        )
        self.assertFalse(
            estimate["bar_records_downloaded"]
        )
        self.assertFalse(
            acquisition["download_authorized"]
        )
        self.assertTrue(
            acquisition[
                "explicit_user_approval_required"
            ]
        )

    def test_cost_cap(self):
        acquisition = get_exp019_preregistration()[
            "acquisition_boundary"
        ]

        self.assertEqual(
            acquisition[
                "maximum_total_cost_usd"
            ],
            35.0,
        )

    def test_mutation_rejected(self):
        record = get_exp019_preregistration()
        record["acquisition_boundary"][
            "download_authorized"
        ] = True

        with self.assertRaisesRegex(
            ValueError,
            "acquisition boundary",
        ):
            validate_exp019_preregistration(
                record
            )


if __name__ == "__main__":
    unittest.main()
