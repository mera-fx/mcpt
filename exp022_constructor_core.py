from __future__ import annotations

from datetime import date
import hashlib
import json
from typing import Any, Iterable

import numpy as np
import pandas as pd

from exp020_constructor_core import (
    CONTRIBUTION_FIELDS,
    EXPECTED_CONTRACT_COUNT,
    EXPECTED_TRANSITION_COUNT,
    KNOWN_PROVIDER_WARNING_CONTRACTS,
    PRICE_COLUMNS,
    SERIES_COLUMNS,
    adjustment_reconciles,
    apply_backward_adjustment,
    common_trading_dates,
    contribution_rows,
    daily_volume,
    latest_shared_reference,
    rows_match_source,
    semantic_frame_hash,
    stitch_series,
    validate_series,
)
from exp021_diagnostic_core import (
    CANDIDATE_TRANSITION_FIELDS,
    semantic_rows_hash,
)


SELECTED_METHOD = "VOL_GT_OUT_2S_E3"
EXPECTED_SELECTED_RANK = 4
EXPECTED_CLEAN_TRANSITIONS = 42
EXPECTED_VOLUME_TRANSITIONS = 40
EXPECTED_CALENDAR_FALLBACKS = 25
EXPECTED_WARNING_FALLBACKS = 23
EXPECTED_CLEAN_FALLBACKS = 2

SELECTED_ROLL_LEDGER_FIELDS = (
    "method",
    "transition_sequence",
    "outgoing_contract",
    "incoming_contract",
    "outgoing_expiration",
    "calendar_roll_date",
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
    "warning_transition",
    "provider_warning_contracts",
    "common_overlap_sessions",
    "reference_timestamp_utc",
    "outgoing_reference_close",
    "incoming_reference_close",
    "roll_difference_points",
    "locked_exp021_candidate_id",
    "roll_offset_common_sessions",
)

INT_FIELDS = frozenset(
    {
        "selection_rank",
        "transition_sequence",
        "required_consecutive_sessions",
        "maximum_effective_common_sessions_after_calendar",
        "roll_offset_common_sessions",
        "common_session_count",
    }
)

BOOL_FIELDS = frozenset(
    {
        "warning_transition",
        "calendar_fallback",
        "selected_warning_volume",
        "post_expiry_boundary",
        "boundary_in_common_overlap",
    }
)

NONPRICE_COMPARISON_COLUMNS = (
    "ts_event",
    "volume",
    "instrument_id",
    "source_contract",
    "roll_method",
    "trading_date",
)


def canonical_json_bytes(payload: Any) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,
    ).encode("utf-8")


def parse_bool(value: Any) -> bool:
    if isinstance(value, (bool, np.bool_)):
        return bool(value)

    if isinstance(value, (int, np.integer)):
        if int(value) in (0, 1):
            return bool(value)

    text = str(value).strip().lower()

    if text in {"true", "1", "yes"}:
        return True
    if text in {"false", "0", "no"}:
        return False

    raise ValueError(
        f"Cannot interpret boolean value: {value!r}"
    )


def normalise_candidate_transition_rows(
    frame: pd.DataFrame,
) -> list[dict[str, Any]]:
    missing = [
        field
        for field in CANDIDATE_TRANSITION_FIELDS
        if field not in frame.columns
    ]

    if missing:
        raise ValueError(
            "Missing EXP-021 transition fields: "
            + ", ".join(missing)
        )

    rows: list[dict[str, Any]] = []

    for raw in frame.loc[
        :, CANDIDATE_TRANSITION_FIELDS
    ].to_dict(orient="records"):
        row: dict[str, Any] = {}

        for field in CANDIDATE_TRANSITION_FIELDS:
            value = raw[field]

            if field in BOOL_FIELDS:
                row[field] = parse_bool(value)
            elif field in INT_FIELDS:
                row[field] = int(value)
            elif pd.isna(value):
                row[field] = ""
            else:
                row[field] = str(value)

        rows.append(row)

    return rows


def candidate_transition_semantic_hash(
    rows: Iterable[dict[str, Any]],
) -> str:
    return semantic_rows_hash(
        rows,
        CANDIDATE_TRANSITION_FIELDS,
    )


