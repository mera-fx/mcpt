# EXP-005 Full-Validation Implementation

**Record:** EXP-005-I3  
**Implemented:** 14 July 2026  
**Status:** Implemented before full-validation results

## Purpose

Execute the preregistered 2023–2025 confirmation test for the unchanged NQ/MNQ 15-minute opening-range breakout after the quick transfer passed and the protected confirmation import was completed.

## Frozen data

The implementation accepts only the completed confirmation import produced under commit `53a740aedb63e2a7508e3e010f5370be49cf816a`:

- 733 aligned full sessions
- 285,870 one-minute rows per symbol
- 57,174 five-minute rows per symbol
- zero invalid sessions included
- zero front-month mismatch sessions included

Every processed-data fingerprint is rechecked before the strategy can run.

## Strategy and costs

The rule set is unchanged:

- 15-minute opening range
- both long and short breakouts
- completed-bar close outside the range
- entry at the next five-minute open
- final signal bar at 11:55 New York time
- final entry at 12:00 New York time
- protective stop at the opposite opening-range boundary
- entry bar may hit the stop
- maximum one trade per session
- forced flat at the 15:55 bar open
- no overnight position

The decision model uses one tick of slippage per side and the locked round-trip costs of $15 for NQ and $3 for MNQ. Zero-, one-, and two-tick slippage cases are reported without changing the decision model.

## Statistical test

NQ remains the primary evidence market. The protected full MCPT uses:

- the frozen NQ one-minute confirmation data
- exactly 1,000 session-aware permutations
- base seed 45
- no optimization inside any permutation
- the existing time-of-day-stratified reconstruction engine
- deterministic multicore execution
- checkpoint and resume support
- p-value `(1 + permutations at least as good as real) / 1001`

MNQ remains a contract-size and cost implementation check rather than independent evidence.

## Mandatory gates

All gates must pass:

- NQ trade Profit Factor greater than 1.05
- MNQ trade Profit Factor greater than 1.00
- NQ net profit greater than $0
- MNQ net profit greater than $0
- NQ MCPT p-value no greater than 0.05
- at least 500 completed NQ trades
- at least two profitable NQ calendar years
- zero invalid sessions included
- zero roll-switch or front-month mismatch sessions included

A pass advances only to `REVIEW`. A failure produces `REJECT`. The runner does not edit lifecycle source files automatically.

## Safety

The runner:

- requires a clean Git working tree;
- verifies the frozen quick-transfer result;
- verifies the confirmation import and every data fingerprint;
- refuses to overwrite an existing full-validation decision;
- never reruns the quick transfer;
- writes the immutable decision marker only after all calculations and report outputs succeed.

An interrupted 1,000-permutation run may be started again because it resumes from the compatible checkpoint. A completed decision may not be rerun.
