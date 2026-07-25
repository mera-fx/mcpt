# EXP-020 Preflight Digest Correction Implementation

**Implementation date:** 2026-07-25

**Status:** `IMPLEMENTED_NOT_AUTHORIZED`

**Construction status:** `NOT_RUN`

## Observed preflight failure

The protected EXP-020 preflight stopped with:

```text
ERROR: EXP-019 archive digest changed.
```

A read-only diagnostic reproduced both digest protocols:

| Digest protocol | SHA-256 |
|---|---|
| Frozen EXP-019 insertion-order JSON | `225a64dc06cb6bb303fd83d186f2e7d81e2a8a8bec44382380c8ccc1b0b6baa3` |
| Incorrect EXP-020 sorted-key JSON | `8734b41f8bc5a3f3773f634323e6d52a4f2fffd6ef0d161863499c64d7110198` |

The frozen EXP-019 digest matched exactly. No source file changed.

## Root cause

EXP-019 encoded the ordered archive manifest payload with compact JSON while
preserving dictionary insertion order. The initial EXP-020 constructor reused
a general canonical JSON helper that adds `sort_keys=True`. Sorting the keys
changes the encoded bytes and therefore changes the digest despite identical
manifest data.

## Correction

`archive_digest` now reproduces the frozen EXP-019 digest protocol exactly:

- rows ordered by integer sequence;
- field order `sequence`, `canonical_symbol`, `sha256`, `size_bytes`;
- compact separators;
- ASCII encoding;
- no key sorting.

The general canonical JSON helper remains unchanged for EXP-020's own new
evidence.

## Additional authorization gate

Because this correction changes a constructor file after the original one-time
authorization, the corrected constructor requires a separate correction
authorization before preflight or construction can proceed.

## Safety state

- EXP-019 rerun: No
- Databento market-data request: No
- EXP-020 construction: No
- EXP-020 output written: No
- Strategy run: No
- Existing authorization replaced: No
