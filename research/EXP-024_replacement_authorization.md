# EXP-024 Replacement Authorization 002

**Authorized date:** 2026-07-26

**User instruction:** `authorize`

**Replacement implementation:** `fb5b8f02ac54cccf29c5d23452db6d8e9ac4589e`

**Superseded authorization:** `EXP-024-ATTRIBUTION-AUTH-001`

## Basis

Attempt 001 stopped before feature reconstruction or attribution because the
frozen Quantower Parquet restored its projected `timestamp` field as the
pandas index. No Databento values or outputs were produced. Authorization 001
is consumed and cannot be reused.

The replacement implementation preserves that failure and changes only the
post-Arrow conversion boundary: when the projected timestamp is the named
pandas index, it is reset to a regular column. A synthetic regression test
reproduces the exact Parquet metadata behavior.

## Authorized action

The user's explicit instruction to `authorize`, after reviewing the failed
attempt boundary and proposed correction, authorizes:

1. the result-free replacement-authorized repository preflight;
2. exactly one corrected local attribution of the same 51 frozen EXP-023
   mismatch rows;
3. the same permitted Quantower and Databento entry-decision windows;
4. the same primary and secondary representations;
5. the two internal deterministic rebuilds, 26 hard checks, atomic evidence,
   charts, and report.

## Unchanged permitted value windows

- Current premarket: 08:00:00 through 09:29:59 New York OHLC
- Current first cash bar: 09:30:00 through 09:34:59 New York OHLC
- Current entry: the 09:35:00 open only
- Required previous gap session: 09:30:00 through 15:59:59 New York OHLC

Arrow row predicates and projections must still precede pandas conversion.
Volume remains prohibited.

## Restrictions

- Maximum corrected replacement runs: 1
- Any further retry: Not authorized
- Modification of attempt-001 evidence: Not authorized
- Non-mismatch values except required prior gap sessions: Not authorized
- Current post-entry, pre-2020, or 2026 values: Not authorized
- Databento API or network access: Not authorized
- Frozen source or result modification: Not authorized
- Strategy replay, exits, P&L, returns, equity, drawdown, or performance:
  Not authorized
- Search, optimization, MCPT, bootstrap, or walk-forward: Not authorized
- Candidate ranking, source-winner selection, protected-history validation,
  paper trading, or live trading: Not authorized

All 51 rows and all three candidates must remain separate and visible. Roll
context remains descriptive rather than causal.
