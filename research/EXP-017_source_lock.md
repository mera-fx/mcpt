# EXP-017 Price-Free Source-Set Lock

**Locked date:** 2026-07-22

**Status:** `SOURCE_SET_LOCKED_METADATA_PENDING`

**Benchmark bar values viewed:** none

## Locked source roles

- **Historical exact-contract candidate:** Databento `GLBX.MDP3`.
- **Exchange-native reference candidate:** CME DataMine.
- **Execution-feed context only:** Quantower connected to the Lucid Trading
  Rithmic evaluation account.
- **Excluded:** London Strategic Edge `NQ.F`, because exact expired NQ contract
  identity was not established.

This is not final OHLCV authorization. Exact aliases, expiry identity,
entitlements, licensing, timestamp semantics and request costs remain pending.

## Lucid/Rithmic/Quantower finding

The existing exports are generic `NQ` and `MNQ` files spanning multiple
expiries. Quantower displayed `NQ` as a front-month symbol. The connection
showed current exact contracts, but searches for `NQH4`, `NQM4`, `NQU4`,
`NQZ4`, `NQH5` and `NQM5` returned no symbols. This source is therefore kept
for execution-feed context but cannot supply the locked historical exact
contracts.

This does not classify Lucid, Rithmic or Quantower as inaccurate.

## Databento candidate

Official documentation identifies `GLBX.MDP3` as the CME Globex MDP 3.0
dataset. Parent and definition symbology can discover exact child contracts,
and individual child-contract requests require the API. Before OHLCV access,
metadata-only work must resolve the six exact aliases, expiration identity,
timestamp semantics, entitlement, license suitability and estimated cost.

## CME DataMine candidate

CME DataMine is CME Group's historical-data service. Exact NQ one-minute
product availability, format, timestamp semantics, license, entitlement and
price must be confirmed before any file download.

## Truth boundary

Quantower, Lucid/Rithmic and Databento are not assumed ground truth. CME
DataMine is the preferred exchange-native reference candidate, but access for
this exact request is not yet confirmed. Without an exchange reference, any
later winner can only be described as best among the sources tested.

## Next permitted work

Only metadata and commercial confirmation are allowed. No EXP-017 OHLCV may
be requested until a final source-eligibility lock is committed.
