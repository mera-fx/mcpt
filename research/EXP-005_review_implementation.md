# EXP-005 Read-Only Review Implementation

**Locked:** 14 July 2026  
**Status:** Locked after full-validation pass and before review decision  
**Review type:** Read-only operational-quality review

The review reads only the frozen quick-transfer and full-validation result
files plus already-produced trade, yearly and cost-sensitivity CSVs. It does
not rerun the ORB strategy, MCPT, data import or optimization.

Every check is mandatory:

1. Full-validation result and 1,000-permutation MCPT integrity.
2. Fixed rules and no-optimization integrity.
3. Confirmation data-quality integrity.
4. Positive NQ and MNQ evidence in both protected periods.
5. Positive NQ net profit in 2023, 2024 and 2025.
6. Positive NQ and MNQ edge under two ticks of slippage per side.
7. Average trade at least twice the modeled round-trip cost.
8. Net profit at least twice maximum drawdown.
9. NQ/MNQ trade-count, Profit-Factor and scaled-P&L consistency.
10. At least 40% long and 40% short trades for both contracts.
11. Top five losses at most 20% of total gross loss.
12. Largest single loss at most 30% of maximum drawdown.

A pass permits only a separately implemented paper-only simulator using the
unchanged fixed rules. It does not authorize live trading or leverage.
