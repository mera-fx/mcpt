# EXP-021 One-Time Diagnostic Authorization

**Authorization date:** 2026-07-26

**Status:** `AUTHORIZED_FOR_ONE_TIME_DIAGNOSTIC`

## Locked boundaries

| Boundary | Locked value |
|---|---|
| Preregistration commit | `27a960ad68f2059e5ac9d60e42e41a9171fbda41` |
| Preregistration record SHA-256 | `00218e65ba5722bf0a4f1ba0571e6bea18d34022f32e3d7a689ae5e83d7c93e5` |
| Implementation commit | `9d365613619e21b9fe4eb9625bba907efd60ecfa` |
| Candidate methods | 8 |
| Transitions per candidate | 65 |
| Hard checks | 16 |
| Maximum diagnostic runs | 1 |
| Databento API calls | 0 |

## Authorised action

This record authorises:

1. the protected read-only EXP-021 preflight; and
2. one protected local EXP-021 diagnostic run after the preflight is reviewed.

The diagnostic may write only the preregistered EXP-021 diagnostic evidence.
It must retain all eight candidate results and perform the independent rebuild.

## Frozen inputs

- The EXP-019 exact-contract archive remains read-only.
- All EXP-020 outputs remain read-only.
- No Databento credential is required or permitted.
- No new market-data request is authorised.

## Explicit exclusions

This authorisation does not permit:

- rerunning EXP-019 or EXP-020;
- constructing a continuous series;
- changing the candidate matrix or gates;
- strategy replay or optimisation;
- MCPT, bootstrap or walk-forward testing;
- paper or live trading.

Any selected roll method requires a separately preregistered construction
experiment. Strategy research requires another separate experiment.

## Rerun boundary

After a completed diagnostic, EXP-021 may not be rerun. A failed attempt must
be reviewed before any further action; this authorisation does not permit an
automatic retry.
