# Historical Market Data Policy

**Effective date:** 2026-07-27

## Primary historical source

Databento is the primary historical market-data source for future strategy
research involving NQ, MNQ and other supported futures markets.

Historical research includes strategy discovery, parameter comparison,
optimization, fixed-rule backtesting, walk-forward testing, MCPT, bootstrap,
robustness analysis and exact-contract diagnostics.

## Contract identity

Exact quarterly contracts are preferred as the raw source whenever contract
identity can affect signals, prices, rolls or execution.

Raw files must retain:

- the explicit contract symbol;
- the provider instrument identity where available;
- acquisition or archive metadata;
- file size and SHA-256;
- resolution and timezone;
- the exact permitted research period.

Generic or continuous symbols with undocumented construction must not be treated
as exact-contract evidence.

## Continuous series

A continuous series used for research must be built from explicit contracts
using a documented and reproducible rule.

Each construction must state:

- the eligible contracts;
- the roll trigger;
- the selected roll session;
- whether prices are adjusted;
- the adjustment method;
- how signals and executions are assigned around the roll.

Provider-managed continuous history may be used only when its construction is
known and explicitly accepted by the experiment preregistration.

## Databento access

Existing frozen Databento archives may be reused only within the access boundary
of the relevant experiment.

This policy does not itself authorise:

- a new Databento API request;
- a new historical download;
- access to protected or out-of-sample periods;
- a change to a frozen roll rule;
- a change to a frozen strategy or parameter set.

Those actions require a separate experiment or data-acquisition authorisation.

## Quantower and Lucid/Rithmic

Quantower and Lucid/Rithmic remain appropriate for:

- current-market observation;
- platform and execution compatibility checks;
- paper execution after separate authorisation;
- live execution only after separate authorisation;
- limited cross-provider validation when separately preregistered.

They are not the default historical research source when expired contract
identity is unavailable or the construction of a generic symbol is undocumented.

## Existing experiments

All completed and frozen experiments retain their original data sources,
assumptions, results and conclusions.

This policy does not retrospectively alter, rescue, reject or rerun an existing
experiment.

## Trading boundary

Using Databento for historical research does not authorise paper trading, live
trading, order API access or capital deployment.
