# EXP-004 Protected Quick-Screen Result

**Experiment:** QQQ 5-Minute Opening Range Breakout  
**Decision:** REJECT  
**Lifecycle stage:** REJECTED  
**Recorded:** 2026-07-13  
**Implementation commit:** `cd887db`  
**Out-of-sample disclosure:** BLOCKED  
**2023–2025 QQQ results viewed:** No

## Data audit

| Item | Result |
|---|---:|
| Included full sessions | 997 |
| Included five-minute rows | 77,766 |
| Early closes excluded | 7 |
| Incomplete sessions excluded | 4 |
| Included invalid sessions | 0 |

The quick screen used only the locked 2019-01-02 through
2022-12-30 QQQ SIP period.

## Gate results

| Gate | Actual | Requirement | Result |
|---|---:|---:|---|
| Best in-sample trade PF | 1.046326 | > 1.10 | FAIL |
| Fixed in-sample trade PF | 1.021062 | > 1.05 | FAIL |
| Combinations with PF ≥ 1 | 3 | ≥ 3 | PASS |
| Session-aware MCPT p-value | 0.307692 | ≤ 0.20 | FAIL |
| Fixed completed trades | 973 | ≥ 250 | PASS |
| Fixed long trades | 508 | ≥ 50 | PASS |
| Fixed short trades | 465 | ≥ 50 | PASS |
| Included invalid sessions | 0 | ≤ 0 | PASS |

The MCPT used 25 deterministic, time-of-day-stratified session
permutations and eight workers.

## Interpretation

The exact basic QQQ ORB specification failed three mandatory
gates. The sample contained 973 completed trades and passed every
data-quality requirement, so the rejection was not caused by an
undersized or invalid sample.

This result applies only to the preregistered basic version:

```text
15-minute opening range
Long or short
Completed-bar breakout
Entry at next five-minute open
Stop at the opposite range boundary
One trade per session
Forced flat at 15:55 ET
```

More structured ORB versions—such as volatility context, volume
confirmation, gap context, breakout buffers, retests, targets or
alternative exits—were not tested. They require new experiment
IDs and cannot modify EXP-004.

## Frozen outputs

```text
results/EXP-004/quick_screen/quick_screen_decision.json
reports/EXP-004-quick-screen/report.html
```

EXP-004 must not be rerun, repaired or exposed to its locked
2023–2025 QQQ period.
