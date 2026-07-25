from __future__ import annotations

from datetime import date, datetime, time, timedelta
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd


NEW_YORK = ZoneInfo("America/New_York")

EXPECTED_CONTRACT_COUNT = 66
EXPECTED_TRANSITION_COUNT = 65
EXPECTED_RECORD_COUNT = 6_276_486

PRIMARY_METHOD = (
    "VOLUME_CROSSOVER_2_SESSION_"
    "WITH_CALENDAR_FALLBACK"
)
CALENDAR_METHOD = (
    "CALENDAR_THURSDAY_8_DAYS_BEFORE_EXPIRY"
)

KNOWN_PROVIDER_WARNING_CONTRACTS = frozenset(
    {
        "NQM14",
        "NQZ14",
        "NQH15",
        "NQZ17",
        "NQZ18",
        "NQH19",
        "NQM19",
        "NQH20",
        "NQU20",
        "NQZ21",
        "NQH22",
        "NQU25",
        "NQZ25",
        "NQH26",
        "NQM26",
        "NQU26",
    }
)

PRICE_COLUMNS = (
    "open",
    "high",
    "low",
    "close",
)

SERIES_COLUMNS = (
    "ts_event",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "instrument_id",
    "source_contract",
    "roll_method",
    "trading_date",
    "adjustment_points",
)

ROLL_LEDGER_FIELDS = (
    "method",
    "transition_sequence",
    "outgoing_contract",
    "incoming_contract",
    "outgoing_expiration",
    "calendar_target_trading_date",
    "roll_trading_date",
    "roll_boundary_utc",
    "trigger_type",
    "trigger_session_1",
    "trigger_session_2",
    "outgoing_volume_session_1",
    "incoming_volume_session_1",
    "outgoing_volume_session_2",
    "incoming_volume_session_2",
    "calendar_fallback",
    "provider_warning_exclusion_scope",
    "provider_warning_contracts",
    "excluded_common_sessions",
    "common_overlap_sessions",
    "reference_timestamp_utc",
    "outgoing_reference_close",
    "incoming_reference_close",
    "roll_difference_points",
)

CONTRIBUTION_FIELDS = (
    "method",
    "source_contract",
    "row_count",
    "first_timestamp_utc",
    "last_timestamp_utc",
    "first_trading_date",
    "last_trading_date",
    "backward_adjustment_points",
)

METHOD_COMPARISON_FIELDS = (
    "method",
    "row_count",
    "first_timestamp_utc",
    "last_timestamp_utc",
    "calendar_fallback_count",
    "provider_warning_transition_count",
    "missing_minute_run_count",
    "largest_missing_minute_run",
    "total_absolute_roll_difference_points",
    "unadjusted_semantic_sha256",
    "adjusted_semantic_sha256",
)


def canonical_json_bytes(payload: Any) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,
    ).encode("utf-8")


def ensure_utc_index(values: Any) -> pd.DatetimeIndex:
    timestamps = pd.DatetimeIndex(
        pd.to_datetime(
            values,
            utc=True,
            errors="raise",
        )
    )

    if timestamps.tz is None:
        return timestamps.tz_localize("UTC")

    return timestamps.tz_convert("UTC")


def timestamp_ns_values(
    timestamps: pd.DatetimeIndex,
) -> np.ndarray:
    try:
        return timestamps.as_unit("ns").asi8
    except (AttributeError, TypeError):
        return (
            timestamps.to_numpy(
                dtype="datetime64[ns]"
            )
            .astype("int64", copy=False)
        )


def assign_trading_dates(values: Any) -> pd.Index:
    timestamps = ensure_utc_index(values)
    local = timestamps.tz_convert(NEW_YORK)
    shifted = local + pd.Timedelta(hours=6)

    return pd.Index(
        shifted.date,
        dtype="object",
        name="trading_date",
    )


def session_open_utc(
    trading_date: date,
) -> pd.Timestamp:
    previous_date = trading_date - timedelta(days=1)
    local_open = datetime.combine(
        previous_date,
        time(18, 0),
        tzinfo=NEW_YORK,
    )

    return pd.Timestamp(local_open).tz_convert("UTC")


