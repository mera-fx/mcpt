from __future__ import annotations

import calendar
from copy import deepcopy
from datetime import date, timedelta


DATASET_START = date(2010, 6, 6)
DATASET_END_EXCLUSIVE = date(2026, 7, 24)

CONTRACT_MONTHS = (
    (3, "H"),
    (6, "M"),
    (9, "U"),
    (12, "Z"),
)

ROLLOVER_OVERLAP_DAYS = 30
MAXIMUM_DOWNLOAD_COST_USD = 35.0

PLANNING_CONTINUOUS_QUOTE_USD = 19.9408
PLANNING_CONTINUOUS_SYMBOL = "NQ.v.0"


def third_friday(
    year: int,
    month: int,
) -> date:
    month_calendar = calendar.monthcalendar(
        year,
        month,
    )

    fridays = [
        week[calendar.FRIDAY]
        for week in month_calendar
        if week[calendar.FRIDAY] != 0
    ]

    return date(
        year,
        month,
        fridays[2],
    )


def previous_quarter(
    year: int,
    month: int,
) -> tuple[int, int]:
    if month == 3:
        return year - 1, 12

    if month == 6:
        return year, 3

    if month == 9:
        return year, 6

    if month == 12:
        return year, 9

    raise ValueError(
        f"Unsupported quarterly contract month: {month}"
    )


def build_contract_plan() -> tuple[
    tuple[str, str, str, str, str],
    ...,
]:
    contracts: list[
        tuple[str, str, str, str, str]
    ] = []

    for year in range(
        DATASET_START.year,
        DATASET_END_EXCLUSIVE.year + 1,
    ):
        for month, month_code in CONTRACT_MONTHS:
            expiration = third_friday(
                year,
                month,
            )

            previous_year, previous_month = (
                previous_quarter(
                    year,
                    month,
                )
            )

            previous_expiration = third_friday(
                previous_year,
                previous_month,
            )

            window_start = max(
                DATASET_START,
                previous_expiration
                - timedelta(
                    days=ROLLOVER_OVERLAP_DAYS
                ),
            )

            window_end = min(
                DATASET_END_EXCLUSIVE,
                expiration + timedelta(days=1),
            )

            if window_start >= window_end:
                continue

            canonical_symbol = (
                f"NQ{month_code}{year % 100:02d}"
            )

            raw_symbol = (
                f"NQ{month_code}{year % 10}"
            )

            contracts.append(
                (
                    canonical_symbol,
                    raw_symbol,
                    window_start.isoformat(),
                    window_end.isoformat(),
                    expiration.isoformat(),
                )
            )

    return tuple(contracts)


CONTRACT_PLAN = build_contract_plan()


