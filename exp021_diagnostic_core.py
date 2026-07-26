from __future__ import annotations

from datetime import date
import hashlib
import json
from statistics import median
from typing import Any, Iterable

import pandas as pd

from exp020_constructor_core import (
    KNOWN_PROVIDER_WARNING_CONTRACTS,
    common_trading_dates,
    daily_volume,
    select_calendar_roll_date,
)


DAILY_VOLUME_FIELDS = (
    "transition_sequence",
    "outgoing_contract",
    "incoming_contract",
    "expiration",
    "calendar_roll_date",
    "trading_date",
    "common_session_offset_from_calendar",
    "outgoing_volume",
    "incoming_volume",
    "incoming_gt_outgoing",
    "warning_transition",
)

CANDIDATE_TRANSITION_FIELDS = (
    "candidate_id",
    "selection_rank",
    "transition_sequence",
    "outgoing_contract",
    "incoming_contract",
    "expiration",
    "calendar_roll_date",
    "required_consecutive_sessions",
    "maximum_effective_common_sessions_after_calendar",
    "warning_transition",
    "trigger_type",
    "trigger_session_1",
    "trigger_session_2",
    "effective_roll_date",
    "roll_offset_common_sessions",
    "calendar_fallback",
    "selected_warning_volume",
    "post_expiry_boundary",
    "boundary_in_common_overlap",
    "common_session_count",
    "diagnostic_window_start",
    "diagnostic_window_end",
)

CANDIDATE_SUMMARY_FIELDS = (
    "candidate_id",
    "selection_rank",
    "required_consecutive_sessions",
    "maximum_effective_common_sessions_after_calendar",
    "transition_count",
    "clean_transition_count",
    "warning_transition_count",
    "volume_trigger_count_all_transitions",
    "volume_trigger_count_clean_transitions",
    "calendar_fallback_count",
    "noncalendar_roll_date_count",
    "median_roll_offset_common_sessions",
    "minimum_roll_offset_common_sessions",
    "maximum_roll_offset_common_sessions",
    "post_expiry_boundary_count",
    "warning_volume_selected_boundary_count",
    "resolved_transition_count",
    "boundary_in_overlap_count",
    "passes_clean_trigger_gate",
    "passes_noncalendar_gate",
    "passes_post_expiry_gate",
    "passes_warning_gate",
    "passes_resolution_gate",
    "passes_boundary_gate",
    "passes_selection_gates",
)

EXPECTED_CANDIDATE_IDS = (
    "VOL_GT_OUT_2S_E0",
    "VOL_GT_OUT_2S_E1",
    "VOL_GT_OUT_2S_E2",
    "VOL_GT_OUT_2S_E3",
    "VOL_GT_OUT_1S_E0",
    "VOL_GT_OUT_1S_E1",
    "VOL_GT_OUT_1S_E2",
    "VOL_GT_OUT_1S_E3",
)


def canonical_json_bytes(payload: Any) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,
    ).encode("utf-8")


def semantic_rows_hash(
    rows: Iterable[dict[str, Any]],
    fields: tuple[str, ...],
) -> str:
    payload = [
        {
            field: row.get(field)
            for field in fields
        }
        for row in rows
    ]
    return hashlib.sha256(
        canonical_json_bytes(payload)
    ).hexdigest()


def validate_candidate_matrix(
    candidates: Iterable[dict[str, Any]],
    fixed_order: Iterable[str],
) -> tuple[dict[str, Any], ...]:
    rows = tuple(candidates)
    order = tuple(fixed_order)

    if len(rows) != 8:
        raise ValueError(
            "EXP-021 requires exactly eight candidates."
        )

    ids = tuple(
        str(row["method_id"])
        for row in rows
    )

    if ids != EXPECTED_CANDIDATE_IDS or ids != order:
        raise ValueError(
            "EXP-021 candidate order changed."
        )

    observed = {
        (
            int(row["required_consecutive_sessions"]),
            int(
                row[
                    "maximum_effective_common_sessions_after_calendar"
                ]
            ),
        )
        for row in rows
    }

    expected = {
        (sessions, extension)
        for sessions in (1, 2)
        for extension in (0, 1, 2, 3)
    }

    if observed != expected:
        raise ValueError(
            "EXP-021 candidate matrix changed."
        )

    controls = [
        row
        for row in rows
        if bool(row["control_method"])
    ]

    if (
        len(controls) != 1
        or controls[0]["method_id"]
        != "VOL_GT_OUT_2S_E0"
    ):
        raise ValueError(
            "EXP-021 control candidate changed."
        )

    return rows