def normalise_contract_frame(
    frame: pd.DataFrame,
    *,
    canonical_symbol: str,
) -> pd.DataFrame:
    required = (
        "instrument_id",
        "open",
        "high",
        "low",
        "close",
        "volume",
    )

    missing = [
        column
        for column in required
        if column not in frame.columns
    ]

    if missing:
        raise ValueError(
            "Missing required DBN columns: "
            + ", ".join(missing)
        )

    if isinstance(frame.index, pd.DatetimeIndex):
        timestamps = ensure_utc_index(frame.index)
    elif "ts_event" in frame.columns:
        timestamps = ensure_utc_index(frame["ts_event"])
    else:
        raise ValueError(
            "DBN frame has no ts_event timestamp."
        )

    result = pd.DataFrame(
        {
            "ts_event": timestamps,
            "open": pd.to_numeric(
                frame["open"],
                errors="raise",
            ).to_numpy(dtype=float),
            "high": pd.to_numeric(
                frame["high"],
                errors="raise",
            ).to_numpy(dtype=float),
            "low": pd.to_numeric(
                frame["low"],
                errors="raise",
            ).to_numpy(dtype=float),
            "close": pd.to_numeric(
                frame["close"],
                errors="raise",
            ).to_numpy(dtype=float),
            "volume": pd.to_numeric(
                frame["volume"],
                errors="raise",
            ).to_numpy(dtype=np.int64),
            "instrument_id": pd.to_numeric(
                frame["instrument_id"],
                errors="raise",
            ).to_numpy(dtype=np.int64),
        }
    )

    result["source_contract"] = canonical_symbol
    result["trading_date"] = assign_trading_dates(
        result["ts_event"]
    )

    result = (
        result.sort_values(
            "ts_event",
            kind="mergesort",
        )
        .reset_index(drop=True)
    )

    if result["ts_event"].duplicated().any():
        raise ValueError(
            f"Duplicate timestamps in {canonical_symbol}."
        )

    if not pd.DatetimeIndex(
        result["ts_event"]
    ).is_monotonic_increasing:
        raise ValueError(
            f"Non-monotonic timestamps in {canonical_symbol}."
        )

    return result


def daily_volume(frame: pd.DataFrame) -> pd.Series:
    result = frame.groupby(
        "trading_date",
        sort=True,
        observed=False,
    )["volume"].sum()

    result.index = pd.Index(
        result.index,
        dtype="object",
    )

    return result.astype("int64")


def common_trading_dates(
    outgoing_daily: pd.Series,
    incoming_daily: pd.Series,
) -> list[date]:
    return sorted(
        set(outgoing_daily.index).intersection(
            incoming_daily.index
        )
    )


def calendar_target_date(
    expiration: date,
) -> date:
    trigger = expiration - timedelta(days=8)

    if trigger.weekday() != 3:
        raise ValueError(
            "Locked calendar trigger is not Thursday."
        )

    return trigger + timedelta(days=1)


def select_calendar_roll_date(
    outgoing_daily: pd.Series,
    incoming_daily: pd.Series,
    *,
    expiration: date,
) -> date:
    target = calendar_target_date(expiration)

    candidates = [
        value
        for value in common_trading_dates(
            outgoing_daily,
            incoming_daily,
        )
        if value >= target
    ]

    if not candidates:
        raise ValueError(
            "No common trading session exists on or "
            "after the locked calendar target."
        )

    return candidates[0]


def conservative_warning_exclusions(
    outgoing_symbol: str,
    incoming_symbol: str,
    common_dates: Iterable[date],
) -> tuple[set[date], tuple[str, ...]]:
    warning_contracts = tuple(
        symbol
        for symbol in (
            outgoing_symbol,
            incoming_symbol,
        )
        if symbol in KNOWN_PROVIDER_WARNING_CONTRACTS
    )

    if not warning_contracts:
        return set(), ()

    return set(common_dates), warning_contracts


