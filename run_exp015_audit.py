from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any, Mapping

from exp014_behaviour_result import verify_local_exp014_behaviour_result
from exp015_catalog import build_catalog_result, canonicalize_catalog_rows
from exp015_implementation import (
    CATALOG_RESULT_FILE,
    CATALOG_ROWS_FILE,
    CATALOG_STAGING_FILE,
    EXPECTED_CLIENT_VERSION,
    EXPECTED_CLIENT_WHEEL,
    EXPECTED_CLIENT_WHEEL_SHA256,
    PACKAGE_CACHE,
    PROBE_MANIFEST,
    PROBE_ROOT,
    PROBE_VENV,
    validate_exp015_implementation,
)
from exp015_preregistration import validate_exp015_preregistration
from experiment_lifecycle import get_experiment_lifecycle


PROJECT_DIR = Path(__file__).resolve().parent
WORKER_FILE = PROJECT_DIR / "exp015_lse_worker.py"


def _run_git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=PROJECT_DIR,
        text=True,
        capture_output=True,
        check=True,
    )
    return completed.stdout.strip()


def git_provenance() -> dict[str, Any]:
    commit = _run_git("rev-parse", "HEAD")
    return {
        "commit": commit,
        "short_commit": commit[:7],
        "working_tree_clean": not bool(_run_git("status", "--porcelain")),
    }


def _atomic_json(payload: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, allow_nan=False),
        encoding="utf-8",
    )
    temporary.replace(path)


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"Expected a JSON object: {path}")
    return value


def _verify_lifecycle() -> None:
    expected = {
        "EXP-005": "ACCEPTED_FOR_PAPER_TESTING",
        "EXP-006": "REJECTED",
        "EXP-007": "REJECTED",
        "EXP-008": "REJECTED",
        "EXP-009": "REVIEW",
        "EXP-010": "REVIEW",
        "EXP-011": "REVIEW",
        "EXP-012": "REVIEW",
        "EXP-013": "REVIEW",
        "EXP-014": "REVIEW",
        "EXP-015": "PRE_REGISTERED",
    }
    for experiment_id, stage in expected.items():
        actual = get_experiment_lifecycle(experiment_id).stage
        if actual != stage:
            raise RuntimeError(
                f"{experiment_id} must remain {stage}; found {actual}."
            )


def protected_preflight() -> dict[str, Any]:
    validate_exp015_preregistration()
    validate_exp015_implementation()
    _verify_lifecycle()
    verify_local_exp014_behaviour_result()

    git = git_provenance()
    if not git["working_tree_clean"]:
        raise RuntimeError(
            "Commit the EXP-015 implementation before probe or catalog access."
        )

    print()
    print("EXP-015 IMPLEMENTATION PREFLIGHT")
    print("================================")
    print("Lifecycle:             PRE_REGISTERED")
    print("Implementation:        IMPLEMENTED_NOT_RUN")
    print("Prior result verified: EXP-014 frozen and valid")
    print("Client distribution:   lse-data 0.14.0")
    print("Main venv install:      False")
    print("Isolated client probe:  available")
    print("Catalog remote method: catalog('futures') only")
    print("History download:       False")
    print("Strategy replay:        False")
    print("API key file storage:   False")
    print("Prior data replacement: False")
    print(f"Git commit:             {git['short_commit']}")
    print("Git clean:              True")
    print("================================")
    return git


def _venv_python() -> Path:
    if os.name == "nt":
        return PROBE_VENV / "Scripts" / "python.exe"
    return PROBE_VENV / "bin" / "python"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _subprocess_env_without_key() -> dict[str, str]:
    env = dict(os.environ)
    env.pop("LSE_API_KEY", None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def run_isolated_client_probe() -> dict[str, Any]:
    git = protected_preflight()
    if CATALOG_RESULT_FILE.exists():
        raise RuntimeError(
            "The catalog result already exists. Do not rebuild the client probe."
        )

    if PROBE_ROOT.exists():
        shutil.rmtree(PROBE_ROOT)
    PACKAGE_CACHE.mkdir(parents=True, exist_ok=False)

    subprocess.run(
        [sys.executable, "-m", "venv", str(PROBE_VENV)],
        cwd=PROJECT_DIR,
        check=True,
    )
    python = _venv_python()

    subprocess.run(
        [
            str(python),
            "-m",
            "pip",
            "download",
            "--disable-pip-version-check",
            "--only-binary=:all:",
            "--no-deps",
            f"lse-data=={EXPECTED_CLIENT_VERSION}",
            "--dest",
            str(PACKAGE_CACHE),
        ],
        cwd=PROJECT_DIR,
        env=_subprocess_env_without_key(),
        check=True,
    )

    wheel = PACKAGE_CACHE / EXPECTED_CLIENT_WHEEL
    if not wheel.is_file():
        raise RuntimeError(f"Expected wheel was not downloaded: {wheel.name}")
    wheel_sha256 = _sha256(wheel)
    if wheel_sha256 != EXPECTED_CLIENT_WHEEL_SHA256:
        raise RuntimeError(
            "lse-data wheel hash mismatch. The isolated probe has stopped."
        )

    subprocess.run(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            str(wheel),
        ],
        cwd=PROJECT_DIR,
        env=_subprocess_env_without_key(),
        check=True,
    )

    completed = subprocess.run(
        [str(python), str(WORKER_FILE), "--probe"],
        cwd=PROJECT_DIR,
        env=_subprocess_env_without_key(),
        text=True,
        capture_output=True,
        check=True,
    )
    probe = json.loads(completed.stdout)
    if (
        probe.get("status") != "PASS"
        or probe.get("distribution") != "lse-data"
        or probe.get("version") != EXPECTED_CLIENT_VERSION
        or probe.get("real_api_key_used") is not False
        or probe.get("network_market_data_call") is not False
    ):
        raise RuntimeError("The isolated lse-data compatibility probe failed.")

    freeze = subprocess.run(
        [str(python), "-m", "pip", "freeze"],
        cwd=PROJECT_DIR,
        env=_subprocess_env_without_key(),
        text=True,
        capture_output=True,
        check=True,
    ).stdout.splitlines()

    manifest = {
        **probe,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "git": git,
        "wheel_filename": wheel.name,
        "wheel_sha256": wheel_sha256,
        "installed_packages": sorted(freeze),
        "probe_root": str(PROBE_ROOT.relative_to(PROJECT_DIR)),
        "main_project_environment_modified": False,
    }
    _atomic_json(manifest, PROBE_MANIFEST)

    print()
    print("EXP-015 ISOLATED CLIENT PROBE")
    print("=============================")
    print("Status:               PASS")
    print(f"Client:               lse-data {manifest['version']}")
    print(f"Probe Python:         {manifest['python_version']}")
    print("Wheel hash verified:  True")
    print("Real API key used:    False")
    print("Market data accessed: False")
    print("Main venv modified:   False")
    print("=============================")
    return manifest


