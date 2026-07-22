from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parent
PAYLOAD = ROOT / "_exp018_impl_payload"
EXPECTED_HEAD = "fd0844dacab65f25d160e0b32a2273504528551f"

PACKAGE_PREFIXES = (
    "README_EXP018_IMPLEMENTATION.txt",
    "apply_exp018_implementation.py",
    "_exp018_impl_payload/",
)

NEW_TARGETS = (
    "exp018_implementation.py",
    "exp018_databento_worker.py",
    "exp018_measurements.py",
    "run_exp018_qualification.py",
    "research/EXP-018_implementation.md",
    "tests/test_exp018_implementation.py",
    "tests/test_exp018_measurements.py",
    "tests/test_exp018_runner_boundary.py",
)

COPY_TARGETS = {
    "exp018_implementation.py": "exp018_implementation.py",
    "exp018_databento_worker.py": "exp018_databento_worker.py",
    "exp018_measurements.py": "exp018_measurements.py",
    "run_exp018_qualification.py": "run_exp018_qualification.py",
    "research/EXP-018_implementation.md": "research/EXP-018_implementation.md",
    "tests/test_exp018_implementation.py": "tests/test_exp018_implementation.py",
    "tests/test_exp018_measurements.py": "tests/test_exp018_measurements.py",
    "tests/test_exp018_runner_boundary.py": "tests/test_exp018_runner_boundary.py",
    "tests/test_exp017_lifecycle.py": "tests/test_exp017_lifecycle.py",
}

OLD_NEXT_ACTION = '''        next_action=(
            "Build and commit the protected EXP-018 implementation before restoring "
            "the Databento API key or requesting bars. Enforce six initial requests, "
            "two delayed repeats, no automatic retries and local-only raw storage."
        ),
'''

NEW_NEXT_ACTION = '''        next_action=(
            "Commit and push the protected EXP-018 implementation, then run its "
            "local preflight with the Databento API key absent. After preflight, "
            "restore the key only in the current PowerShell session and perform "
            "the six locked initial requests. Do not run repeats before 24 hours."
        ),
'''


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=check,
    )


def write_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=path.parent,
        prefix=path.name + ".",
        suffix=".tmp",
        delete=False,
    ) as handle:
        temporary = Path(handle.name)
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(path)


def validate_preconditions() -> None:
    if os.environ.get("LSE_API_KEY") or os.environ.get("DATABENTO_API_KEY"):
        raise RuntimeError("Remove LSE_API_KEY and DATABENTO_API_KEY before applying.")

    if git("rev-parse", "HEAD").stdout.strip() != EXPECTED_HEAD:
        raise RuntimeError(
            "Expected repository HEAD " + EXPECTED_HEAD + "."
        )

    unexpected: list[str] = []
    status = git("status", "--porcelain", "--untracked-files=all").stdout
    for line in status.splitlines():
        if not line:
            continue
        path = line[3:].replace("\\", "/")
        if not any(path == item or path.startswith(item) for item in PACKAGE_PREFIXES):
            unexpected.append(line)
    if unexpected:
        raise RuntimeError(
            "Unexpected Git changes before application:\n" + "\n".join(unexpected)
        )

    if not PAYLOAD.is_dir():
        raise RuntimeError("The implementation payload directory is missing.")

    existing = [path for path in NEW_TARGETS if (ROOT / path).exists()]
    if existing:
        raise RuntimeError(
            "EXP-018 implementation targets already exist:\n" + "\n".join(existing)
        )


def prepare_outputs() -> dict[Path, bytes]:
    outputs: dict[Path, bytes] = {}

    for destination, source in COPY_TARGETS.items():
        source_path = PAYLOAD / source
        if not source_path.is_file():
            raise RuntimeError(f"Payload file is missing: {source}")
        data = source_path.read_bytes()
        if destination.endswith(".py"):
            compile(data.decode("utf-8"), destination, "exec")
        outputs[ROOT / destination] = data

    lifecycle_path = ROOT / "experiment_lifecycle.py"
    lifecycle = lifecycle_path.read_text(encoding="utf-8")
    if lifecycle.count(OLD_NEXT_ACTION) != 1:
        raise RuntimeError(
            "Expected the current EXP-018 lifecycle next action exactly once."
        )
    lifecycle = lifecycle.replace(OLD_NEXT_ACTION, NEW_NEXT_ACTION, 1)
    compile(lifecycle, str(lifecycle_path), "exec")
    outputs[lifecycle_path] = lifecycle.encode("utf-8")

    gitignore_path = ROOT / ".gitignore"
    gitignore = gitignore_path.read_text(encoding="utf-8")
    entry = ".venv-exp017-databento/"
    if entry not in gitignore.splitlines():
        marker = ".venv/\n"
        if marker not in gitignore:
            raise RuntimeError("Expected .venv/ marker in .gitignore.")
        gitignore = gitignore.replace(marker, marker + entry + "\n", 1)
    outputs[gitignore_path] = gitignore.encode("utf-8")

    return outputs


def main() -> None:
    validate_preconditions()
    outputs = prepare_outputs()

    for path, data in outputs.items():
        write_atomic(path, data)

    shutil.rmtree(PAYLOAD)

    print("EXP-018 protected implementation applied.")
    print("EXP-018 lifecycle: PRE_REGISTERED")
    print("Implementation status: IMPLEMENTED_NOT_RUN")
    print("Databento client lock: 0.81.0")
    print("Initial bar requests allowed after commit: 6")
    print("Delayed repeat requests allowed after 24 hours: 2")
    print("Maximum estimated cost: $1.00")
    print("Automatic retries: False")
    print("OHLCV requested now: False")
    print("Strategy execution authorized: False")


if __name__ == "__main__":
    main()
