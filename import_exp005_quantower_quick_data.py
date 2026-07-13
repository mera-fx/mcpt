from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
from typing import Any

import pandas as pd

from exp005_preregistration import (
    get_exp005_preregistration,
    validate_exp005_preregistration,
)
from exp005_quantower_import import (
    IncompleteExportError,
    INCOMING_ROOT,
    PROCESSED_ROOT,
    QQQ_CALENDAR_FILE,
    RESULTS_ROOT,
    build_processed_dataset,
    dataframe_sha256,
    sha256_file,
)
from exp005_source_amendment import (
    validate_exp005_source_amendment,
)
from experiment_lifecycle import (
    get_experiment_lifecycle,
)


PROJECT_DIR = Path(__file__).resolve().parent
AUDIT_FILE = (
    RESULTS_ROOT
    / "quantower_import_audit.json"
)
MANIFEST_FILE = (
    RESULTS_ROOT
    / "quantower_raw_manifest.json"
)
EXCLUDED_FILE = (
    RESULTS_ROOT
    / "quantower_excluded_sessions.csv"
)
PREFLIGHT_MISSING_FILE = (
    RESULTS_ROOT
    / "quantower_missing_expected_sessions.csv"
)
DECISION_FILE = (
    PROJECT_DIR
    / "results"
    / "EXP-005"
    / "quick_transfer"
    / "quick_transfer_decision.json"
)

OUTPUT_FILES = {
    "NQ_1m": (
        PROCESSED_ROOT
        / "NQ_1m_quick.parquet"
    ),
    "MNQ_1m": (
        PROCESSED_ROOT
        / "MNQ_1m_quick.parquet"
    ),
    "NQ_5m": (
        PROCESSED_ROOT
        / "NQ_5m_quick.parquet"
    ),
    "MNQ_5m": (
        PROCESSED_ROOT
        / "MNQ_5m_quick.parquet"
    ),
}


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Import and validate the locked EXP-005 "
            "Quantower NQ/MNQ quick-period CSV files."
        )
    )

    parser.add_argument(
        "--check-existing",
        action="store_true",
        help=(
            "Verify an existing completed import without "
            "rewriting any file."
        ),
    )

    return parser.parse_args()


