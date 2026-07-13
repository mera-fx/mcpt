from __future__ import annotations

from dataclasses import replace
from datetime import date
from pathlib import Path
import unittest

import numpy as np
import pandas as pd

from exp005_missing_session_resolution import (
    get_exp005_missing_session_resolution,
    validate_exp005_missing_session_resolution,
)
from exp005_quantower_import import (
    IncompleteExportError,
    RawFileRecord,
    SymbolImport,
    expected_cash_index,
    validate_locked_provider_unavailable_sessions,
)


def market_rows(
    index: pd.DatetimeIndex,
) -> pd.DataFrame:
    values = (
        9_000.0
        + np.arange(len(index)) * 0.25
    )

    return pd.DataFrame(
        {
            "open": values,
            "high": values + 0.50,
            "low": values - 0.50,
            "close": values + 0.25,
            "volume": np.arange(
                len(index)
            ) + 1,
        },
        index=index.tz_convert("UTC"),
    )


def required_records(
    symbol: str,
) -> tuple[RawFileRecord, ...]:
    record = get_exp005_missing_session_resolution()
    hashes = record[
        "required_source_hashes"
    ][symbol]

    return tuple(
        RawFileRecord(
            symbol=symbol,
            source_path=f"{name}.csv",
            filename=f"{name}.csv",
            sha256=digest,
            size_bytes=1,
            rows=1,
            first_timestamp_utc=(
                "2019-05-06T00:00:00+00:00"
            ),
            last_timestamp_utc=(
                "2020-07-22T00:00:00+00:00"
            ),
        )
        for name, digest in hashes.items()
    )


def symbol_imports(
) -> tuple[SymbolImport, SymbolImport]:
    may = expected_cash_index(
        date(2019, 5, 6)
    )
    june = expected_cash_index(
        date(2019, 6, 17)
    )

    nq_frame = pd.concat(
        [
            market_rows(may),
            market_rows(june),
        ]
    ).sort_index()

    may_mnq = may[
        may.time
        >= pd.Timestamp(
            "10:47"
        ).time()
    ]

    missing_june = {
        "12:24",
        "13:12",
        "13:25",
        "13:29",
        "13:31",
        "13:32",
        "13:33",
        "13:53",
        "14:33",
        "14:39",
        "14:43",
        "14:44",
    }

    june_mnq = june[
        [
            timestamp.strftime(
                "%H:%M"
            )
            not in missing_june
            for timestamp in june
        ]
    ]

    mnq_frame = pd.concat(
        [
            market_rows(may_mnq),
            market_rows(june_mnq),
        ]
    ).sort_index()

    return (
        SymbolImport(
            symbol="NQ",
            frame=nq_frame,
            files=required_records("NQ"),
            duplicate_overlap_rows_removed=0,
        ),
        SymbolImport(
            symbol="MNQ",
            frame=mnq_frame,
            files=required_records("MNQ"),
            duplicate_overlap_rows_removed=0,
        ),
    )


def missing_expected_rows(
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "symbol": "MNQ",
                "session_date": "2019-05-06",
            },
            {
                "symbol": "MNQ",
                "session_date": "2019-06-17",
            },
            {
                "symbol": "NQ,MNQ",
                "session_date": "2020-07-21",
            },
        ]
    )


class Exp005MissingSessionResolutionTests(
    unittest.TestCase
):
    def test_record_is_valid(
        self,
    ) -> None:
        validate_exp005_missing_session_resolution()

    def test_exact_locked_profiles_are_accepted(
        self,
    ) -> None:
        nq, mnq = symbol_imports()

        exclusions = (
            validate_locked_provider_unavailable_sessions(
                nq_import=nq,
                mnq_import=mnq,
                missing_expected=missing_expected_rows(),
            )
        )

        self.assertEqual(
            len(exclusions),
            3,
        )
        self.assertEqual(
            set(exclusions["symbol"]),
            {"BOTH"},
        )
        self.assertEqual(
            int(
                exclusions[
                    "bars_synthesized"
                ].sum()
            ),
            0,
        )

    def test_changed_missing_minute_pattern_stops(
        self,
    ) -> None:
        nq, mnq = symbol_imports()
        changed = mnq.frame.drop(
            mnq.frame.index[
                mnq.frame.index
                == pd.Timestamp(
                    "2019-06-17T16:25:00+00:00"
                )
            ]
        )

        changed_mnq = replace(
            mnq,
            frame=changed,
        )

        with self.assertRaisesRegex(
            IncompleteExportError,
            "profile changed",
        ):
            validate_locked_provider_unavailable_sessions(
                nq_import=nq,
                mnq_import=changed_mnq,
                missing_expected=missing_expected_rows(),
            )

    def test_missing_retry_hash_stops(
        self,
    ) -> None:
        nq, mnq = symbol_imports()
        shortened = replace(
            mnq,
            files=mnq.files[:-1],
        )

        with self.assertRaisesRegex(
            IncompleteExportError,
            "missing a locked",
        ):
            validate_locked_provider_unavailable_sessions(
                nq_import=nq,
                mnq_import=shortened,
                missing_expected=missing_expected_rows(),
            )

    def test_unrecorded_incomplete_session_stops(
        self,
    ) -> None:
        nq, mnq = symbol_imports()
        extra = pd.concat(
            [
                missing_expected_rows(),
                pd.DataFrame(
                    [
                        {
                            "symbol": "NQ",
                            "session_date": "2021-01-04",
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )

        with self.assertRaisesRegex(
            IncompleteExportError,
            "does not exactly match",
        ):
            validate_locked_provider_unavailable_sessions(
                nq_import=nq,
                mnq_import=mnq,
                missing_expected=extra,
            )


if __name__ == "__main__":
    unittest.main()
