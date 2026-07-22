from __future__ import annotations

import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
EXPECTED_HEAD = "1c55e053e862485da6a94f2cff6599beba07265e"
LIFECYCLE = ROOT / "experiment_lifecycle.py"
PACKAGE_PATHS = {
    "README_EXP017_SOURCE_SET_LOCK.txt",
    "apply_exp017_source_set_lock.py",
    "exp017_source_lock.py",
    "research/EXP-017_source_lock.md",
    "tests/test_exp017_source_lock.py",
    "tests/test_exp017_lifecycle.py",
}

OLD = '        next_action=(\n            "Create and commit the EXP-017 source-lock record before any bar access. "\n            "Resolve exact aliases, provider provenance, licensing and an exchange-"\n            "reference candidate without viewing OHLCV values."\n        ),\n'
NEW = '        next_action=(\n            "Complete metadata-only eligibility confirmation for Databento GLBX.MDP3 "\n            "and CME DataMine before any bar access. Resolve exact aliases, expiry "\n            "identity, timestamp semantics, entitlements, licensing and cost; then "\n            "commit the final eligibility lock. Do not request OHLCV yet."\n        ),\n'


def run_git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, text=True, capture_output=True, check=True
    ).stdout


def main() -> None:
    if os.environ.get("LSE_API_KEY") or os.environ.get("DATABENTO_API_KEY"):
        raise RuntimeError("Remove market-data API keys before applying.")

    head = run_git("rev-parse", "HEAD").strip()
    if head != EXPECTED_HEAD:
        raise RuntimeError(f"Expected HEAD {EXPECTED_HEAD}; found {head}.")

    unexpected = []
    for line in run_git("status", "--porcelain", "--untracked-files=all").splitlines():
        if not line:
            continue
        path = line[3:].replace("\\", "/")
        if path not in PACKAGE_PATHS:
            unexpected.append(line)
    if unexpected:
        raise RuntimeError("Unexpected Git changes:\n" + "\n".join(unexpected))

    source = LIFECYCLE.read_text(encoding="utf-8")
    if source.count(OLD) != 1:
        raise RuntimeError("Expected current EXP-017 lifecycle next action exactly once.")
    updated = source.replace(OLD, NEW, 1)
    compile(updated, str(LIFECYCLE), "exec")
    LIFECYCLE.write_text(updated, encoding="utf-8", newline="\n")

    for path in (
        ROOT / "exp017_source_lock.py",
        ROOT / "tests" / "test_exp017_source_lock.py",
        ROOT / "tests" / "test_exp017_lifecycle.py",
    ):
        compile(path.read_text(encoding="utf-8"), str(path), "exec")

    print("EXP-017 source set locked.")
    print("Lucid/Rithmic exact-contract benchmark eligible: False")
    print("Databento GLBX.MDP3 status: METADATA_PENDING")
    print("CME DataMine status: COMMERCIAL_AND_METADATA_PENDING")
    print("London NQ.F included: False")
    print("Benchmark bar values viewed: False")
    print("Remote market-data request performed: False")
    print("OHLCV access authorized: False")
    print("Final eligibility lock still required: True")


if __name__ == "__main__":
    main()
