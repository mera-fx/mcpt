# EXP-009 protected implementation

Status: `IMPLEMENTED_NOT_RUN`

This implementation translates the 24 preregistered candidates into one
shared discovery engine. It has not been run against the frozen 2019–2025
NQ/MNQ history.

## What is implemented

- Six locked strategy families and four candidates per family.
- Completed five-minute signal bars with entry at the next five-minute open.
- Chronological one-minute stop, target and time-exit sequencing.
- Stop-first conservative treatment when both stop and target occur in the
  same one-minute bar.
- Gap-through-stop fills at the one-minute opening price.
- No favourable target price improvement.
- One trade per candidate per session and a 15:55 New York forced exit.
- Fixed one-contract NQ and MNQ measurements.
- NQ zero-, one- and two-tick slippage measurements.
- Full trade ledgers, equity curves, yearly results and rolling trade data.
- Performance, risk, consistency, cost, practical-behaviour and reliability
  measurements.
- Pareto context without an automatic score or winner.
- A vertical plain-English report containing all 24 candidates, one section
  per family, family comparisons, Pareto charts and normalized NQ benchmark
  context.

## Explicitly not implemented in EXP-009

- MCPT
- Bootstrap analysis
- Family optimization
- Automatic winner selection
- A composite strategy score
- Accept/reject gates
- Paper-trading authorization
- Live-trading authorization

Those steps are reserved for new preregistered finalist experiments after
the user reviews all 24 discovery measurements.

## Protected execution

The runner requires an explicit mode:

```powershell
.\.venv\Scripts\python.exe run_exp009_tournament.py --preflight
```

The real one-time discovery run later requires:

```powershell
.\.venv\Scripts\python.exe run_exp009_tournament.py --run
```

The preflight verifies the committed and clean Git state, frozen prior
decisions, lifecycle stages, the 1,639-session input and the absence of any
EXP-009 result. It calculates no candidate result.

The real run refuses to start if any discovery result already exists. It
writes the final manifest only after all 24 candidates have been measured.
