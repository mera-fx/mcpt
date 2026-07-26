from __future__ import annotations

import unittest

from exp021_closure import (
    get_exp021_closure,
    validate_exp021_closure,
)


class Exp021ClosureTests(unittest.TestCase):
    def test_01_closure_is_valid(self):
        validate_exp021_closure()

    def test_02_identity_is_locked(self):
        record = get_exp021_closure()
        self.assertEqual(record["experiment_id"], "EXP-021")
        self.assertEqual(record["research_status"], "REVIEW")
        self.assertEqual(
            record["classification"],
            "DIAGNOSTIC_METHOD_SELECTED_FOR_SEPARATE_CONSTRUCTION",
        )

    def test_03_repository_commits_are_locked(self):
        repository = get_exp021_closure()["repository"]
        self.assertEqual(
            repository["preregistration_commit"],
            "27a960ad68f2059e5ac9d60e42e41a9171fbda41",
        )
        self.assertEqual(
            repository["implementation_commit"],
            "9d365613619e21b9fe4eb9625bba907efd60ecfa",
        )
        self.assertEqual(
            repository["authorization_commit"],
            "790918d8a484b08cff2bfff17edc907141547079",
        )

    def test_04_diagnostic_is_complete_and_frozen(self):
        diagnostic = get_exp021_closure()["diagnostic"]
        self.assertTrue(diagnostic["diagnostic_complete"])
        self.assertEqual(diagnostic["hard_checks"], 16)
        self.assertEqual(diagnostic["hard_failure_count"], 0)
        self.assertTrue(diagnostic["independent_rebuild"])
        self.assertFalse(diagnostic["diagnostic_rerun_authorized"])

    def test_05_selected_method_is_locked(self):
        selected = get_exp021_closure()["selected_method"]
        self.assertEqual(selected["candidate_id"], "VOL_GT_OUT_2S_E3")
        self.assertEqual(selected["selection_rank"], 4)
        self.assertEqual(selected["required_consecutive_sessions"], 2)
        self.assertEqual(
            selected["maximum_effective_common_sessions_after_calendar"],
            3,
        )
        self.assertEqual(selected["clean_volume_trigger_count"], 40)
        self.assertEqual(selected["warning_calendar_fallback_count"], 23)
        self.assertEqual(selected["clean_calendar_fallback_count"], 2)

    def test_06_three_passing_candidates_are_retained(self):
        rows = get_exp021_closure()["passing_candidates"]
        self.assertEqual(len(rows), 3)
        self.assertEqual(
            tuple(row["candidate_id"] for row in rows),
            (
                "VOL_GT_OUT_2S_E3",
                "VOL_GT_OUT_1S_E2",
                "VOL_GT_OUT_1S_E3",
            ),
        )

    def test_07_schedule_differences_are_locked(self):
        rows = get_exp021_closure()["pairwise_roll_date_differences"]
        self.assertEqual(
            tuple(row["different_roll_dates"] for row in rows),
            (40, 42, 2),
        )
        self.assertFalse(
            get_exp021_closure()["interpretation"][
                "passing_candidates_are_equivalent"
            ]
        )

    def test_08_clean_fallbacks_are_locked(self):
        rows = get_exp021_closure()["clean_fallbacks"]
        self.assertEqual(
            tuple(row["transition_sequence"] for row in rows),
            (59, 60),
        )
        self.assertEqual(
            tuple(row["outgoing_contract"] for row in rows),
            ("NQZ24", "NQH25"),
        )

    def test_09_no_construction_strategy_or_trading_permission(self):
        record = get_exp021_closure()
        self.assertFalse(record["diagnostic"]["continuous_construction"])
        self.assertFalse(record["diagnostic"]["strategy_run"])
        self.assertFalse(
            record["selected_method"]["construction_authorized"]
        )
        self.assertFalse(
            record["selected_method"]["strategy_use_authorized"]
        )
        self.assertFalse(
            record["interpretation"]["paper_trading_authorized"]
        )
        self.assertFalse(
            record["interpretation"]["live_trading_authorized"]
        )

    def test_10_mutation_is_rejected(self):
        record = get_exp021_closure()
        record["selected_method"]["candidate_id"] = "VOL_GT_OUT_1S_E3"
        with self.assertRaisesRegex(
            ValueError,
            "closure record changed",
        ):
            validate_exp021_closure(record)


if __name__ == "__main__":
    unittest.main()
