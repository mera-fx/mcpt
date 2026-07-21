from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import re
from typing import Any, Iterable, Mapping


ALLOWED_FIELDS: tuple[str, ...] = (
    "symbol",
    "name",
    "category",
    "dataset",
    "ticks",
    "first",
    "last",
    "country",
)

CONTRACT_FIELD_NAMES: tuple[str, ...] = (
    "contract_type",
    "contract",
    "series_type",
    "continuous",
)

ROLL_FIELD_NAMES: tuple[str, ...] = (
    "roll_method",
    "roll_rule",
    "roll",
)

ADJUSTMENT_FIELD_NAMES: tuple[str, ...] = (
    "adjustment",
    "price_adjustment",
    "back_adjustment",
)

_NQ_TOKEN = re.compile(r"(^|[^A-Z0-9])NQ([^A-Z0-9]|$)")
_MNQ_TOKEN = re.compile(r"(^|[^A-Z0-9])MNQ([^A-Z0-9]|$)")


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _safe_ticks(value: Any) -> int | float | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        raise ValueError("Boolean tick count is invalid.")
    if isinstance(value, (int, float)):
        return value
    text = str(value).replace(",", "").strip()
    try:
        number = float(text)
    except ValueError as exc:
        raise ValueError(f"Invalid catalog tick count: {value!r}") from exc
    return int(number) if number.is_integer() else number


def canonicalize_catalog_rows(
    rows: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    if isinstance(rows, (str, bytes, Mapping)):
        raise ValueError("Catalog rows must be an iterable of mappings.")

    canonical: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise ValueError(f"Catalog row {index} is not a mapping.")
        lowered = {str(key).lower(): value for key, value in row.items()}
        serialized = json.dumps(lowered, default=str).lower()
        if "lse_api_key" in serialized or "authorization" in serialized:
            raise ValueError("Catalog row contains prohibited credential material.")

        item = {
            "symbol": _safe_text(lowered.get("symbol")),
            "name": _safe_text(lowered.get("name")),
            "category": _safe_text(lowered.get("category")),
            "dataset": _safe_text(lowered.get("dataset")),
            "ticks": _safe_ticks(lowered.get("ticks")),
            "first": _safe_text(lowered.get("first")),
            "last": _safe_text(lowered.get("last")),
            "country": _safe_text(lowered.get("country")),
        }

        # Preserve methodology metadata only when the official response supplies it.
        for field in (
            *CONTRACT_FIELD_NAMES,
            *ROLL_FIELD_NAMES,
            *ADJUSTMENT_FIELD_NAMES,
            "upstream_source",
            "exchange",
            "timezone",
        ):
            if field in lowered and lowered[field] not in (None, ""):
                item[field] = deepcopy(lowered[field])

        canonical.append(item)

    canonical.sort(
        key=lambda row: (
            row["category"].casefold(),
            row["dataset"].casefold(),
            row["symbol"].casefold(),
            row["name"].casefold(),
        )
    )
    return canonical


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _candidate_flags(row: Mapping[str, Any]) -> dict[str, bool]:
    symbol = _safe_text(row.get("symbol")).upper()
    name = _safe_text(row.get("name")).upper()
    joined = f"{symbol} {name}"
    nasdaq = "NASDAQ" in joined or "NASDAQ-100" in joined
    micro = "MICRO" in joined
    return {
        "nq_token": bool(_NQ_TOKEN.search(joined)),
        "mnq_token": bool(_MNQ_TOKEN.search(joined)),
        "nasdaq_name": nasdaq,
        "micro_name": micro,
    }


def find_nq_mnq_candidates(
    rows: Iterable[Mapping[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    canonical = canonicalize_catalog_rows(rows)
    result = {"NQ": [], "MNQ": []}
    for row in canonical:
        flags = _candidate_flags(row)
        candidate = dict(row)
        candidate["discovery_flags"] = flags

        if flags["mnq_token"] or (flags["nasdaq_name"] and flags["micro_name"]):
            result["MNQ"].append(candidate)
        if flags["nq_token"] or (
            flags["nasdaq_name"] and not flags["micro_name"]
        ):
            result["NQ"].append(candidate)
    return result


def _first_present(
    rows: Iterable[Mapping[str, Any]],
    fields: tuple[str, ...],
) -> list[Any]:
    values: list[Any] = []
    for row in rows:
        for field in fields:
            value = row.get(field)
            if value not in (None, ""):
                values.append(value)
    return values


def assess_catalog(
    rows: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    canonical = canonicalize_catalog_rows(rows)
    candidates = find_nq_mnq_candidates(canonical)

    if not canonical:
        classification = "CATALOG_UNAVAILABLE"
        reason = "The futures catalog returned no rows."
    else:
        classification = "IDENTITY_UNRESOLVED"
        reason = (
            "Catalog candidates are preserved for review, but catalog-only "
            "evidence does not yet resolve both instrument identity and the "
            "continuous-contract, roll and price-adjustment methodology."
        )

    candidate_rows = candidates["NQ"] + candidates["MNQ"]
    contract_metadata = _first_present(candidate_rows, CONTRACT_FIELD_NAMES)
    roll_metadata = _first_present(candidate_rows, ROLL_FIELD_NAMES)
    adjustment_metadata = _first_present(
        candidate_rows,
        ADJUSTMENT_FIELD_NAMES,
    )

    return {
        "classification": classification,
        "classification_scope": "NQ_MNQ_ONE_MINUTE_HISTORICAL_RESEARCH",
        "reason": reason,
        "futures_catalog_rows": len(canonical),
        "nq_candidate_count": len(candidates["NQ"]),
        "mnq_candidate_count": len(candidates["MNQ"]),
        "nq_identified": False,
        "mnq_identified": False,
        "contract_method_resolved": bool(contract_metadata),
        "roll_method_resolved": bool(roll_metadata),
        "price_adjustment_resolved": bool(adjustment_metadata),
        "history_download_authorized": False,
        "all_vendor_data_qualified": False,
        "paper_trading_authorized": False,
        "live_trading_authorized": False,
    }


def build_catalog_result(
    rows: Iterable[Mapping[str, Any]],
    *,
    git: Mapping[str, Any],
    client_probe: Mapping[str, Any],
) -> dict[str, Any]:
    canonical = canonicalize_catalog_rows(rows)
    candidates = find_nq_mnq_candidates(canonical)
    assessment = assess_catalog(canonical)

    return {
        "schema_version": 1,
        "experiment_id": "EXP-015",
        "result_phase": "CATALOG_ONLY",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "git": dict(git),
        "client_probe": {
            "status": client_probe.get("status"),
            "distribution": client_probe.get("distribution"),
            "version": client_probe.get("version"),
            "python_version": client_probe.get("python_version"),
            "wheel_sha256": client_probe.get("wheel_sha256"),
        },
        "catalog": {
            "category_requested": "futures",
            "rows": canonical,
            "canonical_sha256": canonical_sha256(canonical),
        },
        "candidate_discovery": candidates,
        "assessment": assessment,
        "interpretation": {
            "candidate_discovery_is_not_identity_resolution": True,
            "catalog_does_not_start_history_phase": True,
            "frozen_prior_data_replaced": False,
            "automatic_all_data_claim": False,
            "paper_trading_authorized": False,
            "live_trading_authorized": False,
        },
    }
