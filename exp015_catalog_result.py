from __future__ import annotations

from copy import deepcopy
import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from exp015_implementation import (
    CATALOG_RESULT_FILE,
    CATALOG_ROWS_FILE,
    CATALOG_STAGING_FILE,
    EXPECTED_CLIENT_WHEEL_SHA256,
    validate_exp015_implementation,
)
from exp015_preregistration import validate_exp015_preregistration


EXPECTED_IMPLEMENTATION_COMMIT = (
    "8a74b9a49e95693f260f985df1300f545eedd1e7"
)
EXPECTED_CREATED_AT_UTC = "2026-07-21T16:09:33.885155+00:00"
EXPECTED_CATALOG_JSON_SHA256 = (
    "ba9595726de4018f4b283436c447e5aabd5dfa2109b5296c0a8e41159b3028e5"
)
EXPECTED_CATALOG_CSV_SHA256 = (
    "e191b695ae833984f781236e93551f102218937e5b10f2adb85358f996a5980a"
)
EXPECTED_CATALOG_CANONICAL_SHA256 = (
    "55d5b8057c8b0b50e416d2a4f1601c86296992e334020d239114ade8dd45fceb"
)

EXPECTED_NQ_CANDIDATE: dict[str, Any] = {
    "symbol": "NQ.F",
    "name": "Nasdaq 100 Futures",
    "category": "Futures",
    "dataset": "futures",
    "ticks": 3533260,
    "first": "2016-05-29 22:01:00.000000",
    "last": "2026-07-20 19:58:00.000000",
    "country": "United States",
    "discovery_flags": {
        "nq_token": True,
        "mnq_token": False,
        "nasdaq_name": True,
        "micro_name": False,
    },
}

EXP015_CATALOG_FREEZE: dict[str, Any] = {
    "schema_version": 1,
    "experiment_id": "EXP-015",
    "result_status": "CATALOG_MEASURED_REVIEW",
    "result_phase": "CATALOG_ONLY",
    "created_at_utc": EXPECTED_CREATED_AT_UTC,
    "git": {
        "commit": EXPECTED_IMPLEMENTATION_COMMIT,
        "short_commit": "8a74b9a",
        "working_tree_clean": True,
    },
    "file_hashes": {
        "catalog_result_json_sha256": EXPECTED_CATALOG_JSON_SHA256,
        "catalog_rows_csv_sha256": EXPECTED_CATALOG_CSV_SHA256,
        "catalog_canonical_sha256": EXPECTED_CATALOG_CANONICAL_SHA256,
    },
    "client_probe": {
        "status": "PASS",
        "distribution": "lse-data",
        "version": "0.14.0",
        "python_version": "3.14.6",
        "wheel_sha256": EXPECTED_CLIENT_WHEEL_SHA256,
        "real_api_key_used": False,
        "network_market_data_call": False,
        "main_project_environment_modified": False,
    },
    "catalog_measurement": {
        "category_requested": "futures",
        "futures_catalog_rows": 69,
        "nq_candidate_count": 1,
        "mnq_candidate_count": 0,
        "nq_candidate": EXPECTED_NQ_CANDIDATE,
        "mnq_candidates": [],
    },
    "assessment": {
        "classification": "IDENTITY_UNRESOLVED",
        "classification_scope": "NQ_MNQ_ONE_MINUTE_HISTORICAL_RESEARCH",
        "nq_identified": False,
        "mnq_identified": False,
        "contract_method_resolved": False,
        "roll_method_resolved": False,
        "price_adjustment_resolved": False,
        "history_download_authorized": False,
        "all_vendor_data_qualified": False,
        "paper_trading_authorized": False,
        "live_trading_authorized": False,
    },
    "interpretation": {
        "nq_f_found_as_catalog_candidate": True,
        "nq_f_identity_not_fully_resolved": True,
        "mnq_not_found": True,
        "candidate_discovery_is_not_identity_resolution": True,
        "london_strategic_edge_not_qualified_as_primary_nq_mnq_source": True,
        "frozen_quantower_data_replaced": False,
        "history_downloaded": False,
        "strategy_replay_run": False,
        "automatic_all_data_claim": False,
        "expected_lifecycle_after_measurement": "REVIEW",
        "paper_trading_authorized": False,
        "live_trading_authorized": False,
    },
}


