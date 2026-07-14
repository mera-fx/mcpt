from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import time
import json
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd

from exp005_confirmation_import import (
    CONFIRMATION_END,
    CONFIRMATION_START,
    INCOMING_ROOT,
    RESULTS_ROOT,
)
from exp005_quick_transfer_result import (
    verify_local_quick_transfer_decision,
)
from experiment_lifecycle import (
    get_experiment_lifecycle,
)


NEW_YORK = ZoneInfo("America/New_York")
SESSION_START = time(9, 30)
SESSION_END = time(16, 0)
OUTPUT_DIR = (
    RESULTS_ROOT
    / "duplicate_audit"
)


class ConfirmationDuplicateAuditError(
    RuntimeError
):
    pass


@dataclass(frozen=True)
class DuplicateRecord:
    symbol: str
    file: str
    timestamp_utc: str
    timestamp_new_york: str
    session_date: str
    inside_confirmation_period: bool
    inside_locked_cash_session: bool
    classification: str
    copies: int
    unique_ohlc_rows: int
    unique_ohlcv_rows: int
    unique_volume_values: int
    open_values: str
    high_values: str
    low_values: str
    close_values: str
    volume_values: str
    minimum_volume: float
    maximum_volume: float
    maximum_to_minimum_volume_ratio: (
        float | None
    )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return asdict(self)


