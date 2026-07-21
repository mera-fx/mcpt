from __future__ import annotations
import ast
from pathlib import Path
from exp015_catalog_result import verify_local_exp015_catalog_result
from exp016_preregistration import validate_exp016_preregistration
from experiment_lifecycle import get_experiment_lifecycle

PROJECT_DIR=Path(__file__).resolve().parent
LIFECYCLE_FILE=PROJECT_DIR/'experiment_lifecycle.py'
EXP016_BLOCK='''

    "EXP-016": ExperimentLifecycle(
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

def _atomic_write(path,text):
    tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(text,encoding='utf-8')
    tmp.replace(path)

def add_exp016_lifecycle(text):
    if '"EXP-016": ExperimentLifecycle(' in text:
        return text
    n=text.find('\ndef normalize_experiment_id')
    if n<0:
        raise RuntimeError('Lifecycle normalize function was not found.')
    e=text.rfind('\n}',0,n)
    if e<0:
        raise RuntimeError('Lifecycle registry ending was not found.')
    updated=text[:e]+EXP016_BLOCK+text[e:]
    ast.parse(updated)
    return updated

def main():
    validate_exp016_preregistration()
    verify_local_exp015_catalog_result()
    expected={"EXP-005":"ACCEPTED_FOR_PAPER_TESTING","EXP-006":"REJECTED","EXP-007":"REJECTED","EXP-008":"REJECTED",
              "EXP-009":"REVIEW","EXP-010":"REVIEW","EXP-011":"REVIEW","EXP-012":"REVIEW","EXP-013":"REVIEW","EXP-014":"REVIEW","EXP-015":"REVIEW"}
    for experiment_id,stage in expected.items():
        actual=get_experiment_lifecycle(experiment_id).stage
        if actual!=stage:
            raise RuntimeError(f'{experiment_id} must remain {stage}; found {actual}.')
    original=LIFECYCLE_FILE.read_text(encoding='utf-8')
    updated=add_exp016_lifecycle(original)
    if updated==original:
        print('EXP-016 is already registered.')
    else:
        _atomic_write(LIFECYCLE_FILE,updated)
        print('Registered EXP-016 as PRE_REGISTERED.')
    print('EXP-015 frozen catalog evidence passed hash verification.')
    print('NQ.F history has not been accessed by EXP-016.')
    print('Six fixed sample windows are locked.')
    print('Full NQ.F history download is prohibited.')
    print('Frozen Quantower data remains read-only.')
    print('Strategy replay and optimization are prohibited.')
    print('No paper or live trading is authorized.')

if __name__=='__main__':
    main()
