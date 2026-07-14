# EXP-005-DQ4 — Confirmation Missing-Session Resolution

## Status

`LOCKED_BEFORE_FULL_VALIDATION_RESULTS`

This resolution was written after the protected confirmation importer
identified three missing or incomplete full sessions and before any
confirmation strategy, Profit Factor, MCPT or full-validation decision
was calculated.

## Dedicated retry evidence

The dedicated one-day NQ and MNQ exports contain no duplicate
timestamps.

| Session | NQ cash bars | MNQ cash bars | Resolution |
|---|---:|---:|---|
| 2025-09-24 | 389 | 389 | Exclude both symbols |
| 2025-11-07 | 321 | 321 | Exclude both symbols |
| 2025-12-31 | 390 | 390 | Restore the complete session |

For 2025-09-24, both retries omit exactly `10:59 ET`.

For 2025-11-07, both retries omit the same 69 cash-session minutes:
`11:50, 11:51, 11:52, 11:53, 11:54, 11:55, 11:56, 11:57, 11:58, 11:59, 12:00, 12:01, 12:02, 12:03, 12:04, 12:05, 12:06, 12:07, 12:08, 12:09, 12:10, 12:11, 12:12, 12:13, 12:14, 12:15, 12:16, 12:17, 12:18, 12:19, 12:20, 12:21, 12:22, 12:23, 12:24, 12:25, 12:26, 12:27, 12:28, 12:29, 12:30, 12:31, 12:32, 12:33, 12:34, 12:35, 12:36, 12:37, 12:38, 12:39, 12:40, 12:41, 12:42, 12:43, 12:44, 12:45, 12:46, 12:47, 12:48, 12:49, 12:50, 12:51, 12:52, 12:53, 12:54, 12:55, 12:56, 12:57, 12:59`.

The 2025-12-31 retries contain every minute from `09:30` through
`15:59 America/New_York`.

## Locked policy

- Keep the original full 2023–2025 exports unchanged.
- Keep all six dedicated retries unchanged.
- Verify every retry by SHA-256, boundaries, row count and exact cash
  minute profile.
- Exclude NQ and MNQ together for 2025-09-24 and 2025-11-07.
- Restore 2025-12-31 only from its complete locked retry for each
  symbol.
- Fill or synthesize zero bars.
- Stop on any unrecorded missing session or changed retry profile.
- Do not alter the strategy, costs, gates or quick-transfer result.

## Expected processed confirmation sample

- Frozen calendar full sessions: 744
- Paired provider-unavailable exclusions: 2
- Included sessions: 742
- One-minute rows per symbol: 289,380
- Five-minute rows per symbol: 57,876
- Included invalid sessions: 0
- Bars synthesized: 0

## Research-result protection

The quick-transfer result remains frozen. This resolution uses source
data only and calculates no trades, Profit Factor, MCPT p-value or
full-validation decision.
