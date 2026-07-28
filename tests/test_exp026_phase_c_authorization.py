from __future__ import annotations

from copy import deepcopy
from importlib.metadata import version
import unittest

import pandas as pd

from exp026_phase_b_completion import (
    EXPECTED_EXP026_PHASE_B_COMPLETION_SHA256,
    get_exp026_phase_b_completion,
)
from exp026_phase_c_authorization import (
    EXPECTED_CONTROL_CANDIDATE_IDS,
    EXPECTED_EXP026_PHASE_C_AUTHORIZATION_SHA256,
    EXPECTED_FINALIST_CANDIDATE_IDS,
    EXPECTED_PHASE_C_OUTPUTS,
    EXPECTED_REPRESENTATIONS,
    canonical_record_hash,
    get_exp026_phase_c_authorization,
    validate_exp026_phase_c_authorization,
)
from exp026_runner import (
    PHASE_OUTPUT_DIRS,
    PHASE_PARTIAL_DIRS,
    PHASE_REQUIRED_OUTPUTS,
    _locked_phase_b_finalists,
    load_phase_authorization,
)


class Exp026PhaseCAuthorizationTests(
    unittest.TestCase
):
    def test_01_authorization_is_valid(
        self,
    ) -> None:
        validate_exp026_phase_c_authorization()

    def test_02_identity_is_locked(
        self,
    ) -> None:
        record = (
            get_exp026_phase_c_authorization()
        )
        self.assertEqual(
            record["experiment_id"],
            "EXP-026",
        )
        self.assertEqual(
            record["phase"],
            "C",
        )
        self.assertTrue(
            record["execution_authorized"]
        )
        self.assertTrue(
            record["one_time_run"]
        )
        self.assertEqual(
            record["maximum_runs"],
            1,
        )

    def test_03_ancestry_is_locked(
        self,
    ) -> None:
        record = (
            get_exp026_phase_c_authorization()
        )
        self.assertEqual(
            record[
                "locked_implementation_commit"
            ],
            "13ee0683dfcbbb5d763f7254f3b245ecc8e6d9cd",
        )
        self.assertEqual(
            record[
                "phase_b_completion_commit"
            ],
            "da8456d254dc710336806ad5940afcec649be016",
        )
        self.assertEqual(
            record[
                "phase_b_completion_sha256"
            ],
            EXPECTED_EXP026_PHASE_B_COMPLETION_SHA256,
        )

    def test_04_phase_b_completion_is_exact(
        self,
    ) -> None:
        completion = (
            get_exp026_phase_b_completion()
        )
        self.assertEqual(
            completion[
                "completion_commit"
            ],
            "da8456d254dc710336806ad5940afcec649be016",
        )
        self.assertEqual(
            tuple(
                completion[
                    "finalist_candidate_ids"
                ]
            ),
            EXPECTED_FINALIST_CANDIDATE_IDS,
        )
        self.assertEqual(
            _locked_phase_b_finalists(
                completion
            ),
            EXPECTED_FINALIST_CANDIDATE_IDS,
        )

    def test_05_candidate_population_is_exact(
        self,
    ) -> None:
        record = (
            get_exp026_phase_c_authorization()
        )
        self.assertEqual(
            tuple(
                record[
                    "finalist_candidate_ids"
                ]
            ),
            EXPECTED_FINALIST_CANDIDATE_IDS,
        )
        self.assertEqual(
            tuple(
                record[
                    "control_candidate_ids"
                ]
            ),
            EXPECTED_CONTROL_CANDIDATE_IDS,
        )

    def test_06_periods_are_exact(
        self,
    ) -> None:
        scope = (
            get_exp026_phase_c_authorization()[
                "phase_scope"
            ]
        )
        self.assertEqual(
            scope[
                "materialized_source_start"
            ],
            "2019-12-01",
        )
        self.assertEqual(
            scope[
                "materialized_source_end"
            ],
            "2025-12-31",
        )
        self.assertEqual(
            scope[
                "known_comparison_start"
            ],
            "2020-01-03",
        )
        self.assertEqual(
            scope[
                "known_comparison_end"
            ],
            "2025-12-31",
        )

    def test_07_representations_are_exact(
        self,
    ) -> None:
        scope = (
            get_exp026_phase_c_authorization()[
                "representation_scope"
            ]
        )
        self.assertEqual(
            scope["representations"],
            EXPECTED_REPRESENTATIONS,
        )
        self.assertTrue(
            scope[
                "backward_adjusted_is_primary"
            ]
        )
        self.assertTrue(
            scope[
                "unadjusted_is_post_selection_sensitivity_only"
            ]
        )
        self.assertFalse(
            scope[
                "unadjusted_results_can_change_selection"
            ]
        )

    def test_08_no_reselection_or_parameter_changes(
        self,
    ) -> None:
        scope = (
            get_exp026_phase_c_authorization()[
                "phase_scope"
            ]
        )
        for field in (
            "candidate_reselection",
            "parameter_changes",
            "position_sizing_changes",
            "portfolio_weight_changes",
            "finalist_identity_can_change",
            "known_period_is_independent_confirmation",
            "unadjusted_can_change_finalist_identity",
        ):
            self.assertFalse(scope[field])

    def test_09_required_outputs_match_runner(
        self,
    ) -> None:
        record = (
            get_exp026_phase_c_authorization()
        )
        self.assertEqual(
            tuple(
                record["required_outputs"]
            ),
            PHASE_REQUIRED_OUTPUTS["C"],
        )
        self.assertEqual(
            tuple(
                record["required_outputs"]
            ),
            EXPECTED_PHASE_C_OUTPUTS,
        )

    def test_10_cost_sensitivity_is_exact(
        self,
    ) -> None:
        scope = (
            get_exp026_phase_c_authorization()[
                "phase_scope"
            ]
        )
        self.assertEqual(
            tuple(
                scope[
                    "cost_sensitivity_ticks_per_side"
                ]
            ),
            (0, 1, 2, 3),
        )

    def test_11_runtime_dependency_is_ready(
        self,
    ) -> None:
        record = (
            get_exp026_phase_c_authorization()
        )
        runtime = record[
            "runtime_environment"
        ]
        self.assertEqual(
            version("tabulate"),
            "0.10.0",
        )
        self.assertEqual(
            runtime["tabulate_version"],
            "0.10.0",
        )
        value = pd.DataFrame(
            {"candidate_id": ["smoke"]}
        ).to_markdown(index=False)
        self.assertIn(
            "candidate_id",
            value,
        )

    def test_12_top_level_boundaries_are_locked(
        self,
    ) -> None:
        record = (
            get_exp026_phase_c_authorization()
        )
        for field in (
            "protected_2026_access_authorized",
            "new_databento_download_authorized",
            "network_access_authorized",
            "paper_trading_authorized",
            "live_trading_authorized",
        ):
            self.assertIn(field, record)
            self.assertFalse(record[field])

    def test_13_runner_accepts_interface(
        self,
    ) -> None:
        record = load_phase_authorization("C")
        self.assertEqual(
            record["phase"],
            "C",
        )
        self.assertTrue(
            record["execution_authorized"]
        )
        self.assertFalse(
            record[
                "protected_2026_access_authorized"
            ]
        )

    def test_14_result_and_protected_boundaries_hold(
        self,
    ) -> None:
        record = (
            get_exp026_phase_c_authorization()
        )
        boundary = record[
            "data_access_boundary"
        ]
        self.assertTrue(
            boundary[
                "known_2020_2025_access_authorized"
            ]
        )
        self.assertTrue(
            boundary[
                "phase_c_access_authorized"
            ]
        )
        self.assertEqual(
            boundary[
                "maximum_materialized_trading_date"
            ],
            "2025-12-31",
        )
        self.assertFalse(
            boundary[
                "protected_2026_access_authorized"
            ]
        )
        self.assertEqual(
            boundary[
                "databento_api_calls_authorized"
            ],
            0,
        )
        self.assertFalse(
            PHASE_OUTPUT_DIRS["C"].exists()
        )
        self.assertFalse(
            PHASE_PARTIAL_DIRS["C"].exists()
        )

    def test_15_hash_rejects_mutation(
        self,
    ) -> None:
        record = (
            get_exp026_phase_c_authorization()
        )
        self.assertEqual(
            canonical_record_hash(record),
            EXPECTED_EXP026_PHASE_C_AUTHORIZATION_SHA256,
        )
        changed = deepcopy(record)
        changed[
            "protected_2026_access_authorized"
        ] = True
        with self.assertRaisesRegex(
            ValueError,
            "runner boundary changed",
        ):
            validate_exp026_phase_c_authorization(
                changed
            )


if __name__ == "__main__":
    unittest.main()
