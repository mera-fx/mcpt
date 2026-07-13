from __future__ import annotations

from datetime import date
from pathlib import Path
import tempfile
import unittest

import numpy as np
import pandas as pd

from exp005_quantower_import import (
    AlignmentError,
    IncompleteExportError,
    ProtectedPeriodError,
    QuantowerImportError,
    SessionExtraction,
    aggregate_to_five_minutes,
    align_nq_mnq,
    archive_raw_files,
    build_processed_dataset,
    dataframe_sha256,
    expected_cash_index,
    extract_complete_sessions,
    load_expected_full_sessions,
    load_symbol_chunks,
    read_quantower_csv,
    sha256_file,
)


def write_quantower_csv(
    path: Path,
    index: pd.DatetimeIndex,
    *,
    base: float = 8_000.0,
    price_offset: float = 0.0,
    break_interval: bool = False,
    invalid_ohlc: bool = False,
) -> None:
    values = (
        base
        + price_offset
        + np.arange(len(index)) * 0.25
    )

    frame = pd.DataFrame(
        {
            "Time left": (
                index.tz_convert("UTC")
                .tz_localize(None)
                .strftime("%Y-%m-%d %H:%M:%S.000")
            ),
            "Time right": (
                (
                    index.tz_convert("UTC")
                    .tz_localize(None)
                    + pd.Timedelta(
                        seconds=59,
                        milliseconds=999,
                    )
                )
                .strftime("%Y-%m-%d %H:%M:%S.%f")
                .str[:-3]
            ),
            "Open": values,
            "High": values + 0.50,
            "Median": values + 0.25,
            "Low": values - 0.50,
            "Close": values + 0.25,
            "Typical": values + 0.0833333333,
            "Volume": np.arange(len(index)) + 1,
            "Quote asset volume": 0,
            "Weighted": values + 0.125,
            "": "",
        }
    )

    if break_interval:
        frame.loc[0, "Time right"] = (
            index[0].tz_convert("UTC")
            .tz_localize(None)
            .strftime("%Y-%m-%d %H:%M:%S.000")
        )

    if invalid_ohlc:
        frame.loc[0, "High"] = (
            frame.loc[0, "Low"] - 0.25
        )

    frame.to_csv(
        path,
        sep=";",
        index=False,
    )


def make_full_session(
    session: date,
) -> pd.DatetimeIndex:
    return expected_cash_index(
        session
    ).tz_convert("UTC")


def write_qqq_calendar(
    path: Path,
    sessions: list[date],
) -> None:
    pieces: list[pd.DataFrame] = []

    for session in sessions:
        index = pd.date_range(
            pd.Timestamp.combine(
                session,
                pd.Timestamp("09:30").time(),
            ).tz_localize(
                "America/New_York"
            ),
            periods=78,
            freq="5min",
        ).tz_convert("UTC")

        pieces.append(
            pd.DataFrame(
                {
                    "open": 100.0,
                    "high": 101.0,
                    "low": 99.0,
                    "close": 100.5,
                    "volume": 1_000,
                    "session_date": (
                        session.isoformat()
                    ),
                    "slot": np.arange(78),
                },
                index=index,
            )
        )

    data = pd.concat(
        pieces,
        axis=0,
    )

    data.index.name = "timestamp"
    data.to_csv(path, index=True)


class Exp005QuantowerImportTests(
    unittest.TestCase
):
    def test_valid_quantower_csv_is_parsed(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "NQ.csv"
            index = make_full_session(
                date(2019, 8, 9)
            )

            write_quantower_csv(
                path,
                index,
            )

            frame, record = read_quantower_csv(
                path,
                symbol="NQ",
            )

            self.assertEqual(
                len(frame),
                390,
            )
            self.assertEqual(
                str(frame.index.tz),
                "UTC",
            )
            self.assertEqual(
                record.sha256,
                sha256_file(path),
            )


def test_identical_duplicates_inside_one_file_are_removed(
    self,
) -> None:
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp) / "NQ.csv"
        index = make_full_session(
            date(2019, 8, 9)
        )

        write_quantower_csv(
            path,
            index,
        )

        raw = pd.read_csv(
            path,
            sep=";",
        )

        raw = pd.concat(
            [
                raw,
                raw.iloc[[125]],
            ],
            ignore_index=True,
        )

        raw.to_csv(
            path,
            sep=";",
            index=False,
        )

        frame, record = read_quantower_csv(
            path,
            symbol="NQ",
        )

        self.assertEqual(
            len(frame),
            390,
        )
        self.assertEqual(
            record.duplicate_rows_removed,
            1,
        )
        self.assertFalse(
            frame.index.has_duplicates
        )

