EXP-015 CATALOG FREEZE PACKAGE
==============================

This package freezes the observed catalog evidence and closes EXP-015
to REVIEW.

Frozen findings:

- 69 futures catalog rows
- one NQ candidate: NQ.F
- zero MNQ candidates
- contract, roll and adjustment methodology unresolved
- classification: IDENTITY_UNRESOLVED
- historical bars downloaded: False
- London Strategic Edge qualified as primary NQ/MNQ source: False

Apply:

    Expand-Archive `
        -Path "$env:USERPROFILE\Downloads\EXP-015-catalog-freeze.zip" `
        -DestinationPath "C:\Users\hocke\Documents\mcpt" `
        -Force

    Set-Location "C:\Users\hocke\Documents\mcpt"

Close the lifecycle after verifying the ignored local result files:

    .\.venv\Scripts\python.exe close_exp015_review.py

Focused tests:

    .\.venv\Scripts\python.exe -m unittest `
        tests.test_exp015_preregistration `
        tests.test_exp015_implementation `
        tests.test_exp015_catalog `
        tests.test_exp015_catalog_result `
        tests.test_exp015_lifecycle `
        tests.test_exp015_runner_boundary `
        -v

Then:

    git diff --check
    .\.venv\Scripts\python.exe run_framework_tests.py
    git status --short

Do not set the API key or rerun catalog access.
Do not commit until the output has been reviewed.