EXP019_PREREGISTRATION = {
    "schema_version": 1,
    "experiment_id": "EXP-019",
    "title": (
        "Databento NQ Maximum-History "
        "Exact-Contract Archive Planning"
    ),
    "locked_date": "2026-07-25",
    "research_status": "PRE_REGISTERED",
    "implementation_status": "NOT_IMPLEMENTED",
    "ohlcv_bar_values_viewed": "NONE",
    "objective": {
        "cost_estimate_first": True,
        "exact_contract_archive_planning": True,
        "continuous_series_construction": False,
        "strategy_performance_question": False,
        "exchange_accuracy_claim": False,
        "best_vendor_claim": False,
    },
    "source": {
        "provider": "Databento",
        "client_version": "0.81.0",
        "dataset": "GLBX.MDP3",
        "schema": "ohlcv-1m",
        "stype_in": "raw_symbol",
        "timestamp_field": "ts_event",
        "timestamp_timezone": "UTC",
    },
    "planning_reference": {
        "continuous_symbol": (
            PLANNING_CONTINUOUS_SYMBOL
        ),
        "continuous_stype_in": "continuous",
        "continuous_cost_quote_usd": (
            PLANNING_CONTINUOUS_QUOTE_USD
        ),
        "continuous_start": (
            DATASET_START.isoformat()
        ),
        "continuous_end_exclusive": (
            DATASET_END_EXCLUSIVE.isoformat()
        ),
        "ohlcv_downloaded": False,
    },
    "contract_scope": {
        "contract_plan": CONTRACT_PLAN,
        "contract_count": len(CONTRACT_PLAN),
        "first_contract": CONTRACT_PLAN[0][0],
        "last_contract": CONTRACT_PLAN[-1][0],
        "dataset_start": DATASET_START.isoformat(),
        "dataset_end_exclusive": (
            DATASET_END_EXCLUSIVE.isoformat()
        ),
        "quarterly_contracts_only": True,
        "month_codes": ("H", "M", "U", "Z"),
        "outright_contracts_only": True,
        "calendar_spreads_prohibited": True,
        "options_prohibited": True,
        "rollover_overlap_days": (
            ROLLOVER_OVERLAP_DAYS
        ),
    },
    "cost_estimation": {
        "metadata_get_cost_only": True,
        "maximum_quote_calls": len(
            CONTRACT_PLAN
        ),
        "automatic_retries_prohibited": True,
        "stop_on_first_error": True,
        "bar_records_requested": False,
        "bar_records_downloaded": False,
        "per_contract_estimates_required": True,
        "summed_exact_contract_estimate_required": True,
        "continuous_quote_comparison_required": True,
    },
    "acquisition_boundary": {
        "download_implementation_status": (
            "NOT_IMPLEMENTED"
        ),
        "download_authorized": False,
        "explicit_user_approval_required": True,
        "maximum_total_cost_usd": (
            MAXIMUM_DOWNLOAD_COST_USD
        ),
        "maximum_successful_downloads": (
            len(CONTRACT_PLAN)
        ),
        "automatic_retries_prohibited": True,
        "raw_files_local_and_gitignored": True,
        "credentials_environment_only": True,
    },
    "future_archive_audit": {
        "instrument_identity": True,
        "raw_sha256": True,
        "canonical_sha256": True,
        "timestamp_alignment": True,
        "duplicate_timestamps": True,
        "duplicate_full_rows": True,
        "finite_ohlcv": True,
        "ohlc_invariants": True,
        "negative_volume": True,
        "off_tick_prices": True,
        "contract_window_coverage": True,
        "missing_minute_runs": True,
        "roll_overlap_measurement": True,
    },
    "prohibited_actions": {
        "continuous_symbol_download": True,
        "continuous_series_construction": True,
        "back_adjustment": True,
        "forward_adjustment": True,
        "strategy_replay": True,
        "strategy_optimization": True,
        "paper_trading": True,
        "live_trading": True,
        "changes_to_prior_experiments": True,
    },
    "interpretation": {
        "highest_cost_phase_result": (
            "EXACT_CONTRACT_COST_ESTIMATE_COMPLETE"
        ),
        "cost_result_is_not_data_qualification": True,
        "archive_requires_separate_approval": True,
        "archive_audit_required_before_use": True,
        "roll_construction_requires_later_work": True,
        "strategy_use_not_authorized": True,
    },
}


def get_exp019_preregistration():
    return deepcopy(
        EXP019_PREREGISTRATION
    )


def validate_exp019_preregistration(
    record=None,
):
    r = (
        EXP019_PREREGISTRATION
        if record is None
        else record
    )

    if (
        r["experiment_id"] != "EXP-019"
        or r["research_status"]
        != "PRE_REGISTERED"
        or r["implementation_status"]
        != "NOT_IMPLEMENTED"
        or r["ohlcv_bar_values_viewed"]
        != "NONE"
    ):
        raise ValueError(
            "EXP-019 identity changed."
        )

    scope = r["contract_scope"]

    if (
        scope["contract_count"] != 66
        or scope["first_contract"] != "NQM10"
        or scope["last_contract"] != "NQU26"
        or scope["dataset_start"]
        != "2010-06-06"
        or scope["dataset_end_exclusive"]
        != "2026-07-24"
        or scope["rollover_overlap_days"]
        != 30
    ):
        raise ValueError(
            "EXP-019 contract scope changed."
        )

    if tuple(
        scope["contract_plan"]
    ) != CONTRACT_PLAN:
        raise ValueError(
            "EXP-019 contract plan changed."
        )

    estimate = r["cost_estimation"]

    if (
        estimate["metadata_get_cost_only"]
        is not True
        or estimate["maximum_quote_calls"]
        != 66
        or estimate["automatic_retries_prohibited"]
        is not True
        or estimate["bar_records_requested"]
        is not False
        or estimate["bar_records_downloaded"]
        is not False
    ):
        raise ValueError(
            "EXP-019 estimate boundary changed."
        )

    acquisition = r["acquisition_boundary"]

    if (
        acquisition["download_authorized"]
        is not False
        or acquisition[
            "explicit_user_approval_required"
        ]
        is not True
        or acquisition[
            "maximum_total_cost_usd"
        ]
        != 35.0
        or acquisition[
            "automatic_retries_prohibited"
        ]
        is not True
    ):
        raise ValueError(
            "EXP-019 acquisition boundary changed."
        )

    prohibited = r["prohibited_actions"]

    if not all(
        value is True
        for value in prohibited.values()
    ):
        raise ValueError(
            "EXP-019 prohibited actions changed."
        )
