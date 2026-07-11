from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from parameter_analysis import (
    analyze_parameter_stability,
    create_parameter_heatmaps,
)


def grid_table(
    scores: list[list[float]],
) -> pd.DataFrame:
    rows = []

    for row_index, lookback in enumerate(
        [24, 48, 72]
    ):
        for column_index, threshold in enumerate(
            [1.0, 2.0, 3.0]
        ):
            rows.append(
                {
                    "lookback": lookback,
                    "threshold": threshold,
                    "bar_profit_factor": scores[
                        row_index
                    ][column_index],
                }
            )

    return pd.DataFrame(rows)


class ParameterStabilityTests(unittest.TestCase):
    def test_broad_surface_is_identified(
        self,
    ) -> None:
        table = grid_table(
            [
                [1.02, 1.06, 1.03],
                [1.07, 1.10, 1.08],
                [1.03, 1.07, 1.04],
            ]
        )

        analysis = analyze_parameter_stability(
            table,
            ("lookback", "threshold"),
            {
                "lookback": 48,
                "threshold": 2.0,
            },
        )

        self.assertEqual(
            analysis.summary[
                "edge_assessment"
            ],
            "BROAD_IN_SAMPLE_EDGE",
        )

        self.assertEqual(
            analysis.summary[
                "local_surface_assessment"
            ],
            "BROAD_STABLE_REGION",
        )

        self.assertGreater(
            analysis.summary[
                "near_best_count"
            ],
            1,
        )

    def test_isolated_peak_is_identified(
        self,
    ) -> None:
        table = grid_table(
            [
                [0.90, 0.91, 0.89],
                [0.92, 1.25, 0.90],
                [0.88, 0.93, 0.91],
            ]
        )

        analysis = analyze_parameter_stability(
            table,
            ("lookback", "threshold"),
            {
                "lookback": 48,
                "threshold": 2.0,
            },
        )

        self.assertEqual(
            analysis.summary[
                "local_surface_assessment"
            ],
            "ISOLATED_OR_FRAGILE_PEAK",
        )

        self.assertEqual(
            analysis.summary[
                "near_best_count"
            ],
            1,
        )

    def test_no_edge_is_reported_even_when_surface_is_smooth(
        self,
    ) -> None:
        table = grid_table(
            [
                [0.91, 0.92, 0.91],
                [0.92, 0.98, 0.93],
                [0.91, 0.92, 0.91],
            ]
        )

        analysis = analyze_parameter_stability(
            table,
            ("lookback", "threshold"),
            {
                "lookback": 48,
                "threshold": 2.0,
            },
        )

        self.assertEqual(
            analysis.summary[
                "edge_assessment"
            ],
            "NO_IN_SAMPLE_EDGE",
        )

        self.assertEqual(
            analysis.summary[
                "break_even_count"
            ],
            0,
        )

    def test_two_parameter_heatmap_is_created(
        self,
    ) -> None:
        table = grid_table(
            [
                [1.00, 1.01, 1.02],
                [1.03, 1.04, 1.05],
                [1.06, 1.07, 1.08],
            ]
        )

        with tempfile.TemporaryDirectory() as folder:
            output_directory = Path(folder)

            sections = create_parameter_heatmaps(
                optimization_table=table,
                parameter_names=(
                    "lookback",
                    "threshold",
                ),
                best_parameters={
                    "lookback": 72,
                    "threshold": 3.0,
                },
                output_directory=output_directory,
            )

            self.assertEqual(
                len(sections),
                1,
            )

            self.assertTrue(
                (
                    output_directory
                    / sections[0][1]
                ).exists()
            )

    def test_three_parameter_grid_creates_slices(
        self,
    ) -> None:
        base = grid_table(
            [
                [1.00, 1.01, 1.02],
                [1.03, 1.04, 1.05],
                [1.06, 1.07, 1.08],
            ]
        )

        frames = []

        for holding_period in (12, 24):
            frame = base.copy()
            frame["holding_period"] = (
                holding_period
            )
            frame["bar_profit_factor"] += (
                holding_period / 1000
            )
            frames.append(frame)

        table = pd.concat(
            frames,
            ignore_index=True,
        )

        with tempfile.TemporaryDirectory() as folder:
            output_directory = Path(folder)

            sections = create_parameter_heatmaps(
                optimization_table=table,
                parameter_names=(
                    "lookback",
                    "threshold",
                    "holding_period",
                ),
                best_parameters={
                    "lookback": 72,
                    "threshold": 3.0,
                    "holding_period": 24,
                },
                output_directory=output_directory,
            )

            self.assertEqual(
                len(sections),
                2,
            )

            self.assertTrue(
                all(
                    (
                        output_directory
                        / filename
                    ).exists()
                    for _, filename in sections
                )
            )


if __name__ == "__main__":
    unittest.main()
