from __future__ import annotations

from datetime import date
import unittest

import numpy as np
import pandas as pd

from exp005_futures_orb import (
    get_contract_spec,
    run_futures_orb,
)


def make_session(
    session_date: str = "2020-01-02",
) -> pd.DataFrame:
    index = pd.date_range(
        start=pd.Timestamp(
            session_date,
            tz="America/New_York",
        )
        + pd.Timedelta(
            hours=9,
            minutes=30,
        ),
        periods=78,
        freq="5min",
    ).tz_convert("UTC")

    frame = pd.DataFrame(
        {
            "open": np.full(78, 100.0),
            "high": np.full(78, 100.5),
            "low": np.full(78, 99.5),
            "close": np.full(78, 100.0),
            "volume": np.full(78, 10.0),
            "session_date": session_date,
            "slot": np.arange(78),
        },
        index=index,
    )
    frame.index.name = "timestamp"
    return frame


def set_opening_range(
    frame: pd.DataFrame,
) -> None:
    frame.iloc[
        0:3,
        frame.columns.get_loc("high"),
    ] = 101.0
    frame.iloc[
        0:3,
        frame.columns.get_loc("low"),
    ] = 99.0


class Exp005FuturesOrbTests(
    unittest.TestCase
):
    def test_contract_costs_match_preregistration(
        self,
    ) -> None:
        nq = get_contract_spec("NQ")
        mnq = get_contract_spec("MNQ")

        self.assertEqual(
            nq.round_trip_cost_usd,
            15.0,
        )
        self.assertEqual(
            mnq.round_trip_cost_usd,
            3.0,
        )

    def test_long_signal_enters_next_open_and_can_stop_same_bar(
        self,
    ) -> None:
        frame = make_session()
        set_opening_range(frame)

        frame.iloc[
            3,
            frame.columns.get_loc("close"),
        ] = 101.25
        frame.iloc[
            3,
            frame.columns.get_loc("high"),
        ] = 101.50

        frame.iloc[
            4,
            frame.columns.get_loc("open"),
        ] = 101.50
        frame.iloc[
            4,
            frame.columns.get_loc("high"),
        ] = 101.75
        frame.iloc[
            4,
            frame.columns.get_loc("low"),
        ] = 98.75
        frame.iloc[
            4,
            frame.columns.get_loc("close"),
        ] = 100.0

        result = run_futures_orb(
            frame,
            symbol="NQ",
        )
        trade = result.trades.iloc[0]

        self.assertEqual(
            trade["direction"],
            "long",
        )
        self.assertTrue(
            str(trade["entry_time"])
            .startswith(
                "2020-01-02T09:50:00"
            )
        )
        self.assertEqual(
            trade["exit_reason"],
            "range_stop",
        )
        self.assertEqual(
            float(trade["exit_price"]),
            99.0,
        )
        self.assertAlmostEqual(
            float(
                trade["net_pnl_usd"]
            ),
            -65.0,
        )

    def test_forced_flat_uses_1555_open(
        self,
    ) -> None:
        frame = make_session()
        set_opening_range(frame)

        frame.iloc[
            3,
            frame.columns.get_loc("close"),
        ] = 101.25
        frame.iloc[
            3,
            frame.columns.get_loc("high"),
        ] = 101.50
        frame.iloc[
            4,
            frame.columns.get_loc("open"),
        ] = 101.50
        frame.iloc[
            4,
            frame.columns.get_loc("high"),
        ] = 101.75
        frame.iloc[
            4:77,
            frame.columns.get_loc("low"),
        ] = 100.0
        frame.iloc[
            77,
            frame.columns.get_loc("open"),
        ] = 103.0
        frame.iloc[
            77,
            frame.columns.get_loc("high"),
        ] = 103.25
        frame.iloc[
            77,
            frame.columns.get_loc("low"),
        ] = 102.75
        frame.iloc[
            77,
            frame.columns.get_loc("close"),
        ] = 103.0

        result = run_futures_orb(
            frame,
            symbol="NQ",
        )
        trade = result.trades.iloc[0]

        self.assertEqual(
            trade["exit_reason"],
            "forced_flat_1555",
        )
        self.assertEqual(
            float(trade["exit_price"]),
            103.0,
        )
        self.assertAlmostEqual(
            float(
                trade["net_pnl_usd"]
            ),
            15.0,
        )


    def test_protected_mcpt_path_uses_locked_forced_flat_slot(
        self,
    ) -> None:
        frame = make_session()
        set_opening_range(frame)

        frame.iloc[
            3,
            frame.columns.get_loc("close"),
        ] = 101.25
        frame.iloc[
            3,
            frame.columns.get_loc("high"),
        ] = 101.50
        frame.iloc[
            4,
            frame.columns.get_loc("open"),
        ] = 101.50
        frame.iloc[
            4:77,
            frame.columns.get_loc("low"),
        ] = 100.0
        frame.iloc[
            77,
            frame.columns.get_loc("open"),
        ] = 103.0
        frame.iloc[
            77,
            frame.columns.get_loc("high"),
        ] = 103.25
        frame.iloc[
            77,
            frame.columns.get_loc("low"),
        ] = 102.75
        frame.iloc[
            77,
            frame.columns.get_loc("close"),
        ] = 103.0

        # Simulate a platform/version representation difference
        # in the timestamp clock while preserving the protected
        # and previously validated slot sequence.
        shifted = frame.copy()
        shifted.index = (
            shifted.index
            + pd.Timedelta(hours=1)
        )

        result = run_futures_orb(
            shifted,
            symbol="NQ",
            validate_data=False,
        )
        trade = result.trades.iloc[0]

        self.assertEqual(
            trade["exit_reason"],
            "forced_flat_1555",
        )
        self.assertEqual(
            float(trade["exit_price"]),
            103.0,
        )
    def test_short_stop_uses_range_high(
        self,
    ) -> None:
        frame = make_session()
        set_opening_range(frame)

        frame.iloc[
            3,
            frame.columns.get_loc("close"),
        ] = 98.75
        frame.iloc[
            3,
            frame.columns.get_loc("low"),
        ] = 98.50
        frame.iloc[
            4,
            frame.columns.get_loc("open"),
        ] = 100.0
        frame.iloc[
            4,
            frame.columns.get_loc("high"),
        ] = 102.0
        frame.iloc[
            4,
            frame.columns.get_loc("low"),
        ] = 98.5

        result = run_futures_orb(
            frame,
            symbol="NQ",
        )
        trade = result.trades.iloc[0]

        self.assertEqual(
            trade["direction"],
            "short",
        )
        self.assertEqual(
            float(trade["exit_price"]),
            101.0,
        )
        self.assertEqual(
            trade["exit_reason"],
            "range_stop",
        )
        self.assertAlmostEqual(
            float(
                trade["net_pnl_usd"]
            ),
            -35.0,
        )

    def test_only_one_trade_per_session(
        self,
    ) -> None:
        frame = make_session()
        set_opening_range(frame)

        frame.iloc[
            3,
            frame.columns.get_loc("close"),
        ] = 101.25
        frame.iloc[
            3,
            frame.columns.get_loc("high"),
        ] = 101.50
        frame.iloc[
            4,
            frame.columns.get_loc("open"),
        ] = 101.50
        frame.iloc[
            4,
            frame.columns.get_loc("high"),
        ] = 101.75
        frame.iloc[
            4,
            frame.columns.get_loc("low"),
        ] = 98.75

        # A later short breakout cannot create a reversal.
        frame.iloc[
            20,
            frame.columns.get_loc("close"),
        ] = 98.0
        frame.iloc[
            20,
            frame.columns.get_loc("low"),
        ] = 97.75

        result = run_futures_orb(
            frame,
            symbol="NQ",
        )

        self.assertEqual(
            len(result.trades),
            1,
        )


if __name__ == "__main__":
    unittest.main()
