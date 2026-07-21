# EXP-014 result review correction

## Status

The first local EXP-014 behaviour-study output generated from commit `03a636f`
was reviewed before result freeze and was **not accepted as the frozen result**.

## Defect found

The two research-sleeve pair rows correctly calculated session and monthly
measurements, but their annual aggregation used a pandas grouping key whose
index did not align with the dated P&L series. This produced:

- `total_years = 0`
- `profitable_years = 0`
- missing `worst_year_usd`

The underlying session P&L, candidate measurements, pair net profit, pair
maximum drawdown, monthly measurements, overlap measurements, strategy rules,
parameters, costs, position sizing, and frozen EXP-013 evidence were unchanged.

## Correction

The annual pair grouping now uses the year values as a positional NumPy key.
A regression test requires non-missing and exact annual pair measurements in
the synthetic study.

## Research boundary

This is a reporting/measurement correction made before freezing EXP-014. It
does not select a strategy, optimize a pair, introduce a regime filter, or
authorize paper or live trading. The flawed local output must be deleted and the
full study rerun from a clean committed tree.
