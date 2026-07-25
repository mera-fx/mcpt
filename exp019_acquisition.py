from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
from typing import Any

from exp019_acquisition_authorization import (
    get_exp019_acquisition_authorization,
    validate_exp019_acquisition_authorization,
)
from exp019_preregistration import (
    CONTRACT_PLAN,
    validate_exp019_preregistration,
)


PROJECT_DIR = Path(__file__).resolve().parent

LOCKED_AUTHORIZATION_COMMIT = (
    "4128730da71c3e279afdf0f776db9ce9a4ac11fc"
)

LOCKED_PATHS = (
    "exp019_preregistration.py",
    "research/EXP-019_preregistration.md",
    "exp019_cost_estimator.py",
    "exp019_acquisition_authorization.py",
    "research/EXP-019_acquisition_authorization.md",
)

COST_DIR = (
    PROJECT_DIR
    / "results"
    / "EXP-019"
    / "cost_estimate"
)

COST_JSON_PATH = (
    COST_DIR
    / "exp019_cost_estimate.json"
)

COST_CSV_PATH = (
    COST_DIR
    / "exp019_exact_contract_costs.csv"
)

ARCHIVE_ROOT = (
    PROJECT_DIR
    / "data"
    / "EXP-019"
    / "exact_contract_archive"
)

RAW_DIR = ARCHIVE_ROOT / "raw"

MANIFEST_PATH = (
    ARCHIVE_ROOT
    / "acquisition_manifest.json"
)

COMPLETION_PATH = (
    ARCHIVE_ROOT
    / "ACQUISITION_COMPLETE.json"
)

DATASET = "GLBX.MDP3"
SCHEMA = "ohlcv-1m"
STYPE_IN = "raw_symbol"
STYPE_OUT = "instrument_id"

EXPECTED_CONTRACT_COUNT = 66
QUOTED_TOTAL_USD = 22.914098
MAXIMUM_TOTAL_COST_USD = 35.0


def utc_now() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


def run_git(
    *args: str,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=PROJECT_DIR,
        text=True,
        capture_output=True,
        check=check,
    )


