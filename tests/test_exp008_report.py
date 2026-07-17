from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
import pandas as pd

from exp008_orb import (
    locked_exp008_parameters,
)
from exp008_report import (
    REPORT_VERSION,
    build_exp008_no_candidate_report,
    build_exp008_report,
)


def make_grid() -> pd.DataFrame:
    rows = []
    for index, parameters in enumerate(
        locked_exp008_parameters()
    ):
        rows.append(
            {
                **parameters.to_dict(),
                "nq_trade_profit_factor": (
                    1.05 + index * 0.005
                ),
                "nq_net_profit_usd": (
                    1000.0 + index * 100.0
                ),
                "nq_completed_trades": (
                    600 + index
                ),
                "nq_net_profit_to_drawdown": (
                    1.5 + index * 0.01
                ),
                "profitable_neighbor_fraction": (
                    1.0
                ),
                "neighbor_median_nq_trade_profit_factor": (
                    1.08
                ),
                "neighbor_stable": True,
                "neighbor_keys": "",
                "eligible": True,
                "selected": (
                    parameters.key
                    == "or45_target1p5_flat1555"
                ),
            }
        )

    frame = pd.DataFrame(rows)
    selected_index = frame.index[
        frame["selected"]
    ][0]
    neighbor_keys = frame.loc[
        [
            selected_index - 1,
            selected_index - 3,
        ],
        "parameter_key",
    ].tolist()
    frame.loc[
        selected_index,
        "neighbor_keys",
    ] = "|".join(neighbor_keys)
    return frame


def make_equity(
    key: str,
) -> pd.DataFrame:
    dates = pd.date_range(
        "2021-01-01",
        periods=20,
        freq="D",
    )
    pnl = np.array(
        [
            100.0,
            -50.0,
        ]
        * 10
    )
    cumulative = np.cumsum(pnl)
    peak = np.maximum.accumulate(
        np.maximum(
            cumulative,
            0.0,
        )
    )
    return pd.DataFrame(
        {
            "session_date": dates,
            "session_net_pnl_usd": pnl,
            "cumulative_net_pnl_usd": (
                cumulative
            ),
            "drawdown_usd": (
                cumulative - peak
            ),
            "had_trade": True,
            "parameter_key": key,
        }
    )


def make_decision() -> dict:
    selected = {
        "parameter_key": (
            "or45_target1p5_flat1555"
        ),
        "opening_range_minutes": 45,
        "reward_to_risk": 1.5,
        "forced_flat_time_new_york": (
            "15:55"
        ),
    }
    summary = {
        "completed_trades": 700,
        "long_trades": 700,
        "short_trades": 0,
        "net_profit_usd": 50_000.0,
        "trade_profit_factor": 1.25,
        "win_rate_percent": 52.0,
        "average_trade_usd": 71.4,
        "maximum_drawdown_usd": -10_000.0,
        "maximum_drawdown_percent": -10.0,
        "return_percent": 50.0,
    }
    return {
        "selection": {
            "selected_parameters": selected
        },
        "results": {
            "NQ": summary,
            "MNQ": {
                **summary,
                "net_profit_usd": 5_000.0,
                "maximum_drawdown_usd": (
                    -1_000.0
                ),
            },
        },
        "evaluation": {
            "decision": (
                "LOCK_EXP008_EXIT_GEOMETRY_CANDIDATE_FOR_NEW_FORWARD_PAPER_COMPARISON"
            ),
            "passed": True,
            "failed_gates": [],
            "gates": {
                "selected_nq_trade_profit_factor": {
                    "actual": 1.25,
                    "operator": ">",
                    "threshold": (
                        1.1168167521220216
                    ),
                    "passed": True,
                }
            },
        },
        "bootstrap": {
            "average_trade_usd_95_percentile_interval": [
                20.0,
                120.0,
            ],
            "trade_profit_factor_95_percentile_interval": [
                1.05,
                1.45,
            ],
        },
        "mcpt": {
            "permutations": 1000,
            "p_value": 0.03,
            "permutations_at_least_real": 29,
        },
        "baseline_comparison": {
            "exp007_parameter_key": (
                "or30_target1p0_flat1400"
            ),
            "exp007_nq_trade_profit_factor": (
                1.1168167521220216
            ),
            "exp008_selected_nq_trade_profit_factor": (
                1.25
            ),
            "absolute_profit_factor_difference": (
                1.25
                - 1.1168167521220216
            ),
        },
    }


