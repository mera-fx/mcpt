# EXP-004 Implementation Record

**Experiment:** QQQ 5-Minute Opening Range Breakout  
**Preregistration status:** Locked before implementation  
**Lifecycle:** PRE_REGISTERED  
**Out-of-sample access:** Prohibited  
**Strategy results viewed:** None

## Implemented components

- Alpaca historical SIP downloader using API credentials from Windows
  environment variables
- Official Alpaca market-calendar retrieval
- Full-session filtering for 09:30–16:00 America/New_York
- Exclusion of scheduled early closes and incomplete sessions
- Exact 78-bar session validation
- Dedicated ORB trade simulator with:
  - 5, 15 and 30 minute opening ranges
  - long-only, short-only and both directions
  - confirmed close outside the range
  - next 5-minute open entry
  - opposite range-boundary protective exit
  - gap-through stop handling
  - same-entry-bar stop handling
  - forced flat at the 15:55 ET open
  - one trade per session
- Completed-trade optimization across the nine locked combinations
- Time-of-day-stratified session permutation MCPT
- Deterministic multicore processing and interruption checkpoints
- Protected in-sample-only quick-screen decision
- Responsive quick-screen HTML report

## Research safeguards

The downloader requests only the locked in-sample period:

```text
2019-01-02 through 2022-12-30
```

The quick-screen loader rejects any session after 2022-12-30.

The generic continuous-market research runner is blocked for EXP-004.
The only permitted current research command is:

```text
run_exp004_quick_screen.py
```

The quick-screen decision is written last and prevents a second
completed screen. An interrupted MCPT may resume before the decision
exists.

No OOS downloader or full-validation runner is included in this
implementation.
