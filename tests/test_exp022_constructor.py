from __future__ import annotations

from datetime import date
import unittest

import numpy as np
import pandas as pd

from exp020_constructor_core import (
    SERIES_COLUMNS,
    apply_backward_adjustment,
)
from exp021_diagnostic_core import (
    CANDIDATE_TRANSITION_FIELDS,
)
from exp022_constructor_core import (
    EXPECTED_CALENDAR_FALLBACKS,
    EXPECTED_CLEAN_FALLBACKS,
    EXPECTED_CLEAN_TRANSITIONS,
    EXPECTED_VOLUME_TRANSITIONS,
    EXPECTED_WARNING_FALLBACKS,
    NONPRICE_COMPARISON_COLUMNS,
    SELECTED_METHOD,
    SELECTED_ROLL_LEDGER_FIELDS,
    adjusted_nonprice_fields_match,
    candidate_transition_semantic_hash,
    final_classification,
    ledger_checks,
    ledger_semantic_hash,
    normalise_candidate_transition_rows,
    parse_bool,
    select_locked_candidate_rows,
    selected_transition_counts,
)


def synthetic_rows():
    rows = []

    for sequence in range(1, 66):
        warning = sequence <= 23
        clean_fallback = sequence in (59, 60)
        fallback = warning or clean_fallback
        rows.append(
            {
                "candidate_id": SELECTED_METHOD,
                "selection_rank": 4,
                "transition_sequence": sequence,
                "outgoing_contract": f"OUT{sequence:02d}",
                "incoming_contract": f"IN{sequence:02d}",
                "expiration": "2026-12-18",
                "calendar_roll_date": "2026-12-11",
                "required_consecutive_sessions": 2,
                "maximum_effective_common_sessions_after_calendar": 3,
                "warning_transition": warning,
                "trigger_type": (
                    "CALENDAR_FALLBACK_WARNING"
                    if warning
                    else (
                        "CALENDAR_FALLBACK_NO_TRIGGER"
                        if clean_fallback
                        else "VOLUME_CROSSOVER"
                    )
                ),
                "trigger_session_1": (
                    ""
                    if fallback
                    else "2026-12-10"
                ),
                "trigger_session_2": (
                    ""
                    if fallback
                    else "2026-12-11"
                ),
                "effective_roll_date": (
                    "2026-12-11"
                    if fallback
                    else "2026-12-14"
                ),
                "roll_offset_common_sessions": (
                    0 if fallback else 1
                ),
                "calendar_fallback": fallback,
                "selected_warning_volume": False,
                "post_expiry_boundary": False,
                "boundary_in_common_overlap": True,
                "common_session_count": 14,
                "diagnostic_window_start": "2026-11-27",
                "diagnostic_window_end": "2026-12-16",
            }
        )

    return rows


