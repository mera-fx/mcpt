EXP-014 FINAL RESULT FREEZE PACKAGE

Purpose
-------
This package freezes the corrected EXP-014 finalist behaviour result,
verifies all analytical outputs, and formally closes EXP-014 to REVIEW.

It does not include generated result or report files. Those must already
exist locally from the corrected run at implementation commit f56c1e0.

Files
-----
close_exp014_review.py
exp014_behaviour_result.py
research/EXP-014_behaviour_result.md
tests/test_exp014_behaviour_result.py
tests/test_exp014_lifecycle.py

Installation
------------
Run from C:\Users\hocke\Documents\mcpt:

Expand-Archive `
    -Path "$env:USERPROFILE\Downloads\EXP-014-final-freeze.zip" `
    -DestinationPath "C:\Users\hocke\Documents\mcpt" `
    -Force

Then verify the current state:

git status --short
git log -1 --oneline

Expected before closure:
- HEAD is f56c1e0
- no tracked or untracked source changes
- corrected results and report already exist

Close EXP-014 to REVIEW
-----------------------
.\.venv\Scripts\python.exe close_exp014_review.py

This first verifies the complete corrected result and its frozen hashes,
then changes only the EXP-014 lifecycle block.

Focused tests
-------------
.\.venv\Scripts\python.exe -m unittest `
    tests.test_exp014_preregistration `
    tests.test_exp014_implementation `
    tests.test_exp014_measurements `
    tests.test_exp014_report `
    tests.test_exp014_runner_boundary `
    tests.test_exp014_behaviour_result `
    tests.test_exp014_lifecycle `
    -v

Full verification
-----------------
git diff --check
.\.venv\Scripts\python.exe run_framework_tests.py
git status --short

Expected changed files:
 M experiment_lifecycle.py
 M tests/test_exp014_lifecycle.py
?? close_exp014_review.py
?? exp014_behaviour_result.py
?? research/EXP-014_behaviour_result.md
?? tests/test_exp014_behaviour_result.py

Commit only after all tests pass
--------------------------------
git add `
    close_exp014_review.py `
    exp014_behaviour_result.py `
    experiment_lifecycle.py `
    research/EXP-014_behaviour_result.md `
    tests/test_exp014_behaviour_result.py `
    tests/test_exp014_lifecycle.py

git diff --cached --check
git commit -m "Freeze corrected EXP-014 behaviour result"

Do not rerun EXP-014 after the result is frozen.
Do not add the ignored results or reports directories to Git.
Do not push until the final commit and test output have been reviewed.
