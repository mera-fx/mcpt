from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
from typing import Any

import pandas as pd

import exp005_quantower_import as base
from exp005_confirmation_import import (
    CALENDAR_FILE,
    CALENDAR_SHA256,
    CONFIRMATION_END,
    CONFIRMATION_START,
    INCOMING_ROOT,
    RECHECK_ROOT,
    SESSION_RETRY_ROOT,
    PROCESSED_ROOT,
    RESULTS_ROOT,
    build_confirmation_dataset,
    load_confirmation_calendar,
    sha256_file,
)
from exp005_quick_transfer_result import (
    EXPECTED_FILE_SHA256 as QUICK_RESULT_SHA256,
    verify_local_quick_transfer_decision,
)
from experiment_lifecycle import (
    get_experiment_lifecycle,
)


PROJECT_DIR = Path(__file__).resolve().parent
AUDIT_FILE = (
    RESULTS_ROOT
    / "quantower_confirmation_import_audit.json"
)
MANIFEST_FILE = (
    RESULTS_ROOT
    / "quantower_confirmation_raw_manifest.json"
)
EXCLUDED_FILE = (
    RESULTS_ROOT
    / "quantower_confirmation_excluded_sessions.csv"
)
MISSING_FILE = (
    RESULTS_ROOT
    / "quantower_confirmation_missing_expected_sessions.csv"
)
OUTPUT_FILES = {
    "NQ_1m": (
        PROCESSED_ROOT
        / "NQ_1m_confirmation.parquet"
    ),
    "MNQ_1m": (
        PROCESSED_ROOT
        / "MNQ_1m_confirmation.parquet"
    ),
    "NQ_5m": (
        PROCESSED_ROOT
        / "NQ_5m_confirmation.parquet"
    ),
    "MNQ_5m": (
        PROCESSED_ROOT
        / "MNQ_5m_confirmation.parquet"
    ),
}


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Import and validate the unlocked EXP-005 "
            "2023–2025 NQ/MNQ confirmation CSV files."
        )
    )
    parser.add_argument(
        "--check-existing",
        action="store_true",
        help=(
            "Verify an existing completed confirmation "
            "import without rewriting files."
        ),
    )
    return parser.parse_args()


def git_state() -> dict[str, Any]:
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=PROJECT_DIR,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    short_commit = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=PROJECT_DIR,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=PROJECT_DIR,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    return {
        "commit": commit,
        "short_commit": short_commit,
        "working_tree_clean": not bool(status),
    }


