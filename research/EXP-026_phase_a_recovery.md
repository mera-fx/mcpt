# EXP-026 Phase A Recovery Authorisation

**Experiment:** EXP-026

**Phase:** A

**Recovery ID:** `EXP-026-A-R1`

**Status:** `AUTHORIZED_NOT_RUN`

**Phase A authorisation commit:** `5fa417ed56c2d620c5d348e9ab43f3d7634518b8`

**Implementation commit:** `13ee0683dfcbbb5d763f7254f3b245ecc8e6d9cd`

## Failure classification

The one-time Phase A calculation completed both deterministic rebuilds and wrote five hash-locked result files. It then stopped while producing `report.md` because pandas could not import the optional `tabulate` package.

The existing partial files contain 46,584 decision rows, 11,502 trade rows, 24 reported candidates and six frozen survivors.

## Permitted recovery

The recovery may only verify the five existing files, generate the missing report and manifests, and atomically promote the existing partial directory.

## Prohibited actions

The recovery cannot read market data, replay or recalculate a strategy, repeat selection, change a candidate or parameter, access Phase B, Phase C or protected 2026 data, download data, use a network or order API, or authorise paper or live trading.
