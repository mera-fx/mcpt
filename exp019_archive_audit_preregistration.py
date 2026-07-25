from __future__ import annotations

from copy import deepcopy


EXP019_ARCHIVE_AUDIT_PREREGISTRATION = {
    "schema_version": 1,
    "experiment_id": "EXP-019",
    "locked_date": "2026-07-25",
    "audit_status": "PRE_REGISTERED",
    "audit_execution_status": "NOT_IMPLEMENTED",
    "ohlcv_values_examined_before_lock": False,
    "acquisition_evidence": {
        "downloader_commit": "c06340560a7ea0adb01293a42949dfbac4d1baec",
        "raw_file_count": 66,
        "compressed_total_bytes": 104491346,
        "successful_downloads": 66,
        "automatic_retries": 0,
        "attempted_estimated_cost_usd": (
            22.914097756145
        ),
        "manifest_sha256": (
            "f8fbac395bbe7f9cdafd0187a00c3d77ee8f6ded31d7ba6870d6ed3c8e3007b3"
        ),
        "completion_marker_sha256": (
            "ef8ad499e62284d872edfd480e7aa635a26340e85ba1d74d98a51ed80f71f935"
        ),
        "archive_sha256": (
            "225a64dc06cb6bb303fd83d186f2e7d81e2a8a8bec44382380c8ccc1b0b6baa3"
        ),
    },
    "scope": {
        "local_files_only": True,
        "databento_api_calls": 0,
        "credentials_required": False,
        "files_modified": False,
        "continuous_series_constructed": False,
        "strategy_run": False,
    },
    "hard_failure_checks": (
        "archive_file_count",
        "manifest_file_size",
        "manifest_file_sha256",
        "dbn_readability",
        "ohlcv_1m_schema",
        "nonempty_records",
        "required_columns",
        "single_instrument_id_per_file",
        "timestamps_inside_locked_window",
        "minute_timestamp_alignment",
        "monotonic_timestamp_order",
        "duplicate_timestamps",
        "duplicate_full_rows",
        "finite_ohlcv",
        "ohlc_invariants",
        "negative_volume",
        "nq_quarter_point_tick_alignment",
    ),
    "measured_non_gating_diagnostics": (
        "first_and_last_observed_timestamp",
        "calendar_minute_density",
        "missing_minute_run_count",
        "largest_missing_minute_run",
        "weekend_and_session_gaps",
        "adjacent_contract_overlap_minutes",
        "records_per_contract",
        "instrument_id_by_contract",
    ),
    "missing_minute_interpretation": {
        "absence_is_not_automatically_failure": True,
        "reason": (
            "Databento OHLCV does not print a bar "
            "when no trade occurs in the interval."
        ),
        "provider_condition_evidence_must_be_reported":
            True,
    },
    "known_provider_conditions": {
        "warning_windows_observed": 16,
        "terminal_warning_output_not_exhaustive": True,
        "degraded_examples": (
            "NQM14: 2014-06-11 onward",
            "NQZ14: 2014-09-22 onward",
            "NQH15: 2014-12-31",
            "NQZ17: 2017-11-13",
            "NQZ18: 2018-10-21",
            "NQH19: 2019-01-15, 2019-02-22, "
            "2019-03-13",
            "NQM19: 2019-02-22, 2019-03-13, "
            "2019-03-26",
            "NQH20: 2020-02-27, 2020-02-28",
            "NQU20: 2020-06-30, 2020-07-01",
            "NQZ21: 2021-12-05",
            "NQH22: 2021-12-05, 2022-01-02",
            "NQU25: 2025-09-17",
            "NQZ25: 2025-09-17, 2025-09-24, "
            "2025-11-28",
            "NQH26: 2025-11-28",
            "NQU26: 2026-05-24",
        ),
        "missing_examples": (
            "NQH26: 2026-02-14, 2026-02-21 "
            "and additional truncated dates",
            "NQM26: 2026-02-21, 2026-02-28, "
            "2026-03-07 and additional truncated dates",
        ),
    },
    "classification_rules": {
        "not_qualified": (
            "One or more hard-failure checks fail."
        ),
        "qualified_with_known_provider_conditions": (
            "All hard checks pass and the known "
            "provider warnings remain disclosed."
        ),
        "qualified": (
            "All hard checks pass and there are no "
            "known provider-condition warnings."
        ),
    },
    "prohibited_actions": {
        "redownload": True,
        "api_metadata_request": True,
        "api_timeseries_request": True,
        "continuous_series_construction": True,
        "roll_rule_selection": True,
        "back_adjustment": True,
        "forward_adjustment": True,
        "strategy_replay": True,
        "strategy_optimization": True,
        "paper_trading": True,
        "live_trading": True,
        "changes_to_prior_experiments": True,
    },
    "interpretation_boundaries": {
        "exchange_accuracy_claim": False,
        "best_vendor_claim": False,
        "archive_qualified_before_audit": False,
        "strategy_use_authorized": False,
    },
}