def test_conflicting_duplicates_inside_one_file_are_rejected(
    self,
) -> None:
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp) / "NQ.csv"
        index = make_full_session(
            date(2019, 8, 9)
        )

        write_quantower_csv(
            path,
            index,
        )

        raw = pd.read_csv(
            path,
            sep=";",
        )

        conflicting = raw.iloc[[125]].copy()
        conflicting.loc[
            conflicting.index[0],
            "Close",
        ] += 0.25

        raw = pd.concat(
            [
                raw,
                conflicting,
            ],
            ignore_index=True,
        )

        raw.to_csv(
            path,
            sep=";",
            index=False,
        )

        with self.assertRaisesRegex(
            QuantowerImportError,
            "conflicting duplicate timestamp",
        ):
            read_quantower_csv(
                path,
                symbol="NQ",
            )

    def test_bad_one_minute_interval_is_rejected(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "NQ.csv"
            write_quantower_csv(
                path,
                make_full_session(
                    date(2019, 8, 9)
                ),
                break_interval=True,
            )

            with self.assertRaisesRegex(
                QuantowerImportError,
                "exact one-minute",
            ):
                read_quantower_csv(
                    path,
                    symbol="NQ",
                )

    def test_invalid_ohlc_is_rejected(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "NQ.csv"
            write_quantower_csv(
                path,
                make_full_session(
                    date(2019, 8, 9)
                ),
                invalid_ohlc=True,
            )

            with self.assertRaisesRegex(
                QuantowerImportError,
                "invalid OHLC",
            ):
                read_quantower_csv(
                    path,
                    symbol="NQ",
                )

    def test_identical_overlap_is_deduplicated(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            index = make_full_session(
                date(2019, 8, 9)
            )
            first = root / "NQ_a.csv"
            second = root / "NQ_b.csv"

            write_quantower_csv(
                first,
                index,
            )
            write_quantower_csv(
                second,
                index,
            )

            loaded = load_symbol_chunks(
                [first, second],
                symbol="NQ",
            )

            self.assertEqual(
                len(loaded.frame),
                390,
            )
            self.assertEqual(
                loaded.duplicate_overlap_rows_removed,
                390,
            )

    def test_conflicting_overlap_is_rejected(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            index = make_full_session(
                date(2019, 8, 9)
            )
            first = root / "NQ_a.csv"
            second = root / "NQ_b.csv"

            write_quantower_csv(
                first,
                index,
            )
            write_quantower_csv(
                second,
                index,
                price_offset=0.25,
            )

            with self.assertRaisesRegex(
                QuantowerImportError,
                "disagree",
            ):
                load_symbol_chunks(
                    [first, second],
                    symbol="NQ",
                )

    def test_summer_utc_session_maps_to_new_york(
        self,
    ) -> None:
        index = make_full_session(
            date(2019, 8, 9)
        )

        self.assertEqual(
            index[0],
            pd.Timestamp(
                "2019-08-09 13:30:00+00:00"
            ),
        )
        self.assertEqual(
            index[-1],
            pd.Timestamp(
                "2019-08-09 19:59:00+00:00"
            ),
        )

    def test_winter_utc_session_maps_to_new_york(
        self,
    ) -> None:
        index = make_full_session(
            date(2019, 12, 9)
        )

        self.assertEqual(
            index[0],
            pd.Timestamp(
                "2019-12-09 14:30:00+00:00"
            ),
        )
        self.assertEqual(
            index[-1],
            pd.Timestamp(
                "2019-12-09 20:59:00+00:00"
            ),
        )

    def test_confirmation_cash_rows_are_rejected(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "NQ.csv"
            write_quantower_csv(
                path,
                make_full_session(
                    date(2023, 1, 3)
                ),
            )

            loaded = load_symbol_chunks(
                [path],
                symbol="NQ",
            )

            with self.assertRaisesRegex(
                ProtectedPeriodError,
                "Do not export 2023",
            ):
                extract_complete_sessions(
                    loaded,
                    expected_sessions=[
                        date(2019, 8, 9)
                    ],
                )

    def test_qqq_calendar_provides_full_sessions(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "QQQ.csv"
            sessions = [
                date(2019, 8, 9),
                date(2019, 8, 12),
            ]

            write_qqq_calendar(
                path,
                sessions,
            )

            self.assertEqual(
                load_expected_full_sessions(
                    path
                ),
                tuple(sessions),
            )

    def test_complete_session_aggregates_to_78_bars(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "NQ.csv"
            session = date(2019, 8, 9)

            write_quantower_csv(
                path,
                make_full_session(session),
            )

            loaded = load_symbol_chunks(
                [path],
                symbol="NQ",
            )

            extracted = extract_complete_sessions(
                loaded,
                expected_sessions=[session],
            )

            aggregated = aggregate_to_five_minutes(
                extracted.data
            )

            self.assertEqual(
                len(extracted.data),
                390,
            )
            self.assertEqual(
                len(aggregated),
                78,
            )
            self.assertEqual(
                aggregated.iloc[0]["open"],
                extracted.data.iloc[0]["open"],
            )
            self.assertEqual(
                aggregated.iloc[0]["close"],
                extracted.data.iloc[4]["close"],
            )

    def test_missing_expected_session_blocks_import(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            qqq = root / "QQQ.csv"
            nq = root / "NQ.csv"
            mnq = root / "MNQ.csv"

            sessions = [
                date(2019, 8, 9),
                date(2019, 8, 12),
            ]

            write_qqq_calendar(
                qqq,
                sessions,
            )

            write_quantower_csv(
                nq,
                make_full_session(
                    sessions[0]
                ),
            )
            write_quantower_csv(
                mnq,
                make_full_session(
                    sessions[0]
                ),
            )

            with self.assertRaisesRegex(
                IncompleteExportError,
                "expected full sessions",
            ):
                build_processed_dataset(
                    nq_paths=[nq],
                    mnq_paths=[mnq],
                    qqq_calendar_path=qqq,
                    archive_files=False,
                )

    def test_front_month_mismatch_session_is_excluded(
        self,
    ) -> None:
        first = date(2019, 8, 9)
        second = date(2019, 8, 12)

        nq_pieces: list[pd.DataFrame] = []
        mnq_pieces: list[pd.DataFrame] = []

        for session in (first, second):
            index = make_full_session(
                session
            )

            nq_frame = pd.DataFrame(
                {
                    "open": 8_000.0,
                    "high": 8_000.5,
                    "low": 7_999.5,
                    "close": 8_000.25,
                    "volume": 100,
                    "session_date": (
                        session.isoformat()
                    ),
                    "minute_slot": np.arange(390),
                },
                index=index,
            )

            mnq_frame = nq_frame.copy()

            if session == second:
                mnq_frame[
                    ["open", "high", "low", "close"]
                ] -= 25.0

            nq_pieces.append(nq_frame)
            mnq_pieces.append(mnq_frame)

        nq = SessionExtraction(
            symbol="NQ",
            data=pd.concat(nq_pieces),
            incomplete_sessions=pd.DataFrame(),
            unexpected_sessions=pd.DataFrame(),
        )

        mnq = SessionExtraction(
            symbol="MNQ",
            data=pd.concat(mnq_pieces),
            incomplete_sessions=pd.DataFrame(),
            unexpected_sessions=pd.DataFrame(),
        )

        aligned = align_nq_mnq(
            nq,
            mnq,
        )

        self.assertEqual(
            aligned.nq_1m[
                "session_date"
            ].nunique(),
            1,
        )
        self.assertEqual(
            aligned.excluded_mismatch_sessions.iloc[0][
                "reason"
            ],
            "potential_front_month_mismatch",
        )

    def test_successful_build_creates_aligned_data(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            qqq = root / "QQQ.csv"
            nq = root / "NQ.csv"
            mnq = root / "MNQ.csv"
            session = date(2019, 8, 9)

            write_qqq_calendar(
                qqq,
                [session],
            )

            index = make_full_session(
                session
            )

            write_quantower_csv(
                nq,
                index,
            )
            write_quantower_csv(
                mnq,
                index,
                price_offset=0.25,
            )

            processed = build_processed_dataset(
                nq_paths=[nq],
                mnq_paths=[mnq],
                qqq_calendar_path=qqq,
                archive_files=False,
            )

            self.assertTrue(
                processed.nq_1m.index.equals(
                    processed.mnq_1m.index
                )
            )
            self.assertTrue(
                processed.nq_5m.index.equals(
                    processed.mnq_5m.index
                )
            )
            self.assertEqual(
                processed.audit[
                    "included_sessions"
                ],
                1,
            )
            self.assertFalse(
                processed.audit[
                    "confirmation_period_requested"
                ]
            )

    def test_raw_archive_preserves_exact_hash(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "NQ.csv"
            archive = root / "raw"

            write_quantower_csv(
                source,
                make_full_session(
                    date(2019, 8, 9)
                ),
            )

            _, record = read_quantower_csv(
                source,
                symbol="NQ",
            )

            archived = archive_raw_files(
                [record],
                raw_root=archive,
            )

            destination = Path(
                archived[0].archived_path
            )

            self.assertTrue(
                destination.exists()
            )
            self.assertEqual(
                sha256_file(destination),
                record.sha256,
            )

    def test_dataframe_fingerprint_is_deterministic(
        self,
    ) -> None:
        index = make_full_session(
            date(2019, 8, 9)
        )[:5]

        frame = pd.DataFrame(
            {
                "open": 8_000.0,
                "high": 8_000.5,
                "low": 7_999.5,
                "close": 8_000.25,
                "volume": 100,
                "session_date": "2019-08-09",
                "minute_slot": np.arange(5),
            },
            index=index,
        )

        self.assertEqual(
            dataframe_sha256(frame),
            dataframe_sha256(
                frame.copy()
            ),
        )


if __name__ == "__main__":
    unittest.main()
