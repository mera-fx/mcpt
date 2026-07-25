from __future__ import annotations

import unittest

from exp020_preregistration import (
    EXP019_CLOSURE_COMMIT,
    HARD_CHECKS,
    get_exp020_preregistration,
    validate_exp020_preregistration,
)


class Exp020PreregistrationTests(unittest.TestCase):
    def test_preregistration_is_valid(self):
        validate_exp020_preregistration()

    def test_identity_is_locked(self):
        record = get_exp020_preregistration()

        self.assertEqual(record["experiment_id"], "EXP-020")
        self.assertEqual(
            record["research_status"],
            "PRE_REGISTERED",
        )
        self.assertEqual(
            record["implementation_status"],
            "NOT_IMPLEMENTED",
        )
        self.assertFalse(
            record[
                "roll_trigger_values_viewed_before_lock"
            ]
        )

    def test_exp019_input_is_frozen(self):
        source = get_exp020_preregistration()[
            "frozen_input"
        ]

        self.assertEqual(
            source["closure_commit"],
            EXP019_CLOSURE_COMMIT,
        )
        self.assertEqual(source["contract_count"], 66)
        self.assertEqual(
            source["record_count"],
            6_276_486,
        )
        self.assertEqual(
            source["hard_failure_count"],
            0,
        )
        self.assertTrue(
            source["source_archive_read_only"]
        )
        self.assertEqual(
            len(source["evidence_hashes"]),
            7,
        )

    def test_primary_method_is_fixed(self):
        scope = get_exp020_preregistration()[
            "construction_scope"
        ]

        self.assertEqual(
            scope["primary_method"],
            (
                "VOLUME_CROSSOVER_2_SESSION_"
                "WITH_CALENDAR_FALLBACK"
            ),
        )
        self.assertTrue(
            scope[
                "primary_method_fixed_before_values"
            ]
        )
        self.assertTrue(
            scope[
                "dynamic_method_selection_prohibited"
            ]
        )
        self.assertFalse(
            scope["open_interest_method_in_scope"]
        )

    def test_volume_trigger_is_locked(self):
        rule = get_exp020_preregistration()[
            "volume_roll_rule"
        ]

        self.assertEqual(
            rule["required_consecutive_sessions"],
            2,
        )
        self.assertTrue(
            rule[
                "known_warning_sessions_excluded_from_trigger"
            ]
        )
        self.assertTrue(
            rule["fallbacks_must_be_disclosed"]
        )
        self.assertTrue(
            rule["intraday_roll_prohibited"]
        )

    def test_session_boundary_is_locked(self):
        session = get_exp020_preregistration()[
            "session_definition"
        ]

        self.assertEqual(
            session["timezone"],
            "America/New_York",
        )
        self.assertEqual(
            session["session_start_local"],
            "18:00:00",
        )
        self.assertTrue(
            session[
                "daylight_saving_time_aware"
            ]
        )
        self.assertTrue(
            session["synthetic_bars_prohibited"]
        )

    def test_four_series_are_required(self):
        self.assertEqual(
            tuple(
                get_exp020_preregistration()[
                    "required_series"
                ]
            ),
            (
                "volume_roll_unadjusted",
                "volume_roll_backward_adjusted",
                "calendar_roll_unadjusted",
                "calendar_roll_backward_adjusted",
            ),
        )

    def test_twenty_hard_checks_are_locked(self):
        self.assertEqual(len(HARD_CHECKS), 20)
        self.assertEqual(
            len(set(HARD_CHECKS)),
            20,
        )
        self.assertIn(
            "independent_rebuild_hashes_match",
            HARD_CHECKS,
        )

    def test_no_strategy_or_trading_permission(self):
        record = get_exp020_preregistration()

        self.assertFalse(
            record["classification"][
                "strategy_use_authorized"
            ]
        )

        for key in (
            "strategy_replay",
            "strategy_optimization",
            "mcpt",
            "bootstrap",
            "walk_forward",
            "paper_trading",
            "live_trading",
        ):
            with self.subTest(key=key):
                self.assertTrue(
                    record["prohibited_actions"][key]
                )

    def test_mutation_is_rejected(self):
        record = get_exp020_preregistration()
        record["volume_roll_rule"][
            "required_consecutive_sessions"
        ] = 1

        with self.assertRaisesRegex(
            ValueError,
            "volume-roll rule",
        ):
            validate_exp020_preregistration(
                record
            )


if __name__ == "__main__":
    unittest.main()
