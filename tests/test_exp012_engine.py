from __future__ import annotations

import unittest

import numpy as np

from exp012_engine import (
    context_feature_table,
    generate_exp012_signals,
    get_exp012_candidate,
    locked_exp012_candidates,
    prepare_exp012_arrays,
    run_exp012_candidate,
)
from tests.exp012_test_data import (
    make_exp012_arrays,
    make_extended_frame,
    set_first_cash_bar,
)


class Exp012EngineTests(unittest.TestCase):
    def test_locked_budget_has_six_families_and_24_candidates(
        self,
    ) -> None:
        candidates = locked_exp012_candidates()
        self.assertEqual(len(candidates), 24)
        self.assertEqual(len({item.candidate_id for item in candidates}), 24)
        self.assertEqual(len({item.family_id for item in candidates}), 6)

    def test_prepare_arrays_builds_context_and_cash_alignment(self) -> None:
        dates = ["2024-01-02", "2024-01-03"]
        arrays = prepare_exp012_arrays(
            make_extended_frame(dates),
            calendar_session_dates=dates,
        )
        self.assertEqual(arrays.session_count, 2)
        self.assertEqual(arrays.cash.open.shape, (2, 390))
        self.assertEqual(arrays.cash.open_5m.shape, (2, 78))
        self.assertFalse(bool(arrays.previous_cash_available[0]))
        self.assertTrue(bool(arrays.previous_cash_available[1]))
        self.assertEqual(len(context_feature_table(arrays)), 2)

    def test_gap_requires_immediately_preceding_calendar_session(
        self,
    ) -> None:
        included = ["2024-01-02", "2024-01-03", "2024-01-05"]
        calendar = [
            "2024-01-02",
            "2024-01-03",
            "2024-01-04",
            "2024-01-05",
        ]
        arrays = prepare_exp012_arrays(
            make_extended_frame(included),
            calendar_session_dates=calendar,
        )
        self.assertFalse(bool(arrays.previous_cash_available[0]))
        self.assertTrue(bool(arrays.previous_cash_available[1]))
        self.assertFalse(bool(arrays.previous_cash_available[2]))
        self.assertTrue(np.isnan(arrays.gap_fraction[2]))

    def test_gap_continuation_enters_next_open(self) -> None:
        arrays = make_exp012_arrays(1)
        set_first_cash_bar(
            arrays,
            opening=100.0,
            high=101.25,
            low=99.5,
            close=101.0,
            next_open=101.0,
        )
        candidate = get_exp012_candidate(
            "gap_continuation_0p25_time"
        )
        signals = generate_exp012_signals(arrays, candidate)
        self.assertEqual(int(signals.direction[0]), 1)
        self.assertEqual(int(signals.entry_minute_slot[0]), 5)
        self.assertEqual(float(signals.stop_price[0]), 99.5)
        self.assertTrue(np.isnan(signals.target_price[0]))

    def test_gap_fade_targets_prior_cash_close(self) -> None:
        arrays = make_exp012_arrays(1)
        arrays.previous_cash_close[0] = 98.0
        set_first_cash_bar(
            arrays,
            opening=100.0,
            high=100.5,
            low=98.75,
            close=99.0,
            next_open=99.5,
        )
        candidate = get_exp012_candidate(
            "gap_fade_0p25_prior_close"
        )
        signals = generate_exp012_signals(arrays, candidate)
        self.assertEqual(int(signals.direction[0]), -1)
        self.assertEqual(float(signals.stop_price[0]), 100.5)
        self.assertEqual(float(signals.target_price[0]), 98.0)

    def test_overnight_continuation_uses_overnight_direction(
        self,
    ) -> None:
        arrays = make_exp012_arrays(1)
        arrays.overnight_drive_fraction[0] = 0.80
        arrays.overnight_direction[0] = 1
        set_first_cash_bar(
            arrays,
            opening=100.0,
            high=101.25,
            low=99.5,
            close=101.0,
            next_open=101.0,
        )
        candidate = get_exp012_candidate(
            "overnight_continuation_0p75_1p5r"
        )
        signals = generate_exp012_signals(arrays, candidate)
        self.assertEqual(int(signals.direction[0]), 1)
        self.assertAlmostEqual(float(signals.target_price[0]), 103.25)

    def test_overnight_reversal_targets_overnight_open(self) -> None:
        arrays = make_exp012_arrays(1)
        arrays.overnight_drive_fraction[0] = 0.80
        arrays.overnight_direction[0] = 1
        arrays.overnight_open[0] = 97.0
        set_first_cash_bar(
            arrays,
            opening=100.0,
            high=100.5,
            low=98.75,
            close=99.0,
            next_open=99.5,
        )
        candidate = get_exp012_candidate(
            "overnight_reversal_0p75_open"
        )
        signals = generate_exp012_signals(arrays, candidate)
        self.assertEqual(int(signals.direction[0]), -1)
        self.assertEqual(float(signals.target_price[0]), 97.0)

    def test_overnight_breakout_uses_completed_close(self) -> None:
        arrays = make_exp012_arrays(1)
        arrays.overnight_high[0] = 101.0
        arrays.overnight_low[0] = 98.0
        set_first_cash_bar(
            arrays,
            opening=100.0,
            high=102.25,
            low=99.5,
            close=102.0,
            next_open=101.5,
        )
        candidate = get_exp012_candidate(
            "overnight_breakout_1030_1r"
        )
        signals = generate_exp012_signals(arrays, candidate)
        self.assertEqual(int(signals.direction[0]), 1)
        self.assertEqual(int(signals.entry_minute_slot[0]), 5)
        self.assertEqual(float(signals.stop_price[0]), 99.5)
        self.assertEqual(float(signals.target_price[0]), 103.5)

    def test_premarket_continuation_uses_premarket_direction(
        self,
    ) -> None:
        arrays = make_exp012_arrays(1)
        arrays.premarket_drive_fraction[0] = 0.80
        arrays.premarket_direction[0] = -1
        set_first_cash_bar(
            arrays,
            opening=100.0,
            high=100.5,
            low=98.75,
            close=99.0,
            next_open=99.5,
        )
        candidate = get_exp012_candidate(
            "premarket_continuation_0p75_time"
        )
        signals = generate_exp012_signals(arrays, candidate)
        self.assertEqual(int(signals.direction[0]), -1)
        self.assertTrue(np.isnan(signals.target_price[0]))

    def test_result_retains_context_measurements(self) -> None:
        arrays = make_exp012_arrays(1)
        set_first_cash_bar(
            arrays,
            opening=100.0,
            high=101.25,
            low=99.5,
            close=101.0,
            next_open=101.0,
        )
        arrays.cash.open[0, 385] = 102.0
        candidate = get_exp012_candidate(
            "gap_continuation_0p25_time"
        )
        result = run_exp012_candidate(
            arrays, candidate, symbol="NQ"
        )
        self.assertEqual(result.summary["feature_eligible_sessions"], 1)
        self.assertEqual(result.summary["signal_confirmed_sessions"], 1)
        self.assertEqual(result.summary["context_value_name"], "gap_fraction")
        self.assertIn("context_value", result.trades.columns)


if __name__ == "__main__":
    unittest.main()
