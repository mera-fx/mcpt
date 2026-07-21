# EXP-016 Preregistration

## NQ.F Structural and Cross-Source Sample Audit

**Locked:** 21 July 2026

**State:** PRE_REGISTERED / NOT RUN

**Vendor-history results viewed:** None

## Purpose

EXP-016 will measure whether London Strategic Edge `NQ.F` one-minute
samples are internally valid and sufficiently consistent with the frozen
Quantower NQ reference to remain useful as a supplementary source.

The highest possible result is supplementary-source qualification.
EXP-016 cannot authorize `NQ.F` as the primary source and cannot qualify
MNQ or any other vendor dataset.

## Frozen EXP-015 evidence

EXP-015 closed to REVIEW at commit
`bd877443f637d8041c3de935c1c8c872f5abcf72`.

The protected catalog audit found 69 futures rows, one NQ candidate
(`NQ.F`), zero MNQ candidates, and unresolved contract, roll and price
adjustment methodology. EXP-016 must verify the frozen EXP-015 hashes
before any history request.

## Scope and access

EXP-016 is limited to `NQ.F`, one-minute bars and six fixed samples.
Only the official `lse-data 0.14.0` client in the isolated environment
may be used. The key must be supplied through `LSE_API_KEY` and must
never be printed, written or committed.

The catalog cannot be rerun. The implementation may make at most six
remote history requests: one per fixed window. Full history is
prohibited. Raw responses remain local and ignored by Git.

## Fixed sample windows

| Window | Dates | Purpose |
|---|---|---|
| 2020 March | 6–20 March 2020 | DST, roll and extreme volatility |
| 2021 Thanksgiving | 19 November–3 December 2021 | Holiday and shortened sessions |
| 2022 June | 3–17 June 2022 | Roll and ordinary sessions |
| 2023 March | 3–17 March 2023 | DST and roll |
| 2024 Thanksgiving | 22 November–6 December 2024 | Holiday and shortened sessions |
| 2025 March | 7–21 March 2025 | DST and roll |

The windows cannot change after vendor history is viewed.

## Measurements

Each sample will measure timestamp parsing, timezone, order, duplicates,
finite OHLCV values, OHLC invariants, negative volume, expected and
missing minutes, session completeness, DST, holiday and roll behaviour,
and raw and normalized hashes.

Against Quantower it will measure matched and unmatched UTC minutes,
absolute OHLC differences, exact/quarter-point/one-point/larger buckets,
close-within-one-tick share, session OHLC differences, descriptive
volume differences and the 100 largest discrepancies. No row may be
silently excluded and no price offset may be applied.

## Interpretation

Possible classifications are `ACCESS_UNAVAILABLE`,
`STRUCTURE_UNRESOLVED`, `NOT_QUALIFIED`, `SUPPLEMENTARY_ONLY`, and
`QUALIFIED_AS_SUPPLEMENTARY_NQ_SOURCE`.

The highest result requires all six windows, resolved timestamp
semantics, zero duplicates, zero invalid OHLC rows, zero negative-volume
rows, at least 99.9% expected-minute completeness, at least 99.9%
timestamp overlap and at least 99.5% of ordinary matched closes within
one tick.

Unresolved contract, roll or adjustment methodology limits the result
to `SUPPLEMENTARY_ONLY`. EXP-016 cannot qualify a primary source.

## Prohibitions

EXP-016 must not replace Quantower data, edit prior results, download
complete NQ.F history, change sample windows after seeing results,
silently repair bars, infer methodology from `.F`, apply a price offset,
run or optimize strategies, qualify MNQ or another asset, claim
primary-source status, or authorize paper/live trading.
