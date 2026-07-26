# EXP-021 Protected Diagnostic Implementation

**Implementation date:** 2026-07-26

**Locked preregistration commit:** `27a960ad68f2059e5ac9d60e42e41a9171fbda41`

**Status:** Implemented, not authorised, not run

## Implemented scope

The implementation adds a protected diagnostic that:

- reads the frozen 66-contract EXP-019 archive locally;
- verifies the frozen EXP-020 closure and all EXP-020 output hashes;
- aggregates observed one-minute volume by New York trading date;
- evaluates the eight preregistered volume-roll candidates;
- forces all 23 provider-warning transitions to calendar fallback;
- retains every candidate and transition result;
- applies only the locked data-quality selection gates;
- performs an independent second local rebuild;
- writes diagnostic CSV and JSON evidence only.

## Protection boundary

The executable requires:

1. a clean `main` branch aligned with `origin/main`;
2. unchanged EXP-021 preregistration files;
3. a separately committed implementation lock;
4. a separately committed one-time diagnostic authorisation;
5. unchanged implementation and authorisation files;
6. no existing EXP-021 output directory;
7. no `DATABENTO_API_KEY`.

## Outputs

- `daily_volume_diagnostics.csv`
- `candidate_transition_diagnostics.csv`
- `candidate_method_summary.csv`
- `selected_method.json`
- `output_hashes.json`
- `report.md`
- `DIAGNOSTIC_COMPLETE.json`

## Explicit exclusions

This implementation does not:

- rerun EXP-019 or EXP-020;
- make a Databento API request;
- modify the source archive or EXP-020 outputs;
- construct or write a continuous series;
- calculate strategy returns or trading metrics;
- run optimisation, MCPT, bootstrap or walk-forward testing;
- authorise strategy, paper or live trading.

No diagnostic has been executed by this implementation package.
