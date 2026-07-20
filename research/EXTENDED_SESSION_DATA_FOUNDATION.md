# NQ/MNQ Extended-Session Data Foundation

## Purpose

This protected data upgrade derives an extended-session NQ/MNQ dataset from
the immutable Quantower exports already archived for EXP-005.

It does not calculate a strategy result, optimize a parameter, run MCPT or
change the lifecycle or evidence classification of EXP-005 through EXP-011.

## Why it is separate

The existing frozen research data intentionally contains only the
09:30-16:00 America/New_York cash session. The archived source CSV files also
contain extended-hours records. Those records are copied into a separate
derived dataset so none of the previously frozen research inputs change.

## Session calendar

Each trade date is measured from 18:00 on the prior calendar day through
16:59 on the trade date.

- Before trade date 2021-06-28, the expected calendar excludes the historical
  16:15-16:30 equity-index futures pause.
- From trade date 2021-06-28 onward, that pause is not expected.
- The daily 17:00-18:00 maintenance period is outside the session.
- Timezone conversion uses America/New_York, including historical daylight
  saving transitions.

CME announced that the 15-minute equity-index pause would be eliminated
effective Sunday 2021-06-27 for trade date Monday 2021-06-28.

## Protected normalization

1. Every archived source file is verified against its frozen SHA-256.
2. Exact duplicated OHLCV rows retain one copy.
3. Identical OHLC rows with different volume retain maximum volume.
4. An OHLC conflict is accepted only when one candidate matches the already
   frozen cash-session bar; otherwise the build stops.
5. Large primary exports are authoritative where present.
6. Small supplementary and session-retry exports fill missing timestamps
   only. They do not overwrite an existing primary extended-hours bar.
7. The entire frozen cash-session frame is overlaid exactly.
8. Missing extended-hours bars are never synthesized or forward-filled.
9. Only trade dates complete and timestamp-aligned in both NQ and MNQ enter
   the final dataset.

Fallback disagreements remain recorded in the audit even though fallback
files cannot overwrite primary rows.

## Output

The protected builder creates:

```text
data/extended_session/processed/NQ_1m_extended.parquet
data/extended_session/processed/MNQ_1m_extended.parquet
data/extended_session/processed/NQ_5m_extended.parquet
data/extended_session/processed/MNQ_5m_extended.parquet

results/extended_session_data/extended_session_audit.json
results/extended_session_data/session_quality.csv
results/extended_session_data/source_manifest.json
```

One-minute and five-minute rows include:

- `session_date`
- active-session minute number
- session segment (`evening`, `overnight`, `premarket`, `cash`, `post_cash`)

Five-minute bars are formed from five consecutive tradable minutes. The
historical scheduled pause therefore does not create synthetic empty bars.

## Research boundary

The dataset can later support separately preregistered studies of overnight
inventory, cash-open gaps, overnight range breakouts and premarket momentum.
Creating the data foundation itself is not evidence that any such strategy
has an edge.
