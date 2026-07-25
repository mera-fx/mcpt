from __future__ import annotations

from copy import deepcopy


EXP019_ACQUISITION_AUTHORIZATION = {
    "schema_version": 1,
    "experiment_id": "EXP-019",
    "authorization_date": "2026-07-25",
    "authorization_status": (
        "AUTHORIZED_FOR_ONE_TIME_"
        "EXACT_CONTRACT_ACQUISITION"
    ),
    "authorization_source": (
        "explicit_user_approval_in_"
        "project_conversation"
    ),
    "cost_estimate": {
        "classification": (
            "EXACT_CONTRACT_COST_ESTIMATE_COMPLETE"
        ),
        "contract_count": 66,
        "quote_calls": 66,
        "quoted_total_usd": 22.914098,
        "maximum_total_cost_usd": 35.0,
        "within_locked_cap": True,
        "automatic_retries": 0,
        "bar_records_downloaded": 0,
        "estimator_commit": "d75fdb296cc6e916ba9016c0e549c20bb905d376",
        "cost_json_sha256": "a99aec4804e3be9e256dabbea6885f133727fe3b50045d9c51cfd1e7c165dad3",
        "cost_csv_sha256": "8a8598f04c953ebe8ac38e4fc13eb232f4102ebebebe03389d12b9220bd4d9cc",
    },
    "authorized_acquisition": {
        "explicit_user_approval": True,
        "exact_locked_windows_only": True,
        "maximum_successful_downloads": 66,
        "maximum_total_cost_usd": 35.0,
        "one_time_acquisition": True,
        "automatic_retry_prohibited": True,
        "stop_on_first_error": True,
        "manual_resume_after_failure_allowed": True,
        "completed_contracts_must_not_be_redownloaded": True,
        "credentials_environment_only": True,
    },
    "storage": {
        "format": "DBN",
        "compression": "zstd",
        "one_file_per_contract_window": True,
        "raw_root": (
            "data/EXP-019/"
            "exact_contract_archive/raw"
        ),
        "manifest_path": (
            "data/EXP-019/"
            "exact_contract_archive/"
            "acquisition_manifest.json"
        ),
        "completion_marker": (
            "data/EXP-019/"
            "exact_contract_archive/"
            "ACQUISITION_COMPLETE.json"
        ),
        "raw_files_local_and_gitignored": True,
        "sha256_required_for_every_file": True,
        "atomic_partial_file_required": True,
    },
    "prohibited_actions": {
        "continuous_symbol_download": True,
        "unlocked_contract_window": True,
        "automatic_retry": True,
        "overwrite_completed_file": True,
        "continuous_series_construction": True,
        "back_adjustment": True,
        "forward_adjustment": True,
        "strategy_replay": True,
        "strategy_optimization": True,
        "paper_trading": True,
        "live_trading": True,
        "changes_to_prior_experiments": True,
    },
    "post_acquisition_boundary": {
        "archive_qualified": False,
        "audit_required_before_use": True,
        "continuous_series_constructed": False,
        "strategy_use_authorized": False,
        "paper_trading_authorized": False,
        "live_trading_authorized": False,
    },
}


def get_exp019_acquisition_authorization():
    return deepcopy(
        EXP019_ACQUISITION_AUTHORIZATION
    )


def validate_exp019_acquisition_authorization(
    record=None,
):
    r = (
        EXP019_ACQUISITION_AUTHORIZATION
        if record is None
        else record
    )

    if (
        r["experiment_id"] != "EXP-019"
        or r["authorization_date"]
        != "2026-07-25"
        or r["authorization_status"]
        != (
            "AUTHORIZED_FOR_ONE_TIME_"
            "EXACT_CONTRACT_ACQUISITION"
        )
    ):
        raise ValueError(
            "EXP-019 authorization identity changed."
        )

    estimate = r["cost_estimate"]

    if (
        estimate["contract_count"] != 66
        or estimate["quote_calls"] != 66
        or estimate["quoted_total_usd"]
        != 22.914098
        or estimate[
            "maximum_total_cost_usd"
        ]
        != 35.0
        or estimate["within_locked_cap"]
        is not True
        or estimate["bar_records_downloaded"]
        != 0
    ):
        raise ValueError(
            "EXP-019 cost evidence changed."
        )

    authorization = r[
        "authorized_acquisition"
    ]

    if (
        authorization[
            "explicit_user_approval"
        ]
        is not True
        or authorization[
            "exact_locked_windows_only"
        ]
        is not True
        or authorization[
            "maximum_successful_downloads"
        ]
        != 66
        or authorization[
            "maximum_total_cost_usd"
        ]
        != 35.0
        or authorization[
            "automatic_retry_prohibited"
        ]
        is not True
        or authorization[
            "stop_on_first_error"
        ]
        is not True
    ):
        raise ValueError(
            "EXP-019 acquisition authorization changed."
        )

    if not all(
        value is True
        for value in r[
            "prohibited_actions"
        ].values()
    ):
        raise ValueError(
            "EXP-019 prohibited actions changed."
        )

    boundary = r[
        "post_acquisition_boundary"
    ]

    if (
        boundary["archive_qualified"]
        is not False
        or boundary[
            "audit_required_before_use"
        ]
        is not True
        or boundary[
            "strategy_use_authorized"
        ]
        is not False
    ):
        raise ValueError(
            "EXP-019 post-acquisition boundary changed."
        )
