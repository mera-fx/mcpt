# EXP-020 Preregistration

**Title:** NQ Exact-Contract Continuous-Series Construction

**Locked date:** 2026-07-25

**Lifecycle:** `PRE_REGISTERED`

**Implementation:** `NOT_IMPLEMENTED`

## Research purpose

Construct deterministic and auditable one-minute NQ continuous series from
the frozen EXP-019 exact-contract archive.

EXP-020 is a data-engineering experiment only. Strategy performance will not
be inspected or used to choose the roll method.

## Frozen input

| Measure | Locked value |
|---|---|
| Source experiment | `EXP-019` |
| EXP-019 closure commit | `e86a9074385ad8d2c1b61711b5739910882c2b18` |
| Classification | `QUALIFIED_WITH_KNOWN_PROVIDER_CONDITIONS` |
| Exact quarterly contracts | 66 |
| Audited records | 6,276,486 |
| Compressed bytes | 104,491,346 |
| Hard audit failures | 0 |
| Known provider-warning windows | 16 |
| Source archive | Read-only |
| Databento API calls permitted | 0 |

## Primary roll method

`VOLUME_CROSSOVER_2_SESSION_WITH_CALENDAR_FALLBACK`

For each adjacent contract pair:

1. Convert timestamps to daylight-saving-aware `America/New_York` time.
2. Assign trading dates using the 18:00 New York session boundary.
3. Sum observed one-minute volume for both contracts by trading date.
4. Exclude known provider-warning sessions from trigger evaluation.
5. Require incoming-contract volume to be strictly greater for two
   consecutive eligible sessions.
6. Roll at the start of the following trading session.
7. Use the locked calendar boundary when no valid crossover occurs first.
8. Disclose every calendar fallback.

Intraday rolling is prohibited.

## Calendar benchmark and fallback

`CALENDAR_THURSDAY_8_DAYS_BEFORE_EXPIRY`

Roll at the first complete trading session beginning after the Thursday eight
calendar days before the locked EXP-019 planning expiry date.

The calendar series is a benchmark. It cannot replace the primary series
because of better strategy performance.

## Stitching rule

- Use the outgoing contract before the effective roll trading date.
- Use the incoming contract on and after the effective roll trading date.
- Preserve source-contract, roll-method and adjustment columns.
- Do not fill missing no-trade minutes.
- Do not create synthetic bars.
- Do not resolve duplicates using arbitrary first-row or last-row selection.

## Adjustment method

Use `BACKWARD_DIFFERENCE`.

At each roll:

1. Find the latest timestamp shared by both contracts before the boundary.
2. Calculate `incoming close - outgoing close`.
3. Add the cumulative difference to all earlier OHLC prices.
4. Do not adjust timestamps or volume.
5. Preserve the unadjusted series.

Forward adjustment and ratio adjustment are prohibited.

## Required series

1. `volume_roll_unadjusted`
2. `volume_roll_backward_adjusted`
3. `calendar_roll_unadjusted`
4. `calendar_roll_backward_adjusted`

## Required evidence

- Roll ledger covering all 65 adjacent transitions
- Contract contribution table
- Calendar-fallback disclosure
- Adjustment reconciliation
- Timestamp and duplicate checks
- OHLCV validity checks
- Quarter-point tick checks
- Missing-minute diagnostics
- Independent deterministic rebuild
- SHA-256 hashes for every final output

## Locked hard checks

Twenty hard checks cover source evidence, all 65 transitions, roll-boundary
ordering, common adjustment references, timestamp uniqueness, source-row
reconciliation, OHLCV validity, quarter-point alignment, exact adjustment
reconciliation and deterministic rebuild hashes.

## Classification

- Any hard failure: `NOT_QUALIFIED`
- All checks with no calendar fallback:
  `QUALIFIED_VOLUME_CROSSOVER_CONTINUOUS_SERIES`
- All checks with disclosed calendar fallbacks:
  `QUALIFIED_WITH_DISCLOSED_CALENDAR_FALLBACKS`

Qualification applies only to the constructed dataset.

## Prohibited work

EXP-020 must not:

- request or download market data;
- modify EXP-019 files;
- inspect strategy performance;
- run strategy testing, optimization, MCPT, bootstrap or walk-forward analysis;
- run paper or live trading;
- claim exchange-verified accuracy;
- claim that Databento is the best vendor;
- authorise strategy use.

A separately preregistered experiment is required before strategy research.
