from __future__ import annotations

from datetime import date
import unittest

import pandas as pd

import exp005_quantower_import as base
from advance_exp005_to_full_validation import (
    replace_exp005_lifecycle_block,
)
from exp005_confirmation_import import (
    CALENDAR_SHA256,
    CONFIRMATION_END,
    CONFIRMATION_START,
    _confirmation_cash_only,
    confirmation_period_context,
    load_confirmation_calendar,
    sha256_file,
    CALENDAR_FILE,
)


class Exp005ConfirmationImportTests(
    unittest.TestCase
):
    def test_frozen_calendar_is_valid(
        self,
    ) -> None:
        sessions = load_confirmation_calendar()

        self.assertEqual(
            len(sessions),
            744,
        )
        self.assertEqual(
            sessions[0],
            CONFIRMATION_START,
        )
        self.assertEqual(
            sessions[-1],
            CONFIRMATION_END,
        )
        self.assertEqual(
            sha256_file(CALENDAR_FILE),
            CALENDAR_SHA256,
        )

    def test_early_closes_are_not_full_sessions(
        self,
    ) -> None:
        sessions = set(
            load_confirmation_calendar()
        )

        excluded = {
            date(2023, 7, 3),
            date(2023, 11, 24),
            date(2024, 7, 3),
            date(2024, 11, 29),
            date(2024, 12, 24),
            date(2025, 7, 3),
            date(2025, 11, 28),
            date(2025, 12, 24),
        }

        self.assertTrue(
            excluded.isdisjoint(sessions)
        )

    def test_confirmation_cash_filter_accepts_period(
        self,
    ) -> None:
        index = pd.date_range(
            "2023-01-03 14:30:00+00:00",
            periods=2,
            freq="1min",
        )
        frame = pd.DataFrame(
            {
                "open": [1.0, 1.0],
                "high": [1.0, 1.0],
                "low": [1.0, 1.0],
                "close": [1.0, 1.0],
                "volume": [1.0, 1.0],
            },
            index=index,
        )

        cash = _confirmation_cash_only(
            frame
        )

        self.assertEqual(
            len(cash),
            2,
        )

    def test_confirmation_cash_filter_rejects_quick_period(
        self,
    ) -> None:
        index = pd.date_range(
            "2022-12-30 14:30:00+00:00",
            periods=1,
            freq="1min",
        )
        frame = pd.DataFrame(
            {
                "open": [1.0],
                "high": [1.0],
                "low": [1.0],
                "close": [1.0],
                "volume": [1.0],
            },
            index=index,
        )

        with self.assertRaisesRegex(
            base.ProtectedPeriodError,
            "outside the unlocked",
        ):
            _confirmation_cash_only(frame)

    def test_confirmation_context_restores_quick_period(
        self,
    ) -> None:
        original_start = base.QUICK_START
        original_end = base.QUICK_END
        original_cash = base._cash_only

        with confirmation_period_context():
            self.assertEqual(
                base.QUICK_START,
                CONFIRMATION_START,
            )
            self.assertEqual(
                base.QUICK_END,
                CONFIRMATION_END,
            )
            self.assertIs(
                base._cash_only,
                _confirmation_cash_only,
            )

        self.assertEqual(
            base.QUICK_START,
            original_start,
        )
        self.assertEqual(
            base.QUICK_END,
            original_end,
        )
        self.assertIs(
            base._cash_only,
            original_cash,
        )

    def test_lifecycle_patch_advances_only_exp005(
        self,
    ) -> None:
        source = """from pathlib import Path

EXPERIMENT_LIFECYCLE = {
    "EXP-004": ExperimentLifecycle(
        experiment_id="EXP-004",
        stage="REJECTED",
    ),
    "EXP-005": ExperimentLifecycle(
        experiment_id="EXP-005",
        experiment_name=(
            "NQ/MNQ 5-Minute ORB Locked Transfer"
        ),
        hypothesis=(
            "The unchanged fixed EXP-004 opening-range rules may "
            "transfer from QQQ to Nasdaq-100 futures and remain "
            "profitable after contract-specific futures costs."
        ),
        stage="PRE_REGISTERED",
        stage_reason=(
            "Lucid/Rithmic source was locked."
        ),
        next_action=(
            "Export 2019-05-06 through 2022-12-30. "
            "Keep 2023–2025 unexported."
        ),
        market_name="NQ / MNQ futures",
        timeframe="5 minutes",
        strategy_name="opening_range_breakout_locked_transfer",
        preregistration_file=Path(
            "research/EXP-005_preregistration.md"
        ),
    ),
}


def normalize_experiment_id(value: str) -> str:
    return value
"""

        updated = replace_exp005_lifecycle_block(
            source
        )

        self.assertIn(
            'stage="FULL_VALIDATION"',
            updated,
        )
        self.assertIn(
            'stage="REJECTED"',
            updated,
        )
        self.assertIn(
            "Do not rerun the quick transfer",
            updated,
        )

    def test_lifecycle_patch_is_idempotent(
        self,
    ) -> None:
        source = """from pathlib import Path

EXPERIMENT_LIFECYCLE = {
    "EXP-005": ExperimentLifecycle(
        experiment_id="EXP-005",
        stage="PRE_REGISTERED",
        stage_reason=(
            "Lucid/Rithmic"
        ),
        next_action=(
            "2019-05-06 through 2022-12-30. "
            "Keep 2023–2025 unexported."
        ),
    ),
}


def normalize_experiment_id(value: str) -> str:
    return value
"""

        first = replace_exp005_lifecycle_block(
            source
        )
        second = replace_exp005_lifecycle_block(
            first
        )

        self.assertEqual(
            first,
            second,
        )


if __name__ == "__main__":
    unittest.main()
