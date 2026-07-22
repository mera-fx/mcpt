EXP-017 SOURCE-SET LOCK
=======================

Expected repository HEAD:
  1c55e053e862485da6a94f2cff6599beba07265e

This package records the price-free source investigation and keeps all EXP-017
OHLCV access prohibited.

Apply in PowerShell:

Expand-Archive `
    -Path "$env:USERPROFILE\Downloads\EXP-017-source-set-lock.zip" `
    -DestinationPath "C:\Users\hocke\Documents\mcpt" `
    -Force

Set-Location "C:\Users\hocke\Documents\mcpt"

Remove-Item Env:LSE_API_KEY -ErrorAction SilentlyContinue
Remove-Item Env:DATABENTO_API_KEY -ErrorAction SilentlyContinue

.\.venv\Scripts\python.exe apply_exp017_source_set_lock.py

Focused validation:

.\.venv\Scripts\python.exe -m unittest `
    tests.test_exp016_audit_result `
    tests.test_exp017_preregistration `
    tests.test_exp017_source_lock `
    tests.test_exp017_lifecycle `
    tests.test_experiment_lifecycle `
    -v

Then:

git diff --check
.\.venv\Scripts\python.exe run_framework_tests.py
git status --short

Do not access EXP-017 OHLCV yet. The next step is metadata-only alias,
entitlement, licensing, timestamp-semantics and cost confirmation.
