# EXP-012 preregistration

## NQ/MNQ Extended-Hours Context Discovery

Locked: 2026-07-20  
Status: `PRE_REGISTERED`  
Implementation: `NOT_RUN`  
Results viewed: `NONE`

## Purpose

EXP-012 measures whether information formed outside the regular cash
session helps describe attractive cash-session trading ideas. It is a
measurement-first discovery tournament, not a pass/fail validation and
not a trading authorization.

The cash outcomes for 2020-2025 have appeared in earlier experiments,
but the new overnight, premarket and gap features have not been used in
a strategy test. The result will therefore remain exploratory rather
than independent confirmation.

## Why entries remain in the cash session

The frozen dataset now contains complete extended-session bars, but the
existing commission and slippage model was developed for cash-session
execution. EXP-012 uses overnight and premarket prices as information
while entering and exiting during the cash session. This avoids making
an unsupported claim that the same fill model describes thin overnight
liquidity.

## Frozen data

- Primary market: NQ
- Secondary implementation comparison: MNQ
- Period: 2020-01-02 through 2025-12-31
- Complete aligned NQ/MNQ sessions: 1,331
- Context source: one-minute extended-session data
- Signal bars: completed five-minute bars
- Execution resolution: one minute
- Research timezone: America/New_York
- Full available session: 18:00 prior trade date through 16:59
- Overnight context: 18:00 through 09:29
- Premarket context: 08:00 through 09:29
- Cash session: 09:30 through 15:59

The 13 aligned 2019 sessions are excluded because they provide limited
partial-year coverage. Only complete aligned NQ/MNQ sessions are used.
No missing bar may be filled or synthesized, and the frozen data may
not be edited or rebuilt under EXP-012.

## Common execution and risk rules

- Cash-session entries only
- Completed five-minute signals only
- Entry at the next five-minute bar's actual open
- One-minute chronological stop/target evaluation
- Conservative stop-first treatment when both levels occur in one minute
- Stop gaps filled at the adverse one-minute opening price
- No favourable target improvement
- Forced flat at the 15:55 one-minute open
- Maximum one completed trade per candidate per session
- No same-day re-entry
- No overnight position
- No entry when actual risk is zero or negative
- Fixed one NQ contract and fixed one MNQ contract

Base costs remain the existing common model:

- NQ: $15 base round trip, including one tick per side
- MNQ: $3 base round trip, including one tick per side
- NQ cost sensitivity: zero, one and two ticks per side

## Context features

### Gap fraction

The absolute distance from the current 09:30 open to the immediately
preceding exchange trade date's cash close, divided by that prior
session's cash high-low range. If the immediately preceding exchange
trade date is not a complete aligned session, the gap families skip the
current date.

### Overnight drive fraction

The absolute change from the 18:00 open to the 09:29 close divided by
the complete 18:00-through-09:29 high-low range.

### Premarket drive fraction

The absolute change from the 08:00 open to the 09:29 close divided by
the 08:00-through-09:29 high-low range.

A zero directional change or nonpositive range is ineligible. A feature
qualifies when its fraction is greater than or equal to the locked
candidate threshold.

## Six strategy families

### 1. Gap continuation

A meaningful opening gap may continue when the first five-minute cash
bar also moves in the gap direction. The strategy enters at 09:35,
uses the opposite extreme of the first cash bar as its stop, and either
holds to the time exit or uses a 1.5R target.

### 2. Gap fade

A meaningful opening gap may reverse when the first five-minute cash
bar moves back toward the previous cash close. The strategy enters at
09:35, stops beyond the outer extreme of that bar, and targets either
the previous cash close or 1R.

### 3. Overnight momentum continuation

A strong directional overnight move may continue after the cash open
when the first cash bar agrees with the overnight direction. Entry is
at 09:35, with the first cash bar's opposite extreme as the stop.

### 4. Overnight inventory reversal

A strong overnight move may represent inventory that unwinds after the
cash open. The first cash bar must move opposite the overnight
direction. The exit targets either the 18:00 overnight open or 1R.

### 5. Overnight range breakout

The overnight high and low form a frozen range. The first completed
cash-session five-minute close beyond that range creates a signal,
provided it occurs before the candidate's 10:30 or 12:00 deadline.
The signal bar's opposite extreme is the stop; the target is 1R or 1.5R.

### 6. Premarket momentum continuation

A strong directional move during the final 90 minutes before the cash
open may continue when the first cash bar agrees. Entry is at 09:35,
with the first cash bar's opposite extreme as the stop.

## Candidate budget

Each family has four locked candidates, for 24 total:

- Gap continuation: gap fractions 0.25 and 0.50, each with time or 1.5R exit
- Gap fade: gap fractions 0.25 and 0.50, each with prior-close or 1R exit
- Overnight continuation: drive fractions 0.50 and 0.75, each with time or 1.5R exit
- Overnight reversal: drive fractions 0.50 and 0.75, each with overnight-open or 1R exit
- Overnight range breakout: signal deadlines 10:30 and 12:00, each with 1R or 1.5R
- Premarket continuation: drive fractions 0.50 and 0.75, each with time or 1.5R exit

No candidate may be added, removed or changed after a result is viewed.

## Measurement standard

Every candidate remains visible. Reports must explain each strategy in
plain English and show:

- Net profit, Profit Factor, win rate, average and median trade
- Average winner, average loser and payoff ratio
- Drawdown depth, duration and recovery
- Net profit relative to drawdown
- Annual, monthly and rolling performance
- Trade frequency, holding time, entry time and exit reasons
- Profit concentration and complete trade distribution
- NQ/MNQ comparison
- Zero-, one- and two-tick NQ cost sensitivity
- Normalized NQ price benchmark
- Feature eligibility, signal confirmation and context distributions
- Family summaries and Pareto comparisons

Charts use a solid opaque white canvas. Positive numbers remain neutral,
adverse values use red text, and green is reserved for status words.

## Interpretation boundary

EXP-012 has:

- no formal accept/reject gates
- no automatic winner
- no single composite score
- no MCPT
- no bootstrap
- no walk-forward test
- no family optimization

The user may retain up to three personally attractive finalists after
reviewing all measurements. Each finalist requires a new preregistered
deep-validation experiment. EXP-012 cannot confirm an edge and cannot
authorize paper or live trading.
