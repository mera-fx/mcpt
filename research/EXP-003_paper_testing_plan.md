# EXP-003 Paper-Testing Plan

**Status:** ACCEPTED_FOR_PAPER_TESTING  
**Mode:** Paper only  
**Live orders:** Prohibited

## Purpose

Paper testing validates that live data handling, signal generation,
state transitions, simulated execution and accounting reproduce the
locked research implementation.

It is not a second optimization stage. Paper profitability will be
reported but is not, by itself, the operational pass/fail criterion.

## Locked strategy

```text
vol_lookback = 48
compression_quantile = 0.20
breakout_lookback = 48
compression_reference_window = 2,160 bars
compression_recency = 24 bars
exit_lookback = 24 bars
maximum_holding_period = 168 bars
direction = long only
execution = next hourly open
```

Costs remain:

```text
commission = 5 bps per side
slippage = 2 bps per side
starting paper capital = 100,000
```

## Minimum observation

Paper testing must continue until **both** conditions are met:

- At least 12 calendar weeks
- At least 20 completed trades

## Operational pass requirements

- Signals use completed hourly candles only
- Signal and position state match the replay engine exactly
- Entry and exit occur at the next recorded hourly open
- No duplicate simulated orders
- No pyramiding
- No unresolved reconciliation differences
- No trades when candles are stale, missing, duplicated or unordered
- Every signal, state change, fill, fee and P&L event has an audit log

## Safety rules

- Public market data only for the initial simulator
- No exchange trading API keys
- No live orders
- No leverage
- Stop processing on missing, duplicated or non-monotonic candles
- Do not modify parameters, entries, exits, stops or filters
- Do not rerun EXP-003 research to reinterpret paper results

A changed strategy must become a new preregistered experiment.
