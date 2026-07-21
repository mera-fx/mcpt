EXP-016 CLOSURE + EXP-017 PREREGISTRATION

After extracting into C:\Users\hocke\Documents\mcpt:

Remove-Item Env:LSE_API_KEY -ErrorAction SilentlyContinue

.\.venv\Scripts\python.exe `
    apply_exp016_closure_exp017_preregistration.py

Then run:

.\.venv\Scripts\python.exe -m unittest `
    tests.test_exp016_preregistration `
    tests.test_exp016_lifecycle `
    tests.test_exp016_implementation `
    tests.test_exp016_measurements `
    tests.test_exp016_measurement_alignment `
    tests.test_exp016_timestamp_schema `
    tests.test_exp016_rate_limit_amendment `
    tests.test_exp016_path_separator_correction `
    tests.test_exp016_runner_boundary `
    tests.test_exp016_audit_result `
    tests.test_exp017_preregistration `
    tests.test_exp017_lifecycle `
    tests.test_experiment_lifecycle `
    -v

git diff --check
.\.venv\Scripts\python.exe run_framework_tests.py
git status --short

Do not rerun EXP-016 download, retry or audit.
Do not access EXP-017 bars yet.
A separate EXP-017 source-lock record must be committed before any benchmark bars.