class Exp008ReportTests(
    unittest.TestCase
):
    def test_report_creates_all_primary_assets(
        self,
    ) -> None:
        grid = make_grid()
        key = (
            "or45_target1p5_flat1555"
        )
        equity = make_equity(key)
        yearly = pd.DataFrame(
            {
                "symbol": [
                    "NQ",
                    "MNQ",
                ]
                * 5,
                "year": sorted(
                    [
                        2021,
                        2022,
                        2023,
                        2024,
                        2025,
                    ]
                    * 2
                ),
                "net_profit_usd": [
                    1000.0,
                    100.0,
                ]
                * 5,
            }
        )
        walk = pd.DataFrame(
            {
                "fold": [
                    1,
                    2,
                    3,
                    4,
                    5,
                ],
                "test_net_profit_usd": [
                    100.0,
                    200.0,
                    -50.0,
                    300.0,
                    400.0,
                ],
            }
        )
        costs = pd.DataFrame(
            {
                "symbol": [
                    "NQ",
                    "MNQ",
                ]
                * 3,
                "slippage_ticks_per_side": [
                    0.0,
                    0.0,
                    1.0,
                    1.0,
                    2.0,
                    2.0,
                ],
                "net_profit_usd": [
                    60_000.0,
                    6_000.0,
                    50_000.0,
                    5_000.0,
                    40_000.0,
                    4_000.0,
                ],
            }
        )
        mcpt = pd.DataFrame(
            {
                "selected_trade_profit_factor": (
                    np.linspace(
                        0.9,
                        1.3,
                        100,
                    )
                )
            }
        )

        with tempfile.TemporaryDirectory() as directory:
            report = build_exp008_report(
                decision=make_decision(),
                grid=grid,
                nq_equity=equity,
                mnq_equity=equity,
                yearly=yearly,
                walk_forward=walk,
                cost_sensitivity=costs,
                mcpt=mcpt,
                output_dir=Path(directory),
            )
            assets = Path(directory) / "assets"
            expected = [
                "nq_total_equity.png",
                "nq_drawdown_percent.png",
                "mnq_total_equity.png",
                "mnq_drawdown_percent.png",
                "annual_net_profit.png",
                "walk_forward_net_profit.png",
                "cost_sensitivity.png",
                "mcpt_selected_pf.png",
                "pf_surface_flat_1200.png",
                "pf_surface_flat_1400.png",
                "pf_surface_flat_1555.png",
            ]
            self.assertTrue(
                report.exists()
            )
            for filename in expected:
                self.assertTrue(
                    (
                        assets / filename
                    ).exists(),
                    filename,
                )

    def test_report_is_vertical_and_complete(
        self,
    ) -> None:
        grid = make_grid()
        key = (
            "or45_target1p5_flat1555"
        )
        equity = make_equity(key)
        yearly = pd.DataFrame(
            {
                "symbol": [
                    "NQ",
                    "MNQ",
                ]
                * 5,
                "year": [
                    2021,
                    2021,
                    2022,
                    2022,
                    2023,
                    2023,
                    2024,
                    2024,
                    2025,
                    2025,
                ],
                "net_profit_usd": [
                    1000.0,
                    100.0,
                ]
                * 5,
            }
        )
        walk = pd.DataFrame(
            {
                "fold": [
                    1,
                    2,
                    3,
                    4,
                    5,
                ],
                "test_net_profit_usd": [
                    100.0,
                    200.0,
                    -50.0,
                    300.0,
                    400.0,
                ],
            }
        )
        costs = pd.DataFrame(
            {
                "symbol": [
                    "NQ",
                    "MNQ",
                ]
                * 3,
                "slippage_ticks_per_side": [
                    0.0,
                    0.0,
                    1.0,
                    1.0,
                    2.0,
                    2.0,
                ],
                "net_profit_usd": [
                    60_000.0,
                    6_000.0,
                    50_000.0,
                    5_000.0,
                    40_000.0,
                    4_000.0,
                ],
            }
        )
        mcpt = pd.DataFrame(
            {
                "selected_trade_profit_factor": (
                    np.linspace(
                        0.9,
                        1.3,
                        100,
                    )
                )
            }
        )

        with tempfile.TemporaryDirectory() as directory:
            report = build_exp008_report(
                decision=make_decision(),
                grid=grid,
                nq_equity=equity,
                mnq_equity=equity,
                yearly=yearly,
                walk_forward=walk,
                cost_sensitivity=costs,
                mcpt=mcpt,
                output_dir=Path(directory),
            )
            source = report.read_text(
                encoding="utf-8"
            )
            metadata = json.loads(
                (
                    Path(directory)
                    / "report_metadata.json"
                ).read_text(
                    encoding="utf-8"
                )
            )

        self.assertIn(
            "Complete 27-candidate grid",
            source,
        )
        self.assertIn(
            "Anchored walk-forward evaluation",
            source,
        )
        self.assertIn(
            "Selection-aware MCPT",
            source,
        )
        self.assertIn(
            "Frozen EXP-007 baseline comparison",
            source,
        )
        self.assertIn(
            "grid-template-columns:1fr",
            source,
        )
        self.assertEqual(
            metadata["report_version"],
            REPORT_VERSION,
        )
        self.assertEqual(
            metadata[
                "parameter_combinations"
            ],
            27,
        )
        self.assertTrue(
            metadata[
                "selection_aware_mcpt"
            ]
        )


    def test_no_candidate_report_is_formal_result(
        self,
    ) -> None:
        grid = make_grid()
        grid["selected"] = False
        grid["neighbor_stable"] = False
        grid["eligible"] = False
        walk = pd.DataFrame(
            {
                "fold": [1, 2, 3, 4, 5],
                "test_net_profit_usd": [
                    0.0,
                    100.0,
                    -50.0,
                    0.0,
                    25.0,
                ],
            }
        )
        mcpt = pd.DataFrame(
            {
                "selected_trade_profit_factor": [
                    0.0,
                    1.05,
                    1.10,
                ]
            }
        )
        decision = {
            "grid": {
                "eligible_candidates": 0,
                "stable_eligible_candidates": 0,
            },
            "evaluation": {
                "decision": (
                    "REJECT_EXP008_PRESERVE_AS_NEGATIVE_RESULT"
                ),
                "passed": False,
                "selected_candidate_exists": False,
                "failed_gates": [
                    "selected_candidate_neighbor_stable"
                ],
                "gates": {
                    "selected_candidate_neighbor_stable": {
                        "actual": False,
                        "operator": "is",
                        "threshold": True,
                        "passed": False,
                    }
                },
            },
            "mcpt": {
                "permutations": 1000,
                "p_value": 1.0,
                "permutations_at_least_real": 1000,
            },
            "baseline_comparison": {
                "exp007_parameter_key": (
                    "or30_target1p0_flat1400"
                ),
                "exp007_nq_trade_profit_factor": (
                    1.1168167521220216
                ),
            },
        }

        with tempfile.TemporaryDirectory() as directory:
            report = build_exp008_no_candidate_report(
                decision=decision,
                grid=grid,
                walk_forward=walk,
                mcpt=mcpt,
                output_dir=Path(directory),
            )
            source = report.read_text(
                encoding="utf-8"
            )
            metadata = json.loads(
                (
                    Path(directory)
                    / "report_metadata.json"
                ).read_text(encoding="utf-8")
            )

            self.assertIn(
                "No candidate satisfied",
                source,
            )
            self.assertIn(
                "completed negative result",
                source,
            )
            self.assertIsNone(
                metadata[
                    "selected_parameter_key"
                ]
            )
            self.assertFalse(
                metadata[
                    "selected_candidate_exists"
                ]
            )


if __name__ == "__main__":
    unittest.main()