def validate_stage() -> None:
    verify_local_quick_transfer_decision()

    lifecycle = get_experiment_lifecycle(
        "EXP-005"
    )

    if lifecycle.stage != "FULL_VALIDATION":
        raise ConfirmationDuplicateAuditError(
            "EXP-005 must remain in FULL_VALIDATION."
        )


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
                resolved[target] = lookup[
                    candidate
                ]
                break

        if target not in resolved:
            raise ConfirmationDuplicateAuditError(
                f"Missing required column for "
                f"{target}. Available columns: "
                f"{list(frame.columns)}"
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

    columns = _normalise_columns(
        frame
    )

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

    invalid = parsed.isna().any(
        axis=1
    )

    if invalid.any():
        examples = (
            parsed.loc[invalid]
            .head(5)
            .to_dict(
                orient="records"
            )
        )

        raise ConfirmationDuplicateAuditError(
            f"{path.name} contains "
            f"unparseable rows. Examples: "
            f"{examples}"
        )

    return parsed


def _inside_confirmation_period(
    timestamp: pd.Timestamp,
) -> bool:
    local = timestamp.tz_convert(
        NEW_YORK
    )

    return (
        CONFIRMATION_START
        <= local.date()
        <= CONFIRMATION_END
    )


def _inside_cash_session(
    timestamp: pd.Timestamp,
) -> bool:
    local = timestamp.tz_convert(
        NEW_YORK
    )

    return (
        _inside_confirmation_period(
            timestamp
        )
        and SESSION_START
        <= local.time()
        < SESSION_END
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
    ohlcv_columns = (
        ohlc_columns
        + ["volume"]
    )

    unique_ohlc = (
        group[ohlc_columns]
        .drop_duplicates()
    )
    unique_ohlcv = (
        group[ohlcv_columns]
        .drop_duplicates()
    )

    if len(unique_ohlcv) == 1:
        classification = (
            "EXACT_OHLCV_DUPLICATE"
        )
    elif len(unique_ohlc) == 1:
        classification = (
            "VOLUME_ONLY_CONFLICT"
        )
    else:
        classification = (
            "OHLC_CONFLICT"
        )

    minimum_volume = float(
        group["volume"].min()
    )
    maximum_volume = float(
        group["volume"].max()
    )

    ratio: float | None

    if minimum_volume > 0:
        ratio = (
            maximum_volume
            / minimum_volume
        )
    else:
        ratio = None

    local = timestamp.tz_convert(
        NEW_YORK
    )

    return DuplicateRecord(
        symbol=symbol,
        file=path.name,
        timestamp_utc=(
            timestamp.isoformat()
        ),
        timestamp_new_york=(
            local.isoformat()
        ),
        session_date=(
            local.date().isoformat()
        ),
        inside_confirmation_period=(
            _inside_confirmation_period(
                timestamp
            )
        ),
        inside_locked_cash_session=(
            _inside_cash_session(
                timestamp
            )
        ),
        classification=classification,
        copies=int(len(group)),
        unique_ohlc_rows=int(
            len(unique_ohlc)
        ),
        unique_ohlcv_rows=int(
            len(unique_ohlcv)
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
        maximum_to_minimum_volume_ratio=(
            ratio
        ),
    )


def audit_symbol(
    symbol: str,
) -> list[DuplicateRecord]:
    paths = sorted(
        (
            INCOMING_ROOT
            / symbol
        ).glob("*.csv"),
        key=lambda path: (
            path.name.lower()
        ),
    )

    if not paths:
        raise ConfirmationDuplicateAuditError(
            f"No confirmation CSV files "
            f"found for {symbol}."
        )

    records: list[
        DuplicateRecord
    ] = []

    for path in paths:
        frame = _parse_file(
            path
        )

        duplicated = frame[
            frame[
                "timestamp"
            ].duplicated(
                keep=False
            )
        ]

        if duplicated.empty:
            continue

        for timestamp, group in (
            duplicated.groupby(
                "timestamp",
                sort=True,
            )
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
    records: list[
        DuplicateRecord
    ],
) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "schema_version": 1,
        "experiment_id": "EXP-005",
        "stage": "FULL_VALIDATION",
        "purpose": (
            "Confirmation-period duplicate "
            "timestamp source audit only. "
            "No strategy result is calculated."
        ),
        "confirmation_period": {
            "start": (
                CONFIRMATION_START
                .isoformat()
            ),
            "end": (
                CONFIRMATION_END
                .isoformat()
            ),
        },
        "research_session": (
            "09:30–16:00 "
            "America/New_York"
        ),
        "total_duplicate_timestamps": (
            len(records)
        ),
        "inside_confirmation_cash_session": 0,
        "outside_confirmation_cash_session": 0,
        "classifications": {},
        "inside_session_classifications": {},
        "symbols": {},
        "ohlc_conflict_dates": [],
    }

    ohlc_dates: set[
        tuple[str, str]
    ] = set()

    for record in records:
        location_key = (
            "inside_confirmation_cash_session"
            if record
            .inside_locked_cash_session
            else "outside_confirmation_cash_session"
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

        if (
            record
            .inside_locked_cash_session
        ):
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
                ohlc_dates.add(
                    (
                        record.symbol,
                        record.session_date,
                    )
                )

    summary[
        "ohlc_conflict_dates"
    ] = [
        {
            "symbol": symbol,
            "session_date": session_date,
        }
        for symbol, session_date
        in sorted(ohlc_dates)
    ]

    summary[
        "strategy_results_calculated"
    ] = False
    summary[
        "full_validation_results_calculated"
    ] = False
    summary[
        "quick_transfer_rerun"
    ] = False

    return summary


def main() -> None:
    validate_stage()

    print()
    print(
        "===== EXP-005 CONFIRMATION DUPLICATE AUDIT ====="
    )
    print(
        "Purpose: confirmation source diagnostics only"
    )
    print(
        "Strategy calculations: DISABLED"
    )
    print(
        "Full-validation decision: NOT CALCULATED"
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
    plan_path = (
        OUTPUT_DIR
        / "ohlc_conflict_recheck_plan.csv"
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

    plan = pd.DataFrame(
        summary[
            "ohlc_conflict_dates"
        ],
        columns=[
            "symbol",
            "session_date",
        ],
    )
    plan.to_csv(
        plan_path,
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
        "Inside confirmation cash session: "
        f"{summary['inside_confirmation_cash_session']}"
    )
    print(
        "Outside confirmation cash session: "
        f"{summary['outside_confirmation_cash_session']}"
    )
    print()

    inside = summary[
        "inside_session_classifications"
    ]

    print(
        "Inside-session classifications:"
    )

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
    print(
        "Unique symbol/date rechecks required: "
        f"{len(summary['ohlc_conflict_dates'])}"
    )
    print()

    if inside.get(
        "OHLC_CONFLICT",
        0,
    ):
        print(
            "RESULT: PRICE CONFLICTS FOUND"
        )
        print(
            "Do not change the confirmation importer "
            "or run full validation."
        )
    else:
        print(
            "RESULT: NO CONFIRMATION CASH-SESSION "
            "PRICE CONFLICTS"
        )

    print()
    print(
        f"Details: {details_path.resolve()}"
    )
    print(
        f"Summary: {summary_path.resolve()}"
    )
    print(
        f"Recheck plan: {plan_path.resolve()}"
    )
    print(
        "================================================"
    )


if __name__ == "__main__":
    main()
