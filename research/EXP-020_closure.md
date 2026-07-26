# EXP-020 Closure

**Closed date:** 2026-07-26

**Status:** `REVIEW`

**Classification:** `QUALIFIED_WITH_DISCLOSED_CALENDAR_FALLBACKS`

## Construction result

| Metric | Result |
|---|---:|
| Frozen source contracts | 66 |
| Frozen source records | 6,276,486 |
| Continuous series files | 4 |
| Rows per series | 5,463,753 |
| Adjacent transitions per method | 65 |
| Hard checks | 20/20 |
| Independent rebuild | Passed |
| Databento API calls | 0 |
| Source archive modified | No |

## Method result

| Metric | Result |
|---|---:|
| Volume crossovers selected | 0 |
| Calendar fallbacks | 65 |
| Provider-warning transitions | 23 |
| Fallbacks without provider warnings | 42 |
| Identical roll dates | 65 |
| Identical roll differences | 65 |
| Unadjusted market data identical | Yes |
| Adjusted market data identical | Yes |
| Distinct continuous datasets | 2 |

The primary volume-labelled construction collapsed completely to the locked
calendar fallback. The volume-labelled and calendar-labelled files contain
identical market data and adjustment values; only their `roll_method` labels
differ.

## Interpretation

EXP-020 successfully created and independently verified the frozen continuous
series outputs. It did not demonstrate an active volume-roll method.

This is dataset qualification only. No strategy edge was tested and no
strategy, paper-trading or live-trading use is authorised.

## Frozen boundary

- EXP-020 is complete and frozen.
- EXP-020 construction must never be rerun.
- All output hashes are locked in `exp020_closure.py`.
- Further roll-rule diagnostics require separately preregistered EXP-021.
- EXP-021 may diagnose construction methods only.
- Strategy research remains unauthorised.
