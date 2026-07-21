from __future__ import annotations
import csv, hashlib, json, os, pprint, subprocess
from copy import deepcopy
from pathlib import Path

ROOT=Path(__file__).resolve().parent
EXPECTED_HEAD="c25a517432c40c3c6e2e768dcaef7f2c6c660133"
RESULT_ROOT=ROOT/"results"/"EXP-016"/"source_qualification"
RESULT_JSON=RESULT_ROOT/"audit_result.json"
STRUCTURAL=RESULT_ROOT/"structural_measurements.csv"
CROSS=RESULT_ROOT/"cross_source_measurements.csv"
DISCREP=RESULT_ROOT/"largest_discrepancies.csv"
MANIFEST=ROOT/"data"/"EXP-016"/"nq_f_samples"/"download_manifest.json"
FREEZE_JSON=ROOT/"research"/"EXP-016_audit_freeze.json"
FREEZE_MODULE=ROOT/"exp016_audit_result.py"
RESULT_MD=ROOT/"research"/"EXP-016_audit_result.md"
LIFECYCLE=ROOT/"experiment_lifecycle.py"
WINDOWS=("2020_march_dst_roll_volatility","2021_thanksgiving","2022_june_roll","2023_march_dst_roll","2024_thanksgiving","2025_march_dst_roll")
OUTSIDE=("2021_thanksgiving","2024_thanksgiving")

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()
def canonical(v):
    return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
def loadj(p):
    x=json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(x,dict): raise RuntimeError(f"Expected JSON object: {p}")
    return x
def loadc(p):
    with p.open("r",encoding="utf-8",newline="") as f: return list(csv.DictReader(f))
def write(p,s):
    p.parent.mkdir(parents=True,exist_ok=True)
    t=p.with_suffix(p.suffix+".tmp"); t.write_text(s,encoding="utf-8",newline="\n"); t.replace(p)
def git(*a):
    return subprocess.run(["git",*a],cwd=ROOT,text=True,capture_output=True,check=True).stdout.rstrip()

if os.environ.get("LSE_API_KEY"): raise RuntimeError("Remove LSE_API_KEY first.")
if git("rev-parse","HEAD")!=EXPECTED_HEAD: raise RuntimeError("Unexpected HEAD; stop.")
allowed={
 "README_EXP016_CLOSURE_EXP017_PREREGISTRATION.txt",
 "apply_exp016_closure_exp017_preregistration.py",
 "exp017_preregistration.py",
 "research/EXP-017_preregistration.md",
 "tests/test_exp016_lifecycle.py",
 "tests/test_exp016_audit_result.py",
 "tests/test_exp017_preregistration.py",
 "tests/test_exp017_lifecycle.py",
}
unexpected=[]
for line in git("status","--porcelain","--untracked-files=all").splitlines():
    if line and line[3:].replace(chr(92),"/") not in allowed: unexpected.append(line)
if unexpected: raise RuntimeError("Unexpected Git changes before application:\n"+"\n".join(unexpected))
for p in (RESULT_JSON,STRUCTURAL,CROSS,DISCREP,MANIFEST):
    if not p.is_file(): raise RuntimeError(f"Missing completed EXP-016 evidence: {p}")
for p in (FREEZE_JSON,FREEZE_MODULE,RESULT_MD):
    if p.exists(): raise RuntimeError(f"Output already exists: {p}")

