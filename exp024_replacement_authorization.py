from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any


EXP024_REPLACEMENT_AUTHORIZATION: dict[str, Any] = {
    "schema_version": 1,
    "experiment_id": "EXP-024",
    "authorization_id": "EXP-024-ATTRIBUTION-AUTH-002",
    "authorized_date": "2026-07-26",
    "user_instruction": "authorize",
    "locked_preregistration_commit": (
        "37a6d007b103bb5baddfdbbe471a8b6626b8a35c"
    ),
    "locked_preregistration_sha256": (
        "6bc6b7b493aa5eb4a58699fd8cd2c0af"
        "15d6c8cfe5323edf9cb3bba1193e3871"
    ),
    "original_implementation_commit": (
        "34f7d4c83dee025108229d5247e9cb4f87398a59"
    ),
    "original_authorization_commit": (
        "55ae174f5517bdb5afc48f5a36f5268fbc1eb42a"
    ),
    "original_authorization_id": "EXP-024-ATTRIBUTION-AUTH-001",
    "original_authorization_consumed": True,
    "failed_attempt_id": "EXP-024-ATTEMPT-001",
    "failed_attempt_record_sha256": (
        "556854e35ac217f62677cf15d3e6c03ab"
        "f38414bd65585d9decd441154f7be17"
    ),
    "failed_attempt_attribution_calculated": False,
    "locked_replacement_implementation_commit": (
        "fb5b8f02ac54cccf29c5d23452db6d8e9ac4589e"
    ),
    "replacement_change": (
        "Restore the already-projected Quantower timestamp field from its "
        "named pandas index to a regular column after Arrow-to-pandas "
        "conversion; no row predicate, projection, feature, threshold, "
        "attribution or output rule changes."
    ),
    "candidate_ids": (
        "gap_fade_0p50_1r",
        "premarket_continuation_0p50_time",
        "premarket_continuation_0p75_time",
    ),
    "candidate_session_row_count": 51,
    "unique_session_count": 51,
    "primary_representation": "BACKWARD_ADJUSTED",
    "secondary_representation": "UNADJUSTED",
    "allowed_session_date_start": "2020-01-03",
    "allowed_session_date_end": "2025-12-31",
    "allowed_current_premarket_window_new_york": (
        "08:00:00 through 09:29:59"
    ),
    "allowed_current_first_cash_bar_new_york": (
        "09:30:00 through 09:34:59"
    ),
    "allowed_current_entry_field": "09:35:00 open only",
    "allowed_previous_gap_cash_window_new_york": (
        "09:30:00 through 15:59:59"
    ),
    "replacement_execution_authorized": True,
    "one_time_replacement_run": True,
    "maximum_replacement_runs": 1,
    "protected_preflight_authorized": True,
    "execution_mode": (
        "LOCAL_FROZEN_MISMATCH_ENTRY_FEATURES_ONLY"
    ),
    "output_directory": (
        "results/EXP-024/source_disagreement_attribution"
    ),
    "independent_rebuild_required": True,
    "exp023_output_modification_authorized": False,
    "exp022_output_modification_authorized": False,
    "quantower_output_modification_authorized": False,
    "session_quality_modification_authorized": False,
    "failed_attempt_record_modification_authorized": False,
    "out_of_overlap_access_authorized": False,
    "non_mismatch_session_access_authorized": False,
    "current_post_entry_access_authorized": False,
    "volume_access_authorized": False,
    "new_market_data_download_authorized": False,
    "network_access_authorized": False,
    "databento_api_calls": 0,
    "credentials_required": False,
    "strategy_replay_authorized": False,
    "exit_evaluation_authorized": False,
    "pnl_return_equity_evaluation_authorized": False,
    "strategy_search_authorized": False,
    "optimization_authorized": False,
    "mcpt_authorized": False,
    "bootstrap_authorized": False,
    "walk_forward_authorized": False,
    "candidate_ranking_authorized": False,
    "source_winner_selection_authorized": False,
    "protected_history_validation_authorized": False,
    "paper_trading_authorized": False,
    "live_trading_authorized": False,
    "authorization_boundary": (
        "This replacement authorization permits exactly one corrected local "
        "EXP-024 attribution attempt after attempt 001 failed before any "
        "feature reconstruction or attribution. It preserves the exact 51 "
        "rows, locked entry-decision windows, two internal deterministic "
        "rebuilds, 26 hard checks and evidence outputs. It permits no other "
        "retry, no broader values, no strategy or performance replay, no "
        "source or candidate selection, no protected-history test, and no "
        "paper or live trading."
    ),
}

EXPECTED_EXP024_REPLACEMENT_AUTHORIZATION_SHA256 = (
    "fc25ad90bca377a0d103f8c4eec6d0b40ba179de9b13ceee721587747a466fb3"
)


def canonical_record_hash(record: dict[str, Any]) -> str:
    encoded = json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def get_exp024_replacement_authorization() -> dict[str, Any]:
    return deepcopy(EXP024_REPLACEMENT_AUTHORIZATION)


def validate_exp024_replacement_authorization(
    candidate: dict[str, Any] | None = None,
) -> None:
    record = (
        EXP024_REPLACEMENT_AUTHORIZATION
        if candidate is None
        else candidate
    )
    if (
        record["experiment_id"] != "EXP-024"
        or record["authorization_id"]
        != "EXP-024-ATTRIBUTION-AUTH-002"
        or record["original_authorization_commit"]
        != "55ae174f5517bdb5afc48f5a36f5268fbc1eb42a"
        or record["original_authorization_id"]
        != "EXP-024-ATTRIBUTION-AUTH-001"
        or record["failed_attempt_id"] != "EXP-024-ATTEMPT-001"
        or record["locked_replacement_implementation_commit"]
        != "fb5b8f02ac54cccf29c5d23452db6d8e9ac4589e"
        or tuple(record["candidate_ids"])
        != (
            "gap_fade_0p50_1r",
            "premarket_continuation_0p50_time",
            "premarket_continuation_0p75_time",
        )
        or record["candidate_session_row_count"] != 51
        or record["unique_session_count"] != 51
    ):
        raise ValueError(
            "EXP-024 replacement authorization identity changed."
        )
    if (
        record["original_authorization_consumed"] is not True
        or record["failed_attempt_attribution_calculated"] is not False
        or record["replacement_execution_authorized"] is not True
        or record["one_time_replacement_run"] is not True
        or record["maximum_replacement_runs"] != 1
        or record["protected_preflight_authorized"] is not True
        or record["allowed_session_date_start"] != "2020-01-03"
        or record["allowed_session_date_end"] != "2025-12-31"
        or record["out_of_overlap_access_authorized"] is not False
        or record["non_mismatch_session_access_authorized"] is not False
        or record["current_post_entry_access_authorized"] is not False
        or record["volume_access_authorized"] is not False
        or record["network_access_authorized"] is not False
        or record["databento_api_calls"] != 0
        or record["strategy_replay_authorized"] is not False
        or record["exit_evaluation_authorized"] is not False
        or record["pnl_return_equity_evaluation_authorized"] is not False
        or record["strategy_search_authorized"] is not False
        or record["optimization_authorized"] is not False
        or record["source_winner_selection_authorized"] is not False
        or record["paper_trading_authorized"] is not False
        or record["live_trading_authorized"] is not False
    ):
        raise ValueError(
            "EXP-024 replacement authorization boundary changed."
        )
    if (
        canonical_record_hash(record)
        != EXPECTED_EXP024_REPLACEMENT_AUTHORIZATION_SHA256
    ):
        raise ValueError(
            "EXP-024 replacement authorization record changed."
        )
