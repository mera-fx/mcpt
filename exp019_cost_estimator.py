from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
from typing import Any, Iterable

from exp019_preregistration import (
    CONTRACT_PLAN,
    EXP019_PREREGISTRATION,
    validate_exp019_preregistration,
)


PROJECT_DIR = Path(__file__).resolve().parent

LOCKED_PREREGISTRATION_COMMIT = "c22e5bf84be11abae1d9ae0b04e9d9c9be07e9c4"

LOCKED_PREREGISTRATION_PATHS = (
    "exp019_preregistration.py",
    "research/EXP-019_preregistration.md",
)

OUTPUT_DIR = (
    PROJECT_DIR
    / "results"
    / "EXP-019"
    / "cost_estimate"
)

CSV_PATH = OUTPUT_DIR / "exp019_exact_contract_costs.csv"
JSON_PATH = OUTPUT_DIR / "exp019_cost_estimate.json"

DATASET = "GLBX.MDP3"
SCHEMA = "ohlcv-1m"
STYPE_IN = "raw_symbol"

EXPECTED_CONTRACT_COUNT = 66
CONTINUOUS_REFERENCE_COST_USD = 19.9408
MAXIMUM_DOWNLOAD_COST_USD = 35.0


@dataclass(frozen=True)
class ContractCost:
    sequence: int
    canonical_symbol: str
    raw_symbol: str
    start: str
    end_exclusive: str
    expiration: str
    estimated_cost_usd: float