def git_state() -> dict[str, Any]:
    commit = subprocess.run(
        [
            "git",
            "rev-parse",
            "HEAD",
        ],
        cwd=PROJECT_DIR,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    short_commit = subprocess.run(
        [
            "git",
            "rev-parse",
            "--short",
            "HEAD",
        ],
        cwd=PROJECT_DIR,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    status = subprocess.run(
        [
            "git",
            "status",
            "--porcelain",
        ],
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
    payload: dict[str, Any],
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


def incoming_csvs(
    symbol: str,
) -> list[Path]:
    folder = (
        INCOMING_ROOT
        / symbol
    )

    return sorted(
        folder.glob("*.csv"),
        key=lambda item: item.name.lower(),
    )


def _existing_import_complete() -> bool:
    required = [
        AUDIT_FILE,
        MANIFEST_FILE,
        EXCLUDED_FILE,
        *OUTPUT_FILES.values(),
    ]

    return all(
        path.exists()
        for path in required
    )


def verify_existing_import() -> None:
    if not _existing_import_complete():
        raise FileNotFoundError(
            "The EXP-005 import is incomplete or does not exist."
        )

    audit = json.loads(
        AUDIT_FILE.read_text(
            encoding="utf-8"
        )
    )

    manifest = json.loads(
        MANIFEST_FILE.read_text(
            encoding="utf-8"
        )
    )

    for name, path in OUTPUT_FILES.items():
        frame = pd.read_parquet(
            path
        )

        frame.index = pd.to_datetime(
            frame.index,
            utc=True,
        )

        actual = dataframe_sha256(
            frame
        )

        expected = audit[
            "fingerprints"
        ][name]

        if actual != expected:
            raise RuntimeError(
                f"Existing {name} data does not match its audit."
            )

    for record in manifest[
        "files"
    ]:
        archived = Path(
            record["archived_path"]
        )

        if not archived.exists():
            raise RuntimeError(
                f"Archived raw file is missing: {archived}"
            )

        if sha256_file(
            archived
        ) != record["sha256"]:
            raise RuntimeError(
                f"Archived raw file changed: {archived}"
            )

    print()
    print(
        "EXP-005 existing Quantower import passed "
        "hash verification."
    )
    print(
        f"Sessions: {audit['included_sessions']:,}"
    )
    print(
        "NQ one-minute rows: "
        f"{audit['included_nq_one_minute_rows']:,}"
    )
    print(
        "MNQ one-minute rows: "
        f"{audit['included_mnq_one_minute_rows']:,}"
    )
    print(
        "Confirmation period requested: "
        f"{audit['confirmation_period_requested']}"
    )


def main() -> None:
    arguments = parse_arguments()

    validate_exp005_preregistration()
    validate_exp005_source_amendment()

    lifecycle = get_experiment_lifecycle(
        "EXP-005"
    )

    if lifecycle.stage != "PRE_REGISTERED":
        raise RuntimeError(
            "EXP-005 data import is allowed only while "
            "the lifecycle is PRE_REGISTERED."
        )

    record = get_exp005_preregistration()

    if record["results_viewed"] != "NONE":
        raise RuntimeError(
            "EXP-005 results have already been disclosed."
        )

    if (
        record["research_split"][
            "confirmation_access"
        ]
        != "LOCKED_UNTIL_QUICK_PASS"
    ):
        raise RuntimeError(
            "EXP-005 confirmation-period lock changed."
        )

    if DECISION_FILE.exists():
        raise RuntimeError(
            "The EXP-005 quick-transfer decision already exists. "
            "Research data cannot be imported or replaced."
        )

    git = git_state()

    if not git["working_tree_clean"]:
        raise RuntimeError(
            "Commit and push the protected EXP-005 importer "
            "before importing research data. Git must be clean."
        )

    if arguments.check_existing:
        verify_existing_import()
        return

    if _existing_import_complete():
        verify_existing_import()
        print()
        print(
            "No files were rewritten. The EXP-005 data is frozen."
        )
        return

    existing_partial = [
        path
        for path in [
            AUDIT_FILE,
            MANIFEST_FILE,
            EXCLUDED_FILE,
            *OUTPUT_FILES.values(),
        ]
        if path.exists()
    ]

    if existing_partial:
        names = "\n".join(
            f"- {path}"
            for path in existing_partial
        )

        raise RuntimeError(
            "A partial EXP-005 import exists. Do not overwrite it "
            "automatically. Inspect or remove the partial files "
            "before the first successful import:\n"
            + names
        )

    nq_paths = incoming_csvs(
        "NQ"
    )

    mnq_paths = incoming_csvs(
        "MNQ"
    )

    if not nq_paths or not mnq_paths:
        raise FileNotFoundError(
            "Place Quantower CSV exports in both:\n"
            f"- {INCOMING_ROOT / 'NQ'}\n"
            f"- {INCOMING_ROOT / 'MNQ'}"
        )

    print()
    print(
        "========== EXP-005 QUANTOWER IMPORT =========="
    )
    print(
        "Source:       Lucid Trading / Rithmic"
    )
    print(
        "Application:  Quantower History Exporter"
    )
    print(
        "Symbols:      NQ, MNQ provider front month"
    )
    print(
        "Quick period: 2019-05-06 through 2022-12-30"
    )
    print(
        "Confirmation: BLOCKED"
    )
    print(
        f"NQ files:     {len(nq_paths)}"
    )
    print(
        f"MNQ files:    {len(mnq_paths)}"
    )
    print(
        f"Git commit:   {git['short_commit']}"
    )
    print()

    try:
        processed = build_processed_dataset(
            nq_paths=nq_paths,
            mnq_paths=mnq_paths,
            qqq_calendar_path=QQQ_CALENDAR_FILE,
            archive_files=True,
        )
    except IncompleteExportError as error:
        if (
            error.missing_sessions is not None
            and not error.missing_sessions.empty
        ):
            _atomic_csv(
                error.missing_sessions,
                PREFLIGHT_MISSING_FILE,
            )

            print()
            print(
                "The export is incomplete. A complete missing-"
                "session list was saved to:"
            )
            print(
                PREFLIGHT_MISSING_FILE.resolve()
            )

        raise

    PREFLIGHT_MISSING_FILE.unlink(
        missing_ok=True
    )

    _atomic_parquet(
        processed.nq_1m,
        OUTPUT_FILES["NQ_1m"],
    )
    _atomic_parquet(
        processed.mnq_1m,
        OUTPUT_FILES["MNQ_1m"],
    )
    _atomic_parquet(
        processed.nq_5m,
        OUTPUT_FILES["NQ_5m"],
    )
    _atomic_parquet(
        processed.mnq_5m,
        OUTPUT_FILES["MNQ_5m"],
    )

    file_hashes = {
        name: sha256_file(path)
        for name, path in OUTPUT_FILES.items()
    }

    audit = {
        **processed.audit,
        "imported_at_utc": (
            datetime.now(
                timezone.utc
            ).isoformat(
                timespec="seconds"
            )
        ),
        "git": git,
        "files": {
            name: {
                "path": str(
                    path.resolve()
                ),
                "sha256": file_hashes[name],
            }
            for name, path in OUTPUT_FILES.items()
        },
        "raw_manifest_file": str(
            MANIFEST_FILE.resolve()
        ),
        "excluded_sessions_file": str(
            EXCLUDED_FILE.resolve()
        ),
        "strategy_results_calculated": False,
        "quick_transfer_decision_calculated": False,
        "confirmation_export_detected": False,
    }

    manifest_payload = {
        "experiment_id": "EXP-005",
        "source": (
            "Lucid Trading / Rithmic via Quantower "
            "History Exporter"
        ),
        "raw_files_immutable": True,
        "files": [
            item.to_dict()
            for item in processed.manifest
        ],
    }

    _atomic_json(
        audit,
        AUDIT_FILE,
    )
    _atomic_json(
        manifest_payload,
        MANIFEST_FILE,
    )
    _atomic_csv(
        processed.excluded_sessions,
        EXCLUDED_FILE,
    )

    print(
        "Import completed."
    )
    print(
        "Included sessions: "
        f"{audit['included_sessions']:,}"
    )
    print(
        "NQ one-minute rows: "
        f"{audit['included_nq_one_minute_rows']:,}"
    )
    print(
        "MNQ one-minute rows: "
        f"{audit['included_mnq_one_minute_rows']:,}"
    )
    print(
        "NQ five-minute rows: "
        f"{audit['included_nq_five_minute_rows']:,}"
    )
    print(
        "MNQ five-minute rows: "
        f"{audit['included_mnq_five_minute_rows']:,}"
    )
    print(
        "Potential front-month mismatch sessions excluded: "
        f"{audit['potential_front_month_mismatch_sessions_excluded']}"
    )
    print(
        "Included invalid sessions: "
        f"{audit['included_invalid_sessions']}"
    )
    print(
        "Strategy results calculated: False"
    )
    print(
        "Confirmation period remained locked."
    )
    print(
        f"Audit: {AUDIT_FILE}"
    )
    print(
        "================================================"
    )


if __name__ == "__main__":
    main()
