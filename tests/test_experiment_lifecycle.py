from __future__ import annotations

import unittest

from build_research_dashboard import (
    build_lifecycle_only_record,
)
from experiment_decisions import (
    get_experiment_decision,
)
from experiment_lifecycle import (
    ALLOWED_STAGES,
    get_experiment_lifecycle,
    list_experiment_lifecycles,
    validate_lifecycle_registry,
)


class LifecycleRegistryTests(unittest.TestCase):
    def test_exp005_lifecycle_records_review_acceptance(
            self,
        ) -> None:
            record = get_experiment_lifecycle(
                "EXP-005"
            )
            self.assertIn(
                "12 locked operational-quality",
                record.stage_reason,
            )
            self.assertIn(
                "12 calendar weeks",
                record.next_action,
            )
            self.assertIn(
                "40 completed NQ",
                record.next_action,
            )
            self.assertIn(
                "paper-only",
                record.next_action.lower(),
            )

    def test_registry_is_valid_and_unique(
        self,
    ) -> None:
        validate_lifecycle_registry()

        records = list_experiment_lifecycles()
        identifiers = [
            record.experiment_id
            for record in records
        ]

        self.assertEqual(
            len(identifiers),
            len(set(identifiers)),
        )

        for record in records:
            self.assertIn(
                record.stage,
                ALLOWED_STAGES,
            )

    def test_exp003_is_accepted_for_paper_testing(
        self,
    ) -> None:
        record = get_experiment_lifecycle(
            "EXP-003"
        )

        self.assertEqual(
            record.stage,
            "ACCEPTED_FOR_PAPER_TESTING",
        )

        self.assertIn(
            "paper-only simulator",
            record.next_action.lower(),
        )

        self.assertEqual(
            record.strategy_name,
            "volatility_compression_breakout_long",
        )

        self.assertIsNotNone(
            record.preregistration_file
        )

    def test_exp004_is_rejected(
        self,
    ) -> None:
        record = get_experiment_lifecycle(
            "EXP-004"
        )

        self.assertEqual(
            record.stage,
            "REJECTED",
        )

        self.assertIn(
            "0.3077",
            record.stage_reason,
        )

        self.assertIn(
            "OOS",
            record.next_action,
        )

    def test_exp005_is_accepted_for_paper_testing(
            self,
        ) -> None:
            record = get_experiment_lifecycle(
                "EXP-005"
            )
            self.assertEqual(
                record.stage,
                "ACCEPTED_FOR_PAPER_TESTING",
            )
            self.assertEqual(
                record.market_name,
                "NQ / MNQ futures",
            )
            self.assertEqual(
                record.timeframe,
                "5 minutes",
            )
            self.assertIsNotNone(
                record.preregistration_file
            )

    def test_exp018_is_closed_as_qualified_source(
        self,
    ) -> None:
        record = get_experiment_lifecycle(
            "EXP-018"
        )

        self.assertEqual(
            record.stage,
            "REVIEW",
        )
        self.assertIn(
            "QUALIFIED_AS_ACCESSIBLE_EXACT_CONTRACT_SOURCE",
            record.stage_reason,
        )
        self.assertIn(
            "Do not rerun EXP-018",
            record.next_action,
        )
        self.assertIn(
            "separately preregistered",
            record.next_action,
        )

    def test_exp019_is_closed_with_known_conditions(
        self,
    ) -> None:
        record = get_experiment_lifecycle(
            "EXP-019"
        )

        self.assertEqual(
            record.stage,
            "REVIEW",
        )
        self.assertIn(
            "QUALIFIED_WITH_KNOWN_PROVIDER_CONDITIONS",
            record.stage_reason,
        )
        self.assertIn(
            "6,276,486",
            record.stage_reason,
        )
        self.assertIn(
            "17 hard checks",
            record.stage_reason,
        )
        self.assertIn(
            "16",
            record.stage_reason,
        )
        self.assertIn(
            "frozen",
            record.next_action.lower(),
        )
        self.assertIn(
            "do not rerun any exp-019 mode",
            record.next_action.lower(),
        )
        self.assertIn(
            "separately preregistered new experiment",
            record.next_action.lower(),
        )
        self.assertIn(
            "does not authorize paper or live trading",
            record.next_action.lower(),
        )

    def test_exp020_is_closed_with_calendar_fallbacks(
        self,
    ) -> None:
        record = get_experiment_lifecycle(
            "EXP-020"
        )

        self.assertEqual(
            record.stage,
            "REVIEW",
        )
        self.assertIn(
            "20 hard checks",
            record.stage_reason,
        )
        self.assertIn(
            "QUALIFIED_WITH_DISCLOSED_CALENDAR_FALLBACKS",
            record.stage_reason,
        )
        self.assertIn(
            "0 volume crossovers",
            record.stage_reason,
        )
        self.assertIn(
            "65 calendar fallbacks",
            record.stage_reason,
        )
        self.assertIn(
            "freeze exp-020",
            record.next_action.lower(),
        )
        self.assertIn(
            "do not rerun any exp-020 mode",
            record.next_action.lower(),
        )
        self.assertIn(
            "preregister exp-021",
            record.next_action.lower(),
        )
        self.assertIn(
            "do not run strategy",
            record.next_action.lower(),
        )

    def test_exp021_is_closed_with_selected_roll_rule(
        self,
    ) -> None:
        record = get_experiment_lifecycle(
            "EXP-021"
        )

        self.assertEqual(
            record.stage,
            "REVIEW",
        )
        self.assertIn(
            "16 hard checks",
            record.stage_reason,
        )
        self.assertIn(
            "VOL_GT_OUT_2S_E3",
            record.stage_reason,
        )
        self.assertIn(
            "40 of 42 clean",
            record.stage_reason,
        )
        self.assertIn(
            "23 warning",
            record.stage_reason,
        )
        self.assertIn(
            "2 clean transitions",
            record.stage_reason,
        )
        self.assertIn(
            "not equivalent",
            record.stage_reason,
        )
        self.assertIn(
            "freeze exp-021",
            record.next_action.lower(),
        )
        self.assertIn(
            "do not rerun",
            record.next_action.lower(),
        )
        self.assertIn(
            "preregister exp-022",
            record.next_action.lower(),
        )
        self.assertIn(
            "do not run strategy",
            record.next_action.lower(),
        )

    def test_exp022_is_preregistered_for_selected_construction(
        self,
    ) -> None:
        record = get_experiment_lifecycle(
            "EXP-022"
        )

        self.assertEqual(
            record.stage,
            "PRE_REGISTERED",
        )
        self.assertIn(
            "VOL_GT_OUT_2S_E3",
            record.stage_reason,
        )
        self.assertIn(
            "40 volume-driven transitions",
            record.stage_reason,
        )
        self.assertIn(
            "25 disclosed calendar fallbacks",
            record.stage_reason,
        )
        self.assertIn(
            "protected implementation",
            record.next_action.lower(),
        )
        self.assertIn(
            "do not rerun exp-019, exp-020 or exp-021",
            record.next_action.lower(),
        )
        self.assertIn(
            "do not",
            record.next_action.lower(),
        )
        self.assertIsNotNone(
            record.preregistration_file
        )

    def test_unregistered_config_defaults_to_idea(
        self,
    ) -> None:
        record = get_experiment_lifecycle(
            "EXP-099",
            experiment_name="Test experiment",
            hypothesis="Test hypothesis.",
            market_name="Test market",
            timeframe="1 hour",
            strategy_name="test_strategy",
        )

        self.assertEqual(
            record.stage,
            "IDEA",
        )

        self.assertEqual(
            record.experiment_name,
            "Test experiment",
        )

        self.assertIn(
            "lifecycle record",
            record.stage_reason,
        )


class LifecycleCompatibilityTests(unittest.TestCase):
    def test_decision_wrapper_maps_final_stages(
        self,
    ) -> None:
        rejected = get_experiment_decision(
            "EXP-001"
        )

        accepted = get_experiment_decision(
            "EXP-003"
        )

        self.assertEqual(
            rejected["status"],
            "REJECTED",
        )

        self.assertEqual(
            accepted["status"],
            "ACCEPTED",
        )

    def test_dashboard_supports_accepted_experiment(
        self,
    ) -> None:
        lifecycle = get_experiment_lifecycle(
            "EXP-003"
        )

        record = build_lifecycle_only_record(
            lifecycle
        )

        self.assertFalse(
            record["configured"]
        )

        self.assertFalse(
            record["has_results"]
        )

        self.assertEqual(
            record["status"],
            "ACCEPTED_FOR_PAPER_TESTING",
        )


if __name__ == "__main__":
    unittest.main()
