# EXP-005 Confirmation Alignment Resolution

**Record:** EXP-005-DQ5  
**Locked:** 14 July 2026  
**Status:** Locked before any confirmation strategy or full-validation result

## Decision

Keep the existing NQ/MNQ cross-symbol alignment safeguard unchanged and
exclude both symbols for all nine sessions it rejected.

No price bar is selected, repaired, filled, averaged, or invented. The raw
Quantower exports remain unchanged.

## Evidence

The protected alignment audit found 742 common complete sessions before
alignment and 733 after alignment. Its tracked output fingerprints are:

- Details CSV SHA-256: `deb9d23a2407c9fef4c98e5e28ba5ea1b08c618a4caffe37baa13c3be80b3cf9`
- Summary JSON SHA-256: `5d525a21634a1f3d4014587d99f576ca326924271ddd5de6488c6f3d50decc91`

Three sessions show persistent divergence for all 390 cash-session minutes:

| Session | Median difference | Maximum difference |
|---|---:|---:|
| 2023-03-14 | 132.25 points | 135.00 points |
| 2023-12-12 | 211.25 points | 213.25 points |
| 2024-03-12 | 247.50 points | 250.00 points |

Six sessions have a small median difference but at least one isolated
cross-symbol difference above the locked 20-point maximum:

| Session | Median difference | Maximum difference | Minutes above 20 |
|---|---:|---:|---:|
| 2025-03-24 | 0.25 | 29.75 | 1 |
| 2025-04-01 | 0.25 | 31.25 | 1 |
| 2025-04-09 | 0.75 | 27.75 | 1 |
| 2025-05-19 | 0.25 | 30.25 | 1 |
| 2025-07-01 | 0.25 | 32.75 | 1 |
| 2025-10-24 | 0.25 | 30.75 | 1 |

The persistent cases are consistent with the two provider symbols
representing different price series for the whole session. The isolated
cases are described only as cross-symbol price divergences; the provider's
internal roll or adjustment mechanism is not claimed.

## Locked output counts

- Frozen full-session calendar: 744
- Paired provider-unavailable exclusions: 2
- Common complete sessions before alignment: 742
- Alignment exclusions: 9
- Final included sessions: 733
- One-minute rows per symbol: 285,870
- Five-minute rows per symbol: 57,174
- Included invalid or alignment-mismatch sessions: 0
- Synthesized bars: 0

Any different date, metric, count, or alignment threshold must stop the
confirmation import.
