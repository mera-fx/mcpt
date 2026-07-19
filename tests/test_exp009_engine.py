from __future__ import annotations

import unittest

import numpy as np

from exp009_engine import (
    Exp009Signals,
    execute_exp009_signals,
    generate_exp009_signals,
    get_exp009_candidate,
    locked_exp009_candidates,
    prepare_exp009_arrays,
)
from tests.exp009_test_data import (
    make_exp009_arrays,
    make_exp009_one_minute_data,
    set_opening_range,
)


class Exp009EngineTests(unittest.TestCase):
    def test_locked_budget_has_six_families_and_24_candidates(self) -> None:
        candidates = locked_exp009_candidates()
        self.assertEqual(len(candidates), 24)
        self.assertEqual(len({item.candidate_id for item in candidates}), 24)
        self.assertEqual(len({item.family_id for item in candidates}), 6)

    def test_prepare_arrays_builds_78_completed_five_minute_bars(self) -> None:
        data = make_exp009_one_minute_data(["2024-01-02", "2024-01-03"])
        arrays = prepare_exp009_arrays(data, validate_data=False)
        self.assertEqual(arrays.open.shape, (2, 390))
        self.assertEqual(arrays.open_5m.shape, (2, 78))
        self.assertEqual(arrays.vwap_5m.shape, (2, 78))

    def test_orb_pullback_signal_uses_retest_and_midpoint_stop(self) -> None:
        arrays = make_exp009_arrays()
        set_opening_range(arrays)
        arrays.close_5m[0, 6] = 102.0
        arrays.high_5m[0, 6] = 102.2
        arrays.low_5m[0, 7] = 100.8
        arrays.close_5m[0, 7] = 101.2
        arrays.open_5m[0, 8] = 101.5
        signals = generate_exp009_signals(
            arrays, get_exp009_candidate("orb_pullback_long_1r")
        )
        self.assertEqual(signals.direction[0], 1)
        self.assertEqual(signals.entry_minute_slot[0], 40)
        self.assertAlmostEqual(signals.stop_price[0], 100.0)
        self.assertAlmostEqual(signals.target_price[0], 103.0)

    def test_failed_orb_enters_reversal(self) -> None:
        arrays = make_exp009_arrays()
        set_opening_range(arrays)
        arrays.close_5m[0, 6] = 102.0
        arrays.high_5m[0, 6] = 102.5
        arrays.close_5m[0, 7] = 100.5
        arrays.high_5m[0, 7] = 101.8
        arrays.open_5m[0, 8] = 100.4
        signals = generate_exp009_signals(
            arrays, get_exp009_candidate("failed_orb_30m_1r")
        )
        self.assertEqual(signals.direction[0], -1)
        self.assertAlmostEqual(signals.stop_price[0], 102.5)
        self.assertAlmostEqual(signals.target_price[0], 98.3)

    def test_vwap_mean_reversion_targets_signal_vwap(self) -> None:
        arrays = make_exp009_arrays()
        arrays.close_5m[0, 11] = 103.0
        arrays.high_5m[0, 11] = 103.2
        arrays.close_5m[0, 12] = 101.0
        arrays.high_5m[0, 12] = 102.0
        arrays.open_5m[0, 13] = 100.8
        signals = generate_exp009_signals(
            arrays, get_exp009_candidate("vwap_reversion_1p5sd_vwap")
        )
        self.assertEqual(signals.direction[0], -1)
        self.assertEqual(signals.entry_minute_slot[0], 65)
        self.assertAlmostEqual(signals.target_price[0], 100.0)

    def test_vwap_trend_pullback_requires_trend_side_close(self) -> None:
        arrays = make_exp009_arrays()
        arrays.vwap_5m[0, 3] = 99.0
        arrays.vwap_5m[0, 6] = 100.0
        arrays.close_5m[0, 6] = 100.5
        arrays.low_5m[0, 6] = 99.8
        arrays.open_5m[0, 7] = 100.6
        signals = generate_exp009_signals(
            arrays, get_exp009_candidate("vwap_trend_1close_1r")
        )
        self.assertEqual(signals.direction[0], 1)
        self.assertAlmostEqual(signals.stop_price[0], 99.8)

    def test_compression_freezes_earliest_range_then_breaks_out(self) -> None:
        arrays = make_exp009_arrays()
        set_opening_range(arrays, high=102.0, low=98.0)
        arrays.high_5m[0, 6:12] = 100.5
        arrays.low_5m[0, 6:12] = 99.5
        arrays.close_5m[0, 12] = 101.0
        arrays.open_5m[0, 13] = 101.1
        signals = generate_exp009_signals(
            arrays, get_exp009_candidate("compression_0p5_1r")
        )
        self.assertEqual(signals.direction[0], 1)
        self.assertAlmostEqual(signals.stop_price[0], 99.5)

    def test_opening_drive_time_candidate_has_no_target(self) -> None:
        arrays = make_exp009_arrays()
        arrays.open[0, 0] = 100.0
        arrays.close[0, 29] = 102.0
        arrays.high[0, :30] = 102.2
        arrays.low[0, :30] = 99.8
        arrays.open_5m[0, 6] = 102.1
        signals = generate_exp009_signals(
            arrays, get_exp009_candidate("opening_drive_0p5_time")
        )
        self.assertEqual(signals.direction[0], 1)
        self.assertTrue(np.isnan(signals.target_price[0]))

    def test_same_minute_stop_and_target_uses_stop_first(self) -> None:
        arrays = make_exp009_arrays()
        arrays.open[0, 30] = 100.0
        arrays.high[0, 30] = 102.0
        arrays.low[0, 30] = 98.0
        candidate = get_exp009_candidate("opening_drive_0p5_1p5r")
        signals = Exp009Signals(
            candidate=candidate,
            direction=np.array([1], dtype=np.int8),
            signal_five_minute_slot=np.array([5], dtype=np.int16),
            entry_minute_slot=np.array([30], dtype=np.int16),
            stop_price=np.array([99.0]),
            target_price=np.array([101.0]),
            setup_reference=np.array([0.8]),
        )
        simulation = execute_exp009_signals(
            arrays, signals, symbol="NQ"
        )
        self.assertEqual(simulation.exit_reason[0], "protective_stop")
        self.assertAlmostEqual(simulation.exit_price[0], 99.0)

    def test_stop_gap_fills_at_open(self) -> None:
        arrays = make_exp009_arrays()
        arrays.open[0, 30] = 100.0
        arrays.high[0, 30] = 100.25
        arrays.low[0, 30] = 99.75
        arrays.open[0, 31] = 98.5
        arrays.high[0, 31] = 98.75
        arrays.low[0, 31] = 98.0
        candidate = get_exp009_candidate("opening_drive_0p5_1p5r")
        signals = Exp009Signals(
            candidate=candidate,
            direction=np.array([1], dtype=np.int8),
            signal_five_minute_slot=np.array([5], dtype=np.int16),
            entry_minute_slot=np.array([30], dtype=np.int16),
            stop_price=np.array([99.0]),
            target_price=np.array([101.0]),
            setup_reference=np.array([0.8]),
        )
        simulation = execute_exp009_signals(
            arrays, signals, symbol="NQ"
        )
        self.assertTrue(simulation.trade_mask[0])
        self.assertEqual(simulation.exit_reason[0], "gap_through_stop")
        self.assertAlmostEqual(simulation.exit_price[0], 98.5)


if __name__ == "__main__":
    unittest.main()
