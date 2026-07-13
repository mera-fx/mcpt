# EXP-005 Protected Quick-Transfer Implementation

**Record:** EXP-005-I2  
**Implemented:** 2026-07-13  
**Status:** Implemented before strategy results  
**Confirmation period accessed:** No

## Purpose

Run the unchanged EXP-004 basic opening-range breakout once on the
frozen EXP-005 NQ/MNQ quick-period data.

## Fixed strategy

- 15-minute opening range: 09:30–09:44:59 ET.
- Both long and short breakouts.
- First completed five-minute close strictly outside the range.
- Entry at the next five-minute open.
- Final signal bar 11:55 ET; latest entry 12:00 ET.
- Long stop at the opening-range low.
- Short stop at the opening-range high.
- Gap-through stops fill at the bar open.
- The entry bar can trigger the stop.
- Maximum one trade per session.
- No same-day reversal.
- Forced exit at the 15:55 ET bar open.
- No overnight position.
- No optimization or parameter selection.

## Contract model

| Market | Multiplier | Decision round trip |
|---|---:|---:|
| NQ | $20 per point | $15 |
| MNQ | $2 per point | $3 |

The decision model uses one tick of slippage per side. A separate
report shows zero, one and two ticks per side.

## MCPT

- Primary market: NQ.
- Input: frozen one-minute cash-session bars.
- 25 quick-screen permutations.
- Seed: 45.
- Opening gaps are permuted separately from intraday gaps.
- Relative OHLC components are independently permuted across complete
  sessions within each one-minute time slot.
- Synthetic one-minute sessions are reconstructed and aggregated to
  five minutes before applying the fixed strategy.
- No optimization occurs in real or permuted markets.
- Serial and spawned-worker results are tested for exact equality.
- Checkpoint/resume is deterministic.

## Safety

The runner:

- verifies the frozen import and source-file hashes;
- requires a clean Git working tree;
- reads only the quick-period parquet files;
- refuses to overwrite an existing decision;
- does not alter lifecycle source files automatically;
- leaves 2023–2025 locked unless a later, separately committed closure
  records a passing quick-transfer decision.

This document contains no strategy result.
