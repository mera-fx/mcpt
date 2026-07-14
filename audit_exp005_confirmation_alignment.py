from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

import pandas as pd

import exp005_quantower_import as base
from exp005_confirmation_import import (
    CONFIRMATION_END,
    CONFIRMATION_START,
    INCOMING_ROOT,
    RECHECK_ROOT,
    RESULTS_ROOT,
    SESSION_RETRY_ROOT,
    confirmation_period_context,
    load_confirmation_calendar,
    load_confirmation_recheck_corrections,
)
from exp005_confirmation_missing_session_resolution import (
    load_confirmation_session_retry_evidence,
    restore_locked_confirmation_session,
    validate_locked_confirmation_missing_sessions,
)
from exp005_quick_transfer_result import (
    verify_local_quick_transfer_decision,
)
from experiment_lifecycle import (
    get_experiment_lifecycle,
)


OUTPUT_DIR = (
    RESULTS_ROOT
    / "alignment_audit"
)
CSV_FILE = (
    OUTPUT_DIR
    / "potential_front_month_mismatch_sessions.csv"
)
JSON_FILE = (
    OUTPUT_DIR
    / "potential_front_month_mismatch_summary.json"
)


class ConfirmationAlignmentAuditError(
    RuntimeError
):
    pass


def _csvs(
    root: Path,
    symbol: str,
) -> list[Path]:
    return sorted(
        (root / symbol).glob("*.csv"),
        key=lambda item: item.name.lower(),
    )


def validate_stage() -> None:
    verify_local_quick_transfer_decision()
    lifecycle = get_experiment_lifecycle(
        "EXP-005"
    )

    if lifecycle.stage != "FULL_VALIDATION":
        raise ConfirmationAlignmentAuditError(
            "EXP-005 must remain in FULL_VALIDATION."
        )


def enrich_alignment_exclusions(
    exclusions: pd.DataFrame,
    *,
    nq_data: pd.DataFrame,
    mnq_data: pd.DataFrame,
) -> pd.DataFrame:
    columns = [
        "symbol",
        "session_date",
        "reason",
        "median_close_difference",
        "maximum_close_difference",
        "maximum_difference_timestamp_utc",
        "maximum_difference_timestamp_new_york",
        "nq_close_at_maximum",
        "mnq_close_at_maximum",
        "signed_nq_minus_mnq_at_maximum",
        "minutes_difference_over_5_points",
        "minutes_difference_over_20_points",
        "first_over_20_timestamp_utc",
        "last_over_20_timestamp_utc",
    ]

    if exclusions.empty:
        return pd.DataFrame(columns=columns)

    rows: list[dict[str, Any]] = []

    for item in exclusions.to_dict(
        orient="records"
    ):
        session = str(
            item["session_date"]
        )
        nq_session = nq_data.loc[
            nq_data["session_date"].astype(str)
            == session
        ]
        mnq_session = mnq_data.loc[
            mnq_data["session_date"].astype(str)
            == session
        ]

        if not nq_session.index.equals(
            mnq_session.index
        ):
            rows.append(
                {
                    **item,
                    "maximum_difference_timestamp_utc": None,
                    "maximum_difference_timestamp_new_york": None,
                    "nq_close_at_maximum": None,
                    "mnq_close_at_maximum": None,
                    "signed_nq_minus_mnq_at_maximum": None,
                    "minutes_difference_over_5_points": None,
                    "minutes_difference_over_20_points": None,
                    "first_over_20_timestamp_utc": None,
                    "last_over_20_timestamp_utc": None,
                }
            )
            continue

        signed = (
            nq_session["close"].astype(float)
            - mnq_session["close"].astype(float)
        )
        absolute = signed.abs()
        maximum_timestamp = pd.Timestamp(
            absolute.idxmax()
        )
        over_twenty = absolute[
            absolute
            > base.MAX_SINGLE_CLOSE_DIFFERENCE
        ]

        rows.append(
            {
                **item,
                "maximum_difference_timestamp_utc": (
                    maximum_timestamp.isoformat()
                ),
                "maximum_difference_timestamp_new_york": (
                    maximum_timestamp
                    .tz_convert(base.NEW_YORK_TZ)
                    .isoformat()
                ),
                "nq_close_at_maximum": float(
                    nq_session.loc[
                        maximum_timestamp,
                        "close",
                    ]
                ),
                "mnq_close_at_maximum": float(
                    mnq_session.loc[
                        maximum_timestamp,
                        "close",
                    ]
                ),
                "signed_nq_minus_mnq_at_maximum": float(
                    signed.loc[
                        maximum_timestamp
                    ]
                ),
                "minutes_difference_over_5_points": int(
                    (
                        absolute
                        > base.MAX_MEDIAN_CLOSE_DIFFERENCE
                    ).sum()
                ),
                "minutes_difference_over_20_points": int(
                    len(over_twenty)
                ),
                "first_over_20_timestamp_utc": (
                    pd.Timestamp(
                        over_twenty.index[0]
                    ).isoformat()
                    if len(over_twenty)
                    else None
                ),
                "last_over_20_timestamp_utc": (
                    pd.Timestamp(
                        over_twenty.index[-1]
                    ).isoformat()
                    if len(over_twenty)
                    else None
                ),
            }
        )

    return pd.DataFrame(
        rows,
        columns=columns,
    )


