from pathlib import Path
import os
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent
PAYLOAD = ROOT / "_exp018_payload"
EXPECTED_HEAD = "c9589ed58eb956ef02c7ba4906479c06c0ca32b8"

OLD = '''    "EXP-017": ExperimentLifecycle(
        experiment_id="EXP-017",
        experiment_name="Exact NQ Contract Data Benchmark",
        hypothesis=(
            "Comparing the same exact quarterly NQ contracts across independently "
            "identified sources may distinguish price accuracy, session completeness "
            "and historical reproducibility without continuous-roll ambiguity."
        ),
        stage="PRE_REGISTERED",
        stage_reason=(
            "Six exact-contract windows, a price-free source-lock stage, structural "
            "and cross-source measurements, repeat-download checks and fixed source-"
            "selection rules were locked before accessing EXP-017 benchmark bars."
        ),
        next_action=(
            "Complete metadata-only eligibility confirmation for Databento GLBX.MDP3 "
            "and CME DataMine before any bar access. Resolve exact aliases, expiry "
            "identity, timestamp semantics, entitlements, licensing and cost; then "
            "commit the final eligibility lock. Do not request OHLCV yet."
        ),
        market_name="Exact quarterly NQ futures contracts",
        timeframe="One-minute multi-source data benchmark",
        strategy_name="exact_nq_contract_data_benchmark",
        preregistration_file=Path("research/EXP-017_preregistration.md"),
    ),

'''

NEW = '''    "EXP-017": ExperimentLifecycle(
        experiment_id="EXP-017",
        experiment_name="Exact NQ Contract Data Benchmark",
        hypothesis=(
            "Comparing the same exact quarterly NQ contracts across independently "
            "identified sources may distinguish price accuracy, session completeness "
            "and historical reproducibility without continuous-roll ambiguity."
        ),
        stage="REVIEW",
        stage_reason=(
            "EXP-017 closed as ACCESS_INCOMPLETE before any benchmark OHLCV was "
            "requested. Databento resolved all six exact contracts, but CME DataMine "
            "was financially inaccessible and no second affordable source satisfied "
            "the locked entry requirement. No price comparison occurred."
        ),
        next_action=(
            "Preserve EXP-017 as an access-limited source investigation. EXP-018 "
            "may perform only the preregistered Databento structural and repeatability "
            "qualification. Do not reinterpret EXP-017 as price validation."
        ),
        market_name="Exact quarterly NQ futures contracts",
        timeframe="One-minute multi-source data benchmark",
        strategy_name="exact_nq_contract_data_benchmark",
        preregistration_file=Path("research/EXP-017_preregistration.md"),
    ),

    "EXP-018": ExperimentLifecycle(
        experiment_id="EXP-018",
        experiment_name=(
            "Databento Exact-Contract Structural and "
            "Repeatability Qualification"
        ),
        hypothesis=(
            "Databento GLBX.MDP3 exact-contract one-minute NQ samples may be "
            "structurally valid, sufficiently complete and canonically repeatable "
            "for new research without implying exchange-verified accuracy."
        ),
        stage="PRE_REGISTERED",
        stage_reason=(
            "Six exact-contract windows, two delayed repeats, fixed quality gates, "
            "a $1 cost cap and no-strategy boundaries were locked before OHLCV."
        ),
        next_action=(
            "Build and commit the protected EXP-018 implementation before restoring "
            "the Databento API key or requesting bars. Enforce six initial requests, "
            "two delayed repeats, no automatic retries and local-only raw storage."
        ),
        market_name="Exact quarterly NQ futures contracts",
        timeframe="One-minute Databento source qualification",
        strategy_name="databento_exact_contract_qualification",
        preregistration_file=Path("research/EXP-018_preregistration.md"),
    ),

'''

def git(*args):
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    ).stdout

if os.environ.get("DATABENTO_API_KEY") or os.environ.get("LSE_API_KEY"):
    raise RuntimeError("Remove API keys before applying.")

head = git("rev-parse", "HEAD").strip()
if head != EXPECTED_HEAD:
    raise RuntimeError(f"Expected HEAD {EXPECTED_HEAD}; found {head}.")

allowed_prefixes = (
    "README_EXP017_CLOSURE_EXP018_PREREGISTRATION.txt",
    "apply_exp017_closure_exp018_preregistration.py",
    "_exp018_payload/",
    "experiment_lifecycle.py",
)
unexpected = []
for line in git("status", "--porcelain", "--untracked-files=all").splitlines():
    path = line[3:].replace("\\\\", "/")
    if not any(path == p or path.startswith(p) for p in allowed_prefixes):
        unexpected.append(line)
if unexpected:
    raise RuntimeError("Unexpected Git changes:\\n" + "\\n".join(unexpected))

targets = {
    "exp017_closure.py": "exp017_closure.py",
    "research/EXP-017_closure.md": "research/EXP-017_closure.md",
    "exp018_preregistration.py": "exp018_preregistration.py",
    "research/EXP-018_preregistration.md": "research/EXP-018_preregistration.md",
    "tests/test_exp017_closure.py": "tests/test_exp017_closure.py",
    "tests/test_exp018_preregistration.py": "tests/test_exp018_preregistration.py",
    "tests/test_exp017_lifecycle.py": "tests/test_exp017_lifecycle.py",
}

for destination in targets:
    if (
        (ROOT / destination).exists()
        and destination != "tests/test_exp017_lifecycle.py"
    ):
        raise RuntimeError(f"Target already exists: {destination}")

lifecycle_path = ROOT / "experiment_lifecycle.py"
lifecycle = lifecycle_path.read_text(encoding="utf-8")
if lifecycle.count(OLD) != 1:
    raise RuntimeError(
        "Expected current EXP-017 lifecycle block exactly once."
    )
lifecycle = lifecycle.replace(OLD, NEW, 1)
compile(lifecycle, str(lifecycle_path), "exec")
lifecycle_path.write_text(lifecycle, encoding="utf-8", newline="\n")

for destination, source in targets.items():
    src = PAYLOAD / source
    dst = ROOT / destination
    dst.parent.mkdir(parents=True, exist_ok=True)
    source_text = src.read_text(encoding="utf-8")
    if dst.suffix == ".py":
        compile(source_text, str(dst), "exec")
    dst.write_text(source_text, encoding="utf-8", newline="\n")

shutil.rmtree(PAYLOAD)

print("EXP-017 closed as ACCESS_INCOMPLETE.")
print("EXP-017 OHLCV viewed: False")
print("Accessible exact-contract sources: 1 of required 2")
print("EXP-018 preregistered: True")
print("EXP-018 OHLCV viewed: False")
print("EXP-018 implementation created: False")
print("Databento bar access authorized now: False")
