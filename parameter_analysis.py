from __future__ import annotations

import math
import re
from dataclasses import dataclass
from itertools import product
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ParameterStabilityAnalysis:
    detail: pd.DataFrame
    summary: dict[str, Any]


def _values_equal(left: Any, right: Any) -> bool:
    if isinstance(left, (int, float, np.integer, np.floating)) and isinstance(
        right,
        (int, float, np.integer, np.floating),
    ):
        return bool(
            np.isclose(
                float(left),
                float(right),
                equal_nan=False,
            )
        )

    return left == right


def _stable_unique(series: pd.Series) -> list[Any]:
    values = list(pd.unique(series.dropna()))

    if not values:
        return []

    if all(
        isinstance(value, (int, float, np.integer, np.floating))
        for value in values
    ):
        return sorted(values, key=float)

    return sorted(values, key=lambda value: str(value))


def _slug(value: Any) -> str:
    text = str(value)
    text = re.sub(r"[^A-Za-z0-9_.-]+", "-", text)
    return text.strip("-") or "value"


def analyze_parameter_stability(
    optimization_table: pd.DataFrame,
    parameter_names: tuple[str, ...] | list[str],
    best_parameters: dict[str, Any],
    *,
    score_column: str = "bar_profit_factor",
    near_best_fraction: float = 0.95,
) -> ParameterStabilityAnalysis:
    parameter_names = tuple(parameter_names)

    required = set(parameter_names) | {score_column}
    missing = required.difference(
        optimization_table.columns
    )

    if missing:
        raise ValueError(
            "Optimization table is missing columns: "
            f"{sorted(missing)}"
        )

    if not 0 < near_best_fraction <= 1:
        raise ValueError(
            "near_best_fraction must be in (0, 1]."
        )

    detail = optimization_table.copy()
    detail[score_column] = pd.to_numeric(
        detail[score_column],
        errors="coerce",
    )

    valid_mask = np.isfinite(
        detail[score_column].to_numpy(dtype=float)
    )

    valid = detail.loc[valid_mask].copy()

    if valid.empty:
        raise ValueError(
            "No finite parameter scores were available."
        )

    best_mask = pd.Series(
        True,
        index=valid.index,
    )

    parameter_values: dict[str, list[Any]] = {}
    parameter_positions: dict[str, dict[Any, int]] = {}

    for parameter_name in parameter_names:
        values = _stable_unique(
            valid[parameter_name]
        )
        parameter_values[parameter_name] = values
        parameter_positions[parameter_name] = {
            value: position
            for position, value in enumerate(values)
        }

        target = best_parameters[parameter_name]

        best_mask &= valid[parameter_name].map(
            lambda value: _values_equal(
                value,
                target,
            )
        )

    if not bool(best_mask.any()):
        raise ValueError(
            "Best parameters were not found in the "
            "optimization table."
        )

    best_row = valid.loc[best_mask].iloc[0]
    best_score = float(
        best_row[score_column]
    )

    best_grid_positions: dict[str, int] = {}

    for parameter_name in parameter_names:
        best_value = best_row[parameter_name]
        match_position = None

        for value, position in (
            parameter_positions[
                parameter_name
            ].items()
        ):
            if _values_equal(value, best_value):
                match_position = position
                break

        if match_position is None:
            raise RuntimeError(
                f"Could not locate {parameter_name} "
                "on its parameter grid."
            )

        best_grid_positions[
            parameter_name
        ] = match_position

    distances: list[int] = []

    for _, row in detail.iterrows():
        if not np.isfinite(
            float(row[score_column])
        ):
            distances.append(-1)
            continue

        distance = 0

        for parameter_name in parameter_names:
            row_value = row[parameter_name]
            row_position = None

            for value, position in (
                parameter_positions[
                    parameter_name
                ].items()
            ):
                if _values_equal(value, row_value):
                    row_position = position
                    break

            if row_position is None:
                distance = -1
                break

            distance += abs(
                row_position
                - best_grid_positions[
                    parameter_name
                ]
            )

        distances.append(distance)

    near_best_threshold = (
        best_score * near_best_fraction
    )

    detail["distance_from_best_steps"] = distances
    detail["is_best"] = False
    detail.loc[best_row.name, "is_best"] = True
    detail["is_immediate_neighbor"] = (
        detail["distance_from_best_steps"] == 1
    )
    detail["near_best"] = (
        detail[score_column]
        >= near_best_threshold
    )
    detail["at_or_above_break_even"] = (
        detail[score_column] >= 1.0
    )

    valid_scores = (
        valid[score_column]
        .astype(float)
        .sort_values(
            ascending=False
        )
    )

    detail["score_rank"] = (
        detail[score_column]
        .rank(
            method="min",
            ascending=False,
        )
    )

    immediate_neighbors = detail.loc[
        detail["is_immediate_neighbor"]
        & valid_mask,
        score_column,
    ].astype(float)

    second_best_score = (
        float(valid_scores.iloc[1])
        if len(valid_scores) > 1
        else float("nan")
    )

    if immediate_neighbors.empty:
        neighbor_mean = float("nan")
        neighbor_median = float("nan")
        neighbor_min = float("nan")
        neighbor_max = float("nan")
        neighbor_retention = float("nan")
    else:
        neighbor_mean = float(
            immediate_neighbors.mean()
        )
        neighbor_median = float(
            immediate_neighbors.median()
        )
        neighbor_min = float(
            immediate_neighbors.min()
        )
        neighbor_max = float(
            immediate_neighbors.max()
        )
        neighbor_retention = (
            neighbor_median / best_score
            if best_score != 0
            else float("nan")
        )

    near_best_count = int(
        detail.loc[
            valid_mask,
            "near_best",
        ].sum()
    )

    break_even_count = int(
        detail.loc[
            valid_mask,
            "at_or_above_break_even",
        ].sum()
    )

    valid_count = int(valid_mask.sum())

    near_best_share = (
        near_best_count / valid_count
    )

    break_even_share = (
        break_even_count / valid_count
    )

    if best_score < 1.0:
        edge_assessment = "NO_IN_SAMPLE_EDGE"
    elif break_even_share >= 0.25:
        edge_assessment = "BROAD_IN_SAMPLE_EDGE"
    else:
        edge_assessment = "LIMITED_IN_SAMPLE_EDGE"

    if immediate_neighbors.empty:
        local_surface = "INSUFFICIENT_NEIGHBORS"
    elif (
        neighbor_retention >= 0.95
        and near_best_share >= 0.20
    ):
        local_surface = "BROAD_STABLE_REGION"
    elif neighbor_retention >= 0.90:
        local_surface = "MODERATE_LOCAL_STABILITY"
    elif (
        near_best_count == 1
        or neighbor_retention < 0.85
    ):
        local_surface = "ISOLATED_OR_FRAGILE_PEAK"
    else:
        local_surface = "MIXED_LOCAL_STABILITY"

    if edge_assessment == "NO_IN_SAMPLE_EDGE":
        interpretation = (
            "No tested parameter combination reached a "
            "bar Profit Factor of 1.0. Surface stability "
            "cannot rescue an economically weak objective."
        )
    elif local_surface == "BROAD_STABLE_REGION":
        interpretation = (
            "The best score sits inside a relatively broad "
            "and locally stable parameter region."
        )
    elif local_surface == "ISOLATED_OR_FRAGILE_PEAK":
        interpretation = (
            "The best score is materially stronger than its "
            "immediate grid neighbours, which raises "
            "overfitting risk."
        )
    else:
        interpretation = (
            "The parameter surface shows partial stability, "
            "but not a clearly broad high-performing region."
        )

    numeric_parameter_count = sum(
        pd.api.types.is_numeric_dtype(
            valid[parameter_name]
        )
        for parameter_name in parameter_names
    )

    if (
        len(parameter_names) >= 2
        and numeric_parameter_count
        == len(parameter_names)
    ):
        slice_parameters = parameter_names[2:]
        heatmap_slice_count = math.prod(
            len(parameter_values[name])
            for name in slice_parameters
        ) if slice_parameters else 1
    else:
        heatmap_slice_count = 0

    summary = {
        "score_column": score_column,
        "parameter_names": list(
            parameter_names
        ),
        "total_combinations": int(
            len(detail)
        ),
        "valid_combinations": valid_count,
        "best_score": best_score,
        "second_best_score": (
            second_best_score
        ),
        "best_vs_second_gap": (
            best_score - second_best_score
            if np.isfinite(second_best_score)
            else float("nan")
        ),
        "near_best_fraction_of_best": (
            near_best_fraction
        ),
        "near_best_threshold": (
            near_best_threshold
        ),
        "near_best_count": near_best_count,
        "near_best_share": near_best_share,
        "break_even_count": (
            break_even_count
        ),
        "break_even_share": (
            break_even_share
        ),
        "immediate_neighbor_count": int(
            len(immediate_neighbors)
        ),
        "neighbor_mean_score": (
            neighbor_mean
        ),
        "neighbor_median_score": (
            neighbor_median
        ),
        "neighbor_min_score": (
            neighbor_min
        ),
        "neighbor_max_score": (
            neighbor_max
        ),
        "neighbor_retention_ratio": (
            neighbor_retention
        ),
        "edge_assessment": (
            edge_assessment
        ),
        "local_surface_assessment": (
            local_surface
        ),
        "interpretation": interpretation,
        "heatmap_slice_count": int(
            heatmap_slice_count
        ),
    }

    return ParameterStabilityAnalysis(
        detail=detail,
        summary=summary,
    )


