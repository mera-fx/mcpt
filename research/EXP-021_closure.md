# EXP-021 Closure

**Closed date:** 2026-07-26

**Classification:** `DIAGNOSTIC_METHOD_SELECTED_FOR_SEPARATE_CONSTRUCTION`

## Selected operational rule

`VOL_GT_OUT_2S_E3`

The rule requires two consecutive sessions where incoming daily volume exceeds
outgoing daily volume and permits the effective roll boundary up to three
common trading sessions after the calendar boundary.

| Metric | Result |
|---|---:|
| Clean transitions | 42 |
| Clean volume-driven boundaries | 40 |
| Warning calendar fallbacks | 23 |
| Clean calendar fallbacks | 2 |
| Total calendar fallbacks | 25 |
| Non-calendar roll dates | 40 |
| Hard checks | 16/16 |
| Databento API calls | 0 |
| Continuous series constructed | No |
| Strategy tested | No |

## Passing candidates

| Rank | Candidate | Clean triggers | Fallbacks | Non-calendar rolls |
|---:|---|---:|---:|---:|
| 4 | `VOL_GT_OUT_2S_E3` | 40 | 25 | 40 |
| 7 | `VOL_GT_OUT_1S_E2` | 40 | 25 | 40 |
| 8 | `VOL_GT_OUT_1S_E3` | 42 | 23 | 42 |

The selected method was the first passing candidate in the locked order. It
was not selected using strategy returns.

## Schedule non-equivalence

| Left candidate | Right candidate | Different roll dates |
|---|---|---:|
| `VOL_GT_OUT_2S_E3` | `VOL_GT_OUT_1S_E2` | 40 of 65 |
| `VOL_GT_OUT_2S_E3` | `VOL_GT_OUT_1S_E3` | 42 of 65 |
| `VOL_GT_OUT_1S_E2` | `VOL_GT_OUT_1S_E3` | 2 of 65 |

Aggregate counts do not imply equivalent roll schedules.

## Selected-method clean fallbacks

| Transition | Pair | Calendar date | Diagnostic window |
|---:|---|---|---|
| 59 | `NQZ24` to `NQH25` | 2024-12-13 | 2024-11-29 to 2024-12-18 |
| 60 | `NQH25` to `NQM25` | 2025-03-14 | 2025-02-28 to 2025-03-19 |

The other 23 fallbacks are the frozen provider-warning transitions.

## Boundary

EXP-021 selected an operational roll rule for a separate construction
experiment. It did not construct a continuous series, test a strategy,
establish edge, verify exchange accuracy, select the best vendor, or authorise
paper/live trading.

EXP-021 is permanently frozen. EXP-022 must be separately preregistered before
constructing a continuous series from `VOL_GT_OUT_2S_E3`.
