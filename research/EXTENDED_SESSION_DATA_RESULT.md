# NQ/MNQ Extended-Session Data Result

## Status

The protected extended-session foundation is **DATA_READY**.

It was derived from the immutable Quantower exports already archived for
EXP-005. No strategy, optimization, bootstrap or MCPT result was calculated.
No missing price was filled, and the frozen cash-session data was not changed.

## What is available

The final comparison dataset contains:

| Data | Sessions | Rows per market |
|---|---:|---:|
| One-minute NQ/MNQ | 1,344 aligned complete sessions | 1,849,560 |
| Five-minute NQ/MNQ | 1,344 aligned complete sessions | 369,912 |

The included period begins on 2019-08-02 and ends on 2025-12-31.

Each row identifies the trade date, active-session minute and one of five
readable segments:

- evening;
- overnight;
- premarket;
- cash; or
- post-cash.

## Why 295 cash-session dates were excluded

The starting universe contained the 1,639 dates already accepted in the
frozen cash-session research. The extended-hours audit required every expected
minute to exist in both NQ and MNQ. It excluded 295 dates rather than creating
bars or carrying prices forward.

| Year | Cash dates considered | Complete aligned | Excluded |
|---|---:|---:|---:|
| 2019 | 162 | 13 | 149 |
| 2020 | 246 | 221 | 25 |
| 2021 | 250 | 224 | 26 |
| 2022 | 248 | 233 | 15 |
| 2023 | 246 | 215 | 31 |
| 2024 | 248 | 216 | 32 |
| 2025 | 239 | 222 | 17 |

The concentration in 2019 is primarily an alignment limitation: NQ had 119
individually complete extended sessions, but early MNQ history had only 13.
MNQ began trading in 2019 and the archived provider export contains many
minutes with no MNQ bar during that early period.

From 2020 through 2025, the aligned dataset retains 1,331 sessions.

## Important distinction

The audit also measured each market separately:

- NQ individually had 1,457 complete sessions;
- MNQ individually had 1,464 complete sessions;
- 1,344 dates were complete in both.

The first version deliberately stores the aligned intersection so NQ/MNQ
comparisons use exactly the same dates and timestamps. A later NQ-only study
may use the additional NQ-complete dates, but it must identify that different
sample explicitly rather than mixing it into an aligned comparison.

## Source normalization

- Four large multi-year exports were primary.
- Ten smaller supplementary files were permitted to fill missing timestamps
  only.
- Supplements added 600 final-day rows per symbol.
- No overlapping fallback price disagreed with a primary price.
- Each symbol contained 211 duplicated timestamps:
  - 208 identical-price, different-volume duplicates;
  - three OHLC conflicts resolved only by matching the already frozen cash
    bar.
- Source CSV files were never edited.

## Research boundary

This data foundation unlocks separately preregistered studies of cash-open
gaps, overnight inventory, overnight range breakouts and premarket momentum.
Being data-ready is not evidence that any of those strategies has an edge and
does not authorize paper or live trading.
