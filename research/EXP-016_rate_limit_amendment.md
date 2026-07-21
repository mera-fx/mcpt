# EXP-016 Access Amendment A1

## One delayed retry after a vendor 429 response

**Amendment type:** Post-access operational correction

**Strategy or measurement amendment:** No

The original six-window request sequence completed five fixed samples.
The sixth fixed window, `2025_march_dst_roll`, returned:

```text
LSEError: [429] {"detail":"too many export requests; try again shortly"}
```

The failed request lock, five successful request locks, five raw-file
sizes and five raw-file SHA-256 hashes are frozen in
`exp016_rate_limit_amendment.py`.

## Why this amendment is narrow

The response is an access-throttling result, not a market-data quality
measurement. No sample window, symbol, timeframe, comparison method,
qualification threshold or strategy rule changes.

The original failed lock remains unchanged. A separate retry lock and a
separate raw destination are required.

## Permission

A single additional request is permitted only for:

```text
NQ.F
1m
2025-03-07 through 2025-03-21
```

The retry must occur at least 3,900 seconds after the recorded failure.
No other window may be requested. The catalog may not be rerun and full
history may not be downloaded.

The accounting after a successful retry is:

| Item | Count |
|---|---:|
| Original request attempts | 6 |
| Original successful exports | 5 |
| Original 429 failures | 1 |
| Amended retry attempts | 1 |
| Total remote history attempts | 7 |
| Successful fixed samples | 6 |

If the amended retry fails, no further remote request is authorized.
EXP-016 must close with access unavailable and may not run the six-window
local audit.

## Unchanged boundaries

- Quantower data remains frozen and read-only.
- No vendor bar is filled, deleted, resampled or repaired.
- No price offset is applied.
- No strategy is run or optimized.
- NQ.F cannot be promoted to primary-source status by this amendment.
- MNQ remains out of scope.
- No paper or live trading is authorized.
