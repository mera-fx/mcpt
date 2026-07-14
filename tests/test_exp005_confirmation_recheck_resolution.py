from __future__ import annotations

import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import pandas as pd

import exp005_quantower_import as base
from exp005_confirmation_import import (
    confirmation_period_context,
    load_confirmation_recheck_corrections,
)
from exp005_confirmation_recheck_resolution import (
    get_exp005_confirmation_recheck_resolution,
    validate_exp005_confirmation_recheck_resolution,
)


def write_quantower_csv(
    path: Path,
    rows: list[dict[str, object]],
) -> None:
    frame = pd.DataFrame(rows)
    frame.to_csv(
        path,
        sep=";",
        index=False,
    )


def row(
    timestamp: str,
    *,
    open_: float = 100.0,
    high: float = 101.0,
    low: float = 99.0,
    close: float = 100.5,
    volume: float = 10.0,
) -> dict[str, object]:
    left = pd.Timestamp(timestamp)
    right = (
        left
        + pd.Timedelta(
            seconds=59,
            milliseconds=999,
        )
    )

    return {
        "Time left": left.strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        )[:-3],
        "Time right": right.strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        )[:-3],
        "Open": open_,
        "High": high,
        "Low": low,
        "Close": close,
        "Volume": volume,
    }


def custom_record(
    path: Path,
    *,
    symbol: str = "NQ",
    correction_close: float = 100.5,
) -> dict[str, object]:
    digest = hashlib.sha256(
        path.read_bytes()
    ).hexdigest()
    frame = pd.read_csv(
        path,
        sep=";",
    )
    timestamps = pd.to_datetime(
        frame["Time left"],
        utc=True,
    )
    first = timestamps.iloc[0]
    last = timestamps.iloc[-1]
    full = pd.date_range(
        first,
        last,
        freq="1min",
    )
    missing = full.difference(
        pd.DatetimeIndex(timestamps)
    )

    if len(missing):
        missing_start = missing[0]
        missing_end = missing[-1]
    else:
        # Empty range outside the source boundaries.
        missing_start = last + pd.Timedelta(
            minutes=2
        )
        missing_end = last + pd.Timedelta(
            minutes=1
        )

    target = pd.Timestamp(
        "2024-11-06T14:40:00+00:00"
    )

    item = {
        "sha256": digest,
        "raw_rows": len(frame),
        "unique_timestamps": int(
            timestamps.nunique()
        ),
        "duplicate_timestamps": int(
            timestamps.duplicated(
                keep=False
            ).sum()
        ),
        "first_timestamp_utc": (
            first.isoformat()
        ),
        "last_timestamp_utc": (
            last.isoformat()
        ),
        "expected_missing_start_utc": (
            missing_start.isoformat()
        ),
        "expected_missing_end_utc": (
            missing_end.isoformat()
        ),
        "expected_missing_minutes": int(
            len(missing)
        ),
        "timestamp_utc": target.isoformat(),
        "bar": {
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": correction_close,
            "volume": 10.0,
        },
    }

    other_symbol = (
        "MNQ"
        if symbol == "NQ"
        else "NQ"
    )

    return {
        "recheck_files": {
            symbol: {
                "2024-11-06": item,
            },
            other_symbol: {
                "2024-11-06": item,
            },
        }
    }


