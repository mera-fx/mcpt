# EXP-008 Protected Implementation

## Structured Long-Only ORB Exit-Geometry Optimization

**Implementation status:** `IMPLEMENTED_NOT_RUN`

This implementation follows the frozen EXP-008 preregistration. It does not
contain a strategy result and must be committed with a clean Git working tree
before the protected optimization may run.

## Locked candidate surface

| Parameter | Values |
|---|---|
| Opening range | 15, 30, 45 minutes |
| Profit target | 0.5R, 1.0R, 1.5R |
| Forced flat | 12:00, 14:00, 15:55 New York |
| Direction | Long only |
| Position size | One fixed contract |
| Combinations | 27 |

The frozen EXP-007 geometry, `30 minutes / 1.0R / 14:00`, appears exactly
once and is tested against the EXP-007 engine for exact implementation parity.

## Execution engine

Signals use complete five-minute bars and execution uses the underlying
one-minute data. A candidate enters at the next five-minute opening price
after the first complete close strictly above its opening-range high.

The protective stop is the candidate opening-range low. The target is the
entry plus the candidate R multiple of actual entry risk. A stop gap fills at
the one-minute open; a target gap receives no favourable price improvement.
When both stop and target are present inside the same minute, the stop is
assumed first. A trade can exit in its entry minute. There is no reentry and
no short trade.

## Grid scoring and selection

All 27 NQ candidates are evaluated using the base one-tick-per-side slippage
model. Eligibility and immediate-neighbour stability are calculated exactly
as preregistered. Eligible stable candidates are ranked by Profit Factor,
net-profit-to-drawdown ratio, net profit, completed trades and parameter key.

A no-eligible-candidate outcome is handled as a formal negative result rather
than a software error. Its locked selection statistic is 0.0, and the
walk-forward and selection-aware MCPT procedures still complete.

## Temporal diagnostics

Five anchored annual folds repeat the entire selection process using training
data only, then evaluate the selected training candidate in the next calendar
year. A fold with no stable eligible training candidate records a zero-trade,
zero-profit failed test fold.

The final full-sample selected candidate is also reported by calendar year for
2021 through 2025.

## Selection-aware MCPT

The protected NQ MCPT uses 1,000 session-aware permutations and seed 48. Every
permutation reconstructs a one-minute market, runs all 27 candidates, applies
the complete eligibility and neighbour procedure, and records the selected
candidate Profit Factor. Serial and parallel results are tested for exact
parity. Checkpoint and resume support is included.

## Additional checks

For a selected candidate, the implementation calculates:

- NQ primary results and MNQ implementation consistency results
- Zero-, one- and two-tick-per-side cost sensitivity
- Five final-candidate annual blocks
- 10,000 completed-trade bootstrap resamples using seed 4801
- Total-equity and drawdown curves
- A direct frozen EXP-007 baseline comparison

## Saved outputs

The protected run writes to:

`results/EXP-008/exit_geometry/`

The final decision file is:

`results/EXP-008/exit_geometry/optimization_decision.json`

The selection-aware checkpoint is:

`results/EXP-008/exit_geometry/mcpt_checkpoint.json`

The vertical report is:

`reports/EXP-008-research-lab/report.html`

The report uses a single top-to-bottom flow with full-width metric tables,
equity and drawdown curves, the complete 27-candidate grid, parameter-surface
charts, neighbour evidence, anchored folds, annual performance, cost
sensitivity, MCPT evidence and the EXP-007 comparison.

## Protections

The runner verifies the frozen EXP-005, EXP-006 and EXP-007 records, the
EXP-008 preregistration, the implementation record, the 1,639-session frozen
data lock and a clean committed Git state. It refuses to rerun after the
EXP-008 decision file exists.

No historical EXP-008 outcome authorizes live trading. A passing outcome can
only lock one geometry for comparison on genuinely new forward paper data.
