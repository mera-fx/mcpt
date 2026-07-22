RESEARCH DASHBOARD V2 — PHASE 2
===============================

This package upgrades the heterogeneous research dashboard from commit
92533a90da5b97102822ea9fdef92da593be8cf0.

What it adds
------------

1. Experiment-specific saved-result adapters for:

   - EXP-004 quick screen
   - EXP-006 structured optimization
   - EXP-009 discovery tournament
   - EXP-010 opening-drive validation
   - EXP-011 position-sizing study
   - EXP-012 extended-context tournament
   - EXP-013 extended-context validation
   - EXP-014 finalist behaviour review

2. Multi-candidate and multi-method tables so discovery tournaments, validation
   studies, sizing studies and behaviour reviews are not presented as though
   they were identical single-strategy backtests.

3. Dedicated visual data-quality reports for EXP-015 through EXP-018.

4. Improved data-source parsing for:

   - EXP-015 assessment.classification and catalog counts
   - EXP-016 structural and cross-source sample measurements
   - EXP-017 ACCESS_INCOMPLETE lifecycle closure
   - EXP-018 exact-contract coverage, structural quality, cost and repeatability

5. Explicit descriptive-scope labels. A dashboard headline for a tournament or
   behaviour study never becomes an automatic winner, pass/fail decision, edge
   confirmation, paper-trading authorization or live-trading authorization.

Read-only boundary
------------------

The dashboard reads saved files only. It does not run:

- market-data downloads;
- EXP-015 catalog requests;
- EXP-016 audits;
- EXP-018 repeat requests;
- strategy simulations;
- optimization;
- MCPT;
- bootstrap;
- paper trading;
- live trading.

Generated report paths
----------------------

reports/EXP-015-data-quality/report.html
reports/EXP-016-data-quality/report.html
reports/EXP-017-data-quality/report.html
reports/EXP-018-data-quality/report.html

Dashboard path
--------------

reports/research_dashboard/index.html

Expected phase-2 result
-----------------------

All 18 lifecycle experiments should be displayed. The eight previously missing
strategy adapters should be populated, the four data-source experiments should
have dedicated reports, and the dashboard coverage-gap count should fall from
12 to 0 when all saved files are present.
