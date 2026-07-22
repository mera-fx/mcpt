# EXP-018 Protected Implementation

**Implemented date:** 2026-07-22

**Execution state:** `IMPLEMENTED_NOT_RUN`

**OHLCV requested by implementation:** none

## Purpose

This implementation enforces the locked EXP-018 Databento exact-contract
structural and repeatability qualification.

It supports four mutually exclusive modes:

1. `--preflight`
2. `--initial-downloads`
3. `--repeat-downloads`
4. `--audit-local`

Application and framework tests do not contact Databento.

## Protected request plan

The implementation permits only the six preregistered `GLBX.MDP3`
`ohlcv-1m` raw-symbol requests. The Thanksgiving and March DST windows may
be requested once more after at least 24 hours.

Maximum successful bar requests: **8**.

Before every bar request, the official metadata cost endpoint is checked.
The cumulative estimated cost may not exceed **$1.00**.

Each attempt receives a local request lock before remote access. A failed
attempt remains locked and cannot be retried automatically. A reviewed,
committed amendment would be required.

## Raw data handling

The official Python client streams DBN Zstandard data to a local ignored
path. Raw bytes receive a SHA-256 hash.

For local measurement, the isolated Databento environment extracts only the
raw integer OHLCV fields into an ignored NPZ file. Prices remain in
Databento's fixed raw units. No rounding, repair, fill, deletion, timestamp
shift or resampling is performed.

The canonical row hash covers sorted timestamp, publisher, instrument,
OHLC and volume arrays using fixed little-endian representations.

## Session model

Expected sessions use `America/New_York` so the March DST transition changes
UTC offsets without shifting observed timestamps.

- regular session: 09:30–16:00 ET;
- extended session measurement: Globex minutes outside the regular session;
- normal Globex session: 18:00 ET on the prior calendar day through 17:00 ET;
- Thanksgiving 2024 and the following Friday use locked shortened-session
  exceptions.

Databento omits intervals with no trades. Coverage therefore measures
observed trade minutes against expected tradable minutes; missing intervals
are reported and are not silently filled.

## Output boundary

Raw and derived vendor rows remain under `data/EXP-018/` and are ignored by
Git. Aggregate measurements and hashes are written under
`results/EXP-018/source_qualification/`.

The highest possible classification remains
`QUALIFIED_AS_ACCESSIBLE_EXACT_CONTRACT_SOURCE`. It is not an
exchange-accuracy claim, a best-vendor claim or trading authorization.
