from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import pandas as pd

from alpaca_historical_data import (
    AlpacaHistoricalDataError,
    atomic_parquet_write,
    clean_full_regular_sessions,
    fetch_market_calendar,
    fetch_stock_bars,
    validate_exp004_clean_data,
)
from exp004_preregistration import (
    get_exp004_preregistration,
    validate_exp004_preregistration,
)
from experiment_lifecycle import (
    get_experiment_lifecycle,
)
from run_provenance import (
    git_state,
    json_ready,
    sha256_file,
)


PROJECT_DIR = Path(__file__).resolve().parent
DATA_FILE = (
    PROJECT_DIR
    / "data"
    / "QQQ_5m_SIP.parquet"
)
RESULTS_DIR = (
    PROJECT_DIR
    / "results"
    / "EXP-004"
    / "data"
)
AUDIT_FILE = (
    RESULTS_DIR
    / "in_sample_data_audit.json"
)
EXCLUDED_FILE = (
    RESULTS_DIR
    / "excluded_sessions.csv"
)
QUICK_DECISION_FILE = (
    PROJECT_DIR
    / "results"
    / "EXP-004"
    / "quick_screen"
    / "quick_screen_decision.json"
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Download and validate the locked "
            "EXP-004 QQQ in-sample SIP bars."
        )
    )

    parser.add_argument(
        "--replace",
        action="store_true",
        help=(
            "Replace an existing in-sample file. "
            "Not allowed after a quick-screen "
            "decision exists."
        ),
    )

    return parser.parse_args()


def _atomic_json(
    payload: dict,
    path: Path,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )

    temporary.write_text(
        json.dumps(
            json_ready(payload),
            indent=2,
        ),
        encoding="utf-8",
    )

    temporary.replace(path)


def _atomic_csv(
    frame: pd.DataFrame,
    path: Path,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )

    frame.to_csv(
        temporary,
        index=False,
    )

    temporary.replace(path)


