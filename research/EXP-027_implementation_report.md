# EXP-027 Result-Free Implementation

**Experiment:** EXP-027

**Implementation status:** `RESULT_FREE_IMPLEMENTATION`

## Purpose

This implementation prepares the separately preregistered protected 2026
measurement. It does not authorise or execute the measurement.

## Frozen engine

Strategy signals and executions are delegated to the unchanged EXP-026 core
implementation at commit:

`13ee0683dfcbbb5d763f7254f3b245ecc8e6d9cd`

The EXP-027 layer does not change candidate parameters, entry logic, stops,
targets, time exits, cost assumptions or the conservative same-minute
stop/target rule.

## Protected loader

The execution loader requires an Arrow `date32` `trading_date` column and
attaches this predicate before a table is produced:

```text
2026-01-01 <= trading_date <= 2026-07-23
```

Historical 2010-2025 market rows are outside the EXP-027 scanner predicate.

The implementation preflight inspects only:

- repository and commit state;
- frozen file byte hashes;
- Parquet metadata and schema;
- installed package versions;
- absence of authorisation and output files.

It does not deserialize market values or calculate strategy results.

## Measurement population

The implementation locks:

- 22 unchanged EXP-026 strategy variants;
- two unchanged ORB controls;
- three predeclared primary candidates;
- 19 secondary strategy rows that cannot replace the primary cohort.

No selection or optimisation function is used by EXP-027.

## Rebuild integrity

An authorised execution must perform:

1. two independent protected-file loads and deterministic serial replays;
2. a separate candidate-chunk parallel replay;
3. exact decision-ledger and trade-ledger hash equality.

The output is rejected if independent rebuild or serial/parallel parity fails.

## Canonical evidence

Every one of the 24 rows must write:

```text
series/<candidate_id>/trades.csv
series/<candidate_id>/equity.csv
series/<candidate_id>/comparison_timeseries.csv
series/<candidate_id>/metrics.csv
```

Zero-trade candidates retain a header-only trade ledger and a dense flat equity
series.

## Reporting

The authorised run is designed to write:

- all/long/short measurements;
- monthly results;
- zero-through-three-tick cost sensitivity;
- backward-adjusted versus unadjusted sensitivity;
- trade distributions;
- drawdown episodes;
- frozen EXP-026 historical context;
- full-width equity and drawdown charts;
- Markdown and HTML reports;
- a complete byte-hash manifest.

## Execution boundary

This implementation does not authorise protected access.

A separate authorization commit must lock the implementation commit and permit
exactly one run. The runner rejects execution when that authorization module is
absent.

No Databento API call, download, network access, paper trading, live trading,
order connection or capital deployment is implemented or authorised.