def select_volume_roll(
    outgoing_daily: pd.Series,
    incoming_daily: pd.Series,
    *,
    calendar_roll_date: date,
    excluded_dates: set[date] | None = None,
) -> dict[str, Any]:
    excluded = (
        set()
        if excluded_dates is None
        else set(excluded_dates)
    )

    common_dates = common_trading_dates(
        outgoing_daily,
        incoming_daily,
    )

    eligible = [
        value
        for value in common_dates
        if (
            value < calendar_roll_date
            and value not in excluded
        )
    ]

    streak: list[date] = []

    for value in eligible:
        outgoing_value = int(
            outgoing_daily.loc[value]
        )
        incoming_value = int(
            incoming_daily.loc[value]
        )

        if incoming_value > outgoing_value:
            streak.append(value)
            streak = streak[-2:]
        else:
            streak = []

        if len(streak) != 2:
            continue

        second = streak[-1]
        later_common = [
            candidate
            for candidate in common_dates
            if candidate > second
        ]

        if not later_common:
            break

        effective = later_common[0]

        if effective <= calendar_roll_date:
            first = streak[-2]
            return {
                "roll_trading_date": effective,
                "trigger_type": "VOLUME_CROSSOVER",
                "trigger_session_1": first,
                "trigger_session_2": second,
                "outgoing_volume_session_1": int(
                    outgoing_daily.loc[first]
                ),
                "incoming_volume_session_1": int(
                    incoming_daily.loc[first]
                ),
                "outgoing_volume_session_2": int(
                    outgoing_daily.loc[second]
                ),
                "incoming_volume_session_2": int(
                    incoming_daily.loc[second]
                ),
                "calendar_fallback": False,
            }

        break

    return {
        "roll_trading_date": calendar_roll_date,
        "trigger_type": "CALENDAR_FALLBACK",
        "trigger_session_1": None,
        "trigger_session_2": None,
        "outgoing_volume_session_1": None,
        "incoming_volume_session_1": None,
        "outgoing_volume_session_2": None,
        "incoming_volume_session_2": None,
        "calendar_fallback": True,
    }


def latest_shared_reference(
    outgoing: pd.DataFrame,
    incoming: pd.DataFrame,
    *,
    roll_trading_date: date,
) -> dict[str, Any]:
    boundary = session_open_utc(roll_trading_date)

    outgoing_close = outgoing.set_index(
        "ts_event"
    )["close"]
    incoming_close = incoming.set_index(
        "ts_event"
    )["close"]

    common = outgoing_close.index.intersection(
        incoming_close.index
    )
    eligible = common[common < boundary]

    if len(eligible) == 0:
        raise ValueError(
            "No shared timestamp exists before "
            "the roll boundary."
        )

    reference = eligible.max()
    outgoing_value = float(
        outgoing_close.loc[reference]
    )
    incoming_value = float(
        incoming_close.loc[reference]
    )

    return {
        "roll_boundary_utc": boundary.isoformat(),
        "reference_timestamp_utc": (
            reference.isoformat()
        ),
        "outgoing_reference_close": outgoing_value,
        "incoming_reference_close": incoming_value,
        "roll_difference_points": (
            incoming_value - outgoing_value
        ),
    }


