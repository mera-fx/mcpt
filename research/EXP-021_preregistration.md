# EXP-021 Preregistration

**Locked date:** 2026-07-26  
**Research status:** `PRE_REGISTERED`  
**Implementation status:** `NOT_IMPLEMENTED`  
**Execution status:** `NOT_RUN`

## Title

NQ Volume-Roll Trigger Diagnostic and Rule Selection

## Known result disclosed before lock

EXP-020 is complete and frozen. It selected zero volume crossovers and used
the calendar fallback for all 65 transitions.

| Metric | Known result |
|---|---:|
| Volume crossovers selected | 0 |
| Calendar fallbacks | 65 |
| Provider-warning transitions | 23 |
| Clean transitions that still fell back | 42 |
| Identical roll dates | 65 |
| Market data identical across method labels | Yes |

No EXP-021 candidate result has been viewed.

## Objective

EXP-021 will diagnose why the EXP-020 trigger was inactive and compare a
small, fixed set of volume rules. It uses volume and contract-date evidence
only. Strategy returns and trading performance are outside scope.

EXP-021 does not construct a new continuous series. A selected method requires
a separate construction experiment.

## Frozen inputs

| Input | Locked value |
|---|---|
| EXP-020 closure commit | `44758ef08152b661f32c152866f5e71743d81acf` |
| EXP-020 closure record hash | `d23232285776135e623f35c10db57918274fc475111d70926a241d357f4e106f` |
| EXP-019 archive hash | `225a64dc06cb6bb303fd83d186f2e7d81e2a8a8bec44382380c8ccc1b0b6baa3` |
| Contracts | 66 |
| Adjacent transitions | 65 |
| Source records | 6,276,486 |
| Databento API calls | 0 |

## Candidate matrix

All candidates require incoming daily volume to be strictly greater than
outgoing daily volume. `E0` means no later than the calendar boundary; `E1`
through `E3` allow one through three later common trading sessions.

| Order | Candidate | Consecutive sessions | Extension |
|---:|---|---:|---:|
| 1 | `VOL_GT_OUT_2S_E0` | 2 | 0 |
| 2 | `VOL_GT_OUT_2S_E1` | 2 | 1 |
| 3 | `VOL_GT_OUT_2S_E2` | 2 | 2 |
| 4 | `VOL_GT_OUT_2S_E3` | 2 | 3 |
| 5 | `VOL_GT_OUT_1S_E0` | 1 | 0 |
| 6 | `VOL_GT_OUT_1S_E1` | 1 | 1 |
| 7 | `VOL_GT_OUT_1S_E2` | 1 | 2 |
| 8 | `VOL_GT_OUT_1S_E3` | 1 | 3 |

The control `VOL_GT_OUT_2S_E0` must reproduce EXP-020's zero crossovers.
The search starts ten common trading sessions before the calendar boundary.
No effective boundary may be after expiry.

## Provider-warning policy

The 23 transitions touching a provider-warning contract are forced to the
calendar fallback in every candidate. Their volume may be reported but cannot
select a roll boundary. Selection therefore uses the 42 clean transitions.

## Selection gates

A candidate qualifies only when all hard checks pass and it:

- selects volume on at least 34 of 42 clean transitions;
- produces at least 20 roll dates different from calendar;
- resolves all 65 transitions with disclosed fallback;
- never selects warning volume;
- never rolls after expiry;
- never exceeds three common sessions after calendar.

The first passing candidate in the fixed order is selected. Every result is
retained even when it fails or no method is selected.

## Boundaries

EXP-021 is diagnostic data engineering only. It does not authorise EXP-019 or
EXP-020 reruns, Databento requests, continuous-series construction, strategy
testing, optimisation, MCPT, paper trading or live trading.
