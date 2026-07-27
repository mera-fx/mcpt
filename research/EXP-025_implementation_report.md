# EXP-025 Result-Free Implementation Report

**Experiment:** `EXP-025`

**Implementation status:** Implemented, not authorized, not run

**Locked preregistration commit:** `1d736705a41d0208e353fb17710c8a16cc937710`

**Locked preregistration record SHA-256:** `7534f8ba59a57e79ec98067b3fda3606e5b327a2320c82805cf8001f8c6dd5aa`

## Purpose

This implementation prepares the protected exact-contract source and
decision-engine diagnostic preregistered for all 43 unresolved EXP-024
`gap_fade_0p50_1r` sessions.

It does not export or ingest Quantower data during installation. It does not
materialize Databento market values during installation or implementation-only
preflight. It does not execute EXP-025, rerun EXP-024, calculate strategy
performance, or authorize paper or live trading.

## Files

- `exp025_exact_contract_core.py`
- `exp025_exact_contract_diagnostic.py`
- `tests/test_exp025_exact_contract_diagnostic.py`
- `research/EXP-025_implementation_report.md`

## Locked diagnostic population

The implementation selects exactly the 43 frozen EXP-024 rows where:

- `candidate_id == gap_fade_0p50_1r`;
- `primary_attribution_category == UNRESOLVED_WITH_LOCKED_FEATURES`;
- the frozen Quantower-reference reconstruction failed;
- the frozen Quantower reference contains no trade;
- the frozen Databento transfer contains a trade;
- the frozen Databento transfer rebuild matches the transfer decision.

The selected session date and exact Databento quarterly contract are joined to
the frozen EXP-024 roll-context ledger. Adjusted and unadjusted contract and
instrument identities must agree. Sampling, replacing, adding or removing rows
is rejected.

## Frozen source checks

The implementation-only preflight verifies, without reading market values:

1. clean synchronized `main`;
2. unchanged EXP-025 preregistration files;
3. one shared latest implementation revision across all four implementation files;
4. all 14 frozen EXP-024 output files and hashes;
5. the frozen EXP-019 acquisition manifest and completion marker;
6. all 66 exact-contract archive file sizes and SHA-256 hashes;
7. the locked archive digest and total byte count;
8. all 43 population contracts are present in the frozen archive;
9. no EXP-025 result or partial-result directory exists;
10. no Quantower export or authorization file exists.

The implementation-only preflight refuses while `DATABENTO_API_KEY` is set.
It makes no API call and does not import or instantiate a Databento historical
client.

## Quantower exact-contract export format

A later separately authorized export phase must create:

`data/EXP-025/quantower_exact_contract_exports/export_manifest.json`

The manifest is an object with these locked top-level fields:

```json
{
  "schema_version": 1,
  "experiment_id": "EXP-025",
  "status": "COMPLETE",
  "source": "Lucid/Rithmic via Quantower History Exporter",
  "resolution": "1 minute",
  "research_timezone": "America/New_York",
  "required_columns": [
    "timestamp",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "explicit_contract_symbol"
  ],
  "files": []
}
```

Exactly 43 file entries are required. Each entry must contain:

- `session_date`;
- `previous_session_date`;
- `explicit_contract_symbol`;
- `relative_path`;
- `size_bytes`;
- `sha256`;
- `row_count`;
- `timestamp_timezone`;
- `pretrimmed_to_allowed_windows: true`.

Each CSV must have the exact required column order. The contract must equal the
frozen exact quarterly NQ contract for that session. Continuous symbols,
synthetic identities, path traversal and ambiguous contract names are rejected.

The raw export files remain beneath the gitignored `data/` directory.

## Permitted rows

For each session, the only rows that may be materialized are:

- immediately previous frozen cash session, 09:30 through 15:59 New York;
- current session, 09:30 through the 09:35 one-minute bar New York.

Quantower CSVs must already be trimmed to those windows. Any materialized row
outside them is a hard failure.

The frozen Databento DBN file is iterated record by record. Only `ts_event` is
inspected until a record is found inside a permitted session window. OHLCV and
instrument fields are accessed only for retained records. No full-contract
DataFrame is created.

Missing rows remain missing. The implementation does not fill, repair,
forward-fill, backfill or synthesize bars.

## Price and bar rules

- NQ tick size: 0.25 points.
- Prices must map exactly to integer NQ ticks.
- No tolerance beyond canonical tick representation.
- Timestamps must be unique, timezone-aware and aligned to exact minutes.
- OHLC geometry must be valid.
- Volume is descriptive only and must be non-negative.
- Five-minute aggregation uses observed one-minute rows only.

## Two decision engines

### Canonical engine

The canonical path calls the existing frozen EXP-024
`build_candidate_features` function with the unchanged candidate:

