from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import hashlib
import unittest

from exp026_preregistration import (
    EXPECTED_EXP026_PREREGISTRATION_SHA256,
    canonical_record_hash,
    get_exp026_preregistration,
    validate_exp026_preregistration,
)
from experiment_lifecycle import (
    get_experiment_lifecycle,
)


POLICY_PATH = Path(
    "research/HISTORICAL_DATA_POLICY.md"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for block in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


class Exp026PreregistrationTests(unittest.TestCase):
    def test_01_preregistration_is_valid(self) -> None:
        validate_exp026_preregistration()

    def test_02_identity_is_locked(self) -> None:
        record = get_exp026_preregistration()

        self.assertEqual(
            record["experiment_id"],
            "EXP-026",
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
            record["execution_status"],
            "NOT_RUN",
        )

    def test_03_exp025_closure_and_policy_are_locked(
        self,
    ) -> None:
        frozen = get_exp026_preregistration()[
            "frozen_inputs"
        ]

        self.assertEqual(
            frozen["exp025_classification"],
            "BLOCKED_DATA_UNAVAILABLE",
        )
        self.assertEqual(
            frozen["historical_data_policy_sha256"],
            sha256_file(POLICY_PATH),
        )

    def test_04_exp022_series_are_locked(self) -> None:
        frozen = get_exp026_preregistration()[
            "frozen_inputs"
        ]
        series = frozen["series"]

        self.assertEqual(
            frozen["selected_roll_method"],
            "VOL_GT_OUT_2S_E3",
        )
        self.assertEqual(
            frozen["series_row_count"],
            5_457_606,
        )
        self.assertEqual(len(series), 2)
        self.assertEqual(
            series[0]["representation_id"],
            "BACKWARD_ADJUSTED",
        )
        self.assertEqual(
            series[1]["representation_id"],
            "UNADJUSTED",
        )

    def test_05_periods_and_protected_2026_are_locked(
        self,
    ) -> None:
        periods = get_exp026_preregistration()[
            "research_periods"
        ]

        self.assertEqual(
            periods["phase_a_development"][
                "session_start"
            ],
            "2010-06-07",
        )
        self.assertEqual(
            periods["phase_b_internal_validation"][
                "session_end"
            ],
            "2019-12-31",
        )
        self.assertEqual(
            periods["phase_c_known_comparison"][
                "session_end"
            ],
            "2025-12-31",
        )
        self.assertTrue(
            periods["protected_exp027_confirmation"][
                "materialization_prohibited"
            ]
        )

    def test_06_candidate_counts_are_locked(self) -> None:
        grid = get_exp026_preregistration()[
            "candidate_grid"
        ]

        self.assertEqual(grid["family_count"], 3)
        self.assertEqual(
            grid["development_candidate_count"],
            22,
        )
        self.assertEqual(
            grid["control_candidate_count"],
            2,
        )
        self.assertEqual(
            grid["total_reported_candidate_count"],
            24,
        )

    def test_07_family_grids_are_locked(self) -> None:
        families = get_exp026_preregistration()[
            "candidate_grid"
        ]["families"]

        self.assertEqual(
            families["gap_fade"]["candidate_count"],
            6,
        )
        self.assertEqual(
            families[
                "premarket_momentum_continuation"
            ]["candidate_count"],
            8,
        )
        self.assertEqual(
            families[
                "opening_drive_continuation"
            ]["candidate_count"],
            8,
        )

    def test_08_candidate_ids_are_unique(self) -> None:
        grid = get_exp026_preregistration()[
            "candidate_grid"
        ]
        candidates = grid["development_candidates"]
        controls = grid["control_candidates"]

        identifiers = [
            item["candidate_id"]
            for item in (
                tuple(candidates)
                + tuple(controls)
            )
        ]

        self.assertEqual(
            len(identifiers),
            len(set(identifiers)),
        )

    def test_09_controls_are_not_selectable(self) -> None:
        controls = get_exp026_preregistration()[
            "candidate_grid"
        ]["control_candidates"]

        self.assertTrue(
            all(
                item["eligible_for_selection"] is False
                for item in controls
            )
        )

    def test_10_phase_sequence_is_locked(self) -> None:
        phase = get_exp026_preregistration()[
            "phase_sequence"
        ]

        self.assertEqual(
            phase["phase_a"][
                "select_up_to_per_family"
            ],
            2,
        )
        self.assertEqual(
            phase["phase_b"][
                "select_up_to_per_family"
            ],
            1,
        )
        self.assertFalse(
            phase["phase_c"]["candidate_reselection"]
        )

    def test_11_robustness_counts_are_locked(self) -> None:
        robustness = get_exp026_preregistration()[
            "robustness_plan"
        ]

        self.assertEqual(
            robustness["selection_aware_mcpt"][
                "permutations"
            ],
            1_000,
        )
        self.assertEqual(
            robustness["bootstrap"]["resamples"],
            10_000,
        )
        self.assertEqual(
            robustness["anchored_walk_forward"][
                "test_years"
            ],
            (2014, 2015, 2016, 2017, 2018, 2019),
        )

    def test_12_reporting_layout_is_locked(self) -> None:
        reporting = get_exp026_preregistration()[
            "reporting_requirements"
        ]
        measurement = get_exp026_preregistration()[
            "measurement_plan"
        ]

        self.assertTrue(
            reporting["vertical_full_width_layout"]
        )
        self.assertTrue(
            reporting["full_width_equity_curves"]
        )
        self.assertTrue(
            reporting["full_width_drawdown_curves"]
        )
        self.assertEqual(
            measurement["metric_columns"],
            (
                "ALL_TRADES",
                "LONG_TRADES",
                "SHORT_TRADES",
            ),
        )

    def test_13_no_data_download_or_trading_is_authorized(
        self,
    ) -> None:
        boundary = get_exp026_preregistration()[
            "execution_boundary"
        ]
        prohibited = get_exp026_preregistration()[
            "prohibited_actions"
        ]

        self.assertEqual(
            boundary["databento_api_calls"],
            0,
        )
        self.assertFalse(
            boundary["new_databento_download"]
        )
        self.assertTrue(
            prohibited[
                "materialize_protected_2026_market_values"
            ]
        )
        self.assertTrue(prohibited["paper_trading"])
        self.assertTrue(prohibited["live_trading"])

    def test_14_lifecycle_matches_preregistration(
        self,
    ) -> None:
        lifecycle = get_experiment_lifecycle(
            "EXP-026"
        )

        self.assertEqual(
            lifecycle.stage,
            "PRE_REGISTERED",
        )
        self.assertIn(
            "Databento",
            lifecycle.experiment_name,
        )
        self.assertIn(
            "protected 2026",
            lifecycle.next_action,
        )

    def test_15_hash_rejects_mutation(self) -> None:
        record = get_exp026_preregistration()

        self.assertEqual(
            canonical_record_hash(record),
            EXPECTED_EXP026_PREREGISTRATION_SHA256,
        )

        changed = deepcopy(record)
        changed["candidate_grid"][
            "development_candidate_count"
        ] = 21

        with self.assertRaisesRegex(
            ValueError,
            "candidate grid changed",
        ):
            validate_exp026_preregistration(
                changed
            )


if __name__ == "__main__":
    unittest.main()
