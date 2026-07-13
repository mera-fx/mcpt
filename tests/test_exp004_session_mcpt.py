from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import numpy as np
import pandas as pd

from exp004_session_mcpt import (
    permute_exp004_sessions,
    run_exp004_mcpt,
)
from intraday_market_foundation import (
    expected_regular_session_index,
)


def synthetic_sessions(
    count: int = 12,
) -> pd.DataFrame:
    frames = []

    for number in range(count):
        session_date = (
            pd.Timestamp("2022-03-01")
            + pd.offsets.BDay(number)
        ).strftime("%Y-%m-%d")

        index = (
            expected_regular_session_index(
                session_date
            )
            .tz_convert("UTC")
        )

        base = 100.0 + number
        close = np.full(
            78,
            base,
            dtype=float,
        )

        # Every session has a clear first
        # post-range breakout at slot 3.
        close[3] = (
            base + 2.0
            if number % 2 == 0
            else base - 2.0
        )

        close[4:] = (
            close[3]
            + (
                0.8
                if number % 3 == 0
                else -0.6
            )
        )

        open_price = np.r_[
            base,
            close[:-1],
        ]

        high = np.maximum(
            open_price,
            close,
        ) + 0.35

        low = np.minimum(
            open_price,
            close,
        ) - 0.35

        frame = pd.DataFrame(
            {
                "open": open_price,
                "high": high,
                "low": low,
                "close": close,
                "volume": (
                    1000.0
                    + number
                    + np.arange(78)
                ),
                "session_date": (
                    session_date
                ),
                "slot": np.arange(
                    78,
                    dtype=int,
                ),
            },
            index=index,
        )

        frames.append(frame)

    return pd.concat(
        frames,
        axis=0,
    ).sort_index()


def close_move_by_slot(
    data: pd.DataFrame,
    slot: int,
) -> np.ndarray:
    selected = data[
        data["slot"] == slot
    ]

    values = np.log(
        selected["close"].to_numpy(
            dtype=float
        )
        / selected["open"].to_numpy(
            dtype=float
        )
    )

    return np.sort(values)


class Exp004SessionMcptTests(
    unittest.TestCase
):
    def test_same_seed_is_deterministic(
        self,
    ) -> None:
        data = synthetic_sessions()

        first = permute_exp004_sessions(
            data,
            seed=44,
        )

        second = permute_exp004_sessions(
            data,
            seed=44,
        )

        pd.testing.assert_frame_equal(
            first,
            second,
            check_exact=True,
        )

    def test_different_seed_changes_market(
        self,
    ) -> None:
        data = synthetic_sessions()

        first = permute_exp004_sessions(
            data,
            seed=44,
        )

        second = permute_exp004_sessions(
            data,
            seed=45,
        )

        self.assertFalse(
            first[
                [
                    "open",
                    "high",
                    "low",
                    "close",
                ]
            ].equals(
                second[
                    [
                        "open",
                        "high",
                        "low",
                        "close",
                    ]
                ]
            )
        )

    def test_permutation_preserves_structure(
        self,
    ) -> None:
        data = synthetic_sessions()

        permuted = (
            permute_exp004_sessions(
                data,
                seed=100,
            )
        )

        self.assertTrue(
            data.index.equals(
                permuted.index
            )
        )

        counts = permuted.groupby(
            "session_date"
        ).size()

        self.assertTrue(
            counts.eq(78).all()
        )

        self.assertTrue(
            (
                permuted["high"]
                >= permuted[
                    [
                        "open",
                        "close",
                        "low",
                    ]
                ].max(axis=1)
            ).all()
        )

        self.assertTrue(
            (
                permuted["low"]
                <= permuted[
                    [
                        "open",
                        "close",
                        "high",
                    ]
                ].min(axis=1)
            ).all()
        )

    def test_time_slot_distribution_is_preserved(
        self,
    ) -> None:
        data = synthetic_sessions()

        permuted = (
            permute_exp004_sessions(
                data,
                seed=200,
            )
        )

        for slot in (
            0,
            3,
            20,
            77,
        ):
            np.testing.assert_allclose(
                close_move_by_slot(
                    data,
                    slot,
                ),
                close_move_by_slot(
                    permuted,
                    slot,
                ),
                rtol=1e-12,
                atol=1e-12,
            )

    def test_serial_parallel_results_match(
        self,
    ) -> None:
        data = synthetic_sessions(
            count=16
        )

        common = {
            "data": data,
            "grid": {
                "opening_range_minutes": [
                    15,
                ],
                "direction_mode": [
                    "both",
                ],
            },
            "starting_capital": (
                100_000.0
            ),
            "total_cost_bps_per_side": (
                1.5
            ),
            "minimum_valid_trades": 1,
            "random_seed": 44,
            "permutations": 2,
            "real_best_profit_factor": (
                1.0
            ),
            "checkpoint_signature": {
                "test": "parity",
            },
            "checkpoint_every": 1,
            "resume": False,
        }

        with TemporaryDirectory() as temporary:
            root = Path(temporary)

            serial, _, _, _ = (
                run_exp004_mcpt(
                    **common,
                    requested_workers=1,
                    checkpoint_directory=(
                        root / "serial"
                    ),
                )
            )

            parallel, _, _, _ = (
                run_exp004_mcpt(
                    **common,
                    requested_workers=2,
                    checkpoint_directory=(
                        root / "parallel"
                    ),
                )
            )

        pd.testing.assert_frame_equal(
            serial,
            parallel,
            check_exact=True,
        )


if __name__ == "__main__":
    unittest.main()