r=loadj(RESULT_JSON); s=loadc(STRUCTURAL); c=loadc(CROSS); d=loadc(DISCREP); m=loadj(MANIFEST)
if not (r.get("experiment_id")=="EXP-016" and r.get("classification")=="NOT_QUALIFIED" and r.get("result_phase")=="LOCAL_SAMPLE_AUDIT" and r.get("sample_windows")==6): raise RuntimeError("EXP-016 result changed.")
if r["git"]["commit"]!=EXPECTED_HEAD or r["git"]["working_tree_clean"] is not True: raise RuntimeError("EXP-016 provenance changed.")
if tuple(x["window_id"] for x in s)!=WINDOWS or tuple(x["window_id"] for x in c)!=WINDOWS: raise RuntimeError("Window set changed.")
for x in s:
    if not (x["timestamp_source"]=="ts" and x["timestamp_timezone_aware"].lower()=="true" and all(int(x[k])==0 for k in ("duplicate_timestamp_count","invalid_ohlc_rows","negative_volume_rows","nonfinite_ohlcv_rows"))): raise RuntimeError("Structural evidence changed.")
for x in c:
    if not (x["comparison_status"]=="MEASURED" and float(x["expected_minute_completeness"])<.999 and float(x["matched_timestamp_share"])<.999): raise RuntimeError("Coverage evidence changed.")
by={x["window_id"]:x for x in c}
for w in OUTSIDE:
    if float(by[w]["close_within_one_tick_share"])>=.995: raise RuntimeError("Outside-roll evidence changed.")
if not (m["successful_sample_count"]==6 and m["original_request_attempt_count"]==6 and m["amended_retry_attempt_count"]==1 and m["total_remote_history_request_attempts"]==7 and m["api_key_written"] is False): raise RuntimeError("Manifest changed.")
for x in m["requests"]:
    p=ROOT.joinpath(*str(x["local_path"]).replace("\\","/").split("/"))
    if not p.is_file() or p.stat().st_size!=int(x["size_bytes"]) or sha(p)!=x["sha256"]: raise RuntimeError(f"Raw sample changed: {x['window_id']}")

freeze={
 "schema_version":1,"experiment_id":"EXP-016","freeze_status":"AUDIT_MEASURED_REVIEW","classification":"NOT_QUALIFIED","result_git_commit":EXPECTED_HEAD,
 "file_hashes":{"audit_result_json_sha256":sha(RESULT_JSON),"structural_measurements_csv_sha256":sha(STRUCTURAL),"cross_source_measurements_csv_sha256":sha(CROSS),"largest_discrepancies_csv_sha256":sha(DISCREP),"download_manifest_json_sha256":sha(MANIFEST)},
 "result":r,"structural_rows":s,"cross_source_rows":c,"largest_discrepancy_row_count":len(d),
 "sample_files":[{"window_id":x["window_id"],"size_bytes":int(x["size_bytes"]),"sha256":x["sha256"]} for x in m["requests"]],
 "interpretation":{"vendor_files_structurally_clean":True,"cross_source_coverage_below_locked_threshold":True,"outside_roll_price_agreement_below_locked_threshold":True,"london_nq_f_inaccurate_claimed":False,"interchangeable_with_frozen_quantower":False,"qualified_as_supplementary_source":False,"quantower_proven_as_ground_truth":False,"quantower_replaced":False,"strategy_replay_run":False,"paper_trading_authorized":False,"live_trading_authorized":False,"expected_lifecycle_after_measurement":"REVIEW"}
}
freeze["canonical_sha256"]=canonical(freeze)
write(FREEZE_JSON,json.dumps(freeze,indent=2,allow_nan=False)+"\n")

