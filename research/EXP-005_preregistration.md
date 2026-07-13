# EXP-005 Preregistration

## NQ/MNQ 5-Minute ORB Locked Transfer

**Status:** PRE_REGISTERED  
**Locked:** 2026-07-13  
**Implementation:** Not implemented  
**NQ/MNQ research data downloaded:** No  
**NQ/MNQ results viewed:** None

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

## 3. Historical data convention

```text
Provider: Databento
Dataset: GLBX.MDP3
Input schema: ohlcv-1m
Input symbol type: continuous
NQ symbol: NQ.v.0
MNQ symbol: MNQ.v.0
Roll rule: volume-ranked front contract
Price adjustment: none
Five-minute bars: aggregated from one-minute bars
```

Continuous prices remain the original unadjusted contract prices.
Any session in which the mapped contract changes during the
09:30–16:00 ET test window is excluded.

## 4. Session rules

- ORB anchor: 09:30 New York cash-equity open
- Included window: 09:30–16:00 ET
- Required input: exactly 390 one-minute bars
- Required output: exactly 78 five-minute bars
- Early closes: excluded
- Incomplete sessions: excluded
- Missing-bar filling: prohibited
- Duplicate timestamps: stop
- Intraday roll switch: exclude the session
- Included invalid or roll-switch sessions: zero

Futures data outside the cash window may be used only to identify
the session-opening gap or contract mapping. No overnight signal
or position is allowed.

## 5. Protected research periods

| Stage | Period | Access |
|---|---|---|
| Quick transfer | 2019-05-06 through 2022-12-30 | First |
| Confirmation | 2023-01-03 through 2025-12-31 | Locked until quick pass |

The start date is the MNQ launch date.

## 6. Contract and cost assumptions

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

Results are reported on a one-contract basis. Profit Factor is the
primary scale-independent comparison. Capital percentage return
is not a pass/fail gate because whole-contract notional exposure
changes with the index level and account size.

Cost sensitivity at zero, one and two ticks of slippage per side
must be reported. The one-tick case is the decision model.

## 7. Session-aware MCPT

EXP-005 uses the same economic randomization principle as EXP-004,
but begins with one-minute futures bars:

- Relative OHLC components are permuted across complete sessions
  inside each one-minute time slot.
- Session-opening gaps are permuted separately.
- Synthetic one-minute sessions are reconstructed.
- Synthetic data is then aggregated to five-minute bars.
- Time-of-day distributions and session boundaries are preserved.
- There is no parameter optimization on real or permuted data.
- Numbered deterministic seeds are required.
- Serial and multicore results must match exactly.

```text
Random seed: 45
Quick MCPT: 25 NQ permutations
Full MCPT: 1,000 NQ permutations
```

## 8. Quick-transfer gates

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
| Included intraday roll-switch sessions | 0 |

A failure rejects EXP-005 without exposing 2023–2025.

A complete pass permits one protected confirmation run.

## 9. Full-validation gates

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
| Included intraday roll-switch sessions | 0 |

A pass advances to review rather than directly to paper testing.

## 10. Interpretation limits

- A rejection applies only to the unchanged basic ORB.
- It does not reject more structured ORB variants.
- A pass would support transfer of this exact rule set only.
- NQ and MNQ are not counted as two independent confirmations.
- No result may be used to change EXP-005 after disclosure.

Structured ORB research is documented separately in:

```text
research/ORB_structured_variant_roadmap.md
```