def warning_transition(
    outgoing_contract: str,
    incoming_contract: str,
) -> bool:
    return bool(
        outgoing_contract
        in KNOWN_PROVIDER_WARNING_CONTRACTS
        or incoming_contract
        in KNOWN_PROVIDER_WARNING_CONTRACTS
    )


def _candidate_boundary(
    outgoing_daily: pd.Series,
    incoming_daily: pd.Series,
    *,
    calendar_roll_date: date,
    expiration: date,
    required_sessions: int,
    extension_sessions: int,
    warning: bool,
    search_sessions_before_calendar: int = 10,
) -> dict[str, Any]:
    common = common_trading_dates(
        outgoing_daily,
        incoming_daily,
    )

    if calendar_roll_date not in common:
        raise ValueError(
            "Calendar boundary is not a common session."
        )

    calendar_index = common.index(calendar_roll_date)
    start_index = max(
        0,
        calendar_index
        - int(search_sessions_before_calendar),
    )

    expiry_eligible = [
        index
        for index, value in enumerate(common)
        if value <= expiration
    ]

    if not expiry_eligible:
        raise ValueError(
            "No common session exists on or before expiry."
        )

    latest_index = min(
        calendar_index + int(extension_sessions),
        max(expiry_eligible),
    )

    window_end = common[latest_index]

    if warning:
        return {
            "trigger_type": "CALENDAR_FALLBACK_WARNING",
            "trigger_session_1": "",
            "trigger_session_2": "",
            "effective_roll_date": calendar_roll_date,
            "roll_offset_common_sessions": 0,
            "calendar_fallback": True,
            "selected_warning_volume": False,
            "post_expiry_boundary": False,
            "boundary_in_common_overlap": True,
            "common_session_count": len(common),
            "diagnostic_window_start": (
                common[start_index].isoformat()
            ),
            "diagnostic_window_end": (
                window_end.isoformat()
            ),
        }

    required = int(required_sessions)

    for final_trigger_index in range(
        start_index + required - 1,
        latest_index,
    ):
        trigger_indices = list(
            range(
                final_trigger_index - required + 1,
                final_trigger_index + 1,
            )
        )

        qualifies = all(
            int(incoming_daily.loc[common[index]])
            > int(outgoing_daily.loc[common[index]])
            for index in trigger_indices
        )

        if not qualifies:
            continue

        effective_index = final_trigger_index + 1

        if effective_index > latest_index:
            continue

        effective = common[effective_index]

        if effective > expiration:
            continue

        trigger_dates = [
            common[index]
            for index in trigger_indices
        ]

        return {
            "trigger_type": "VOLUME_CROSSOVER",
            "trigger_session_1": (
                trigger_dates[0].isoformat()
            ),
            "trigger_session_2": (
                trigger_dates[-1].isoformat()
                if required == 2
                else ""
            ),
            "effective_roll_date": effective,
            "roll_offset_common_sessions": (
                effective_index - calendar_index
            ),
            "calendar_fallback": False,
            "selected_warning_volume": False,
            "post_expiry_boundary": (
                effective > expiration
            ),
            "boundary_in_common_overlap": (
                effective in common
            ),
            "common_session_count": len(common),
            "diagnostic_window_start": (
                common[start_index].isoformat()
            ),
            "diagnostic_window_end": (
                window_end.isoformat()
            ),
        }

    return {
        "trigger_type": "CALENDAR_FALLBACK_NO_TRIGGER",
        "trigger_session_1": "",
        "trigger_session_2": "",
        "effective_roll_date": calendar_roll_date,
        "roll_offset_common_sessions": 0,
        "calendar_fallback": True,
        "selected_warning_volume": False,
        "post_expiry_boundary": False,
        "boundary_in_common_overlap": True,
        "common_session_count": len(common),
        "diagnostic_window_start": (
            common[start_index].isoformat()
        ),
        "diagnostic_window_end": (
            window_end.isoformat()
        ),
    }


