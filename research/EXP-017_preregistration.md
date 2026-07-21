# EXP-017 Exact NQ Contract Data Benchmark — Preregistration

**Locked date:** 2026-07-21

**Stage:** PRE_REGISTERED
**Benchmark bar values viewed:** none

EXP-017 will determine which accessible exact-contract one-minute NQ source has the strongest evidence for new historical strategy research. Data quality is evaluated before cost; cost and licensing are tie-breakers only.

Continuous futures symbols are prohibited. Every comparison must use the same quarterly contract, such as NQH24 versus NQH24. This removes vendor-specific roll and back-adjustment rules from the price comparison.

A separate tracked source-lock record is required before downloading benchmark bars. It must freeze the Quantower exact-contract export and actual provider, London only when exact-contract identity can be verified, and one independent exchange-native or exchange-licensed reference candidate when accessible. Source selection may use documentation, metadata, licensing, access method, historical depth and quoted cost, but not OHLCV values or strategy results.

Two exact-contract sources are the minimum; three are the target. Two disagreeing sources cannot identify truth. Without an exchange reference, three-source consensus can identify only the best available among those tested.

## Locked windows

| Window | Contract | Start | End | Context |
|---|---|---|---|---|
| nqh24_february_ordinary | NQH24 | 2024-02-05 | 2024-02-16 | Ordinary |
| nqm24_may_ordinary | NQM24 | 2024-05-06 | 2024-05-17 | Ordinary |
| nqu24_august_volatility | NQU24 | 2024-08-05 | 2024-08-16 | High volatility |
| nqz24_thanksgiving | NQZ24 | 2024-11-22 | 2024-12-06 | Holiday/early close |
| nqh25_march_dst | NQH25 | 2025-03-07 | 2025-03-14 | DST transition |
| nqm25_may_ordinary | NQM25 | 2025-05-12 | 2025-05-23 | Ordinary |

Thanksgiving and March-DST are repeated after at least 24 hours to measure reproducibility.

No bar may be filled, deleted, repaired or shifted. Measurements cover identity, timestamp semantics, structural validity, regular and extended-session completeness, matched/source-only minutes, OHLC differences, one-tick agreement, volume differences, session boundaries and repeat-download stability.

A primary candidate requires all six windows, resolved identity/timestamps, zero structural defects, at least 99.99% regular-session completeness, at least 99.9% extended-session completeness, exchange-referenced one-tick thresholds, and identical canonical rows in both repeatability windows.

There is no weighted score. Eligible sources are compared by exchange-referenced OHLC accuracy, completeness, repeatability, execution-feed similarity, operational reliability, then cost/licensing.

EXP-005 through EXP-016 remain frozen. EXP-017 cannot replace prior data, download full history, construct a continuous series, replay strategies, optimize parameters, or authorize paper/live trading. A separate experiment is required for full history and an internally controlled continuous NQ series.
