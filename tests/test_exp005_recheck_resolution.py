from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import pandas as pd

from exp005_quantower_import import (
    QuantowerImportError,
    _deduplicate_identical_timestamp_rows,
)
from exp005_recheck_resolution import (
    get_exp005_recheck_resolution,
    validate_exp005_recheck_resolution,
)


TS = pd.Timestamp(
    "2020-06-11T17:40:00+00:00"
)


def frame(
    rows: list[dict[str, float]],
) -> pd.DataFrame:
    result = pd.DataFrame(
        rows,
        index=pd.DatetimeIndex(
            [TS] * len(rows),
            name="timestamp",
        ),
    )

    return result


class Exp005RecheckResolutionTests(
    unittest.TestCase
):
    def test_record_is_valid(
        self,
    ) -> None:
        validate_exp005_recheck_resolution()

    def test_locked_hashes_and_bars_exist(
        self,
    ) -> None:
        record = get_exp005_recheck_resolution()

        for symbol in ("NQ", "MNQ"):
            self.assertEqual(
                len(record["recheck_files"][symbol]),
                2,
            )

            for item in record[
                "recheck_files"
            ][symbol].values():
                self.assertEqual(
                    len(item["sha256"]),
                    64,
                )
                self.assertEqual(
                    set(item["bar"]),
                    {
                        "open",
                        "high",
                        "low",
                        "close",
                        "volume",
                    },
                )

    def test_volume_only_conflict_keeps_maximum_volume(
        self,
    ) -> None:
        source = frame(
            [
                {
                    "open": 100.0,
                    "high": 101.0,
                    "low": 99.0,
                    "close": 100.5,
                    "volume": 10.0,
                },
                {
                    "open": 100.0,
                    "high": 101.0,
                    "low": 99.0,
                    "close": 100.5,
                    "volume": 30.0,
                },
            ]
        )

        (
            result,
            removed,
            _,
            volume_resolved,
            ohlc_resolved,
        ) = _deduplicate_identical_timestamp_rows(
            source,
            path=Path("NQ.csv"),
            symbol="NQ",
        )

        self.assertEqual(
            len(result),
            1,
        )
        self.assertEqual(
            float(result.iloc[0]["volume"]),
            30.0,
        )
        self.assertEqual(removed, 1)
        self.assertEqual(volume_resolved, 1)
        self.assertEqual(ohlc_resolved, 0)

    def test_ohlc_conflict_uses_matching_recheck(
        self,
    ) -> None:
        lower = {
            "open": 9737.75,
            "high": 9741.50,
            "low": 9732.00,
            "close": 9739.75,
            "volume": 953.0,
        }
        upper = {
            **lower,
            "close": 9739.25,
            "volume": 2858.0,
        }

        source = frame(
            [lower, upper]
        )
        correction = frame(
            [lower]
        )

        (
            result,
            removed,
            _,
            volume_resolved,
            ohlc_resolved,
        ) = _deduplicate_identical_timestamp_rows(
            source,
            path=Path("NQ.csv"),
            symbol="NQ",
            corrections=correction,
        )

        self.assertEqual(
            float(result.iloc[0]["close"]),
            9739.75,
        )
        self.assertEqual(removed, 1)
        self.assertEqual(volume_resolved, 0)
        self.assertEqual(ohlc_resolved, 1)

    def test_unresolved_ohlc_conflict_stops(
        self,
    ) -> None:
        source = frame(
            [
                {
                    "open": 100.0,
                    "high": 101.0,
                    "low": 99.0,
                    "close": 100.0,
                    "volume": 10.0,
                },
                {
                    "open": 100.0,
                    "high": 102.0,
                    "low": 99.0,
                    "close": 101.0,
                    "volume": 20.0,
                },
            ]
        )

        with self.assertRaisesRegex(
            QuantowerImportError,
            "unresolved research-session OHLC conflict",
        ):
            _deduplicate_identical_timestamp_rows(
                source,
                path=Path("NQ.csv"),
                symbol="NQ",
            )

    def test_recheck_must_match_original_candidate(
        self,
    ) -> None:
        source = frame(
            [
                {
                    "open": 100.0,
                    "high": 101.0,
                    "low": 99.0,
                    "close": 100.0,
                    "volume": 10.0,
                },
                {
                    "open": 100.0,
                    "high": 102.0,
                    "low": 99.0,
                    "close": 101.0,
                    "volume": 20.0,
                },
            ]
        )

        correction = frame(
            [
                {
                    "open": 100.0,
                    "high": 103.0,
                    "low": 99.0,
                    "close": 102.0,
                    "volume": 30.0,
                }
            ]
        )

        with self.assertRaisesRegex(
            QuantowerImportError,
            "does not match either original",
        ):
            _deduplicate_identical_timestamp_rows(
                source,
                path=Path("NQ.csv"),
                symbol="NQ",
                corrections=correction,
            )


if __name__ == "__main__":
    unittest.main()
