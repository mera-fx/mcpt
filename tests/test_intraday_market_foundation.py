from __future__ import annotations

import unittest

import pandas as pd

from intraday_market_foundation import (
    expected_regular_session_index,
    get_intraday_market,
    list_intraday_markets,
    validate_complete_regular_session,
    validate_intraday_market_registry,
)


def valid_session(
    session_date: str,
) -> pd.DataFrame:
    index = expected_regular_session_index(
        session_date
    )

    close = pd.Series(
        range(100, 100 + len(index)),
        index=index,
        dtype=float,
    )

    return pd.DataFrame(
        {
            "open": close,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close + 0.25,
            "volume": 1000.0,
        },
        index=index,
    )


class IntradayMarketFoundationTests(
    unittest.TestCase
):
    def test_registry_is_valid(
        self,
    ) -> None:
        validate_intraday_market_registry()

        self.assertEqual(
            len(list_intraday_markets()),
            6,
        )

    def test_qqq_primary_session(
        self,
    ) -> None:
        qqq = get_intraday_market(
            "qqq"
        )

        self.assertEqual(
            qqq.orb_session_start,
            "09:30",
        )
        self.assertEqual(
            qqq.orb_session_end,
            "16:00",
        )
        self.assertEqual(
            qqq.default_bar_minutes,
            5,
        )

    def test_nq_and_mnq_tick_values(
        self,
    ) -> None:
        nq = get_intraday_market("NQ")
        mnq = get_intraday_market("MNQ")

        self.assertEqual(
            nq.tick_value,
            5.0,
        )
        self.assertEqual(
            mnq.tick_value,
            0.5,
        )

    def test_full_session_has_78_bars(
        self,
    ) -> None:
        winter = expected_regular_session_index(
            "2026-01-15"
        )

        summer = expected_regular_session_index(
            "2026-07-15"
        )

        self.assertEqual(
            len(winter),
            78,
        )
        self.assertEqual(
            len(summer),
            78,
        )
        self.assertEqual(
            winter[0].strftime("%H:%M"),
            "09:30",
        )
        self.assertEqual(
            summer[-1].strftime("%H:%M"),
            "15:55",
        )

    def test_complete_session_passes(
        self,
    ) -> None:
        data = valid_session(
            "2026-07-15"
        )

        validate_complete_regular_session(
            data,
            session_date="2026-07-15",
            market_id="QQQ",
        )

    def test_missing_bar_is_rejected(
        self,
    ) -> None:
        data = valid_session(
            "2026-07-15"
        ).drop(
            index=expected_regular_session_index(
                "2026-07-15"
            )[10]
        )

        with self.assertRaises(
            ValueError
        ):
            validate_complete_regular_session(
                data,
                session_date="2026-07-15",
                market_id="QQQ",
            )


if __name__ == "__main__":
    unittest.main()