def evaluate_candidate_transition(
    outgoing_daily: pd.Series,
    incoming_daily: pd.Series,
    *,
    candidate: dict[str, Any],
    selection_rank: int,
    transition_sequence: int,
    outgoing_contract: str,
    incoming_contract: str,
    expiration: date,
    calendar_roll_date: date,
    warning: bool,
) -> dict[str, Any]:
    choice = _candidate_boundary(
        outgoing_daily,
        incoming_daily,
        calendar_roll_date=calendar_roll_date,
        expiration=expiration,
        required_sessions=int(
            candidate["required_consecutive_sessions"]
        ),
        extension_sessions=int(
            candidate[
                "maximum_effective_common_sessions_after_calendar"
            ]
        ),
        warning=warning,
    )

    effective = choice["effective_roll_date"]

    return {
        "candidate_id": candidate["method_id"],
        "selection_rank": int(selection_rank),
        "transition_sequence": int(
            transition_sequence
        ),
        "outgoing_contract": outgoing_contract,
        "incoming_contract": incoming_contract,
        "expiration": expiration.isoformat(),
        "calendar_roll_date": (
            calendar_roll_date.isoformat()
        ),
        "required_consecutive_sessions": int(
            candidate["required_consecutive_sessions"]
        ),
        "maximum_effective_common_sessions_after_calendar": int(
            candidate[
                "maximum_effective_common_sessions_after_calendar"
            ]
        ),
        "warning_transition": bool(warning),
        "trigger_type": choice["trigger_type"],
        "trigger_session_1": choice[
            "trigger_session_1"
        ],
        "trigger_session_2": choice[
            "trigger_session_2"
        ],
        "effective_roll_date": effective.isoformat(),
        "roll_offset_common_sessions": int(
            choice["roll_offset_common_sessions"]
        ),
        "calendar_fallback": bool(
            choice["calendar_fallback"]
        ),
        "selected_warning_volume": bool(
            choice["selected_warning_volume"]
        ),
        "post_expiry_boundary": bool(
            choice["post_expiry_boundary"]
        ),
        "boundary_in_common_overlap": bool(
            choice["boundary_in_common_overlap"]
        ),
        "common_session_count": int(
            choice["common_session_count"]
        ),
        "diagnostic_window_start": choice[
            "diagnostic_window_start"
        ],
        "diagnostic_window_end": choice[
            "diagnostic_window_end"
        ],
    }


def daily_volume_rows_for_transition(
    outgoing_daily: pd.Series,
    incoming_daily: pd.Series,
    *,
    transition_sequence: int,
    outgoing_contract: str,
    incoming_contract: str,
    expiration: date,
    calendar_roll_date: date,
    warning: bool,
) -> list[dict[str, Any]]:
    common = common_trading_dates(
        outgoing_daily,
        incoming_daily,
    )
    calendar_index = common.index(calendar_roll_date)
    start_index = max(0, calendar_index - 10)
    end_index = min(
        calendar_index + 3,
        max(
            index
            for index, value in enumerate(common)
            if value <= expiration
        ),
    )

    rows = []

    for index in range(start_index, end_index + 1):
        trading_date = common[index]
        outgoing_value = int(
            outgoing_daily.loc[trading_date]
        )
        incoming_value = int(
            incoming_daily.loc[trading_date]
        )
        rows.append(
            {
                "transition_sequence": int(
                    transition_sequence
                ),
                "outgoing_contract": outgoing_contract,
                "incoming_contract": incoming_contract,
                "expiration": expiration.isoformat(),
                "calendar_roll_date": (
                    calendar_roll_date.isoformat()
                ),
                "trading_date": (
                    trading_date.isoformat()
                ),
                "common_session_offset_from_calendar": (
                    index - calendar_index
                ),
                "outgoing_volume": outgoing_value,
                "incoming_volume": incoming_value,
                "incoming_gt_outgoing": (
                    incoming_value > outgoing_value
                ),
                "warning_transition": bool(warning),
            }
        )

    return rows


