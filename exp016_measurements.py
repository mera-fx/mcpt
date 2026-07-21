from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import hashlib
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


OHLCV = ["open", "high", "low", "close", "volume"]
TIMESTAMP_ALIASES = (
    "timestamp",
    "ts",
    "datetime",
    "date_time",
    "time",
    "time_left",
    "time left",
)

ALL_WINDOW_IDS = (
    "2020_march_dst_roll_volatility",
    "2021_thanksgiving",
    "2022_june_roll",
    "2023_march_dst_roll",
    "2024_thanksgiving",
    "2025_march_dst_roll",
)
ROLL_WINDOW_IDS = frozenset(
    {
        "2020_march_dst_roll_volatility",
        "2022_june_roll",
        "2023_march_dst_roll",
        "2025_march_dst_roll",
    }
)
OUTSIDE_ROLL_WINDOW_IDS = frozenset(
    {
        "2021_thanksgiving",
        "2024_thanksgiving",
    }
)


class Exp016MeasurementError(RuntimeError):
    pass


@dataclass(frozen=True)
class CanonicalFrame:
    frame: pd.DataFrame
    timestamp_timezone_aware: bool
    timestamp_source: str
    duplicate_timestamp_count: int
    invalid_ohlc_rows: int
    negative_volume_rows: int
    nonfinite_ohlcv_rows: int


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _normalized_name(value: Any) -> str:
    return str(value).strip().lower().replace("-", "_")


def canonicalize_vendor_frame(frame: pd.DataFrame) -> CanonicalFrame:
    if frame.empty:
        raise Exp016MeasurementError("Vendor sample contains no rows.")

    local = frame.copy()
    lower = {_normalized_name(column): column for column in local.columns}

    timestamp_source = ""
    if isinstance(local.index, pd.DatetimeIndex):
        raw_timestamp = pd.Series(local.index, index=local.index)
        timestamp_source = "index"
    else:
        timestamp_column = next(
            (
                lower[alias]
                for alias in TIMESTAMP_ALIASES
                if alias in lower
            ),
            None,
        )
        if timestamp_column is None:
            raise Exp016MeasurementError(
                "Vendor sample has no recognized timestamp field."
            )
        raw_timestamp = local[timestamp_column]
        timestamp_source = str(timestamp_column)

    parsed = pd.to_datetime(raw_timestamp, errors="coerce")
    if parsed.isna().any():
        raise Exp016MeasurementError(
            "Vendor sample contains unparseable timestamps."
        )

    timezone_aware = getattr(parsed.dt, "tz", None) is not None
    if timezone_aware:
        utc_index = pd.DatetimeIndex(parsed.dt.tz_convert("UTC"))
    else:
        utc_index = pd.DatetimeIndex(parsed)

    rename: dict[Any, str] = {}
    for target in OHLCV:
        source = lower.get(target)
        if source is None:
            raise Exp016MeasurementError(
                f"Vendor sample is missing the {target} field."
            )
        rename[source] = target

    values = local.rename(columns=rename)[OHLCV].copy()
    for column in OHLCV:
        values[column] = pd.to_numeric(values[column], errors="coerce")

    finite = np.isfinite(values.to_numpy(dtype=float))
    nonfinite_rows = int((~finite).any(axis=1).sum())

    high_invalid = values["high"] < values[
        ["open", "low", "close"]
    ].max(axis=1)
    low_invalid = values["low"] > values[
        ["open", "high", "close"]
    ].min(axis=1)
    invalid_ohlc = int((high_invalid | low_invalid).sum())
    negative_volume = int(values["volume"].lt(0).sum())

    values.index = utc_index
    values.index.name = "timestamp"
    duplicate_count = int(values.index.duplicated(keep=False).sum())
    values = values.sort_index(kind="mergesort")

    return CanonicalFrame(
        frame=values,
        timestamp_timezone_aware=timezone_aware,
        timestamp_source=timestamp_source,
        duplicate_timestamp_count=duplicate_count,
        invalid_ohlc_rows=invalid_ohlc,
        negative_volume_rows=negative_volume,
        nonfinite_ohlcv_rows=nonfinite_rows,
    )


def utc_window_bounds(start: str, end: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    lower = pd.Timestamp(start, tz="UTC")
    upper = pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1)
    return lower, upper


def _difference_bucket_counts(
    values: pd.Series,
    prefix: str,
) -> dict[str, int]:
    return {
        f"{prefix}_diff_exact_rows": int(values.eq(0.0).sum()),
        f"{prefix}_diff_gt_0_to_0p25_rows": int(
            values.gt(0.0).where(values.le(0.25), False).sum()
        ),
        f"{prefix}_diff_gt_0p25_to_1_rows": int(
            values.gt(0.25).where(values.le(1.0), False).sum()
        ),
        f"{prefix}_diff_gt_1_rows": int(values.gt(1.0).sum()),
    }


