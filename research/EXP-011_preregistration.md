# EXP-011 — Opening-Drive Position-Sizing Study

## Status

Locked on 2026-07-20 before any EXP-011 sizing result was calculated.

EXP-011 keeps the two visible EXP-010 signal variants unchanged:

- Primary measurement leader: `opening_drive_0p5_time`
- User reference: `opening_drive_0p5_1p5r`

The experiment changes position size only. It cannot be used to claim that
position sizing discovered or confirmed the opening-drive signal edge.

## Research question

Compared with fixed one-contract NQ exposure, how do theoretical fractional
NQ and practical integer MNQ equal-dollar-risk sizing change:

- Profit and Profit Factor
- Maximum drawdown and recovery
- Net profit relative to drawdown
- Initial-risk consistency
- Contract-count behaviour
- Costs and skipped trades
- Monthly and annual consistency

## Frozen signal rules

Both signal variants use:

- First-30-minute window: 09:30–10:00 New York
- Minimum drive fraction: 0.50
- Direction: sign of the first-30-minute close minus open
- Entry: 10:00 five-minute bar open
- Stop: opposite side of the first 30-minute opening range
- Maximum one trade per session
- Forced flat: 15:55 one-minute bar open

The primary variant has no target. The user reference exits at 1.5R when
reached before the stop or forced flat. No entry, filter, stop, target or
time parameter may be added or changed.

## Calibration and evaluation split

- Risk-target calibration: 2019-05-06 through 2020-12-31
- Sizing evaluation: 2021-01-04 through 2025-12-31

Calibration sessions cannot appear in evaluation measurements.

The target dollar risk is the median valid initial risk of one NQ contract
across the primary signal's calibration trades:

```text
initial risk =
    abs(actual entry - stop) × NQ point value
    + locked base round-trip cost
```

The target is calculated once and then frozen. Evaluation data cannot set or
change it. The target is not an optimized risk percentage.

## Locked sizing methods

### 1. Fixed one NQ

One NQ contract on every valid signal. This is the baseline, not an automatic
selection candidate.

### 2. Fractional NQ equal risk

```text
contracts = target dollar risk / current one-NQ initial risk
```

The result is capped at 2.0 NQ contracts. It is theoretical because futures
contracts cannot be traded fractionally.

### 3. Integer MNQ equal risk

```text
contracts = floor(target dollar risk / current one-MNQ initial risk)
```

The size may be zero and is capped at 20 MNQ contracts. A zero-sized setup is
skipped and recorded rather than silently forced to one contract.

Contract size is known at entry from the entry price, stop and frozen target.
Future prices cannot affect it. Sizing does not compound with historical
profits, and costs scale with contract count.

## Worked example

Suppose the frozen target risk is $1,500.

If one NQ contract would risk $2,000:

```text
fractional NQ size = 1,500 / 2,000 = 0.75 contracts
```

If one MNQ contract would risk $203:

```text
integer MNQ size = floor(1,500 / 203) = 7 contracts
```

The fraction is a contract quantity, not a 75% probability or a 75% market
move.

## Execution and costs

- Reuse EXP-010 one-minute chronological execution
- Stop first when stop and target touch in the same minute
- Base slippage: one tick per side
- NQ round-trip cost: $15 per contract
- MNQ round-trip cost: $3 per contract
- No new fill or data-cleaning assumptions

## Measurement and uncertainty

All six signal-by-sizing rows must remain visible. There is no automatic
winner, composite score or pass/fail gate.

The report will include equity, drawdown, initial-risk distributions,
contract-count distributions, skipped trades, costs, annual and monthly
results, and the existing normalized NQ benchmark.

A 10,000-resample paired session bootstrap (seed 5111) will describe
differences from fixed sizing. It is diagnostic only. No new MCPT is run
because EXP-011 does not introduce a new signal and cannot make a new
alpha-significance claim.

## Research limitations

The 2019–2025 history has already been viewed. EXP-011 is therefore an
exploratory sizing study, not independent confirmation. It authorizes neither
paper nor live trading.
