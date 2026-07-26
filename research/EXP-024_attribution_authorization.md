# EXP-024 Attribution Authorization

**Authorized date:** 2026-07-26

**Preregistration commit:** `37a6d007b103bb5baddfdbbe471a8b6626b8a35c`

**Implementation commit:** `34f7d4c83dee025108229d5247e9cb4f87398a59`

## Authorized action

The user's instruction to "proceed", immediately after the explicit handoff
that the next gate was the separate one-time EXP-024 authorization and
protected attribution run, authorizes:

1. the authorized result-free repository preflight;
2. exactly one local attribution of the 51 frozen primary EXP-023
   candidate-session decision mismatches;
3. Quantower one-minute reconstruction and comparison with its frozen
   five-minute bars inside the permitted windows;
4. the backward-adjusted EXP-022 representation as primary and the
   unadjusted representation as secondary adjustment sensitivity;
5. the internal independent rebuild, 26 hard checks, atomic evidence outputs,
   four charts, and the locked interpretation report.

## Permitted value access

Only the 51 frozen mismatch sessions may be inspected. Gap-fade rows may also
use their immediately prior frozen reference cash session.

- Current premarket: 08:00:00 through 09:29:59 New York OHLC
- Current first cash bar: 09:30:00 through 09:34:59 New York OHLC
- Current entry: the 09:35:00 open only
- Required previous gap session: 09:30:00 through 15:59:59 New York OHLC

Arrow row predicates and column projections must precede materialization.
Volume is not authorized.

## Restrictions

- Maximum attribution runs: 1
- Any non-mismatch session except the required prior gap sessions: Not
  authorized
- Current-session values after the 09:35 open: Not authorized
- Pre-2020 or 2026 market values: Not authorized
- Databento API calls: 0
- Network access or new market-data download: Not authorized
- Frozen EXP-022, EXP-023, Quantower, or session-quality modification: Not
  authorized
- Strategy replay, stop, target, exit, P&L, return, equity, drawdown, or
  performance measurement: Not authorized
- Strategy search, optimization, MCPT, bootstrap, or walk-forward: Not
  authorized
- Candidate ranking or source-winner selection: Not authorized
- Protected-history validation: Not authorized
- Paper or live trading: Not authorized

All 51 mismatch rows and all three candidates must remain separate and
visible. Roll proximity and warning context are descriptive only and cannot
be used as automatic causal attribution. A completed run may not be rerun.