class Exp005ConfirmationRecheckResolutionTests(
    unittest.TestCase
):
    def test_record_is_valid(
        self,
    ) -> None:
        validate_exp005_confirmation_recheck_resolution()

    def test_locked_hashes_and_bars(
        self,
    ) -> None:
        record = (
            get_exp005_confirmation_recheck_resolution()
        )

        self.assertEqual(
            record["recheck_files"]["NQ"][
                "2024-11-06"
            ]["sha256"],
            (
                "82356fcec569434e317ea1ad60bf294a"
                "76493fb65eae8a842438df98bcc93986"
            ),
        )
        self.assertEqual(
            record["recheck_files"]["MNQ"][
                "2024-11-06"
            ]["sha256"],
            (
                "ed8704b7932a1077bd521cea5abc40e9"
                "d735e9d032bb2014127ebbd4e4a2f0db"
            ),
        )
        self.assertEqual(
            record["recheck_files"]["NQ"][
                "2024-11-06"
            ]["bar"]["close"],
            20783.75,
        )
        self.assertEqual(
            record["recheck_files"]["MNQ"][
                "2024-11-06"
            ]["bar"]["close"],
            20783.75,
        )

    def test_duplicate_audit_counts_are_frozen(
        self,
    ) -> None:
        audit = (
            get_exp005_confirmation_recheck_resolution()
            ["duplicate_audit"]
        )

        self.assertEqual(
            audit["total_duplicate_timestamps"],
            200,
        )
        self.assertEqual(
            audit["inside_volume_only_conflicts"],
            52,
        )
        self.assertEqual(
            audit["inside_ohlc_conflicts"],
            2,
        )

    def test_loader_accepts_locked_file(
        self,
    ) -> None:
        with TemporaryDirectory() as temporary:
            path = (
                Path(temporary)
                / "NQ_recheck.csv"
            )
            write_quantower_csv(
                path,
                [
                    row(
                        "2024-11-06 14:40:00",
                    ),
                    row(
                        "2024-11-06 14:41:00",
                    ),
                ],
            )
            record = custom_record(path)

            with (
                patch(
                    "exp005_confirmation_import."
                    "validate_exp005_confirmation_"
                    "recheck_resolution",
                ),
                patch(
                    "exp005_confirmation_import."
                    "get_exp005_confirmation_"
                    "recheck_resolution",
                    return_value=record,
                ),
            ):
                corrections, records = (
                    load_confirmation_recheck_corrections(
                        [path],
                        symbol="NQ",
                    )
                )

            self.assertEqual(
                len(corrections),
                1,
            )
            self.assertEqual(
                float(
                    corrections.iloc[0][
                        "close"
                    ]
                ),
                100.5,
            )
            self.assertEqual(
                records[0].source_role,
                (
                    "CONFIRMATION_"
                    "RECHECK_CORRECTION"
                ),
            )

    def test_loader_rejects_changed_hash(
        self,
    ) -> None:
        with TemporaryDirectory() as temporary:
            path = (
                Path(temporary)
                / "NQ_recheck.csv"
            )
            write_quantower_csv(
                path,
                [
                    row(
                        "2024-11-06 14:40:00",
                    ),
                    row(
                        "2024-11-06 14:41:00",
                    ),
                ],
            )
            record = custom_record(path)
            record["recheck_files"]["NQ"][
                "2024-11-06"
            ]["sha256"] = "0" * 64

            with (
                patch(
                    "exp005_confirmation_import."
                    "validate_exp005_confirmation_"
                    "recheck_resolution",
                ),
                patch(
                    "exp005_confirmation_import."
                    "get_exp005_confirmation_"
                    "recheck_resolution",
                    return_value=record,
                ),
                self.assertRaisesRegex(
                    base.QuantowerImportError,
                    "Unexpected NQ confirmation "
                    "recheck file hash",
                ),
            ):
                load_confirmation_recheck_corrections(
                    [path],
                    symbol="NQ",
                )

    def test_locked_correction_matches_original_candidate(
        self,
    ) -> None:
        with TemporaryDirectory() as temporary:
            directory = Path(temporary)
            recheck = directory / "recheck.csv"
            full = directory / "full.csv"

            write_quantower_csv(
                recheck,
                [
                    row(
                        "2024-11-06 14:40:00",
                        close=100.5,
                    ),
                    row(
                        "2024-11-06 14:41:00",
                    ),
                ],
            )
            write_quantower_csv(
                full,
                [
                    row(
                        "2024-11-06 14:40:00",
                        close=100.25,
                        volume=30.0,
                    ),
                    row(
                        "2024-11-06 14:40:00",
                        close=100.5,
                        volume=10.0,
                    ),
                    row(
                        "2024-11-06 14:41:00",
                    ),
                ],
            )
            record = custom_record(
                recheck,
                correction_close=100.5,
            )

            with (
                patch(
                    "exp005_confirmation_import."
                    "validate_exp005_confirmation_"
                    "recheck_resolution",
                ),
                patch(
                    "exp005_confirmation_import."
                    "get_exp005_confirmation_"
                    "recheck_resolution",
                    return_value=record,
                ),
                confirmation_period_context(),
            ):
                corrections, _ = (
                    load_confirmation_recheck_corrections(
                        [recheck],
                        symbol="NQ",
                    )
                )
                cleaned, file_record = (
                    base.read_quantower_csv(
                        full,
                        symbol="NQ",
                        corrections=corrections,
                    )
                )

            target = pd.Timestamp(
                "2024-11-06T14:40:00+00:00"
            )
            self.assertEqual(
                float(
                    cleaned.loc[
                        target,
                        "close",
                    ]
                ),
                100.5,
            )
            self.assertEqual(
                file_record
                .research_ohlc_conflicts_resolved_by_recheck,
                1,
            )

    def test_correction_not_matching_candidate_stops(
        self,
    ) -> None:
        with TemporaryDirectory() as temporary:
            directory = Path(temporary)
            recheck = directory / "recheck.csv"
            full = directory / "full.csv"

            write_quantower_csv(
                recheck,
                [
                    row(
                        "2024-11-06 14:40:00",
                        close=100.75,
                    ),
                    row(
                        "2024-11-06 14:41:00",
                    ),
                ],
            )
            write_quantower_csv(
                full,
                [
                    row(
                        "2024-11-06 14:40:00",
                        close=100.25,
                        volume=30.0,
                    ),
                    row(
                        "2024-11-06 14:40:00",
                        close=100.5,
                        volume=10.0,
                    ),
                    row(
                        "2024-11-06 14:41:00",
                    ),
                ],
            )
            record = custom_record(
                recheck,
                correction_close=100.75,
            )

            with (
                patch(
                    "exp005_confirmation_import."
                    "validate_exp005_confirmation_"
                    "recheck_resolution",
                ),
                patch(
                    "exp005_confirmation_import."
                    "get_exp005_confirmation_"
                    "recheck_resolution",
                    return_value=record,
                ),
                confirmation_period_context(),
            ):
                corrections, _ = (
                    load_confirmation_recheck_corrections(
                        [recheck],
                        symbol="NQ",
                    )
                )

                with self.assertRaisesRegex(
                    base.QuantowerImportError,
                    "does not match either original",
                ):
                    base.read_quantower_csv(
                        full,
                        symbol="NQ",
                        corrections=corrections,
                    )


if __name__ == "__main__":
    unittest.main()
