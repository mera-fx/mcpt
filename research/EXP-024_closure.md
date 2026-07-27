# EXP-024 Closure

**Research status:** `REVIEW`

**Classification:** `ATTRIBUTION_DIAGNOSTIC_NOT_QUALIFIED`

**Closure record SHA-256:** `f11d3dc899d6ffcb1e24be6113715240da7ab7af109b1ab45daac64f5aadf183`

## Completed workflow

EXP-024 was preregistered to attribute 51 frozen EXP-023 cross-source
candidate-session decision mismatches. Attempt 001 failed before attribution.
The corrected attempt 002 completed both deterministic attribution rebuilds and
wrote nine evidence artifacts, but report publication stopped on a Markdown
formatting defect. A separately implemented and authorised evidence-only
recovery then published the final 14-file result without reading market
Parquet files, recalculating attribution or rebuilding charts.

## Locked diagnostic result

| Measurement | Result |
|---|---:|
| Candidate-session rows | 51 |
| Quantower aggregation rows matching | 4,709 / 4,709 |
| Transfer decision rebuild matching | 51 / 51 |
| Quantower reference rebuild matching | 8 / 51 |
| Quantower reference rebuild failures | 43 |
| Unresolved rows | 43 |
| Diagnostic hard failures | 1 |
| Recovery hard failures | 0 |

The failed hard check is
`reference_decision_rebuild_matches_frozen_alignment`. All 43 failed reference
rebuild rows are `gap_fade_0p50_1r` rows.

## Attribution categories

| Category | Count |
|---|---:|
| `ELIGIBILITY_DIFFERENCE` | 1 |
| `NORMALIZED_CONTEXT_THRESHOLD_CROSSING` | 5 |
| `MULTIPLE_DECISION_COMPONENT_DIFFERENCES` | 2 |
| `UNRESOLVED_WITH_LOCKED_FEATURES` | 43 |
| Other locked categories | 0 |

## Interpretation

The transfer reconstruction and Quantower one-minute-to-five-minute
aggregation checks passed, but the Quantower reference decision reconstruction
did not. Therefore the attribution diagnostic is not qualified and cannot be
used to declare either source correct, equivalent or superior. It does not
validate strategy edge, select a candidate, unlock protected history or
authorise paper or live trading.

## Frozen outputs

All 14 files in
`results/EXP-024/source_disagreement_attribution` are byte-hash locked by
`exp024_closure.py`. The output-manifest SHA-256 is
`93803c61ef670193556b2c7f1acb43a3cef9d4d6a692ead3afcf22baa1601cad`.

## Permanent boundary

EXP-024 is permanently frozen. Do not rerun any EXP-024 preflight, original
attribution, replacement attribution or evidence-recovery mode. Do not modify
the 14 final outputs. Any further data or engine qualification requires a new
experiment ID, beginning with EXP-025 or later, separate preregistration,
separate implementation and separate execution authorisation. Paper and live
trading remain prohibited.
## Analytics registry integration

EXP-024 is registered as a closed noncanonical strategy diagnostic. Its
published attribution summary, mismatch ledger and report remain available as
diagnostic evidence, but no canonical strategy-series analytics are exposed.
The registry correction does not create strategy trades, equity curves,
performance metrics or a source/candidate selection.
