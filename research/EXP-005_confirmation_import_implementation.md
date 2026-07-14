# EXP-005 Confirmation-Import Implementation

**Implementation date:** 2026-07-14  
**Quick result:** frozen pass  
**Confirmation strategy results viewed:** no  
**Optimization:** disabled

## Purpose

This implementation records the protected quick-transfer pass, advances
EXP-005 to `FULL_VALIDATION`, and unlocks data acquisition for the
preregistered 2023-01-03 through 2025-12-31 confirmation period.

It does not run the ORB, calculate trades, calculate Profit Factor, run
MCPT, or make a full-validation decision.

## Frozen quick evidence

The tracked JSON is an exact copy of the one-time quick-transfer decision.

```text
research/EXP-005_quick_transfer_result.json
SHA-256: 4705eeece180b05f4242943680829256458625a3c5e4ed7f712c674bbc51c51d
```

The result passed all ten quick gates and confirms that the confirmation
period had not been accessed.

## Frozen confirmation calendar

The importer uses a tracked list of 744 full 09:30–16:00
America/New_York equity sessions from 2023-01-03 through 2025-12-31.

```text
research/EXP-005_confirmation_full_sessions.csv
SHA-256: 3ca50dfd41e9e069c4a848ca63845ebc9a308a19245da85fe669808c831867b2
```

Eight early-close sessions are not part of the full-session list:

```text
2023-07-03
2023-11-24
2024-07-03
2024-11-29
2024-12-24
2025-07-03
2025-11-28
2025-12-24
```

The calendar was generated and frozen before any confirmation CSV was
imported. The runtime importer does not require a calendar package or
network access.

## Protected import rules

- Only cash-session dates from 2023-01-03 through 2025-12-31 are allowed.
- NQ and MNQ must each contain every expected full session.
- Every included session must contain exactly 390 one-minute bars.
- Aggregation must produce exactly 78 five-minute bars.
- Missing bars are never filled.
- Exact duplicated rows may be collapsed.
- Equal-price, volume-only duplicates keep maximum volume; volume is not
  used by EXP-005.
- Any unresolved OHLC conflict stops the import.
- NQ/MNQ timestamp alignment is mandatory.
- Potential front-month mismatch sessions are excluded from both symbols.
- Original CSV files are archived and hash-verified.
- No strategy result is calculated during import.
- The quick-transfer test cannot be rerun by this workflow.

## Output

A successful import writes separate confirmation-only parquet files,
a raw-file manifest, excluded-session table, dataset fingerprints, and
an audit linked to the frozen quick-transfer result.
