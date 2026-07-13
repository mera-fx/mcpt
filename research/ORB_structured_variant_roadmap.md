# Structured ORB Research Roadmap

This roadmap records future hypotheses without changing EXP-004
or EXP-005. It is not a preregistration and contains no permission
to inspect data.

## Why separate experiments are required

EXP-004 tested a deliberately simple opening-range breakout and
failed its locked QQQ quick-screen gates. EXP-005 tests only
whether those exact rules transfer unchanged to NQ/MNQ.

A more structured ORB can still be investigated, but each logical
addition creates a new hypothesis and must receive a new
experiment ID before results are viewed.

## Proposed sequence

### ORB-A — Entry geometry

Test one family at a time:

- Close outside the range
- Minimum breakout buffer
- Breakout followed by a retest
- Consecutive closes outside the range

Keep context filters and exits fixed.

### ORB-B — Session context

Candidate families:

- Opening-range width relative to recent volatility
- Overnight gap size and direction
- Previous-session trend
- Relative opening volume
- Intraday volatility regime

Use only entry logic that survived its own earlier experiment.

### ORB-C — Risk and exits

Candidate families:

- Opposite range boundary
- Opening-range midpoint
- Volatility-scaled stop
- Fixed reward-to-risk target
- Time-based exit
- Trailing structure

Do not combine several exit families into one unrestricted search.

### ORB-D — Confirmatory combination

Combine only components that independently passed their locked
experiments. Preregister the small final grid, use a fresh data
split, run session-aware MCPT and retain untouched OOS data.

## Guardrails

- No giant all-variable grid
- No post-result gate changes
- No use of locked OOS data for feature selection
- No treating QQQ, NQ and MNQ as independent confirmations
- No rescuing a rejected experiment under the same ID
- Every material signal or exit change receives a new ID
