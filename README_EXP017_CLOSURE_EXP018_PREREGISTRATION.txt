EXP-017 CLOSURE + EXP-018 PREREGISTRATION
=========================================

This package performs documentation and preregistration only.
It does not request or download OHLCV.

Expected repository HEAD:
c9589ed58eb956ef02c7ba4906479c06c0ca32b8

Apply
-----
Expand-Archive `
    -Path "$env:USERPROFILE\Downloads\EXP-017-closure-EXP-018-preregistration.zip" `
    -DestinationPath "C:\Users\hocke\Documents\mcpt" `
    -Force

Set-Location "C:\Users\hocke\Documents\mcpt"

Remove-Item Env:LSE_API_KEY -ErrorAction SilentlyContinue
Remove-Item Env:DATABENTO_API_KEY -ErrorAction SilentlyContinue

.\.venv\Scripts\python.exe `
    .\apply_exp017_closure_exp018_preregistration.py

Focused tests
-------------
.\.venv\Scripts\python.exe -m unittest `
    tests.test_exp017_preregistration `
    tests.test_exp017_source_lock `
    tests.test_exp017_closure `
    tests.test_exp017_lifecycle `
    tests.test_exp018_preregistration `
    tests.test_experiment_lifecycle `
    -v

Full validation
---------------
git diff --check
.\.venv\Scripts\python.exe run_framework_tests.py
git status --short

Do not restore DATABENTO_API_KEY or request EXP-018 bars until these
preregistration changes are committed and pushed.
