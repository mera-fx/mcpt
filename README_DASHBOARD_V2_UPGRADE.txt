RESEARCH DASHBOARD V2 UPGRADE
=============================

This package adds a heterogeneous dashboard without replacing or deleting the
existing dashboard builder.

The upgraded dashboard separates:

- strategy research: EXP-001 through EXP-014;
- data-source qualification: EXP-015 through EXP-018.

It reads lifecycle records and saved files only. It does not rerun a strategy,
optimization, MCPT, bootstrap, market-data request, audit download or paper
simulator.

Files
-----

- dashboard_experiment_profiles.py
- build_research_dashboard_v2.py
- tests/test_dashboard_experiment_profiles.py
- tests/test_build_research_dashboard_v2.py

The v2 builder writes the normal dashboard location:

reports/research_dashboard/index.html

It also writes:

results/research_dashboard_profiles.csv
results/research_dashboard_profiles.json

Blank strategy metrics are deliberately reported as adapter gaps rather than
being guessed from unrelated files. Data-source experiments use structural,
coverage, repeatability, cost and claim-boundary measurements when a saved
qualification JSON is available.
