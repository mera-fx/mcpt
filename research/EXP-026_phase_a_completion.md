# EXP-026 Phase A Completion Record

**Experiment:** EXP-026

**Phase:** A — Development

**Completion date:** 2026-07-28

**Status:** `COMPLETED`

**Implementation commit:** `13ee0683dfcbbb5d763f7254f3b245ecc8e6d9cd`

**Authorisation commit:** `5fa417ed56c2d620c5d348e9ab43f3d7634518b8`

**Recovery commit:** `d54289659ffa058ae31558ad3b99b646c31d0bf7`

**Completion-record SHA-256:** `79899140135d5d4aba92c0f7aa7056dce6a0540f9e48d2e70383e7c4cc5ecf40`

## Completed evidence

- Source sessions: `2010-06-07` through `2017-12-31`
- Reported candidates: 24
- Development candidates: 22
- Fixed controls: 2
- Decision rows: 46,584
- Completed trades: 11,502
- Independent deterministic rebuild: Yes
- Selected survivors: 6

## Frozen Phase A survivors

- `gap_fade_0p75_1r`
- `gap_fade_0p25_1r`
- `opening_drive_0p75_1p5r`
- `opening_drive_0p75_time`
- `premarket_continuation_0p875_1p5r`
- `premarket_continuation_0p625_1p5r`

These are exploratory development survivors. They are not validated trading
edges and do not authorise Phase B, Phase C, EXP-027, paper trading or live
trading.

## Recovery disclosure

The authorised Phase A computation completed both independent calculations and
wrote five result files. Report generation then failed because the optional
`tabulate` package was absent.

Recovery `EXP-026-A-R1` generated only `report.md`, `output_hashes.json` and
`PHASE_A_COMPLETE.json` from the hash-locked existing evidence. Recovery did
not read market values, replay strategies, alter candidates, alter parameters
or repeat selection.

## Frozen output files

- `development_summary.json` — 567 bytes — `4a18a93c22eeefbf2d4cc028bdb8c36bc6e49dd1ab2a5dbf675a0b10b3910caf`
- `candidate_registry.csv` — 2,997 bytes — `325c043aecdbf498f994da07975cf09bb8b44f48812028014aef9998cfe4010f`
- `development_metrics.csv` — 24,066 bytes — `5bd340778f3baa239298bc0f79e7cc9b184f820f9a852be6b081106a1a7df45f`
- `development_annual_results.csv` — 22,801 bytes — `753cf86ccb3f6dd0eba9698edd36facdc5b416a035992bdd5cd7385883865146`
- `phase_a_survivors.json` — 502 bytes — `e9d940a3c247d885d1ea7537a7673ce67a15517ef79ba18ef5d243096a5f27cf`
- `output_hashes.json` — 952 bytes — `6406c73e0944fdde3a4087f9fde98740210c4ec4bbebd97a888aaeb1ccad962b`
- `report.md` — 9,788 bytes — `0d4fe9e17105c117bdfd54f70f4658ac552fd6bbff3bdc9515900b8375bd6d18`
- `PHASE_A_COMPLETE.json` — 1,275 bytes — `c39eb9eb0f5093bc8b6e3135b280af27be8b229bd577d2bd59828e91447b3342`

## Protected boundary

- Phase B execution authorised: No
- Phase C execution authorised: No
- Protected 2026 accessed: No
- Protected 2026 access authorised: No
- New Databento download authorised: No
- Databento API calls: 0
- Network access: No
- Paper trading authorised: No
- Live trading authorised: No
