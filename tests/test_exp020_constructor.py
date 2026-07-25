from __future__ import annotations

from datetime import date
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd

from exp020_constructor import (
    AUTHORIZATION_PATH,
    CALENDAR_METHOD,
    EXPECTED_TRANSITION_COUNT,
    PRIMARY_METHOD,
    load_authorization,
)
from exp020_constructor_core import (
    KNOWN_PROVIDER_WARNING_CONTRACTS,
    adjustment_map_from_ledger,
    apply_backward_adjustment,
    assign_trading_dates,
    calendar_target_date,
    conservative_warning_exclusions,
    latest_shared_reference,
    normalise_contract_frame,
    select_calendar_roll_date,
    select_volume_roll,
    session_open_utc,
    stitch_series,
    validate_series,
)


def frame_for_dates(
    symbol: str,
    dates: list[date],
    *,
    volumes: list[int],
    price: float,
    instrument_id: int,
) -> pd.DataFrame:
    timestamps = [
        session_open_utc(value)
        + pd.Timedelta(minutes=1)
        for value in dates
    ]

    return pd.DataFrame(
        {
            "ts_event": timestamps,
            "open": [price for _ in dates],
            "high": [price + 0.25 for _ in dates],
            "low": [price - 0.25 for _ in dates],
            "close": [price for _ in dates],
            "volume": volumes,
            "instrument_id": [
                instrument_id
                for _ in dates
            ],
            "source_contract": [
                symbol
                for _ in dates
            ],
            "trading_date": dates,
        }
    )