def _run_git(
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


def repository_preflight() -> dict[str, str]:
    validate_exp019_preregistration()

    status = _run_git(
        "status",
        "--porcelain",
    ).stdout.strip()

    if status:
        raise RuntimeError(
            "Repository must be clean before running "
            "the EXP-019 cost estimator."
        )

    branch = _run_git(
        "branch",
        "--show-current",
    ).stdout.strip()

    if branch != "main":
        raise RuntimeError(
            f"EXP-019 must run on main, found {branch!r}."
        )

    head = _run_git(
        "rev-parse",
        "HEAD",
    ).stdout.strip()

    origin_main = _run_git(
        "rev-parse",
        "origin/main",
    ).stdout.strip()

    if head != origin_main:
        raise RuntimeError(
            "Local HEAD and origin/main are not aligned."
        )

    ancestor = _run_git(
        "merge-base",
        "--is-ancestor",
        LOCKED_PREREGISTRATION_COMMIT,
        "HEAD",
        check=False,
    )

    if ancestor.returncode != 0:
        raise RuntimeError(
            "Locked EXP-019 preregistration commit is "
            "not an ancestor of HEAD."
        )

    protected_diff = _run_git(
        "diff",
        "--quiet",
        LOCKED_PREREGISTRATION_COMMIT,
        "--",
        *LOCKED_PREREGISTRATION_PATHS,
        check=False,
    )

    if protected_diff.returncode != 0:
        raise RuntimeError(
            "Locked EXP-019 preregistration files changed "
            "after preregistration."
        )

    if CSV_PATH.exists() or JSON_PATH.exists():
        raise RuntimeError(
            "EXP-019 cost-estimate output already exists. "
            "Refusing to repeat the quote."
        )

    if len(CONTRACT_PLAN) != EXPECTED_CONTRACT_COUNT:
        raise RuntimeError(
            "EXP-019 contract count changed."
        )

    return {
        "branch": branch,
        "head": head,
        "origin_main": origin_main,
        "locked_preregistration_commit": (
            LOCKED_PREREGISTRATION_COMMIT
        ),
    }


def contract_plan_digest(
    plan: Iterable[
        tuple[str, str, str, str, str]
    ] = CONTRACT_PLAN,
) -> str:
    encoded = json.dumps(
        list(plan),
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()


def estimate_contract_costs(
    client: Any,
    plan: Iterable[
        tuple[str, str, str, str, str]
    ] = CONTRACT_PLAN,
) -> list[ContractCost]:
    rows: list[ContractCost] = []

    for sequence, contract in enumerate(
        plan,
        start=1,
    ):
        (
            canonical_symbol,
            raw_symbol,
            start,
            end_exclusive,
            expiration,
        ) = contract

        cost = client.metadata.get_cost(
            dataset=DATASET,
            schema=SCHEMA,
            symbols=raw_symbol,
            stype_in=STYPE_IN,
            start=start,
            end=end_exclusive,
        )

        rows.append(
            ContractCost(
                sequence=sequence,
                canonical_symbol=canonical_symbol,
                raw_symbol=raw_symbol,
                start=start,
                end_exclusive=end_exclusive,
                expiration=expiration,
                estimated_cost_usd=float(cost),
            )
        )

    return rows


def build_summary(
    rows: list[ContractCost],
    repository: dict[str, str],
) -> dict[str, Any]:
    total = sum(
        row.estimated_cost_usd
        for row in rows
    )

    return {
        "experiment_id": "EXP-019",
        "classification": (
            "EXACT_CONTRACT_COST_ESTIMATE_COMPLETE"
        ),
        "generated_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "repository": repository,
        "request": {
            "dataset": DATASET,
            "schema": SCHEMA,
            "stype_in": STYPE_IN,
            "contract_count": len(rows),
            "quote_calls": len(rows),
            "automatic_retries": 0,
            "bar_records_requested": False,
            "bar_records_downloaded": False,
            "contract_plan_sha256": (
                contract_plan_digest()
            ),
        },
        "costs": {
            "exact_contract_total_usd": total,
            "continuous_reference_usd": (
                CONTINUOUS_REFERENCE_COST_USD
            ),
            "difference_usd": (
                total
                - CONTINUOUS_REFERENCE_COST_USD
            ),
            "ratio_to_continuous": (
                total
                / CONTINUOUS_REFERENCE_COST_USD
            ),
            "maximum_download_cost_usd": (
                MAXIMUM_DOWNLOAD_COST_USD
            ),
            "within_locked_cap": (
                total
                <= MAXIMUM_DOWNLOAD_COST_USD
            ),
        },
        "interpretation": {
            "download_authorized": False,
            "archive_qualified": False,
            "continuous_series_constructed": False,
            "strategy_run": False,
            "separate_approval_required": True,
        },
        "contracts": [
            asdict(row)
            for row in rows
        ],
    }


def write_outputs(
    rows: list[ContractCost],
    summary: dict[str, Any],
) -> None:
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=False,
    )

    with CSV_PATH.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "sequence",
                "canonical_symbol",
                "raw_symbol",
                "start",
                "end_exclusive",
                "expiration",
                "estimated_cost_usd",
            ],
        )
        writer.writeheader()

        for row in rows:
            writer.writerow(
                asdict(row)
            )

    JSON_PATH.write_text(
        json.dumps(
            summary,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


def create_databento_client() -> Any:
    key = os.environ.get(
        "DATABENTO_API_KEY",
        "",
    ).strip()

    if not key:
        raise RuntimeError(
            "DATABENTO_API_KEY is not set."
        )

    import databento as db

    return db.Historical(key=key)


def print_preflight(
    repository: dict[str, str],
) -> None:
    print("EXP-019 COST ESTIMATOR PREFLIGHT")
    print("================================")
    print(f"Branch:                 {repository['branch']}")
    print(f"HEAD:                   {repository['head']}")
    print("Contract windows:       66")
    print("Quote calls allowed:    66")
    print("Automatic retries:      0")
    print("Bar records requested:  False")
    print("Download authorised:    False")
    print("Existing output:        False")
    print("================================")


def print_result(
    summary: dict[str, Any],
) -> None:
    costs = summary["costs"]

    print()
    print("EXP-019 EXACT-CONTRACT COST ESTIMATE")
    print("====================================")
    print("Contracts quoted:       66")
    print(
        "Exact-contract total:  "
        f"${costs['exact_contract_total_usd']:.6f}"
    )
    print(
        "Continuous reference:  "
        f"${costs['continuous_reference_usd']:.6f}"
    )
    print(
        "Difference:            "
        f"${costs['difference_usd']:.6f}"
    )
    print(
        "Exact/continuous ratio: "
        f"{costs['ratio_to_continuous']:.6f}"
    )
    print(
        "Locked download cap:   "
        f"${costs['maximum_download_cost_usd']:.2f}"
    )
    print(
        "Within locked cap:      "
        f"{costs['within_locked_cap']}"
    )
    print("Automatic retries:      0")
    print("Bars downloaded:        0")
    print("Download authorised:    False")
    print(f"CSV:                    {CSV_PATH}")
    print(f"JSON:                   {JSON_PATH}")
    print("====================================")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "EXP-019 metadata-only exact-contract "
            "cost estimator."
        )
    )

    mode = parser.add_mutually_exclusive_group(
        required=True
    )

    mode.add_argument(
        "--preflight",
        action="store_true",
    )
    mode.add_argument(
        "--estimate",
        action="store_true",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repository = repository_preflight()

    if args.preflight:
        print_preflight(repository)
        return 0

    client = create_databento_client()

    rows = estimate_contract_costs(
        client
    )

    if len(rows) != EXPECTED_CONTRACT_COUNT:
        raise RuntimeError(
            "Not all locked contracts were quoted."
        )

    summary = build_summary(
        rows,
        repository,
    )

    write_outputs(
        rows,
        summary,
    )

    print_result(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