def build_alignment_audit() -> tuple[
    pd.DataFrame,
    dict[str, Any],
]:
    expected_sessions = (
        load_confirmation_calendar()
    )

    nq_paths = _csvs(
        INCOMING_ROOT,
        "NQ",
    )
    mnq_paths = _csvs(
        INCOMING_ROOT,
        "MNQ",
    )
    nq_rechecks = _csvs(
        RECHECK_ROOT,
        "NQ",
    )
    mnq_rechecks = _csvs(
        RECHECK_ROOT,
        "MNQ",
    )
    nq_retries = _csvs(
        SESSION_RETRY_ROOT,
        "NQ",
    )
    mnq_retries = _csvs(
        SESSION_RETRY_ROOT,
        "MNQ",
    )

    expected_counts = {
        "NQ full exports": (
            len(nq_paths),
            1,
        ),
        "MNQ full exports": (
            len(mnq_paths),
            1,
        ),
        "NQ rechecks": (
            len(nq_rechecks),
            1,
        ),
        "MNQ rechecks": (
            len(mnq_rechecks),
            1,
        ),
        "NQ session retries": (
            len(nq_retries),
            3,
        ),
        "MNQ session retries": (
            len(mnq_retries),
            3,
        ),
    }

    invalid_counts = [
        f"{name}: observed {observed}, "
        f"expected {expected}"
        for name, (observed, expected)
        in expected_counts.items()
        if observed != expected
    ]

    if invalid_counts:
        raise ConfirmationAlignmentAuditError(
            "Confirmation source-file layout changed. "
            + "; ".join(invalid_counts)
        )

    with confirmation_period_context():
        (
            nq_corrections,
            _,
        ) = load_confirmation_recheck_corrections(
            nq_rechecks,
            symbol="NQ",
        )
        (
            mnq_corrections,
            _,
        ) = load_confirmation_recheck_corrections(
            mnq_rechecks,
            symbol="MNQ",
        )

        nq_retry = (
            load_confirmation_session_retry_evidence(
                nq_retries,
                symbol="NQ",
            )
        )
        mnq_retry = (
            load_confirmation_session_retry_evidence(
                mnq_retries,
                symbol="MNQ",
            )
        )

        nq_import = base.load_symbol_chunks(
            nq_paths,
            symbol="NQ",
            corrections=nq_corrections,
        )
        mnq_import = base.load_symbol_chunks(
            mnq_paths,
            symbol="MNQ",
            corrections=mnq_corrections,
        )

        (
            nq_import,
            nq_restored_bars,
        ) = restore_locked_confirmation_session(
            nq_import,
            nq_retry,
        )
        (
            mnq_import,
            mnq_restored_bars,
        ) = restore_locked_confirmation_session(
            mnq_import,
            mnq_retry,
        )

        nq = base.extract_complete_sessions(
            nq_import,
            expected_sessions=expected_sessions,
        )
        mnq = base.extract_complete_sessions(
            mnq_import,
            expected_sessions=expected_sessions,
        )

        missing_expected = (
            base._strict_missing_session_rows(
                expected_sessions,
                nq,
                mnq,
            )
        )
        locked_exclusions = (
            validate_locked_confirmation_missing_sessions(
                missing_expected=missing_expected,
            )
        )

        aligned = base.align_nq_mnq(
            nq,
            mnq,
        )

    details = enrich_alignment_exclusions(
        aligned.excluded_mismatch_sessions,
        nq_data=nq.data,
        mnq_data=mnq.data,
    )

    nq_complete = int(
        nq.data["session_date"].nunique()
    )
    mnq_complete = int(
        mnq.data["session_date"].nunique()
    )
    common_complete = len(
        set(
            nq.data["session_date"].astype(str)
        ).intersection(
            set(
                mnq.data["session_date"].astype(str)
            )
        )
    )
    aligned_count = int(
        aligned.nq_1m[
            "session_date"
        ].nunique()
    )

    summary: dict[str, Any] = {
        "schema_version": 1,
        "experiment_id": "EXP-005",
        "stage": "FULL_VALIDATION",
        "purpose": (
            "Confirmation NQ/MNQ alignment "
            "diagnostic only. No strategy "
            "result is calculated."
        ),
        "calculated_at_utc": (
            datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat()
        ),
        "confirmation_period": {
            "start": (
                CONFIRMATION_START.isoformat()
            ),
            "end": (
                CONFIRMATION_END.isoformat()
            ),
        },
        "calendar_sessions": int(
            len(expected_sessions)
        ),
        "locked_provider_unavailable_sessions": int(
            len(
                set(
                    locked_exclusions[
                        "session_date"
                    ].astype(str)
                )
            )
        ),
        "nq_complete_sessions_before_alignment": (
            nq_complete
        ),
        "mnq_complete_sessions_before_alignment": (
            mnq_complete
        ),
        "common_complete_sessions_before_alignment": (
            common_complete
        ),
        "potential_front_month_mismatch_sessions": int(
            len(details)
        ),
        "included_sessions_after_alignment": (
            aligned_count
        ),
        "nq_retry_bars_restored": int(
            nq_restored_bars
        ),
        "mnq_retry_bars_restored": int(
            mnq_restored_bars
        ),
        "alignment_thresholds": {
            "maximum_allowed_median_close_difference_points": (
                base.MAX_MEDIAN_CLOSE_DIFFERENCE
            ),
            "maximum_allowed_single_close_difference_points": (
                base.MAX_SINGLE_CLOSE_DIFFERENCE
            ),
        },
        "mismatch_dates": (
            details["session_date"]
            .astype(str)
            .tolist()
        ),
        "strategy_results_calculated": False,
        "full_validation_results_calculated": False,
        "quick_transfer_rerun": False,
        "source_files_modified": False,
    }

    return details, summary