class Exp022ConstructorTests(unittest.TestCase):
    def test_01_selected_method_is_locked(self):
        self.assertEqual(
            SELECTED_METHOD,
            "VOL_GT_OUT_2S_E3",
        )

    def test_02_expected_counts_are_locked(self):
        self.assertEqual(
            (
                EXPECTED_CLEAN_TRANSITIONS,
                EXPECTED_VOLUME_TRANSITIONS,
                EXPECTED_CALENDAR_FALLBACKS,
                EXPECTED_WARNING_FALLBACKS,
                EXPECTED_CLEAN_FALLBACKS,
            ),
            (42, 40, 25, 23, 2),
        )

    def test_03_ledger_fields_are_unique(self):
        self.assertEqual(
            len(SELECTED_ROLL_LEDGER_FIELDS),
            len(set(SELECTED_ROLL_LEDGER_FIELDS)),
        )

    def test_04_nonprice_columns_are_locked(self):
        self.assertEqual(
            NONPRICE_COMPARISON_COLUMNS,
            (
                "ts_event",
                "volume",
                "instrument_id",
                "source_contract",
                "roll_method",
                "trading_date",
            ),
        )

    def test_05_parse_bool_accepts_locked_encodings(self):
        for value in (True, 1, "true", "Yes"):
            with self.subTest(value=value):
                self.assertTrue(parse_bool(value))

        for value in (False, 0, "false", "No"):
            with self.subTest(value=value):
                self.assertFalse(parse_bool(value))

    def test_06_parse_bool_rejects_unknown_values(self):
        with self.assertRaises(ValueError):
            parse_bool("maybe")

    def test_07_normalisation_restores_types(self):
        row = synthetic_rows()[0]
        raw = {
            key: str(value)
            for key, value in row.items()
        }
        raw["trigger_session_1"] = np.nan
        raw["trigger_session_2"] = np.nan
        frame = pd.DataFrame([raw])

        normalised = normalise_candidate_transition_rows(
            frame
        )[0]

        self.assertIsInstance(
            normalised["selection_rank"],
            int,
        )
        self.assertIsInstance(
            normalised["warning_transition"],
            bool,
        )
        self.assertEqual(
            normalised["trigger_session_1"],
            "",
        )

    def test_08_missing_transition_field_is_rejected(self):
        frame = pd.DataFrame(synthetic_rows()).drop(
            columns=["effective_roll_date"]
        )
        with self.assertRaisesRegex(
            ValueError,
            "Missing EXP-021",
        ):
            normalise_candidate_transition_rows(
                frame
            )

    def test_09_selected_rows_validate(self):
        selected = select_locked_candidate_rows(
            synthetic_rows()
        )
        self.assertEqual(len(selected), 65)

    def test_10_selected_sequence_mutation_is_rejected(self):
        rows = synthetic_rows()
        rows[0]["transition_sequence"] = 2

        with self.assertRaisesRegex(
            ValueError,
            "sequence changed",
        ):
            select_locked_candidate_rows(rows)

    def test_11_selected_parameter_mutation_is_rejected(self):
        rows = synthetic_rows()
        rows[0][
            "required_consecutive_sessions"
        ] = 1

        with self.assertRaisesRegex(
            ValueError,
            "parameters changed",
        ):
            select_locked_candidate_rows(rows)

    def test_12_selected_count_mutation_is_rejected(self):
        rows = synthetic_rows()
        rows[23]["calendar_fallback"] = True

        with self.assertRaisesRegex(
            ValueError,
            "counts changed",
        ):
            select_locked_candidate_rows(rows)

    def test_13_selected_counts_are_reported(self):
        counts = selected_transition_counts(
            synthetic_rows()
        )
        self.assertEqual(
            counts,
            {
                "transition_count": 65,
                "clean_transition_count": 42,
                "volume_driven_transition_count": 40,
                "calendar_fallback_count": 25,
                "warning_calendar_fallback_count": 23,
                "clean_calendar_fallback_count": 2,
            },
        )

    def test_14_candidate_hash_is_deterministic(self):
        rows = synthetic_rows()
        self.assertEqual(
            candidate_transition_semantic_hash(rows),
            candidate_transition_semantic_hash(rows),
        )

    def test_15_ledger_hash_is_order_sensitive_by_sequence(self):
        rows = [
            {
                "transition_sequence": 2,
                "value": "b",
            },
            {
                "transition_sequence": 1,
                "value": "a",
            },
        ]
        self.assertEqual(
            ledger_semantic_hash(rows),
            ledger_semantic_hash(
                list(reversed(rows))
            ),
        )

    def test_16_ledger_checks_accept_valid_minimal_ledger(self):
        rows = []

        for sequence in range(1, 66):
            rows.append(
                {
                    "transition_sequence": sequence,
                    "outgoing_contract": f"O{sequence}",
                    "incoming_contract": f"I{sequence}",
                    "roll_trading_date": (
                        date(
                            2000 + sequence // 4,
                            (sequence % 12) + 1,
                            1,
                        ).isoformat()
                    ),
                    "outgoing_expiration": "2099-12-31",
                    "common_overlap_sessions": 10,
                    "roll_boundary_utc": "2026-01-01T23:00:00+00:00",
                    "reference_timestamp_utc": "2026-01-01T22:59:00+00:00",
                    "outgoing_reference_close": 100.0,
                    "incoming_reference_close": 101.0,
                    "roll_difference_points": 1.0,
                }
            )

        checks = ledger_checks(rows)
        self.assertTrue(all(checks.values()))

    def test_17_nonprice_fields_match(self):
        frame = pd.DataFrame(
            {
                "ts_event": pd.to_datetime(
                    ["2026-01-01T00:00:00Z"]
                ),
                "open": [100.0],
                "high": [101.0],
                "low": [99.0],
                "close": [100.5],
                "volume": [5],
                "instrument_id": [1],
                "source_contract": ["NQH26"],
                "roll_method": [SELECTED_METHOD],
                "trading_date": [
                    date(2026, 1, 1)
                ],
                "adjustment_points": [0.0],
            }
        )
        adjusted = frame.copy()
        for column in ("open", "high", "low", "close"):
            adjusted[column] += 1.0
        adjusted["adjustment_points"] = 1.0

        self.assertTrue(
            adjusted_nonprice_fields_match(
                frame,
                adjusted,
            )
        )

    def test_18_nonprice_mutation_is_detected(self):
        frame = pd.DataFrame(
            {
                "ts_event": pd.to_datetime(
                    ["2026-01-01T00:00:00Z"]
                ),
                "volume": [5],
                "instrument_id": [1],
                "source_contract": ["A"],
                "roll_method": [SELECTED_METHOD],
                "trading_date": [
                    date(2026, 1, 1)
                ],
            }
        )
        adjusted = frame.copy()
        adjusted["volume"] = 6

        self.assertFalse(
            adjusted_nonprice_fields_match(
                frame,
                adjusted,
            )
        )

    def test_19_final_classification_requires_all_checks(self):
        self.assertEqual(
            final_classification(
                {"a": True, "b": True}
            ),
            (
                "QUALIFIED_AS_SELECTED_VOLUME_ROLL_"
                "CONTINUOUS_SERIES"
            ),
        )
        self.assertEqual(
            final_classification(
                {"a": True, "b": False}
            ),
            "CONSTRUCTION_NOT_QUALIFIED",
        )

    def test_20_series_columns_remain_compatible(self):
        self.assertEqual(
            tuple(SERIES_COLUMNS),
            (
                "ts_event",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "instrument_id",
                "source_contract",
                "roll_method",
                "trading_date",
                "adjustment_points",
            ),
        )


if __name__ == "__main__":
    unittest.main()
