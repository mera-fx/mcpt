# EXP-011 MNQ bootstrap unit correction

## Problem found before result closure

The initial EXP-011 run correctly produced all six signal-by-sizing
measurements. However, its report-only paired bootstrap multiplied the complete
dynamically sized MNQ position by ten before comparing it with fixed one-NQ.

That was a unit error. The MNQ trade ledger had already:

1. calculated a whole number of MNQ contracts,
2. multiplied each one-contract profit, loss and cost by that quantity, and
3. stored the completed position in actual US dollars.

An additional ten-times conversion therefore double-counted the NQ/MNQ
contract-multiplier difference.

## Protected correction

The correction:

- requires exact hashes of the original result, bootstrap and measurement CSV;
- preserves the original JSON and report in an audit directory;
- leaves the target-risk calibration and all six measurement rows unchanged;
- recomputes only the four deterministic paired session bootstraps;
- compares the complete NQ and MNQ positions in actual US dollars at scale 1.0;
- rebuilds only the report presentation; and
- records original and corrected hashes.

No signal, entry, stop, exit, strategy P&L, contract quantity, calibration,
cost, lifecycle decision, MCPT, or trading authorization is changed.
