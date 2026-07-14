# EXP-005 Confirmation Recheck Resolution — EXP-005-DQ3

**Locked:** 2026-07-14  
**Stage:** Full-validation confirmation-data import  
**Strategy results calculated during resolution:** No  
**Full-validation results calculated during resolution:** No  
**Raw source files edited:** No

## Trigger

The protected 2023–2025 confirmation importer stopped before producing
processed data because the full NQ and MNQ exports each contained one
research-session OHLC conflict at:

- UTC: `2024-11-06 14:40:00`
- America/New_York: `2024-11-06 09:40:00`

Both conflicting pairs had identical open, high and low values but
different closes: `20783.50` and `20783.75`.

## Complete duplicate audit

The source-only audit found:

| Item | Count |
|---|---:|
| Duplicate timestamps | 200 |
| Inside the confirmation cash session | 54 |
| Outside the confirmation cash session | 146 |
| Inside-session volume-only conflicts | 52 |
| Inside-session OHLC conflicts | 2 |
| Unique OHLC-conflict timestamps | 1 |

Each symbol had 100 duplicate timestamps: 73 outside the research cash
session, 26 inside-session volume-only conflicts and one inside-session
OHLC conflict.

## Locked one-day rechecks

Both one-day exports contain 1,380 unique timestamps, no duplicates and
the expected `22:00–22:59 UTC` maintenance gap.

### NQ

- SHA-256:
  `82356fcec569434e317ea1ad60bf294a76493fb65eae8a842438df98bcc93986`
- Locked bar:
  `O 20793.00 H 20805.25 L 20778.25 C 20783.75 V 3845`

### MNQ

- SHA-256:
  `ed8704b7932a1077bd521cea5abc40e9d735e9d032bb2014127ebbd4e4a2f0db`
- Locked bar:
  `O 20793.00 H 20806.75 L 20778.25 C 20783.75 V 8851`

Each one-day recheck exactly matches the lower-volume candidate in the
corresponding full export.

## Resolution rules

1. Exact OHLCV duplicates: retain one copy.
2. Inside-session volume-only conflicts: retain the maximum-volume row.
   Volume is not used by EXP-005 signals, entries, exits or gates.
3. The two OHLC conflicts: use only the matching SHA-256-locked one-day
   recheck bar.
4. Any changed hash, changed recheck structure, unrecorded price
   conflict, changed duplicate population or correction that does not
   match an original candidate stops the import.
5. No bars are synthesized and no source CSV is edited.

This resolution does not claim why the provider export contained the
additional rows.
