from __future__ import annotations

import csv
from datetime import date, datetime
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
from typing import Any, Iterable, Iterator, Mapping, Sequence
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd


EXPERIMENT_ID = "EXP-025"
CANDIDATE_ID = "gap_fade_0p50_1r"
UNRESOLVED_CATEGORY = "UNRESOLVED_WITH_LOCKED_FEATURES"
RESEARCH_TIMEZONE = "America/New_York"
UTC = "UTC"
NQ_TICK_SIZE_POINTS = 0.25
DBN_FIXED_PRICE_SCALE = 1_000_000_000
EXPECTED_POPULATION_ROWS = 43
EXPECTED_ARCHIVE_CONTRACTS = 66
EXPECTED_QUANTOWER_FILES = 43
GAP_THRESHOLD = 0.50
CONTRACT_PATTERN = re.compile(r"^NQ[HMUZ]\d{2}$")

QUANTOWER_REQUIRED_COLUMNS = (
    "timestamp",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "explicit_contract_symbol",
)

DECISION_FIELDS = (
    "eligibility",
    "previous_cash_close",
    "previous_cash_high",
    "previous_cash_low",
    "previous_cash_range",
    "current_cash_open",
    "gap_move",
    "gap_direction",
    "normalized_gap",
    "threshold_margin",
    "threshold_passes",
    "fade_direction",
    "first_cash_bar_open",
    "first_cash_bar_high",
    "first_cash_bar_low",
    "first_cash_bar_close",
    "first_cash_bar_direction",
    "first_cash_bar_confirmation",
    "entry_0935_open",
    "entry_risk_points",
    "entry_risk_positive",
    "setup_passes",
    "decision_direction",
)

PRICE_DECISION_FIELDS = (
    "previous_cash_close",
    "previous_cash_high",
    "previous_cash_low",
    "previous_cash_range",
    "current_cash_open",
    "gap_move",
    "threshold_margin",
    "first_cash_bar_open",
    "first_cash_bar_high",
    "first_cash_bar_low",
    "first_cash_bar_close",
    "entry_0935_open",
    "entry_risk_points",
)

OUTPUT_SCHEMAS: dict[str, tuple[str, ...]] = {
    "session_contract_map.csv": (
        "candidate_id",
        "session_date",
        "previous_session_date",
        "exact_contract_symbol",
        "databento_instrument_id",
        "quantower_file",
        "quantower_file_sha256",
        "databento_file",
        "databento_file_sha256",
    ),
    "one_minute_bar_comparison.csv": (
        "session_date",
        "exact_contract_symbol",
        "timestamp_utc",
        "window",
        "quantower_present",
        "databento_present",
        "open_difference_ticks",
        "high_difference_ticks",
        "low_difference_ticks",
        "close_difference_ticks",
        "all_ohlc_match",
    ),
    "five_minute_component_comparison.csv": (
        "session_date",
        "exact_contract_symbol",
        "component",
        "quantower_value",
        "databento_value",
        "difference_ticks",
        "matches",
    ),
    "decision_engine_comparison.csv": (
        "session_date",
        "exact_contract_symbol",
        "source_id",
        "canonical_input_sha256",
        "independent_input_sha256",
        "input_hashes_match",
        "canonical_setup_passes",
        "independent_setup_passes",
        "canonical_direction",
        "independent_direction",
        "engines_match",
        "frozen_continuous_trade_flag",
        "frozen_continuous_direction",
    ),
    "source_difference_summary.csv": (
        "session_date",
        "exact_contract_symbol",
        "one_minute_ohlc_match",
        "canonical_decision_match",
        "independent_decision_match",
        "same_input_engine_difference",
        "source_bar_difference",
        "session_classification",
    ),
}

REQUIRED_OUTPUT_NAMES = (
    "exp025_summary.json",
    *OUTPUT_SCHEMAS.keys(),
    "output_hashes.json",
    "report.md",
    "report.html",
    "EXACT_CONTRACT_DIAGNOSTIC_COMPLETE.json",
    "assets/exact_contract_bar_match.png",
    "assets/decision_comparison.png",
    "assets/component_difference_ticks.png",
    "assets/prior_vs_exact_decisions.png",
)

FORBIDDEN_OUTPUT_TOKENS = (
    "pnl",
    "profit",
    "loss",
    "return",
    "equity",
    "drawdown",
    "sharpe",
    "sortino",
    "win_rate",
    "profit_factor",
    "exit_price",
    "target_price",
    "stop_price",
)


class Exp025DataError(ValueError):
    """Raised when locked EXP-025 evidence violates the preregistration."""


def _normalise_scalar(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (pd.Timestamp, datetime, date)):
        return value.isoformat()
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer, int)) and not isinstance(value, bool):
        return int(value)
    if isinstance(value, (np.floating, float)):
        numeric = float(value)
        if math.isnan(numeric):
            return None
        if math.isinf(numeric):
            return "Infinity" if numeric > 0 else "-Infinity"
        return numeric
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value