def sha256_file(
    path: Path,
) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for block in iter(
            lambda: handle.read(
                1024 * 1024
            ),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


def contract_plan_digest() -> str:
    encoded = json.dumps(
        list(CONTRACT_PLAN),
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")

    return hashlib.sha256(
        encoded
    ).hexdigest()


def atomic_write_json(
    path: Path,
    payload: dict[str, Any],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = path.with_name(
        path.name + ".tmp"
    )

    if temporary.exists():
        raise RuntimeError(
            f"Temporary metadata file already "
            f"exists: {temporary}"
        )

    temporary.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    os.replace(
        temporary,
        path,
    )


def load_cost_evidence() -> tuple[
    dict[str, Any],
    dict[str, dict[str, Any]],
]:
    authorization = (
        get_exp019_acquisition_authorization()
    )

    expected_json_hash = authorization[
        "cost_estimate"
    ]["cost_json_sha256"]

    expected_csv_hash = authorization[
        "cost_estimate"
    ]["cost_csv_sha256"]

    if not COST_JSON_PATH.is_file():
        raise RuntimeError(
            "Missing EXP-019 cost JSON."
        )

    if not COST_CSV_PATH.is_file():
        raise RuntimeError(
            "Missing EXP-019 cost CSV."
        )

    if (
        sha256_file(COST_JSON_PATH)
        != expected_json_hash
    ):
        raise RuntimeError(
            "EXP-019 cost JSON hash changed."
        )

    if (
        sha256_file(COST_CSV_PATH)
        != expected_csv_hash
    ):
        raise RuntimeError(
            "EXP-019 cost CSV hash changed."
        )

    summary = json.loads(
        COST_JSON_PATH.read_text(
            encoding="utf-8"
        )
    )

    if (
        summary["experiment_id"]
        != "EXP-019"
        or summary["classification"]
        != (
            "EXACT_CONTRACT_"
            "COST_ESTIMATE_COMPLETE"
        )
    ):
        raise RuntimeError(
            "EXP-019 cost evidence identity "
            "changed."
        )

    costs = summary["costs"]
    request = summary["request"]

    if (
        round(
            float(
                costs[
                    "exact_contract_total_usd"
                ]
            ),
            6,
        )
        != QUOTED_TOTAL_USD
        or float(
            costs[
                "maximum_download_cost_usd"
            ]
        )
        != MAXIMUM_TOTAL_COST_USD
        or costs["within_locked_cap"]
        is not True
        or request["contract_count"]
        != EXPECTED_CONTRACT_COUNT
        or request[
            "contract_plan_sha256"
        ]
        != contract_plan_digest()
    ):
        raise RuntimeError(
            "EXP-019 locked cost evidence "
            "changed."
        )

    quotes: dict[
        str,
        dict[str, Any],
    ] = {}

    for row in summary["contracts"]:
        symbol = row[
            "canonical_symbol"
        ]

        if symbol in quotes:
            raise RuntimeError(
                "Duplicate contract in cost "
                f"evidence: {symbol}"
            )

        quotes[symbol] = row

    if len(quotes) != EXPECTED_CONTRACT_COUNT:
        raise RuntimeError(
            "EXP-019 cost evidence does not "
            "contain 66 contracts."
        )

    for (
        canonical_symbol,
        raw_symbol,
        start,
        end_exclusive,
        expiration,
    ) in CONTRACT_PLAN:
        quote = quotes.get(
            canonical_symbol
        )

        if quote is None:
            raise RuntimeError(
                "Missing contract quote: "
                f"{canonical_symbol}"
            )

        if (
            quote["raw_symbol"]
            != raw_symbol
            or quote["start"]
            != start
            or quote["end_exclusive"]
            != end_exclusive
            or quote["expiration"]
            != expiration
        ):
            raise RuntimeError(
                "Contract quote changed: "
                f"{canonical_symbol}"
            )

    return summary, quotes


def output_filename(
    sequence: int,
    canonical_symbol: str,
    start: str,
    end_exclusive: str,
) -> str:
    return (
        f"{sequence:03d}_"
        f"{canonical_symbol}_"
        f"{start}_"
        f"{end_exclusive}."
        f"{SCHEMA}.dbn.zst"
    )


def partial_filename(
    final_name: str,
) -> str:
    suffix = ".dbn.zst"

    if not final_name.endswith(
        suffix
    ):
        raise ValueError(
            "Final DBN filename has an "
            "unexpected suffix."
        )

    return (
        final_name[
            :-len(suffix)
        ]
        + ".partial"
        + suffix
    )


def new_manifest(
    repository: dict[str, str],
) -> dict[str, Any]:
    now = utc_now()

    return {
        "schema_version": 1,
        "experiment_id": "EXP-019",
        "status": "IN_PROGRESS",
        "created_at_utc": now,
        "updated_at_utc": now,
        "authorization_commit": (
            LOCKED_AUTHORIZATION_COMMIT
        ),
        "repository": repository,
        "request": {
            "dataset": DATASET,
            "schema": SCHEMA,
            "stype_in": STYPE_IN,
            "stype_out": STYPE_OUT,
            "contract_count": (
                EXPECTED_CONTRACT_COUNT
            ),
            "contract_plan_sha256": (
                contract_plan_digest()
            ),
            "quoted_total_usd": (
                QUOTED_TOTAL_USD
            ),
            "maximum_total_cost_usd": (
                MAXIMUM_TOTAL_COST_USD
            ),
            "automatic_retries": 0,
        },
        "attempts": [],
        "completed": [],
        "interpretation": {
            "archive_qualified": False,
            "continuous_series_constructed": False,
            "strategy_run": False,
        },
    }


def read_manifest() -> (
    dict[str, Any] | None
):
    if not MANIFEST_PATH.exists():
        return None

    return json.loads(
        MANIFEST_PATH.read_text(
            encoding="utf-8"
        )
    )


def completed_by_symbol(
    manifest: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    completed: dict[
        str,
        dict[str, Any],
    ] = {}

    for entry in manifest[
        "completed"
    ]:
        symbol = entry[
            "canonical_symbol"
        ]

        if symbol in completed:
            raise RuntimeError(
                "Duplicate completed manifest "
                f"entry: {symbol}"
            )

        completed[symbol] = entry

    return completed


def attempted_estimated_cost(
    manifest: dict[str, Any],
) -> float:
    return sum(
        float(
            attempt[
                "estimated_cost_usd"
            ]
        )
        for attempt in manifest[
            "attempts"
        ]
    )


def verify_manifest(
    manifest: dict[str, Any],
) -> None:
    if (
        manifest["experiment_id"]
        != "EXP-019"
        or manifest[
            "authorization_commit"
        ]
        != LOCKED_AUTHORIZATION_COMMIT
    ):
        raise RuntimeError(
            "EXP-019 acquisition manifest "
            "identity changed."
        )

    request = manifest["request"]

    if (
        request["dataset"]
        != DATASET
        or request["schema"]
        != SCHEMA
        or request["stype_in"]
        != STYPE_IN
        or request["stype_out"]
        != STYPE_OUT
        or request["contract_count"]
        != EXPECTED_CONTRACT_COUNT
        or request[
            "contract_plan_sha256"
        ]
        != contract_plan_digest()
        or float(
            request[
                "maximum_total_cost_usd"
            ]
        )
        != MAXIMUM_TOTAL_COST_USD
        or request[
            "automatic_retries"
        ]
        != 0
    ):
        raise RuntimeError(
            "EXP-019 acquisition manifest "
            "request changed."
        )

    plan_symbols = {
        row[0]
        for row in CONTRACT_PLAN
    }

    completed = completed_by_symbol(
        manifest
    )

    if not set(completed).issubset(
        plan_symbols
    ):
        raise RuntimeError(
            "Manifest contains an unlocked "
            "contract."
        )

    expected_files: set[str] = set()

    for symbol, entry in (
        completed.items()
    ):
        relative_path = entry[
            "relative_path"
        ]

        if (
            Path(relative_path).is_absolute()
            or Path(relative_path).parts[0]
            != "raw"
        ):
            raise RuntimeError(
                "Manifest raw path is not "
                "archive-relative."
            )

        file_path = (
            ARCHIVE_ROOT
            / relative_path
        )

        expected_files.add(
            str(
                file_path.resolve()
            )
        )

        if not file_path.is_file():
            raise RuntimeError(
                "Missing completed archive "
                f"file: {file_path}"
            )

        size_bytes = (
            file_path.stat().st_size
        )

        if size_bytes <= 0:
            raise RuntimeError(
                "Completed archive file is "
                f"empty: {file_path}"
            )

        if size_bytes != int(
            entry["size_bytes"]
        ):
            raise RuntimeError(
                "Completed archive file size "
                f"changed: {symbol}"
            )

        if (
            sha256_file(file_path)
            != entry["sha256"]
        ):
            raise RuntimeError(
                "Completed archive file hash "
                f"changed: {symbol}"
            )

    if RAW_DIR.exists():
        actual_files = {
            str(path.resolve())
            for path in RAW_DIR.glob(
                "*.dbn.zst"
            )
            if ".partial.dbn.zst"
            not in path.name
        }

        orphans = sorted(
            actual_files
            - expected_files
        )

        if orphans:
            raise RuntimeError(
                "Unregistered archive files "
                f"exist: {orphans}"
            )

    if (
        attempted_estimated_cost(
            manifest
        )
        > MAXIMUM_TOTAL_COST_USD
        + 1e-9
    ):
        raise RuntimeError(
            "Manifest attempted cost exceeds "
            "the locked cap."
        )


def repository_preflight() -> dict[
    str,
    Any,
]:
    validate_exp019_preregistration()
    validate_exp019_acquisition_authorization()

    status = run_git(
        "status",
        "--porcelain",
    ).stdout.strip()

    if status:
        raise RuntimeError(
            "Repository must be clean before "
            "EXP-019 acquisition."
        )

    branch = run_git(
        "branch",
        "--show-current",
    ).stdout.strip()

    if branch != "main":
        raise RuntimeError(
            "EXP-019 acquisition must run "
            f"on main, found {branch!r}."
        )

    head = run_git(
        "rev-parse",
        "HEAD",
    ).stdout.strip()

    origin_main = run_git(
        "rev-parse",
        "origin/main",
    ).stdout.strip()

    if head != origin_main:
        raise RuntimeError(
            "Local HEAD and origin/main are "
            "not aligned."
        )

    ancestor = run_git(
        "merge-base",
        "--is-ancestor",
        LOCKED_AUTHORIZATION_COMMIT,
        "HEAD",
        check=False,
    )

    if ancestor.returncode != 0:
        raise RuntimeError(
            "Locked EXP-019 authorization "
            "commit is not an ancestor of HEAD."
        )

    protected_diff = run_git(
        "diff",
        "--quiet",
        LOCKED_AUTHORIZATION_COMMIT,
        "--",
        *LOCKED_PATHS,
        check=False,
    )

    if protected_diff.returncode != 0:
        raise RuntimeError(
            "Locked EXP-019 files changed "
            "after authorization."
        )

    summary, quotes = (
        load_cost_evidence()
    )

    partials = (
        sorted(
            RAW_DIR.glob(
                "*.partial.dbn.zst"
            )
        )
        if RAW_DIR.exists()
        else []
    )

    if partials:
        raise RuntimeError(
            "Partial archive files exist. "
            "Do not retry until they are "
            f"reviewed: {partials}"
        )

    manifest = read_manifest()

    if manifest is not None:
        verify_manifest(
            manifest
        )

    if COMPLETION_PATH.exists():
        if manifest is None:
            raise RuntimeError(
                "Completion marker exists "
                "without a manifest."
            )

        if (
            manifest["status"]
            != "COMPLETE"
            or len(
                manifest["completed"]
            )
            != EXPECTED_CONTRACT_COUNT
        ):
            raise RuntimeError(
                "Invalid EXP-019 completion "
                "state."
            )

    return {
        "branch": branch,
        "head": head,
        "origin_main": origin_main,
        "summary": summary,
        "quotes": quotes,
        "manifest": manifest,
        "completed": (
            0
            if manifest is None
            else len(
                manifest["completed"]
            )
        ),
        "attempted_cost_usd": (
            0.0
            if manifest is None
            else attempted_estimated_cost(
                manifest
            )
        ),
        "complete": (
            COMPLETION_PATH.exists()
        ),
    }


def create_client() -> Any:
    key = os.environ.get(
        "DATABENTO_API_KEY",
        "",
    ).strip()

    if not key:
        raise RuntimeError(
            "DATABENTO_API_KEY is not set."
        )

    import databento as db

    return db.Historical(
        key=key
    )


def download_contract(
    client: Any,
    *,
    sequence: int,
    canonical_symbol: str,
    raw_symbol: str,
    start: str,
    end_exclusive: str,
    expiration: str,
    estimated_cost_usd: float,
    raw_dir: Path = RAW_DIR,
    archive_root: Path = ARCHIVE_ROOT,
) -> dict[str, Any]:
    raw_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    final_name = output_filename(
        sequence,
        canonical_symbol,
        start,
        end_exclusive,
    )

    final_path = (
        raw_dir
        / final_name
    )

    partial_path = (
        raw_dir
        / partial_filename(
            final_name
        )
    )

    if final_path.exists():
        raise RuntimeError(
            "Refusing to overwrite completed "
            f"file: {final_path}"
        )

    if partial_path.exists():
        raise RuntimeError(
            "Refusing to overwrite partial "
            f"file: {partial_path}"
        )

    client.timeseries.get_range(
        dataset=DATASET,
        schema=SCHEMA,
        symbols=raw_symbol,
        stype_in=STYPE_IN,
        stype_out=STYPE_OUT,
        start=start,
        end=end_exclusive,
        path=partial_path,
    )

    if not partial_path.is_file():
        raise RuntimeError(
            "Databento request returned "
            "without creating the DBN file."
        )

    size_bytes = (
        partial_path.stat().st_size
    )

    if size_bytes <= 0:
        raise RuntimeError(
            "Databento created an empty DBN "
            f"file for {canonical_symbol}."
        )

    os.replace(
        partial_path,
        final_path,
    )

    return {
        "sequence": sequence,
        "canonical_symbol": (
            canonical_symbol
        ),
        "raw_symbol": raw_symbol,
        "start": start,
        "end_exclusive": (
            end_exclusive
        ),
        "expiration": expiration,
        "estimated_cost_usd": float(
            estimated_cost_usd
        ),
        "relative_path": str(
            final_path.relative_to(
                archive_root
            )
        ).replace("\\", "/"),
        "size_bytes": (
            final_path.stat().st_size
        ),
        "sha256": sha256_file(
            final_path
        ),
        "completed_at_utc": utc_now(),
    }


def archive_digest(
    completed: list[
        dict[str, Any]
    ],
) -> str:
    payload = [
        {
            "sequence": row["sequence"],
            "canonical_symbol": (
                row[
                    "canonical_symbol"
                ]
            ),
            "sha256": row["sha256"],
            "size_bytes": (
                row["size_bytes"]
            ),
        }
        for row in sorted(
            completed,
            key=lambda item: item[
                "sequence"
            ],
        )
    ]

    encoded = json.dumps(
        payload,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")

    return hashlib.sha256(
        encoded
    ).hexdigest()


def finalize_archive(
    manifest: dict[str, Any],
) -> None:
    verify_manifest(
        manifest
    )

    if (
        len(
            manifest["completed"]
        )
        != EXPECTED_CONTRACT_COUNT
    ):
        raise RuntimeError(
            "Cannot finalize an incomplete "
            "EXP-019 archive."
        )

    manifest["status"] = "COMPLETE"
    manifest["updated_at_utc"] = (
        utc_now()
    )
    manifest["completed_at_utc"] = (
        utc_now()
    )
    manifest["archive_sha256"] = (
        archive_digest(
            manifest["completed"]
        )
    )

    atomic_write_json(
        MANIFEST_PATH,
        manifest,
    )

    marker = {
        "experiment_id": "EXP-019",
        "classification": (
            "EXACT_CONTRACT_"
            "ACQUISITION_COMPLETE"
        ),
        "completed_at_utc": (
            manifest[
                "completed_at_utc"
            ]
        ),
        "contract_count": (
            EXPECTED_CONTRACT_COUNT
        ),
        "successful_downloads": (
            EXPECTED_CONTRACT_COUNT
        ),
        "automatic_retries": 0,
        "attempt_count": len(
            manifest["attempts"]
        ),
        "attempted_estimated_cost_usd": (
            attempted_estimated_cost(
                manifest
            )
        ),
        "maximum_total_cost_usd": (
            MAXIMUM_TOTAL_COST_USD
        ),
        "archive_sha256": (
            manifest[
                "archive_sha256"
            ]
        ),
        "archive_qualified": False,
        "audit_required_before_use": True,
        "continuous_series_constructed": False,
        "strategy_run": False,
    }

    atomic_write_json(
        COMPLETION_PATH,
        marker,
    )


def run_acquisition() -> None:
    preflight = repository_preflight()

    if preflight["complete"]:
        raise RuntimeError(
            "EXP-019 acquisition is already "
            "complete. Refusing to rerun."
        )

    manifest = preflight[
        "manifest"
    ]

    if manifest is None:
        manifest = new_manifest(
            {
                "branch": preflight[
                    "branch"
                ],
                "head": preflight[
                    "head"
                ],
                "origin_main": preflight[
                    "origin_main"
                ],
            }
        )

        atomic_write_json(
            MANIFEST_PATH,
            manifest,
        )

    completed = completed_by_symbol(
        manifest
    )

    if (
        len(completed)
        == EXPECTED_CONTRACT_COUNT
    ):
        finalize_archive(
            manifest
        )
        return

    client = create_client()
    quotes = preflight["quotes"]

    for sequence, contract in enumerate(
        CONTRACT_PLAN,
        start=1,
    ):
        (
            canonical_symbol,
            raw_symbol,
            start,
            end_exclusive,
            expiration,
        ) = contract

        if canonical_symbol in completed:
            print(
                f"[{sequence:02d}/"
                f"{EXPECTED_CONTRACT_COUNT}] "
                f"Verified existing "
                f"{canonical_symbol}"
            )
            continue

        estimated_cost = float(
            quotes[
                canonical_symbol
            ][
                "estimated_cost_usd"
            ]
        )

        current_attempted_cost = (
            attempted_estimated_cost(
                manifest
            )
        )

        projected_attempted_cost = (
            current_attempted_cost
            + estimated_cost
        )

        if (
            projected_attempted_cost
            > MAXIMUM_TOTAL_COST_USD
            + 1e-9
        ):
            manifest["status"] = (
                "BLOCKED_BY_COST_CAP"
            )
            manifest[
                "updated_at_utc"
            ] = utc_now()

            atomic_write_json(
                MANIFEST_PATH,
                manifest,
            )

            raise RuntimeError(
                "The next request would exceed "
                "the locked $35.00 attempted-"
                "cost cap."
            )

        attempt_number = (
            len(
                manifest["attempts"]
            )
            + 1
        )

        print(
            f"[{sequence:02d}/"
            f"{EXPECTED_CONTRACT_COUNT}] "
            f"Downloading "
            f"{canonical_symbol} "
            f"({start} to "
            f"{end_exclusive})"
        )

        attempt = {
            "attempt_number": (
                attempt_number
            ),
            "sequence": sequence,
            "canonical_symbol": (
                canonical_symbol
            ),
            "raw_symbol": raw_symbol,
            "start": start,
            "end_exclusive": (
                end_exclusive
            ),
            "estimated_cost_usd": (
                estimated_cost
            ),
            "started_at_utc": (
                utc_now()
            ),
            "status": "STARTED",
        }

        manifest["attempts"].append(
            attempt
        )
        manifest[
            "updated_at_utc"
        ] = utc_now()

        atomic_write_json(
            MANIFEST_PATH,
            manifest,
        )

        try:
            completed_entry = (
                download_contract(
                    client,
                    sequence=sequence,
                    canonical_symbol=(
                        canonical_symbol
                    ),
                    raw_symbol=raw_symbol,
                    start=start,
                    end_exclusive=(
                        end_exclusive
                    ),
                    expiration=expiration,
                    estimated_cost_usd=(
                        estimated_cost
                    ),
                )
            )
        except Exception as exc:
            final_name = output_filename(
                sequence,
                canonical_symbol,
                start,
                end_exclusive,
            )

            partial_path = (
                RAW_DIR
                / partial_filename(
                    final_name
                )
            )

            partial_deleted = False

            if partial_path.exists():
                partial_path.unlink()
                partial_deleted = True

            attempt["status"] = "FAILED"
            attempt[
                "completed_at_utc"
            ] = utc_now()
            attempt["error_type"] = (
                type(exc).__name__
            )
            attempt["error_message"] = (
                str(exc)[:1000]
            )
            attempt[
                "partial_deleted"
            ] = partial_deleted

            manifest["status"] = (
                "STOPPED_ON_ERROR"
            )
            manifest[
                "updated_at_utc"
            ] = utc_now()

            atomic_write_json(
                MANIFEST_PATH,
                manifest,
            )

            raise

        attempt["status"] = "SUCCESS"
        attempt["completed_at_utc"] = (
            utc_now()
        )
        attempt["sha256"] = (
            completed_entry[
                "sha256"
            ]
        )
        attempt["size_bytes"] = (
            completed_entry[
                "size_bytes"
            ]
        )

        manifest["completed"].append(
            completed_entry
        )
        manifest["status"] = (
            "IN_PROGRESS"
        )
        manifest[
            "updated_at_utc"
        ] = utc_now()

        atomic_write_json(
            MANIFEST_PATH,
            manifest,
        )

        completed[
            canonical_symbol
        ] = completed_entry

        print(
            f"  Saved "
            f"{completed_entry['size_bytes']:,} "
            f"bytes | "
            f"{completed_entry['sha256'][:12]}..."
        )

    finalize_archive(
        manifest
    )


def print_preflight(
    preflight: dict[str, Any],
) -> None:
    print(
        "EXP-019 ACQUISITION PREFLIGHT"
    )
    print(
        "============================="
    )
    print(
        f"Branch:                 "
        f"{preflight['branch']}"
    )
    print(
        f"HEAD:                   "
        f"{preflight['head']}"
    )
    print(
        "Locked contract windows:66"
    )
    print(
        "Quoted total:           "
        "$22.914098"
    )
    print(
        "Maximum cost:           "
        "$35.00"
    )
    print(
        f"Completed windows:      "
        f"{preflight['completed']}"
    )
    print(
        f"Remaining windows:      "
        f"{EXPECTED_CONTRACT_COUNT - preflight['completed']}"
    )
    print(
        "Attempted quoted cost:  "
        f"${preflight['attempted_cost_usd']:.6f}"
    )
    print(
        "Automatic retries:      0"
    )
    print(
        "Continuous symbol:      "
        "Prohibited"
    )
    print(
        "Continuous construction:"
        "Prohibited"
    )
    print(
        "Strategy run:           "
        "Prohibited"
    )
    print(
        f"Acquisition complete:   "
        f"{preflight['complete']}"
    )
    print(
        "============================="
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Protected one-time EXP-019 "
            "exact-contract acquisition."
        )
    )

    mode = (
        parser.add_mutually_exclusive_group(
            required=True
        )
    )

    mode.add_argument(
        "--preflight",
        action="store_true",
    )

    mode.add_argument(
        "--download",
        action="store_true",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.preflight:
        print_preflight(
            repository_preflight()
        )
        return 0

    run_acquisition()

    marker = json.loads(
        COMPLETION_PATH.read_text(
            encoding="utf-8"
        )
    )

    print()
    print(
        "EXP-019 ACQUISITION COMPLETE"
    )
    print(
        "============================"
    )
    print(
        "Contracts downloaded:   "
        f"{marker['contract_count']}"
    )
    print(
        "Successful downloads:   "
        f"{marker['successful_downloads']}"
    )
    print(
        "Automatic retries:      "
        f"{marker['automatic_retries']}"
    )
    print(
        "Attempted quoted cost:  "
        f"${marker['attempted_estimated_cost_usd']:.6f}"
    )
    print(
        "Maximum cost:           "
        f"${marker['maximum_total_cost_usd']:.2f}"
    )
    print(
        "Archive qualified:      "
        f"{marker['archive_qualified']}"
    )
    print(
        "Audit required:         "
        f"{marker['audit_required_before_use']}"
    )
    print(
        "Continuous constructed: "
        f"{marker['continuous_series_constructed']}"
    )
    print(
        "Strategy run:           "
        f"{marker['strategy_run']}"
    )
    print(
        f"Manifest:               "
        f"{MANIFEST_PATH}"
    )
    print(
        f"Completion marker:      "
        f"{COMPLETION_PATH}"
    )
    print(
        "============================"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
