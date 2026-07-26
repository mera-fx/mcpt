# EXP-024 Replacement Implementation Report

**Implemented:** 2026-07-26

**Attempt 001 status:** `FAILED_BEFORE_ATTRIBUTION`

**Replacement status:** `CORRECTED_NOT_REAUTHORIZED_NOT_RUN`

## Narrow correction

The replacement changes one market-value conversion boundary:

```python
frame = table.to_pandas(...)
if timestamp_column not in frame.columns:
    if frame.index.name != timestamp_column:
        raise RuntimeError(...)
    frame = frame.reset_index()
```

This handles both frozen source layouts:

- Quantower Parquet, where pandas metadata restores `timestamp` as the index;
- Databento Parquet, where `ts_event` remains a regular column.

The Arrow predicate and explicit projection still execute before pandas
materialization. The correction does not broaden any row interval or column
set.

## Unchanged research boundary

The following remain byte-for-byte or logically unchanged:

- the EXP-024 preregistration and three candidates;
- the exact 51 frozen mismatch rows;
- all frozen input hashes;
- the permitted current and prior-session windows;
- the feature formulas and thresholds;
- the seven attribution categories;
- the 26 hard checks and required outputs;
- the prohibition on exits, P&L, performance, optimization, source ranking,
  protected history, and trading.

## Regression coverage

The protected scanner tests now write a synthetic Parquet file from a pandas
DataFrame whose named `timestamp` index is preserved in Parquet metadata. The
test verifies that:

- Arrow filtering and projection still precede conversion;
- the timestamp is restored as a regular column;
- only permitted rows are returned;
- prohibited columns are absent.

## Replacement gates

Before another execution attempt:

1. this replacement implementation and the attempt-001 failure record must be
   committed together;
2. the clean synchronized result-free replacement preflight must pass;
3. a distinct `EXP-024-ATTRIBUTION-AUTH-002` commit must lock the replacement
   implementation;
4. final and partial output directories must remain absent.

No EXP-024 result is calculated by this correction.
