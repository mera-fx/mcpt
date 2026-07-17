# EXP-007 Protected Implementation

**Status:** Implemented, not run  
**Strategy results viewed:** None

The implementation preserves the exact EXP-007 preregistration:

- one fixed 30-minute opening range;
- long only;
- completed 5-minute close above the range high;
- entry at the next 5-minute open;
- stop at the opening-range low;
- target at 1R;
- forced flat at 14:00 New York;
- one fixed contract;
- one-minute stop/target sequencing;
- stop-first treatment when both boundaries occur in one minute;
- 2021–2025 annual diagnostics;
- zero, one and two ticks per-side cost sensitivity;
- 10,000 diagnostic bootstrap resamples;
- 1,000 fixed-strategy session-aware NQ permutations;
- no optimization inside real or permuted markets.

EXP-005 remains unchanged as the accepted control. EXP-006 remains unchanged as a rejected historical optimization. No live trading is authorized.
