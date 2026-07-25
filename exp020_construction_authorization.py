from __future__ import annotations

from copy import deepcopy


LOCKED_PREREGISTRATION_COMMIT = (
    "93776c52806820e137ec02f7fe6382d8981c4500"
)

LOCKED_IMPLEMENTATION_COMMIT = (
    "36473b354c0b1a200c01494d4b64a78cee1e3430"
)

EXP020_CONSTRUCTION_AUTHORIZATION = {
    "schema_version": 1,
    "experiment_id": "EXP-020",
    "authorization_date": "2026-07-25",
    "authorization_status": "AUTHORIZED",
    "construction_authorized": True,
    "one_time_construction": True,
    "maximum_construction_runs": 1,
    "databento_api_calls": 0,
    "locked_preregistration_commit": (
        LOCKED_PREREGISTRATION_COMMIT
    ),
    "locked_implementation_commit": (
        LOCKED_IMPLEMENTATION_COMMIT
    ),
    "implementation_files": (
        "exp020_constructor.py",
        "exp020_constructor_core.py",
        "tests/test_exp020_constructor.py",
        "research/EXP-020_implementation_report.md",
    ),
    "source_boundary": {
        "source_experiment": "EXP-019",
        "source_classification": (
            "QUALIFIED_WITH_KNOWN_PROVIDER_CONDITIONS"
        ),
        "source_contract_count": 66,
        "source_record_count": 6_276_486,
        "source_archive_read_only": True,
        "archive_sha256": (
            "225a64dc06cb6bb303fd83d186f2e7d8"
            "1e2a8a8bec44382380c8ccc1b0b6baa3"
        ),
    },
    "execution_boundary": {
        "protected_preflight_required": True,
        "clean_main_branch_required": True,
        "head_must_equal_origin_main": True,
        "minimum_free_bytes": 4_000_000_000,
        "databento_api_calls": 0,
        "credentials_required": False,
        "source_archive_modifications": False,
        "independent_rebuild_required": True,
        "completed_output_overwrite_prohibited": True,
        "construction_rerun_prohibited": True,
    },
    "required_outputs": (
        "construction_summary.json",
        "roll_ledger.csv",
        "contract_contribution.csv",
        "method_comparison.csv",
        "volume_roll_unadjusted.parquet",
        "volume_roll_backward_adjusted.parquet",
        "calendar_roll_unadjusted.parquet",
        "calendar_roll_backward_adjusted.parquet",
        "output_hashes.json",
        "report.md",
        "CONSTRUCTION_COMPLETE.json",
    ),
    "expected_hard_check_count": 20,
    "strategy_run_authorized": False,
    "optimization_authorized": False,
    "mcpt_authorized": False,
    "bootstrap_authorized": False,
    "walk_forward_authorized": False,
    "paper_trading_authorized": False,
    "live_trading_authorized": False,
    "interpretation": {
        "data_engineering_only": True,
        "strategy_performance_not_inspected": True,
        "strategy_edge_not_tested": True,
        "exchange_accuracy_not_claimed": True,
        "best_vendor_not_claimed": True,
        "separate_strategy_experiment_required": True,
    },
}


def get_exp020_construction_authorization():
    return deepcopy(
        EXP020_CONSTRUCTION_AUTHORIZATION
    )


def validate_exp020_construction_authorization(
    candidate=None,
):
    record = (
        EXP020_CONSTRUCTION_AUTHORIZATION
        if candidate is None
        else candidate
    )

    if (
        record["experiment_id"] != "EXP-020"
        or record["authorization_date"] != "2026-07-25"
        or record["authorization_status"] != "AUTHORIZED"
        or record["construction_authorized"] is not True
        or record["one_time_construction"] is not True
        or record["maximum_construction_runs"] != 1
        or record["databento_api_calls"] != 0
    ):
        raise ValueError(
            "EXP-020 construction authorization "
            "identity changed."
        )

    if (
        record["locked_preregistration_commit"]
        != LOCKED_PREREGISTRATION_COMMIT
        or record["locked_implementation_commit"]
        != LOCKED_IMPLEMENTATION_COMMIT
    ):
        raise ValueError(
            "EXP-020 locked commits changed."
        )

    if tuple(
        record["implementation_files"]
    ) != (
        "exp020_constructor.py",
        "exp020_constructor_core.py",
        "tests/test_exp020_constructor.py",
        "research/EXP-020_implementation_report.md",
    ):
        raise ValueError(
            "EXP-020 implementation file scope changed."
        )

    source = record["source_boundary"]

    if (
        source["source_experiment"] != "EXP-019"
        or source["source_classification"]
        != "QUALIFIED_WITH_KNOWN_PROVIDER_CONDITIONS"
        or source["source_contract_count"] != 66
        or source["source_record_count"] != 6_276_486
        or source["source_archive_read_only"] is not True
        or source["archive_sha256"]
        != (
            "225a64dc06cb6bb303fd83d186f2e7d8"
            "1e2a8a8bec44382380c8ccc1b0b6baa3"
        )
    ):
        raise ValueError(
            "EXP-020 source boundary changed."
        )

    execution = record["execution_boundary"]

    required_true = (
        "protected_preflight_required",
        "clean_main_branch_required",
        "head_must_equal_origin_main",
        "independent_rebuild_required",
        "completed_output_overwrite_prohibited",
        "construction_rerun_prohibited",
    )

    if not all(
        execution[key] is True
        for key in required_true
    ):
        raise ValueError(
            "EXP-020 execution safeguards changed."
        )

    if (
        execution["minimum_free_bytes"]
        != 4_000_000_000
        or execution["databento_api_calls"] != 0
        or execution["credentials_required"] is not False
        or execution["source_archive_modifications"]
        is not False
    ):
        raise ValueError(
            "EXP-020 execution boundary changed."
        )

    if len(
        tuple(
            record["required_outputs"]
        )
    ) != 11:
        raise ValueError(
            "EXP-020 required output scope changed."
        )

    if record["expected_hard_check_count"] != 20:
        raise ValueError(
            "EXP-020 hard-check count changed."
        )

    prohibited_permissions = (
        "strategy_run_authorized",
        "optimization_authorized",
        "mcpt_authorized",
        "bootstrap_authorized",
        "walk_forward_authorized",
        "paper_trading_authorized",
        "live_trading_authorized",
    )

    if not all(
        record[key] is False
        for key in prohibited_permissions
    ):
        raise ValueError(
            "EXP-020 research or trading permission changed."
        )

    interpretation = record["interpretation"]

    required_interpretation_true = (
        "data_engineering_only",
        "strategy_performance_not_inspected",
        "strategy_edge_not_tested",
        "exchange_accuracy_not_claimed",
        "best_vendor_not_claimed",
        "separate_strategy_experiment_required",
    )

    if not all(
        interpretation[key] is True
        for key in required_interpretation_true
    ):
        raise ValueError(
            "EXP-020 interpretation boundary changed."
        )
