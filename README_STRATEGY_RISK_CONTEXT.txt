RESEARCH REPORT POSITION-SIZING CONTEXT UPGRADE
================================================

Purpose
-------
Add visible position-sizing and initial-risk context to the shared
"How the strategy works" sections.

Scope
-----
- EXP-005 through EXP-010:
  fixed one NQ primary measurement and fixed one MNQ implementation
  comparison; fixed contract quantity but variable dollar risk.
- EXP-011:
  fixed one NQ, theoretical fractional NQ, and practical integer MNQ
  equal-dollar-risk methods using the frozen $1,005 target.
- EXP-009 family explanations:
  shared fixed-contract context.

The upgrade also changes the report refresher so an existing
strategy-rules section is replaced from the catalog rather than skipped.
Unregistered data-source reports are not modified.

Safety
------
- Reads and rewrites report HTML only when the explicit refresher is run.
- Does not rerun strategies, optimization, MCPT, bootstrap, downloads,
  paper simulation, or live trading.
- Does not change frozen experiment results.
