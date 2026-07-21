EXP-014 COMPLETED IMPLEMENTATION PACKAGE
========================================

Purpose
-------
This package completes the interrupted EXP-014 protected implementation.
It overwrites the three incomplete implementation files, adds the protected
runner, and adds focused synthetic tests. It does not contain or alter the
already-pushed EXP-014 preregistration.

Files
-----
exp014_implementation.py
exp014_measurements.py
exp014_report.py
run_exp014_study.py
research/EXP-014_implementation.md
tests/exp014_test_data.py
tests/test_exp014_implementation.py
tests/test_exp014_measurements.py
tests/test_exp014_report.py
tests/test_exp014_runner_boundary.py

Install from PowerShell
-----------------------
1. Keep the EXP-014-uncommitted.zip backup you already made.

2. Extract this ZIP into the project root:

   Expand-Archive `
       -Path "$env:USERPROFILE\Downloads\EXP-014-completed-implementation.zip" `
       -DestinationPath "C:\Users\hocke\Documents\mcpt" `
       -Force

   Change the ZIP path if your browser saved it somewhere else.

3. Open the project:

   Set-Location "C:\Users\hocke\Documents\mcpt"

4. Run the focused EXP-014 checks:

   .\.venv\Scripts\python.exe -m unittest `
       tests.test_exp014_preregistration `
       tests.test_exp014_lifecycle `
       tests.test_exp014_implementation `
       tests.test_exp014_measurements `
       tests.test_exp014_report `
       tests.test_exp014_runner_boundary `
       -v

   Expected at the current repository checkpoint: 31 focused tests passing.

5. Run formatting and the complete framework:

   git diff --check
   .\.venv\Scripts\python.exe run_framework_tests.py

6. Confirm no EXP-014 result was calculated:

   Test-Path .\results\EXP-014\finalist_behaviour
   Test-Path .\reports\EXP-014-research-lab
   git status --short

   The two Test-Path commands should return False before the one-time run.

7. Commit the result-free implementation:

   git add `
       exp014_implementation.py `
       exp014_measurements.py `
       exp014_report.py `
       run_exp014_study.py `
       research/EXP-014_implementation.md `
       tests/exp014_test_data.py `
       tests/test_exp014_implementation.py `
       tests/test_exp014_measurements.py `
       tests/test_exp014_report.py `
       tests/test_exp014_runner_boundary.py

   git commit -m "Implement protected EXP-014 behaviour study"

8. Run the clean-commit preflight:

   .\.venv\Scripts\python.exe run_exp014_study.py --preflight

Do not run --run until the focused tests, full framework, clean commit and
preflight have all passed. The protected runner will refuse to calculate a
result from an uncommitted working tree.

What was added
--------------
- Exact reconstruction checks against frozen EXP-013 headline metrics.
- Year, month, direction, exit, holding-time, context and regime analysis.
- 2025 comparisons against 2020-2024 and 2022-2024.
- Fixed rolling 20-trade and 50-trade diagnostics.
- MFE/MAE, concentration, losing streak and worst-window measurements.
- Session-based drawdown duration and recovery.
- Pairwise overlap, correlation and underwater diagnostics.
- Two fixed arithmetic research-sleeve comparisons.
- A vertical plain-English report with 18 opaque-white charts.
- No MCPT, bootstrap or walk-forward rerun.
- No parameter, regime-filter, weight or winner selection.
- No paper or live trading authorization.