class Exp020ConstructorTests(unittest.TestCase):
    def test_warning_contract_count_is_locked(self):
        self.assertEqual(
            len(KNOWN_PROVIDER_WARNING_CONTRACTS),
            16,
        )

    def test_trading_date_boundary_standard_time(self):
        timestamps = pd.DatetimeIndex(
            [
                "2024-01-02 22:59:00+00:00",
                "2024-01-02 23:00:00+00:00",
            ]
        )
        self.assertEqual(
            list(assign_trading_dates(timestamps)),
            [
                date(2024, 1, 2),
                date(2024, 1, 3),
            ],
        )

    def test_trading_date_boundary_daylight_time(self):
        timestamps = pd.DatetimeIndex(
            [
                "2024-07-02 21:59:00+00:00",
                "2024-07-02 22:00:00+00:00",
            ]
        )
        self.assertEqual(
            list(assign_trading_dates(timestamps)),
            [
                date(2024, 7, 2),
                date(2024, 7, 3),
            ],
        )

    def test_calendar_target_is_locked(self):
        self.assertEqual(
            calendar_target_date(
                date(2024, 3, 15)
            ),
            date(2024, 3, 8),
        )

    def test_calendar_roll_uses_first_common_session(self):
        index = [
            date(2024, 3, 7),
            date(2024, 3, 8),
            date(2024, 3, 11),
        ]
        outgoing = pd.Series(
            [100, 100, 100],
            index=index,
        )
        incoming = pd.Series(
            [50, 60, 70],
            index=index,
        )
        self.assertEqual(
            select_calendar_roll_date(
                outgoing,
                incoming,
                expiration=date(2024, 3, 15),
            ),
            date(2024, 3, 8),
        )

    def test_volume_roll_requires_two_sessions(self):
        index = [
            date(2024, 3, 4),
            date(2024, 3, 5),
            date(2024, 3, 6),
            date(2024, 3, 7),
            date(2024, 3, 8),
        ]
        outgoing = pd.Series(
            [100, 90, 80, 70, 60],
            index=index,
        )
        incoming = pd.Series(
            [50, 100, 120, 130, 140],
            index=index,
        )
        result = select_volume_roll(
            outgoing,
            incoming,
            calendar_roll_date=date(2024, 3, 8),
        )
        self.assertEqual(
            result["trigger_type"],
            "VOLUME_CROSSOVER",
        )
        self.assertEqual(
            result["trigger_session_1"],
            date(2024, 3, 5),
        )
        self.assertEqual(
            result["trigger_session_2"],
            date(2024, 3, 6),
        )
        self.assertEqual(
            result["roll_trading_date"],
            date(2024, 3, 7),
        )
        self.assertFalse(
            result["calendar_fallback"]
        )

    def test_excluded_session_does_not_trigger(self):
        index = [
            date(2024, 3, 4),
            date(2024, 3, 5),
            date(2024, 3, 6),
            date(2024, 3, 7),
            date(2024, 3, 8),
        ]
        outgoing = pd.Series(
            [100, 90, 80, 70, 60],
            index=index,
        )
        incoming = pd.Series(
            [50, 100, 120, 130, 140],
            index=index,
        )
        result = select_volume_roll(
            outgoing,
            incoming,
            calendar_roll_date=date(2024, 3, 8),
            excluded_dates={date(2024, 3, 5)},
        )
        self.assertEqual(
            result["trigger_session_1"],
            date(2024, 3, 6),
        )
        self.assertEqual(
            result["trigger_session_2"],
            date(2024, 3, 7),
        )
        self.assertEqual(
            result["roll_trading_date"],
            date(2024, 3, 8),
        )

    def test_no_crossover_uses_calendar_fallback(self):
        index = [
            date(2024, 3, 5),
            date(2024, 3, 6),
            date(2024, 3, 7),
            date(2024, 3, 8),
        ]
        outgoing = pd.Series(
            [100, 100, 100, 100],
            index=index,
        )
        incoming = pd.Series(
            [50, 50, 50, 50],
            index=index,
        )
        result = select_volume_roll(
            outgoing,
            incoming,
            calendar_roll_date=date(2024, 3, 8),
        )
        self.assertEqual(
            result["trigger_type"],
            "CALENDAR_FALLBACK",
        )
        self.assertTrue(
            result["calendar_fallback"]
        )

    def test_warning_window_excludes_all_common_dates(self):
        common = [
            date(2024, 3, 5),
            date(2024, 3, 6),
        ]
        excluded, contracts = (
            conservative_warning_exclusions(
                "NQH14",
                "NQM14",
                common,
            )
        )
        self.assertEqual(excluded, set(common))
        self.assertEqual(contracts, ("NQM14",))

    def test_latest_reference_is_before_boundary(self):
        trading_dates = [
            date(2024, 3, 7),
            date(2024, 3, 8),
        ]
        outgoing = frame_for_dates(
            "A",
            trading_dates,
            volumes=[100, 100],
            price=100.0,
            instrument_id=1,
        )
        incoming = frame_for_dates(
            "B",
            trading_dates,
            volumes=[100, 100],
            price=102.0,
            instrument_id=2,
        )
        result = latest_shared_reference(
            outgoing,
            incoming,
            roll_trading_date=date(2024, 3, 8),
        )
        self.assertEqual(
            result["reference_timestamp_utc"],
            outgoing.loc[0, "ts_event"].isoformat(),
        )
        self.assertEqual(
            result["roll_difference_points"],
            2.0,
        )

    def test_cumulative_backward_adjustment(self):
        ledger = [
            {
                "transition_sequence": 1,
                "outgoing_contract": "A",
                "incoming_contract": "B",
                "roll_difference_points": 2.0,
            },
            {
                "transition_sequence": 2,
                "outgoing_contract": "B",
                "incoming_contract": "C",
                "roll_difference_points": -1.0,
            },
        ]
        self.assertEqual(
            adjustment_map_from_ledger(ledger),
            {
                "A": 1.0,
                "B": -1.0,
                "C": 0.0,
            },
        )

    def test_stitch_and_adjustment_are_exact(self):
        dates = [
            date(2024, 3, 6),
            date(2024, 3, 7),
            date(2024, 3, 8),
        ]
        frames = {
            "A": frame_for_dates(
                "A",
                dates,
                volumes=[100, 100, 100],
                price=100.0,
                instrument_id=1,
            ),
            "B": frame_for_dates(
                "B",
                dates,
                volumes=[100, 100, 100],
                price=102.0,
                instrument_id=2,
            ),
        }
        plan = (
            (
                "A",
                "A",
                "2024-03-01",
                "2024-03-16",
                "2024-03-15",
            ),
            (
                "B",
                "B",
                "2024-03-01",
                "2024-06-22",
                "2024-06-21",
            ),
        )
        ledger = [
            {
                "transition_sequence": 1,
                "outgoing_contract": "A",
                "incoming_contract": "B",
                "roll_trading_date": "2024-03-08",
                "roll_difference_points": 2.0,
            }
        ]
        unadjusted = stitch_series(
            frames,
            plan,
            ledger,
            method=PRIMARY_METHOD,
        )
        self.assertEqual(
            list(unadjusted["source_contract"]),
            ["A", "A", "B"],
        )
        self.assertFalse(
            unadjusted["ts_event"].duplicated().any()
        )
        adjusted = apply_backward_adjustment(
            unadjusted,
            ledger,
        )
        self.assertEqual(
            list(adjusted["adjustment_points"]),
            [2.0, 2.0, 0.0],
        )
        self.assertEqual(
            list(adjusted["close"]),
            [102.0, 102.0, 102.0],
        )
        checks = validate_series(
            unadjusted,
            adjusted,
            expected_contracts={"A", "B"},
        )
        self.assertTrue(all(checks.values()))

    def test_normalisation_adds_locked_fields(self):
        raw = pd.DataFrame(
            {
                "instrument_id": [1],
                "open": [100.0],
                "high": [100.25],
                "low": [99.75],
                "close": [100.0],
                "volume": [5],
            },
            index=pd.DatetimeIndex(
                ["2024-03-07 23:01:00+00:00"]
            ),
        )
        result = normalise_contract_frame(
            raw,
            canonical_symbol="NQH24",
        )
        self.assertEqual(
            result.loc[0, "source_contract"],
            "NQH24",
        )
        self.assertEqual(
            result.loc[0, "trading_date"],
            date(2024, 3, 8),
        )

    def test_construction_requires_separate_authorization(self):
        missing = (
            Path(tempfile.gettempdir())
            / "missing_exp020_authorization.py"
        )
        with patch(
            "exp020_constructor.AUTHORIZATION_PATH",
            missing,
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "not authorized",
            ):
                load_authorization()

    def test_method_constants_are_distinct(self):
        self.assertNotEqual(
            PRIMARY_METHOD,
            CALENDAR_METHOD,
        )
        self.assertEqual(
            EXPECTED_TRANSITION_COUNT,
            65,
        )


if __name__ == "__main__":
    unittest.main()
