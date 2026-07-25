# EXP-019 Local Exact-Contract Archive Audit Preregistration

**Locked:** 2026-07-25

**Status:** `PRE_REGISTERED`

## Acquisition evidence locked before examining OHLCV values

| Evidence | Locked value |
|---|---:|
| Raw DBN files | 66 |
| Compressed bytes | 104,491,346 |
| Successful downloads | 66 |
| Automatic retries | 0 |
| Attempted quoted cost | $22.914097756145 |
| Manifest SHA-256 | `f8fbac395bbe7f9cdafd0187a00c3d77ee8f6ded31d7ba6870d6ed3c8e3007b3` |
| Completion SHA-256 | `ef8ad499e62284d872edfd480e7aa635a26340e85ba1d74d98a51ed80f71f935` |
| Archive digest | `225a64dc06cb6bb303fd83d186f2e7d81e2a8a8bec44382380c8ccc1b0b6baa3` |

## Audit boundary

The audit is local and read-only. It will make zero Databento API requests,
require no API key, modify no archive file and construct no continuous series.

Every file will be checked for:

- manifest size and SHA-256 agreement;
- DBN readability and one-minute OHLCV schema;
- nonempty data and required fields;
- one instrument ID per exact-contract file;
- timestamps inside the locked request window;
- one-minute timestamp alignment and monotonic order;
- duplicate timestamps and duplicate full rows;
- finite OHLCV values and valid OHLC relationships;
- nonnegative volume;
- NQ quarter-point tick alignment.

Minute gaps, window density and adjacent-contract overlap will be measured.
They are not automatic failures because a one-minute OHLCV record is absent
when no trade occurs during that minute.

## Provider-condition warnings

The acquisition emitted provider warnings for 16 contract windows. Some warning
messages were truncated after several example dates. These warnings must remain
visible in the final audit report.

The final classification is locked as:

- `NOT_QUALIFIED` when any hard check fails;
- `QUALIFIED_WITH_KNOWN_PROVIDER_CONDITIONS` when all hard checks pass while
  the known warnings remain disclosed;
- `QUALIFIED` only when all hard checks pass and no provider-condition warnings
  are known.

The audit does not establish exchange accuracy, best-vendor status, a roll rule
or permission to use the archive in strategy research.
