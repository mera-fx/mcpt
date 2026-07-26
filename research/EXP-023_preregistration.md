# EXP-023 Preregistration

**Locked date:** 2026-07-26

**Status:** `PRE_REGISTERED`

**Implementation:** `NOT_IMPLEMENTED`

**Execution:** `NOT_RUN`

## Title

NQ Frozen-Finalist Continuous-Series Transfer Qualification

## Why this experiment comes next

EXP-022 qualified two representations of the selected
`VOL_GT_OUT_2S_E3` NQ continuous series. It did not test a strategy.

Before the new series is used on previously unexamined dates, EXP-023 will
measure whether three unchanged EXP-014 finalists transfer faithfully during
the already-known 2020-2025 overlap:

1. `gap_fade_0p50_1r`
2. `premarket_continuation_0p50_time`
3. `premarket_continuation_0p75_time`

This is a cross-source and data-treatment diagnostic. The reference strategy
results are already known, so EXP-023 cannot be independent confirmation or
new evidence of edge.

## Frozen evidence

| Item | Locked value |
|---|---|
| EXP-022 closure commit | `9d157c8e7a6ba584a96cb5d37086672ad5b64ea1` |
| EXP-022 closure record | `1cc01baddeeae3acf81b0785923b581fad6aac0b6e36071d07d0d83d35bf588d` |
| Selected roll method | `VOL_GT_OUT_2S_E3` |
| Rows per representation | 5,457,606 |
| EXP-014 freeze commit | `5ac5e8ebe2dd251f394d8cdac8d4bad654a2fd0c` |
| Frozen reference sessions | 1,331 |
| Comparison period | 2020-01-03 through 2025-12-31 |
| Databento API calls | 0 |

The EXP-022 Parquet files, EXP-014 ledgers and frozen session-quality record
remain read-only.

## Representation roles

The backward-adjusted series is selected in advance as the primary transfer
series because the gap-fade rule compares prices across adjacent cash
sessions. The unadjusted series is a secondary roll-sensitivity diagnostic.

They are two representations of one roll schedule, not two independent
markets or competing strategies.

## Strategy and execution lock

All three strategies retain their exact EXP-013 and EXP-014 rules:

- signals use completed five-minute bars;
- entries occur at the 09:35 New York bar open;
- stops and targets are unchanged;
- positions are forced flat at the 15:55 one-minute bar open;
- same-minute stop and target contact remains stop-first;
- exposure is one NQ contract;
- fees are $2.50 per side;
- slippage is one tick per side;
- total round-trip cost is $15;
- no overnight position or same-session re-entry is allowed.

No candidate, parameter, cost, execution rule or roll rule may be changed.

## Protected data window

EXP-023 may deserialize OHLCV values only for session dates from 2020-01-03
through 2025-12-31.

The following EXP-022 periods remain protected from strategy calculation:

- 2010-06-06 through 2019-12-31;
- 2026-01-01 through 2026-07-23.

Full-file cryptographic hash verification and Parquet metadata inspection
are permitted because they do not calculate strategy values. Market values
outside the locked overlap may not be loaded, summarized or replayed.

## Missing-minute and session rules

Databento omits minutes without trades. EXP-023 will not fill or synthesize
them.

Five-minute bars use observed one-minute records only and require at least one
observation. Every candidate requires all 78 cash five-minute bins, the exact
09:35 entry minute and the exact 15:55 forced-flat minute. Premarket
continuation also requires all 18 final-premarket bins. Gap fade also requires
all prior-cash five-minute bins from the immediately preceding frozen
reference session.

Every one of the 1,331 reference sessions must be classified as eligible or
excluded with an explicit reason. Ineligible sessions are logged, not
repaired.

## Locked comparisons

For every candidate, EXP-023 will compare:

- session eligibility;
- trade/no-trade decisions and direction;
- entry and exit timestamps;
- exit reason;
- gross and net trade P&L;
- Profit Factor, net profit and maximum drawdown;
- annual and monthly results;
- differences near and away from frozen roll boundaries.

Profitability is reported but is not a transfer gate. EXP-023 cannot rank the
strategies or select a winner.

## Qualification gates

Each primary backward-adjusted replay must pass all of these gates:

| Gate | Threshold |
|---|---:|
| Required-session eligibility | at least 99% |
| Trade-indicator and direction agreement | at least 99% |
| Relative trade-count difference | no more than 1% |
| Common-trade match share | at least 98% |
| Matching entry-time agreement | 100% |
| Common-trade gross-P&L correlation | at least 98% |
| Common-trade gross-P&L sign agreement | at least 95% |

The denominators and matching rules are fixed:

- eligibility is eligible primary sessions divided by 1,331;
- trade-decision agreement compares `(trade flag, direction)` on eligible
  primary sessions;
- relative trade-count difference uses the frozen reference count;
- common-trade match share is the intersection divided by the union of
  `(session date, direction)` trade keys;
- entry-time and P&L comparisons use those common trade keys;
- P&L correlation is Pearson correlation of gross NQ dollars;
- an insufficient or zero-variance correlation fails its gate.

Possible classifications are:

- `QUALIFIED_FOR_SEPARATE_FIXED_RULE_HISTORY_VALIDATION`
- `TRANSFER_DIAGNOSTIC_COMPLETE_WITH_MATERIAL_DIFFERENCES`
- `TRANSFER_DIAGNOSTIC_NOT_QUALIFIED`

Even the qualified classification does not permit access to protected dates.
A new experiment ID and preregistration are required first.

## Required outputs

- `transfer_summary.json`
- `candidate_transfer_metrics.csv`
- `session_alignment.csv`
- `trade_alignment.csv`
- `representation_sensitivity.csv`
- `ineligible_sessions.csv`
- `output_hashes.json`
- `report.md`
- `TRANSFER_DIAGNOSTIC_COMPLETE.json`
- a visual HTML report with coverage, agreement, P&L, roll-proximity and
  representation-sensitivity charts

## Execution boundary

EXP-023 requires:

1. this preregistration to be committed;
2. a separate protected implementation commit;
3. a separate one-time execution authorization;
4. a result-free preflight;
5. one authorized diagnostic run;
6. an independent rebuild and immutable closure.

The preregistration itself calculates no strategy result and reads no
out-of-overlap market value.

## Prohibited work

EXP-023 must not:

- rerun EXP-022 or modify any EXP-022 output;
- modify EXP-014 evidence;
- access or calculate strategy values outside 2020-2025;
- make a Databento request or download market data;
- add, remove, rank or alter a finalist;
- change costs, execution or the roll method;
- optimize parameters;
- run MCPT, bootstrap or walk-forward analysis;
- authorize paper or live trading.