def create_parameter_heatmaps(
    optimization_table: pd.DataFrame,
    parameter_names: tuple[str, ...] | list[str],
    best_parameters: dict[str, Any],
    output_directory: Path,
    *,
    score_column: str = "bar_profit_factor",
    filename_prefix: str = "03a_parameter_heatmap",
    maximum_slices: int = 16,
) -> list[tuple[str, str]]:
    parameter_names = tuple(parameter_names)

    if len(parameter_names) < 2:
        return []

    if not all(
        pd.api.types.is_numeric_dtype(
            optimization_table[
                parameter_name
            ]
        )
        for parameter_name in parameter_names
    ):
        return []

    if maximum_slices < 1:
        raise ValueError(
            "maximum_slices must be at least 1."
        )

    x_parameter = parameter_names[1]
    y_parameter = parameter_names[0]
    slice_parameters = parameter_names[2:]

    slice_values = [
        _stable_unique(
            optimization_table[
                parameter_name
            ]
        )
        for parameter_name in slice_parameters
    ]

    slice_combinations = (
        list(product(*slice_values))
        if slice_parameters
        else [()]
    )

    if len(slice_combinations) > maximum_slices:
        scored_slices: list[
            tuple[float, tuple[Any, ...]]
        ] = []

        for combination in slice_combinations:
            subset = optimization_table

            for parameter_name, value in zip(
                slice_parameters,
                combination,
            ):
                subset = subset.loc[
                    subset[parameter_name].map(
                        lambda candidate: (
                            _values_equal(
                                candidate,
                                value,
                            )
                        )
                    )
                ]

            maximum = pd.to_numeric(
                subset[score_column],
                errors="coerce",
            ).max()

            scored_slices.append(
                (
                    float(maximum)
                    if np.isfinite(maximum)
                    else float("-inf"),
                    combination,
                )
            )

        slice_combinations = [
            combination
            for _, combination in sorted(
                scored_slices,
                key=lambda item: item[0],
                reverse=True,
            )[:maximum_slices]
        ]

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    chart_sections: list[
        tuple[str, str]
    ] = []

    for slice_number, combination in enumerate(
        slice_combinations,
        start=1,
    ):
        subset = optimization_table.copy()
        slice_description_parts: list[str] = []

        for parameter_name, value in zip(
            slice_parameters,
            combination,
        ):
            subset = subset.loc[
                subset[parameter_name].map(
                    lambda candidate: _values_equal(
                        candidate,
                        value,
                    )
                )
            ]

            slice_description_parts.append(
                f"{parameter_name}={value}"
            )

        x_values = _stable_unique(
            subset[x_parameter]
        )
        y_values = _stable_unique(
            subset[y_parameter]
        )

        pivot = subset.pivot_table(
            index=y_parameter,
            columns=x_parameter,
            values=score_column,
            aggfunc="max",
        ).reindex(
            index=y_values,
            columns=x_values,
        )

        matrix = pivot.to_numpy(
            dtype=float
        )

        fig, axis = plt.subplots(
            figsize=(11, 8)
        )

        image = axis.imshow(
            matrix,
            aspect="auto",
            origin="lower",
        )

        fig.colorbar(
            image,
            ax=axis,
            label="In-Sample Bar Profit Factor",
        )

        axis.set_xticks(
            np.arange(len(x_values))
        )
        axis.set_xticklabels(
            [str(value) for value in x_values]
        )
        axis.set_yticks(
            np.arange(len(y_values))
        )
        axis.set_yticklabels(
            [str(value) for value in y_values]
        )

        axis.set_xlabel(x_parameter)
        axis.set_ylabel(y_parameter)

        title = (
            "Parameter Heatmap: "
            f"{y_parameter} × {x_parameter}"
        )

        if slice_description_parts:
            title += (
                " | "
                + ", ".join(
                    slice_description_parts
                )
            )

        axis.set_title(title)

        for row_index in range(
            matrix.shape[0]
        ):
            for column_index in range(
                matrix.shape[1]
            ):
                value = matrix[
                    row_index,
                    column_index,
                ]

                if np.isfinite(value):
                    axis.text(
                        column_index,
                        row_index,
                        f"{value:.3f}",
                        ha="center",
                        va="center",
                    )

        best_in_slice = all(
            _values_equal(
                best_parameters[
                    parameter_name
                ],
                value,
            )
            for parameter_name, value in zip(
                slice_parameters,
                combination,
            )
        )

        if best_in_slice:
            best_x = best_parameters[
                x_parameter
            ]
            best_y = best_parameters[
                y_parameter
            ]

            x_index = next(
                (
                    index
                    for index, value in enumerate(
                        x_values
                    )
                    if _values_equal(
                        value,
                        best_x,
                    )
                ),
                None,
            )

            y_index = next(
                (
                    index
                    for index, value in enumerate(
                        y_values
                    )
                    if _values_equal(
                        value,
                        best_y,
                    )
                ),
                None,
            )

            if (
                x_index is not None
                and y_index is not None
            ):
                axis.scatter(
                    [x_index],
                    [y_index],
                    marker="x",
                    s=180,
                    linewidths=3,
                    label="Global best",
                )
                axis.legend()

        fig.tight_layout()

        suffix = ""

        if slice_description_parts:
            suffix = "_" + "_".join(
                _slug(part)
                for part in (
                    slice_description_parts
                )
            )

        filename = (
            f"{filename_prefix}_"
            f"{slice_number:02d}"
            f"{suffix}.png"
        )

        fig.savefig(
            output_directory / filename,
            dpi=150,
            bbox_inches="tight",
        )

        plt.close(fig)

        chart_sections.append(
            (
                title,
                filename,
            )
        )

    return chart_sections
