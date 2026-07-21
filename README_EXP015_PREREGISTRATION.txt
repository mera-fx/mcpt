EXP-015 PREREGISTRATION PACKAGE
==================================

This package adds only the protected EXP-015 preregistration and
lifecycle entry.

It does not install lse-data.
It does not read an API key.
It does not access the vendor catalog.
It does not download market data.
It does not run a strategy.

Apply from the repository root:

    Expand-Archive `
        -Path "$env:USERPROFILE\Downloads\EXP-015-preregistration.zip" `
        -DestinationPath "C:\Users\hocke\Documents\mcpt" `
        -Force

    Set-Location "C:\Users\hocke\Documents\mcpt"

    .\.venv\Scripts\python.exe register_exp015.py

Focused tests:

    .\.venv\Scripts\python.exe -m unittest `
        tests.test_exp015_preregistration `
        tests.test_exp015_lifecycle `
        -v

Then:

    git diff --check
    .\.venv\Scripts\python.exe run_framework_tests.py
    git status --short

Do not commit until the output has been reviewed.