def build_roll_ledgers(
    contract_frames: dict[str, pd.DataFrame],
    contract_plan: Iterable[
        tuple[str, str, str, str, str]
    ],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    plan = list(contract_plan)

    if len(plan) != EXPECTED_CONTRACT_COUNT:
        raise ValueError("Expected 66 contracts.")

    volume_rows: list[dict[str, Any]] = []
    calendar_rows: list[dict[str, Any]] = []

    for index in range(len(plan) - 1):
        outgoing_contract = plan[index]
        incoming_contract = plan[index + 1]
        outgoing_symbol = outgoing_contract[0]
        incoming_symbol = incoming_contract[0]
        outgoing = contract_frames[outgoing_symbol]
        incoming = contract_frames[incoming_symbol]
        outgoing_daily = daily_volume(outgoing)
        incoming_daily = daily_volume(incoming)
        common_dates = common_trading_dates(
            outgoing_daily,
            incoming_daily,
        )
        expiration = date.fromisoformat(
            outgoing_contract[4]
        )
        calendar_roll_date = select_calendar_roll_date(
            outgoing_daily,
            incoming_daily,
            expiration=expiration,
        )
        excluded_dates, warning_contracts = (
            conservative_warning_exclusions(
                outgoing_symbol,
                incoming_symbol,
                common_dates,
            )
        )
        volume_choice = select_volume_roll(
            outgoing_daily,
            incoming_daily,
            calendar_roll_date=calendar_roll_date,
            excluded_dates=excluded_dates,
        )

        base = {
            "transition_sequence": index + 1,
            "outgoing_contract": outgoing_symbol,
            "incoming_contract": incoming_symbol,
            "outgoing_expiration": expiration.isoformat(),
            "calendar_target_trading_date": (
                calendar_target_date(expiration).isoformat()
            ),
            "provider_warning_exclusion_scope": (
                "ENTIRE_CONTRACT_WINDOW"
                if warning_contracts
                else "NONE"
            ),
            "provider_warning_contracts": "|".join(
                warning_contracts
            ),
            "excluded_common_sessions": len(
                excluded_dates
            ),
            "common_overlap_sessions": len(common_dates),
        }

        volume_reference = latest_shared_reference(
            outgoing,
            incoming,
            roll_trading_date=volume_choice[
                "roll_trading_date"
            ],
        )

        volume_rows.append(
            {
                "method": PRIMARY_METHOD,
                **base,
                "roll_trading_date": volume_choice[
                    "roll_trading_date"
                ].isoformat(),
                "trigger_type": volume_choice[
                    "trigger_type"
                ],
                "trigger_session_1": (
                    volume_choice["trigger_session_1"].isoformat()
                    if volume_choice["trigger_session_1"]
                    else ""
                ),
                "trigger_session_2": (
                    volume_choice["trigger_session_2"].isoformat()
                    if volume_choice["trigger_session_2"]
                    else ""
                ),
                "outgoing_volume_session_1": (
                    volume_choice["outgoing_volume_session_1"]
                    if volume_choice["outgoing_volume_session_1"]
                    is not None
                    else ""
                ),
                "incoming_volume_session_1": (
                    volume_choice["incoming_volume_session_1"]
                    if volume_choice["incoming_volume_session_1"]
                    is not None
                    else ""
                ),
                "outgoing_volume_session_2": (
                    volume_choice["outgoing_volume_session_2"]
                    if volume_choice["outgoing_volume_session_2"]
                    is not None
                    else ""
                ),
                "incoming_volume_session_2": (
                    volume_choice["incoming_volume_session_2"]
                    if volume_choice["incoming_volume_session_2"]
                    is not None
                    else ""
                ),
                "calendar_fallback": volume_choice[
                    "calendar_fallback"
                ],
                **volume_reference,
            }
        )

        calendar_reference = latest_shared_reference(
            outgoing,
            incoming,
            roll_trading_date=calendar_roll_date,
        )

        calendar_rows.append(
            {
                "method": CALENDAR_METHOD,
                **base,
                "roll_trading_date": (
                    calendar_roll_date.isoformat()
                ),
                "trigger_type": "CALENDAR_BENCHMARK",
                "trigger_session_1": "",
                "trigger_session_2": "",
                "outgoing_volume_session_1": "",
                "incoming_volume_session_1": "",
                "outgoing_volume_session_2": "",
                "incoming_volume_session_2": "",
                "calendar_fallback": False,
                **calendar_reference,
            }
        )

    return volume_rows, calendar_rows


def method_boundaries(
    ledger: list[dict[str, Any]],
) -> list[date]:
    ordered = sorted(
        ledger,
        key=lambda row: int(
            row["transition_sequence"]
        ),
    )

    return [
        date.fromisoformat(row["roll_trading_date"])
        for row in ordered
    ]


def stitch_series(
    contract_frames: dict[str, pd.DataFrame],
    contract_plan: Iterable[
        tuple[str, str, str, str, str]
    ],
    ledger: list[dict[str, Any]],
    *,
    method: str,
) -> pd.DataFrame:
    plan = list(contract_plan)
    boundaries = method_boundaries(ledger)

    if len(boundaries) != len(plan) - 1:
        raise ValueError(
            "Roll ledger does not contain all transitions."
        )

    pieces: list[pd.DataFrame] = []

    for index, contract in enumerate(plan):
        symbol = contract[0]
        frame = contract_frames[symbol]
        mask = pd.Series(True, index=frame.index)

        if index > 0:
            mask &= (
                frame["trading_date"]
                >= boundaries[index - 1]
            )

        if index < len(plan) - 1:
            mask &= (
                frame["trading_date"]
                < boundaries[index]
            )

        selected = frame.loc[
            mask,
            [
                "ts_event",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "instrument_id",
                "source_contract",
                "trading_date",
            ],
        ].copy()
        selected["roll_method"] = method
        selected["adjustment_points"] = 0.0
        pieces.append(selected.loc[:, SERIES_COLUMNS])

    return (
        pd.concat(pieces, ignore_index=True)
        .sort_values("ts_event", kind="mergesort")
        .reset_index(drop=True)
    )


def adjustment_map_from_ledger(
    ledger: list[dict[str, Any]],
) -> dict[str, float]:
    ordered = sorted(
        ledger,
        key=lambda row: int(
            row["transition_sequence"]
        ),
    )

    if not ordered:
        raise ValueError("Roll ledger is empty.")

    adjustment_map: dict[str, float] = {
        ordered[-1]["incoming_contract"]: 0.0
    }
    cumulative = 0.0

    for row in reversed(ordered):
        cumulative += float(
            row["roll_difference_points"]
        )
        adjustment_map[row["outgoing_contract"]] = (
            cumulative
        )

    return adjustment_map


def apply_backward_adjustment(
    unadjusted: pd.DataFrame,
    ledger: list[dict[str, Any]],
) -> pd.DataFrame:
    result = unadjusted.copy()
    adjustment_map = adjustment_map_from_ledger(
        ledger
    )
    adjustments = result["source_contract"].map(
        adjustment_map
    )

    if adjustments.isna().any():
        missing = sorted(
            result.loc[
                adjustments.isna(),
                "source_contract",
            ].unique()
        )
        raise ValueError(
            "Missing adjustment mapping for: "
            + ", ".join(missing)
        )

    adjustments = adjustments.astype(float)

    for column in PRICE_COLUMNS:
        result[column] = (
            result[column].astype(float)
            + adjustments
        )

    result["adjustment_points"] = adjustments
    return result


def minute_gap_diagnostics(
    values: Any,
) -> dict[str, int]:
    timestamps = (
        ensure_utc_index(values)
        .drop_duplicates()
        .sort_values()
    )

    if len(timestamps) < 2:
        return {
            "missing_minute_run_count": 0,
            "largest_missing_minute_run": 0,
        }

    minute_ns = 60_000_000_000
    missing = (
        np.diff(timestamp_ns_values(timestamps))
        // minute_ns
        - 1
    )
    positive = missing[missing > 0]

    return {
        "missing_minute_run_count": int(
            len(positive)
        ),
        "largest_missing_minute_run": int(
            positive.max() if len(positive) else 0
        ),
    }


def tick_aligned(values: np.ndarray) -> bool:
    scaled = values.astype(float) * 4.0
    return bool(
        np.all(
            np.isclose(
                scaled,
                np.rint(scaled),
                rtol=0.0,
                atol=1e-7,
                equal_nan=False,
            )
        )
    )


def validate_series(
    unadjusted: pd.DataFrame,
    adjusted: pd.DataFrame,
    *,
    expected_contracts: set[str],
) -> dict[str, bool]:
    timestamps = ensure_utc_index(
        unadjusted["ts_event"]
    )
    adjusted_timestamps = ensure_utc_index(
        adjusted["ts_event"]
    )
    price_values = unadjusted.loc[
        :, PRICE_COLUMNS
    ].to_numpy(dtype=float)
    adjusted_price_values = adjusted.loc[
        :, PRICE_COLUMNS
    ].to_numpy(dtype=float)
    volume = unadjusted["volume"].to_numpy(
        dtype=float
    )

    high = unadjusted["high"].to_numpy(dtype=float)
    low = unadjusted["low"].to_numpy(dtype=float)
    open_price = unadjusted["open"].to_numpy(
        dtype=float
    )
    close = unadjusted["close"].to_numpy(
        dtype=float
    )

    adjusted_high = adjusted["high"].to_numpy(
        dtype=float
    )
    adjusted_low = adjusted["low"].to_numpy(
        dtype=float
    )
    adjusted_open = adjusted["open"].to_numpy(
        dtype=float
    )
    adjusted_close = adjusted["close"].to_numpy(
        dtype=float
    )

    return {
        "constructed_series_is_nonempty": (
            len(unadjusted) > 0
            and len(adjusted) == len(unadjusted)
        ),
        "timestamps_are_strictly_increasing": (
            timestamps.is_monotonic_increasing
            and adjusted_timestamps.is_monotonic_increasing
        ),
        "constructed_timestamps_are_unique": (
            not timestamps.duplicated().any()
            and not adjusted_timestamps.duplicated().any()
        ),
        "source_contract_identity_is_complete": (
            set(
                unadjusted["source_contract"].unique()
            )
            == expected_contracts
        ),
        "all_ohlcv_values_are_finite": bool(
            np.isfinite(price_values).all()
            and np.isfinite(
                adjusted_price_values
            ).all()
            and np.isfinite(volume).all()
        ),
        "unadjusted_ohlc_invariants_hold": bool(
            np.all(
                (high >= low)
                & (high >= open_price)
                & (high >= close)
                & (low <= open_price)
                & (low <= close)
            )
        ),
        "adjusted_ohlc_invariants_hold": bool(
            np.all(
                (adjusted_high >= adjusted_low)
                & (adjusted_high >= adjusted_open)
                & (adjusted_high >= adjusted_close)
                & (adjusted_low <= adjusted_open)
                & (adjusted_low <= adjusted_close)
            )
        ),
        "volume_is_nonnegative": bool(
            np.all(volume >= 0)
        ),
        "unadjusted_prices_are_quarter_tick_aligned": (
            tick_aligned(price_values)
        ),
        "adjustments_are_quarter_tick_aligned": (
            tick_aligned(
                adjusted["adjustment_points"].to_numpy(
                    dtype=float
                )
            )
        ),
    }


def rows_match_source(
    unadjusted: pd.DataFrame,
    contract_frames: dict[str, pd.DataFrame],
) -> bool:
    compare_columns = (
        "open",
        "high",
        "low",
        "close",
        "volume",
        "instrument_id",
    )

    for symbol, selected in unadjusted.groupby(
        "source_contract",
        sort=True,
        observed=False,
    ):
        source = contract_frames[str(symbol)].set_index(
            "ts_event"
        )
        timestamps = ensure_utc_index(
            selected["ts_event"]
        )
        expected = source.loc[
            timestamps,
            compare_columns,
        ].reset_index(drop=True)
        actual = selected.loc[
            :, compare_columns
        ].reset_index(drop=True)

        if len(expected) != len(actual):
            return False

        for column in compare_columns:
            if not np.array_equal(
                expected[column].to_numpy(),
                actual[column].to_numpy(),
            ):
                return False

    return True


def adjustment_reconciles(
    unadjusted: pd.DataFrame,
    adjusted: pd.DataFrame,
    ledger: list[dict[str, Any]],
) -> bool:
    if len(unadjusted) != len(adjusted):
        return False

    expected_map = adjustment_map_from_ledger(
        ledger
    )
    expected = unadjusted["source_contract"].map(
        expected_map
    ).to_numpy(dtype=float)
    actual = adjusted["adjustment_points"].to_numpy(
        dtype=float
    )

    if not np.array_equal(expected, actual):
        return False

    for column in PRICE_COLUMNS:
        difference = (
            adjusted[column].to_numpy(dtype=float)
            - unadjusted[column].to_numpy(dtype=float)
        )
        if not np.array_equal(difference, expected):
            return False

    return True


def semantic_frame_hash(frame: pd.DataFrame) -> str:
    canonical = frame.loc[:, SERIES_COLUMNS].copy()
    canonical["ts_event"] = timestamp_ns_values(
        ensure_utc_index(canonical["ts_event"])
    )
    canonical["trading_date"] = canonical[
        "trading_date"
    ].map(lambda value: value.isoformat())

    row_hashes = pd.util.hash_pandas_object(
        canonical,
        index=False,
        categorize=False,
    ).to_numpy(dtype=np.uint64)

    digest = hashlib.sha256()
    digest.update(
        canonical_json_bytes(list(canonical.columns))
    )
    digest.update(row_hashes.tobytes())
    return digest.hexdigest()


def ledger_semantic_hash(
    rows: list[dict[str, Any]],
) -> str:
    ordered = sorted(
        rows,
        key=lambda row: (
            row["method"],
            int(row["transition_sequence"]),
        ),
    )
    return hashlib.sha256(
        canonical_json_bytes(ordered)
    ).hexdigest()


def contribution_rows(
    unadjusted: pd.DataFrame,
    adjusted: pd.DataFrame,
    *,
    method: str,
) -> list[dict[str, Any]]:
    adjustment_by_contract = adjusted.groupby(
        "source_contract",
        sort=True,
        observed=False,
    )["adjustment_points"].first().to_dict()

    rows: list[dict[str, Any]] = []

    for symbol, group in unadjusted.groupby(
        "source_contract",
        sort=True,
        observed=False,
    ):
        rows.append(
            {
                "method": method,
                "source_contract": str(symbol),
                "row_count": int(len(group)),
                "first_timestamp_utc": (
                    group["ts_event"].min().isoformat()
                ),
                "last_timestamp_utc": (
                    group["ts_event"].max().isoformat()
                ),
                "first_trading_date": min(
                    group["trading_date"]
                ).isoformat(),
                "last_trading_date": max(
                    group["trading_date"]
                ).isoformat(),
                "backward_adjustment_points": float(
                    adjustment_by_contract[symbol]
                ),
            }
        )

    return rows


def method_comparison_row(
    unadjusted: pd.DataFrame,
    adjusted: pd.DataFrame,
    ledger: list[dict[str, Any]],
    *,
    method: str,
) -> dict[str, Any]:
    gaps = minute_gap_diagnostics(
        unadjusted["ts_event"]
    )

    return {
        "method": method,
        "row_count": int(len(unadjusted)),
        "first_timestamp_utc": (
            unadjusted["ts_event"].min().isoformat()
        ),
        "last_timestamp_utc": (
            unadjusted["ts_event"].max().isoformat()
        ),
        "calendar_fallback_count": int(
            sum(
                bool(row["calendar_fallback"])
                for row in ledger
            )
        ),
        "provider_warning_transition_count": int(
            sum(
                bool(row["provider_warning_contracts"])
                for row in ledger
            )
        ),
        "missing_minute_run_count": gaps[
            "missing_minute_run_count"
        ],
        "largest_missing_minute_run": gaps[
            "largest_missing_minute_run"
        ],
        "total_absolute_roll_difference_points": float(
            sum(
                abs(float(row["roll_difference_points"]))
                for row in ledger
            )
        ),
        "unadjusted_semantic_sha256": (
            semantic_frame_hash(unadjusted)
        ),
        "adjusted_semantic_sha256": (
            semantic_frame_hash(adjusted)
        ),
    }