def summarise_candidate(
    candidate_rows: list[dict[str, Any]],
    *,
    candidate: dict[str, Any],
    selection_rank: int,
    gates: dict[str, Any],
) -> dict[str, Any]:
    rows = [
        row
        for row in candidate_rows
        if row["candidate_id"]
        == candidate["method_id"]
    ]

    clean = [
        row
        for row in rows
        if not row["warning_transition"]
    ]
    warnings = [
        row
        for row in rows
        if row["warning_transition"]
    ]
    triggers = [
        row
        for row in rows
        if not row["calendar_fallback"]
    ]
    clean_triggers = [
        row
        for row in clean
        if not row["calendar_fallback"]
    ]
    offsets = [
        int(row["roll_offset_common_sessions"])
        for row in triggers
    ]

    clean_gate = (
        len(clean_triggers)
        >= int(
            gates[
                "minimum_clean_volume_trigger_count"
            ]
        )
    )
    noncalendar_count = sum(
        row["effective_roll_date"]
        != row["calendar_roll_date"]
        for row in rows
    )
    noncalendar_gate = (
        noncalendar_count
        >= int(
            gates[
                "minimum_noncalendar_roll_date_count"
            ]
        )
    )
    post_expiry_count = sum(
        bool(row["post_expiry_boundary"])
        for row in rows
    )
    warning_selected_count = sum(
        bool(row["selected_warning_volume"])
        for row in rows
    )
    resolved_count = sum(
        bool(row["effective_roll_date"])
        for row in rows
    )
    boundary_count = sum(
        bool(row["boundary_in_common_overlap"])
        for row in rows
    )

    post_gate = (
        post_expiry_count
        == int(gates["post_expiry_boundary_count"])
    )
    warning_gate = (
        warning_selected_count
        == int(
            gates[
                "warning_volume_selected_boundary_count"
            ]
        )
    )
    resolution_gate = (
        resolved_count == 65
    )
    boundary_gate = (
        boundary_count == 65
    )

    passes = all(
        (
            clean_gate,
            noncalendar_gate,
            post_gate,
            warning_gate,
            resolution_gate,
            boundary_gate,
        )
    )

    return {
        "candidate_id": candidate["method_id"],
        "selection_rank": int(selection_rank),
        "required_consecutive_sessions": int(
            candidate["required_consecutive_sessions"]
        ),
        "maximum_effective_common_sessions_after_calendar": int(
            candidate[
                "maximum_effective_common_sessions_after_calendar"
            ]
        ),
        "transition_count": len(rows),
        "clean_transition_count": len(clean),
        "warning_transition_count": len(warnings),
        "volume_trigger_count_all_transitions": len(
            triggers
        ),
        "volume_trigger_count_clean_transitions": len(
            clean_triggers
        ),
        "calendar_fallback_count": sum(
            bool(row["calendar_fallback"])
            for row in rows
        ),
        "noncalendar_roll_date_count": int(
            noncalendar_count
        ),
        "median_roll_offset_common_sessions": (
            float(median(offsets))
            if offsets
            else 0.0
        ),
        "minimum_roll_offset_common_sessions": (
            min(offsets) if offsets else 0
        ),
        "maximum_roll_offset_common_sessions": (
            max(offsets) if offsets else 0
        ),
        "post_expiry_boundary_count": int(
            post_expiry_count
        ),
        "warning_volume_selected_boundary_count": int(
            warning_selected_count
        ),
        "resolved_transition_count": int(
            resolved_count
        ),
        "boundary_in_overlap_count": int(
            boundary_count
        ),
        "passes_clean_trigger_gate": bool(
            clean_gate
        ),
        "passes_noncalendar_gate": bool(
            noncalendar_gate
        ),
        "passes_post_expiry_gate": bool(
            post_gate
        ),
        "passes_warning_gate": bool(
            warning_gate
        ),
        "passes_resolution_gate": bool(
            resolution_gate
        ),
        "passes_boundary_gate": bool(
            boundary_gate
        ),
        "passes_selection_gates": bool(passes),
    }