def _atomic_json(
    payload: Any,
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
            payload,
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


def _atomic_parquet(
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
    frame.to_parquet(
        temporary,
    )
    temporary.replace(path)


def csvs(
    symbol: str,
) -> list[Path]:
    return sorted(
        (INCOMING_ROOT / symbol).glob(
            "*.csv"
        ),
        key=lambda item: item.name.lower(),
    )


def recheck_csvs(
    symbol: str,
) -> list[Path]:
    return sorted(
        (RECHECK_ROOT / symbol).glob(
            "*.csv"
        ),
        key=lambda item: item.name.lower(),
    )


def session_retry_csvs(
    symbol: str,
) -> list[Path]:
    return sorted(
        (
            SESSION_RETRY_ROOT
            / symbol
        ).glob(
            "*.csv"
        ),
        key=lambda item: item.name.lower(),
    )


def validate_stage() -> None:
    lifecycle = get_experiment_lifecycle(
        "EXP-005"
    )

    if lifecycle.stage != "FULL_VALIDATION":
        raise RuntimeError(
            "EXP-005 lifecycle must be FULL_VALIDATION "
            "before confirmation data can be imported."
        )


def verify_existing_import() -> dict[str, Any]:
    verify_local_quick_transfer_decision()
    validate_stage()

    if not AUDIT_FILE.exists():
        raise FileNotFoundError(
            f"Confirmation audit is missing: {AUDIT_FILE}"
        )

    for path in OUTPUT_FILES.values():
        if not path.exists():
            raise FileNotFoundError(
                f"Confirmation output is missing: {path}"
            )

    audit = json.loads(
        AUDIT_FILE.read_text(
            encoding="utf-8"
        )
    )

    if (
        audit.get("confirmation_period_requested")
        is not True
        or audit.get("strategy_results_calculated")
        is not False
        or audit.get("full_validation_results_calculated")
        is not False
        or audit.get("quick_transfer_rerun")
        is not False
    ):
        raise RuntimeError(
            "Confirmation import protection fields changed."
        )

    if audit.get(
        "quick_transfer_result_sha256"
    ) != QUICK_RESULT_SHA256:
        raise RuntimeError(
            "Confirmation import is linked to a different "
            "quick-transfer result."
        )

    if audit.get(
        "confirmation_calendar_sha256"
    ) != CALENDAR_SHA256:
        raise RuntimeError(
            "Confirmation calendar fingerprint changed."
        )

    if (
        audit.get(
            "confirmation_missing_session_record_id"
        ) != "EXP-005-DQ4"
        or audit.get(
            "provider_unavailable_sessions_excluded"
        ) != 2
        or audit.get(
            "provider_complete_sessions_restored"
        ) != 1
        or audit.get(
            "bars_synthesized"
        ) != 0
    ):
        raise RuntimeError(
            "Confirmation missing-session resolution "
            "fields changed."
        )

    if (
        audit.get(
            "confirmation_alignment_record_id"
        ) != "EXP-005-DQ5"
        or audit.get(
            "potential_front_month_mismatch_sessions_excluded"
        ) != 9
        or audit.get(
            "persistent_cross_symbol_divergence_sessions_excluded"
        ) != 3
        or audit.get(
            "isolated_cross_symbol_divergence_sessions_excluded"
        ) != 6
        or audit.get(
            "included_front_month_mismatch_sessions"
        ) != 0
        or audit.get(
            "included_sessions"
        ) != 733
    ):
        raise RuntimeError(
            "Confirmation alignment resolution fields "
            "changed."
        )

    for name, path in OUTPUT_FILES.items():
        frame = pd.read_parquet(path)
        frame.index = pd.to_datetime(
            frame.index,
            utc=True,
        )
        actual = base.dataframe_sha256(
            frame
        )
        expected = audit[
            "fingerprints"
        ][name]

        if actual != expected:
            raise RuntimeError(
                f"{name} confirmation fingerprint changed."
            )

    print(
        "EXP-005 existing confirmation import "
        "passed hash verification."
    )
    print(
        f"Sessions: {audit['included_sessions']:,}"
    )
    print(
        "Strategy results calculated: False"
    )

    return audit


def main() -> None:
    arguments = parse_arguments()
    verify_local_quick_transfer_decision()
    validate_stage()
    load_confirmation_calendar()

    if arguments.check_existing:
        verify_existing_import()
        return

    git = git_state()

    if not git["working_tree_clean"]:
        raise RuntimeError(
            "Commit the confirmation importer and lifecycle "
            "advance before importing data. Git must be clean."
        )

    existing = [
        path
        for path in (
            AUDIT_FILE,
            MANIFEST_FILE,
            EXCLUDED_FILE,
            *OUTPUT_FILES.values(),
        )
        if path.exists()
    ]

    if existing:
        raise RuntimeError(
            "A confirmation import already exists. Use "
            "--check-existing instead of rewriting it."
        )

    nq_paths = csvs("NQ")
    mnq_paths = csvs("MNQ")
    nq_recheck_paths = recheck_csvs(
        "NQ"
    )
    mnq_recheck_paths = recheck_csvs(
        "MNQ"
    )
    nq_session_retry_paths = (
        session_retry_csvs(
            "NQ"
        )
    )
    mnq_session_retry_paths = (
        session_retry_csvs(
            "MNQ"
        )
    )

    print()
    print(
        "===== EXP-005 CONFIRMATION IMPORT ====="
    )
    print(
        "Source:       Lucid Trading / Rithmic"
    )
    print(
        "Application:  Quantower History Exporter"
    )
    print(
        "Period:       "
        f"{CONFIRMATION_START} through {CONFIRMATION_END}"
    )
    print(
        "Quick result: FROZEN PASS"
    )
    print(
        "Strategy:     NOT CALCULATED"
    )
    print(f"NQ files:     {len(nq_paths)}")
    print(f"MNQ files:    {len(mnq_paths)}")
    print(
        "NQ rechecks:  "
        f"{len(nq_recheck_paths)}"
    )
    print(
        "MNQ rechecks: "
        f"{len(mnq_recheck_paths)}"
    )
    print(
        "NQ session retries:  "
        f"{len(nq_session_retry_paths)}"
    )
    print(
        "MNQ session retries: "
        f"{len(mnq_session_retry_paths)}"
    )
    print(f"Git commit:   {git['short_commit']}")
    print()

    if (
        len(nq_paths) != 1
        or len(mnq_paths) != 1
    ):
        raise FileNotFoundError(
            "Keep exactly one full confirmation export "
            "in each incoming folder. Move the six locked "
            "one-day session retries into the dedicated "
            "session_retry folders."
        )

    if (
        len(nq_recheck_paths) != 1
        or len(mnq_recheck_paths) != 1
    ):
        raise FileNotFoundError(
            "Place exactly one locked 2024-11-06 "
            "recheck CSV in each confirmation recheck "
            "folder."
        )

    if (
        len(nq_session_retry_paths) != 3
        or len(mnq_session_retry_paths) != 3
    ):
        raise FileNotFoundError(
            "Place exactly three SHA-256-locked "
            "confirmation session retry CSV files in "
            "each session_retry folder."
        )

    try:
        processed = build_confirmation_dataset(
            nq_paths=nq_paths,
            mnq_paths=mnq_paths,
            nq_recheck_paths=nq_recheck_paths,
            mnq_recheck_paths=mnq_recheck_paths,
            nq_session_retry_paths=(
                nq_session_retry_paths
            ),
            mnq_session_retry_paths=(
                mnq_session_retry_paths
            ),
            archive_files=True,
        )
    except base.IncompleteExportError as error:
        if error.missing_sessions is not None:
            _atomic_csv(
                error.missing_sessions,
                MISSING_FILE,
            )
            print(
                "The confirmation export is incomplete. "
                "A missing-session list was saved to:"
            )
            print(MISSING_FILE.resolve())
        raise

    frames = {
        "NQ_1m": processed.nq_1m,
        "MNQ_1m": processed.mnq_1m,
        "NQ_5m": processed.nq_5m,
        "MNQ_5m": processed.mnq_5m,
    }

    fingerprints = {
        name: base.dataframe_sha256(frame)
        for name, frame in frames.items()
    }

    audit = {
        **processed.audit,
        "schema_version": 1,
        "confirmation_calendar_file": str(
            CALENDAR_FILE.resolve()
        ),
        "confirmation_calendar_sha256": (
            CALENDAR_SHA256
        ),
        "fingerprints": fingerprints,
        "git": git,
        "imported_at_utc": (
            datetime.now(
                timezone.utc
            ).replace(
                microsecond=0
            ).isoformat()
        ),
    }

    for name, frame in frames.items():
        _atomic_parquet(
            frame,
            OUTPUT_FILES[name],
        )

    _atomic_json(
        [
            item.to_dict()
            for item in processed.manifest
        ],
        MANIFEST_FILE,
    )
    _atomic_json(
        audit,
        AUDIT_FILE,
    )
    _atomic_csv(
        processed.excluded_sessions,
        EXCLUDED_FILE,
    )

    MISSING_FILE.unlink(
        missing_ok=True
    )

    print("Confirmation import completed.")
    print(
        f"Included sessions: "
        f"{audit['included_sessions']:,}"
    )
    print(
        f"NQ one-minute rows: "
        f"{audit['included_nq_one_minute_rows']:,}"
    )
    print(
        f"MNQ one-minute rows: "
        f"{audit['included_mnq_one_minute_rows']:,}"
    )
    print(
        f"NQ five-minute rows: "
        f"{audit['included_nq_five_minute_rows']:,}"
    )
    print(
        f"MNQ five-minute rows: "
        f"{audit['included_mnq_five_minute_rows']:,}"
    )
    print(
        "Provider-unavailable sessions excluded: "
        f"{audit['provider_unavailable_sessions_excluded']}"
    )
    print(
        "Complete retry sessions restored: "
        f"{audit['provider_complete_sessions_restored']}"
    )
    print(
        "Potential front-month mismatch sessions "
        f"excluded: "
        f"{audit['potential_front_month_mismatch_sessions_excluded']}"
    )
    print(
        "Included invalid sessions: 0"
    )
    print(
        "Strategy results calculated: False"
    )
    print(
        f"Audit: {AUDIT_FILE.resolve()}"
    )
    print(
        "======================================="
    )


if __name__ == "__main__":
    main()
