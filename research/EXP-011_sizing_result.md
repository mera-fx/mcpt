# EXP-011 position-sizing result

## What was measured

EXP-011 kept both frozen EXP-010 opening-drive signals unchanged and compared
three ways of expressing each signal during 2021–2025:

1. fixed one-contract NQ;
2. theoretical fractional NQ sized toward constant dollar risk; and
3. implementable whole-contract MNQ sized toward the same dollar target.

The target was **$1,005**, calculated once as the median valid one-NQ initial
risk from 181 primary-signal trades in the separate 2019–2020 calibration
period.

## Main result

Equal-risk sizing did what it was designed to do: it made initial dollar risk
far more consistent and materially reduced drawdown. It also reduced absolute
profit because the 2021–2025 fixed one-NQ baseline happened to average about
$2,157 of initial risk per trade—more than twice the frozen $1,005 target.

### Primary time-exit signal

| Sizing | Net profit | PF | Win rate | Max drawdown | Avg initial risk | Risk CV |
|---|---:|---:|---:|---:|---:|---:|
| Fixed 1 NQ | $197,970 | 1.3870 | 49.83% | -$25,280 | $2,156.99 | 0.5148 |
| Fractional NQ | $95,871.10 | 1.3721 | 49.83% | -$9,715.64 | $1,004.56 | 0.0096 |
| Integer MNQ | $80,339.50 | 1.3443 | 49.66% | -$9,162.50 | $899.58 | 0.0902 |

### User-reference 1.5R-or-time signal

| Sizing | Net profit | PF | Win rate | Max drawdown | Avg initial risk | Risk CV |
|---|---:|---:|---:|---:|---:|---:|
| Fixed 1 NQ | $177,245 | 1.3557 | 52.19% | -$24,930 | $2,156.99 | 0.5148 |
| Fractional NQ | $79,260.50 | 1.3195 | 52.19% | -$9,715.64 | $1,004.56 | 0.0096 |
| Integer MNQ | $67,727.50 | 1.3020 | 52.18% | -$9,162.50 | $899.58 | 0.0902 |

Fractional NQ held risk almost exactly at the target except where the 2.0
contract cap applied. Whole-contract MNQ had somewhat more variation because
it must round down, but its risk dispersion remained much lower than fixed one
NQ. MNQ skipped one signal that could not fund one whole contract within the
target.

## Paired diagnostic

The paired session bootstrap confirms that the lower-risk methods produced
less raw P&L per evaluation session than the much higher-risk fixed baseline.
For the primary signal:

- fractional NQ minus fixed NQ averaged **-$82.94 per session**, with a 95%
  interval of **-$143.31 to -$23.29**;
- integer MNQ minus fixed NQ averaged **-$95.56 per session**, with a 95%
  interval of **-$161.77 to -$30.24**.

These are exposure comparisons, not new tests of the entry signal.

## Unit correction

Before closure, the initial report-only MNQ bootstrap was found to multiply the
already multi-contract MNQ dollar ledger by ten again. The original files were
preserved in an audit directory. Only the deterministic paired bootstrap and
its report text were corrected to use actual US dollars at scale 1.0. The
calibration and all six strategy/sizing measurements were unchanged.

## Research interpretation

EXP-011 is a useful sizing measurement, not a pass/fail decision:

- fixed NQ produced more absolute historical profit by taking materially more
  average initial risk;
- equal-risk sizing greatly reduced risk variation and drawdown;
- theoretical fractional NQ delivered the best risk consistency;
- integer MNQ is the practical implementation and closely approximated the
  target with whole contracts;
- neither method is declared an automatic winner; and
- EXP-011 does not provide independent signal confirmation or authorize paper
  or live trading.
