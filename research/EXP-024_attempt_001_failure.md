# EXP-024 Attempt 001 Failure Record

**Failed date:** 2026-07-26

**Execution head:** `55ae174f5517bdb5afc48f5a36f5268fbc1eb42a`

**Authorization:** `EXP-024-ATTRIBUTION-AUTH-001`

**Outcome:** `FAILED_BEFORE_ATTRIBUTION`

## What happened

The authorized command entered the first protected Quantower scan. Arrow
correctly projected the `timestamp` field and the permitted current-session
OHLC rows. The frozen Quantower Parquet contains pandas metadata declaring
`timestamp` as its index, so `table.to_pandas()` restored the projected field
as the DataFrame index. The scanner then requested a regular `timestamp`
column and stopped with:

```text
KeyError: 'timestamp'
```

## Exact access boundary reached

- Quantower current mismatch windows, 08:00 through 09:34 New York OHLC:
  materialized
- Quantower 09:35 entry opens: not materialized
- Quantower required previous gap cash sessions: not materialized
- Quantower frozen five-minute bars: not materialized
- Databento values: not materialized
- Non-mismatch, current post-entry, out-of-overlap, or volume values: not
  materialized

No candidate feature was reconstructed, no attribution was calculated, and no
independent rebuild or report began.

## Evidence state

- Final EXP-024 output directory: absent
- Partial EXP-024 output directory: absent
- Frozen evidence modified: no
- Network or API access: no
- Strategy replay or performance calculation: no
- Paper or live action: no

Authorization 001 is treated as consumed. Retrying under it is prohibited.

## Replacement boundary

A replacement attempt requires all of the following:

1. preserve this failure record;
2. change only the protected conversion boundary so a projected timestamp
   restored as the named pandas index is reset to a regular column;
3. add a synthetic regression test using Parquet pandas-index metadata;
4. commit and push the replacement implementation;
5. pass a result-free replacement preflight;
6. commit a distinct one-time replacement authorization.

The candidate rules, mismatch population, permitted value windows, feature
formulas, attribution categories, frozen inputs, outputs, and interpretation
policy remain unchanged.