def compare_with_reference(
    *,
    vendor: CanonicalFrame,
    reference: pd.DataFrame,
    start: str,
    end: str,
    window_id: str,
) -> tuple[dict[str, Any], pd.DataFrame]:
    if not vendor.timestamp_timezone_aware:
        return (
            {
                "window_id": window_id,
                "comparison_status": "TIMESTAMP_TIMEZONE_UNRESOLVED",
                "reference_rows": None,
                "vendor_rows": int(len(vendor.frame)),
                "matched_rows": None,
                "vendor_only_rows": None,
                "quantower_only_rows": None,
                "expected_minute_completeness": None,
                "matched_timestamp_share": None,
                "close_within_one_tick_share": None,
            },
            pd.DataFrame(),
        )
    if vendor.duplicate_timestamp_count:
        return (
            {
                "window_id": window_id,
                "comparison_status": "DUPLICATE_TIMESTAMPS",
                "reference_rows": None,
                "vendor_rows": int(len(vendor.frame)),
                "matched_rows": None,
                "vendor_only_rows": None,
                "quantower_only_rows": None,
                "expected_minute_completeness": None,
                "matched_timestamp_share": None,
                "close_within_one_tick_share": None,
            },
            pd.DataFrame(),
        )

    local_reference = reference.copy()
    local_reference.index = pd.to_datetime(
        local_reference.index,
        utc=True,
    )
    lower, upper = utc_window_bounds(start, end)
    vendor_frame = vendor.frame.loc[
        (vendor.frame.index >= lower) & (vendor.frame.index < upper)
    ]
    reference_frame = local_reference.loc[
        (local_reference.index >= lower) & (local_reference.index < upper),
        OHLCV,
    ]

    matched_index = vendor_frame.index.intersection(reference_frame.index)
    vendor_only = vendor_frame.index.difference(reference_frame.index)
    reference_only = reference_frame.index.difference(vendor_frame.index)

    matched = vendor_frame.loc[matched_index, OHLCV].join(
        reference_frame.loc[matched_index, OHLCV],
        lsuffix="_vendor",
        rsuffix="_quantower",
        how="inner",
    )

    for column in ("open", "high", "low", "close"):
        matched[f"{column}_abs_diff"] = (
            matched[f"{column}_vendor"]
            - matched[f"{column}_quantower"]
        ).abs()
    matched["volume_abs_diff"] = (
        matched["volume_vendor"] - matched["volume_quantower"]
    ).abs()

    close_diff = matched["close_abs_diff"]
    difference_buckets: dict[str, int] = {}
    for column in ("open", "high", "low", "close"):
        difference_buckets.update(
            _difference_bucket_counts(
                matched[f"{column}_abs_diff"],
                column,
            )
        )

    reference_rows = int(len(reference_frame))
    matched_rows = int(len(matched_index))
    matched_share = (
        matched_rows / reference_rows if reference_rows else float("nan")
    )
    within_tick = (
        float(close_diff.le(0.25).mean()) if matched_rows else float("nan")
    )

    metrics = {
        "window_id": window_id,
        "comparison_status": "MEASURED",
        "reference_rows": reference_rows,
        "vendor_rows": int(len(vendor_frame)),
        "matched_rows": matched_rows,
        "vendor_only_rows": int(len(vendor_only)),
        "quantower_only_rows": int(len(reference_only)),
        "expected_minute_completeness": matched_share,
        "matched_timestamp_share": matched_share,
        "close_within_one_tick_share": within_tick,
        **difference_buckets,
        "mean_open_abs_diff": float(matched["open_abs_diff"].mean()),
        "mean_high_abs_diff": float(matched["high_abs_diff"].mean()),
        "mean_low_abs_diff": float(matched["low_abs_diff"].mean()),
        "mean_close_abs_diff": float(matched["close_abs_diff"].mean()),
        "mean_volume_abs_diff": float(matched["volume_abs_diff"].mean()),
    }

    if matched.empty:
        discrepancies = pd.DataFrame()
    else:
        discrepancies = matched.nlargest(
            100,
            "close_abs_diff",
        ).reset_index()
        discrepancies.insert(0, "window_id", window_id)

    return metrics, discrepancies


def classify_audit(
    structural: pd.DataFrame,
    cross_source: pd.DataFrame,
) -> str:
    if len(structural) != 6:
        return "STRUCTURE_UNRESOLVED"
    if (
        structural["invalid_ohlc_rows"].sum() > 0
        or structural["negative_volume_rows"].sum() > 0
        or structural["nonfinite_ohlcv_rows"].sum() > 0
    ):
        return "NOT_QUALIFIED"
    if structural["duplicate_timestamp_count"].sum() > 0:
        return "SUPPLEMENTARY_ONLY"
    if not bool(structural["timestamp_timezone_aware"].all()):
        return "STRUCTURE_UNRESOLVED"
    if len(cross_source) != 6:
        return "STRUCTURE_UNRESOLVED"
    if not cross_source["comparison_status"].eq("MEASURED").all():
        return "STRUCTURE_UNRESOLVED"

    if "window_id" not in cross_source.columns:
        return "STRUCTURE_UNRESOLVED"
    window_ids = set(cross_source["window_id"].astype(str))
    if window_ids != set(ALL_WINDOW_IDS):
        return "STRUCTURE_UNRESOLVED"

    required_overlap = cross_source[
        [
            "expected_minute_completeness",
            "matched_timestamp_share",
        ]
    ].apply(pd.to_numeric, errors="coerce")
    if not np.isfinite(required_overlap.to_numpy(dtype=float)).all():
        return "STRUCTURE_UNRESOLVED"
    if (
        required_overlap["expected_minute_completeness"].min() < 0.999
        or required_overlap["matched_timestamp_share"].min() < 0.999
    ):
        return "NOT_QUALIFIED"

    outside_roll = cross_source[
        cross_source["window_id"].isin(OUTSIDE_ROLL_WINDOW_IDS)
    ]
    if len(outside_roll) != len(OUTSIDE_ROLL_WINDOW_IDS):
        return "STRUCTURE_UNRESOLVED"
    outside_roll_close_share = pd.to_numeric(
        outside_roll["close_within_one_tick_share"],
        errors="coerce",
    )
    if not np.isfinite(outside_roll_close_share.to_numpy(dtype=float)).all():
        return "STRUCTURE_UNRESOLVED"
    if outside_roll_close_share.min() < 0.995:
        return "NOT_QUALIFIED"

    # Contract, roll and adjustment methodology remains unresolved.
    return "SUPPLEMENTARY_ONLY"
