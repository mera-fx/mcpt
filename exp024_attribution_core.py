from __future__ import annotations

from datetime import date, datetime
import hashlib
import json
import math
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd

from exp024_preregistration import (
    ATTRIBUTION_CATEGORIES,
    CANDIDATE_IDS,
)


RESEARCH_TIMEZONE = "America/New_York"
PRIMARY_REPRESENTATION = "BACKWARD_ADJUSTED"
SECONDARY_REPRESENTATION = "UNADJUSTED"
SOURCE_IDS = (
    "QUANTOWER_REFERENCE",
    PRIMARY_REPRESENTATION,
    SECONDARY_REPRESENTATION,
)
NQ_TICK_SIZE_POINTS = 0.25

CANDIDATE_RULES: dict[str, dict[str, Any]] = {
    "gap_fade_0p50_1r": {
        "setup_kind": "gap_fade",
        "threshold": 0.50,
    },
    "premarket_continuation_0p50_time": {
        "setup_kind": "premarket_continuation",
        "threshold": 0.50,
    },
    "premarket_continuation_0p75_time": {
        "setup_kind": "premarket_continuation",
        "threshold": 0.75,
    },
}

DECISION_COMPONENTS = (
    "eligibility",
    "threshold_passes",
    "context_direction",
    "first_cash_bar_confirmation",
    "entry_risk_positive",
)

SINGLE_COMPONENT_CATEGORIES = {
    "eligibility": "ELIGIBILITY_DIFFERENCE",
    "threshold_passes": "NORMALIZED_CONTEXT_THRESHOLD_CROSSING",
    "context_direction": "CONTEXT_DIRECTION_DIFFERENCE",
    (
        "first_cash_bar_confirmation"
    ): "FIRST_CASH_BAR_CONFIRMATION_DIFFERENCE",
    "entry_risk_positive": "ENTRY_RISK_VALIDITY_DIFFERENCE",
}

PRICE_FEATURES_BY_KIND = {
    "gap_fade": (
        "previous_cash_close",
        "previous_cash_high",
        "previous_cash_low",
        "previous_cash_range",
        "current_cash_open",
        "gap_move",
        "first_cash_bar_open",
        "first_cash_bar_close",
        "entry_0935_open",
        "entry_risk_points",
    ),
    "premarket_continuation": (
        "premarket_open",
        "premarket_last_close",
        "premarket_high",
        "premarket_low",
        "premarket_range",
        "premarket_move",
        "first_cash_bar_open",
        "first_cash_bar_close",
        "entry_0935_open",
        "entry_risk_points",
    ),
}

EXPECTED_MISMATCH_COUNTS = {
    "gap_fade_0p50_1r": 48,
    "premarket_continuation_0p50_time": 2,
    "premarket_continuation_0p75_time": 1,
}


def _normalise_scalar(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (pd.Timestamp, datetime, date)):
        return value.isoformat()
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer, int)) and not isinstance(value, bool):
        return int(value)
    if isinstance(value, (np.floating, float)):
        numeric = float(value)
        if math.isnan(numeric):
            return None
        if math.isinf(numeric):
            return "Infinity" if numeric > 0 else "-Infinity"
        return numeric
    if pd.isna(value):
        return None
    return value


