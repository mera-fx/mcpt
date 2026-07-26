# EXP-023 Protected Transfer Implementation

**Locked preregistration commit:** `66ba6a46f31cc8715447179c19caf2f4c1a1e8be`

**Status:** `IMPLEMENTED_NOT_AUTHORIZED_NOT_RUN`

## Scope

This implementation replays exactly the three frozen EXP-014 finalists on the
two frozen EXP-022 representations during only the already-known 2020-01-03
through 2025-12-31 overlap:

1. `gap_fade_0p50_1r`
2. `premarket_continuation_0p50_time`
3. `premarket_continuation_0p75_time`

The backward-adjusted series is the primary transfer series. The unadjusted
series is a secondary roll-sensitivity diagnostic. It is not a competing
strategy and cannot replace the primary series after results are viewed.

## Protected read boundary

`exp023_transfer.py` attaches both UTC timestamp and trading-date predicates to
the PyArrow dataset scanner before any Arrow table is converted to pandas.
Python therefore receives OHLCV rows only inside the locked overlap. The
runner rejects any returned timestamp or trading date outside that boundary.

The implementation does not use an unrestricted `read_parquet` call. It does
not access, calculate, summarize or report strategy values from:

- 2010-06-06 through 2019-12-31; or
- 2026-01-01 through 2026-07-23.

Those periods remain untouched evidence for separately preregistered future
work.

## Missing-bar and session rules

The runner never fills a minute and never creates a synthetic bar. Five-minute
bars aggregate only observed source minutes. A five-minute bin exists only
when at least one source observation exists.

Every candidate requires:

- all 78 observed cash-session five-minute bins;
- the exact 09:35 entry minute;
- the exact 15:55 forced-flat minute.

The premarket candidates additionally require all 18 observed 08:00-09:30
premarket bins. The gap-fade candidate additionally requires the immediately
preceding frozen reference session and all 78 of its observed cash bins.
Ineligible sessions are logged and remain in the 1,331-session denominator.

## Frozen execution

The implementation preserves:

- fixed one-contract NQ sizing;
- the 09:35 five-minute-bar-open entry;
- the first cash bar's opposite extreme as stop;
- a 1R target for `gap_fade_0p50_1r`;
- a 15:55 time exit for both premarket candidates;
- chronological one-minute exit evaluation;
- entry-minute exit eligibility;
- gap-through-stop handling;
- stop-first treatment when stop and target touch in one minute;
- $2.50 fees per side plus one tick of slippage per side, represented by the
  frozen $15 round-trip cost.

No candidate, parameter, cost or execution choice can be added, removed or
changed by the runner.

## Qualification and interpretation

The seven preregistered transfer gates are evaluated separately for each
primary candidate. Profitability is measured but is not a qualification gate.
No candidate is ranked, selected or rejected as a trading system.

The roll-distance bands are locked before execution as:

- `0`: the roll session;
- `1`: one reference session away;
- `2-3`: two or three reference sessions away;
- `OTHER`: every larger distance.

Even the qualified classification means only that a separately preregistered
fixed-rule history validation may be considered. It does not validate edge,
unlock the protected dates, or authorize paper or live trading.

## Protection and authorization

The implementation:

- requires a separate authorization commit locked to the implementation SHA;
- requires clean and synchronized `main`;
- refuses if any EXP-023 final or partial output directory exists;
- refuses while `DATABENTO_API_KEY` is present;
- makes zero Databento API calls and contains no network client;
- verifies the frozen EXP-022 closure, both series byte hashes, the locked
  semantic hashes recorded by that byte-identical closure, all three canonical
  EXP-014 ledger hashes and the session-quality hash;
- snapshots every frozen input before and after the run;
- rebuilds the complete diagnostic independently and compares canonical frame
  hashes;
- permits one authorized run and prohibits rerunning after completion.

This implementation commit does not itself authorize preflight or execution.

## Outputs

The authorized run will write only under
`results/EXP-023/transfer_qualification/`:

- `transfer_summary.json`
- `candidate_transfer_metrics.csv`
- `session_alignment.csv`
- `trade_alignment.csv`
- `transfer_trade_ledger.csv`
- `representation_sensitivity.csv`
- `ineligible_sessions.csv`
- `period_comparison.csv`
- `roll_proximity_differences.csv`
- `output_hashes.json`
- `report.md`
- `report.html`
- seven opaque-white visual evidence charts under `assets/`
- `TRANSFER_DIAGNOSTIC_COMPLETE.json`

The HTML report is a vertical single-column report. All three finalists and
all adverse outcomes remain visible. Green is reserved for status words;
positive numbers use neutral text and failed conditions use red.

## Hard checks

All 20 preregistered hard checks are represented explicitly. A hard-check
failure produces `TRANSFER_DIAGNOSTIC_NOT_QUALIFIED`. A complete diagnostic
that misses one or more transfer thresholds produces
`TRANSFER_DIAGNOSTIC_COMPLETE_WITH_MATERIAL_DIFFERENCES`.

No strategy result was calculated while creating or testing this
implementation.
