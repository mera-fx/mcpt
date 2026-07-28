from __future__ import annotations

from pathlib import Path
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

    def test_exp022_is_closed_as_selected_continuous_series(
        self,
    ) -> None:
        record = get_experiment_lifecycle(
            "EXP-022"
        )

        self.assertEqual(
            record.stage,
            "REVIEW",
        )
        self.assertIn(
            "QUALIFIED_AS_SELECTED_VOLUME_ROLL_CONTINUOUS_SERIES",
            record.stage_reason,
        )
        self.assertIn(
            "20 hard checks",
            record.stage_reason,
        )
        self.assertIn(
            "5,457,606 rows each",
            record.stage_reason,
        )
        self.assertIn(
            "40 transitions",
            record.stage_reason,
        )
        self.assertIn(
            "25 used calendar fallback",
            record.stage_reason,
        )
        self.assertIn(
            "freeze exp-022",
            record.next_action.lower(),
        )
        self.assertIn(
            "do not rerun",
            record.next_action.lower(),
        )
        self.assertIn(
            "preregister exp-023",
            record.next_action.lower(),
        )
        self.assertIn(
            "do not modify exp-022 outputs",
            record.next_action.lower(),
        )
        self.assertIn(
            "strategy",
            record.next_action.lower(),
        )
        self.assertIsNotNone(
            record.preregistration_file
        )

    def test_exp023_is_closed_with_material_transfer_differences(
        self,
    ) -> None:
        record = get_experiment_lifecycle(
            "EXP-023"
        )

        self.assertEqual(
            record.stage,
            "REVIEW",
        )
        self.assertIn(
            "three unchanged EXP-014 finalists",
            record.hypothesis,
        )
        self.assertIn(
            "2020-2025 overlap",
            record.hypothesis,
        )
        self.assertIn(
            "TRANSFER_DIAGNOSTIC_COMPLETE_WITH_MATERIAL_DIFFERENCES",
            record.stage_reason,
        )
        self.assertIn(
            "20 hard checks",
            record.stage_reason,
        )
        self.assertIn(
            "premarket_continuation_0p50_time",
            record.stage_reason,
        )
        self.assertIn(
            "gap_fade_0p50_1r",
            record.stage_reason,
        )
        self.assertIn(
            "1% trade-count-difference gate",
            record.stage_reason,
        )
        self.assertIn(
            "do not rerun",
            record.next_action.lower(),
        )
        self.assertIn(
            "all three finalists as separate evidence rows",
            record.next_action.lower(),
        )
        self.assertIn(
            "do not select or rescue a winner",
            record.next_action.lower(),
        )
        self.assertIn(
            "new experiment id",
            record.next_action.lower(),
        )
        self.assertIn(
            "separate preregistration",
            record.next_action.lower(),
        )
        self.assertIn(
            "do not begin paper or live trading",
            record.next_action.lower(),
        )
        self.assertIsNotNone(
            record.preregistration_file
        )
        self.assertEqual(
            record.preregistration_file,
            Path(
                "research/EXP-023_preregistration.md"
            ),
        )

    def test_exp024_is_closed_after_failed_attribution_diagnostic(
        self,
    ) -> None:
        record = get_experiment_lifecycle("EXP-024")

        self.assertEqual(record.stage, "REVIEW")
        self.assertIn("51 frozen EXP-023", record.hypothesis)
        self.assertIn(
            "ATTRIBUTION_DIAGNOSTIC_NOT_QUALIFIED",
            record.stage_reason,
        )
        self.assertIn("evidence-only recovery", record.stage_reason)
        self.assertIn("51 of 51", record.stage_reason)
        self.assertIn("8 of 51", record.stage_reason)
        self.assertIn("43 gap-fade", record.stage_reason)
        self.assertIn(
            "freeze exp-024 permanently",
            record.next_action.lower(),
        )
        self.assertIn(
            "do not rerun any exp-024",
            record.next_action.lower(),
        )
        self.assertIn(
            "do not modify exp-024 outputs",
            record.next_action.lower(),
        )
        self.assertIn(
            "new experiment id",
            record.next_action.lower(),
        )
        self.assertIn(
            "data or engine qualification",
            record.next_action.lower(),
        )
        self.assertIn(
            "do not begin paper or live trading",
            record.next_action.lower(),
        )
        self.assertIsNotNone(record.preregistration_file)
        self.assertEqual(
            record.preregistration_file,
            Path("research/EXP-024_preregistration.md"),
        )

    def test_exp025_is_closed_as_data_unavailable(
        self,
    ) -> None:
        record = get_experiment_lifecycle("EXP-025")

        self.assertEqual(record.stage, "REVIEW")
        self.assertIn("43 unresolved EXP-024", record.hypothesis)
        self.assertIn("same explicit quarterly NQ", record.hypothesis)
        self.assertIn(
            "BLOCKED_DATA_UNAVAILABLE",
            record.stage_reason,
        )
        self.assertIn(
            "no expired NQH0 contract",
            record.stage_reason,
        )
        self.assertIn(
            "no explicit contract identity",
            record.stage_reason,
        )
        self.assertIn(
            "freeze exp-025",
            record.next_action.lower(),
        )
        self.assertIn(
            "databento as the primary historical",
            record.next_action.lower(),
        )
        self.assertIn(
            "new experiment id",
            record.next_action.lower(),
        )
        self.assertIn(
            "do not infer a strategy conclusion",
            record.next_action.lower(),
        )
        self.assertIn(
            "paper or live trading",
            record.next_action.lower(),
        )
        self.assertIsNotNone(record.preregistration_file)
        self.assertEqual(
            record.preregistration_file,
            Path("research/EXP-025_preregistration.md"),
        )

    def test_exp026_is_closed_after_measurement_review(
        self,
    ) -> None:
        record = get_experiment_lifecycle(
            "EXP-026"
        )

        self.assertEqual(
            record.stage,
            "REVIEW",
        )
        self.assertIn(
            "Databento-Native",
            record.experiment_name,
        )
        self.assertIn(
            "bounded set of gap-fade",
            record.hypothesis,
        )
        self.assertIn(
            "COMPLETED_MEASUREMENT_REVIEW",
            record.stage_reason,
        )
        self.assertIn(
            "six survivors",
            record.stage_reason,
        )
        self.assertIn(
            "three family finalists",
            record.stage_reason,
        )
        self.assertIn(
            "0.465534",
            record.stage_reason,
        )
        self.assertIn(
            "not independent confirmation",
            record.stage_reason,
        )
        self.assertIn(
            "freeze exp-026 permanently",
            record.next_action.lower(),
        )
        self.assertIn(
            "exp-027",
            record.next_action.lower(),
        )
        self.assertIn(
            "separate preregistration",
            record.next_action.lower(),
        )
        self.assertIn(
            "does not authorise exp-027",
            record.next_action.lower(),
        )
        self.assertIn(
            "paper trading or live trading",
            record.next_action.lower(),
        )
        self.assertEqual(
            record.preregistration_file,
            Path(
                "research/EXP-026_preregistration.md"
            ),
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
