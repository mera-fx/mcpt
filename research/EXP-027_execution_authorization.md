# EXP-027 One-Time Execution Authorisation

**Experiment:** EXP-027

**Authorised date:** 2026-07-28

**Status:** `AUTHORIZED`

**Authorization SHA-256:** `d0745af1570530772ec8b647aedb81c4c0a88f4358c087b9dd72765d694ff383`

## Authorised action

This record authorises exactly one execution of:

```text
exp027_runner.py
```

against the frozen EXP-027 implementation commit:

```text
591cdf43b4c23abc312ae3d50b7d7948f88c90b2
```

## Data boundary

The authorised Arrow scanner predicate is:

```text
2026-01-01 <= trading_date <= 2026-07-23
```

The predicate must be attached before a table is materialised.

Authorised local read-only representations:

1. `selected_roll_backward_adjusted.parquet`
2. `selected_roll_unadjusted.parquet`

The backward-adjusted series is primary. The unadjusted series is
representation sensitivity only.

Historical 2010-2025 market-row access is not authorised by EXP-027.

## Candidate boundary

The run must report:

- 22 unchanged EXP-026 strategy variants;
- two unchanged ORB controls;
- three predeclared primary candidates;
- 19 secondary strategy rows as comparison context.

EXP-027 does not authorise selection, reselection, parameter changes,
secondary-candidate promotion, a composite score or one winner.

## Execution integrity

The authorised run requires:

- a clean `main` branch aligned with `origin/main`;
- the authorisation commit to equal `HEAD`;
- no existing final or partial output directory;
- two independent serial rebuilds;
- a separate parallel rebuild;
- exact decision and trade hash parity;
- an output byte-hash manifest;
- no rerun after successful completion.

A failed or interrupted execution requires separate review. It does not
automatically authorise a recovery run.

## Output contract

Every one of the 24 evidence rows must write:

```text
series/<candidate_id>/trades.csv
series/<candidate_id>/equity.csv
series/<candidate_id>/comparison_timeseries.csv
series/<candidate_id>/metrics.csv
```

Root reports, cost sensitivity, representation sensitivity, monthly results,
trade distributions, drawdown episodes and historical context are also
required.

## Explicitly not authorised

This record does not authorise:

- a Databento API call;
- any market-data download;
- network access;
- modification of frozen EXP-022 or EXP-026 evidence;
- missing-bar repair or synthetic bars;
- paper trading;
- live trading;
- order API access;
- capital deployment.

The result remains measurement evidence and does not automatically establish
an edge, strategy failure or trading approval.
