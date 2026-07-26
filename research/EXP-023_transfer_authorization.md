# EXP-023 Transfer Authorization

**Authorized date:** 2026-07-26

**Preregistration commit:** `66ba6a46f31cc8715447179c19caf2f4c1a1e8be`

**Implementation commit:** `c17e9ea567c234e2d941f949168d62721f6d4963`

## Authorized action

The user's instruction to “push and continue,” following the explicit handoff
that the next phase was the single protected EXP-023 run, authorizes:

1. the result-free protected EXP-023 preflight;
2. exactly one local transfer replay of the three frozen EXP-014 finalists;
3. use of the backward-adjusted EXP-022 series as primary;
4. use of the unadjusted series as the locked roll-sensitivity diagnostic;
5. OHLCV access only for the known 2020-01-03 through 2025-12-31 overlap;
6. the independent rebuild, 20 hard checks and locked evidence report.

## Restrictions

- Maximum transfer runs: 1
- Pre-2020 or 2026 OHLCV access: Not authorized
- Databento API calls: 0
- Network access or new market-data download: Not authorized
- EXP-022 output modification: Not authorized
- EXP-014 output modification: Not authorized
- Session-quality modification: Not authorized
- Candidate addition, removal or rule change: Not authorized
- Strategy search or optimization: Not authorized
- MCPT, bootstrap or walk-forward: Not authorized
- Candidate ranking or winner selection: Not authorized
- Paper or live trading: Not authorized
- Separate protected-history validation: Not authorized

The run may measure profitability, but profitability is not a transfer gate.
All three finalists must remain separate and visible. After a successful
transfer diagnostic, rerunning EXP-023 is prohibited.
