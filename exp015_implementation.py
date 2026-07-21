from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from exp015_preregistration import validate_exp015_preregistration


PROJECT_DIR = Path(__file__).resolve().parent
PROBE_ROOT = PROJECT_DIR / "data" / "EXP-015" / "lse_client_probe"
PROBE_VENV = PROBE_ROOT / "venv"
PACKAGE_CACHE = PROBE_ROOT / "package_cache"
PROBE_MANIFEST = PROBE_ROOT / "probe_manifest.json"

RESULT_DIR = (
    PROJECT_DIR / "results" / "EXP-015" / "source_qualification"
)
CATALOG_STAGING_FILE = RESULT_DIR / ".catalog_rows_staging.json"
CATALOG_RESULT_FILE = RESULT_DIR / "catalog_result.json"
CATALOG_ROWS_FILE = RESULT_DIR / "catalog_rows.csv"

EXPECTED_PREREGISTRATION_COMMIT = (
    "1a615f222b46e98e19009c411b5a6d73ca85d201"
)
EXPECTED_CLIENT_VERSION = "0.14.0"
EXPECTED_CLIENT_WHEEL = "lse_data-0.14.0-py3-none-any.whl"
EXPECTED_CLIENT_WHEEL_SHA256 = (
    "b1e2f34af882ace2d8dab6fb5fe2b45d0bd6b1f1f39d95d71c3aeb4a56aac1a0"
)
EXPECTED_CLIENT_SOURCE_COMMIT = (
    "564c63dd99e3b447777cb396314ec6c4342f82ff"
)


EXP015_IMPLEMENTATION: dict[str, Any] = {
    "schema_version": 1,
    "experiment_id": "EXP-015",
    "implementation_status": "IMPLEMENTED_NOT_RUN",
    "expected_preregistration_commit": EXPECTED_PREREGISTRATION_COMMIT,
    "client_lock": {
        "distribution": "lse-data",
        "version": EXPECTED_CLIENT_VERSION,
        "wheel_filename": EXPECTED_CLIENT_WHEEL,
        "wheel_sha256": EXPECTED_CLIENT_WHEEL_SHA256,
        "source_repository": "londonstrategicedge/lse-data",
        "source_commit": EXPECTED_CLIENT_SOURCE_COMMIT,
        "requires_python": ">=3.8",
        "required_dependency": "websockets>=11.0",
        "main_environment_install_prohibited": True,
    },
    "runner_modes": {
        "preflight": True,
        "probe_client": True,
        "catalog": True,
        "history": False,
        "strategy_replay": False,
        "modes_mutually_exclusive": True,
    },
    "probe_boundary": {
        "isolated_venv_under_ignored_data_directory": True,
        "exact_wheel_download": True,
        "wheel_hash_verified_before_install": True,
        "real_api_key_removed_from_probe_environment": True,
        "client_constructed_with_non_secret_dummy_key": True,
        "network_market_data_call": False,
        "probe_manifest_written_locally": True,
    },
    "catalog_boundary": {
        "requires_clean_committed_implementation": True,
        "requires_successful_probe_manifest": True,
        "api_key_environment_variable": "LSE_API_KEY",
        "api_key_never_printed_or_written": True,
        "official_client_only": True,
        "only_allowed_remote_method": "catalog('futures')",
        "candles_call_prohibited": True,
        "history_call_prohibited": True,
        "dataset_call_prohibited": True,
        "stream_call_prohibited": True,
        "one_time_final_catalog_result": True,
        "history_phase_automatically_starts": False,
    },
    "catalog_outputs": {
        "staging_json": str(CATALOG_STAGING_FILE.relative_to(PROJECT_DIR)),
        "result_json": str(CATALOG_RESULT_FILE.relative_to(PROJECT_DIR)),
        "rows_csv": str(CATALOG_ROWS_FILE.relative_to(PROJECT_DIR)),
        "output_root_is_gitignored": True,
        "raw_secret_headers_saved": False,
        "catalog_rows_preserved": True,
        "canonical_sort": ["category", "dataset", "symbol", "name"],
    },
    "identity_policy": {
        "candidate_discovery_is_not_identity_resolution": True,
        "symbol_guessing_prohibited": True,
        "catalog_alone_cannot_resolve_roll_method_unless_metadata_supplies_it": True,
        "catalog_only_classifications": [
            "CATALOG_UNAVAILABLE",
            "IDENTITY_UNRESOLVED",
        ],
        "history_download_from_catalog_mode": False,
    },
    "prior_research_protection": {
        "verify_exp014_frozen_result_before_external_access": True,
        "no_prior_data_write_paths": True,
        "no_prior_result_write_paths": True,
        "no_strategy_engine_import_in_catalog_worker": True,
        "no_parameter_or_candidate_search": True,
        "paper_trading_authorized": False,
        "live_trading_authorized": False,
    },
}