def main() -> None:
    validate_stage()

    print()
    print(
        "===== EXP-005 CONFIRMATION ALIGNMENT AUDIT ====="
    )
    print(
        "Purpose: NQ/MNQ front-month alignment "
        "diagnostics only"
    )
    print(
        "Strategy calculations: DISABLED"
    )
    print(
        "Full-validation decision: NOT CALCULATED"
    )
    print()

    details, summary = (
        build_alignment_audit()
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )
    details.to_csv(
        CSV_FILE,
        index=False,
    )
    JSON_FILE.write_text(
        json.dumps(
            summary,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        "Common complete sessions before alignment: "
        f"{summary['common_complete_sessions_before_alignment']}"
    )
    print(
        "Potential front-month mismatch sessions: "
        f"{summary['potential_front_month_mismatch_sessions']}"
    )
    print(
        "Included sessions after alignment: "
        f"{summary['included_sessions_after_alignment']}"
    )
    print()

    if details.empty:
        print(
            "No alignment exclusions were detected."
        )
    else:
        print(
            "Excluded dates and close differences:"
        )
        for row in details.itertuples(
            index=False
        ):
            print(
                "  "
                f"{row.session_date}: "
                f"median={row.median_close_difference:.2f}, "
                f"max={row.maximum_close_difference:.2f}, "
                f"minutes>20="
                f"{row.minutes_difference_over_20_points}"
            )

    print()
    print(
        f"Details: {CSV_FILE.resolve()}"
    )
    print(
        f"Summary: {JSON_FILE.resolve()}"
    )
    print(
        "No source data or strategy result was changed."
    )
    print(
        "================================================"
    )


if __name__ == "__main__":
    main()
