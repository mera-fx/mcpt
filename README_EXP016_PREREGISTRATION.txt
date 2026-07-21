EXP-016 PREREGISTRATION PACKAGE
===============================

This package adds only the protected EXP-016 preregistration and
lifecycle entry.

It does not read an API key.
It does not access NQ.F history.
It does not rerun the catalog.
It does not download complete history.
It does not run a strategy.

Apply:

    Expand-Archive `
        -Path "$env:USERPROFILE\Downloads\EXP-016-preregistration.zip" `
        -DestinationPath "C:\Users\hocke\Documents\mcpt" `
        -Force

    Set-Location "C:\Users\hocke\Documents\mcpt"

    .\.venv\Scripts\python.exe register_exp016.py

Focused tests:

    .\.venv\Scripts\python.exe -m unittest `
        tests.test_exp016_preregistration `
        tests.test_exp016_lifecycle `
        -v

Then:

    git diff --check
    .\.venv\Scripts\python.exe run_framework_tests.py
    git status --short

Do not set the API key or access NQ.F history.
Do not commit until the output has been reviewed.
