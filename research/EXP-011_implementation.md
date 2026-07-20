# EXP-011 protected implementation

## Status

`IMPLEMENTED_NOT_RUN`

This implementation contains no EXP-011 result. The implementation must be
committed with a clean working tree before its protected preflight or one-time
measurement run is allowed.

## Reused signal and execution

EXP-011 reuses the exact `opening_drive_0p5_time` and
`opening_drive_0p5_1p5r` signal and one-minute execution records from the
EXP-009/EXP-010 engine. It does not alter entry, stop, target, forced-flat,
transaction-cost, slippage, or same-minute stop-first rules.

## Calibration

The target dollar risk is calculated once as the median valid one-NQ initial
risk of the primary time-exit signal from 2019-05-06 through 2020-12-31.
Initial risk is actual entry-to-stop points times the NQ point value plus the
locked one-contract round-trip cost. No evaluation-period trade can affect the
target.

## Evaluation

Only 2021-01-04 through 2025-12-31 contributes to the six measurement rows:

1. Primary signal with fixed one NQ.
2. Primary signal with theoretical fractional equal-risk NQ.
3. Primary signal with implementable whole-contract equal-risk MNQ.
4. User-reference signal with fixed one NQ.
5. User-reference signal with theoretical fractional equal-risk NQ.
6. User-reference signal with implementable whole-contract equal-risk MNQ.

Fractional NQ is capped at 2.0 contracts. Integer MNQ is floored, permits zero,
and is capped at 20 contracts. Zero-contract signals are retained with their
skip reason. Costs scale linearly with contract quantity. The dollar target is
constant and profits are not compounded.

## Diagnostics and reporting

The implementation records performance, drawdown, initial-risk dispersion,
contract distribution, skipped trades, annual and monthly behaviour, costs,
and practical holding measurements. Four paired session bootstraps use 10,000
resamples and seed 5111. Both the fixed NQ position and the complete dynamically
sized MNQ position are already recorded in actual US dollars. The MNQ result
therefore receives no additional ten-times conversion; doing so would
double-count the contract multiplier after contract quantity has already been
applied.

The report includes a plain-English strategy explanation, a worked sizing
example, all six rows, equity versus a normalized NQ price benchmark,
drawdowns, risk distributions, contracts, annual and monthly charts, and
paired bootstrap intervals.

EXP-011 has no automatic sizing winner, composite score, pass/fail gate, new
MCPT, signal-edge claim, independent-confirmation claim, or paper/live-trading
authorization.
