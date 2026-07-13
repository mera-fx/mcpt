# EXP-005 Preregistration

## NQ/MNQ 5-Minute ORB Locked Transfer

**Status:** PRE_REGISTERED  
**Originally locked:** 2026-07-13  
**Source amendment:** EXP-005-A1, locked 2026-07-13  
**Implementation:** Not implemented  
**Full quick-transfer data exported:** No  
**Source-validation samples inspected:** Yes  
**Strategy results viewed:** None

EXP-005 is a no-optimization transfer test. It asks whether the
exact fixed basic ORB from EXP-004 behaves differently on
Nasdaq-100 futures.

It does not reopen or repair EXP-004.

## 1. Fixed inherited signal

EXP-005 inherits exactly:

```text
Opening range: 15 minutes
Direction: long and short
Confirmation: completed five-minute close outside the range
Entry: next five-minute open
Last signal bar: 11:55 ET
Protective stop: opposite opening-range boundary
Maximum trades: one per session
Same-day reversal: prohibited
Forced flat: 15:55 ET bar open
Overnight position: prohibited
```

There is one parameter combination and no optimization.

## 2. Markets and evidence hierarchy

| Role | Contract |
|---|---|
| Primary transfer evidence | NQ |
| Secondary contract/cost check | MNQ |

MNQ is not treated as an independent second market because it
tracks the same Nasdaq-100 futures exposure. It tests whether the
smaller contract remains viable after its different per-contract
cost burden.

## 3. Amended free historical source

The original Databento source was replaced before any complete
research-period export or strategy result was viewed.

```text
Provider: Lucid Trading / Rithmic
Export application: Quantower History Exporter
Additional data cost: $0
Input format: Time-Time one-minute CSV
NQ symbol: NQ — provider-managed front month
MNQ symbol: MNQ — provider-managed front month
CSV timestamps: parsed as UTC
Five-minute bars: aggregated locally from one-minute bars
```

The exact provider rollover trigger and any historical price
adjustment method are not exposed by the CSV export. EXP-005
therefore makes no volume-roll, calendar-roll, adjusted-price or
unadjusted-price claim.

This uncertainty is limited by the strategy design: every range,
signal, entry and exit occurs within the same 09:30–16:00 ET cash
session. Previous closes, overnight gaps, cross-session returns
and overnight positions are not used.

For a session to be included, NQ and MNQ must have identical cash
minute timestamps. A session is excluded from both symbols as a
potential front-month mismatch or data anomaly when either:

```text
Median absolute NQ–MNQ one-minute close difference > 5 points
Maximum absolute NQ–MNQ one-minute close difference > 20 points
```

Zero potential mismatch sessions may be included.

The full amendment is recorded in:

```text
research/EXP-005_source_amendment.md
```

## 4. Source-validation evidence

A single normal session, 9 August 2019, was exported for each
provider front-month symbol solely to establish data availability,
timestamp interpretation and file quality.

| Check | NQ | MNQ |
|---|---:|---:|
| Raw one-minute rows | 1,305 | 1,300 |
| 09:30–16:00 ET rows | 390 | 390 |
| Five-minute bars | 78 | 78 |
| Missing cash minutes | 0 | 0 |
| Duplicate timestamps | 0 | 0 |
| Invalid OHLC rows | 0 | 0 |
| Tick violations | 0 | 0 |

No ORB trades, returns, Profit Factors, parameter comparisons or
pass/fail decisions were calculated from these samples.

## 5. Session rules

- ORB anchor: 09:30 New York cash-equity open
- Included window: 09:30–16:00 ET
- Required input: exactly 390 one-minute bars per symbol
- Required output: exactly 78 five-minute bars per symbol
- Early closes: excluded
- Incomplete sessions: excluded
- Missing-bar filling: prohibited
- Duplicate timestamps: stop
- Potential front-month mismatch: exclude from both symbols
- Included invalid or mismatch sessions: zero
- Raw files are immutable after import

Raw exports may contain surrounding futures bars, but only the
locked cash-session window enters the research data.

## 6. Protected research periods

| Stage | Period | Access |
|---|---|---|
| Quick transfer | 2019-05-06 through 2022-12-30 | First |
| Confirmation | 2023-01-03 through 2025-12-31 | Locked until quick pass |

The start date remains the MNQ launch date. The source amendment
does not alter either period.

## 7. Contract and cost assumptions

### NQ

```text
Multiplier: $20 per index point
Minimum tick: 0.25 points
Tick value: $5.00
Commission/exchange/NFA assumption: $2.50 per side
Slippage: 1 tick = $5.00 per side
Total modeled cost: $7.50 per side
Round trip: $15.00
```

### MNQ

```text
Multiplier: $2 per index point
Minimum tick: 0.25 points
Tick value: $0.50
Commission/exchange/NFA assumption: $1.00 per side
Slippage: 1 tick = $0.50 per side
Total modeled cost: $1.50 per side
Round trip: $3.00
```

These assumptions and every decision gate remain unchanged.

## 8. Session-aware MCPT

EXP-005 uses the same economic randomization principle as EXP-004,
beginning with one-minute futures bars:

- Relative OHLC components are permuted across complete sessions
  inside each one-minute time slot.
- Session-opening components are permuted separately.
- Synthetic one-minute sessions are reconstructed.
- Synthetic data is aggregated to five-minute bars.
- Time-of-day distributions and session boundaries are preserved.
- No parameter optimization occurs on real or permuted data.
- Deterministic numbered seeds are required.
- Serial and multicore results must match exactly.

```text
Random seed: 45
Quick MCPT: 25 NQ permutations
Full MCPT: 1,000 NQ permutations
```

## 9. Quick-transfer gates

All gates must pass:

| Gate | Requirement |
|---|---:|
| NQ completed-trade PF | Strictly above 1.05 |
| MNQ completed-trade PF | Strictly above 1.00 |
| NQ net P&L | Strictly above $0 |
| MNQ net P&L | Strictly above $0 |
| NQ session-aware MCPT p-value | At most 0.20 |
| NQ completed trades | At least 700 |
| NQ long trades | At least 150 |
| NQ short trades | At least 150 |
| Included invalid sessions | 0 |
| Included front-month mismatch sessions | 0 |

A failure rejects EXP-005 without exposing 2023–2025.

## 10. Full-validation gates

All gates must pass:

| Gate | Requirement |
|---|---:|
| NQ completed-trade PF | Strictly above 1.05 |
| MNQ completed-trade PF | Strictly above 1.00 |
| NQ net P&L | Strictly above $0 |
| MNQ net P&L | Strictly above $0 |
| NQ 1,000-permutation MCPT p-value | At most 0.05 |
| NQ completed trades | At least 500 |
| Profitable NQ calendar years | At least 2 |
| Included invalid sessions | 0 |
| Included front-month mismatch sessions | 0 |

A pass advances to review rather than directly to paper testing.

## 11. Interpretation limits

- A rejection applies only to the unchanged basic ORB.
- It does not reject more structured ORB variants.
- A pass supports this exact rule set only.
- NQ and MNQ are not independent confirmations.
- The provider roll and adjustment methods remain unknown.
- No result may be used to change EXP-005 after disclosure.

Structured ORB research remains separate in:

```text
research/ORB_structured_variant_roadmap.md
```
