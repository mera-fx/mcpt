from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any


EXP025_QUANTOWER_EXPORT_AUTHORIZATION: dict[str, Any] = {'schema_version': 1,
 'experiment_id': 'EXP-025',
 'authorization_id': 'EXP-025-QUANTOWER-EXPORT-AUTH-001',
 'authorized_date': '2026-07-27',
 'preregistration_commit': '1d736705a41d0208e353fb17710c8a16cc937710',
 'preregistration_sha256': '7534f8ba59a57e79ec98067b3fda3606e5b327a2320c82805cf8001f8c6dd5aa',
 'implementation_commit': '2011745145b9799a4a42b556d57780002d30e317',
 'session_quality_sha256': '6b55077783ad2c1cd8ef99f10d50ed7d691aad7cafcdb7e8fa37639d90724712',
 'export_plan_path': 'research/EXP-025_quantower_export_plan.csv',
 'export_plan_sha256': 'd716978b28b98f01798760e8298bf7217585a9f5397da068d1893dd28781e6de',
 'population_rows': 43,
 'unique_session_count': 43,
 'unique_contract_count': 22,
 'candidate_id': 'gap_fade_0p50_1r',
 'source': 'Lucid/Rithmic via Quantower History Exporter',
 'resolution': '1 minute',
 'research_timezone': 'America/New_York',
 'required_columns': ('timestamp',
                      'open',
                      'high',
                      'low',
                      'close',
                      'volume',
                      'explicit_contract_symbol'),
 'previous_cash_window_new_york': '09:30:00 through 15:59:00',
 'current_entry_window_new_york': '09:30:00 through 09:35:00',
 'quantower_history_access_authorized': True,
 'manual_history_export_authorized': True,
 'one_export_phase_authorized': True,
 'maximum_export_phases': 1,
 'authorized_window_export_count': 86,
 'authorized_final_file_count': 43,
 'format_verification_pair_authorized': True,
 'staging_directory': 'data/EXP-025/quantower_export_staging',
 'final_directory': 'data/EXP-025/quantower_exact_contract_exports',
 'final_manifest_path': 'data/EXP-025/quantower_exact_contract_exports/export_manifest.json',
 'explicit_quarterly_contract_required': True,
 'same_contract_as_frozen_plan_required': True,
 'continuous_symbol_authorized': False,
 'out_of_population_export_authorized': False,
 'out_of_window_export_authorized': False,
 'current_post_0935_export_authorized': False,
 'missing_bar_fill_authorized': False,
 'bar_repair_authorized': False,
 'synthetic_bar_authorized': False,
 'contract_reselection_authorized': False,
 'python_network_access_authorized': False,
 'databento_api_calls_authorized': 0,
 'new_databento_download_authorized': False,
 'order_api_access_authorized': False,
 'strategy_replay_authorized': False,
 'diagnostic_execution_authorized': False,
 'performance_calculation_authorized': False,
 'strategy_search_authorized': False,
 'strategy_optimization_authorized': False,
 'mcpt_authorized': False,
 'bootstrap_authorized': False,
 'walk_forward_authorized': False,
 'paper_trading_authorized': False,
 'live_trading_authorized': False,
 'authorization_boundary': 'This record authorizes one manual Quantower export phase '
                           'for exactly the 43 frozen EXP-025 sessions and their two '
                           'permitted windows. It authorizes no diagnostic execution, '
                           'performance calculation, strategy research, Databento '
                           'request, order access, paper trading or live trading.'}

EXPECTED_EXP025_QUANTOWER_EXPORT_AUTHORIZATION_SHA256 = (
    "bfc06527f421002e54adaed83c1a2d5136c877dd6ef86906aefb6c081ba2b607"
)


def canonical_record_hash(record: dict[str, Any]) -> str:
    encoded = json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def get_exp025_quantower_export_authorization() -> dict[str, Any]:
    return deepcopy(EXP025_QUANTOWER_EXPORT_AUTHORIZATION)


def validate_exp025_quantower_export_authorization(
    candidate: dict[str, Any] | None = None,
) -> None:
    record = (
        EXP025_QUANTOWER_EXPORT_AUTHORIZATION
        if candidate is None
        else candidate
    )

    if (
        record.get("experiment_id") != "EXP-025"
        or record.get("authorization_id")
        != "EXP-025-QUANTOWER-EXPORT-AUTH-001"
        or record.get("preregistration_commit")
        != "1d736705a41d0208e353fb17710c8a16cc937710"
        or record.get("preregistration_sha256")
        != "7534f8ba59a57e79ec98067b3fda3606e5b327a2320c82805cf8001f8c6dd5aa"
        or record.get("implementation_commit")
        != "2011745145b9799a4a42b556d57780002d30e317"
        or record.get("session_quality_sha256")
        != "6b55077783ad2c1cd8ef99f10d50ed7d691aad7cafcdb7e8fa37639d90724712"
        or record.get("export_plan_sha256")
        != "d716978b28b98f01798760e8298bf7217585a9f5397da068d1893dd28781e6de"
        or record.get("population_rows") != 43
        or record.get("unique_session_count") != 43
        or record.get("authorized_window_export_count") != 86
        or record.get("authorized_final_file_count") != 43
    ):
        raise ValueError(
            "EXP-025 Quantower export authorization identity changed."
        )

    required_true = (
        "quantower_history_access_authorized",
        "manual_history_export_authorized",
        "one_export_phase_authorized",
        "format_verification_pair_authorized",
        "explicit_quarterly_contract_required",
        "same_contract_as_frozen_plan_required",
    )
    if any(record.get(key) is not True for key in required_true):
        raise ValueError(
            "EXP-025 Quantower export authorization boundary changed."
        )

    required_false = (
        "continuous_symbol_authorized",
        "out_of_population_export_authorized",
        "out_of_window_export_authorized",
        "current_post_0935_export_authorized",
        "missing_bar_fill_authorized",
        "bar_repair_authorized",
        "synthetic_bar_authorized",
        "contract_reselection_authorized",
        "python_network_access_authorized",
        "new_databento_download_authorized",
        "order_api_access_authorized",
        "strategy_replay_authorized",
        "diagnostic_execution_authorized",
        "performance_calculation_authorized",
        "strategy_search_authorized",
        "strategy_optimization_authorized",
        "mcpt_authorized",
        "bootstrap_authorized",
        "walk_forward_authorized",
        "paper_trading_authorized",
        "live_trading_authorized",
    )
    if any(record.get(key) is not False for key in required_false):
        raise ValueError(
            "EXP-025 Quantower export authorization boundary changed."
        )

    if (
        record.get("maximum_export_phases") != 1
        or record.get("databento_api_calls_authorized") != 0
        or tuple(record.get("required_columns", ()))
        != ('timestamp', 'open', 'high', 'low', 'close', 'volume', 'explicit_contract_symbol')
    ):
        raise ValueError(
            "EXP-025 Quantower export authorization boundary changed."
        )

    if (
        canonical_record_hash(record)
        != EXPECTED_EXP025_QUANTOWER_EXPORT_AUTHORIZATION_SHA256
    ):
        raise ValueError(
            "EXP-025 Quantower export authorization record changed."
        )
