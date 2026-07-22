# EXP-017 Exact NQ Contract Data Benchmark — Closure

**Closed date:** 2026-07-22

**Lifecycle:** `REVIEW`

**Classification:** `ACCESS_INCOMPLETE`

**Benchmark OHLCV viewed:** none

EXP-017 required at least two accessible exact-contract sources before a
price comparison. Only Databento satisfied the metadata and identity checks
within the user's budget. No price comparison or winner selection occurred.

## Databento

All six locked contracts resolved and their definition identities were
confirmed:

| Contract | Raw symbol | Instrument ID | Expiration UTC | Estimated bars |
|---|---|---:|---|---:|
| NQH24 | `NQH4` | 750 | 2024-03-15 13:30 | $0.050133 |
| NQM24 | `NQM4` | 13,743 | 2024-06-21 13:30 | $0.049921 |
| NQU24 | `NQU4` | 4,358 | 2024-09-20 13:30 | $0.049943 |
| NQZ24 | `NQZ4` | 106,364 | 2024-12-20 14:30 | $0.053499 |
| NQH25 | `NQH5` | 42,288,528 | 2025-03-21 13:30 | $0.030009 |
| NQM25 | `NQM5` | 42,005,804 | 2025-06-20 13:30 | $0.049943 |

Combined estimated bar cost: **$0.283447**.

Definitions confirmed `XCME`, NQ futures, a 0.25-point tick and $20 per
index point. This confirms identity, not structural quality, repeatability
or exchange-verified price accuracy.

## CME DataMine

The catalogue exposed exchange-native NQ Market Depth FIX dataset
`MD_XCME_NQ_FUT_0`. It displayed $18,558 for complete history and $4,257
for an annual subscription. Prebuilt one-minute OHLCV was not confirmed.

The user cannot purchase the dataset. No order or sample download occurred.

## Other candidates

Lucid/Rithmic did not expose the required expired contracts. London exposed
only unresolved `NQ.F`. Website scraping was not used.

EXP-017 closes without weakening its rules. Previous experiments remain
frozen. No paper or live trading is authorized.
