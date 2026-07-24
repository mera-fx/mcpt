# EXP-018 Databento Exact-Contract Qualification Closure

**Closed date:** 2026-07-24

**Lifecycle stage:** `REVIEW`

**Classification:** `QUALIFIED_AS_ACCESSIBLE_EXACT_CONTRACT_SOURCE`

## Result

Databento `GLBX.MDP3` exact-contract NQ one-minute data passed the
preregistered structural, coverage, cost and delayed-repeatability gates.

| Measurement | Result |
|---|---:|
| Initial windows measured | 6 |
| Delayed repeat windows measured | 2 |
| Successful bar requests | 8 |
| Automatic retries | 0 |
| Minimum regular trade-minute coverage | 100.000000% |
| Minimum extended trade-minute coverage | 99.918699% |
| Total estimated cost | $0.366955 |

## Delayed repeatability

| Window | Delay hours | Canonical rows | Row count | Timestamp set |
|---|---:|---:|---:|---:|
| `nqh25_march_dst` | 48.394 | True | True | True |
| `nqz24_thanksgiving` | 48.398 | True | True | True |

Both repeats occurred after the locked minimum delay of 24 hours.
Canonical hashes, row counts and timestamp sets matched exactly.

## Structural quality

The six locked initial windows contained:

- zero instrument-identity mismatch rows;
- zero duplicate timestamps;
- zero duplicate full rows;
- zero invalid OHLC rows;
- zero negative-volume rows;
- zero non-finite OHLCV rows;
- zero off-tick OHLC values.

## Interpretation

EXP-018 qualifies Databento as an accessible exact-contract source for
separately preregistered future research.

It does **not**:

- verify exchange accuracy;
- establish Databento as the best vendor;
- authorize a full-history download;
- authorize continuous-contract construction under EXP-018;
- validate any strategy;
- alter earlier experiments;
- authorize paper or live trading.

EXP-018 must not be rerun.
