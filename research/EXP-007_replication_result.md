# EXP-007 Fixed Historical Replication Result

**Decision:** Reject EXP-007 and preserve it as a completed negative
historical result.

## Fixed strategy

- NQ primary evidence market; MNQ implementation check
- 30-minute opening range
- Long only
- Entry on the next five-minute open after the first completed close
  above the range
- Stop at the opening-range low
- Target at 1R
- Forced flat at 14:00 New York
- One fixed contract
- No optimization, delta confirmation or added filters

## Main evidence

| Metric | NQ | MNQ |
|---|---:|---:|
| Completed trades | 988 | 985 |
| Profit Factor | 1.116817 | 1.096446 |
| Net profit | $67,780.00 | $5,649.50 |
| Average trade | $68.60 | $5.74 |
| Maximum drawdown | -$26,020.00 | -$2,618.50 |
| Profitable calendar years | 5 of 7 | 5 of 7 |

NQ produced four profitable annual evaluation blocks out of five and
$70,880 combined net profit over 2021–2025. It remained profitable with
two ticks of slippage per side, producing $57,900.

## Statistical evidence

The locked session-aware NQ MCPT used 1,000 permutations. Fifty-five
permutations produced a Profit Factor at least as large as the real
result.

`p = (1 + 55) / (1 + 1000) = 0.055944`

The locked maximum passing value was 0.050000. This was the only failed
gate.

The diagnostic trade bootstrap also remained uncertain: its 95%
percentile interval for average trade crossed zero, and its Profit Factor
interval crossed 1.0. The bootstrap was report-only and did not determine
the formal decision.

## Interpretation

The fixed strategy was profitable, cost-resilient and directionally
confirmed by MNQ, but it did not meet the preregistered statistical
threshold. The threshold, seed and permutation count may not be modified
after viewing the result.

Because the 2019–2025 data had already been viewed in earlier research,
this was exploratory historical evidence in any case. No live trading is
authorized.

Further exit or position-sizing research must be performed as a separate
preregistered experiment without modifying EXP-007.
