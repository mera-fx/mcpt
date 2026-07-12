# EXP-003 Corrected Review Decision

**Lifecycle decision:** ACCEPTED_FOR_PAPER_TESTING  
**Corrected review:** v2  
**Research rerun:** No

## Audit history

The original read-only review returned `REJECT` because it searched
for obsolete parameter-stability field names and defaulted broad
parameter support to zero.

The saved research schema actually recorded:

```text
break_even_count = 27
total_combinations = 27
```

The original review output remains preserved under
`results/EXP-003/review/`.

The corrected review v2 read the existing saved results only. No
MCPT, optimization, walk-forward test or out-of-sample backtest was
rerun.

## Corrected review result

Every review check passed:

- Full validation decision: `PASS_TO_REVIEW`
- Fixed OOS return: `+31.1074%`
- Walk-forward return: `+37.3675%`
- Fixed trade Profit Factor: `1.1665`
- Walk-forward trade Profit Factor: `1.3171`
- Fixed completed trades: `128`
- Walk-forward completed trades: `81`
- Fixed payoff ratio: `2.3686`
- Walk-forward payoff ratio: `2.3682`
- Largest loss: `-8.2767%`
- Broad parameter support: `27/27`
- Profitable OOS calendar years: `3`
- Drawdown improvement versus Buy and Hold: `39.3051` percentage points

## Decision

EXP-003 is accepted for **paper testing**, not live trading.

The research result is frozen. Strategy rules and parameters cannot
be altered under EXP-003. Any changed hypothesis requires a new
experiment ID and a new preregistration.