`gap_fade_0p50_1r`

The threshold remains 0.50 and the operator remains `>=`.

### Independent engine

The independent path separately calculates:

- previous cash close, high, low and range;
- current cash open;
- gap move, direction and normalized gap;
- threshold margin and pass status;
- fade direction;
- first cash-bar OHLC and confirmation;
- 09:35 entry open;
- entry-risk points and positive-risk status;
- final setup decision and direction.

It does not import or call the canonical decision function.

Both engines receive the same canonical input hash for each source-session
pair. A disagreement on identical input is classified as an engine difference.

## Diagnostic classifications

The implemented final classifications are:

- `EXACT_CONTRACT_DIAGNOSTIC_COMPLETE_EQUIVALENT`
- `EXACT_CONTRACT_DIAGNOSTIC_COMPLETE_SOURCE_DIFFERENCES`
- `EXACT_CONTRACT_DIAGNOSTIC_COMPLETE_ENGINE_DIFFERENCES`
- `EXACT_CONTRACT_DIAGNOSTIC_COMPLETE_MIXED_DIFFERENCES`
- `EXACT_CONTRACT_DIAGNOSTIC_NOT_QUALIFIED`

Any failed hard check forces `EXACT_CONTRACT_DIAGNOSTIC_NOT_QUALIFIED`.

No classification establishes vendor superiority, selects a strategy, validates
edge, unlocks protected history or authorizes trading.

## Output contract

A future authorized run may create exactly 14 files beneath:

`results/EXP-025/exact_contract_diagnostic`

The files are:

1. `exp025_summary.json`
2. `session_contract_map.csv`
3. `one_minute_bar_comparison.csv`
4. `five_minute_component_comparison.csv`
5. `decision_engine_comparison.csv`
6. `source_difference_summary.csv`
7. `output_hashes.json`
8. `report.md`
9. `report.html`
10. `EXACT_CONTRACT_DIAGNOSTIC_COMPLETE.json`
11. `assets/exact_contract_bar_match.png`
12. `assets/decision_comparison.png`
13. `assets/component_difference_ticks.png`
14. `assets/prior_vs_exact_decisions.png`

The output schemas exclude exits, P&L, profit factor, win rate, returns, equity,
drawdown and strategy ranking.

## Execution guards

The runner has three explicit modes:

```powershell
.\.venv\Scripts\python.exe .\exp025_exact_contract_diagnostic.py `
    --implementation-preflight
```

```powershell
.\.venv\Scripts\python.exe .\exp025_exact_contract_diagnostic.py `
    --execution-preflight
```

```powershell
.\.venv\Scripts\python.exe .\exp025_exact_contract_diagnostic.py `
    --execute
```

Only the first mode is appropriate after this implementation is committed.

Execution preflight and execution require a later
`exp025_execution_authorization.py` record locked to:

- the exact implementation commit;
- the preregistration record hash;
- one diagnostic run only;
- the SHA-256 of the completed 43-file Quantower export manifest;
- zero Databento API calls;
- no network, strategy replay, performance calculation, paper trading or live
  trading authorization.

## Independent rebuild

A future authorized execution builds all five tabular evidence sets twice from
the locked source files. Their canonical DataFrame hashes must agree before
publication.

## Current boundary

After this implementation is committed:

1. run only the implementation preflight;
2. freeze the implementation commit;
3. create a separate Quantower export authorization and export plan;
4. do not export data until that authorization is committed;
5. after exports exist, lock their manifest hash in a separate one-time
   execution authorization;
6. run execution preflight before any diagnostic execution.

EXP-024 remains permanently frozen.

## Result-free guard correction

A post-preflight implementation review identified two missing protections before
any Quantower export was authorized:

1. the export manifest previously required only that `previous_session_date`
   precede the target date, rather than equal the immediately prior frozen cash
   session;
2. the implementation baseline previously resolved the commit that created the
   implementation files, rather than the latest single commit shared by all four
   implementation files.

The corrected implementation hash-verifies
`results/extended_session_data/session_quality.csv` at 78,768 bytes and SHA-256
`6b55077783ad2c1cd8ef99f10d50ed7d691aad7cafcdb7e8fa37639d90724712`.
It uses only that file's `session_date` metadata to map each of the 43 target
sessions to the immediately preceding frozen session. It reads no OHLC values.

The Quantower export manifest must now contain that exact prior-session mapping.
A merely earlier calendar date is rejected. The implementation preflight now
reports the latest shared commit that modified all four implementation files, so
a later authorization can lock the final corrected implementation revision.

This correction does not authorize or create Quantower exports, materialize
market values, execute the diagnostic, calculate performance, or authorize
paper or live trading.
