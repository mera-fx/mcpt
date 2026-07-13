# EXP-005 Quantower Recheck Resolution

**Record:** EXP-005-DQ1  
**Locked:** 2026-07-13  
**Strategy results viewed:** No  
**2023–2025 confirmation accessed:** No

## Audit result

The full NQ/MNQ exports contained 222 duplicated timestamps:

| Location/type | Count |
|---|---:|
| Inside 09:30–16:00 ET | 66 |
| Outside 09:30–16:00 ET | 156 |
| Inside, volume-only conflict | 62 |
| Inside, OHLC conflict | 4 |

The four OHLC conflicts were two timestamps present in both NQ
and MNQ:

```text
2020-06-11 13:40 America/New_York
2020-10-21 12:20 America/New_York
```

## Dedicated one-day re-exports

NQ and MNQ were re-exported separately for both affected days.
Each re-export contained 1,365 rows, no duplicate timestamps and
one stable bar at the affected minute.

The stable re-export bar matched one of the two original
candidates exactly in every case—the lower-volume candidate.

## Locked normalization

1. Exact OHLCV duplicates: keep one copy.
2. Same OHLC but differing volume: keep maximum volume.
   EXP-005 does not use volume.
3. Differing OHLC: use a dedicated re-export only when:
   - its SHA-256 is locked;
   - its timestamp and OHLCV match this record;
   - it matches one original conflicting candidate.
4. Any unrecorded OHLC conflict: stop.
5. Never edit the original source CSV files.

## Locked correction bars

| Symbol | UTC timestamp | O | H | L | C | Volume |
|---|---|---:|---:|---:|---:|---:|
| NQ | 2020-06-11 17:40 | 9737.75 | 9741.50 | 9732.00 | 9739.75 | 953 |
| MNQ | 2020-06-11 17:40 | 9738.00 | 9741.75 | 9732.00 | 9739.50 | 1034 |
| NQ | 2020-10-21 16:20 | 11653.75 | 11701.00 | 11651.00 | 11700.00 | 3082 |
| MNQ | 2020-10-21 16:20 | 11653.75 | 11700.00 | 11651.00 | 11700.00 | 4284 |

This is a source-data quality resolution only. It does not change
the ORB signal, costs, periods, MCPT method or decision gates.
