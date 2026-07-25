# EXP-019 Exact-Contract Acquisition Authorization

**Authorization date:** 2026-07-25

**Status:** `AUTHORIZED_FOR_ONE_TIME_EXACT_CONTRACT_ACQUISITION`

## Completed cost estimate

| Measure | Locked result |
|---|---:|
| Contract windows | 66 |
| Exact-contract quote | $22.914098 |
| Continuous reference | $19.940800 |
| Maximum acquisition cost | $35.00 |
| Within cap | Yes |
| Automatic retries | 0 |
| Bars downloaded so far | 0 |

Cost-estimator commit:

`d75fdb296cc6e916ba9016c0e549c20bb905d376`

Local evidence hashes:

- Cost JSON: `a99aec4804e3be9e256dabbea6885f133727fe3b50045d9c51cfd1e7c165dad3`
- Contract-cost CSV: `8a8598f04c953ebe8ac38e4fc13eb232f4102ebebebe03389d12b9220bd4d9cc`

## Explicit authorization

The user explicitly authorized the one-time acquisition of the 66 exact
quarterly NQ contract windows locked by EXP-019, provided the total estimated
cost does not exceed **$35.00**.

The authorization applies only to:

- `GLBX.MDP3`;
- `ohlcv-1m`;
- raw-symbol exact quarterly NQ contracts;
- the 66 preregistered windows from NQM10 through NQU26;
- one successful download per locked window;
- local DBN Zstandard-compressed files;
- SHA-256 recording for every completed file.

## Failure handling

Automatic retries are prohibited.

A request failure must stop the process immediately. A later manual resume may
continue only after all existing completed files and manifest entries pass hash
verification. Completed contracts may not be downloaded again.

## Still prohibited

This authorization does not permit:

- downloading `NQ.v.0`;
- changing the locked windows;
- constructing a continuous series;
- back-adjusting or forward-adjusting prices;
- running or optimizing a strategy;
- paper trading;
- live trading;
- modifying any frozen earlier experiment.

The completed archive remains unqualified until the separate local archive
audit passes.