def main() -> None:
    arguments = parse_arguments()

    validate_exp004_preregistration()
    preregistration = (
        get_exp004_preregistration()
    )

    lifecycle = get_experiment_lifecycle(
        "EXP-004"
    )

    if lifecycle.stage != "PRE_REGISTERED":
        raise RuntimeError(
            "The EXP-004 in-sample downloader "
            "is allowed only while the lifecycle "
            "is PRE_REGISTERED."
        )

    git = git_state(PROJECT_DIR)

    if git.get(
        "working_tree_dirty"
    ) is not False:
        raise RuntimeError(
            "Commit and push the EXP-004 "
            "implementation before downloading "
            "research data. Git must be clean."
        )

    if (
        QUICK_DECISION_FILE.exists()
        and arguments.replace
    ):
        raise RuntimeError(
            "The EXP-004 quick-screen decision "
            "already exists. The research data "
            "cannot be replaced."
        )

    if DATA_FILE.exists() and not (
        arguments.replace
    ):
        existing = pd.read_parquet(
            DATA_FILE
        )

        existing.index = pd.to_datetime(
            existing.index,
            utc=True,
        )

        validate_exp004_clean_data(
            existing,
            maximum_session_date=(
                "2022-12-30"
            ),
        )

        if not AUDIT_FILE.exists():
            raise RuntimeError(
                "The EXP-004 data file exists but its "
                "validation audit is missing. Before a "
                "quick-screen decision exists, rerun with "
                "--replace to recreate the complete "
                "validated dataset and audit."
            )

        existing_audit = json.loads(
            AUDIT_FILE.read_text(
                encoding="utf-8"
            )
        )

        existing_hash = sha256_file(
            DATA_FILE
        )

        if (
            existing_audit.get(
                "data_file_sha256"
            )
            != existing_hash
        ):
            raise RuntimeError(
                "The existing EXP-004 data file does "
                "not match its audit. Before a quick-"
                "screen decision exists, rerun with "
                "--replace."
            )

        print()
        print(
            "EXP-004 in-sample data already exists "
            "and passed validation."
        )
        print(
            f"Rows:     {len(existing):,}"
        )
        print(
            "Sessions: "
            f"{existing['session_date'].nunique():,}"
        )
        print(f"File:     {DATA_FILE}")
        print()
        print(
            "Use --replace only before the "
            "quick-screen decision if a deliberate "
            "clean download is required."
        )
        return

    split = preregistration[
        "research_split"
    ]

    start_date = split[
        "in_sample_start"
    ]

    end_date = split[
        "in_sample_end"
    ]

    # Add one day to the RFC3339 request end, then
    # enforce the locked local session dates during
    # cleaning. The requested history is years older
    # than Alpaca's delayed SIP boundary.
    request_end = (
        pd.Timestamp(end_date)
        + pd.Timedelta(days=1)
    ).strftime("%Y-%m-%d")

    print()
    print(
        "========== EXP-004 IN-SAMPLE DATA =========="
    )
    print("Market:      QQQ")
    print("Timeframe:   5 minutes")
    print("Feed:        SIP")
    print("Adjustment:  split")
    print(
        f"Period:      {start_date} through "
        f"{end_date}"
    )
    print("OOS request: DISABLED")
    print(
        f"Git commit:  "
        f"{git.get('short_commit')}"
    )
    print()
    print(
        "Downloading official market calendar..."
    )

    try:
        calendar = fetch_market_calendar(
            start=start_date,
            end=end_date,
        )

        print(
            "Downloading historical QQQ SIP bars..."
        )

        bars = fetch_stock_bars(
            symbol="QQQ",
            start=start_date,
            end=request_end,
            timeframe="5Min",
            feed="sip",
            adjustment="split",
            limit=10_000,
        )
    except AlpacaHistoricalDataError as error:
        print()
        print(str(error))
        print()
        print(
            "Create a free Alpaca account, generate "
            "market-data API keys, then run:"
        )
        print(
            r".\setup_alpaca_credentials.ps1"
        )
        raise SystemExit(1) from error

    cleaned = clean_full_regular_sessions(
        bars=bars,
        calendar=calendar,
        start_date=start_date,
        end_date=end_date,
    )

    DATA_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    atomic_parquet_write(
        cleaned.data,
        DATA_FILE,
    )

    data_hash = sha256_file(
        DATA_FILE
    )

    audit = {
        **cleaned.audit,
        "experiment_id": "EXP-004",
        "research_stage": (
            "PRE_REGISTERED_IS_ONLY"
        ),
        "symbol": "QQQ",
        "timeframe": "5Min",
        "feed": "sip",
        "adjustment": "split",
        "data_file": str(
            DATA_FILE
        ),
        "data_file_sha256": data_hash,
        "downloaded_at_utc": (
            datetime.now(
                timezone.utc
            ).isoformat(
                timespec="seconds"
            )
        ),
        "git_commit": git.get(
            "commit"
        ),
        "out_of_sample_requested": False,
        "out_of_sample_rows": 0,
    }

    _atomic_json(
        audit,
        AUDIT_FILE,
    )

    _atomic_csv(
        cleaned.excluded_sessions,
        EXCLUDED_FILE,
    )

    print()
    print("Data download completed.")
    print(
        f"Included sessions: "
        f"{audit['included_sessions']:,}"
    )
    print(
        f"Included rows:     "
        f"{audit['included_rows']:,}"
    )
    print(
        "Early closes excluded: "
        f"{audit['early_close_sessions_excluded']}"
    )
    print(
        "Incomplete sessions excluded: "
        f"{audit['incomplete_sessions_excluded']}"
    )
    print(
        "Included invalid sessions: "
        f"{audit['included_invalid_sessions']}"
    )
    print(f"Data:  {DATA_FILE}")
    print(f"Audit: {AUDIT_FILE}")
    print(
        "Out-of-sample data remained locked."
    )
    print(
        "============================================"
    )


if __name__ == "__main__":
    main()
