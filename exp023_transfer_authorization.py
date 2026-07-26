from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any


EXP023_TRANSFER_AUTHORIZATION: dict[str, Any] = {
    "schema_version": 1,
    "experiment_id": "EXP-023",
    "authorization_id": "EXP-023-TRANSFER-AUTH-001",
    "authorized_date": "2026-07-26",
    "locked_preregistration_commit": (
        "66ba6a46f31cc8715447179c19caf2f4c1a1e8be"
    ),
    "locked_preregistration_sha256": (
        "20c7295123adead63b5e9c398419a3129aa93c4fcd3e597e6e92c295dc2841be"
    ),
    "locked_implementation_commit": (
        "c17e9ea567c234e2d941f949168d62721f6d4963"
    ),
    "candidate_ids": (
        "gap_fade_0p50_1r",
        "premarket_continuation_0p50_time",
        "premarket_continuation_0p75_time",
    ),
    "primary_representation": "BACKWARD_ADJUSTED",
    "secondary_representation": "UNADJUSTED",
    "allowed_session_date_start": "2020-01-03",
    "allowed_session_date_end": "2025-12-31",
    "transfer_execution_authorized": True,
    "one_time_transfer_run": True,
    "maximum_transfer_runs": 1,
    "protected_preflight_authorized": True,
    "execution_mode": "LOCAL_FROZEN_KNOWN_OVERLAP_ONLY",
    "output_directory": "results/EXP-023/transfer_qualification",
    "independent_rebuild_required": True,
    "exp022_output_modification_authorized": False,
    "exp014_output_modification_authorized": False,
    "session_quality_modification_authorized": False,
    "out_of_overlap_access_authorized": False,
    "new_market_data_download_authorized": False,
    "network_access_authorized": False,
    "databento_api_calls": 0,
    "credentials_required": False,
    "strategy_search_authorized": False,
    "strategy_optimization_authorized": False,
    "mcpt_authorized": False,
    "bootstrap_authorized": False,
    "walk_forward_authorized": False,
    "strategy_ranking_authorized": False,
    "paper_trading_authorized": False,
    "live_trading_authorized": False,
    "protected_history_validation_authorized": False,
    "authorization_boundary": (
        "This authorization permits the protected result-free preflight "
        "and exactly one local EXP-023 transfer replay of the three frozen "
        "EXP-014 finalists on the two frozen EXP-022 representations during "
        "only the known 2020-2025 overlap. It permits no rerun, no protected "
        "history access, no search or robustness procedure, no candidate "
        "ranking, and no paper or live trading."
    ),
}

EXPECTED_EXP023_TRANSFER_AUTHORIZATION_SHA256 = (
    "810e04027692a9edc14b05fa2a9326e3bcaa8cce15000ce60ebc2312bed5a55c"
)


def canonical_record_hash(record: dict[str, Any]) -> str:
    encoded = json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def get_exp023_transfer_authorization() -> dict[str, Any]:
    return deepcopy(EXP023_TRANSFER_AUTHORIZATION)


def validate_exp023_transfer_authorization(
    candidate: dict[str, Any] | None = None,
) -> None:
    record = (
        EXP023_TRANSFER_AUTHORIZATION
        if candidate is None
        else candidate
    )
    if (
        record["experiment_id"] != "EXP-023"
        or record["authorization_id"]
        != "EXP-023-TRANSFER-AUTH-001"
        or record["locked_preregistration_commit"]
        != "66ba6a46f31cc8715447179c19caf2f4c1a1e8be"
        or record["locked_implementation_commit"]
        != "c17e9ea567c234e2d941f949168d62721f6d4963"
        or tuple(record["candidate_ids"])
        != (
            "gap_fade_0p50_1r",
            "premarket_continuation_0p50_time",
            "premarket_continuation_0p75_time",
        )
    ):
        raise ValueError("EXP-023 transfer authorization identity changed.")
    if (
        record["transfer_execution_authorized"] is not True
        or record["one_time_transfer_run"] is not True
        or record["maximum_transfer_runs"] != 1
        or record["protected_preflight_authorized"] is not True
        or record["allowed_session_date_start"] != "2020-01-03"
        or record["allowed_session_date_end"] != "2025-12-31"
        or record["out_of_overlap_access_authorized"] is not False
        or record["network_access_authorized"] is not False
        or record["databento_api_calls"] != 0
        or record["strategy_search_authorized"] is not False
        or record["paper_trading_authorized"] is not False
        or record["live_trading_authorized"] is not False
    ):
        raise ValueError("EXP-023 transfer authorization boundary changed.")
    if (
        canonical_record_hash(record)
        != EXPECTED_EXP023_TRANSFER_AUTHORIZATION_SHA256
    ):
        raise ValueError("EXP-023 transfer authorization record changed.")
