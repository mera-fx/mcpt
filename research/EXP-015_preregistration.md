# EXP-015 Preregistration

## London Strategic Edge NQ/MNQ Data-Source Qualification

**Locked:** 21 July 2026
**State:** PRE_REGISTERED / NOT RUN
**Results viewed:** None from the EXP-015 vendor catalog or history

## Purpose

EXP-015 will determine whether London Strategic Edge can be used as a
source of one-minute NQ and MNQ historical data for **new** research.

A successful result would not qualify every dataset on the platform.
It would apply only to the tested NQ/MNQ historical use case. Separate
qualification would still be required for other markets, resolutions,
options, macro data, live streaming and execution use.

EXP-015 cannot replace, edit or reinterpret the frozen Quantower data
used by EXP-005 through EXP-014.

## Why this audit is required

The vendor publicly describes a large free databank, futures coverage,
fourteen candle resolutions and an official `lse-data` Python client.
Those are vendor claims, not evidence that the exact NQ/MNQ history,
continuous-contract construction, timestamps and session coverage meet
this repository's requirements.

The official package observed when this document was locked was
`lse-data` 0.14.0, released 7 July 2026. It was marked Beta, required
Python 3.8 or later and listed classifiers through Python 3.13. The
project currently uses Python 3.14.6, so compatibility must be tested
outside the main environment before installation there.

## Source and credential boundary

Only the official API or official Python client may be used.

The key must be supplied through the `LSE_API_KEY` environment variable.
It must never be printed, written into a file, embedded in a command,
committed to Git or included in a report.

Raw vendor downloads remain local and ignored by Git. Tracked evidence
may include manifests, hashes, normalized measurements and reports, but
not credentials or unrestricted raw data.

Website scraping is prohibited.

## Frozen audit sequence

### Phase 1 — environment probe

1. Record Python and operating-system versions.
2. Verify the `lse-data` package version and distribution hash.
3. Test import and client construction in an isolated environment.
4. Do not install the package into the main project environment unless
   compatibility is demonstrated.

### Phase 2 — futures catalog

The futures catalog must be read before any history download.

The audit must locate NQ and MNQ without guessing symbols. For each
candidate dataset it must preserve the catalog symbol, name, category,
history span and tick count.

The audit must record whether each series is:

- an individual contract;
- a continuous contract; or
- unknown/other.

Roll construction, price adjustment and upstream-source metadata must be
recorded when available. Ambiguous NQ or MNQ identity stops the history
phase.

### Phase 3 — fixed one-minute samples

The following windows are locked before catalog or bar results:

| Window | Dates | Purpose |
|---|---|---|
| 2020 March | 6–20 March 2020 | DST, quarterly roll and extreme volatility |
| 2021 Thanksgiving | 19 November–3 December 2021 | Holiday and shortened sessions |
| 2022 June | 3–17 June 2022 | Quarterly roll and ordinary sessions |
| 2023 March | 3–17 March 2023 | DST and quarterly roll |
| 2024 Thanksgiving | 22 November–6 December 2024 | Holiday and shortened sessions |
| 2025 March | 7–21 March 2025 | DST and quarterly roll |

The windows cannot be changed after viewing catalog or history results.
A full 2020–2025 vendor download is prohibited until these samples have
been reviewed.

Downloaded bars must not be silently filled, deleted, resampled or
repaired.

## Measurements

For NQ and MNQ separately, EXP-015 will measure:

- timestamp order, uniqueness and timezone awareness;
- finite numeric OHLCV fields and OHLC invariants;
- negative volume;
- expected, missing and unexpected extended-session minutes;
- session completeness;
- DST, holiday, shortened-session and roll-window behaviour;
- raw and normalized file hashes.

Against the frozen Quantower reference it will measure:

- matched and unmatched timestamps;
- absolute open, high, low and close differences;
- counts at exact, quarter-point, one-point and larger differences;
- session OHLC differences;
- volume differences as descriptive evidence;
- the 100 largest discrepancies;
- roll windows separately from ordinary sessions.

No row may be silently excluded to improve agreement.

## Frozen-strategy replay diagnostic

Only after catalog identity and structural samples pass, the three
unchanged EXP-014 finalists may be replayed on both sources:

- `gap_fade_0p50_1r`
- `premarket_continuation_0p50_time`
- `premarket_continuation_0p75_time`

Rules, costs and execution remain exact. There is no candidate search,
parameter change, optimization or new edge test.

The comparison measures trade counts, entry and exit timestamps,
direction, net profit and drawdown. It is a data-sensitivity diagnostic,
not a new strategy result.

## Interpretation

Possible use-case classifications are:

1. `CATALOG_UNAVAILABLE`
2. `IDENTITY_UNRESOLVED`
3. `SUPPLEMENTARY_ONLY`
4. `QUALIFIED_FOR_NEW_NQ_MNQ_HISTORICAL_RESEARCH`

The highest classification requires resolved NQ and MNQ identity,
timestamp and roll methodology, no duplicate timestamps, no invalid
OHLC rows, no negative volume, at least 99.9% expected-minute
completeness and timestamp overlap, at least 99.5% of matched ordinary
close values within one tick, at least 99% replay entry-direction
agreement and no more than a 1% relative trade-count difference.

These are precommitted qualification thresholds, not strategy gates.

## Prohibitions

EXP-015 must not:

- change any frozen prior data or result;
- guess symbols;
- download history before catalog identity passes;
- alter sample windows after seeing results;
- silently repair vendor data;
- expose the API key;
- scrape the website;
- optimize a strategy;
- claim every platform dataset is qualified;
- authorize paper or live trading.

## Expected lifecycle

After measurement, EXP-015 moves to `REVIEW` with all measurements and
limitations visible. It does not automatically authorize use of the
source or any trading activity.
