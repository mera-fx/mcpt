# EXP-015 Catalog Result

## London Strategic Edge NQ/MNQ Data-Source Qualification

**Measured:** 21 July 2026

**Lifecycle after closure:** REVIEW

**Classification:** `IDENTITY_UNRESOLVED`

## What was actually accessed

The protected implementation used the official `lse-data 0.14.0`
client and called only:

```python
client.catalog("futures")
```

No candle, bulk-history, dataset, streaming or strategy method was
called.

The API key was supplied through a temporary environment variable and
removed after the catalog request. It was not printed or written into
the repository.

## Client compatibility result

The exact locked wheel was installed only in an isolated virtual
environment under the ignored `data/EXP-015` directory.

| Measurement | Result |
|---|---:|
| Client | `lse-data 0.14.0` |
| Probe Python | `3.14.6` |
| Locked wheel hash matched | Yes |
| Real API key used by compatibility probe | No |
| Market data accessed by compatibility probe | No |
| Main project virtual environment modified | No |

## Futures catalog result

| Measurement | Result |
|---|---:|
| Futures catalog rows | 69 |
| NQ candidates | 1 |
| MNQ candidates | 0 |
| Contract method resolved | No |
| Roll method resolved | No |
| Price adjustment resolved | No |
| Historical bars downloaded | No |

### NQ candidate

| Field | Catalog value |
|---|---|
| Symbol | `NQ.F` |
| Name | Nasdaq 100 Futures |
| Dataset | futures |
| Catalog tick count | 3,533,260 |
| First catalog timestamp | 29 May 2016 22:01:00 |
| Last catalog timestamp | 20 July 2026 19:58:00 |
| Country | United States |

`NQ.F` is a catalog candidate, not a fully resolved research series.
The catalog did not establish whether it is an individual or continuous
contract, how any continuous series rolls, whether prices are adjusted,
what session calendar is used, or how one-minute bars are constructed.

### MNQ result

No MNQ catalog candidate was found.

## Interpretation

London Strategic Edge is **not qualified as the primary NQ/MNQ source**
for this environment because EXP-015 required identifiable NQ and MNQ
series and documented contract methodology.

`NQ.F` may remain visible as an unresolved supplementary candidate, but
it cannot replace the frozen Quantower source. An NQ.F-only sample audit
would require a new preregistered experiment.

The result does not claim that every London Strategic Edge dataset is
unusable. It applies only to the locked NQ/MNQ historical-data use case.

## Frozen evidence

| Evidence | SHA-256 |
|---|---|
| `catalog_result.json` | `ba9595726de4018f4b283436c447e5aabd5dfa2109b5296c0a8e41159b3028e5` |
| `catalog_rows.csv` | `e191b695ae833984f781236e93551f102218937e5b10f2adb85358f996a5980a` |
| Canonical catalog rows | `55d5b8057c8b0b50e416d2a4f1601c86296992e334020d239114ade8dd45fceb` |

The catalog result was produced from implementation commit:

`8a74b9a49e95693f260f985df1300f545eedd1e7`

## Research boundary

EXP-015:

- did not replace EXP-005 through EXP-014 data;
- did not download historical bars;
- did not run a strategy;
- did not optimize parameters;
- did not qualify all vendor data;
- did not authorize paper or live trading.
