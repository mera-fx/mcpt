# EXP-026 Phase C Completion Record

**Experiment:** EXP-026

**Phase:** C — Known 2020–2025 Comparison

**Completion date:** 2026-07-28

**Status:** `PHASE_C_COMPLETED_PENDING_CLOSURE`

**Locked implementation commit:** `13ee0683dfcbbb5d763f7254f3b245ecc8e6d9cd`

**Phase B completion commit:** `da8456d254dc710336806ad5940afcec649be016`

**Phase C authorisation commit:** `5e03bb449468b980e003c133ce076cf1b87b3ac7`

**Completion-record SHA-256:** `743aa1638cd00c279e216e6ccfedb402d7d9ce1954daafc3538e6362f4cc247a`

## Completed evidence

- Materialised source: `2019-12-01` through `2025-12-31`
- Reported known comparison: `2020-01-03` through `2025-12-31`
- Frozen finalists: 3
- Fixed controls: 2
- Candidate reselection: No
- Parameter changes: No
- Independent deterministic rebuild: Yes
- Known period treated as confirmation: No

## Frozen finalists

- `gap_fade_0p75_1r`
- `opening_drive_0p75_time`
- `premarket_continuation_0p875_1p5r`

## Fixed controls

- `orb_control_exp005_15m_both_time`
- `orb_control_exp007_30m_long_1r`

## Interpretation

The 2020–2025 period is a disclosed known comparison, not independent
confirmation. The backward-adjusted representation is primary. The unadjusted
representation is sensitivity-only and cannot alter finalist identity.

No finalist is accepted as a confirmed trading edge by this record.

## Frozen output files

- `PHASE_C_COMPLETE.json` — 1,319 bytes — `7df37817253333f1960a0fbe96dd2c4dc8e5af2204766a1121d35a37d1a23b05`
- `annual_results.csv` — 3,714 bytes — `ce3b489daf6c47b27e510b3d4c5086d60d0d512b1c98039f25959c5b914b6392`
- `assets/drawdown_curves.png` — 362,808 bytes — `b8e2d570c81b1451996eed31a9204ad3dfd0c451b28c5d74033e69045362d566`
- `assets/equity_curves.png` — 205,202 bytes — `c0db2fa8f3bca3e4e18ec92510c4353d74a69e6fc73d49d4e9afc8a1e17f0dd6`
- `cost_sensitivity.csv` — 1,990 bytes — `277cad1090024860fa3233b251129cf76ede643b60fa016ff48dbd772690ffa3`
- `drawdown_episodes.csv` — 12,561 bytes — `ce48212324a4d2e94138d13e7da4dbbb1039f01c573a34a08c5a5f1ab3b5e66f`
- `known_comparison_metrics.csv` — 5,362 bytes — `22da9e4599d5ccf912409adf3578cd9880e7db976ef21a0a204f9716a8e26fab`
- `known_comparison_summary.json` — 506 bytes — `c3a053fe074980187d5363c38376664dc30b3bb5954aaa67b531ea7ee92e1435`
- `monthly_results.csv` — 23,126 bytes — `973db92d1fb64a61536e0505fecc9f52080b0da4ebc2afbe5a2caee7308fe17b`
- `output_hashes.json` — 1,841 bytes — `c1a66777fa04fb69306ffe737cb15a1190051d0c1f9c34aa2a0b8542049a25c5`
- `report.html` — 14,048 bytes — `e2ca5cce5d6b01e64723f113c782d2146020a0636897ef807963a9312351e461`
- `report.md` — 4,226 bytes — `48b509018d1a16776130d395e8b4afe32db677e56ec81499a0de5d80b7d07e3a`
- `representation_sensitivity.csv` — 4,807 bytes — `e90449d02aa27d8461e43949f840cacaad6004bcdf3da46eb1385bd92c5f8657`
- `trade_distribution.csv` — 1,934 bytes — `a83ba336b79a136145edc63a7e3e20b9889645a50e5fce5888ae3f60df4b0060`

## Protected boundary

- Protected 2026 accessed: No
- Protected 2026 access authorised: No
- EXP-027 execution authorised: No
- New Databento download authorised: No
- Databento API calls: 0
- Network access: No
- Paper trading authorised: No
- Live trading authorised: No

EXP-026 remains pending a separate closure commit. That closure cannot
authorise protected 2026 access, EXP-027, paper trading or live trading.
