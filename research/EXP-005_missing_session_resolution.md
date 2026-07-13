# EXP-005 Provider-History Session Resolution

**Record:** EXP-005-DQ2  
**Locked:** 2026-07-13  
**Strategy results viewed:** No  
**2023–2025 confirmation accessed:** No

## Evidence

Dedicated one-day exports were attempted after the original full
exports reported three incomplete expected sessions. The retries
reproduced the same provider-history limitations:

| Session | NQ | MNQ | Resolution |
|---|---:|---:|---|
| 2019-05-06 | 390/390 | 313/390 | Exclude both |
| 2019-06-17 | 390/390 | 378/390 | Exclude both |
| 2020-07-21 | 0/390 | 0/390 | Exclude both |

On 2019-05-06, MNQ begins at 10:47 ET and is missing the first
77 cash-session minutes.

On 2019-06-17, MNQ is missing these 12 minutes:

```text
12:24, 13:12, 13:25, 13:29, 13:31, 13:32,
13:33, 13:53, 14:33, 14:39, 14:43, 14:44 ET
```

On 2020-07-21, neither provider front-month export returns any
cash-session bars.

## Locked handling

- Exclude both NQ and MNQ for all three dates.
- Do not fill, interpolate, copy, or synthesize any bar.
- Keep every raw full export and retry unchanged and hash-locked.
- Stop on any incomplete expected session not listed here.
- Stop if any listed date's observed missing-minute pattern or
  required source hashes change.
- Keep every EXP-005 strategy rule, period, cost assumption,
  MCPT method and decision gate unchanged.

These sessions are excluded before NQ/MNQ alignment and before
any strategy calculation. Therefore the included invalid-session
count remains zero.
