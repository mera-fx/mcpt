EXP-018 PROTECTED IMPLEMENTATION
================================

This package builds the protected Databento exact-contract downloader,
structural audit and delayed-repeatability implementation.

It does not access Databento when extracted, applied or tested.
It does not read or write an API key during tests.
It does not request OHLCV automatically.
It does not run a strategy.

Expected repository HEAD:
fd0844dacab65f25d160e0b32a2273504528551f

Apply
-----
Expand-Archive `
    -Path "$env:USERPROFILE\Downloads\EXP-018-protected-implementation.zip" `
    -DestinationPath "C:\Users\hocke\Documents\mcpt" `
    -Force

Set-Location "C:\Users\hocke\Documents\mcpt"

Remove-Item Env:LSE_API_KEY -ErrorAction SilentlyContinue
Remove-Item Env:DATABENTO_API_KEY -ErrorAction SilentlyContinue

.\.venv\Scripts\python.exe .\apply_exp018_implementation.py

Focused tests
-------------
.\.venv\Scripts\python.exe -m unittest `
    tests.test_exp017_closure `
    tests.test_exp018_preregistration `
    tests.test_exp018_implementation `
    tests.test_exp018_measurements `
    tests.test_exp018_runner_boundary `
    tests.test_exp017_lifecycle `
    tests.test_experiment_lifecycle `
    -v

Full validation
---------------
git diff --check
.\.venv\Scripts\python.exe run_framework_tests.py
git status --short

Commit and push the implementation before running --preflight.
Do not restore DATABENTO_API_KEY or request bars before that commit.
