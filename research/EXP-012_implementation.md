# EXP-012 protected implementation

Status: `IMPLEMENTED_NOT_RUN`

This implementation realizes the locked EXP-012 preregistration without
calculating a strategy result.

## Implemented

- Frozen 2020-2025 complete aligned extended-session loader
- Exact overnight, premarket, prior-cash and opening-gap features
- Six strategy families and all 24 locked candidates
- Cash-session-only entries
- Completed five-minute signals and next-open entries
- Existing one-minute conservative execution and cost engine
- Fixed one-contract NQ and MNQ measurements
- Zero-, one- and two-tick NQ cost sensitivity
- Candidate, family, context, distribution and Pareto measurements
- Plain-English full-width report
- Normalized NQ benchmark and drawdown/consistency visuals
- Solid opaque white chart canvases
- Staging directories and one-time result protection
- Explicit `--preflight` or `--run` mode

## Reused execution logic

EXP-012 reuses the tested EXP-009 one-minute execution engine for stops,
targets, gap-through-stop fills, costs and the 15:55 forced exit. The new
engine constructs only the extended-hours context and cash-session signals.
This prevents a new experiment from silently using a different fill model.

## Still prohibited

- Calculating results before the implementation is committed and clean
- Editing or rebuilding the frozen extended-session dataset
- Entering positions outside the cash session
- Claiming that cash-session costs describe overnight execution
- Adding or removing candidates
- Selecting an automatic winner
- Running MCPT, bootstrap, walk-forward or family optimization
- Calling a discovery measurement a confirmed edge
- Authorizing paper or live trading
