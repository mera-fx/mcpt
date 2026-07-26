from __future__ import annotations

from copy import deepcopy


LOCKED_ORIGINAL_AUTHORIZATION_COMMIT = (
    "e497b1abf247ed83295caa9378c2a4e6869922b1"
)

LOCKED_CORRECTED_IMPLEMENTATION_COMMIT = (
    "fde5ee88b306f97b9e567fabe1b12267c9db4ae8"
)

EXP020_PREFLIGHT_CORRECTION_AUTHORIZATION = {
    "schema_version": 1,
    "experiment_id": "EXP-020",
    "correction_id": "EXP-020-PREFLIGHT-DIGEST-001",
    "authorization_date": "2026-07-26",
    "authorization_status": "AUTHORIZED",
    "correction_authorized": True,
    "preflight_authorized": True,
    "original_authorization_commit": (
        LOCKED_ORIGINAL_AUTHORIZATION_COMMIT
    ),
    "locked_corrected_implementation_commit": (
        LOCKED_CORRECTED_IMPLEMENTATION_COMMIT
    ),
    "archive_digest_protocol": (
        "EXP-019_INSERTION_ORDER_JSON_V1"
    ),
    "correction_implementation_files": (
        "exp020_constructor.py",
        "tests/test_exp020_preflight_correction.py",
        (
            "research/"
            "EXP-020_preflight_correction_implementation.md"
        ),
    ),
    "correction_authorization_files": (
        "exp020_preflight_correction_authorization.py",
        (
            "tests/"
            "test_exp020_preflight_correction_authorization.py"
        ),
        (
            "research/"
            "EXP-020_preflight_correction_authorization.md"
        ),
    ),
    "digest_evidence": {
        "frozen_exp019_archive_sha256": (
            "225a64dc06cb6bb303fd83d186f2e7d8"
            "1e2a8a8bec44382380c8ccc1b0b6baa3"
        ),
        "incorrect_sorted_key_sha256": (
            "8734b41f8bc5a3f3773f634323e6d52a"
            "4f2fffd6ef0d161863499c64d7110198"
        ),
        "frozen_digest_matched": True,
        "source_mutation_detected": False,
    },
    "databento_api_calls": 0,
    "credentials_required": False,
    "source_archive_modified": False,
    "source_archive_read_only": True,
    "construction_run": False,
    "construction_authorization_unchanged": True,
    "one_time_construction_limit_unchanged": True,
    "strategy_run_authorized": False,
    "optimization_authorized": False,
    "mcpt_authorized": False,
    "bootstrap_authorized": False,
    "walk_forward_authorized": False,
    "paper_trading_authorized": False,
    "live_trading_authorized": False,
}


def get_exp020_preflight_correction_authorization():
    return deepcopy(
        EXP020_PREFLIGHT_CORRECTION_AUTHORIZATION
    )


def validate_exp020_preflight_correction_authorization(
    candidate=None,
):
    record = (
        EXP020_PREFLIGHT_CORRECTION_AUTHORIZATION
        if candidate is None
        else candidate
    )

    if (
        record["schema_version"] != 1
        or record["experiment_id"] != "EXP-020"
        or record["correction_id"]
        != "EXP-020-PREFLIGHT-DIGEST-001"
        or record["authorization_date"] != "2026-07-26"
        or record["authorization_status"] != "AUTHORIZED"
        or record["correction_authorized"] is not True
        or record["preflight_authorized"] is not True
    ):
        raise ValueError(
            "EXP-020 preflight correction "
            "authorization identity changed."
        )

    if (
        record["original_authorization_commit"]
        != LOCKED_ORIGINAL_AUTHORIZATION_COMMIT
        or record[
            "locked_corrected_implementation_commit"
        ]
        != LOCKED_CORRECTED_IMPLEMENTATION_COMMIT
    ):
        raise ValueError(
            "EXP-020 preflight correction "
            "locked commits changed."
        )

    if (
        record["archive_digest_protocol"]
        != "EXP-019_INSERTION_ORDER_JSON_V1"
    ):
        raise ValueError(
            "EXP-020 archive digest protocol changed."
        )

    if tuple(
        record["correction_implementation_files"]
    ) != (
        "exp020_constructor.py",
        "tests/test_exp020_preflight_correction.py",
        (
            "research/"
            "EXP-020_preflight_correction_implementation.md"
        ),
    ):
        raise ValueError(
            "EXP-020 correction implementation "
            "scope changed."
        )

    if tuple(
        record["correction_authorization_files"]
    ) != (
        "exp020_preflight_correction_authorization.py",
        (
            "tests/"
            "test_exp020_preflight_correction_authorization.py"
        ),
        (
            "research/"
            "EXP-020_preflight_correction_authorization.md"
        ),
    ):
        raise ValueError(
            "EXP-020 correction authorization "
            "scope changed."
        )

    evidence = record["digest_evidence"]

    if (
        evidence["frozen_exp019_archive_sha256"]
        != (
            "225a64dc06cb6bb303fd83d186f2e7d8"
            "1e2a8a8bec44382380c8ccc1b0b6baa3"
        )
        or evidence["incorrect_sorted_key_sha256"]
        != (
            "8734b41f8bc5a3f3773f634323e6d52a"
            "4f2fffd6ef0d161863499c64d7110198"
        )
        or evidence["frozen_digest_matched"] is not True
        or evidence["source_mutation_detected"] is not False
    ):
        raise ValueError(
            "EXP-020 digest evidence changed."
        )

    if (
        record["databento_api_calls"] != 0
        or record["credentials_required"] is not False
        or record["source_archive_modified"] is not False
        or record["source_archive_read_only"] is not True
        or record["construction_run"] is not False
        or record["construction_authorization_unchanged"]
        is not True
        or record["one_time_construction_limit_unchanged"]
        is not True
    ):
        raise ValueError(
            "EXP-020 correction safety boundary changed."
        )

    prohibited = (
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
        for key in prohibited
    ):
        raise ValueError(
            "EXP-020 research or trading permission changed."
        )