def canonical_object_sha256(value: Any) -> str:
    def normalise(item: Any) -> Any:
        if isinstance(item, Mapping):
            return {
                str(key): normalise(current)
                for key, current in item.items()
            }
        if isinstance(item, (list, tuple)):
            return [normalise(current) for current in item]
        return _normalise_scalar(item)

    encoded = json.dumps(
        normalise(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def canonical_dataframe_sha256(frame: pd.DataFrame) -> str:
    return canonical_object_sha256(frame.to_dict(orient="records"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def strict_bool(value: Any, *, name: str) -> bool:
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer, int)) and int(value) in {0, 1}:
        return bool(int(value))
    text = str(value).strip().lower()
    if text == "true":
        return True
    if text == "false":
        return False
    raise Exp025DataError(f"{name} contains a non-boolean value: {value!r}.")


def normalise_contract_symbol(value: Any) -> str:
    symbol = str(value).strip().upper()
    if not CONTRACT_PATTERN.fullmatch(symbol):
        raise Exp025DataError(
            f"EXP-025 requires an explicit quarterly NQ contract, found {value!r}."
        )
    return symbol


def safe_relative_path(value: Any) -> str:
    text = str(value).strip().replace("\\", "/")
    path = PurePosixPath(text)
    if (
        not text
        or not path.parts
        or path.is_absolute()
        or ".." in path.parts
        or path.parts[0] in {"", "."}
    ):
        raise Exp025DataError(f"Unsafe relative path: {value!r}.")
    return path.as_posix()


def select_unresolved_population(
    mismatch_attribution: pd.DataFrame,
    roll_context: pd.DataFrame,
    *,
    require_production_count: bool = True,
) -> pd.DataFrame:
    required_mismatch = {
        "candidate_id",
        "session_date",
        "frozen_reference_trade_flag",
        "frozen_transfer_trade_flag",
        "frozen_reference_direction",
        "frozen_transfer_direction",
        "reference_rebuild_matches_frozen",
        "transfer_rebuild_matches_frozen",
        "primary_attribution_category",
    }
    missing = sorted(required_mismatch.difference(mismatch_attribution.columns))
    if missing:
        raise Exp025DataError(
            "EXP-024 mismatch attribution is missing: " + ", ".join(missing)
        )

    required_roll = {
        "candidate_id",
        "session_date",
        "backward_adjusted_source_contract",
        "backward_adjusted_instrument_id",
        "unadjusted_source_contract",
        "unadjusted_instrument_id",
    }
    missing_roll = sorted(required_roll.difference(roll_context.columns))
    if missing_roll:
        raise Exp025DataError(
            "EXP-024 roll context is missing: " + ", ".join(missing_roll)
        )

    mismatch = mismatch_attribution.loc[:, sorted(required_mismatch)].copy()
    for column in (
        "frozen_reference_trade_flag",
        "frozen_transfer_trade_flag",
        "reference_rebuild_matches_frozen",
        "transfer_rebuild_matches_frozen",
    ):
        mismatch[column] = mismatch[column].map(
            lambda value, name=column: strict_bool(value, name=name)
        )

    mismatch["candidate_id"] = mismatch["candidate_id"].astype(str)
    mismatch["session_date"] = mismatch["session_date"].astype(str)
    mismatch["primary_attribution_category"] = (
        mismatch["primary_attribution_category"].astype(str)
    )
    mismatch["frozen_reference_direction"] = (
        mismatch["frozen_reference_direction"].fillna("").astype(str).str.lower()
    )
    mismatch["frozen_transfer_direction"] = (
        mismatch["frozen_transfer_direction"].fillna("").astype(str).str.lower()
    )

    selected = mismatch.loc[
        mismatch["candidate_id"].eq(CANDIDATE_ID)
        & mismatch["primary_attribution_category"].eq(UNRESOLVED_CATEGORY)
        & ~mismatch["reference_rebuild_matches_frozen"]
    ].copy()

    if selected.duplicated(["candidate_id", "session_date"]).any():
        raise Exp025DataError("EXP-025 unresolved population keys are not unique.")
    if not selected["session_date"].between("2020-01-03", "2025-12-31").all():
        raise Exp025DataError("EXP-025 unresolved population left the locked overlap.")

    roll = roll_context.loc[:, sorted(required_roll)].copy()
    roll["candidate_id"] = roll["candidate_id"].astype(str)
    roll["session_date"] = roll["session_date"].astype(str)
    if roll.duplicated(["candidate_id", "session_date"]).any():
        raise Exp025DataError("EXP-024 roll-context keys are not unique.")

    selected = selected.merge(
        roll,
        on=["candidate_id", "session_date"],
        how="left",
        validate="one_to_one",
    )
    if selected["backward_adjusted_source_contract"].isna().any():
        raise Exp025DataError("EXP-025 unresolved row has no exact-contract mapping.")

    selected["exact_contract_symbol"] = selected[
        "backward_adjusted_source_contract"
    ].map(normalise_contract_symbol)
    selected["unadjusted_source_contract"] = selected[
        "unadjusted_source_contract"
    ].map(normalise_contract_symbol)
    if not selected["exact_contract_symbol"].eq(
        selected["unadjusted_source_contract"]
    ).all():
        raise Exp025DataError(
            "Frozen adjusted and unadjusted rows disagree on exact contract."
        )

    selected["databento_instrument_id"] = pd.to_numeric(
        selected["backward_adjusted_instrument_id"], errors="raise"
    ).astype("int64")
    unadjusted_ids = pd.to_numeric(
        selected["unadjusted_instrument_id"], errors="raise"
    ).astype("int64")
    if not selected["databento_instrument_id"].eq(unadjusted_ids).all():
        raise Exp025DataError(
            "Frozen adjusted and unadjusted rows disagree on instrument ID."
        )

    if require_production_count:
        if len(selected) != EXPECTED_POPULATION_ROWS:
            raise Exp025DataError(
                f"EXP-025 requires 43 unresolved rows, found {len(selected)}."
            )
        if selected["session_date"].nunique() != EXPECTED_POPULATION_ROWS:
            raise Exp025DataError("EXP-025 requires 43 unique session dates.")
        if selected["frozen_reference_trade_flag"].any():
            raise Exp025DataError(
                "Locked unresolved rows must all be Quantower-reference non-trades."
            )
        if not selected["frozen_transfer_trade_flag"].all():
            raise Exp025DataError(
                "Locked unresolved rows must all be Databento transfer trades."
            )
        if not selected["transfer_rebuild_matches_frozen"].all():
            raise Exp025DataError(
                "Locked Databento transfer rebuild no longer matches all rows."
            )
        if not selected["frozen_transfer_direction"].isin({"long", "short"}).all():
            raise Exp025DataError("Frozen transfer direction is incomplete.")

    keep = (
        "candidate_id",
        "session_date",
        "frozen_reference_trade_flag",
        "frozen_transfer_trade_flag",
        "frozen_reference_direction",
        "frozen_transfer_direction",
        "exact_contract_symbol",
        "databento_instrument_id",
    )
    return selected.loc[:, keep].sort_values(
        ["session_date", "candidate_id"], kind="stable"
    ).reset_index(drop=True)


def attach_previous_session_dates(
    population: pd.DataFrame,
    session_quality: pd.DataFrame,
) -> pd.DataFrame:
    if "session_date" not in population.columns:
        raise Exp025DataError(
            "EXP-025 population is missing session_date."
        )
    if "session_date" not in session_quality.columns:
        raise Exp025DataError(
            "Frozen session calendar is missing session_date."
        )

    calendar = session_quality.loc[:, ["session_date"]].copy()
    if calendar.empty:
        raise Exp025DataError("Frozen session calendar is empty.")

    calendar["session_date"] = calendar["session_date"].astype(str)
    if calendar["session_date"].duplicated().any():
        raise Exp025DataError(
            "Frozen session calendar contains duplicate session dates."
        )

    try:
        parsed_calendar = pd.to_datetime(
            calendar["session_date"],
            format="%Y-%m-%d",
            errors="raise",
        )
    except (TypeError, ValueError) as exc:
        raise Exp025DataError(
            "Frozen session calendar contains an invalid date."
        ) from exc

    canonical_calendar = parsed_calendar.dt.strftime("%Y-%m-%d")
    if not canonical_calendar.eq(calendar["session_date"]).all():
        raise Exp025DataError(
            "Frozen session calendar dates are not canonical ISO dates."
        )

    sessions = sorted(canonical_calendar.tolist())
    if len(sessions) < 2:
        raise Exp025DataError(
            "Frozen session calendar cannot define a prior session."
        )

    previous_by_session = {
        current: previous
        for previous, current in zip(sessions[:-1], sessions[1:])
    }

    result = population.copy()
    result["session_date"] = result["session_date"].astype(str)

    try:
        parsed_population = pd.to_datetime(
            result["session_date"],
            format="%Y-%m-%d",
            errors="raise",
        )
    except (TypeError, ValueError) as exc:
        raise Exp025DataError(
            "EXP-025 population contains an invalid session date."
        ) from exc

    canonical_population = parsed_population.dt.strftime("%Y-%m-%d")
    if not canonical_population.eq(result["session_date"]).all():
        raise Exp025DataError(
            "EXP-025 population dates are not canonical ISO dates."
        )

    missing = sorted(
        set(result["session_date"]) - set(previous_by_session)
    )
    if missing:
        raise Exp025DataError(
            "EXP-025 target sessions are absent from the frozen session "
            "calendar or lack a prior session: "
            + ", ".join(missing)
        )

    result["previous_session_date"] = result["session_date"].map(
        previous_by_session
    )

    if result["previous_session_date"].isna().any():
        raise Exp025DataError(
            "EXP-025 previous-session mapping is incomplete."
        )
    if not result["previous_session_date"].lt(
        result["session_date"]
    ).all():
        raise Exp025DataError(
            "EXP-025 previous-session mapping is not strictly prior."
        )

    columns = list(result.columns)
    columns.remove("previous_session_date")
    insert_at = columns.index("session_date") + 1
    columns.insert(insert_at, "previous_session_date")

    return result.loc[:, columns].sort_values(
        ["session_date", "candidate_id"],
        kind="stable",
    ).reset_index(drop=True)


def archive_digest(completed: Sequence[Mapping[str, Any]]) -> str:
    payload = [
        {
            "sequence": int(row["sequence"]),
            "canonical_symbol": normalise_contract_symbol(
                row["canonical_symbol"]
            ),
            "sha256": str(row["sha256"]),
            "size_bytes": int(row["size_bytes"]),
        }
        for row in sorted(completed, key=lambda item: int(item["sequence"]))
    ]
    encoded = json.dumps(
        payload,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_archive_index(
    manifest: Mapping[str, Any],
    *,
    require_production_count: bool = True,
) -> dict[str, dict[str, Any]]:
    if manifest.get("experiment_id") != "EXP-019":
        raise Exp025DataError("Exact-contract archive manifest experiment changed.")
    if manifest.get("status") != "COMPLETE":
        raise Exp025DataError("Exact-contract archive manifest is not complete.")
    completed = manifest.get("completed")
    if not isinstance(completed, list):
        raise Exp025DataError("Exact-contract archive completed list is missing.")
    if require_production_count and len(completed) != EXPECTED_ARCHIVE_CONTRACTS:
        raise Exp025DataError(
            f"Expected 66 exact-contract files, found {len(completed)}."
        )

    index: dict[str, dict[str, Any]] = {}
    sequences: set[int] = set()
    for raw in completed:
        if not isinstance(raw, Mapping):
            raise Exp025DataError("Archive manifest entry is not an object.")
        required = {
            "sequence",
            "canonical_symbol",
            "relative_path",
            "size_bytes",
            "sha256",
        }
        missing = sorted(required.difference(raw))
        if missing:
            raise Exp025DataError(
                "Archive manifest entry is missing: " + ", ".join(missing)
            )
        sequence = int(raw["sequence"])
        if sequence in sequences:
            raise Exp025DataError("Archive manifest sequence is duplicated.")
        sequences.add(sequence)
        symbol = normalise_contract_symbol(raw["canonical_symbol"])
        if symbol in index:
            raise Exp025DataError("Archive manifest contract is duplicated.")
        entry = dict(raw)
        entry["sequence"] = sequence
        entry["canonical_symbol"] = symbol
        entry["relative_path"] = safe_relative_path(raw["relative_path"])
        entry["size_bytes"] = int(raw["size_bytes"])
        entry["sha256"] = str(raw["sha256"]).strip().lower()
        if entry["size_bytes"] <= 0 or not re.fullmatch(
            r"[0-9a-f]{64}", entry["sha256"]
        ):
            raise Exp025DataError("Archive manifest file identity is invalid.")
        index[symbol] = entry
    return index


def validate_population_contracts_in_archive(
    population: pd.DataFrame,
    archive_index: Mapping[str, Mapping[str, Any]],
) -> None:
    missing = sorted(
        set(population["exact_contract_symbol"].astype(str))
        - set(archive_index)
    )
    if missing:
        raise Exp025DataError(
            "Population exact contracts are absent from archive: "
            + ", ".join(missing)
        )


def validate_quantower_export_manifest(
    manifest: Mapping[str, Any],
    population: pd.DataFrame,
    *,
    require_production_count: bool = True,
) -> pd.DataFrame:
    expected_header = {
        "schema_version": 1,
        "experiment_id": EXPERIMENT_ID,
        "status": "COMPLETE",
        "source": "Lucid/Rithmic via Quantower History Exporter",
        "resolution": "1 minute",
        "research_timezone": RESEARCH_TIMEZONE,
    }
    for key, expected in expected_header.items():
        if manifest.get(key) != expected:
            raise Exp025DataError(
                f"Quantower export manifest {key} changed: "
                f"{manifest.get(key)!r} != {expected!r}."
            )
    columns = tuple(manifest.get("required_columns", ()))
    if columns != QUANTOWER_REQUIRED_COLUMNS:
        raise Exp025DataError("Quantower export columns changed.")
    files = manifest.get("files")
    if not isinstance(files, list):
        raise Exp025DataError("Quantower export manifest files list is missing.")
    if require_production_count and len(files) != EXPECTED_QUANTOWER_FILES:
        raise Exp025DataError(
            f"EXP-025 requires 43 Quantower exports, found {len(files)}."
        )

    if "previous_session_date" not in population.columns:
        raise Exp025DataError(
            "Population lacks locked previous-session dates."
        )

    expected = population.set_index("session_date")
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in files:
        if not isinstance(raw, Mapping):
            raise Exp025DataError("Quantower export entry is not an object.")
        required = {
            "session_date",
            "previous_session_date",
            "explicit_contract_symbol",
            "relative_path",
            "size_bytes",
            "sha256",
            "row_count",
            "timestamp_timezone",
            "pretrimmed_to_allowed_windows",
        }
        missing = sorted(required.difference(raw))
        if missing:
            raise Exp025DataError(
                "Quantower export entry is missing: " + ", ".join(missing)
            )
        session_date = str(raw["session_date"])
        if session_date in seen:
            raise Exp025DataError("Quantower export session is duplicated.")
        seen.add(session_date)
        if session_date not in expected.index:
            raise Exp025DataError(
                f"Quantower export contains an out-of-population session: {session_date}."
            )
        previous_session_date = str(raw["previous_session_date"])
        try:
            date.fromisoformat(session_date)
            date.fromisoformat(previous_session_date)
        except ValueError as exc:
            raise Exp025DataError(
                "Quantower manifest date is invalid."
            ) from exc

        expected_previous_session = str(
            expected.loc[session_date, "previous_session_date"]
        )
        if previous_session_date != expected_previous_session:
            raise Exp025DataError(
                "Quantower previous-session mismatch for "
                f"{session_date}: {previous_session_date} != "
                f"{expected_previous_session}."
            )
        symbol = normalise_contract_symbol(raw["explicit_contract_symbol"])
        expected_symbol = str(expected.loc[session_date, "exact_contract_symbol"])
        if symbol != expected_symbol:
            raise Exp025DataError(
                f"Quantower contract mismatch for {session_date}: "
                f"{symbol} != {expected_symbol}."
            )
        relative_path = safe_relative_path(raw["relative_path"])
        if not relative_path.lower().endswith(".csv"):
            raise Exp025DataError("Quantower export must be a CSV file.")
        size_bytes = int(raw["size_bytes"])
        row_count = int(raw["row_count"])
        digest = str(raw["sha256"]).strip().lower()
        if size_bytes <= 0 or row_count <= 0 or row_count > 396:
            raise Exp025DataError("Quantower export size or row count is invalid.")
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise Exp025DataError("Quantower export SHA-256 is invalid.")
        timezone_name = str(raw["timestamp_timezone"])
        try:
            ZoneInfo(timezone_name)
        except Exception as exc:
            raise Exp025DataError(
                f"Unknown Quantower timestamp timezone: {timezone_name}."
            ) from exc
        if strict_bool(
            raw["pretrimmed_to_allowed_windows"],
            name="pretrimmed_to_allowed_windows",
        ) is not True:
            raise Exp025DataError(
                "Quantower exports must be pretrimmed to the locked windows."
            )
        rows.append(
            {
                "session_date": session_date,
                "previous_session_date": previous_session_date,
                "exact_contract_symbol": symbol,
                "relative_path": relative_path,
                "size_bytes": size_bytes,
                "sha256": digest,
                "row_count": row_count,
                "timestamp_timezone": timezone_name,
            }
        )

    expected_sessions = set(population["session_date"].astype(str))
    if seen != expected_sessions:
        missing = sorted(expected_sessions - seen)
        unexpected = sorted(seen - expected_sessions)
        raise Exp025DataError(
            "Quantower export session set changed. "
            f"Missing: {missing}; unexpected: {unexpected}."
        )
    return pd.DataFrame(rows).sort_values("session_date", kind="stable").reset_index(
        drop=True
    )


def parse_timestamp(value: Any, *, declared_timezone: str) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if pd.isna(timestamp):
        raise Exp025DataError("Timestamp is missing.")
    if timestamp.tzinfo is None:
        try:
            timestamp = timestamp.tz_localize(
                ZoneInfo(declared_timezone), ambiguous="raise", nonexistent="raise"
            )
        except Exception as exc:
            raise Exp025DataError(
                f"Timestamp {value!r} cannot be localized to {declared_timezone}."
            ) from exc
    return timestamp.tz_convert(UTC)


def local_window_label(
    timestamp_utc: pd.Timestamp,
    *,
    session_date: str,
    previous_session_date: str,
) -> str | None:
    if timestamp_utc.tzinfo is None:
        raise Exp025DataError("EXP-025 timestamps must be timezone-aware.")
    local = timestamp_utc.tz_convert(RESEARCH_TIMEZONE)
    if local.second != 0 or local.microsecond != 0 or local.nanosecond != 0:
        raise Exp025DataError("EXP-025 bars must start on exact minutes.")
    local_date = local.date().isoformat()
    minute = int(local.hour) * 60 + int(local.minute)
    if local_date == previous_session_date and 9 * 60 + 30 <= minute < 16 * 60:
        return "PREVIOUS_CASH"
    if local_date == session_date and 9 * 60 + 30 <= minute <= 9 * 60 + 35:
        return "CURRENT_ENTRY_WINDOW"
    return None


def price_to_ticks(value: Any, *, name: str) -> int:
    numeric = float(value)
    if not math.isfinite(numeric):
        raise Exp025DataError(f"{name} is nonfinite.")
    scaled = numeric / NQ_TICK_SIZE_POINTS
    rounded = round(scaled)
    if not math.isclose(scaled, rounded, rel_tol=0.0, abs_tol=1e-7):
        raise Exp025DataError(f"{name} is not aligned to the NQ tick size.")
    return int(rounded)


def ticks_to_price(value: int | float | None) -> float | None:
    if value is None:
        return None
    return float(value) * NQ_TICK_SIZE_POINTS


def dbn_fixed_price_to_float(value: Any) -> float:
    integer = int(value)
    if abs(integer) > 10**16:
        raise Exp025DataError("DBN fixed price is undefined or outside NQ bounds.")
    return float(integer) / float(DBN_FIXED_PRICE_SCALE)


def dbn_record_timestamp(record: Any) -> pd.Timestamp:
    try:
        raw = int(getattr(record, "ts_event"))
    except Exception as exc:
        raise Exp025DataError("DBN record has no valid ts_event.") from exc
    return pd.Timestamp(raw, unit="ns", tz=UTC)


def dbn_record_to_row(
    record: Any,
    *,
    exact_contract_symbol: str,
) -> dict[str, Any]:
    symbol = normalise_contract_symbol(exact_contract_symbol)
    return {
        "timestamp": dbn_record_timestamp(record),
        "open": dbn_fixed_price_to_float(getattr(record, "open")),
        "high": dbn_fixed_price_to_float(getattr(record, "high")),
        "low": dbn_fixed_price_to_float(getattr(record, "low")),
        "close": dbn_fixed_price_to_float(getattr(record, "close")),
        "volume": int(getattr(record, "volume")),
        "explicit_contract_symbol": symbol,
        "instrument_id": int(getattr(record, "instrument_id")),
    }


def stream_restricted_dbn_records(
    records: Iterable[Any],
    *,
    session_date: str,
    previous_session_date: str,
    exact_contract_symbol: str,
) -> list[dict[str, Any]]:
    """Retain only locked rows without accessing out-of-window OHLCV fields.

    Every DBN record's timestamp is inspected. Price, volume and instrument
    fields are accessed only after the timestamp is inside a permitted window.
    """

    rows: list[dict[str, Any]] = []
    for record in records:
        timestamp = dbn_record_timestamp(record)
        if local_window_label(
            timestamp,
            session_date=session_date,
            previous_session_date=previous_session_date,
        ) is None:
            continue
        rows.append(
            dbn_record_to_row(
                record,
                exact_contract_symbol=exact_contract_symbol,
            )
        )
    return rows


def stream_quantower_csv(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != QUANTOWER_REQUIRED_COLUMNS:
            raise Exp025DataError(
                "Quantower CSV columns or order changed: "
                f"{tuple(reader.fieldnames or ())!r}."
            )
        for row in reader:
            rows.append(dict(row))
    return rows


def normalise_source_rows(
    rows: Iterable[Mapping[str, Any]],
    *,
    source_id: str,
    session_date: str,
    previous_session_date: str,
    exact_contract_symbol: str,
    timestamp_timezone: str,
    expected_instrument_id: int | None = None,
) -> pd.DataFrame:
    symbol = normalise_contract_symbol(exact_contract_symbol)
    normalised: list[dict[str, Any]] = []
    for index, raw in enumerate(rows):
        timestamp_value = raw.get("timestamp", raw.get("timestamp_utc"))
        if timestamp_value is None:
            raise Exp025DataError(f"Row {index} is missing timestamp.")
        timestamp = parse_timestamp(
            timestamp_value,
            declared_timezone=timestamp_timezone,
        )
        window = local_window_label(
            timestamp,
            session_date=session_date,
            previous_session_date=previous_session_date,
        )
        if window is None:
            raise Exp025DataError(
                "Materialized source row is outside the locked EXP-025 windows."
            )
        row_symbol = normalise_contract_symbol(
            raw.get("explicit_contract_symbol", symbol)
        )
        if row_symbol != symbol:
            raise Exp025DataError("Source row contract identity changed.")
        instrument_value = raw.get("instrument_id")
        instrument_id = (
            int(instrument_value)
            if instrument_value not in {None, ""}
            else None
        )
        if (
            expected_instrument_id is not None
            and instrument_id is not None
            and instrument_id != int(expected_instrument_id)
        ):
            raise Exp025DataError("Databento instrument ID changed.")
        open_ticks = price_to_ticks(raw["open"], name="open")
        high_ticks = price_to_ticks(raw["high"], name="high")
        low_ticks = price_to_ticks(raw["low"], name="low")
        close_ticks = price_to_ticks(raw["close"], name="close")
        if (
            high_ticks < max(open_ticks, low_ticks, close_ticks)
            or low_ticks > min(open_ticks, high_ticks, close_ticks)
        ):
            raise Exp025DataError("Source row OHLC geometry is invalid.")
        volume = int(float(raw.get("volume", 0)))
        if volume < 0:
            raise Exp025DataError("Source row volume is negative.")
        local = timestamp.tz_convert(RESEARCH_TIMEZONE)
        normalised.append(
            {
                "source_id": str(source_id),
                "session_date": session_date,
                "previous_session_date": previous_session_date,
                "exact_contract_symbol": symbol,
                "instrument_id": instrument_id,
                "timestamp_utc": timestamp,
                "local_timestamp": local,
                "local_date": local.date().isoformat(),
                "local_minute": int(local.hour) * 60 + int(local.minute),
                "window": window,
                "open_ticks": open_ticks,
                "high_ticks": high_ticks,
                "low_ticks": low_ticks,
                "close_ticks": close_ticks,
                "open": ticks_to_price(open_ticks),
                "high": ticks_to_price(high_ticks),
                "low": ticks_to_price(low_ticks),
                "close": ticks_to_price(close_ticks),
                "volume": volume,
            }
        )
    frame = pd.DataFrame(normalised)
    if frame.empty:
        raise Exp025DataError("Source produced no rows in the locked windows.")
    if frame["timestamp_utc"].duplicated().any():
        raise Exp025DataError("Source timestamps are duplicated.")
    frame = frame.sort_values("timestamp_utc", kind="stable").reset_index(drop=True)
    return frame


def aggregate_observed_five_minute(frame: pd.DataFrame) -> pd.DataFrame:
    required = {
        "source_id",
        "session_date",
        "exact_contract_symbol",
        "timestamp_utc",
        "local_minute",
        "window",
        "open_ticks",
        "high_ticks",
        "low_ticks",
        "close_ticks",
    }
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise Exp025DataError(
            "Five-minute aggregation is missing: " + ", ".join(missing)
        )
    local = frame.copy()
    local["five_minute_start"] = (local["local_minute"].astype(int) // 5) * 5
    rows: list[dict[str, Any]] = []
    group_columns = (
        "source_id",
        "session_date",
        "exact_contract_symbol",
        "window",
        "five_minute_start",
    )
    for key, group in local.groupby(list(group_columns), sort=True):
        ordered = group.sort_values("timestamp_utc", kind="stable")
        row = dict(zip(group_columns, key))
        row.update(
            {
                "timestamp_utc": ordered.iloc[0]["timestamp_utc"],
                "observation_count": int(len(ordered)),
                "open_ticks": int(ordered.iloc[0]["open_ticks"]),
                "high_ticks": int(ordered["high_ticks"].max()),
                "low_ticks": int(ordered["low_ticks"].min()),
                "close_ticks": int(ordered.iloc[-1]["close_ticks"]),
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)


def decision_input_hash(frame: pd.DataFrame) -> str:
    ordered = frame.sort_values("timestamp_utc", kind="stable").loc[
        :,
        [
            "timestamp_utc",
            "open_ticks",
            "high_ticks",
            "low_ticks",
            "close_ticks",
        ],
    ]
    return canonical_dataframe_sha256(ordered)


def _window_ohlc_ticks(
    frame: pd.DataFrame,
    *,
    local_date: str,
    start_minute: int,
    end_minute_exclusive: int,
) -> dict[str, int] | None:
    rows = frame.loc[
        frame["local_date"].eq(local_date)
        & frame["local_minute"].between(
            start_minute, end_minute_exclusive - 1
        )
    ].sort_values("timestamp_utc", kind="stable")
    if rows.empty:
        return None
    return {
        "open_ticks": int(rows.iloc[0]["open_ticks"]),
        "high_ticks": int(rows["high_ticks"].max()),
        "low_ticks": int(rows["low_ticks"].min()),
        "close_ticks": int(rows.iloc[-1]["close_ticks"]),
        "row_count": int(len(rows)),
    }


def independent_gap_fade_decision(
    frame: pd.DataFrame,
    *,
    session_date: str,
    previous_session_date: str,
    eligible: bool = True,
) -> dict[str, Any]:
    previous_cash = _window_ohlc_ticks(
        frame,
        local_date=previous_session_date,
        start_minute=9 * 60 + 30,
        end_minute_exclusive=16 * 60,
    )
    first_cash = _window_ohlc_ticks(
        frame,
        local_date=session_date,
        start_minute=9 * 60 + 30,
        end_minute_exclusive=9 * 60 + 35,
    )
    entry = frame.loc[
        frame["local_date"].eq(session_date)
        & frame["local_minute"].eq(9 * 60 + 35)
    ].sort_values("timestamp_utc", kind="stable")
    if eligible and (previous_cash is None or first_cash is None or len(entry) != 1):
        raise Exp025DataError(
            "Eligible exact-contract source is missing a locked decision window."
        )
    previous_close = previous_cash["close_ticks"] if previous_cash else None
    previous_high = previous_cash["high_ticks"] if previous_cash else None
    previous_low = previous_cash["low_ticks"] if previous_cash else None
    previous_range = (
        previous_high - previous_low if previous_cash is not None else None
    )
    first_open = first_cash["open_ticks"] if first_cash else None
    first_high = first_cash["high_ticks"] if first_cash else None
    first_low = first_cash["low_ticks"] if first_cash else None
    first_close = first_cash["close_ticks"] if first_cash else None
    entry_open = int(entry.iloc[0]["open_ticks"]) if len(entry) == 1 else None
    gap_move = (
        first_open - previous_close
        if first_open is not None and previous_close is not None
        else None
    )
    gap_direction = 1 if gap_move and gap_move > 0 else -1 if gap_move and gap_move < 0 else 0
    normalized_gap = (
        abs(gap_move) / previous_range
        if gap_move is not None and previous_range is not None and previous_range > 0
        else None
    )
    fade_direction = -gap_direction
    first_direction = (
        1 if first_close is not None and first_open is not None and first_close > first_open
        else -1 if first_close is not None and first_open is not None and first_close < first_open
        else 0
    )
    threshold_margin = (
        normalized_gap - GAP_THRESHOLD if normalized_gap is not None else None
    )
    threshold_passes = bool(
        normalized_gap is not None
        and math.isfinite(normalized_gap)
        and normalized_gap >= GAP_THRESHOLD
    )
    confirmation = bool(fade_direction != 0 and first_direction == fade_direction)
    risk_ticks = (
        fade_direction
        * (
            entry_open
            - (first_low if fade_direction == 1 else first_high)
        )
        if (
            fade_direction != 0
            and entry_open is not None
            and first_cash is not None
        )
        else None
    )
    risk_positive = bool(risk_ticks is not None and risk_ticks > 0)
    setup_passes = bool(
        eligible
        and threshold_passes
        and fade_direction != 0
        and confirmation
        and risk_positive
    )
    return {
        "eligibility": bool(eligible),
        "previous_cash_close": ticks_to_price(previous_close),
        "previous_cash_high": ticks_to_price(previous_high),
        "previous_cash_low": ticks_to_price(previous_low),
        "previous_cash_range": ticks_to_price(previous_range),
        "current_cash_open": ticks_to_price(first_open),
        "gap_move": ticks_to_price(gap_move),
        "gap_direction": gap_direction,
        "normalized_gap": normalized_gap,
        "threshold_margin": threshold_margin,
        "threshold_passes": threshold_passes,
        "fade_direction": fade_direction,
        "first_cash_bar_open": ticks_to_price(first_open),
        "first_cash_bar_high": ticks_to_price(first_high),
        "first_cash_bar_low": ticks_to_price(first_low),
        "first_cash_bar_close": ticks_to_price(first_close),
        "first_cash_bar_direction": first_direction,
        "first_cash_bar_confirmation": confirmation,
        "entry_0935_open": ticks_to_price(entry_open),
        "entry_risk_points": ticks_to_price(risk_ticks),
        "entry_risk_positive": risk_positive,
        "setup_passes": setup_passes,
        "decision_direction": (
            "long" if fade_direction == 1 else "short" if fade_direction == -1 else ""
        ),
    }


def canonical_gap_fade_decision(
    frame: pd.DataFrame,
    *,
    source_id: str,
    session_date: str,
    previous_session_date: str,
    eligible: bool = True,
) -> dict[str, Any]:
    """Run the existing frozen EXP-024 rule path without changing parameters."""

    from exp024_attribution_core import build_candidate_features

    mapping = {
        "QUANTOWER_EXACT": "QUANTOWER_REFERENCE",
        "DATABENTO_EXACT": "BACKWARD_ADJUSTED",
    }
    if source_id not in mapping:
        raise Exp025DataError(f"Unknown exact-contract source: {source_id}.")
    prepared = frame.copy()
    prepared["session_date"] = prepared["local_date"].astype(str)
    current = prepared.loc[
        prepared["session_date"].eq(session_date)
        & prepared["local_minute"].between(9 * 60 + 30, 9 * 60 + 34)
    ].copy()
    entry = prepared.loc[
        prepared["session_date"].eq(session_date)
        & prepared["local_minute"].eq(9 * 60 + 35)
    ].copy()
    previous = prepared.loc[
        prepared["session_date"].eq(previous_session_date)
        & prepared["local_minute"].between(9 * 60 + 30, 15 * 60 + 59)
    ].copy()
    return build_candidate_features(
        source_id=mapping[source_id],
        candidate_id=CANDIDATE_ID,
        session_date=session_date,
        eligible=eligible,
        current_rows=current,
        entry_rows=entry,
        previous_cash_rows=previous,
    )


def decision_vectors_match(
    left: Mapping[str, Any],
    right: Mapping[str, Any],
) -> bool:
    for field in DECISION_FIELDS:
        left_value = left.get(field)
        right_value = right.get(field)
        if field in PRICE_DECISION_FIELDS:
            if left_value is None or right_value is None:
                if left_value is not None or right_value is not None:
                    return False
                continue
            if field == "threshold_margin":
                if not math.isclose(
                    float(left_value), float(right_value), rel_tol=0.0, abs_tol=1e-12
                ):
                    return False
            else:
                if price_to_ticks(left_value, name=field) != price_to_ticks(
                    right_value, name=field
                ):
                    return False
        elif field == "normalized_gap":
            if left_value is None or right_value is None:
                if left_value is not None or right_value is not None:
                    return False
            elif not math.isclose(
                float(left_value), float(right_value), rel_tol=0.0, abs_tol=1e-12
            ):
                return False
        elif left_value != right_value:
            return False
    return True


def compare_one_minute_sources(
    quantower: pd.DataFrame,
    databento: pd.DataFrame,
) -> pd.DataFrame:
    columns = [
        "timestamp_utc",
        "window",
        "open_ticks",
        "high_ticks",
        "low_ticks",
        "close_ticks",
    ]
    left = quantower.loc[:, columns].rename(
        columns={column: f"quantower_{column}" for column in columns if column != "timestamp_utc"}
    )
    right = databento.loc[:, columns].rename(
        columns={column: f"databento_{column}" for column in columns if column != "timestamp_utc"}
    )
    merged = left.merge(right, on="timestamp_utc", how="outer", indicator=True)
    merged["quantower_present"] = merged["_merge"].isin({"left_only", "both"})
    merged["databento_present"] = merged["_merge"].isin({"right_only", "both"})
    merged["window"] = merged["quantower_window"].fillna(merged["databento_window"])
    for field in ("open", "high", "low", "close"):
        merged[f"{field}_difference_ticks"] = (
            merged[f"databento_{field}_ticks"]
            - merged[f"quantower_{field}_ticks"]
        )
    merged["all_ohlc_match"] = (
        merged["_merge"].eq("both")
        & merged[
            [f"{field}_difference_ticks" for field in ("open", "high", "low", "close")]
        ].eq(0).all(axis=1)
    )
    return merged.sort_values("timestamp_utc", kind="stable").reset_index(drop=True)


def session_classification(
    *,
    source_bar_difference: bool,
    same_input_engine_difference: bool,
) -> str:
    if source_bar_difference and same_input_engine_difference:
        return "MIXED_DIFFERENCE"
    if source_bar_difference:
        return "SOURCE_DIFFERENCE"
    if same_input_engine_difference:
        return "ENGINE_DIFFERENCE"
    return "EQUIVALENT"


def final_classification(
    hard_checks: Mapping[str, bool],
    *,
    source_difference_present: bool,
    engine_difference_present: bool,
) -> str:
    if not hard_checks or not all(bool(value) for value in hard_checks.values()):
        return "EXACT_CONTRACT_DIAGNOSTIC_NOT_QUALIFIED"
    if source_difference_present and engine_difference_present:
        return "EXACT_CONTRACT_DIAGNOSTIC_COMPLETE_MIXED_DIFFERENCES"
    if source_difference_present:
        return "EXACT_CONTRACT_DIAGNOSTIC_COMPLETE_SOURCE_DIFFERENCES"
    if engine_difference_present:
        return "EXACT_CONTRACT_DIAGNOSTIC_COMPLETE_ENGINE_DIFFERENCES"
    return "EXACT_CONTRACT_DIAGNOSTIC_COMPLETE_EQUIVALENT"


def validate_output_schemas() -> None:
    if len(REQUIRED_OUTPUT_NAMES) != 14:
        raise Exp025DataError("EXP-025 required output count changed.")
    if len(set(REQUIRED_OUTPUT_NAMES)) != len(REQUIRED_OUTPUT_NAMES):
        raise Exp025DataError("EXP-025 required output names are duplicated.")
    for filename, columns in OUTPUT_SCHEMAS.items():
        if not filename.endswith(".csv"):
            raise Exp025DataError("EXP-025 tabular output must be CSV.")
        if len(columns) != len(set(columns)):
            raise Exp025DataError(f"{filename} has duplicate columns.")
        lowered = {column.lower() for column in columns}
        for token in FORBIDDEN_OUTPUT_TOKENS:
            if any(token in column for column in lowered):
                raise Exp025DataError(
                    f"{filename} exposes prohibited performance field {token}."
                )


def required_output_set() -> set[str]:
    validate_output_schemas()
    return set(REQUIRED_OUTPUT_NAMES)