def get_exp015_implementation() -> dict[str, Any]:
    return deepcopy(EXP015_IMPLEMENTATION)


def validate_exp015_implementation(
    record: dict[str, Any] | None = None,
) -> None:
    validate_exp015_preregistration()
    current = EXP015_IMPLEMENTATION if record is None else record

    if (
        current.get("schema_version") != 1
        or current.get("experiment_id") != "EXP-015"
        or current.get("implementation_status") != "IMPLEMENTED_NOT_RUN"
        or current.get("expected_preregistration_commit")
        != EXPECTED_PREREGISTRATION_COMMIT
    ):
        raise ValueError("EXP-015 implementation identity changed.")

    client = current["client_lock"]
    if (
        client["distribution"] != "lse-data"
        or client["version"] != EXPECTED_CLIENT_VERSION
        or client["wheel_filename"] != EXPECTED_CLIENT_WHEEL
        or client["wheel_sha256"] != EXPECTED_CLIENT_WHEEL_SHA256
        or client["source_commit"] != EXPECTED_CLIENT_SOURCE_COMMIT
        or client["main_environment_install_prohibited"] is not True
    ):
        raise ValueError("EXP-015 client lock changed.")

    modes = current["runner_modes"]
    if (
        modes
        != {
            "preflight": True,
            "probe_client": True,
            "catalog": True,
            "history": False,
            "strategy_replay": False,
            "modes_mutually_exclusive": True,
        }
    ):
        raise ValueError("EXP-015 runner modes changed.")

    probe = current["probe_boundary"]
    if (
        probe["isolated_venv_under_ignored_data_directory"] is not True
        or probe["exact_wheel_download"] is not True
        or probe["wheel_hash_verified_before_install"] is not True
        or probe["real_api_key_removed_from_probe_environment"] is not True
        or probe["client_constructed_with_non_secret_dummy_key"] is not True
        or probe["network_market_data_call"] is not False
    ):
        raise ValueError("EXP-015 probe boundary changed.")

    catalog = current["catalog_boundary"]
    if (
        catalog["requires_clean_committed_implementation"] is not True
        or catalog["requires_successful_probe_manifest"] is not True
        or catalog["api_key_environment_variable"] != "LSE_API_KEY"
        or catalog["api_key_never_printed_or_written"] is not True
        or catalog["only_allowed_remote_method"] != "catalog('futures')"
        or catalog["candles_call_prohibited"] is not True
        or catalog["history_call_prohibited"] is not True
        or catalog["dataset_call_prohibited"] is not True
        or catalog["stream_call_prohibited"] is not True
        or catalog["history_phase_automatically_starts"] is not False
    ):
        raise ValueError("EXP-015 catalog boundary changed.")

    identity = current["identity_policy"]
    if (
        identity["candidate_discovery_is_not_identity_resolution"] is not True
        or identity["symbol_guessing_prohibited"] is not True
        or identity[
            "catalog_alone_cannot_resolve_roll_method_unless_metadata_supplies_it"
        ]
        is not True
        or identity["catalog_only_classifications"]
        != ["CATALOG_UNAVAILABLE", "IDENTITY_UNRESOLVED"]
        or identity["history_download_from_catalog_mode"] is not False
    ):
        raise ValueError("EXP-015 identity policy changed.")

    protection = current["prior_research_protection"]
    if (
        protection["verify_exp014_frozen_result_before_external_access"]
        is not True
        or protection["no_prior_data_write_paths"] is not True
        or protection["no_prior_result_write_paths"] is not True
        or protection["no_strategy_engine_import_in_catalog_worker"] is not True
        or protection["no_parameter_or_candidate_search"] is not True
        or protection["paper_trading_authorized"] is not False
        or protection["live_trading_authorized"] is not False
    ):
        raise ValueError("EXP-015 prior-research protection changed.")
