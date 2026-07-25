# EXP-020 One-Time Construction Authorization

**Authorization date:** 2026-07-25

**Authorization status:** `AUTHORIZED`

**Construction status:** `NOT_RUN`

## Locked commits

| Boundary | Commit |
|---|---|
| Preregistration | `93776c52806820e137ec02f7fe6382d8981c4500` |
| Constructor implementation | `36473b354c0b1a200c01494d4b64a78cee1e3430` |

The implementation commit includes:

- `exp020_constructor.py`
- `exp020_constructor_core.py`
- `tests/test_exp020_constructor.py`
- `research/EXP-020_implementation_report.md`

## Authorised action

One local construction run is authorised after the protected read-only
preflight passes.

The run may:

- read the frozen EXP-019 archive;
- construct the four preregistered continuous-series outputs;
- create the locked ledgers, diagnostics, report and completion marker;
- perform the required independent deterministic rebuild;
- write only to the new EXP-020 output directory.

## Source boundary

- Source experiment: `EXP-019`
- Exact quarterly contracts: 66
- Audited records: 6,276,486
- Archive classification:
  `QUALIFIED_WITH_KNOWN_PROVIDER_CONDITIONS`
- Archive access: read-only
- Databento API calls: 0
- Credentials required: No
- Minimum free disk space: 4,000,000,000 bytes

## Run limit

- Maximum construction runs: 1
- Completed output overwrite: Prohibited
- Construction rerun: Prohibited
- Partial output must be retained after an error for diagnosis

## Not authorised

This authorization does not permit:

- strategy replay;
- optimisation;
- MCPT;
- bootstrap analysis;
- walk-forward analysis;
- paper trading;
- live trading;
- modification of EXP-019;
- claims of exchange-verified accuracy;
- claims that Databento is the best vendor.

A separately preregistered experiment is required before strategy research.