def get_exp015_catalog_freeze() -> dict[str, Any]:
    return deepcopy(EXP015_CATALOG_FREEZE)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def _load_csv(path: Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def validate_exp015_catalog_freeze(
    record: Mapping[str, Any] | None = None,
) -> None:
    validate_exp015_preregistration()
    validate_exp015_implementation()
    current = EXP015_CATALOG_FREEZE if record is None else record

    if (
        current.get("schema_version") != 1
        or current.get("experiment_id") != "EXP-015"
        or current.get("result_status") != "CATALOG_MEASURED_REVIEW"
        or current.get("result_phase") != "CATALOG_ONLY"
        or current.get("created_at_utc") != EXPECTED_CREATED_AT_UTC
    ):
        raise ValueError("EXP-015 catalog result identity changed.")

    git = current["git"]
    if (
        git["commit"] != EXPECTED_IMPLEMENTATION_COMMIT
        or git["short_commit"] != "8a74b9a"
        or git["working_tree_clean"] is not True
    ):
        raise ValueError("EXP-015 implementation provenance changed.")

    hashes = current["file_hashes"]
    if (
        hashes["catalog_result_json_sha256"]
        != EXPECTED_CATALOG_JSON_SHA256
        or hashes["catalog_rows_csv_sha256"]
        != EXPECTED_CATALOG_CSV_SHA256
        or hashes["catalog_canonical_sha256"]
        != EXPECTED_CATALOG_CANONICAL_SHA256
    ):
        raise ValueError("EXP-015 frozen catalog hashes changed.")

    probe = current["client_probe"]
    if (
        probe["status"] != "PASS"
        or probe["distribution"] != "lse-data"
        or probe["version"] != "0.14.0"
        or probe["python_version"] != "3.14.6"
        or probe["wheel_sha256"] != EXPECTED_CLIENT_WHEEL_SHA256
        or probe["real_api_key_used"] is not False
        or probe["network_market_data_call"] is not False
        or probe["main_project_environment_modified"] is not False
    ):
        raise ValueError("EXP-015 isolated client probe evidence changed.")

    catalog = current["catalog_measurement"]
    if (
        catalog["category_requested"] != "futures"
        or catalog["futures_catalog_rows"] != 69
        or catalog["nq_candidate_count"] != 1
        or catalog["mnq_candidate_count"] != 0
        or catalog["nq_candidate"] != EXPECTED_NQ_CANDIDATE
        or catalog["mnq_candidates"] != []
    ):
        raise ValueError("EXP-015 catalog measurement changed.")

    assessment = current["assessment"]
    if (
        assessment["classification"] != "IDENTITY_UNRESOLVED"
        or assessment["classification_scope"]
        != "NQ_MNQ_ONE_MINUTE_HISTORICAL_RESEARCH"
        or assessment["nq_identified"] is not False
        or assessment["mnq_identified"] is not False
        or assessment["contract_method_resolved"] is not False
        or assessment["roll_method_resolved"] is not False
        or assessment["price_adjustment_resolved"] is not False
        or assessment["history_download_authorized"] is not False
        or assessment["all_vendor_data_qualified"] is not False
        or assessment["paper_trading_authorized"] is not False
        or assessment["live_trading_authorized"] is not False
    ):
        raise ValueError("EXP-015 qualification assessment changed.")

    interpretation = current["interpretation"]
    if (
        interpretation["nq_f_found_as_catalog_candidate"] is not True
        or interpretation["nq_f_identity_not_fully_resolved"] is not True
        or interpretation["mnq_not_found"] is not True
        or interpretation[
            "candidate_discovery_is_not_identity_resolution"
        ]
        is not True
        or interpretation[
            "london_strategic_edge_not_qualified_as_primary_nq_mnq_source"
        ]
        is not True
        or interpretation["frozen_quantower_data_replaced"] is not False
        or interpretation["history_downloaded"] is not False
        or interpretation["strategy_replay_run"] is not False
        or interpretation["automatic_all_data_claim"] is not False
        or interpretation["expected_lifecycle_after_measurement"] != "REVIEW"
        or interpretation["paper_trading_authorized"] is not False
        or interpretation["live_trading_authorized"] is not False
    ):
        raise ValueError("EXP-015 interpretation boundary changed.")


def verify_local_exp015_catalog_result() -> dict[str, Any]:
    validate_exp015_catalog_freeze()

    if CATALOG_STAGING_FILE.exists():
        raise ValueError(
            "EXP-015 catalog staging output still exists; result is incomplete."
        )
    if not CATALOG_RESULT_FILE.is_file():
        raise FileNotFoundError(CATALOG_RESULT_FILE)
    if not CATALOG_ROWS_FILE.is_file():
        raise FileNotFoundError(CATALOG_ROWS_FILE)

    actual_json_hash = _sha256(CATALOG_RESULT_FILE)
    actual_csv_hash = _sha256(CATALOG_ROWS_FILE)
    if actual_json_hash != EXPECTED_CATALOG_JSON_SHA256:
        raise ValueError(
            "EXP-015 catalog_result.json hash changed: "
            f"expected {EXPECTED_CATALOG_JSON_SHA256}, got {actual_json_hash}."
        )
    if actual_csv_hash != EXPECTED_CATALOG_CSV_SHA256:
        raise ValueError(
            "EXP-015 catalog_rows.csv hash changed: "
            f"expected {EXPECTED_CATALOG_CSV_SHA256}, got {actual_csv_hash}."
        )

    result = _load_json(CATALOG_RESULT_FILE)
    if (
        result.get("schema_version") != 1
        or result.get("experiment_id") != "EXP-015"
        or result.get("result_phase") != "CATALOG_ONLY"
        or result.get("created_at_utc") != EXPECTED_CREATED_AT_UTC
    ):
        raise ValueError("EXP-015 local catalog result identity changed.")

    git = result["git"]
    if (
        git["commit"] != EXPECTED_IMPLEMENTATION_COMMIT
        or git["short_commit"] != "8a74b9a"
        or git["working_tree_clean"] is not True
    ):
        raise ValueError("EXP-015 local catalog provenance changed.")

    probe = result["client_probe"]
    if (
        probe["status"] != "PASS"
        or probe["distribution"] != "lse-data"
        or probe["version"] != "0.14.0"
        or probe["python_version"] != "3.14.6"
        or probe["wheel_sha256"] != EXPECTED_CLIENT_WHEEL_SHA256
    ):
        raise ValueError("EXP-015 local client probe evidence changed.")

    catalog = result["catalog"]
    if (
        catalog["category_requested"] != "futures"
        or len(catalog["rows"]) != 69
        or catalog["canonical_sha256"]
        != EXPECTED_CATALOG_CANONICAL_SHA256
    ):
        raise ValueError("EXP-015 local futures catalog changed.")

    candidates = result["candidate_discovery"]
    if (
        candidates["NQ"] != [EXPECTED_NQ_CANDIDATE]
        or candidates["MNQ"] != []
    ):
        raise ValueError("EXP-015 local NQ/MNQ candidate evidence changed.")

    assessment = result["assessment"]
    expected_assessment = EXP015_CATALOG_FREEZE["assessment"]
    for key, expected in expected_assessment.items():
        if assessment.get(key) != expected:
            raise ValueError(
                f"EXP-015 local assessment changed for {key}: "
                f"expected {expected!r}, got {assessment.get(key)!r}."
            )
    if (
        assessment["futures_catalog_rows"] != 69
        or assessment["nq_candidate_count"] != 1
        or assessment["mnq_candidate_count"] != 0
    ):
        raise ValueError("EXP-015 local catalog counts changed.")

    rows = _load_csv(CATALOG_ROWS_FILE)
    if len(rows) != 69:
        raise ValueError(
            f"EXP-015 catalog_rows.csv expected 69 rows; found {len(rows)}."
        )
    nq_rows = [row for row in rows if row.get("symbol") == "NQ.F"]
    mnq_rows = [
        row
        for row in rows
        if row.get("symbol", "").upper() in {"MNQ", "MNQ.F"}
        or "MICRO E-MINI NASDAQ" in row.get("name", "").upper()
    ]
    if len(nq_rows) != 1:
        raise ValueError("EXP-015 NQ.F catalog row changed.")
    if mnq_rows:
        raise ValueError("EXP-015 unexpectedly contains an MNQ catalog row.")

    nq = nq_rows[0]
    expected_csv_nq = {
        "symbol": "NQ.F",
        "name": "Nasdaq 100 Futures",
        "category": "Futures",
        "dataset": "futures",
        "ticks": "3533260",
        "first": "2016-05-29 22:01:00.000000",
        "last": "2026-07-20 19:58:00.000000",
        "country": "United States",
    }
    if nq != expected_csv_nq:
        raise ValueError("EXP-015 NQ.F CSV evidence changed.")

    return get_exp015_catalog_freeze()


if __name__ == "__main__":
    result = verify_local_exp015_catalog_result()
    print("EXP-015 catalog result is frozen and valid.")
    print("Classification:", result["assessment"]["classification"])
    print("Futures catalog rows: 69")
    print("NQ candidate: NQ.F")
    print("MNQ candidates: 0")
    print("Historical bars downloaded: False")
    print("No paper or live trading is authorized.")
