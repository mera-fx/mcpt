from __future__ import annotations

import unittest

from exp015_preregistration import (
    FIXED_SAMPLE_WINDOWS,
    OFFICIAL_SOURCE_SNAPSHOT,
    QUALIFICATION_LEVELS,
    get_exp015_preregistration,
    validate_exp015_preregistration,
)


class Exp015PreregistrationTests(unittest.TestCase):
    def test_preregistration_is_valid(self) -> None:
        validate_exp015_preregistration()

    def test_scope_does_not_claim_all_data(self) -> None:
        scope = get_exp015_preregistration()["scope_boundary"]
        self.assertTrue(scope["does_not_qualify_all_vendor_asset_classes"])
        self.assertTrue(
            scope["does_not_replace_frozen_exp005_through_exp014_data"]
        )
        self.assertTrue(scope["does_not_validate_live_streaming"])
        self.assertTrue(scope["does_not_authorize_paper_or_live_trading"])

    def test_official_source_snapshot_is_locked(self) -> None:
        source = get_exp015_preregistration()["official_source_snapshot"]
        self.assertEqual(source, OFFICIAL_SOURCE_SNAPSHOT)
        self.assertEqual(source["python_distribution"], "lse-data")
        self.assertEqual(source["observed_package_version"], "0.14.0")
        self.assertTrue(source["claims_are_vendor_statements_not_yet_verified"])

    def test_api_key_and_access_safety_are_locked(self) -> None:
        safety = get_exp015_preregistration()["credential_and_access_safety"]
        self.assertEqual(
            safety["api_key_source"],
            "LSE_API_KEY environment variable only",
        )
        self.assertTrue(safety["api_key_must_not_be_written_to_disk"])
        self.assertTrue(safety["api_key_must_not_be_printed"])
        self.assertTrue(safety["website_scraping_prohibited"])
        self.assertEqual(safety["maximum_bulk_exports_per_hour"], 8)

    def test_python_314_requires_isolated_compatibility_probe(self) -> None:
        environment = get_exp015_preregistration()[
            "environment_qualification"
        ]
        self.assertEqual(environment["current_project_python"], "3.14.6")
        self.assertFalse(
            environment["official_package_classifiers_include_python_3_14"]
        )
        self.assertTrue(environment["isolated_import_probe_required"])
        self.assertTrue(
            environment[
                "main_venv_install_before_compatibility_test_prohibited"
            ]
        )

    def test_catalog_must_precede_history(self) -> None:
        catalog = get_exp015_preregistration()["catalog_phase"]
        self.assertTrue(catalog["must_run_before_any_history_download"])
        self.assertEqual(catalog["category"], "futures")
        self.assertTrue(catalog["exact_nq_and_mnq_identity_required"])
        self.assertTrue(catalog["symbol_guessing_prohibited"])
        self.assertTrue(catalog["unresolved_identity_stops_history_phase"])

    def test_six_sample_windows_are_fixed(self) -> None:
        history = get_exp015_preregistration()["fixed_history_phase"]
        self.assertEqual(tuple(history["sample_windows"]), FIXED_SAMPLE_WINDOWS)
        self.assertEqual(history["sample_window_count"], 6)
        self.assertTrue(history["window_changes_after_catalog_view_prohibited"])
        self.assertTrue(
            history["full_2020_2025_download_before_sample_review_prohibited"]
        )

    def test_frozen_replay_is_diagnostic_only(self) -> None:
        replay = get_exp015_preregistration()[
            "frozen_strategy_replay_diagnostic"
        ]
        self.assertEqual(len(replay["candidate_ids"]), 3)
        self.assertTrue(replay["exact_existing_rules_and_costs"])
        self.assertTrue(replay["no_candidate_selection"])
        self.assertTrue(replay["no_parameter_change"])
        self.assertTrue(replay["no_optimization"])
        self.assertTrue(replay["diagnostic_only_not_new_edge_test"])

    def test_qualification_levels_are_per_use_case(self) -> None:
        interpretation = get_exp015_preregistration()[
            "qualification_interpretation"
        ]
        self.assertEqual(
            tuple(interpretation["levels"]),
            QUALIFICATION_LEVELS,
        )
        self.assertTrue(
            interpretation["classification_is_per_use_case_not_global"]
        )
        self.assertTrue(interpretation["automatic_all_data_claim_prohibited"])
        self.assertFalse(interpretation["paper_trading_authorized"])
        self.assertFalse(interpretation["live_trading_authorized"])

    def test_history_window_mutation_is_rejected(self) -> None:
        changed = get_exp015_preregistration()
        changed["fixed_history_phase"]["sample_windows"] = list(
            FIXED_SAMPLE_WINDOWS[:-1]
        )
        with self.assertRaisesRegex(ValueError, "fixed-history"):
            validate_exp015_preregistration(changed)

    def test_api_key_safety_mutation_is_rejected(self) -> None:
        changed = get_exp015_preregistration()
        changed["credential_and_access_safety"][
            "api_key_must_not_be_printed"
        ] = False
        with self.assertRaisesRegex(ValueError, "credential or access"):
            validate_exp015_preregistration(changed)

    def test_all_data_claim_mutation_is_rejected(self) -> None:
        changed = get_exp015_preregistration()
        changed["scope_boundary"][
            "does_not_qualify_all_vendor_asset_classes"
        ] = False
        with self.assertRaisesRegex(ValueError, "scope boundary"):
            validate_exp015_preregistration(changed)

    def test_reporting_standard_is_preserved(self) -> None:
        reporting = get_exp015_preregistration()["reporting_requirements"]
        self.assertTrue(reporting["vertical_single_column_report"])
        self.assertTrue(reporting["catalog_identity_table"])
        self.assertTrue(reporting["cross_source_difference_table"])
        self.assertTrue(reporting["frozen_strategy_replay_comparison"])
        self.assertTrue(reporting["positive_numbers_use_neutral_text"])
        self.assertTrue(reporting["adverse_numbers_use_red_text"])
        self.assertTrue(reporting["green_reserved_for_status_words"])
        self.assertTrue(reporting["charts_use_solid_opaque_white_canvas"])


if __name__ == "__main__":
    unittest.main()
