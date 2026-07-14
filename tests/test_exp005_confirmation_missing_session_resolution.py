from __future__ import annotations

from copy import deepcopy
from datetime import date
import unittest

import numpy as np
import pandas as pd

import exp005_quantower_import as base
from exp005_confirmation_missing_session_resolution import (
    ConfirmationSessionRetryEvidence,
    EXP005_CONFIRMATION_MISSING_SESSION_RESOLUTION,
    _observed_retry_profile,
    get_exp005_confirmation_missing_session_resolution,
    locked_confirmation_excluded_dates,
    restore_locked_confirmation_session,
    validate_exp005_confirmation_missing_session_resolution,
    validate_locked_confirmation_missing_sessions,
)


def make_cash_frame(
    session_text: str,
    *,
    periods: int = 390,
) -> pd.DataFrame:
    index = pd.date_range(
        f"{session_text} 09:30",
        periods=periods,
        freq="min",
        tz=base.NEW_YORK_TZ,
    ).tz_convert("UTC")

    frame = pd.DataFrame(
        {
            "open": np.full(periods, 100.0),
            "high": np.full(periods, 100.25),
            "low": np.full(periods, 99.75),
            "close": np.full(periods, 100.0),
            "volume": np.arange(
                1,
                periods + 1,
                dtype=float,
            ),
        },
        index=index,
    )
    frame.index.name = "timestamp"

    return frame


class Exp005ConfirmationMissingSessionResolutionTests(
    unittest.TestCase
):
    def test_record_is_valid(
        self,
    ) -> None:
        validate_exp005_confirmation_missing_session_resolution()

    def test_locked_dates_are_exact(
        self,
    ) -> None:
        self.assertEqual(
            locked_confirmation_excluded_dates(),
            (
                date(2025, 9, 24),
                date(2025, 11, 7),
            ),
        )

    def test_six_retry_hashes_are_unique(
        self,
    ) -> None:
        record = (
            get_exp005_confirmation_missing_session_resolution()
        )
        hashes = [
            specification["sha256"]
            for symbol in ("NQ", "MNQ")
            for specification in record[
                "retry_files"
            ][symbol].values()
        ]

        self.assertEqual(
            len(hashes),
            6,
        )
        self.assertEqual(
            len(set(hashes)),
            6,
        )
        self.assertTrue(
            all(
                len(item) == 64
                for item in hashes
            )
        )

    def test_locked_output_counts_are_exact(
        self,
    ) -> None:
        result = (
            EXP005_CONFIRMATION_MISSING_SESSION_RESOLUTION[
                "result"
            ]
        )

        self.assertEqual(
            result["expected_included_sessions"],
            742,
        )
        self.assertEqual(
            result[
                "expected_one_minute_rows_per_symbol"
            ],
            289380,
        )
        self.assertEqual(
            result[
                "expected_five_minute_rows_per_symbol"
            ],
            57876,
        )
        self.assertEqual(
            result["bars_synthesized"],
            0,
        )

    def test_observed_profile_detects_single_missing_minute(
        self,
    ) -> None:
        frame = make_cash_frame(
            "2025-09-24"
        )
        local = frame.index.tz_convert(
            base.NEW_YORK_TZ
        )
        frame = frame.loc[
            local.time
            != pd.Timestamp(
                "10:59"
            ).time()
        ]

        observed = _observed_retry_profile(
            frame,
            session_date=date(
                2025,
                9,
                24,
            ),
        )

        self.assertEqual(
            observed["actual_bars"],
            389,
        )
        self.assertEqual(
            observed["missing_times"],
            ["10:59"],
        )
        self.assertEqual(
            observed["unexpected_bars"],
            0,
        )

    def test_exact_missing_set_is_accepted(
        self,
    ) -> None:
        missing = pd.DataFrame(
            [
                {
                    "symbol": "NQ,MNQ",
                    "session_date": "2025-09-24",
                },
                {
                    "symbol": "NQ,MNQ",
                    "session_date": "2025-11-07",
                },
            ]
        )

        exclusions = (
            validate_locked_confirmation_missing_sessions(
                missing_expected=missing,
            )
        )

        self.assertEqual(
            len(exclusions),
            2,
        )
        self.assertTrue(
            exclusions[
                "bars_synthesized"
            ].eq(0).all()
        )

    def test_changed_missing_set_stops(
        self,
    ) -> None:
        missing = pd.DataFrame(
            [
                {
                    "symbol": "NQ,MNQ",
                    "session_date": "2025-09-24",
                },
            ]
        )

        with self.assertRaisesRegex(
            base.IncompleteExportError,
            "does not exactly match",
        ):
            validate_locked_confirmation_missing_sessions(
                missing_expected=missing,
            )

    def test_complete_retry_replaces_incomplete_cash_session(
        self,
    ) -> None:
        complete = make_cash_frame(
            "2025-12-31"
        )
        incomplete = complete.iloc[
            :100
        ].copy()
        imported = base.SymbolImport(
            symbol="NQ",
            frame=incomplete,
            files=tuple(),
            duplicate_overlap_rows_removed=0,
        )
        evidence = (
            ConfirmationSessionRetryEvidence(
                symbol="NQ",
                cash_sessions={
                    "2025-12-31": complete,
                },
                records=tuple(),
            )
        )

        restored, original_bars = (
            restore_locked_confirmation_session(
                imported,
                evidence,
            )
        )

        self.assertEqual(
            original_bars,
            100,
        )
        self.assertEqual(
            len(restored.frame),
            390,
        )
        self.assertFalse(
            restored.frame.index.has_duplicates
        )

    def test_complete_original_session_is_not_overwritten(
        self,
    ) -> None:
        complete = make_cash_frame(
            "2025-12-31"
        )
        imported = base.SymbolImport(
            symbol="MNQ",
            frame=complete,
            files=tuple(),
            duplicate_overlap_rows_removed=0,
        )
        evidence = (
            ConfirmationSessionRetryEvidence(
                symbol="MNQ",
                cash_sessions={
                    "2025-12-31": complete,
                },
                records=tuple(),
            )
        )

        with self.assertRaisesRegex(
            base.QuantowerImportError,
            "was not missing or incomplete",
        ):
            restore_locked_confirmation_session(
                imported,
                evidence,
            )

    def test_mutated_record_is_rejected(
        self,
    ) -> None:
        record = deepcopy(
            EXP005_CONFIRMATION_MISSING_SESSION_RESOLUTION
        )
        record["result"][
            "bars_synthesized"
        ] = 1

        with self.assertRaisesRegex(
            ValueError,
            "result changed",
        ):
            validate_exp005_confirmation_missing_session_resolution(
                record
            )


if __name__ == "__main__":
    unittest.main()