def select_locked_candidate_rows(
    rows: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    selected = [
        dict(row)
        for row in rows
        if row["candidate_id"] == SELECTED_METHOD
    ]

    selected.sort(
        key=lambda row: int(
            row["transition_sequence"]
        )
    )

    if len(selected) != EXPECTED_TRANSITION_COUNT:
        raise ValueError(
            "Expected exactly 65 selected transitions."
        )

    if [
        int(row["transition_sequence"])
        for row in selected
    ] != list(
        range(1, EXPECTED_TRANSITION_COUNT + 1)
    ):
        raise ValueError(
            "Selected transition sequence changed."
        )

    pairs = {
        (
            row["outgoing_contract"],
            row["incoming_contract"],
        )
        for row in selected
    }

    if len(pairs) != EXPECTED_TRANSITION_COUNT:
        raise ValueError(
            "Selected adjacent-pair identity changed."
        )

    if any(
        int(row["selection_rank"])
        != EXPECTED_SELECTED_RANK
        or int(
            row["required_consecutive_sessions"]
        )
        != 2
        or int(
            row[
                "maximum_effective_common_sessions_after_calendar"
            ]
        )
        != 3
        for row in selected
    ):
        raise ValueError(
            "Selected method parameters changed."
        )

    clean = [
        row
        for row in selected
        if not row["warning_transition"]
    ]
    triggers = [
        row
        for row in clean
        if not row["calendar_fallback"]
    ]
    fallbacks = [
        row
        for row in selected
        if row["calendar_fallback"]
    ]
    warning_fallbacks = [
        row
        for row in fallbacks
        if row["warning_transition"]
    ]
    clean_fallbacks = [
        row
        for row in fallbacks
        if not row["warning_transition"]
    ]

    observed = (
        len(clean),
        len(triggers),
        len(fallbacks),
        len(warning_fallbacks),
        len(clean_fallbacks),
    )
    expected = (
        EXPECTED_CLEAN_TRANSITIONS,
        EXPECTED_VOLUME_TRANSITIONS,
        EXPECTED_CALENDAR_FALLBACKS,
        EXPECTED_WARNING_FALLBACKS,
        EXPECTED_CLEAN_FALLBACKS,
    )

    if observed != expected:
        raise ValueError(
            "Selected transition counts changed: "
            f"{observed!r}."
        )

    if any(
        row["post_expiry_boundary"]
        or row["selected_warning_volume"]
        or not row["boundary_in_common_overlap"]
        for row in selected
    ):
        raise ValueError(
            "Selected transition safety boundary changed."
        )

    return selected


def selected_transition_counts(
    rows: Iterable[dict[str, Any]],
) -> dict[str, int]:
    selected = list(rows)
    clean = [
        row
        for row in selected
        if not row["warning_transition"]
    ]
    fallbacks = [
        row
        for row in selected
        if row["calendar_fallback"]
    ]

    return {
        "transition_count": len(selected),
        "clean_transition_count": len(clean),
        "volume_driven_transition_count": sum(
            not row["calendar_fallback"]
            for row in clean
        ),
        "calendar_fallback_count": len(fallbacks),
        "warning_calendar_fallback_count": sum(
            row["calendar_fallback"]
            and row["warning_transition"]
            for row in selected
        ),
        "clean_calendar_fallback_count": sum(
            row["calendar_fallback"]
            and not row["warning_transition"]
            for row in selected
        ),
    }


def _volume_at(
    daily: pd.Series,
    value: str,
) -> int | str:
    text = str(value).strip()

    if not text:
        return ""

    trading_date = date.fromisoformat(text)

    if trading_date not in daily.index:
        raise ValueError(
            "Locked trigger session is absent from "
            "the source daily-volume series."
        )

    return int(daily.loc[trading_date])


def build_selected_roll_ledger(
    contract_frames: dict[str, pd.DataFrame],
    contract_plan: Iterable[
        tuple[str, str, str, str, str]
    ],
    selected_rows: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    plan = list(contract_plan)
    selected = list(selected_rows)

    if len(plan) != EXPECTED_CONTRACT_COUNT:
        raise ValueError("Expected 66 source contracts.")
    if len(selected) != EXPECTED_TRANSITION_COUNT:
        raise ValueError("Expected 65 frozen boundaries.")

    ledger: list[dict[str, Any]] = []

    for index, row in enumerate(selected):
        outgoing_plan = plan[index]
        incoming_plan = plan[index + 1]
        outgoing_symbol = outgoing_plan[0]
        incoming_symbol = incoming_plan[0]

        if (
            row["outgoing_contract"]
            != outgoing_symbol
            or row["incoming_contract"]
            != incoming_symbol
            or row["expiration"]
            != outgoing_plan[4]
        ):
            raise ValueError(
                "Frozen EXP-021 transition does not "
                "match the source contract plan."
            )

        outgoing = contract_frames[
            outgoing_symbol
        ]
        incoming = contract_frames[
            incoming_symbol
        ]
        outgoing_daily = daily_volume(outgoing)
        incoming_daily = daily_volume(incoming)
        common_dates = common_trading_dates(
            outgoing_daily,
            incoming_daily,
        )

        roll_date = date.fromisoformat(
            row["effective_roll_date"]
        )
        calendar_date = date.fromisoformat(
            row["calendar_roll_date"]
        )
        expiration = date.fromisoformat(
            row["expiration"]
        )

        if (
            roll_date not in common_dates
            or roll_date > expiration
        ):
            raise ValueError(
                "Frozen roll boundary is outside "
                "the locked common overlap."
            )

        warning_contracts = tuple(
            symbol
            for symbol in (
                outgoing_symbol,
                incoming_symbol,
            )
            if symbol
            in KNOWN_PROVIDER_WARNING_CONTRACTS
        )
        warning = bool(warning_contracts)

        if warning != bool(
            row["warning_transition"]
        ):
            raise ValueError(
                "Frozen warning-transition identity changed."
            )

        reference = latest_shared_reference(
            outgoing,
            incoming,
            roll_trading_date=roll_date,
        )

        trigger_1 = row["trigger_session_1"]
        trigger_2 = row["trigger_session_2"]

        ledger.append(
            {
                "method": SELECTED_METHOD,
                "transition_sequence": index + 1,
                "outgoing_contract": outgoing_symbol,
                "incoming_contract": incoming_symbol,
                "outgoing_expiration": (
                    expiration.isoformat()
                ),
                "calendar_roll_date": (
                    calendar_date.isoformat()
                ),
                "roll_trading_date": (
                    roll_date.isoformat()
                ),
                "trigger_type": row["trigger_type"],
                "trigger_session_1": trigger_1,
                "trigger_session_2": trigger_2,
                "outgoing_volume_session_1": (
                    _volume_at(
                        outgoing_daily,
                        trigger_1,
                    )
                ),
                "incoming_volume_session_1": (
                    _volume_at(
                        incoming_daily,
                        trigger_1,
                    )
                ),
                "outgoing_volume_session_2": (
                    _volume_at(
                        outgoing_daily,
                        trigger_2,
                    )
                ),
                "incoming_volume_session_2": (
                    _volume_at(
                        incoming_daily,
                        trigger_2,
                    )
                ),
                "calendar_fallback": bool(
                    row["calendar_fallback"]
                ),
                "warning_transition": warning,
                "provider_warning_contracts": (
                    "|".join(warning_contracts)
                ),
                "common_overlap_sessions": len(
                    common_dates
                ),
                "locked_exp021_candidate_id": (
                    row["candidate_id"]
                ),
                "roll_offset_common_sessions": int(
                    row[
                        "roll_offset_common_sessions"
                    ]
                ),
                **reference,
            }
        )

    return ledger


def ledger_semantic_hash(
    rows: Iterable[dict[str, Any]],
) -> str:
    ordered = sorted(
        (dict(row) for row in rows),
        key=lambda row: int(
            row["transition_sequence"]
        ),
    )
    return hashlib.sha256(
        canonical_json_bytes(ordered)
    ).hexdigest()


def ledger_checks(
    ledger: Iterable[dict[str, Any]],
) -> dict[str, bool]:
    rows = sorted(
        (dict(row) for row in ledger),
        key=lambda row: int(
            row["transition_sequence"]
        ),
    )
    roll_dates = [
        date.fromisoformat(
            row["roll_trading_date"]
        )
        for row in rows
    ]

    return {
        "exactly_65_ordered_transitions": (
            len(rows) == EXPECTED_TRANSITION_COUNT
            and [
                int(row["transition_sequence"])
                for row in rows
            ]
            == list(
                range(
                    1,
                    EXPECTED_TRANSITION_COUNT + 1,
                )
            )
        ),
        "one_boundary_per_adjacent_pair": (
            len(
                {
                    (
                        row["outgoing_contract"],
                        row["incoming_contract"],
                    )
                    for row in rows
                }
            )
            == EXPECTED_TRANSITION_COUNT
            and roll_dates == sorted(roll_dates)
        ),
        "all_boundaries_are_inside_locked_overlap": all(
            int(row["common_overlap_sessions"]) > 0
            and bool(row["roll_boundary_utc"])
            for row in rows
        ),
        "no_effective_boundary_is_after_expiry": all(
            date.fromisoformat(
                row["roll_trading_date"]
            )
            <= date.fromisoformat(
                row["outgoing_expiration"]
            )
            for row in rows
        ),
        "adjustment_references_exist_and_are_finite": all(
            bool(row["reference_timestamp_utc"])
            and np.isfinite(
                float(
                    row[
                        "outgoing_reference_close"
                    ]
                )
            )
            and np.isfinite(
                float(
                    row[
                        "incoming_reference_close"
                    ]
                )
            )
            and np.isfinite(
                float(
                    row["roll_difference_points"]
                )
            )
            for row in rows
        ),
    }


def stitching_boundary_is_exact(
    frame: pd.DataFrame,
    contract_plan: Iterable[
        tuple[str, str, str, str, str]
    ],
    ledger: Iterable[dict[str, Any]],
) -> bool:
    plan = list(contract_plan)
    rows = sorted(
        (dict(row) for row in ledger),
        key=lambda row: int(
            row["transition_sequence"]
        ),
    )
    boundaries = [
        date.fromisoformat(
            row["roll_trading_date"]
        )
        for row in rows
    ]

    if len(plan) != 66 or len(boundaries) != 65:
        return False

    for index, contract in enumerate(plan):
        symbol = contract[0]
        selected = frame[
            frame["source_contract"] == symbol
        ]

        if selected.empty:
            return False

        dates = selected["trading_date"]

        if (
            index > 0
            and bool(
                (dates < boundaries[index - 1]).any()
            )
        ):
            return False

        if (
            index < len(plan) - 1
            and bool(
                (dates >= boundaries[index]).any()
            )
        ):
            return False

    return True


def adjusted_nonprice_fields_match(
    unadjusted: pd.DataFrame,
    adjusted: pd.DataFrame,
) -> bool:
    if len(unadjusted) != len(adjusted):
        return False

    for column in NONPRICE_COMPARISON_COLUMNS:
        left = unadjusted[column].to_numpy()
        right = adjusted[column].to_numpy()

        if not np.array_equal(left, right):
            return False

    return True


def construct_selected_in_memory(
    contract_frames: dict[str, pd.DataFrame],
    contract_plan: Iterable[
        tuple[str, str, str, str, str]
    ],
    selected_rows: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    plan = list(contract_plan)
    selected = list(selected_rows)
    ledger = build_selected_roll_ledger(
        contract_frames,
        plan,
        selected,
    )
    unadjusted = stitch_series(
        contract_frames,
        plan,
        ledger,
        method=SELECTED_METHOD,
    )
    adjusted = apply_backward_adjustment(
        unadjusted,
        ledger,
    )
    expected_contracts = {
        contract[0]
        for contract in plan
    }

    series_checks = validate_series(
        unadjusted,
        adjusted,
        expected_contracts=expected_contracts,
    )
    ledger_result = ledger_checks(ledger)

    return {
        "ledger": ledger,
        "unadjusted": unadjusted,
        "adjusted": adjusted,
        "contributions": contribution_rows(
            unadjusted,
            adjusted,
            method=SELECTED_METHOD,
        ),
        "checks": {
            **series_checks,
            **ledger_result,
            "stitching_boundary_rule_is_exact": (
                stitching_boundary_is_exact(
                    unadjusted,
                    plan,
                    ledger,
                )
            ),
            "stitched_rows_reconcile_to_source": (
                rows_match_source(
                    unadjusted,
                    contract_frames,
                )
            ),
            "backward_adjustment_reconciles": (
                adjustment_reconciles(
                    unadjusted,
                    adjusted,
                    ledger,
                )
            ),
            "adjusted_and_unadjusted_nonprice_fields_match": (
                adjusted_nonprice_fields_match(
                    unadjusted,
                    adjusted,
                )
            ),
        },
        "semantic_hashes": {
            "roll_ledger_semantic_sha256": (
                ledger_semantic_hash(ledger)
            ),
            "selected_roll_unadjusted_semantic_sha256": (
                semantic_frame_hash(unadjusted)
            ),
            "selected_roll_backward_adjusted_semantic_sha256": (
                semantic_frame_hash(adjusted)
            ),
        },
    }


def final_classification(
    hard_checks: dict[str, bool],
) -> str:
    if all(hard_checks.values()):
        return (
            "QUALIFIED_AS_SELECTED_VOLUME_ROLL_"
            "CONTINUOUS_SERIES"
        )

    return "CONSTRUCTION_NOT_QUALIFIED"


__all__ = [
    "BOOL_FIELDS",
    "CONTRIBUTION_FIELDS",
    "EXPECTED_CALENDAR_FALLBACKS",
    "EXPECTED_CLEAN_FALLBACKS",
    "EXPECTED_CLEAN_TRANSITIONS",
    "EXPECTED_VOLUME_TRANSITIONS",
    "EXPECTED_WARNING_FALLBACKS",
    "INT_FIELDS",
    "NONPRICE_COMPARISON_COLUMNS",
    "SELECTED_METHOD",
    "SELECTED_ROLL_LEDGER_FIELDS",
    "adjusted_nonprice_fields_match",
    "build_selected_roll_ledger",
    "candidate_transition_semantic_hash",
    "construct_selected_in_memory",
    "final_classification",
    "ledger_checks",
    "ledger_semantic_hash",
    "normalise_candidate_transition_rows",
    "parse_bool",
    "select_locked_candidate_rows",
    "selected_transition_counts",
    "stitching_boundary_is_exact",
]
