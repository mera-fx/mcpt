EXP-015 IMPLEMENTATION PACKAGE
==============================

This package adds the protected client-compatibility and catalog-only
implementation.

It does not install lse-data when extracted.
It does not read an API key when extracted.
It does not access the catalog when extracted.
It cannot download historical bars.
It cannot run strategies.

Apply:

    Expand-Archive `
        -Path "$env:USERPROFILE\Downloads\EXP-015-implementation.zip" `
        -DestinationPath "C:\Users\hocke\Documents\mcpt" `
        -Force

    Set-Location "C:\Users\hocke\Documents\mcpt"

Focused tests:

    .\.venv\Scripts\python.exe -m unittest `
        tests.test_exp015_preregistration `
        tests.test_exp015_lifecycle `
        tests.test_exp015_implementation `
        tests.test_exp015_catalog `
        tests.test_exp015_runner_boundary `
        -v

Then:

    git diff --check
    .\.venv\Scripts\python.exe run_framework_tests.py
    git status --short

Commit the implementation before running any mode of run_exp015_audit.py.
Do not enter or set an API key yet.
