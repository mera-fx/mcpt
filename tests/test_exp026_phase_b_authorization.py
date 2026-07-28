from __future__ import annotations

from copy import deepcopy
from importlib.metadata import version
import unittest

import pandas as pd

from exp026_phase_a_completion import (
    EXPECTED_EXP026_PHASE_A_COMPLETION_SHA256,
    get_exp026_phase_a_completion,
)
from exp026_phase_b_authorization import (
    EXPECTED_EXP026_PHASE_B_AUTHORIZATION_SHA256,
    EXPECTED_PHASE_A_SURVIVORS,
    EXPECTED_PHASE_B_OUTPUTS,
    EXPECTED_PHASE_B_SELECTION_RANK,
    canonical_record_hash,
    get_exp026_phase_b_authorization,
    validate_exp026_phase_b_authorization,
)
from exp026_runner import (
    PHASE_OUTPUT_DIRS,
    PHASE_PARTIAL_DIRS,
    PHASE_REQUIRED_OUTPUTS,
    load_phase_authorization,
)


class Exp026PhaseBAuthorizationTests(
    unittest.TestCase
):
    def test_01_authorization_is_valid(
        self,
    ) -> None:
        validate_exp026_phase_b_authorization()

    def test_02_identity_is_locked(
        self,
    ) -> None:
        record = (
            get_exp026_phase_b_authorization()
        )

        self.assertEqual(
            record["experiment_id"],
            "EXP-026",
        )
        self.assertEqual(record["phase"], "B")
        self.assertTrue(
            record["execution_authorized"]
        )
        self.assertTrue(record["one_time_run"])
        self.assertEqual(record["maximum_runs"], 1)

    def test_03_ancestry_is_locked(
        self,
    ) -> None:
        record = (
            get_exp026_phase_b_authorization()
        )

        self.assertEqual(
            record[
                "locked_implementation_commit"
            ],
            "13ee0683dfcbbb5d763f7254f3b245ecc8e6d9cd",
        )
        self.assertEqual(
            record[
                "phase_a_completion_commit"
            ],
            "28bd4209711f0c9b98a7650ab91f6408c2bdf4b7",
        )
        self.assertEqual(
            record[
                "phase_a_completion_sha256"
            ],
            EXPECTED_EXP026_PHASE_A_COMPLETION_SHA256,
        )

    def test_04_phase_a_completion_is_exact(
        self,
    ) -> None:
        completion = (
            get_exp026_phase_a_completion()
        )

        self.assertEqual(
            completion["completion_commit"],
            "28bd4209711f0c9b98a7650ab91f6408c2bdf4b7",
        )
        self.assertEqual(
            tuple(
                completion[
                    "survivor_candidate_ids"
                ]
            ),
            EXPECTED_PHASE_A_SURVIVORS,
        )

    def test_05_survivor_population_is_exact(
        self,
    ) -> None:
        record = (
            get_exp026_phase_b_authorization()
        )

        self.assertEqual(
            tuple(
                record["phase_a_survivor_ids"]
            ),
            EXPECTED_PHASE_A_SURVIVORS,
        )
        self.assertEqual(
            len(
                record[
                    "phase_a_survivor_ids"
                ]
            ),
            6,
        )

    def test_06_periods_are_exact(
        self,
    ) -> None:
        scope = (
            get_exp026_phase_b_authorization()[
                "phase_scope"
            ]
        )

        self.assertEqual(
            scope["materialized_source_start"],
            "2010-06-07",
        )
        self.assertEqual(
            scope["materialized_source_end"],
            "2019-12-31",
        )
        self.assertEqual(
            scope["internal_validation_start"],
            "2018-01-01",
        )
        self.assertEqual(
            scope["internal_validation_end"],
            "2019-12-31",
        )

    def test_07_selection_rule_is_exact(
        self,
    ) -> None:
        scope = (
            get_exp026_phase_b_authorization()[
                "phase_scope"
            ]
        )

        self.assertEqual(
            tuple(scope["selection_rank"]),
            EXPECTED_PHASE_B_SELECTION_RANK,
        )
        self.assertEqual(
            scope[
                "maximum_finalists_per_family"
            ],
            1,
        )
        self.assertEqual(
            scope["finalist_count_minimum"],
            0,
        )
        self.assertEqual(
            scope["finalist_count_maximum"],
            3,
        )
        self.assertTrue(
            scope["no_minimum_profit_gate"]
        )

    def test_08_robustness_is_exact(
        self,
    ) -> None:
        scope = (
            get_exp026_phase_b_authorization()[
                "robustness_scope"
            ]
        )

        self.assertEqual(
            scope[
                "selection_aware_mcpt_permutations"
            ],
            1000,
        )
        self.assertEqual(
            scope[
                "selection_aware_mcpt_seed"
            ],
            26026,
        )
        self.assertEqual(
            scope["bootstrap_resamples"],
            10000,
        )
        self.assertEqual(
            scope["bootstrap_seed"],
            26027,
        )
        self.assertFalse(
            scope["decision_gates"]
        )

    def test_09_required_outputs_match_runner(
        self,
    ) -> None:
        record = (
            get_exp026_phase_b_authorization()
        )

        self.assertEqual(
            tuple(record["required_outputs"]),
            PHASE_REQUIRED_OUTPUTS["B"],
        )
        self.assertEqual(
            tuple(record["required_outputs"]),
            EXPECTED_PHASE_B_OUTPUTS,
        )

    def test_10_runtime_dependency_is_ready(
        self,
    ) -> None:
        record = (
            get_exp026_phase_b_authorization()
        )
        runtime = record["runtime_environment"]

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

    def test_11_top_level_boundaries_are_locked(
        self,
    ) -> None:
        record = (
            get_exp026_phase_b_authorization()
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

    def test_12_runner_accepts_interface(
        self,
    ) -> None:
        record = load_phase_authorization("B")

        self.assertEqual(record["phase"], "B")
        self.assertTrue(
            record["execution_authorized"]
        )
        self.assertFalse(
            record[
                "protected_2026_access_authorized"
            ]
        )

    def test_13_later_access_is_absent(
        self,
    ) -> None:
        boundary = (
            get_exp026_phase_b_authorization()[
                "data_access_boundary"
            ]
        )

        self.assertFalse(
            boundary[
                "known_2020_2025_access_authorized"
            ]
        )
        self.assertFalse(
            boundary[
                "phase_c_access_authorized"
            ]
        )
        self.assertFalse(
            boundary[
                "protected_2026_access_authorized"
            ]
        )

        self.assertFalse(
            PHASE_OUTPUT_DIRS["B"].exists()
        )
        self.assertFalse(
            PHASE_PARTIAL_DIRS["B"].exists()
        )
        self.assertFalse(
            PHASE_OUTPUT_DIRS["C"].exists()
        )
        self.assertFalse(
            PHASE_PARTIAL_DIRS["C"].exists()
        )

    def test_14_controls_are_not_selectable(
        self,
    ) -> None:
        scope = (
            get_exp026_phase_b_authorization()[
                "phase_scope"
            ]
        )

        self.assertEqual(
            scope["control_candidate_count"],
            2,
        )
        self.assertTrue(
            scope[
                "controls_are_not_selectable"
            ]
        )

    def test_15_hash_rejects_mutation(
        self,
    ) -> None:
        record = (
            get_exp026_phase_b_authorization()
        )

        self.assertEqual(
            canonical_record_hash(record),
            EXPECTED_EXP026_PHASE_B_AUTHORIZATION_SHA256,
        )

        changed = deepcopy(record)
        changed[
            "protected_2026_access_authorized"
        ] = True

        with self.assertRaisesRegex(
            ValueError,
            "runner boundary changed",
        ):
            validate_exp026_phase_b_authorization(
                changed
            )


if __name__ == "__main__":
    unittest.main()
