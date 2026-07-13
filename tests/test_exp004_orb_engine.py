from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from exp004_orb_engine import (
    optimize_orb,
    run_orb_backtest,
)
from intraday_market_foundation import (
    expected_regular_session_index,
)


def make_session(
    session_date: str,
    *,
    base_price: float = 100.0,
) -> pd.DataFrame:
    index = (
        expected_regular_session_index(
            session_date
        )
    )

    frame = pd.DataFrame(
        {
            "open": base_price,
            "high": base_price + 0.4,
            "low": base_price - 0.4,
            "close": base_price,
            "volume": 1000.0,
            "session_date": (
                session_date
            ),
            "slot": np.arange(
                78,
                dtype=int,
            ),
        },
        index=index.tz_convert("UTC"),
    )

    return frame


def combine_sessions(
    *sessions: pd.DataFrame,
) -> pd.DataFrame:
    return pd.concat(
        sessions,
        axis=0,
    ).sort_index()


class Exp004OrbEngineTests(
    unittest.TestCase
):
    def test_long_signal_executes_next_open(
        self,
    ) -> None:
        session = make_session(
            "2022-01-03"
        )

        # 15-minute range is 99.6 to 100.4.
        session.iloc[3, session.columns.get_loc(
            "close"
        )] = 101.0
        session.iloc[3, session.columns.get_loc(
            "high"
        )] = 101.2

        session.iloc[4, session.columns.get_loc(
            "open"
        )] = 101.5
        session.iloc[4, session.columns.get_loc(
            "high"
        )] = 101.8
        session.iloc[4, session.columns.get_loc(
            "low"
        )] = 101.2
        session.iloc[4, session.columns.get_loc(
            "close"
        )] = 101.6

        session.iloc[5:77, session.columns.get_loc(
            "open"
        )] = 101.6
        session.iloc[5:77, session.columns.get_loc(
            "high"
        )] = 101.9
        session.iloc[5:77, session.columns.get_loc(
            "low"
        )] = 101.3
        session.iloc[5:77, session.columns.get_loc(
            "close"
        )] = 101.7

        session.iloc[77, session.columns.get_loc(
            "open"
        )] = 102.0
        session.iloc[77, session.columns.get_loc(
            "high"
        )] = 102.2
        session.iloc[77, session.columns.get_loc(
            "low"
        )] = 101.8
        session.iloc[77, session.columns.get_loc(
            "close"
        )] = 102.0

        result = run_orb_backtest(
            session,
            opening_range_minutes=15,
            direction_mode="both",
            total_cost_bps_per_side=0.0,
        )

        trade = result.trades.iloc[0]

        self.assertEqual(
            trade["direction"],
            "long",
        )
        self.assertTrue(
            str(
                trade["signal_time"]
            ).endswith(
                "09:45:00-05:00"
            )
        )
        self.assertTrue(
            str(
                trade["entry_time"]
            ).endswith(
                "09:50:00-05:00"
            )
        )
        self.assertEqual(
            trade["entry_price"],
            101.5,
        )
        self.assertEqual(
            trade["exit_reason"],
            "forced_flat_1555",
        )

    def test_same_entry_bar_can_stop(
        self,
    ) -> None:
        session = make_session(
            "2022-01-04"
        )

        session.iloc[3, session.columns.get_loc(
            "close"
        )] = 101.0
        session.iloc[3, session.columns.get_loc(
            "high"
        )] = 101.2

        session.iloc[4, session.columns.get_loc(
            "open"
        )] = 101.2
        session.iloc[4, session.columns.get_loc(
            "high"
        )] = 101.4
        session.iloc[4, session.columns.get_loc(
            "low"
        )] = 99.4
        session.iloc[4, session.columns.get_loc(
            "close"
        )] = 100.0

        result = run_orb_backtest(
            session,
            opening_range_minutes=15,
            direction_mode="long_only",
            total_cost_bps_per_side=0.0,
        )

        trade = result.trades.iloc[0]

        self.assertEqual(
            trade["exit_reason"],
            "range_stop",
        )
        self.assertEqual(
            trade["bars_held"],
            1,
        )
        self.assertEqual(
            trade["exit_price"],
            99.6,
        )

    def test_short_gap_through_stop_uses_open(
        self,
    ) -> None:
        session = make_session(
            "2022-01-05"
        )

        session.iloc[3, session.columns.get_loc(
            "close"
        )] = 99.0
        session.iloc[3, session.columns.get_loc(
            "low"
        )] = 98.8

        session.iloc[4, session.columns.get_loc(
            "open"
        )] = 99.0
        session.iloc[4, session.columns.get_loc(
            "high"
        )] = 99.3
        session.iloc[4, session.columns.get_loc(
            "low"
        )] = 98.7
        session.iloc[4, session.columns.get_loc(
            "close"
        )] = 99.0

        session.iloc[5, session.columns.get_loc(
            "open"
        )] = 101.0
        session.iloc[5, session.columns.get_loc(
            "high"
        )] = 101.2
        session.iloc[5, session.columns.get_loc(
            "low"
        )] = 100.8
        session.iloc[5, session.columns.get_loc(
            "close"
        )] = 101.0

        result = run_orb_backtest(
            session,
            opening_range_minutes=15,
            direction_mode="short_only",
            total_cost_bps_per_side=0.0,
        )

        trade = result.trades.iloc[0]

        self.assertEqual(
            trade["direction"],
            "short",
        )
        self.assertEqual(
            trade["exit_reason"],
            "gap_through_range_stop",
        )
        self.assertEqual(
            trade["exit_price"],
            101.0,
        )

    def test_cost_is_charged_on_both_sides(
        self,
    ) -> None:
        session = make_session(
            "2022-01-06"
        )

        session.iloc[3, session.columns.get_loc(
            "close"
        )] = 101.0
        session.iloc[3, session.columns.get_loc(
            "high"
        )] = 101.2

        session.iloc[4, session.columns.get_loc(
            "open"
        )] = 101.0
        session.iloc[4, session.columns.get_loc(
            "high"
        )] = 101.2
        session.iloc[4, session.columns.get_loc(
            "low"
        )] = 100.8
        session.iloc[4, session.columns.get_loc(
            "close"
        )] = 101.0

        session.iloc[5:77, session.columns.get_loc(
            "open"
        )] = 101.0
        session.iloc[5:77, session.columns.get_loc(
            "high"
        )] = 101.2
        session.iloc[5:77, session.columns.get_loc(
            "low"
        )] = 100.8
        session.iloc[5:77, session.columns.get_loc(
            "close"
        )] = 101.0

        session.iloc[77, session.columns.get_loc(
            "open"
        )] = 101.0
        session.iloc[77, session.columns.get_loc(
            "high"
        )] = 101.2
        session.iloc[77, session.columns.get_loc(
            "low"
        )] = 100.8
        session.iloc[77, session.columns.get_loc(
            "close"
        )] = 101.0

        result = run_orb_backtest(
            session,
            opening_range_minutes=15,
            direction_mode="long_only",
            total_cost_bps_per_side=1.5,
        )

        self.assertAlmostEqual(
            result.trades.iloc[0][
                "net_return_percent"
            ],
            -0.03,
            places=10,
        )

    def test_direction_mode_is_respected(
        self,
    ) -> None:
        session = make_session(
            "2022-01-07"
        )

        session.iloc[3, session.columns.get_loc(
            "close"
        )] = 99.0
        session.iloc[3, session.columns.get_loc(
            "low"
        )] = 98.8

        long_only = run_orb_backtest(
            session,
            opening_range_minutes=15,
            direction_mode="long_only",
        )

        short_only = run_orb_backtest(
            session,
            opening_range_minutes=15,
            direction_mode="short_only",
        )

        self.assertEqual(
            len(long_only.trades),
            0,
        )
        self.assertEqual(
            len(short_only.trades),
            1,
        )

    def test_force_flat_prevents_overnight_position(
        self,
    ) -> None:
        session = make_session(
            "2022-01-10"
        )

        session.iloc[3, session.columns.get_loc(
            "close"
        )] = 101.0
        session.iloc[3, session.columns.get_loc(
            "high"
        )] = 101.2

        session.iloc[4:, session.columns.get_loc(
            "open"
        )] = 101.0
        session.iloc[4:, session.columns.get_loc(
            "high"
        )] = 101.3
        session.iloc[4:, session.columns.get_loc(
            "low"
        )] = 100.7
        session.iloc[4:, session.columns.get_loc(
            "close"
        )] = 101.1

        result = run_orb_backtest(
            session,
            opening_range_minutes=15,
            direction_mode="both",
        )

        self.assertEqual(
            result.trades.iloc[0][
                "exit_reason"
            ],
            "forced_flat_1555",
        )
        self.assertTrue(
            str(
                result.trades.iloc[0][
                    "exit_time"
                ]
            ).endswith(
                "15:55:00-05:00"
            )
        )

    def test_optimization_uses_all_nine_combinations(
        self,
    ) -> None:
        sessions = []

        for number in range(6):
            day = (
                pd.Timestamp("2022-02-01")
                + pd.Timedelta(
                    days=number
                )
            )

            session = make_session(
                day.strftime("%Y-%m-%d"),
                base_price=(
                    100.0 + number
                ),
            )

            if number % 2 == 0:
                session.iloc[
                    7,
                    session.columns.get_loc(
                        "close"
                    ),
                ] += 2.0
                session.iloc[
                    7,
                    session.columns.get_loc(
                        "high"
                    ),
                ] += 2.2
            else:
                session.iloc[
                    7,
                    session.columns.get_loc(
                        "close"
                    ),
                ] -= 2.0
                session.iloc[
                    7,
                    session.columns.get_loc(
                        "low"
                    ),
                ] -= 2.2

            sessions.append(session)

        data = combine_sessions(
            *sessions
        )

        optimization, best, _ = (
            optimize_orb(
                data,
                grid={
                    "opening_range_minutes": [
                        5,
                        15,
                        30,
                    ],
                    "direction_mode": [
                        "long_only",
                        "short_only",
                        "both",
                    ],
                },
                minimum_valid_trades=1,
            )
        )

        self.assertEqual(
            len(optimization),
            9,
        )
        self.assertIn(
            best[
                "opening_range_minutes"
            ],
            {5, 15, 30},
        )
        self.assertIn(
            best["direction_mode"],
            {
                "long_only",
                "short_only",
                "both",
            },
        )


if __name__ == "__main__":
    unittest.main()