module=f'''from __future__ import annotations
from copy import deepcopy
import csv, hashlib, json
from pathlib import Path
from typing import Any, Mapping
ROOT=Path(__file__).resolve().parent
TRACKED=ROOT/"research"/"EXP-016_audit_freeze.json"
LOCAL=ROOT/"results"/"EXP-016"/"source_qualification"
EXPECTED={pprint.pformat(freeze,width=100,sort_dicts=False)}

def _canonical(v):
    return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
def _sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()
def _csv(p):
    with p.open("r",encoding="utf-8",newline="") as f: return list(csv.DictReader(f))
def get_exp016_audit_freeze(): return deepcopy(EXPECTED)
def validate_exp016_audit_freeze(record: Mapping[str,Any]|None=None):
    x=EXPECTED if record is None else dict(record)
    if x.get("experiment_id")!="EXP-016" or x.get("classification")!="NOT_QUALIFIED" or x.get("freeze_status")!="AUDIT_MEASURED_REVIEW": raise ValueError("EXP-016 audit freeze identity changed.")
    y=deepcopy(x); stored=y.pop("canonical_sha256",None)
    if _canonical(y)!=stored: raise ValueError("EXP-016 audit freeze canonical hash changed.")
    i=x["interpretation"]
    if i["london_nq_f_inaccurate_claimed"] is not False or i["quantower_proven_as_ground_truth"] is not False or i["qualified_as_supplementary_source"] is not False or i["quantower_replaced"] is not False or i["paper_trading_authorized"] is not False or i["live_trading_authorized"] is not False: raise ValueError("EXP-016 interpretation changed.")
def verify_tracked_exp016_audit_freeze():
    validate_exp016_audit_freeze()
    actual=json.loads(TRACKED.read_text(encoding="utf-8"))
    if actual!=EXPECTED: raise ValueError("Tracked EXP-016 freeze changed.")
    return actual
def verify_local_exp016_audit_outputs():
    x=verify_tracked_exp016_audit_freeze(); h=x["file_hashes"]
    files={{"audit_result_json_sha256":LOCAL/"audit_result.json","structural_measurements_csv_sha256":LOCAL/"structural_measurements.csv","cross_source_measurements_csv_sha256":LOCAL/"cross_source_measurements.csv","largest_discrepancies_csv_sha256":LOCAL/"largest_discrepancies.csv","download_manifest_json_sha256":ROOT/"data"/"EXP-016"/"nq_f_samples"/"download_manifest.json"}}
    for k,p in files.items():
        if _sha(p)!=h[k]: raise ValueError(f"EXP-016 local hash changed: {{p}}")
    if json.loads(files["audit_result_json_sha256"].read_text(encoding="utf-8"))!=x["result"]: raise ValueError("Local audit result changed.")
    if _csv(files["structural_measurements_csv_sha256"])!=x["structural_rows"]: raise ValueError("Local structural rows changed.")
    if _csv(files["cross_source_measurements_csv_sha256"])!=x["cross_source_rows"]: raise ValueError("Local cross-source rows changed.")
    return x
'''
write(FREEZE_MODULE,module)

rows=[f'| {x["window_id"]} | {100*float(x["expected_minute_completeness"]):.6f}% | {100*float(x["matched_timestamp_share"]):.6f}% | {100*float(x["close_within_one_tick_share"]):.6f}% |' for x in c]
hashrows=[f"| {k} | `{v}` |" for k,v in freeze["file_hashes"].items()]
md=f'''# EXP-016 NQ.F Structural and Cross-Source Sample Audit Result

**Classification:** `NOT_QUALIFIED`

All six vendor samples were structurally clean. The source failed interchangeable supplementary qualification because every window was below the locked 99.9% expected-minute and matched-timestamp thresholds, and both outside-roll windows were below the 99.5% close-within-one-tick threshold.

This does not prove London data is inherently inaccurate and does not prove Quantower is ground truth. It proves the two tested continuous series are not sufficiently equivalent under the locked rules.

| Window | Completeness | Matched timestamps | Close within one tick |
|---|---:|---:|---:|
{chr(10).join(rows)}

Raw vendor bars and largest-discrepancy rows remain local and gitignored. Only aggregate measurements and hashes are tracked.

| Local output | SHA-256 |
|---|---|
{chr(10).join(hashrows)}

**Tracked aggregate canonical SHA-256:** `{freeze["canonical_sha256"]}`
'''
write(RESULT_MD,md)

