# EXP-016 Pre-measurement Alignment Correction

**Basis:** locked preregistration and code review only  
**Vendor bar values viewed:** no  
**Local audit results viewed:** no  
**Remote access performed by correction:** no

Five original samples had already downloaded and the sixth request had failed
with HTTP 429 when this implementation review identified three mismatches.
Only request status, file size and SHA-256 metadata had been inspected.

## Locked definitions restored

- Expected-minute completeness is explicitly reported as
  `matched_rows / reference_rows`, where the frozen Quantower timestamps are
  the expected one-minute axis.
- The 99.5% close-within-one-tick threshold applies only outside roll windows:
  `2021_thanksgiving` and `2024_thanksgiving`.
- Roll/DST windows remain fully measured and visible, but do not enter that
  ordinary-window close gate.
- Difference buckets are reported independently for open, high, low and close.

## Unchanged boundaries

The six dates, NQ.F symbol, one-minute timeframe, raw files, hashes, request
locks, one-retry amendment, Quantower data, methodology cap, primary-source
prohibition and paper/live trading prohibition remain unchanged.
