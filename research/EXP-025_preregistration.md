# EXP-025 Preregistration

**Experiment:** `EXP-025`

**Title:** NQ Gap-Fade Exact-Contract Decision-Engine Qualification

**Locked:** 2026-07-27

**Preregistration record SHA-256:** `7534f8ba59a57e79ec98067b3fda3606e5b327a2320c82805cf8001f8c6dd5aa`

## Research question

EXP-024 left 43 `gap_fade_0p50_1r` rows unresolved because the
Quantower-reference decision could not be reconstructed from the locked
provider-managed continuous-series features. EXP-025 will test whether those
same 43 sessions agree when both sources use the **same explicit quarterly NQ
contract**, and whether two independently implemented versions of the frozen
gap-fade decision rule agree on identical inputs.

## Frozen population

The population is all 43 rows selected from the frozen EXP-024 mismatch ledger
where the candidate is `gap_fade_0p50_1r`, the attribution is
`UNRESOLVED_WITH_LOCKED_FEATURES`, and the locked Quantower-reference
reconstruction failed.

Sampling, adding rows, removing rows, replacing dates or selecting only easier
sessions is prohibited.

## Source boundary

### Databento

Use only the frozen EXP-019 exact-contract archive:

- dataset: `GLBX.MDP3`;
- schema: `ohlcv-1m`;
- 66 quarterly NQ contracts;
- archive SHA-256: `225a64dc06cb6bb303fd83d186f2e7d81e2a8a8bec44382380c8ccc1b0b6baa3`;
- no API calls or new Databento download.

The exact contract for each session is the contract already recorded by the
frozen EXP-022/EXP-024 roll context. It cannot be reselected.

### Quantower

A later result-free implementation must define a protected ingest path for
manual Quantower/Lucid-Rithmic exports of the **identical exact contract**.
Each export must provide explicit contract identity, one-minute timestamps,
OHLCV, declared timezone and a byte-hash manifest.

This preregistration does not authorize the export, ingest or diagnostic run.
Continuous symbols cannot be used as exact-contract evidence. Missing or
ambiguous contract identity is a hard failure.

## Permitted market windows

For each of the 43 rows, only these New York windows may be materialized:

- immediately previous cash session: 09:30:00–15:59:59;
- current session: 09:30:00 through the 09:35:00 one-minute bar.

No current data after the 09:35 bar, no unrelated sessions and no protected
history may be read. Missing bars cannot be filled, repaired, forward-filled
or synthesized.

## Comparisons

The diagnostic will compare:

1. exact contract identity;
2. aligned one-minute OHLC bars;
3. observed-minute five-minute aggregation;
4. all frozen gap-fade decision components;
5. the canonical frozen engine;
6. a separately coded independent engine;
7. exact-contract decisions against the already-frozen provider-managed
   Quantower and Databento transfer decisions.

OHLC equality requires identical timestamps and identical values after
canonical 0.25-point NQ tick normalization. Volume is descriptive only.

## Classification

The possible classifications are:

- `EXACT_CONTRACT_DIAGNOSTIC_COMPLETE_EQUIVALENT`
- `EXACT_CONTRACT_DIAGNOSTIC_COMPLETE_SOURCE_DIFFERENCES`
- `EXACT_CONTRACT_DIAGNOSTIC_COMPLETE_ENGINE_DIFFERENCES`
- `EXACT_CONTRACT_DIAGNOSTIC_COMPLETE_MIXED_DIFFERENCES`
- `EXACT_CONTRACT_DIAGNOSTIC_NOT_QUALIFIED`

No classification establishes vendor superiority, validates strategy edge,
selects a candidate, unlocks protected history or authorizes trading.

## Prohibited work

EXP-025 may not:

- rerun or modify EXP-024;
- modify the EXP-019 archive;
- reselect a contract or roll rule;
- use a continuous symbol as exact-contract evidence;
- calculate exits, P&L, returns, equity or drawdown;
- change the strategy rule or threshold;
- optimize, run MCPT, bootstrap or walk-forward analysis;
- call the Databento API or access the network;
- start paper or live trading.

## Required sequence

1. Commit this preregistration.
2. Build and commit a result-free implementation.
3. Run the implementation-only protected preflight.
4. Commit a separate one-time execution authorization.
5. Run the authorized preflight.
6. Run one diagnostic execution.
7. Freeze and close EXP-025.
