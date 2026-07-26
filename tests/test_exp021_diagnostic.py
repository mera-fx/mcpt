from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import unittest

import pandas as pd

from exp021_diagnostic_core import (
    CANDIDATE_SUMMARY_FIELDS,
    CANDIDATE_TRANSITION_FIELDS,
    DAILY_VOLUME_FIELDS,
    EXPECTED_CANDIDATE_IDS,
    _candidate_boundary,
    semantic_rows_hash,
    select_candidate,
    validate_candidate_matrix,
)
from exp021_preregistration import (
    get_exp021_preregistration,
    validate_exp021_preregistration,
)


PROJECT_DIR = Path(__file__).resolve().parents[1]


def series(
    start: date,
    outgoing: list[int],
    incoming: list[int],
) -> tuple[pd.Series, pd.Series, list[date]]:
    dates = [
        start + timedelta(days=index)
        for index in range(len(outgoing))
    ]
    return (
        pd.Series(
            outgoing,
            index=pd.Index(dates, dtype="object"),
            dtype="int64",
        ),
        pd.Series(
            incoming,
            index=pd.Index(dates, dtype="object"),
            dtype="int64",
        ),
        dates,
    )


class Exp021DiagnosticCoreTests(unittest.TestCase):
    def setUp(self):
        self.record = get_exp021_preregistration()
        self.candidates = tuple(
            self.record["candidate_methods"]
        )

    def test_01_preregistration_remains_valid(self):
        validate_exp021_preregistration()

    def test_02_candidate_ids_are_exact(self):
        rows = validate_candidate_matrix(
            self.candidates,
            self.record["fixed_selection_order"],
        )
        self.assertEqual(
            tuple(row["method_id"] for row in rows),
            EXPECTED_CANDIDATE_IDS,
        )

    def test_03_control_candidate_is_unique(self):
        controls = [
            row for row in self.candidates
            if row["control_method"]
        ]
        self.assertEqual(len(controls), 1)
        self.assertEqual(
            controls[0]["method_id"],
            "VOL_GT_OUT_2S_E0",
        )

    def test_04_one_session_e0_triggers_before_calendar(self):
        outgoing, incoming, dates = series(
            date(2026, 1, 1),
            [100, 100, 100, 100, 100],
            [50, 50, 150, 50, 50],
        )
        result = _candidate_boundary(
            outgoing,
            incoming,
            calendar_roll_date=dates[3],
            expiration=dates[4],
            required_sessions=1,
            extension_sessions=0,
            warning=False,
        )
        self.assertFalse(result["calendar_fallback"])
        self.assertEqual(
            result["effective_roll_date"],
            dates[3],
        )

    def test_05_two_session_rule_rejects_broken_streak(self):
        outgoing, incoming, dates = series(
            date(2026, 1, 1),
            [100, 100, 100, 100, 100],
            [50, 150, 50, 150, 50],
        )
        result = _candidate_boundary(
            outgoing,
            incoming,
            calendar_roll_date=dates[3],
            expiration=dates[4],
            required_sessions=2,
            extension_sessions=0,
            warning=False,
        )
        self.assertTrue(result["calendar_fallback"])

    def test_06_two_session_rule_selects_consecutive_streak(self):
        outgoing, incoming, dates = series(
            date(2026, 1, 1),
            [100, 100, 100, 100, 100],
            [50, 150, 160, 50, 50],
        )
        result = _candidate_boundary(
            outgoing,
            incoming,
            calendar_roll_date=dates[3],
            expiration=dates[4],
            required_sessions=2,
            extension_sessions=0,
            warning=False,
        )
        self.assertFalse(result["calendar_fallback"])
        self.assertEqual(
            result["effective_roll_date"],
            dates[3],
        )

    def test_07_e0_rejects_trigger_effective_after_calendar(self):
        outgoing, incoming, dates = series(
            date(2026, 1, 1),
            [100, 100, 100, 100, 100],
            [50, 50, 50, 150, 50],
        )
        result = _candidate_boundary(
            outgoing,
            incoming,
            calendar_roll_date=dates[3],
            expiration=dates[4],
            required_sessions=1,
            extension_sessions=0,
            warning=False,
        )
        self.assertTrue(result["calendar_fallback"])

    def test_08_e1_allows_next_common_session(self):
        outgoing, incoming, dates = series(
            date(2026, 1, 1),
            [100, 100, 100, 100, 100],
            [50, 50, 50, 150, 50],
        )
        result = _candidate_boundary(
            outgoing,
            incoming,
            calendar_roll_date=dates[3],
            expiration=dates[4],
            required_sessions=1,
            extension_sessions=1,
            warning=False,
        )
        self.assertFalse(result["calendar_fallback"])
        self.assertEqual(
            result["effective_roll_date"],
            dates[4],
        )
        self.assertEqual(
            result["roll_offset_common_sessions"],
            1,
        )

    def test_09_warning_transition_is_forced_to_calendar(self):
        outgoing, incoming, dates = series(
            date(2026, 1, 1),
            [100, 100, 100, 100, 100],
            [150, 150, 150, 150, 150],
        )
        result = _candidate_boundary(
            outgoing,
            incoming,
            calendar_roll_date=dates[2],
            expiration=dates[4],
            required_sessions=1,
            extension_sessions=2,
            warning=True,
        )
        self.assertTrue(result["calendar_fallback"])
        self.assertEqual(
            result["trigger_type"],
            "CALENDAR_FALLBACK_WARNING",
        )
        self.assertFalse(
            result["selected_warning_volume"]
        )

    def test_10_no_boundary_after_expiry(self):
        outgoing, incoming, dates = series(
            date(2026, 1, 1),
            [100, 100, 100, 100, 100],
            [50, 50, 150, 150, 150],
        )
        result = _candidate_boundary(
            outgoing,
            incoming,
            calendar_roll_date=dates[2],
            expiration=dates[3],
            required_sessions=2,
            extension_sessions=3,
            warning=False,
        )
        self.assertLessEqual(
            result["effective_roll_date"],
            dates[3],
        )
        self.assertFalse(
            result["post_expiry_boundary"]
        )

    def test_11_zero_volume_is_observed(self):
        outgoing, incoming, dates = series(
            date(2026, 1, 1),
            [10, 0, 10, 10],
            [0, 1, 0, 0],
        )
        result = _candidate_boundary(
            outgoing,
            incoming,
            calendar_roll_date=dates[2],
            expiration=dates[3],
            required_sessions=1,
            extension_sessions=0,
            warning=False,
        )
        self.assertFalse(result["calendar_fallback"])

    def test_12_first_passing_candidate_is_selected(self):
        rows = [
            {
                "candidate_id": candidate_id,
                "selection_rank": index,
                "passes_selection_gates": (
                    index in (3, 5)
                ),
            }
            for index, candidate_id in enumerate(
                EXPECTED_CANDIDATE_IDS,
                start=1,
            )
        ]
        selected = select_candidate(
            rows,
            EXPECTED_CANDIDATE_IDS,
        )
        self.assertEqual(
            selected["candidate_id"],
            EXPECTED_CANDIDATE_IDS[2],
        )
        self.assertFalse(
            selected["construction_authorized"]
        )

    def test_13_no_candidate_selection_is_explicit(self):
        rows = [
            {
                "candidate_id": candidate_id,
                "selection_rank": index,
                "passes_selection_gates": False,
            }
            for index, candidate_id in enumerate(
                EXPECTED_CANDIDATE_IDS,
                start=1,
            )
        ]
        selected = select_candidate(
            rows,
            EXPECTED_CANDIDATE_IDS,
        )
        self.assertFalse(selected["selected"])
        self.assertIsNone(selected["candidate_id"])

    def test_14_semantic_hash_is_deterministic(self):
        rows = [{"a": 1, "b": "x"}]
        first = semantic_rows_hash(
            rows,
            ("a", "b"),
        )
        second = semantic_rows_hash(
            rows,
            ("a", "b"),
        )
        self.assertEqual(first, second)
        self.assertEqual(len(first), 64)

    def test_15_output_field_sets_are_nonempty_and_unique(self):
        for fields in (
            DAILY_VOLUME_FIELDS,
            CANDIDATE_TRANSITION_FIELDS,
            CANDIDATE_SUMMARY_FIELDS,
        ):
            self.assertTrue(fields)
            self.assertEqual(
                len(fields),
                len(set(fields)),
            )

    def test_16_implementation_requires_separate_authorization(self):
        source = (
            PROJECT_DIR / "exp021_diagnostic.py"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "exp021_diagnostic_authorization",
            source,
        )
        self.assertIn(
            "maximum_diagnostic_runs",
            source,
        )

    def test_17_implementation_has_no_strategy_execution(self):
        source = (
            PROJECT_DIR / "exp021_diagnostic.py"
        ).read_text(encoding="utf-8")
        prohibited = (
            "run_strategy(",
            "profit_factor(",
            "walk_forward(",
            "mcpt(",
            "paper_trade(",
            "live_trade(",
        )
        for token in prohibited:
            with self.subTest(token=token):
                self.assertNotIn(token, source)

    def test_18_diagnostic_does_not_write_continuous_series(self):
        source = (
            PROJECT_DIR / "exp021_diagnostic.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn(
            "write_parquet(",
            source,
        )
        self.assertIn(
            '"continuous_construction": False',
            source,
        )


if __name__ == "__main__":
    unittest.main()
