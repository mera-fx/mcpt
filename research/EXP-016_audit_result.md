# EXP-016 NQ.F Structural and Cross-Source Sample Audit Result

**Classification:** `NOT_QUALIFIED`

All six vendor samples were structurally clean. The source failed interchangeable supplementary qualification because every window was below the locked 99.9% expected-minute and matched-timestamp thresholds, and both outside-roll windows were below the 99.5% close-within-one-tick threshold.

This does not prove London data is inherently inaccurate and does not prove Quantower is ground truth. It proves the two tested continuous series are not sufficiently equivalent under the locked rules.

| Window | Completeness | Matched timestamps | Close within one tick |
|---|---:|---:|---:|
| 2020_march_dst_roll_volatility | 98.888889% | 98.888889% | 96.273408% |
| 2021_thanksgiving | 89.320388% | 89.320388% | 97.047101% |
| 2022_june_roll | 90.789474% | 90.789474% | 88.123994% |
| 2023_march_dst_roll | 89.805825% | 89.805825% | 87.585586% |
| 2024_thanksgiving | 87.978142% | 87.978142% | 97.826087% |
| 2025_march_dst_roll | 90.829694% | 90.829694% | 96.818910% |

Raw vendor bars and largest-discrepancy rows remain local and gitignored. Only aggregate measurements and hashes are tracked.

| Local output | SHA-256 |
|---|---|
| audit_result_json_sha256 | `f2a63b304490eaeb60a437dd92250aace492367f9263ce0dce375f5a942455b5` |
| structural_measurements_csv_sha256 | `f7a7aa0a6c06d87f79ddd4d9e1f025a2a73205974e299ee60dedd3079665437b` |
| cross_source_measurements_csv_sha256 | `c23ac3c14093feba12840895e83804712f21acfa06e55b431fbb68b5d730f988` |
| largest_discrepancies_csv_sha256 | `d577944a6bbac241e40f11f69bdb8f70357c46a69f4da73855beb2d2c587478b` |
| download_manifest_json_sha256 | `fb540777eab1e1f6ee6e7b26989eb52a8a5cc3eaa48add968a6f1c8801a7d799` |

**Tracked aggregate canonical SHA-256:** `d18456790c3596a5ab031868b2e224152849219227f5903fe5f4fcdd6bab74f8`
