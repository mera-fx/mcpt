from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, time
import json
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd


QUICK_START = date(2019, 5, 6)
QUICK_END = date(2022, 12, 30)
NEW_YORK = ZoneInfo("America/New_York")
SESSION_START = time(9, 30)
SESSION_END = time(16, 0)

ROOT = Path("data") / "EXP-005" / "incoming"
OUTPUT_DIR = (
    Path("results")
    / "EXP-005"
    / "data"
    / "duplicate_audit"
)


class DuplicateAuditError(RuntimeError):
    pass


@dataclass(frozen=True)
class DuplicateRecord:
    symbol: str
    file: str
    timestamp_utc: str
    timestamp_new_york: str
    inside_locked_cash_session: bool
    classification: str
    copies: int
    unique_ohlc_rows: int
    unique_volume_values: int
    open_values: str
    high_values: str
    low_values: str
    close_values: str
    volume_values: str
    minimum_volume: float
    maximum_volume: float
    maximum_to_minimum_volume_ratio: float | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _normalise_columns(
    frame: pd.DataFrame,
) -> dict[str, str]:
    lookup = {
        str(column).strip().lower(): str(column)
        for column in frame.columns
    }

    required = {
        "timestamp": (
            "time left",
            "timestamp",
            "time",
            "datetime",
            "date",
        ),
        "open": ("open",),
        "high": ("high",),
        "low": ("low",),
        "close": ("close",),
        "volume": ("volume",),
    }

    resolved: dict[str, str] = {}

    for target, candidates in required.items():
        for candidate in candidates:
            if candidate in lookup:
                resolved[target] = lookup[candidate]
                break

        if target not in resolved:
            raise DuplicateAuditError(
                f"Missing required column for {target}. "
                f"Available columns: {list(frame.columns)}"
            )

    return resolved


def _parse_file(
    path: Path,
) -> pd.DataFrame:
    frame = pd.read_csv(
        path,
        sep=";",
        low_memory=False,
    )

    columns = _normalise_columns(frame)

    parsed = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(
                frame[columns["timestamp"]],
                errors="coerce",
                utc=True,
                format="mixed",
            ),
            "open": pd.to_numeric(
                frame[columns["open"]],
                errors="coerce",
            ),
            "high": pd.to_numeric(
                frame[columns["high"]],
                errors="coerce",
            ),
            "low": pd.to_numeric(
                frame[columns["low"]],
                errors="coerce",
            ),
            "close": pd.to_numeric(
                frame[columns["close"]],
                errors="coerce",
            ),
            "volume": pd.to_numeric(
                frame[columns["volume"]],
                errors="coerce",
            ),
        }
    )

    invalid = parsed.isna().any(axis=1)

    if invalid.any():
        examples = (
            parsed.loc[invalid]
            .head(5)
            .to_dict(orient="records")
        )
        raise DuplicateAuditError(
            f"{path.name} contains unparseable rows. "
            f"Examples: {examples}"
        )

    return parsed


def _is_inside_locked_cash_session(
    timestamp: pd.Timestamp,
) -> bool:
    local = timestamp.tz_convert(
        NEW_YORK
    )

    return (
        QUICK_START <= local.date() <= QUICK_END
        and SESSION_START <= local.time() < SESSION_END
    )


def _format_unique(
    values: pd.Series,
) -> str:
    unique = sorted(
        {
            float(value)
            for value in values
        }
    )

    return "|".join(
        f"{value:.10g}"
        for value in unique
    )


def _audit_duplicate_group(
    *,
    symbol: str,
    path: str | Path,
    timestamp: pd.Timestamp,
    group: pd.DataFrame,
) -> DuplicateRecord:
    path = Path(path)
    ohlc_columns = [
        "open",
        "high",
        "low",
        "close",
    ]

    unique_ohlc = (
        group[ohlc_columns]
        .drop_duplicates()
    )
    unique_ohlcv = (
        group[
            ohlc_columns + ["volume"]
        ]
        .drop_duplicates()
    )

    if len(unique_ohlcv) == 1:
        classification = "EXACT_OHLCV_DUPLICATE"
    elif len(unique_ohlc) == 1:
        classification = "VOLUME_ONLY_CONFLICT"
    else:
        classification = "OHLC_CONFLICT"

    minimum_volume = float(
        group["volume"].min()
    )
    maximum_volume = float(
        group["volume"].max()
    )

    ratio: float | None

    if minimum_volume > 0:
        ratio = maximum_volume / minimum_volume
    else:
        ratio = None

    local = timestamp.tz_convert(
        NEW_YORK
    )

    return DuplicateRecord(
        symbol=symbol,
        file=path.name,
        timestamp_utc=timestamp.isoformat(),
        timestamp_new_york=local.isoformat(),
        inside_locked_cash_session=(
            _is_inside_locked_cash_session(
                timestamp
            )
        ),
        classification=classification,
        copies=int(len(group)),
        unique_ohlc_rows=int(
            len(unique_ohlc)
        ),
        unique_volume_values=int(
            group["volume"].nunique()
        ),
        open_values=_format_unique(
            group["open"]
        ),
        high_values=_format_unique(
            group["high"]
        ),
        low_values=_format_unique(
            group["low"]
        ),
        close_values=_format_unique(
            group["close"]
        ),
        volume_values=_format_unique(
            group["volume"]
        ),
        minimum_volume=minimum_volume,
        maximum_volume=maximum_volume,
        maximum_to_minimum_volume_ratio=ratio,
    )


