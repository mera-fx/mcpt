# EXP-013 protected implementation

EXP-013 implements the preregistered three-finalist validation without
calculating a result.

The implementation:

- keeps the three finalist rules unchanged;
- reselects among those three in four anchored walk-forward folds;
- applies the locked 10,000-resample trade bootstrap to every finalist;
- repeats all 24 EXP-012 candidates inside every primary permutation;
- reconstructs randomized extended sessions from five independently shuffled
  one-minute components within every exact time-of-day slot;
- reports the discovery-wide maximum-Profit-Factor null and separate
  fixed-candidate diagnostics;
- keeps measurements primary and any evidence classification secondary;
- provides plain-English strategy and fraction explanations in the report;
- uses opaque white chart canvases and the established report colour rules;
- does not select an automatic trading winner or authorize paper/live trading.

No EXP-013 strategy, walk-forward, bootstrap, MCPT, classification or report
result is included in this implementation commit.
