# EXP-022 Construction Authorization

**Authorized date:** 2026-07-26

**Preregistration commit:** `73c1255bcb904e71d927ed1097788de9b791bb54`

**Implementation commit:** `6dd69307c3dcfed876c57d6f62ae6d98bcb6ad93`

## Authorized action

This record authorizes:

1. the protected read-only EXP-022 preflight;
2. exactly one local construction run using `VOL_GT_OUT_2S_E3`;
3. creation of the unadjusted and backward-adjusted selected-roll series;
4. the locked independent rebuild and 20 hard checks.

## Restrictions

- Maximum construction runs: 1
- Databento API calls: 0
- Credentials required or authorized: No
- EXP-019 archive modifications: Not authorized
- EXP-020 output modifications: Not authorized
- EXP-021 output modifications: Not authorized
- Roll-rule reselection: Not authorized
- Roll-date recalculation: Not authorized
- Strategy replay or optimization: Not authorized
- MCPT, bootstrap or walk-forward: Not authorized
- Paper or live trading: Not authorized

After successful construction, rerunning EXP-022 is prohibited.