def canonical_object_sha256(value: Any) -> str:
    def normalise(item: Any) -> Any:
        if isinstance(item, Mapping):
            return {
                str(key): normalise(current)
                for key, current in item.items()
            }
        if isinstance(item, (list, tuple)):
            return [normalise(current) for current in item]
        return _normalise_scalar(item)

    encoded = json.dumps(
        normalise(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def canonical_dataframe_sha256(frame: pd.DataFrame) -> str:
    return canonical_object_sha256(frame.to_dict(orient="records"))


def _strict_bool_series(series: pd.Series, *, name: str) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series.astype(bool)
    normalised = series.astype(str).str.strip().str.lower()
    if not normalised.isin({"true", "false"}).all():
        raise ValueError(f"{name} contains a non-boolean value.")
    return normalised.eq("true")


def validate_candidate_rules() -> None:
    if tuple(CANDIDATE_RULES) != CANDIDATE_IDS:
        raise ValueError("EXP-024 candidate order or identity changed.")
    expected = {
        "gap_fade_0p50_1r": ("gap_fade", 0.50),
        "premarket_continuation_0p50_time": (
            "premarket_continuation",
            0.50,
        ),
        "premarket_continuation_0p75_time": (
            "premarket_continuation",
            0.75,
        ),
    }
    actual = {
        candidate_id: (
            str(rule["setup_kind"]),
            float(rule["threshold"]),
        )
        for candidate_id, rule in CANDIDATE_RULES.items()
    }
    if actual != expected:
        raise ValueError("EXP-024 candidate rule changed.")
    if set(SINGLE_COMPONENT_CATEGORIES.values()).difference(
        ATTRIBUTION_CATEGORIES
    ):
        raise ValueError("EXP-024 attribution category map changed.")


def select_frozen_mismatch_population(
    trade_alignment: pd.DataFrame,
    *,
    require_production_count: bool = True,
) -> pd.DataFrame:
    """Select the locked EXP-023 primary mismatch population.

    Only decision fields are retained. Profit, return and exit fields in the
    frozen alignment are deliberately not propagated into EXP-024.
    """

    required = {
        "representation_id",
        "candidate_id",
        "session_date",
        "eligible",
        "reference_trade_flag",
        "transfer_trade_flag",
        "reference_direction",
        "transfer_direction",
        "trade_indicator_and_direction_match",
    }
    missing = sorted(required.difference(trade_alignment.columns))
    if missing:
        raise ValueError(
            "EXP-024 frozen alignment is missing: " + ", ".join(missing)
        )

    local = trade_alignment.loc[:, sorted(required)].copy()
    for column in (
        "eligible",
        "reference_trade_flag",
        "transfer_trade_flag",
        "trade_indicator_and_direction_match",
    ):
        local[column] = _strict_bool_series(
            local[column],
            name=column,
        )
    local["representation_id"] = local["representation_id"].astype(str)
    local["candidate_id"] = local["candidate_id"].astype(str)
    local["session_date"] = local["session_date"].astype(str)
    local["reference_direction"] = (
        local["reference_direction"].fillna("").astype(str).str.lower()
    )
    local["transfer_direction"] = (
        local["transfer_direction"].fillna("").astype(str).str.lower()
    )

    result = local.loc[
        local["representation_id"].eq(PRIMARY_REPRESENTATION)
        & ~local["trade_indicator_and_direction_match"]
    ].copy()
    result = result.sort_values(
        ["candidate_id", "session_date"],
        kind="stable",
    ).reset_index(drop=True)

    if result.duplicated(["candidate_id", "session_date"]).any():
        raise ValueError("EXP-024 mismatch keys are not unique.")
    if not set(result["candidate_id"]).issubset(CANDIDATE_IDS):
        raise ValueError("EXP-024 mismatch population has another candidate.")
    if not result["session_date"].between(
        "2020-01-03",
        "2025-12-31",
    ).all():
        raise ValueError("EXP-024 mismatch population left the overlap.")

    if require_production_count:
        counts = (
            result.groupby("candidate_id", sort=False)
            .size()
            .to_dict()
        )
        if len(result) != 51 or counts != EXPECTED_MISMATCH_COUNTS:
            raise ValueError(
                "EXP-024 mismatch population does not match the locked "
                "51-row candidate counts."
            )
        if result["session_date"].nunique() != 51:
            raise ValueError(
                "EXP-024 production population must have 51 unique dates."
            )
        relationship_counts = {
            "reference_only": int(
                (
                    result["reference_trade_flag"]
                    & ~result["transfer_trade_flag"]
                ).sum()
            ),
            "transfer_only": int(
                (
                    ~result["reference_trade_flag"]
                    & result["transfer_trade_flag"]
                ).sum()
            ),
            "direction_mismatch": int(
                (
                    result["reference_trade_flag"]
                    & result["transfer_trade_flag"]
                    & (
                        result["reference_direction"]
                        != result["transfer_direction"]
                    )
                ).sum()
            ),
        }
        if relationship_counts != {
            "reference_only": 5,
            "transfer_only": 46,
            "direction_mismatch": 0,
        }:
            raise ValueError(
                "EXP-024 frozen mismatch relationship counts changed."
            )

    return result


def normalise_restricted_rows(
    frame: pd.DataFrame,
    *,
    source_id: str,
    timestamp_column: str,
    window: str,
) -> pd.DataFrame:
    if source_id not in SOURCE_IDS:
        raise ValueError(f"Unknown EXP-024 source: {source_id}.")
    if timestamp_column not in frame.columns:
        raise ValueError(
            f"EXP-024 frame is missing timestamp column {timestamp_column}."
        )
    if "open" not in frame.columns:
        raise ValueError("EXP-024 restricted frame is missing open.")

    local = frame.copy()
    local = local.rename(columns={timestamp_column: "timestamp_utc"})
    local["timestamp_utc"] = pd.to_datetime(
        local["timestamp_utc"],
        utc=True,
        errors="raise",
    )
    if local["timestamp_utc"].duplicated().any():
        raise ValueError("EXP-024 restricted timestamps are not unique.")
    local = local.sort_values("timestamp_utc", kind="stable").reset_index(
        drop=True
    )
    timestamp_local = local["timestamp_utc"].dt.tz_convert(
        RESEARCH_TIMEZONE
    )
    if (
        (timestamp_local.dt.second != 0)
        | (timestamp_local.dt.microsecond != 0)
    ).any():
        raise ValueError("EXP-024 bars must start on exact minutes.")
    local["session_date"] = timestamp_local.dt.strftime("%Y-%m-%d")
    local["local_minute"] = (
        timestamp_local.dt.hour.astype(int) * 60
        + timestamp_local.dt.minute.astype(int)
    )
    local["source_id"] = source_id
    local["window"] = window

    numeric = [
        column
        for column in ("open", "high", "low", "close")
        if column in local.columns
    ]
    for column in numeric:
        local[column] = pd.to_numeric(local[column], errors="raise")
    if numeric and not np.isfinite(
        local.loc[:, numeric].to_numpy(dtype=float)
    ).all():
        raise ValueError("EXP-024 restricted prices are nonfinite.")
    if {"open", "high", "low", "close"}.issubset(local.columns):
        if (
            (
                local["high"]
                < local[["open", "close", "low"]].max(axis=1)
            )
            | (
                local["low"]
                > local[["open", "close", "high"]].min(axis=1)
            )
        ).any():
            raise ValueError("EXP-024 restricted OHLC geometry is invalid.")
    return local


def _direction(value: float) -> int:
    if not np.isfinite(value):
        return 0
    return 1 if value > 0 else -1 if value < 0 else 0


def _optional_float(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None
    numeric = float(value)
    return numeric if np.isfinite(numeric) else None


def _window_ohlc(
    frame: pd.DataFrame,
    *,
    start_minute: int,
    end_minute: int,
) -> dict[str, Any] | None:
    required = {
        "timestamp_utc",
        "local_minute",
        "open",
        "high",
        "low",
        "close",
    }
    if frame.empty:
        return None
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(
            "EXP-024 OHLC window is missing: " + ", ".join(missing)
        )
    rows = frame.loc[
        frame["local_minute"].between(
            start_minute,
            end_minute - 1,
        )
    ].sort_values("timestamp_utc", kind="stable")
    if rows.empty:
        return None
    return {
        "open": float(rows.iloc[0]["open"]),
        "high": float(rows["high"].max()),
        "low": float(rows["low"].min()),
        "close": float(rows.iloc[-1]["close"]),
        "row_count": int(len(rows)),
        "five_minute_bin_count": int(
            (rows["local_minute"].astype(int) // 5).nunique()
        ),
    }


def build_candidate_features(
    *,
    source_id: str,
    candidate_id: str,
    session_date: str,
    eligible: bool,
    current_rows: pd.DataFrame,
    entry_rows: pd.DataFrame,
    previous_cash_rows: pd.DataFrame | None = None,
) -> dict[str, Any]:
    """Rebuild one source's locked entry-decision vector.

    The function has no exit, target, return, P&L or performance inputs.
    """

    validate_candidate_rules()
    if source_id not in SOURCE_IDS:
        raise ValueError(f"Unknown EXP-024 source: {source_id}.")
    if candidate_id not in CANDIDATE_RULES:
        raise ValueError(f"Unknown EXP-024 candidate: {candidate_id}.")

    rule = CANDIDATE_RULES[candidate_id]
    setup_kind = str(rule["setup_kind"])
    threshold = float(rule["threshold"])

    current = current_rows.loc[
        current_rows["session_date"].astype(str).eq(session_date)
    ].copy()
    entry = entry_rows.loc[
        entry_rows["session_date"].astype(str).eq(session_date)
    ].copy()
    if len(entry) > 1:
        raise ValueError(
            f"EXP-024 has duplicate 09:35 opens for {session_date}."
        )

    first_cash = _window_ohlc(
        current,
        start_minute=9 * 60 + 30,
        end_minute=9 * 60 + 35,
    )
    if eligible and (first_cash is None or len(entry) != 1):
        raise ValueError(
            "EXP-024 eligible source is missing a locked entry window "
            f"for {source_id} {candidate_id} {session_date}."
        )

    first_open = first_cash["open"] if first_cash else None
    first_close = first_cash["close"] if first_cash else None
    first_high = first_cash["high"] if first_cash else None
    first_low = first_cash["low"] if first_cash else None
    first_direction = (
        _direction(float(first_close) - float(first_open))
        if first_cash
        else 0
    )
    entry_open = float(entry.iloc[0]["open"]) if len(entry) == 1 else None

    record: dict[str, Any] = {
        "source_id": source_id,
        "candidate_id": candidate_id,
        "session_date": session_date,
        "setup_kind": setup_kind,
        "threshold": threshold,
        "eligibility": bool(eligible),
        "first_cash_bar_open": first_open,
        "first_cash_bar_high": first_high,
        "first_cash_bar_low": first_low,
        "first_cash_bar_close": first_close,
        "first_cash_bar_direction": first_direction,
        "entry_0935_open": entry_open,
        "context_direction": 0,
        "threshold_margin": None,
        "threshold_passes": False,
        "first_cash_bar_confirmation": False,
        "entry_risk_points": None,
        "entry_risk_positive": False,
        "setup_passes": False,
    }

    if setup_kind == "gap_fade":
        prior = (
            pd.DataFrame()
            if previous_cash_rows is None
            else previous_cash_rows.copy()
        )
        previous_cash = _window_ohlc(
            prior,
            start_minute=9 * 60 + 30,
            end_minute=16 * 60,
        )
        if eligible and previous_cash is None:
            raise ValueError(
                "EXP-024 eligible gap source is missing its previous "
                f"cash window for {source_id} {session_date}."
            )
        previous_close = (
            previous_cash["close"] if previous_cash else None
        )
        previous_high = (
            previous_cash["high"] if previous_cash else None
        )
        previous_low = previous_cash["low"] if previous_cash else None
        previous_range = (
            float(previous_high) - float(previous_low)
            if previous_cash
            else None
        )
        gap_move = (
            float(first_open) - float(previous_close)
            if first_cash and previous_cash
            else None
        )
        gap_direction = (
            _direction(float(gap_move)) if gap_move is not None else 0
        )
        context_value = (
            abs(float(gap_move)) / float(previous_range)
            if (
                gap_move is not None
                and previous_range is not None
                and previous_range > 0
            )
            else None
        )
        decision_direction = -gap_direction
        record.update(
            {
                "previous_cash_close": previous_close,
                "previous_cash_high": previous_high,
                "previous_cash_low": previous_low,
                "previous_cash_range": previous_range,
                "current_cash_open": first_open,
                "gap_move": gap_move,
                "gap_direction": gap_direction,
                "normalized_gap": context_value,
                "fade_direction": decision_direction,
                "context_direction": gap_direction,
            }
        )
    else:
        premarket = _window_ohlc(
            current,
            start_minute=8 * 60,
            end_minute=9 * 60 + 30,
        )
        if eligible and premarket is None:
            raise ValueError(
                "EXP-024 eligible premarket source is missing its "
                f"premarket window for {source_id} {session_date}."
            )
        premarket_open = premarket["open"] if premarket else None
        premarket_close = premarket["close"] if premarket else None
        premarket_high = premarket["high"] if premarket else None
        premarket_low = premarket["low"] if premarket else None
        premarket_range = (
            float(premarket_high) - float(premarket_low)
            if premarket
            else None
        )
        premarket_move = (
            float(premarket_close) - float(premarket_open)
            if premarket
            else None
        )
        premarket_direction = (
            _direction(float(premarket_move))
            if premarket_move is not None
            else 0
        )
        context_value = (
            abs(float(premarket_move)) / float(premarket_range)
            if (
                premarket_move is not None
                and premarket_range is not None
                and premarket_range > 0
            )
            else None
        )
        decision_direction = premarket_direction
        record.update(
            {
                "premarket_open": premarket_open,
                "premarket_last_close": premarket_close,
                "premarket_high": premarket_high,
                "premarket_low": premarket_low,
                "premarket_range": premarket_range,
                "premarket_move": premarket_move,
                "premarket_direction": premarket_direction,
                "normalized_premarket_move": context_value,
                "continuation_direction": decision_direction,
                "context_direction": premarket_direction,
            }
        )

    threshold_margin = (
        float(context_value) - threshold
        if context_value is not None
        else None
    )
    threshold_passes = (
        context_value is not None
        and np.isfinite(context_value)
        and context_value >= threshold
    )
    confirmation = (
        decision_direction != 0
        and first_direction == decision_direction
    )
    risk_points = (
        decision_direction
        * (
            float(entry_open)
            - (
                float(first_low)
                if decision_direction == 1
                else float(first_high)
            )
        )
        if (
            decision_direction != 0
            and entry_open is not None
            and first_cash is not None
        )
        else None
    )
    risk_positive = (
        risk_points is not None
        and np.isfinite(risk_points)
        and risk_points > 0
    )
    setup_passes = bool(
        eligible
        and threshold_passes
        and decision_direction != 0
        and confirmation
        and risk_positive
    )
    record.update(
        {
            "threshold_margin": threshold_margin,
            "threshold_passes": bool(threshold_passes),
            "first_cash_bar_confirmation": bool(confirmation),
            "entry_risk_points": risk_points,
            "entry_risk_positive": bool(risk_positive),
            "setup_passes": setup_passes,
            "decision_direction": (
                "long"
                if decision_direction == 1
                else "short"
                if decision_direction == -1
                else ""
            ),
        }
    )
    return record


def _component_difference(
    reference: Mapping[str, Any],
    transfer: Mapping[str, Any],
    component: str,
) -> bool:
    left = reference.get(component)
    right = transfer.get(component)
    if component == "context_direction":
        return int(left or 0) != int(right or 0)
    return bool(left) != bool(right)


def attribution_category(
    reference: Mapping[str, Any],
    transfer: Mapping[str, Any],
) -> tuple[tuple[str, ...], str]:
    differing = tuple(
        component
        for component in DECISION_COMPONENTS
        if _component_difference(
            reference,
            transfer,
            component,
        )
    )
    if not differing:
        category = "UNRESOLVED_WITH_LOCKED_FEATURES"
    elif len(differing) > 1:
        category = "MULTIPLE_DECISION_COMPONENT_DIFFERENCES"
    else:
        category = SINGLE_COMPONENT_CATEGORIES[differing[0]]
    if category not in ATTRIBUTION_CATEGORIES:
        raise ValueError("EXP-024 produced an unlocked category.")
    return differing, category


def build_attribution(
    mismatch_population: pd.DataFrame,
    feature_comparison: pd.DataFrame,
) -> pd.DataFrame:
    required_features = {
        "source_id",
        "candidate_id",
        "session_date",
        "setup_passes",
        "decision_direction",
        *DECISION_COMPONENTS,
    }
    missing = sorted(required_features.difference(feature_comparison.columns))
    if missing:
        raise ValueError(
            "EXP-024 feature comparison is missing: " + ", ".join(missing)
        )
    indexed = feature_comparison.set_index(
        ["source_id", "candidate_id", "session_date"],
    )
    if not indexed.index.is_unique:
        raise ValueError("EXP-024 feature comparison keys are not unique.")
    rows: list[dict[str, Any]] = []
    for mismatch in mismatch_population.itertuples(index=False):
        key = (str(mismatch.candidate_id), str(mismatch.session_date))
        try:
            reference = indexed.loc[("QUANTOWER_REFERENCE", *key)]
            transfer = indexed.loc[(PRIMARY_REPRESENTATION, *key)]
        except KeyError as exc:
            raise ValueError(
                f"EXP-024 feature row missing for {key}."
            ) from exc

        reference_setup = bool(reference["setup_passes"])
        transfer_setup = bool(transfer["setup_passes"])
        reference_direction = str(reference["decision_direction"])
        transfer_direction = str(transfer["decision_direction"])
        reference_matches = (
            reference_setup == bool(mismatch.reference_trade_flag)
            and (
                not reference_setup
                or reference_direction
                == str(mismatch.reference_direction)
            )
        )
        transfer_matches = (
            transfer_setup == bool(mismatch.transfer_trade_flag)
            and (
                not transfer_setup
                or transfer_direction
                == str(mismatch.transfer_direction)
            )
        )
        differing, category = attribution_category(reference, transfer)
        rows.append(
            {
                "candidate_id": key[0],
                "session_date": key[1],
                "frozen_reference_trade_flag": bool(
                    mismatch.reference_trade_flag
                ),
                "frozen_transfer_trade_flag": bool(
                    mismatch.transfer_trade_flag
                ),
                "frozen_reference_direction": str(
                    mismatch.reference_direction
                ),
                "frozen_transfer_direction": str(
                    mismatch.transfer_direction
                ),
                "reference_rebuilt_setup_passes": reference_setup,
                "transfer_rebuilt_setup_passes": transfer_setup,
                "reference_rebuilt_direction": reference_direction,
                "transfer_rebuilt_direction": transfer_direction,
                "reference_rebuild_matches_frozen": reference_matches,
                "transfer_rebuild_matches_frozen": transfer_matches,
                "differing_decision_components": "|".join(differing),
                "differing_decision_component_count": len(differing),
                "primary_attribution_category": category,
                "roll_context_used_as_causal_attribution": False,
            }
        )
    result = pd.DataFrame(rows).sort_values(
        ["candidate_id", "session_date"],
        kind="stable",
    ).reset_index(drop=True)
    if len(result) != len(mismatch_population):
        raise ValueError("EXP-024 attribution lost a mismatch row.")
    if result.duplicated(["candidate_id", "session_date"]).any():
        raise ValueError("EXP-024 attribution keys are not unique.")
    return result


def raw_component_differences(
    feature_comparison: pd.DataFrame,
) -> pd.DataFrame:
    indexed = feature_comparison.set_index(
        ["source_id", "candidate_id", "session_date"],
    )
    if not indexed.index.is_unique:
        raise ValueError("EXP-024 feature comparison keys are not unique.")
    pairs = (
        ("QUANTOWER_REFERENCE", PRIMARY_REPRESENTATION),
        ("QUANTOWER_REFERENCE", SECONDARY_REPRESENTATION),
        (PRIMARY_REPRESENTATION, SECONDARY_REPRESENTATION),
    )
    rows: list[dict[str, Any]] = []
    keys = sorted(
        {
            (str(candidate), str(session))
            for _, candidate, session in indexed.index
        }
    )
    for candidate_id, session_date in keys:
        setup_kind = str(CANDIDATE_RULES[candidate_id]["setup_kind"])
        for left_source, right_source in pairs:
            left = indexed.loc[
                (left_source, candidate_id, session_date)
            ]
            right = indexed.loc[
                (right_source, candidate_id, session_date)
            ]
            for feature_name in PRICE_FEATURES_BY_KIND[setup_kind]:
                left_value = _optional_float(left.get(feature_name))
                right_value = _optional_float(right.get(feature_name))
                difference_points = (
                    right_value - left_value
                    if left_value is not None and right_value is not None
                    else None
                )
                rows.append(
                    {
                        "candidate_id": candidate_id,
                        "session_date": session_date,
                        "feature_name": feature_name,
                        "left_source": left_source,
                        "right_source": right_source,
                        "left_value_points": left_value,
                        "right_value_points": right_value,
                        "difference_points": difference_points,
                        "difference_nq_ticks": (
                            difference_points / NQ_TICK_SIZE_POINTS
                            if difference_points is not None
                            else None
                        ),
                    }
                )
    return pd.DataFrame(rows).sort_values(
        [
            "candidate_id",
            "session_date",
            "feature_name",
            "left_source",
            "right_source",
        ],
        kind="stable",
    ).reset_index(drop=True)


def aggregate_observed_ohlc(frame: pd.DataFrame) -> pd.DataFrame:
    required = {
        "timestamp_utc",
        "session_date",
        "open",
        "high",
        "low",
        "close",
    }
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(
            "EXP-024 aggregation input is missing: " + ", ".join(missing)
        )
    if frame.empty:
        return pd.DataFrame(
            columns=[
                "session_date",
                "timestamp_utc",
                "open",
                "high",
                "low",
                "close",
                "observation_count",
            ]
        )
    local = frame.sort_values("timestamp_utc", kind="stable").copy()
    local["five_minute_timestamp_utc"] = local[
        "timestamp_utc"
    ].dt.floor("5min")
    result = (
        local.groupby(
            ["session_date", "five_minute_timestamp_utc"],
            sort=True,
            as_index=False,
        )
        .agg(
            open=("open", "first"),
            high=("high", "max"),
            low=("low", "min"),
            close=("close", "last"),
            observation_count=("timestamp_utc", "size"),
        )
        .rename(
            columns={
                "five_minute_timestamp_utc": "timestamp_utc",
            }
        )
    )
    return result


def compare_quantower_aggregation(
    one_minute: pd.DataFrame,
    frozen_five_minute: pd.DataFrame,
) -> pd.DataFrame:
    rebuilt = aggregate_observed_ohlc(one_minute)
    required = {
        "timestamp_utc",
        "session_date",
        "open",
        "high",
        "low",
        "close",
    }
    missing = sorted(required.difference(frozen_five_minute.columns))
    if missing:
        raise ValueError(
            "EXP-024 frozen five-minute frame is missing: "
            + ", ".join(missing)
        )
    frozen = frozen_five_minute.loc[:, sorted(required)].copy()
    merged = rebuilt.merge(
        frozen,
        on=["session_date", "timestamp_utc"],
        how="outer",
        suffixes=("_rebuilt_1m", "_frozen_5m"),
        indicator=True,
        validate="one_to_one",
    )
    for column in ("open", "high", "low", "close"):
        merged[f"{column}_matches"] = np.isclose(
            pd.to_numeric(
                merged[f"{column}_rebuilt_1m"],
                errors="coerce",
            ),
            pd.to_numeric(
                merged[f"{column}_frozen_5m"],
                errors="coerce",
            ),
            rtol=0.0,
            atol=1e-9,
            equal_nan=False,
        )
    match_columns = [
        f"{column}_matches"
        for column in ("open", "high", "low", "close")
    ]
    merged["all_ohlc_match"] = (
        merged["_merge"].eq("both")
        & merged[match_columns].all(axis=1)
    )
    return merged.sort_values(
        ["session_date", "timestamp_utc"],
        kind="stable",
    ).reset_index(drop=True)


def final_classification(
    hard_checks: Mapping[str, bool],
    *,
    unresolved_count: int,
) -> str:
    if not hard_checks or not all(bool(value) for value in hard_checks.values()):
        return "ATTRIBUTION_DIAGNOSTIC_NOT_QUALIFIED"
    if unresolved_count:
        return "ATTRIBUTION_COMPLETE_WITH_UNRESOLVED_CASES"
    return "ATTRIBUTION_COMPLETE_WITH_IDENTIFIED_COMPONENTS"


def validate_feature_rows(
    frame: pd.DataFrame,
    mismatch_population: pd.DataFrame,
) -> None:
    expected = {
        (source_id, str(row.candidate_id), str(row.session_date))
        for source_id in SOURCE_IDS
        for row in mismatch_population.itertuples(index=False)
    }
    actual = {
        (str(row.source_id), str(row.candidate_id), str(row.session_date))
        for row in frame.itertuples(index=False)
    }
    if actual != expected or len(frame) != len(expected):
        raise ValueError(
            "EXP-024 feature comparison must contain exactly three "
            "source rows per frozen mismatch."
        )
