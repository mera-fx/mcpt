# EXP-005 Paper-Testing Plan

**Status:** Accepted for paper testing  
**Mode:** Offline end-of-day paper replay only  
**Markets:** NQ primary evidence, MNQ implementation shadow

## Observation requirement

Paper observation must continue until both conditions are satisfied:

- at least 12 calendar weeks; and
- at least 40 completed NQ paper trades.

## Daily workflow

After each completed trading session, export NQ and MNQ one-minute `Last`
data from Quantower using the existing Lucid/Rithmic provider. Timestamps
are interpreted as UTC. The paper processor may read only a completed
session and must not connect to an order API.

## Percentage reporting basis

Reports use fixed analytical reference capital:

- NQ: $100,000
- MNQ: $10,000

This creates an explicit denominator for return and drawdown percentage.
It is not a margin requirement and is not a live-account recommendation.

## What determines success

The paper phase primarily evaluates implementation fidelity, complete data,
deterministic rebuilds and exact audit reconciliation. Profit, Profit Factor,
win rate, return percentage and drawdown percentage are reported, but the
minimum paper period is too short to make any one of them a stand-alone
pass/fail test.

## Prohibited

No live orders, order API, leverage decision, parameter change, optimization,
new rule, historical rerun or editing of accepted paper records is permitted
under EXP-005.
