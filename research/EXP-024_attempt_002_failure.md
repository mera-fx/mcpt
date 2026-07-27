# EXP-024 Attempt 002 Publication Failure

**Failed date:** 2026-07-26

**Execution head:** `da7bbe843361fd9d08cf64cc1e772c9eabf82fb5`

**Authorization:** `EXP-024-ATTRIBUTION-AUTH-002`

**Outcome:** `ATTRIBUTION_CALCULATED_PUBLICATION_INCOMPLETE`

## What completed

The corrected protected loader completed all permitted Quantower and
Databento scans. Both independent attribution rebuilds completed and their
semantic hashes matched.

The process then wrote and hashed in this failure record:

- five CSV evidence files;
- four visual assets.

The exception occurred while building the Markdown hard-check table, after
the charts were saved but before the summary, reports, manifest, completion
marker, or atomic final-directory rename.

## Publication exception

```text
TypeError: cannot use 'dict' as a set element (unhashable type: 'dict')
```

An extra pair of braces in an f-string created a set literal containing a
dictionary. This is a report-formatting bug; it did not change the calculated
attribution artifacts.

## Preserved evidence

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `aggregation_check.csv` | 641,094 | `c2c693c142a076db404739047f8e683cb63e1c218f057e1c3d46b9c20f63a7fa` |
| `assets/attribution_categories.png` | 74,003 | `9c88dc6b2c68fd36eb471b0c8298e8e3d455de80fbef0a29d511ba4e8d4d5f85` |
| `assets/raw_component_differences.png` | 79,515 | `8e81cf3d629653841c90abac421e37b7f994ced81490eb1420ee7fb3e58f3214` |
| `assets/roll_context.png` | 57,825 | `f8b9fd976c18ce3e227dacb5317adf96f73ee4c769548e5ca892a5ccaf13e0bf` |
| `assets/threshold_margins.png` | 89,786 | `f7489bb363b51e9a6250a53ca262d545c3dbf6cac93fa09b31132cd056dde7a6` |
| `feature_comparison.csv` | 38,064 | `d10a5ffb4e01ee0b7ab65d65f721ab5beca0a4b9cfac6eca4fdacc82c9bd595c` |
| `mismatch_attribution.csv` | 6,797 | `1f762b2cbb2d53c0cd979171a584a42fb3e8742040b2c3bb9494155e7d55dbae` |
| `raw_component_differences.csv` | 163,741 | `de13b28fb809ce5b267816b126b71ecbe3ae4d2d396b7cab9bbf9860e417c457` |
| `roll_context.csv` | 8,791 | `35ec1eba30a6eeea59ab369b89a575b0cad44cf23b6b3ca89d494a8ef6428ffc` |

## Reconstructed locked result

- Candidate-session rows: 51
- Quantower aggregation rows: 4,709, all matched
- Transfer decision rebuild: 51/51 matched
- Quantower reference decision rebuild: 8/51 matched
- Failed reference rebuild rows: 43, all gap fade
- Unresolved rows: 43
- Locked classification:
  `ATTRIBUTION_DIAGNOSTIC_NOT_QUALIFIED`

The 43 failed reference rows rebuild as Quantower gap-fade signals even though
the frozen reference ledger records no trade. This violates a hard check, so
the identified categories on the remaining rows cannot qualify the overall
diagnostic.

## Evidence-only recovery boundary

Authorization 002 is consumed. No market-data rerun is authorized.

The user's later instruction `authorize` permits a separate recovery that:

1. validates the exact nine hashes above;
2. reads only those persisted files;
3. creates the missing summary, Markdown/HTML reports, output manifest and
   completion marker;
4. verifies the nine original hashes are unchanged;
5. atomically publishes the partial directory.

Feature reconstruction, attribution, chart rebuilding, market Parquet access,
and modification of the nine artifacts are prohibited.
