# EXP-003 Quick-Screen Decision

## Official decision: PASS TO FULL VALIDATION

**Research stage after this decision:** `FULL_VALIDATION`  
**Strategy implementation commit:** `0e4e67a`  
**Out-of-sample results viewed during quick screen:** No

The one-time locked quick screen used only the preregistered
2018–2021 in-sample period. Its decision file was written after all
other quick-screen outputs.

| Gate | Actual | Requirement | Result |
|---|---:|---:|---|
| Best in-sample bar Profit Factor | 1.114966 | Strictly above 1.00 | PASS |
| Parameter combinations with PF ≥ 1.00 | 27 of 27 | At least 6 | PASS |
| Immediate-neighbour median / best | 0.991716 | At least 0.95 | PASS |
| 25-permutation MCPT p-value | 0.076923 | At most 0.20 | PASS |
| Fixed-parameter completed trades | 105 | At least 50 | PASS |

## Interpretation

The result passes every preregistered screening gate. The parameter
surface is broad: every locked parameter combination reached an
in-sample bar Profit Factor of at least 1.00, and the immediate
neighbours retained about 99.17% of the best score.

This is permission to reveal the locked out-of-sample period once.
It is not evidence that the strategy has passed full validation.
The 25-permutation p-value is a screening statistic and must be
replaced by the preregistered 1,000-permutation test.

## Locked next action

Run the protected full-validation workflow exactly once. It must use:

- The existing strategy implementation and parameter grid
- The fixed 2022–2025 out-of-sample period
- The existing transaction-cost assumptions
- The fixed-parameter and walk-forward tests
- The 1,000-permutation MCPT
- Every preregistered full-validation gate

No strategy, parameter, cost, date or pass/fail rule may be changed
before or after the full-validation result.