def audit_symbol(
    symbol: str,
) -> list[DuplicateRecord]:
    folder = ROOT / symbol
    paths = sorted(
        folder.glob("*.csv")
    )

    if not paths:
        raise DuplicateAuditError(
            f"No CSV files found in {folder}."
        )

    records: list[DuplicateRecord] = []

    for path in paths:
        frame = _parse_file(
            path
        )

        duplicated = frame[
            frame["timestamp"].duplicated(
                keep=False
            )
        ]

        if duplicated.empty:
            continue

        for timestamp, group in duplicated.groupby(
            "timestamp",
            sort=True,
        ):
            records.append(
                _audit_duplicate_group(
                    symbol=symbol,
                    path=path,
                    timestamp=pd.Timestamp(
                        timestamp
                    ),
                    group=group,
                )
            )

    return records


def build_summary(
    records: list[DuplicateRecord],
) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "schema_version": 1,
        "experiment_id": "EXP-005",
        "purpose": (
            "Duplicate-timestamp source audit only. "
            "No strategy results are calculated."
        ),
        "quick_period": {
            "start": QUICK_START.isoformat(),
            "end": QUICK_END.isoformat(),
        },
        "research_session": (
            "09:30–16:00 America/New_York"
        ),
        "total_duplicate_timestamps": len(
            records
        ),
        "inside_locked_cash_session": 0,
        "outside_locked_cash_session": 0,
        "classifications": {},
        "inside_session_classifications": {},
        "symbols": {},
    }

    for record in records:
        location_key = (
            "inside_locked_cash_session"
            if record.inside_locked_cash_session
            else "outside_locked_cash_session"
        )
        summary[location_key] += 1

        classifications = summary[
            "classifications"
        ]
        classifications[
            record.classification
        ] = (
            classifications.get(
                record.classification,
                0,
            )
            + 1
        )

        if record.inside_locked_cash_session:
            inside = summary[
                "inside_session_classifications"
            ]
            inside[
                record.classification
            ] = (
                inside.get(
                    record.classification,
                    0,
                )
                + 1
            )

        symbol_summary = summary[
            "symbols"
        ].setdefault(
            record.symbol,
            {
                "duplicate_timestamps": 0,
                "inside_session": 0,
                "volume_only_inside_session": 0,
                "ohlc_conflicts_inside_session": 0,
            },
        )

        symbol_summary[
            "duplicate_timestamps"
        ] += 1

        if record.inside_locked_cash_session:
            symbol_summary[
                "inside_session"
            ] += 1

            if (
                record.classification
                == "VOLUME_ONLY_CONFLICT"
            ):
                symbol_summary[
                    "volume_only_inside_session"
                ] += 1

            if (
                record.classification
                == "OHLC_CONFLICT"
            ):
                symbol_summary[
                    "ohlc_conflicts_inside_session"
                ] += 1

    summary["decision_support"] = {
        "all_inside_session_conflicts_are_volume_only": (
            summary[
                "inside_session_classifications"
            ].get(
                "OHLC_CONFLICT",
                0,
            )
            == 0
        ),
        "safe_to_consider_max_volume_rule": (
            summary[
                "inside_session_classifications"
            ].get(
                "OHLC_CONFLICT",
                0,
            )
            == 0
            and summary[
                "inside_session_classifications"
            ].get(
                "VOLUME_ONLY_CONFLICT",
                0,
            )
            > 0
        ),
    }

    return summary


def main() -> None:
    print()
    print(
        "========== EXP-005 DUPLICATE AUDIT =========="
    )
    print(
        "Purpose: source diagnostics only"
    )
    print(
        "Strategy calculations: DISABLED"
    )
    print(
        "Confirmation period: BLOCKED"
    )
    print()

    records = (
        audit_symbol("NQ")
        + audit_symbol("MNQ")
    )

    summary = build_summary(
        records
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    details_path = (
        OUTPUT_DIR
        / "duplicate_timestamp_details.csv"
    )
    summary_path = (
        OUTPUT_DIR
        / "duplicate_timestamp_summary.json"
    )

    details = pd.DataFrame(
        [
            record.to_dict()
            for record in records
        ]
    )

    details.to_csv(
        details_path,
        index=False,
    )

    summary_path.write_text(
        json.dumps(
            summary,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        "Duplicate timestamps: "
        f"{summary['total_duplicate_timestamps']}"
    )
    print(
        "Inside research session: "
        f"{summary['inside_locked_cash_session']}"
    )
    print(
        "Outside research session: "
        f"{summary['outside_locked_cash_session']}"
    )
    print()

    print("Inside-session classifications:")

    inside = summary[
        "inside_session_classifications"
    ]

    for name in (
        "EXACT_OHLCV_DUPLICATE",
        "VOLUME_ONLY_CONFLICT",
        "OHLC_CONFLICT",
    ):
        print(
            f"  {name}: "
            f"{inside.get(name, 0)}"
        )

    print()

    if inside.get(
        "OHLC_CONFLICT",
        0,
    ) > 0:
        print(
            "RESULT: PRICE CONFLICTS FOUND"
        )
        print(
            "Do not change the importer or run EXP-005."
        )
    elif inside.get(
        "VOLUME_ONLY_CONFLICT",
        0,
    ) > 0:
        print(
            "RESULT: ALL RESEARCH-SESSION CONFLICTS "
            "ARE VOLUME-ONLY"
        )
        print(
            "A locked max-volume normalisation rule may "
            "be considered because EXP-005 does not use "
            "volume."
        )
    else:
        print(
            "RESULT: NO RESEARCH-SESSION CONFLICTS"
        )

    print()
    print(
        f"Details: {details_path.resolve()}"
    )
    print(
        f"Summary: {summary_path.resolve()}"
    )
    print(
        "============================================="
    )


if __name__ == "__main__":
    main()
