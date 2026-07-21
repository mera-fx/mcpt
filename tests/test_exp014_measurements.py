from __future__ import annotations

import unittest

import numpy as np

from exp014_measurements import (
    behaviour_breakdowns,
    concentration_measurements,
    drawdown_diagnostics,
    enrich_trade_ledger,
    monthly_measurements,
    overlap_measurements,
    period_comparison,
    rolling_trade_measurements,
    session_pnl_table,
    session_regime_table,
    sleeve_pair_measurements,
)
from exp014_preregistration import FINALIST_IDS
from tests.exp014_test_data import (
    synthetic_exp014_arrays,
    synthetic_exp014_results,
)


class Exp014MeasurementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.arrays = synthetic_exp014_arrays()
        cls.results = synthetic_exp014_results(cls.arrays)
        cls.regimes, cls.boundary = session_regime_table(cls.arrays)
        cls.ledgers = {
            candidate_id: enrich_trade_ledger(
                cls.arrays,
                cls.results[candidate_id],
                cls.regimes,
            )
            for candidate_id in FINALIST_IDS
        }
        cls.session_pnl = session_pnl_table(cls.arrays, cls.ledgers)

    def test_regimes_use_prior_data_and_report_boundary(self) -> None:
        self.assertTrue(np.isfinite(self.boundary))
        self.assertEqual(len(self.regimes), self.arrays.session_count)
        self.assertEqual(
            self.regimes.loc[0, "trend_regime"], "UNAVAILABLE"
        )
        self.assertIn(
            "UP",
            set(self.regimes["trend_regime"]),
        )

    def test_enriched_ledgers_include_locked_diagnostics(self) -> None:
        for candidate_id, ledger in self.ledgers.items():
            self.assertEqual(len(ledger), 80)
            self.assertTrue(
                {
                    "trend_regime",
                    "volatility_regime",
                    "entry_time",
                    "exit_time",
                    "holding_time_band",
                    "context_strength_band",
                    "pre_exit_mfe_usd",
                    "pre_exit_mae_usd",
                    "captured_fraction_of_mfe",
                    "candidate_trade_number",
                }.issubset(ledger.columns)
            )
            self.assertTrue((ledger["pre_exit_mfe_usd"] >= 0).all())
            self.assertTrue((ledger["pre_exit_mae_usd"] <= 0).all())
            self.assertEqual(
                list(ledger["candidate_trade_number"]),
                list(range(1, 81)),
            )

    def test_all_preregistered_breakdowns_are_measured(self) -> None:
        behaviour = behaviour_breakdowns(self.ledgers)
        self.assertEqual(
            set(behaviour["dimension"]),
            {
                "year",
                "direction",
                "exit_reason",
                "holding_time",
                "context_strength",
                "trend_regime",
                "volatility_regime",
                "entry_time",
                "exit_time",
            },
        )
        periods = period_comparison(self.ledgers)
        self.assertEqual(len(periods), 9)
        self.assertEqual(
            set(periods["period"]),
            {"2020-2024", "2022-2024", "2025"},
        )
        concentration = concentration_measurements(self.ledgers)
        self.assertEqual(len(concentration), 3)
        self.assertIn(
            "net_after_removing_best_10_usd",
            concentration.columns,
        )

    def test_monthly_rolling_overlap_pair_and_drawdown_outputs(self) -> None:
        monthly = monthly_measurements(self.session_pnl, self.ledgers)
        expected_months = (
            self.session_pnl["session_date"].str[:7].nunique()
        )
        self.assertEqual(len(monthly), expected_months * 3)
        self.assertEqual(set(monthly["candidate_id"]), set(FINALIST_IDS))

        rolling = rolling_trade_measurements(self.ledgers)
        self.assertEqual(set(rolling["window_trades"]), {20, 50})
        self.assertEqual(set(rolling["candidate_id"]), set(FINALIST_IDS))

        overlap = overlap_measurements(self.session_pnl, self.ledgers)
        self.assertEqual(len(overlap), 3)
        self.assertTrue((overlap["overlap_sessions"] > 0).all())
        self.assertTrue(
            overlap["all_session_pnl_correlation"].between(-1, 1).all()
        )

        pairs, pair_daily = sleeve_pair_measurements(
            self.session_pnl, self.ledgers
        )
        self.assertEqual(len(pairs), 2)
        self.assertEqual(len(pair_daily), self.arrays.session_count)
        self.assertTrue(
            pairs["diagnostic_not_executable_portfolio"].all()
        )
        self.assertTrue((pairs["total_years"] == 1).all())
        self.assertTrue((pairs["profitable_years"] == 1).all())
        self.assertFalse(pairs["worst_year_usd"].isna().any())
        self.assertTrue(
            np.allclose(
                pairs["worst_year_usd"].to_numpy(dtype=float),
                pairs["net_profit_usd"].to_numpy(dtype=float),
            )
        )

        drawdowns = drawdown_diagnostics(self.session_pnl, pair_daily)
        self.assertEqual(len(drawdowns), 5)
        self.assertEqual(
            set(drawdowns["series_type"]),
            {"standalone", "research_sleeve_pair"},
        )
        self.assertTrue((drawdowns["maximum_drawdown_usd"] <= 0).all())


if __name__ == "__main__":
    unittest.main()
