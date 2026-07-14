# EXP-005 Quick-Transfer Result

**Stage:** QUICK_TRANSFER  
**Decision:** PASS_TO_FULL_VALIDATION  
**Calculated:** 2026-07-13 22:23:32 UTC  
**Implementation commit:** `4a791e121af129bcad75122e532def4ca27d70dd`  
**Tracked result SHA-256:** `4705eeece180b05f4242943680829256458625a3c5e4ed7f712c674bbc51c51d`

## Protected data

- Quick period: 2019-05-06 through 2022-12-30
- Included aligned sessions: 906
- Included invalid sessions: 0
- Included roll-switch sessions: 0
- Potential front-month mismatch sessions excluded: 3
- Provider-unavailable sessions excluded: 3
- Optimization: disabled
- Fixed parameter combinations: 1
- Confirmation period accessed: no
- Confirmation results calculated: no

## Results

| Metric | NQ | MNQ |
|---|---:|---:|
| Completed trades | 884 | 884 |
| Long trades | 457 | 454 |
| Short trades | 427 | 430 |
| Net profit | $94,660.00 | $8,549.50 |
| Trade Profit Factor | 1.134046 | 1.120163 |
| Win rate | 45.8145% | 45.7014% |
| Average trade | $107.08 | $9.67 |
| Median trade | -$297.50 | -$31.50 |
| Maximum drawdown | -$37,925.00 | -$4,078.50 |

## Quick MCPT

- Primary market: NQ
- Permutations: 25
- Real-or-better permutations: 1
- P-value: 0.076923
- Deterministic seed: 45
- Workers used: 8
- Optimization inside permutations: disabled

## Gate decision

All ten preregistered quick-transfer gates passed. EXP-005 advances once to
`FULL_VALIDATION`. The quick transfer is frozen and must not be rerun.

The 2023-01-03 through 2025-12-31 confirmation period may now be acquired
and imported through the protected confirmation workflow. This pass does
not constitute final acceptance or permission to change the ORB rules.
