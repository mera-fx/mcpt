# EXP-026 Result-Free Implementation Report

**Experiment:** EXP-026

**Implementation status:** `IMPLEMENTED_NOT_AUTHORIZED`

**Preregistration commit:** `ce661c7785fa6d8d409378ee2ad63a00f0e0a9b9`

## Scope

This implementation provides the complete protected execution path for the
three preregistered EXP-026 phases without calculating any strategy result.

The implementation includes:

- a protected Arrow trading-date loader;
- deterministic New York session normalization;
- observed-only one-minute to five-minute aggregation;
- all 22 development candidates;
- both fixed ORB controls;
- conservative one-minute stop and target execution;
- All / Long / Short metrics;
- Phase A and Phase B selection;
- anchored walk-forward measurement;
- session-block bootstrap;
- selection-aware market permutation testing;
- parameter-neighbour stability;
- known-period cost and representation sensitivity;
- vertical full-width reports;
- independent deterministic rebuilds;
- separate authorization and completion interfaces for each phase.

## Protected data access

The loader attaches a `trading_date` predicate to the Arrow scanner before a
table is produced. The implementation rejects every requested end date after
2025-12-31.

The implementation preflight may read:

- file bytes for SHA-256 verification;
- Parquet schema;
- Parquet row count and row-group metadata.

It does not deserialize OHLCV rows.

The 2026 period remains inaccessible to EXP-026.

## Candidate engine

The replay engine implements:

### Gap fade

- previous eligible cash close and cash range;
- opening-gap fraction;
- opposite-direction first cash bar;
- 09:35 entry;
- first-bar outer-extreme stop;
- prior-close or one-R target;
- 15:55 forced exit.

### Premarket continuation

- 08:00 through 09:29 premarket drive fraction;
- same-direction first cash bar;
- 09:35 entry;
- first-bar opposite-extreme stop;
- time or 1.5R exit;
- 15:55 forced exit.

### Opening drive

- first 30-minute drive fraction;
- 10:00 entry in the drive direction;
- opposite opening-range stop;
- time or 1.5R exit;
- 15:55 forced exit.

### Controls

- unchanged EXP-005 15-minute both-direction ORB;
- unchanged EXP-007 30-minute long-only one-R ORB.

Controls are report-only and cannot enter either selection step.

## Statistical implementation

### Selection-aware MCPT

The Phase B null is a session-shared post-entry market-path sign permutation.

For every session, one random real-or-mirrored post-entry path choice is shared
across all 22 candidates. This preserves cross-candidate dependence and keeps
the entry-known setup schedule fixed while breaking its directional alignment
with the realised post-entry path.

Every permutation repeats:

1. Phase A selection of up to two candidates per family;
2. Phase B selection of up to one candidate per family;
3. the registered cross-family statistic.

The method is conditional on the observed entry-known setup schedule. It is not
a claim that the full market-generating process is reproduced.

### Bootstrap

The bootstrap resamples whole sessions. All trades from a sampled session are
retained together.

### Walk-forward

For each 2014 through 2019 test year:

- the earliest training years form the development block;
- the two immediately preceding years form the internal-validation block;
- both selection stages are repeated;
- the frozen fold finalists are measured only in the next year.

## Phase boundary

No phase authorization module is created by this implementation.

The runner refuses to execute unless the required separate phase authorization
exists, validates, targets the implementation commit and is the current clean
`main` HEAD.

Phase B additionally requires a committed Phase A completion record.

Phase C additionally requires a committed Phase B completion record.

## Outputs

Outputs are written first to a phase-specific partial directory. A completed
directory is published only after:

- deterministic independent rebuild agreement;
- required-output verification;
- output hash-manifest creation;
- completion-marker creation.

Existing output or partial-output directories cause a hard stop.

## Explicit non-actions

This implementation does not:

- access or deserialize market values;
- calculate a strategy result;
- run Phase A;
- create an authorization;
- call Databento;
- use network access;
- change the roll rule;
- change the adjustment method;
- change the candidate grid;
- access protected 2026 history;
- authorize paper or live trading.
