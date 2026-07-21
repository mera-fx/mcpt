# EXP-016 Protected Implementation

## NQ.F Structural and Cross-Source Sample Audit

**Implementation state:** IMPLEMENTED / NOT RUN

This implementation is locked to preregistration commit:

`55577ca589fbc2b899c93a088592d32398121e49`

## Modes

The runner has three mutually exclusive modes:

```text
--preflight
--download-samples
--audit-local
```

No catalog, full-history, strategy or optimization mode exists.

## Remote boundary

The isolated `lse-data 0.14.0` environment created and verified by
EXP-015 is reused. The project virtual environment is not modified.

For each of the six preregistered windows, the worker may call only:

```python
client.history(
    "NQ.F",
    dataset="futures",
    timeframe="1m",
    start=...,
    end=...,
    dataframe=False,
)
```

A request-attempt lock is written before each remote call. A completed
window is never requested again. A failed or interrupted attempt remains
locked for review rather than being silently retried.

The API key is read only from `LSE_API_KEY`. It is not printed, written
or stored in a manifest.

## Local audit

The local audit verifies the frozen Quantower NQ extended-session
Parquet hash before reading it.

Vendor timestamps are converted to UTC only when the Parquet timestamp
field is already timezone-aware. A naive timestamp does not receive an
assumed timezone and produces `STRUCTURE_UNRESOLVED`.

The audit does not fill, delete, resample or repair bars. Duplicate
timestamps are measured and block ordinary timestamp matching.

The outputs measure:

- timestamp awareness and duplicates;
- finite OHLCV values;
- OHLC invariants and negative volume;
- matched, vendor-only and Quantower-only timestamps;
- OHLC absolute differences;
- close differences in the locked point buckets;
- closes within one NQ tick;
- descriptive volume differences;
- the 100 largest discrepancies per window.

## Interpretation boundary

The highest possible classification is supplementary NQ use.

Unresolved contract, continuous-series, roll and price-adjustment
methodology remains visible. The implementation cannot qualify NQ.F as
the primary source, qualify MNQ, replace Quantower data, run a strategy,
or authorize paper/live trading.
