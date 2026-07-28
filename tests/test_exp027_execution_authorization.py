from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import unittest

from exp027_execution_authorization import (
    EXPECTED_EXP027_EXECUTION_AUTHORIZATION_SHA256,
    canonical_record_hash,
    get_exp027_execution_authorization,
    validate_exp027_execution_authorization,
)
from exp027_preregistration import (
    EXPECTED_EXP027_PREREGISTRATION_SHA256,
)


PROJECT_DIR = Path(__file__).resolve().parents[1]


class Exp027ExecutionAuthorizationTests(unittest.TestCase):
    def test_01_authorization_is_valid(self) -> None:
        validate_exp027_execution_authorization()

    def test_02_identity_is_one_time(self) -> None:
        record = get_exp027_execution_authorization()
        self.assertEqual(record["experiment_id"], "EXP-027")
        self.assertEqual(
            record["authorization_status"],
            "AUTHORIZED",
        )
        self.assertTrue(record["execution_authorized"])
        self.assertTrue(record["one_time_run"])
        self.assertEqual(record["maximum_runs"], 1)

    def test_03_preregistration_and_implementation_are_locked(
        self,
    ) -> None:
        record = get_exp027_execution_authorization()
        self.assertEqual(
            record["preregistration_commit"],
            "21c182e119cde651e6c4fe22b1e4e8d6b99def5b",
        )
        self.assertEqual(
            record["preregistration_sha256"],
            EXPECTED_EXP027_PREREGISTRATION_SHA256,
        )
        self.assertEqual(
            record["locked_implementation_commit"],
            "591cdf43b4c23abc312ae3d50b7d7948f88c90b2",
        )
        self.assertEqual(
            record["locked_exp026_engine_commit"],
            "13ee0683dfcbbb5d763f7254f3b245ecc8e6d9cd",
        )

    def test_04_protected_period_is_exact(self) -> None:
        scope = get_exp027_execution_authorization()[
            "protected_measurement_scope"
        ]
        self.assertEqual(
            scope["session_start"],
            "2026-01-01",
        )
        self.assertEqual(
            scope["session_end"],
            "2026-07-23",
        )
        self.assertTrue(scope["partial_year"])

    def test_05_all_24_rows_are_authorized(self) -> None:
        scope = get_exp027_execution_authorization()[
            "candidate_scope"
        ]
        self.assertEqual(
            scope["strategy_candidate_count"],
            22,
        )
        self.assertEqual(
            scope["control_candidate_count"],
            2,
        )
        self.assertEqual(scope["reported_count"], 24)
        self.assertEqual(
            len(scope["reported_ids"]),
            24,
        )
        self.assertEqual(
            len(set(scope["reported_ids"])),
            24,
        )

    def test_06_primary_cohort_is_predeclared(self) -> None:
        scope = get_exp027_execution_authorization()[
            "candidate_scope"
        ]
        self.assertEqual(
            scope["primary_confirmation_cohort"],
            (
                "gap_fade_0p75_1r",
                "opening_drive_0p75_time",
                "premarket_continuation_0p875_1p5r",
            ),
        )
        self.assertEqual(scope["primary_count"], 3)

    def test_07_selection_and_optimization_are_absent(
        self,
    ) -> None:
        scope = get_exp027_execution_authorization()[
            "candidate_scope"
        ]
        self.assertFalse(scope["candidate_selection"])
        self.assertFalse(scope["candidate_reselection"])
        self.assertFalse(
            scope["secondary_candidate_promotion"]
        )
        self.assertFalse(scope["parameter_changes"])
        self.assertFalse(scope["single_winner_selection"])

    def test_08_data_boundary_excludes_historical_rows(
        self,
    ) -> None:
        boundary = get_exp027_execution_authorization()[
            "data_access_boundary"
        ]
        self.assertTrue(
            boundary["parquet_filter_pushdown_required"]
        )
        self.assertTrue(
            boundary[
                "filter_applied_before_table_materialization"
            ]
        )
        self.assertFalse(
            boundary[
                "historical_2010_2025_market_access_authorized"
            ]
        )
        self.assertTrue(
            boundary["protected_2026_access_authorized"]
        )

    def test_09_frozen_series_are_read_only(self) -> None:
        scope = get_exp027_execution_authorization()[
            "representation_scope"
        ]
        self.assertEqual(
            len(scope["representations"]),
            2,
        )
        self.assertTrue(
            scope["both_representations_read_only"]
        )
        self.assertFalse(
            scope["roll_rule_change_authorized"]
        )
        self.assertFalse(
            scope["source_series_modification_authorized"]
        )

    def test_10_rebuild_and_no_rerun_are_required(
        self,
    ) -> None:
        boundary = get_exp027_execution_authorization()[
            "execution_boundary"
        ]
        self.assertTrue(
            boundary["independent_rebuild_required"]
        )
        self.assertTrue(
            boundary["serial_parallel_parity_required"]
        )
        self.assertFalse(
            boundary["rerun_after_completion_authorized"]
        )

    def test_11_output_contract_requires_24_series(
        self,
    ) -> None:
        outputs = get_exp027_execution_authorization()[
            "required_outputs"
        ]
        self.assertEqual(outputs["per_series_count"], 24)
        self.assertEqual(outputs["files_per_series"], 4)
        self.assertIn("report.html", outputs["root"])
        self.assertIn(
            "series/<candidate_id>/trades.csv",
            outputs["per_series_patterns"],
        )
        self.assertIn(
            "series/<candidate_id>/equity.csv",
            outputs["per_series_patterns"],
        )

    def test_12_no_download_network_or_trading(
        self,
    ) -> None:
        record = get_exp027_execution_authorization()
        self.assertFalse(
            record["new_databento_download_authorized"]
        )
        self.assertFalse(
            record["network_access_authorized"]
        )
        self.assertFalse(
            record["paper_trading_authorized"]
        )
        self.assertFalse(
            record["live_trading_authorized"]
        )
        self.assertEqual(
            record["data_access_boundary"][
                "databento_api_calls_authorized"
            ],
            0,
        )

    def test_13_runner_accepts_authorization_interface(
        self,
    ) -> None:
        from exp027_runner import load_authorization

        record = load_authorization()
        self.assertEqual(record["experiment_id"], "EXP-027")
        self.assertTrue(
            record["protected_2026_access_authorized"]
        )
        self.assertEqual(
            record["locked_implementation_commit"],
            "591cdf43b4c23abc312ae3d50b7d7948f88c90b2",
        )

    def test_14_authorization_does_not_create_results(
        self,
    ) -> None:
        self.assertFalse(
            (
                PROJECT_DIR
                / "results"
                / "EXP-027"
                / "protected_2026_measurement"
            ).exists()
        )
        self.assertFalse(
            (
                PROJECT_DIR
                / "results"
                / "EXP-027"
                / "protected_2026_measurement.partial"
            ).exists()
        )

    def test_15_hash_rejects_mutation(self) -> None:
        record = get_exp027_execution_authorization()
        self.assertEqual(
            canonical_record_hash(record),
            EXPECTED_EXP027_EXECUTION_AUTHORIZATION_SHA256,
        )
        changed = deepcopy(record)
        changed["candidate_scope"][
            "candidate_selection"
        ] = True
        with self.assertRaisesRegex(
            ValueError,
            "candidate scope|record changed",
        ):
            validate_exp027_execution_authorization(changed)


if __name__ == "__main__":
    unittest.main()
