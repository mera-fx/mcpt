from __future__ import annotations

import unittest

from exp019_closure import (
    get_exp019_closure,
    validate_exp019_closure,
)


class Exp019ClosureTests(
    unittest.TestCase
):
    def test_closure_is_valid(self):
        validate_exp019_closure()

    def test_classification_is_locked(self):
        record = get_exp019_closure()

        self.assertEqual(
            record["research_status"],
            "REVIEW",
        )
        self.assertEqual(
            record["classification"],
            (
                "QUALIFIED_WITH_KNOWN_"
                "PROVIDER_CONDITIONS"
            ),
        )

    def test_acquisition_is_frozen(self):
        acquisition = (
            get_exp019_closure()[
                "acquisition"
            ]
        )

        self.assertEqual(
            acquisition[
                "successful_downloads"
            ],
            66,
        )
        self.assertEqual(
            acquisition[
                "automatic_retries"
            ],
            0,
        )
        self.assertEqual(
            acquisition[
                "compressed_total_bytes"
            ],
            104491346,
        )
        self.assertEqual(
            len(
                acquisition[
                    "archive_sha256"
                ]
            ),
            64,
        )

    def test_all_hard_checks_passed(self):
        audit = get_exp019_closure()[
            "audit"
        ]

        self.assertEqual(
            audit["contracts_audited"],
            66,
        )
        self.assertEqual(
            audit["records_audited"],
            6276486,
        )
        self.assertEqual(
            audit["hard_checks"],
            17,
        )
        self.assertEqual(
            audit["hard_failure_count"],
            0,
        )

    def test_known_conditions_are_preserved(self):
        record = get_exp019_closure()

        self.assertEqual(
            record["audit"][
                "known_provider_warning_windows"
            ],
            16,
        )
        self.assertTrue(
            record["interpretation"][
                "provider_conditions_must_remain_disclosed"
            ]
        )

    def test_all_evidence_hashes_are_locked(self):
        hashes = get_exp019_closure()[
            "evidence_hashes"
        ]

        self.assertEqual(
            len(hashes),
            7,
        )

        for value in hashes.values():
            self.assertEqual(
                len(value),
                64,
            )

    def test_no_strategy_or_trading_authorization(self):
        interpretation = (
            get_exp019_closure()[
                "interpretation"
            ]
        )

        self.assertFalse(
            interpretation[
                "continuous_series_constructed"
            ]
        )
        self.assertFalse(
            interpretation["strategy_run"]
        )
        self.assertFalse(
            interpretation[
                "strategy_use_authorized"
            ]
        )
        self.assertFalse(
            interpretation[
                "paper_trading_authorized"
            ]
        )
        self.assertFalse(
            interpretation[
                "live_trading_authorized"
            ]
        )

    def test_new_experiment_is_required(self):
        boundary = get_exp019_closure()[
            "next_research_boundary"
        ]

        self.assertTrue(
            boundary["exp019_frozen"]
        )
        self.assertTrue(
            boundary[
                "rerun_exp019_prohibited"
            ]
        )
        self.assertTrue(
            boundary[
                "new_experiment_id_required"
            ]
        )
        self.assertTrue(
            boundary[
                "separate_preregistration_required"
            ]
        )

    def test_mutation_is_rejected(self):
        record = get_exp019_closure()

        record["audit"][
            "hard_failure_count"
        ] = 1

        with self.assertRaisesRegex(
            ValueError,
            "audit result",
        ):
            validate_exp019_closure(
                record
            )


if __name__ == "__main__":
    unittest.main()
