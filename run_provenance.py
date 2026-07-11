from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from importlib import metadata as importlib_metadata
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


PACKAGE_DISTRIBUTIONS = (
    "numpy",
    "pandas",
    "matplotlib",
    "pyarrow",
    "tqdm",
    "scikit-learn",
)


def json_ready(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)

    if isinstance(value, dict):
        return {
            str(key): json_ready(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [
            json_ready(item)
            for item in value
        ]

    if isinstance(value, np.integer):
        return int(value)

    if isinstance(value, np.floating):
        return float(value)

    if isinstance(value, pd.Timestamp):
        return value.isoformat()

    return value


def stable_json(value: Any) -> str:
    return json.dumps(
        json_ready(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(
    path: Path,
    chunk_size: int = 1024 * 1024,
) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as file_handle:
        while chunk := file_handle.read(chunk_size):
            digest.update(chunk)

    return digest.hexdigest()


def combined_code_fingerprint(
    project_directory: Path,
    relative_paths: tuple[str, ...],
) -> str:
    digest = hashlib.sha256()

    for relative_path in sorted(relative_paths):
        path = project_directory / relative_path

        digest.update(
            relative_path.encode("utf-8")
        )

        if path.exists():
            digest.update(path.read_bytes())
        else:
            digest.update(b"<missing>")

    return digest.hexdigest()


def configuration_fingerprint(config: Any) -> str:
    return sha256_bytes(
        stable_json(asdict(config)).encode("utf-8")
    )


def utc_run_identity() -> tuple[str, str]:
    now = datetime.now(timezone.utc)

    timestamp = now.isoformat(
        timespec="seconds"
    ).replace("+00:00", "Z")

    run_id = now.strftime(
        "%Y%m%dT%H%M%SZ"
    )

    return run_id, timestamp


def git_state(
    project_directory: Path,
) -> dict[str, Any]:
    def git_command(
        *arguments: str,
    ) -> str | None:
        try:
            completed = subprocess.run(
                ["git", *arguments],
                cwd=project_directory,
                capture_output=True,
                text=True,
                check=True,
            )
        except (
            FileNotFoundError,
            subprocess.CalledProcessError,
        ):
            return None

        return completed.stdout.strip()

    commit = git_command(
        "rev-parse",
        "HEAD",
    )

    short_commit = git_command(
        "rev-parse",
        "--short",
        "HEAD",
    )

    branch = git_command(
        "branch",
        "--show-current",
    )

    status = git_command(
        "status",
        "--porcelain",
    )

    return {
        "commit": commit,
        "short_commit": short_commit,
        "branch": branch,
        "working_tree_dirty": (
            bool(status)
            if status is not None
            else None
        ),
    }


def package_versions() -> dict[str, str | None]:
    versions: dict[str, str | None] = {}

    for distribution in PACKAGE_DISTRIBUTIONS:
        try:
            versions[distribution] = (
                importlib_metadata.version(
                    distribution
                )
            )
        except importlib_metadata.PackageNotFoundError:
            versions[distribution] = None

    return versions


def runtime_environment() -> dict[str, Any]:
    return {
        "python_version": sys.version,
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "package_versions": package_versions(),
    }


def mcpt_base_signature(
    *,
    config: Any,
    data_file_sha256: str,
    code_fingerprint: str,
) -> dict[str, Any]:
    """
    Identify the assumptions that must match before cached MCPT
    results can be reused safely.
    """

    return {
        "signature_version": 1,
        "objective": "bar_return_profit_factor_v1",
        "experiment_id": config.experiment_id,
        "strategy_name": config.strategy_name,
        "optimization_grid": json_ready(
            config.optimization_grid
        ),
        "in_sample_start": config.in_sample_start,
        "in_sample_end": config.in_sample_end,
        "random_seed": config.random_seed,
        "data_file_sha256": data_file_sha256,
        "code_fingerprint": code_fingerprint,
    }


def signature_digest(
    signature: dict[str, Any],
) -> str:
    return sha256_bytes(
        stable_json(signature).encode("utf-8")
    )


def save_mcpt_cache(
    *,
    results_directory: Path,
    results: pd.DataFrame,
    p_value: float,
    better_or_equal: int,
    permutations: int,
    configured_full_permutations: int,
    base_signature: dict[str, Any],
    real_score: float,
) -> dict[str, Any]:
    cache_kind = (
        "full"
        if permutations
        == configured_full_permutations
        else "quick"
    )

    csv_path = (
        results_directory
        / f"mcpt_{cache_kind}.csv"
    )

    metadata_path = (
        results_directory
        / f"mcpt_{cache_kind}_metadata.json"
    )

    results.to_csv(
        csv_path,
        index=False,
    )

    metadata = {
        "cache_kind": cache_kind,
        "permutations": int(permutations),
        "p_value": float(p_value),
        "better_or_equal": int(
            better_or_equal
        ),
        "real_score": float(real_score),
        "base_signature": base_signature,
        "signature_digest": signature_digest(
            base_signature
        ),
        "created_at_utc": datetime.now(
            timezone.utc
        ).isoformat(
            timespec="seconds"
        ).replace("+00:00", "Z"),
        "csv_file": csv_path.name,
    }

    metadata_path.write_text(
        json.dumps(
            json_ready(metadata),
            indent=2,
        ),
        encoding="utf-8",
    )

    # Backward-compatible active result used by older utilities.
    results.to_csv(
        results_directory / "mcpt.csv",
        index=False,
    )

    return metadata


def load_compatible_mcpt_cache(
    *,
    results_directory: Path,
    base_signature: dict[str, Any],
) -> tuple[
    pd.DataFrame | None,
    dict[str, Any] | None,
]:
    """
    Prefer a compatible full cache, then a compatible quick cache.
    Legacy mcpt.csv files without provenance metadata are deliberately
    not reused automatically.
    """

    expected_digest = signature_digest(
        base_signature
    )

    for cache_kind in ("full", "quick"):
        metadata_path = (
            results_directory
            / f"mcpt_{cache_kind}_metadata.json"
        )

        csv_path = (
            results_directory
            / f"mcpt_{cache_kind}.csv"
        )

        if (
            not metadata_path.exists()
            or not csv_path.exists()
        ):
            continue

        try:
            metadata = json.loads(
                metadata_path.read_text(
                    encoding="utf-8"
                )
            )
        except (
            json.JSONDecodeError,
            OSError,
        ):
            continue

        if (
            metadata.get("signature_digest")
            != expected_digest
        ):
            continue

        try:
            results = pd.read_csv(csv_path)
        except (
            OSError,
            pd.errors.ParserError,
        ):
            continue

        expected_rows = int(
            metadata.get("permutations", -1)
        )

        if len(results) != expected_rows:
            continue

        return results, metadata

    return None, None


def append_run_history(
    *,
    history_file: Path,
    row: dict[str, Any],
) -> None:
    new_row = pd.DataFrame(
        [json_ready(row)]
    )

    if history_file.exists():
        existing = pd.read_csv(
            history_file
        )

        combined = pd.concat(
            [existing, new_row],
            ignore_index=True,
        )
    else:
        combined = new_row

    combined.to_csv(
        history_file,
        index=False,
    )
