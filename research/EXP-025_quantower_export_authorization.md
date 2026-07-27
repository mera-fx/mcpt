# EXP-025 Quantower Export Authorization

**Authorized date:** 2026-07-27

**Preregistration commit:** `1d736705a41d0208e353fb17710c8a16cc937710`

**Corrected implementation commit:** `2011745145b9799a4a42b556d57780002d30e317`

**Export plan:** `research/EXP-025_quantower_export_plan.csv`

**Export plan SHA-256:** `d716978b28b98f01798760e8298bf7217585a9f5397da068d1893dd28781e6de`

## Authorized action

This record authorizes one manual Quantower History Exporter phase for the
43 frozen EXP-025 exact-contract sessions.

For each session, the plan authorizes exactly two one-minute export windows:

1. the immediately previous frozen cash session from 09:30 through 15:59
   New York time;
2. the current target session from 09:30 through the 09:35 one-minute bar
   New York time.

The two permitted window exports will later be normalized and combined into
one final evidence CSV per session. Exactly 43 final files are required.

## Locked identity

- Candidate: `gap_fade_0p50_1r`
- Frozen sessions: 43
- Unique exact contracts: 22
- Permitted Quantower window exports: 86
- Required final evidence files: 43
- Resolution: one minute
- Source: Lucid/Rithmic through Quantower History Exporter
- Continuous symbols: prohibited
- Contract reselection: prohibited

## Data boundary

Only the timestamps named in the committed export plan are authorized.
Current-session bars after 09:35 are prohibited. Out-of-population sessions,
overnight rows and any additional history are prohibited.

Missing bars must remain missing. Forward fill, backfill, repair and synthetic
bar construction are prohibited.

## Execution boundary

This authorization does not authorize:

- the EXP-025 diagnostic execution;
- strategy replay or exit simulation;
- P&L, return, equity, drawdown or performance calculation;
- Databento API calls or a new Databento download;
- Python network access;
- order API access;
- strategy search, optimization, MCPT, bootstrap or walk-forward;
- paper trading or live trading.

After this authorization is committed, the separate export preflight must pass
before any Quantower export directory is created.

The first permitted data action after preflight is one previous/current window
pair for the first plan row, used only to verify Quantower's CSV structure.
No diagnostic comparison or strategy interpretation is authorized at that
format-verification stage.
