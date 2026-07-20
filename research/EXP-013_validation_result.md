# EXP-013 — Extended-Context Finalist Validation Result

## Status

EXP-013 is complete and preserved in **REVIEW** with the secondary
classification **STRONG_HISTORICAL_EVIDENCE**.

This is measurement-first historical research. It is not independent
confirmation: all three finalists were selected after viewing the
EXP-012 tournament. No paper or live trading is authorized automatically.

## What was tested

- Three locked EXP-012 finalists:
  - gap fade at a 0.50 gap fraction with a 1R-or-time exit
  - premarket continuation at a 0.50 drive fraction with a time exit
  - premarket continuation at a 0.75 drive fraction with a time exit
- 1,331 frozen NQ and MNQ sessions from 2020-01-03 to 2025-12-31
- Fixed one-contract exposure and the common execution/cost model
- Four anchored annual walk-forward folds covering 2022–2025
- Zero-, one- and two-tick NQ cost measurements
- 10,000-resample trade bootstraps for all three finalists
- 1,000 session-aware permutations, with the complete 24-candidate
  EXP-012 search repeated inside every permutation

## What the strategies mean

The gap-fade strategy waits for a large opening gap, then trades back
toward the previous cash-session close when the first completed cash bar
confirms the reversal. Its 1R target gives it a relatively high win rate
and short average holding time.

The premarket-continuation strategies measure how much of the final
90-minute premarket range was converted into directional movement. A
0.50 fraction means the premarket moved at least halfway across its
high-low range; 0.75 requires a stronger three-quarter move. After the
first cash bar confirms that direction, the strategy enters and holds
until the 15:55 time exit unless its stop is reached.

## Three distinct trade-offs

### Gap fade 0.50 / 1R

- NQ Profit Factor: **1.530924**
- NQ net profit: **$34,810**
- Completed trades: **186**
- Win rate: **59.68%**
- Average trade: **$187.15**
- Maximum drawdown: **-$5,080**
- Net profit / maximum drawdown: **6.85**
- Fixed-candidate MCPT p-value: **0.001998**

This finalist best matches a preference for higher win rate, shorter
holding time and lower drawdown.

### Premarket continuation 0.50 / time

- NQ Profit Factor: **1.736374**
- NQ net profit: **$121,255**
- Completed trades: **291**
- Win rate: **27.84%**
- Average trade: **$416.68**
- Maximum drawdown: **-$20,695**
- Net profit / maximum drawdown: **5.86**
- Fixed-candidate MCPT p-value: **0.000999**

This finalist has the broadest sample and highest absolute historical
profit, but it accepts a lower win rate and larger drawdown.

### Premarket continuation 0.75 / time

- NQ Profit Factor: **2.023738**
- NQ net profit: **$44,205**
- Completed trades: **88**
- Win rate: **31.82%**
- Average trade: **$502.33**
- Maximum drawdown: **-$5,540**
- Net profit / maximum drawdown: **7.98**
- MNQ Profit Factor: **2.098280**
- Two-tick NQ net profit: **$43,325**
- Fixed-candidate MCPT p-value: **0.000999**

This was the measurement leader, but its 88-trade sample is much smaller.
Its stronger threshold selects fewer, more directional premarket setups.

## Forward-style and statistical evidence

- Profitable anchored walk-forward folds: **3 of 4**
- Combined walk-forward net profit: **$26,295**
- Profitable test years: **2022, 2023 and 2024**
- Losing test year: **2025, -$2,890**
- Discovery-wide exceedances: **3 of 1,000**
- Discovery-wide MCPT p-value: **0.003996**

The primary MCPT comparison used the maximum Profit Factor from all 24
EXP-012 candidates in every randomized market. Only three randomized
full searches matched or exceeded the real maximum. The plus-one formula
is `(3 + 1) / (1,000 + 1) = 0.003996`.

This corrects the statistical search across the 24 locked candidates. It
does not make the later human choice of these three finalists independent.

## Interpretation

All locked strong-evidence context checks passed. The three finalists
deserve continued comparison because they offer materially different
win-rate, drawdown, trade-count and payoff profiles. The correct claim is
strong exploratory historical evidence—not untouched confirmation, an
automatic winner, or trading approval.