def select_candidate(
    summaries: Iterable[dict[str, Any]],
    fixed_order: Iterable[str],
) -> dict[str, Any]:
    by_id = {
        row["candidate_id"]: row
        for row in summaries
    }

    for candidate_id in fixed_order:
        row = by_id[candidate_id]

        if row["passes_selection_gates"]:
            return {
                "selected": True,
                "candidate_id": candidate_id,
                "selection_rank": int(
                    row["selection_rank"]
                ),
                "classification": (
                    "DIAGNOSTIC_METHOD_SELECTED_"
                    "FOR_SEPARATE_CONSTRUCTION"
                ),
                "construction_authorized": False,
                "strategy_use_authorized": False,
            }

    return {
        "selected": False,
        "candidate_id": None,
        "selection_rank": None,
        "classification": (
            "DIAGNOSTIC_COMPLETE_NO_METHOD_SELECTED"
        ),
        "construction_authorized": False,
        "strategy_use_authorized": False,
    }


def build_diagnostics(
    daily_by_contract: dict[str, pd.Series],
    contract_plan: Iterable[
        tuple[str, str, str, str, str]
    ],
    *,
    candidates: Iterable[dict[str, Any]],
    fixed_order: Iterable[str],
    gates: dict[str, Any],
) -> dict[str, Any]:
    plan = list(contract_plan)
    candidate_rows = validate_candidate_matrix(
        candidates,
        fixed_order,
    )

    if len(plan) != 66:
        raise ValueError("Expected 66 contracts.")

    daily_rows: list[dict[str, Any]] = []
    transition_rows: list[dict[str, Any]] = []

    for index in range(len(plan) - 1):
        outgoing = plan[index]
        incoming = plan[index + 1]
        outgoing_symbol = outgoing[0]
        incoming_symbol = incoming[0]
        expiration = date.fromisoformat(outgoing[4])
        outgoing_daily = daily_by_contract[
            outgoing_symbol
        ]
        incoming_daily = daily_by_contract[
            incoming_symbol
        ]
        calendar_roll_date = (
            select_calendar_roll_date(
                outgoing_daily,
                incoming_daily,
                expiration=expiration,
            )
        )
        warning = warning_transition(
            outgoing_symbol,
            incoming_symbol,
        )

        daily_rows.extend(
            daily_volume_rows_for_transition(
                outgoing_daily,
                incoming_daily,
                transition_sequence=index + 1,
                outgoing_contract=outgoing_symbol,
                incoming_contract=incoming_symbol,
                expiration=expiration,
                calendar_roll_date=calendar_roll_date,
                warning=warning,
            )
        )

        for rank, candidate in enumerate(
            candidate_rows,
            start=1,
        ):
            transition_rows.append(
                evaluate_candidate_transition(
                    outgoing_daily,
                    incoming_daily,
                    candidate=candidate,
                    selection_rank=rank,
                    transition_sequence=index + 1,
                    outgoing_contract=outgoing_symbol,
                    incoming_contract=incoming_symbol,
                    expiration=expiration,
                    calendar_roll_date=calendar_roll_date,
                    warning=warning,
                )
            )

    summaries = [
        summarise_candidate(
            transition_rows,
            candidate=candidate,
            selection_rank=rank,
            gates=gates,
        )
        for rank, candidate in enumerate(
            candidate_rows,
            start=1,
        )
    ]

    selected = select_candidate(
        summaries,
        fixed_order,
    )

    hashes = {
        "daily_volume_semantic_sha256": (
            semantic_rows_hash(
                daily_rows,
                DAILY_VOLUME_FIELDS,
            )
        ),
        "candidate_transition_semantic_sha256": (
            semantic_rows_hash(
                transition_rows,
                CANDIDATE_TRANSITION_FIELDS,
            )
        ),
        "candidate_summary_semantic_sha256": (
            semantic_rows_hash(
                summaries,
                CANDIDATE_SUMMARY_FIELDS,
            )
        ),
        "selected_method_semantic_sha256": (
            hashlib.sha256(
                canonical_json_bytes(selected)
            ).hexdigest()
        ),
    }

    return {
        "daily_volume_rows": daily_rows,
        "candidate_transition_rows": transition_rows,
        "candidate_summaries": summaries,
        "selected_method": selected,
        "semantic_hashes": hashes,
    }
