# EXP-020 Preflight Digest Correction Authorization

**Authorization date:** 2026-07-26

**Authorization status:** `AUTHORIZED`

**Correction ID:** `EXP-020-PREFLIGHT-DIGEST-001`

**Construction status:** `NOT_RUN`

## Locked commits

| Boundary | Commit |
|---|---|
| Original one-time construction authorization | `e497b1abf247ed83295caa9378c2a4e6869922b1` |
| Corrected preflight implementation | `fde5ee88b306f97b9e567fabe1b12267c9db4ae8` |

## Authorised correction

This authorization accepts the corrected EXP-020 archive-digest
implementation and permits the protected read-only preflight to evaluate it.

The accepted digest protocol is:

```text
EXP-019_INSERTION_ORDER_JSON_V1
```

It reproduces the frozen EXP-019 archive digest:

```text
225a64dc06cb6bb303fd83d186f2e7d81e2a8a8bec44382380c8ccc1b0b6baa3
```

The incorrect sorted-key diagnostic digest was:

```text
8734b41f8bc5a3f3773f634323e6d52a4f2fffd6ef0d161863499c64d7110198
```

## Exact authorization scope

This authorization commit must add exactly:

- `exp020_preflight_correction_authorization.py`
- `tests/test_exp020_preflight_correction_authorization.py`
- `research/EXP-020_preflight_correction_authorization.md`

No constructor file may change in the authorization commit.

## Preserved construction boundary

The original one-time construction authorization remains in force and is not
expanded:

- maximum construction runs: 1;
- construction already run: No;
- completed-output overwrite: Prohibited;
- construction rerun: Prohibited;
- EXP-019 archive access: Read-only;
- Databento API calls: 0;
- credentials required: No.

The correction authorization permits review of the protected read-only
preflight. It does not itself execute construction.

## Not authorised

This authorization does not permit:

- EXP-019 reruns or mutation;
- Databento market-data requests;
- strategy replay;
- optimisation;
- MCPT;
- bootstrap analysis;
- walk-forward analysis;
- paper trading;
- live trading;
- claims of exchange-verified accuracy;
- claims that Databento is the best vendor.