def _verified_probe_manifest() -> dict[str, Any]:
    if not PROBE_MANIFEST.is_file():
        raise RuntimeError(
            "Run --probe-client successfully before catalog access."
        )
    manifest = _load_json(PROBE_MANIFEST)
    if (
        manifest.get("status") != "PASS"
        or manifest.get("distribution") != "lse-data"
        or manifest.get("version") != EXPECTED_CLIENT_VERSION
        or manifest.get("wheel_sha256") != EXPECTED_CLIENT_WHEEL_SHA256
        or manifest.get("real_api_key_used") is not False
        or manifest.get("network_market_data_call") is not False
    ):
        raise RuntimeError("The EXP-015 isolated client probe is not valid.")
    return manifest


def _write_catalog_csv(rows: list[dict[str, Any]]) -> None:
    CATALOG_ROWS_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary = CATALOG_ROWS_FILE.with_suffix(".csv.tmp")
    fieldnames = [
        "symbol",
        "name",
        "category",
        "dataset",
        "ticks",
        "first",
        "last",
        "country",
    ]
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fieldnames})
    temporary.replace(CATALOG_ROWS_FILE)


def run_catalog_only() -> dict[str, Any]:
    git = protected_preflight()
    probe = _verified_probe_manifest()

    if CATALOG_RESULT_FILE.exists():
        raise RuntimeError(
            "EXP-015 already has a catalog result. Do not rerun catalog access."
        )
    if CATALOG_STAGING_FILE.exists():
        CATALOG_STAGING_FILE.unlink()

    key = os.environ.get("LSE_API_KEY")
    if not key:
        raise RuntimeError(
            "LSE_API_KEY is not set in this PowerShell session. "
            "Do not place the key in a file or paste it into source code."
        )

    python = _venv_python()
    if not python.is_file():
        raise RuntimeError("The isolated probe environment is missing.")

    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    subprocess.run(
        [
            str(python),
            str(WORKER_FILE),
            "--catalog",
            str(CATALOG_STAGING_FILE),
        ],
        cwd=PROJECT_DIR,
        env=env,
        check=True,
    )

    raw_rows = json.loads(CATALOG_STAGING_FILE.read_text(encoding="utf-8"))
    rows = canonicalize_catalog_rows(raw_rows)
    result = build_catalog_result(rows, git=git, client_probe=probe)

    _atomic_json(result, CATALOG_RESULT_FILE)
    _write_catalog_csv(rows)
    CATALOG_STAGING_FILE.unlink(missing_ok=True)

    assessment = result["assessment"]
    print()
    print("EXP-015 FUTURES CATALOG RESULT")
    print("==============================")
    print(f"Futures rows:         {assessment['futures_catalog_rows']}")
    print(f"NQ candidates:        {assessment['nq_candidate_count']}")
    print(f"MNQ candidates:       {assessment['mnq_candidate_count']}")
    print(f"Classification:       {assessment['classification']}")
    print("History downloaded:   False")
    print("All data qualified:   False")
    print("Paper/live authority: False")
    print("==============================")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--preflight", action="store_true")
    group.add_argument("--probe-client", action="store_true")
    group.add_argument("--catalog", action="store_true")
    args = parser.parse_args()

    if args.preflight:
        protected_preflight()
    elif args.probe_client:
        run_isolated_client_probe()
    else:
        run_catalog_only()


if __name__ == "__main__":
    main()
