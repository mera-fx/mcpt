# EXP-025 Closure

**Closed date:** 2026-07-27

**Research status:** `REVIEW`

**Classification:** `BLOCKED_DATA_UNAVAILABLE`

**Closure record SHA-256:** `b386a0c45a81e40a3f9459f802882b8c749b6038e1d447b75d14d59acfea660c`

## Objective

EXP-025 was preregistered to compare the same explicit quarterly NQ contracts
from Quantower/Lucid-Rithmic and the frozen Databento exact-contract archive for
43 unresolved EXP-024 gap-fade sessions.

The comparison required explicit contract identity. Continuous or generic
symbols were prohibited as exact-contract evidence.

## Work completed

The result-free implementation was frozen at:

`2011745145b9799a4a42b556d57780002d30e317`

The separate Quantower export authorisation was frozen at:

`6a76dba1702f87f7610b0d7346958478c6685ed4`

Both the corrected implementation preflight and the Quantower export preflight
passed.

No diagnostic execution was authorised.

## Provider-access result

The required March 2020 contract could not be found using `NQH20`, `NQH0` or
`NQH0.CME` in Quantower.

`NQH0.CME` also returned zero results in R Trader Pro.

Generic `NQ` history was available, but Lucid did not confirm whether that
history was continuous, back-adjusted, unadjusted, which roll trigger it used,
or which contract supplied each historical row.

## Rejected format-verification files

Two generic-`NQ` CSV files were produced only during the format check and were
quarantined:

| File | Rows | Size | SHA-256 |
|---|---:|---:|---|
| `01_2020-01-22_GENERIC_NQ_previous.csv` | 389 | 44,529 | `622945e4ef717c3b4d3fd32e1c30e0d84d4f39367a9fa3839c2dd9b71e1ca809` |
| `01_2020-01-22_GENERIC_NQ_current.csv` | 5 | 656 | `3b12528811de9fbefdd7037e6b355647d8f542da400f3f2f46ba7528ba5d43fe` |

The CSV structure contained no explicit contract-symbol column. Renaming a file
to include `NQH20` cannot establish the contract that generated its rows.

These files are rejected audit evidence and are not part of an accepted
exact-contract manifest.

## Research conclusion

EXP-025 did not execute its diagnostic.

Therefore EXP-025 establishes none of the following:

- exact-contract source equivalence;
- a Quantower or Databento source winner;
- decision-engine qualification;
- strategy edge;
- strategy failure;
- candidate acceptance or rejection.

Its only conclusion is that the required Lucid/Rithmic expired exact-contract
evidence was unavailable through the accessible account and tools.

## Next research boundary

EXP-025 is frozen and must not be rerun or weakened to accept generic `NQ`
history.

Future historical strategy testing will use the Databento-first policy recorded
at `research/HISTORICAL_DATA_POLICY.md`.

Existing frozen Databento archives may be reused when a new experiment permits
them. A new Databento download or API request still requires separate
authorisation.

A future cross-provider comparison requires a new experiment ID and separate
preregistration.

This closure does not authorise paper trading, live trading, order access or
capital deployment.
