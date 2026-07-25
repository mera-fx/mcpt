# EXP-020 Constructor Implementation

**Implementation date:** 2026-07-25

**Locked preregistration commit:**  
`93776c52806820e137ec02f7fe6382d8981c4500`

**Implementation status:** `READY_FOR_SEPARATE_AUTHORIZATION`

**Construction status:** `NOT_RUN`

## Added implementation

`exp020_constructor.py` and `exp020_constructor_core.py` implement the
preregistered local-only construction pipeline:

- verify all frozen EXP-019 acquisition and audit hashes;
- require a clean and synchronised `main` branch;
- refuse to run while `DATABENTO_API_KEY` is present;
- require a separately committed EXP-020 construction authorization;
- read the 66 exact-contract DBN files locally;
- apply the locked New York 18:00 trading-date boundary;
- build the two-session volume-crossover primary method;
- apply the fixed-calendar benchmark and fallback;
- treat all 16 provider-warning contract windows conservatively by excluding
  their entire overlap from volume-trigger evaluation;
- construct unadjusted and backward-difference-adjusted outputs;
- validate the 20 preregistered hard checks;
- perform a second independent local rebuild;
- compare deterministic semantic and byte hashes;
- preserve partial output after an error for diagnosis;
- refuse to overwrite or rerun completed EXP-020 output.

## Required later step

This implementation does not authorize construction.

After the implementation is tested, committed and pushed, a separate
authorization record must lock that implementation commit. Only then may the
read-only preflight be run.

## Explicit exclusions

This implementation makes no Databento API request and does not run:

- strategy replay;
- optimisation;
- MCPT;
- bootstrap analysis;
- walk-forward analysis;
- paper trading;
- live trading.

A completed dataset would still require separately preregistered strategy
research.
