# EXP-019 Closure Report

**Closed:** 2026-07-25

**Lifecycle status:** `REVIEW`

**Classification:** `QUALIFIED_WITH_KNOWN_PROVIDER_CONDITIONS`

## Purpose

EXP-019 created and audited a date-bounded archive of exact quarterly NQ
one-minute contracts from Databento `GLBX.MDP3`. It did not construct a
continuous contract or run a trading strategy.

## Acquisition result

| Measure | Result |
|---|---:|
| Exact quarterly contracts | 66 |
| Historical range | 2010-06-06 to 2026-07-24 exclusive |
| Successful downloads | 66 |
| Automatic retries | 0 |
| Attempted estimated cost | $22.914097756145 |
| Maximum authorised cost | $35.00 |
| Compressed archive size | 104,491,346 bytes |
| Archive digest | `225a64dc06cb6bb303fd83d186f2e7d81e2a8a8bec44382380c8ccc1b0b6baa3` |

## Read-only local audit result

| Measure | Result |
|---|---:|
| Classification | `QUALIFIED_WITH_KNOWN_PROVIDER_CONDITIONS` |
| Contracts audited | 66 |
| Records audited | 6,276,486 |
| Locked hard checks | 17 |
| Hard failures | 0 |
| Known provider-warning windows | 16 |
| Missing-minute runs measured | 330,174 |
| Largest missing-minute run | 5,808 minutes |
| Adjacent contract pairs measured | 65 |
| Overlapping timestamps | 807,158 |
| Databento API calls during audit | 0 |
| Archive files modified | No |

All locked integrity, DBN readability, timestamp, OHLCV, volume and
quarter-point tick checks passed.

The missing-minute and overlap figures are diagnostics, not a continuous-series
construction rule. Known provider-condition warnings remain part of the
evidence and must be disclosed in later work.

## Frozen evidence hashes

| File | SHA-256 |
|---|---|
| Acquisition manifest | `f8fbac395bbe7f9cdafd0187a00c3d77ee8f6ded31d7ba6870d6ed3c8e3007b3` |
| Acquisition completion marker | `ef8ad499e62284d872edfd480e7aa635a26340e85ba1d74d98a51ed80f71f935` |
| Audit summary | `e02b3e6d67715fbdfa2c42677225ce74cdf444b8d14cbf93a80e897fbca18287` |
| Audited contract table | `540008d208cf1d4f35d3b2cdbdb1eda71f25b18bb931c9c4091cfdad29548b11` |
| Adjacent overlap table | `e07d8cd41a0ae2544d1adb786fa50680a595f5c479ca699ff044d29991d26e7f` |
| Audit report | `172719fee061f133dce5a4755caa29e29b48d8984065cb43df4c6ab93eb043da` |
| Audit completion marker | `4f4f224531d3de440e20d9da600e93c6a0427ddec04b70e507005aecf67075b8` |

## Interpretation boundary

EXP-019 establishes that the acquired exact-contract archive passed its
preregistered structural audit with known provider conditions.

It does not establish:

- exchange-verified accuracy;
- selection of the best data vendor;
- a roll rule;
- a back-adjustment or forward-adjustment method;
- a completed continuous contract;
- a tested strategy edge;
- permission for paper or live trading.

EXP-019 is frozen. Any continuous-series construction, adjustment method or
strategy research requires a separately preregistered new experiment ID.