def get_exp019_archive_audit_preregistration():
    return deepcopy(
        EXP019_ARCHIVE_AUDIT_PREREGISTRATION
    )


def validate_exp019_archive_audit_preregistration(
    record=None,
):
    r = (
        EXP019_ARCHIVE_AUDIT_PREREGISTRATION
        if record is None
        else record
    )

    if (
        r["experiment_id"] != "EXP-019"
        or r["locked_date"] != "2026-07-25"
        or r["audit_status"] != "PRE_REGISTERED"
        or r["audit_execution_status"]
        != "NOT_IMPLEMENTED"
        or r["ohlcv_values_examined_before_lock"]
        is not False
    ):
        raise ValueError(
            "EXP-019 audit identity changed."
        )

    evidence = r["acquisition_evidence"]

    if (
        evidence["raw_file_count"] != 66
        or evidence["compressed_total_bytes"]
        != 104491346
        or evidence["successful_downloads"] != 66
        or evidence["automatic_retries"] != 0
        or evidence["manifest_sha256"]
        != "f8fbac395bbe7f9cdafd0187a00c3d77ee8f6ded31d7ba6870d6ed3c8e3007b3"
        or evidence["completion_marker_sha256"]
        != "ef8ad499e62284d872edfd480e7aa635a26340e85ba1d74d98a51ed80f71f935"
        or evidence["archive_sha256"]
        != "225a64dc06cb6bb303fd83d186f2e7d81e2a8a8bec44382380c8ccc1b0b6baa3"
    ):
        raise ValueError(
            "EXP-019 acquisition evidence changed."
        )

    scope = r["scope"]

    if (
        scope["local_files_only"] is not True
        or scope["databento_api_calls"] != 0
        or scope["credentials_required"] is not False
        or scope["files_modified"] is not False
        or scope["continuous_series_constructed"]
        is not False
        or scope["strategy_run"] is not False
    ):
        raise ValueError(
            "EXP-019 audit scope changed."
        )

    if len(
        r["hard_failure_checks"]
    ) != 17:
        raise ValueError(
            "EXP-019 hard-check set changed."
        )

    if (
        r["known_provider_conditions"][
            "warning_windows_observed"
        ]
        != 16
    ):
        raise ValueError(
            "EXP-019 warning evidence changed."
        )

    if not all(
        value is True
        for value in r[
            "prohibited_actions"
        ].values()
    ):
        raise ValueError(
            "EXP-019 audit prohibition changed."
        )

    boundaries = r[
        "interpretation_boundaries"
    ]

    if (
        boundaries["exchange_accuracy_claim"]
        is not False
        or boundaries["best_vendor_claim"]
        is not False
        or boundaries[
            "archive_qualified_before_audit"
        ]
        is not False
        or boundaries[
            "strategy_use_authorized"
        ]
        is not False
    ):
        raise ValueError(
            "EXP-019 interpretation changed."
        )
