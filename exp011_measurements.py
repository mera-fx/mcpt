from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pandas as pd

from exp011_sizing import Exp011SizedResult, SIZING_IDS


SIGNAL_IDS = (
    "opening_drive_0p5_time",
    "opening_drive_0p5_1p5r",
)


def build_exp011_measurement_table(
    results: Mapping[tuple[str, str], Exp011SizedResult],
) -> pd.DataFrame:
    expected = {
        (signal_id, sizing_id)
        for signal_id in SIGNAL_IDS
        for sizing_id in SIZING_IDS
    }
    actual = set(results)
    if actual != expected:
        missing = sorted(expected.difference(actual))
        extra = sorted(actual.difference(expected))
        raise ValueError(
            f"EXP-011 requires all six rows; missing={missing}, extra={extra}."
        )

    records: list[dict[str, Any]] = []
    for signal_id in SIGNAL_IDS:
        for sizing_id in SIZING_IDS:
            records.append(dict(results[(signal_id, sizing_id)].summary))
    table = pd.DataFrame.from_records(records)
    table["measurement_role"] = table["signal_candidate_id"].map(
        {
            "opening_drive_0p5_time": "PRIMARY_SIGNAL",
            "opening_drive_0p5_1p5r": "USER_REFERENCE_SIGNAL",
        }
    )
    table["automatic_winner"] = False
    table["composite_score"] = pd.NA
    table["pass_fail_decision"] = "NOT_APPLICABLE"
    return table


def build_exp011_annual_table(
    results: Mapping[tuple[str, str], Exp011SizedResult],
) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    for (signal_id, sizing_id), result in results.items():
        for row in result.yearly_results.to_dict(orient="records"):
            records.append(
                {
                    "signal_candidate_id": signal_id,
                    "sizing_id": sizing_id,
                    "symbol": result.symbol,
                    **row,
                }
            )
    return pd.DataFrame.from_records(records)


def build_exp011_monthly_table(
    results: Mapping[tuple[str, str], Exp011SizedResult],
) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    for (signal_id, sizing_id), result in results.items():
        for row in result.monthly_results.to_dict(orient="records"):
            records.append(
                {
                    "signal_candidate_id": signal_id,
                    "sizing_id": sizing_id,
                    "symbol": result.symbol,
                    **row,
                }
            )
    return pd.DataFrame.from_records(records)