old='''    "EXP-016": ExperimentLifecycle(
        experiment_id="EXP-016",
        experiment_name="NQ.F Structural and Cross-Source Sample Audit",
        hypothesis=(
            "The London Strategic Edge NQ.F one-minute series may be complete, "
            "internally valid and sufficiently consistent with the frozen "
            "Quantower NQ reference to serve as a supplementary source."
        ),
        stage="PRE_REGISTERED",
        stage_reason=(
            "Six fixed DST, holiday and roll sample windows, structural checks, "
            "cross-source comparisons and supplementary-only interpretation "
            "rules were locked before accessing NQ.F history."
        ),
        next_action=(
            "Implement and commit a protected six-request NQ.F sample audit. "
            "Do not rerun the catalog, download full history, alter Quantower "
            "data, run strategies or authorize paper/live trading."
        ),
        market_name="NQ.F versus frozen Quantower NQ",
        timeframe="One-minute structural and cross-source sample audit",
        strategy_name="nq_f_data_sample_qualification",
        preregistration_file=Path("research/EXP-016_preregistration.md"),
    ),
'''
new='''    "EXP-016": ExperimentLifecycle(
        experiment_id="EXP-016",
        experiment_name="NQ.F Structural and Cross-Source Sample Audit",
        hypothesis=(
            "The London Strategic Edge NQ.F one-minute series may be complete, "
            "internally valid and sufficiently consistent with the frozen "
            "Quantower NQ reference to serve as a supplementary source."
        ),
        stage="REVIEW",
        stage_reason=(
            "The protected six-window audit classified NQ.F as NOT_QUALIFIED. "
            "All samples were structurally clean, but expected-minute and matched-"
            "timestamp shares ranged from 87.978% to 98.889%, below the locked "
            "99.9% requirement. The two outside-roll close-within-one-tick shares "
            "were 97.047% and 97.826%, below the locked 99.5% requirement."
        ),
        next_action=(
            "Preserve EXP-016 in REVIEW. Do not rerun its download, retry or audit. "
            "Use a new exact-contract benchmark before selecting data for new research."
        ),
        market_name="NQ.F versus frozen Quantower NQ",
        timeframe="One-minute structural and cross-source sample audit",
        strategy_name="nq_f_data_sample_qualification",
        preregistration_file=Path("research/EXP-016_preregistration.md"),
    ),

    "EXP-017": ExperimentLifecycle(
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
            "Create and commit the EXP-017 source-lock record before any bar access. "
            "Resolve exact aliases, provider provenance, licensing and an exchange-"
            "reference candidate without viewing OHLCV values."
        ),
        market_name="Exact quarterly NQ futures contracts",
        timeframe="One-minute multi-source data benchmark",
        strategy_name="exact_nq_contract_data_benchmark",
        preregistration_file=Path("research/EXP-017_preregistration.md"),
    ),
'''
src=LIFECYCLE.read_text(encoding="utf-8")
if src.count(old)!=1: raise RuntimeError("Expected EXP-016 lifecycle block exactly once.")
src=src.replace(old,new,1); compile(src,str(LIFECYCLE),"exec"); write(LIFECYCLE,src)
for p in (FREEZE_MODULE,ROOT/"exp017_preregistration.py",ROOT/"tests"/"test_exp016_lifecycle.py",ROOT/"tests"/"test_exp016_audit_result.py",ROOT/"tests"/"test_exp017_preregistration.py",ROOT/"tests"/"test_exp017_lifecycle.py",LIFECYCLE):
    compile(p.read_text(encoding="utf-8"),str(p),"exec")
print("Closed EXP-016 and preregistered EXP-017.")
print("EXP-016 classification: NOT_QUALIFIED")
print("EXP-016 lifecycle: REVIEW")
print("EXP-017 lifecycle: PRE_REGISTERED")
print("Tracked aggregate freeze SHA256:",freeze["canonical_sha256"])
print("Remote request performed: False")
print("API key accessed: False")
print("Strategy run performed: False")
print("EXP-017 benchmark bars accessed: False")
print("EXP-017 source lock still required: True")
