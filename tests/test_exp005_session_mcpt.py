from __future__ import annotations

from concurrent.futures import (
    ProcessPoolExecutor,
)
import multiprocessing
import unittest

import numpy as np
import pandas as pd

from exp005_session_mcpt import (
    _permuted_component_arrays,
    _worker_initialize,
    _worker_run,
    build_permutation_components,
    reconstruct_permuted_five_minute_data,
    run_one_permutation,
)


def make_one_minute_data(
    sessions: int = 6,
) -> pd.DataFrame:
    pieces = []
    dates = pd.bdate_range(
        "2020-01-02",
        periods=sessions,
    )
    previous_close = 9_000.0

    for session_number, day in enumerate(
        dates
    ):
        local_index = pd.date_range(
            start=(
                pd.Timestamp(
                    day.date(),
                    tz="America/New_York",
                )
                + pd.Timedelta(
                    hours=9,
                    minutes=30,
                )
            ),
            periods=390,
            freq="1min",
        )
        index = local_index.tz_convert(
            "UTC"
        )
        slot = np.arange(390)
        opening_gap = (
            (session_number - 2.5)
            * 0.0002
        )
        open_values = np.empty(390)
        close_values = np.empty(390)
        high_values = np.empty(390)
        low_values = np.empty(390)

        for position in range(390):
            if position == 0:
                open_price = (
                    previous_close
                    * np.exp(opening_gap)
                )
            else:
                open_price = (
                    close_values[position - 1]
                    * np.exp(
                        (
                            (position % 7) - 3
                        )
                        * 0.00001
                    )
                )

            move = (
                np.sin(
                    (
                        position
                        + session_number
                    )
                    / 21.0
                )
                * 0.00008
            )
            close_price = (
                open_price
                * np.exp(move)
            )
            excursion = (
                0.00005
                + (
                    position % 5
                )
                * 0.000005
            )

            open_values[position] = (
                open_price
            )
            close_values[position] = (
                close_price
            )
            high_values[position] = (
                max(
                    open_price,
                    close_price,
                )
                * np.exp(excursion)
            )
            low_values[position] = (
                min(
                    open_price,
                    close_price,
                )
                * np.exp(-excursion)
            )

        previous_close = float(
            close_values[-1]
        )

        pieces.append(
            pd.DataFrame(
                {
                    "open": open_values,
                    "high": high_values,
                    "low": low_values,
                    "close": close_values,
                    "volume": (
                        100
                        + session_number
                        + slot
                    ).astype(float),
                    "session_date": (
                        str(day.date())
                    ),
                    "minute_slot": slot,
                },
                index=index,
            )
        )

    frame = pd.concat(
        pieces
    ).sort_index()
    frame.index.name = "timestamp"
    return frame


class Exp005SessionMcptTests(
    unittest.TestCase
):
    @classmethod
    def setUpClass(
        cls,
    ) -> None:
        cls.data = make_one_minute_data()
        cls.components = (
            build_permutation_components(
                cls.data
            )
        )

    def test_reconstruction_has_locked_structure(
        self,
    ) -> None:
        permuted = (
            reconstruct_permuted_five_minute_data(
                self.components,
                seed=123,
            )
        )

        self.assertEqual(
            len(permuted),
            6 * 78,
        )
        self.assertTrue(
            permuted.groupby(
                "session_date"
            ).size().eq(78).all()
        )
        self.assertTrue(
            permuted.index.equals(
                pd.to_datetime(
                    self.components
                    .five_minute_index_ns
                    .reshape(-1),
                    utc=True,
                )
            )
        )
        self.assertTrue(
            (
                permuted["high"]
                >= permuted[
                    ["open", "close"]
                ].max(axis=1)
            ).all()
        )
        self.assertTrue(
            (
                permuted["low"]
                <= permuted[
                    ["open", "close"]
                ].min(axis=1)
            ).all()
        )

    def test_same_seed_is_exact(
        self,
    ) -> None:
        first = (
            reconstruct_permuted_five_minute_data(
                self.components,
                seed=456,
            )
        )
        second = (
            reconstruct_permuted_five_minute_data(
                self.components,
                seed=456,
            )
        )

        pd.testing.assert_frame_equal(
            first,
            second,
            check_exact=True,
        )

    def test_different_seed_changes_market(
        self,
    ) -> None:
        first = (
            reconstruct_permuted_five_minute_data(
                self.components,
                seed=456,
            )
        )
        second = (
            reconstruct_permuted_five_minute_data(
                self.components,
                seed=457,
            )
        )

        self.assertFalse(
            first[
                ["open", "high", "low", "close"]
            ].equals(
                second[
                    ["open", "high", "low", "close"]
                ]
            )
        )

    def test_time_slot_distributions_are_preserved(
        self,
    ) -> None:
        permuted = (
            _permuted_component_arrays(
                self.components,
                seed=789,
            )
        )
        originals = (
            self.components.open_gap,
            self.components.close_move,
            self.components.high_excursion,
            self.components.low_excursion,
            self.components.volume,
        )

        for original, changed in zip(
            originals,
            permuted,
            strict=True,
        ):
            for slot in (
                0,
                1,
                100,
                389,
            ):
                np.testing.assert_allclose(
                    np.sort(
                        original[:, slot]
                    ),
                    np.sort(
                        changed[:, slot]
                    ),
                    rtol=0.0,
                    atol=0.0,
                )

    def test_serial_and_spawned_worker_are_exact(
        self,
    ) -> None:
        serial = [
            run_one_permutation(
                self.components,
                zero_based_permutation=index,
                base_seed=45,
            )
            for index in range(2)
        ]

        context = (
            multiprocessing.get_context(
                "spawn"
            )
        )

        with ProcessPoolExecutor(
            max_workers=2,
            mp_context=context,
            initializer=_worker_initialize,
            initargs=(
                self.components,
                45,
            ),
        ) as executor:
            parallel = list(
                executor.map(
                    _worker_run,
                    range(2),
                )
            )

        self.assertEqual(
            serial,
            parallel,
        )


if __name__ == "__main__":
    unittest.main()
