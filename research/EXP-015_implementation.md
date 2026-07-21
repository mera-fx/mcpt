# EXP-015 Protected Implementation

## Status

`IMPLEMENTED_NOT_RUN`

This implementation was prepared after the EXP-015 preregistration was
committed. It has not accessed the London Strategic Edge futures
catalog and has not downloaded market data.

## Locked external client

The implementation uses the official `lse-data` distribution:

- version: `0.14.0`;
- wheel: `lse_data-0.14.0-py3-none-any.whl`;
- wheel SHA-256:
  `b1e2f34af882ace2d8dab6fb5fe2b45d0bd6b1f1f39d95d71c3aeb4a56aac1a0`;
- source repository commit:
  `564c63dd99e3b447777cb396314ec6c4342f82ff`;
- declared dependency: `websockets>=11.0`.

The package remains outside the main project environment. The client
probe creates an isolated virtual environment inside the ignored
`data/EXP-015` directory, downloads the exact wheel, verifies its hash,
installs it there and constructs the client with a non-secret dummy key.

The probe removes `LSE_API_KEY` from its child environment and makes no
market-data request.

## Runner modes

`run_exp015_audit.py` supports exactly three mutually exclusive modes.

### `--preflight`

This validates:

- the EXP-015 preregistration;
- the protected implementation;
- all lifecycle stages;
- the frozen EXP-014 result;
- a clean committed Git state.

It performs no external request.

### `--probe-client`

This creates the isolated environment and verifies that `lse-data`
imports and constructs under the project machine's Python version.

It accesses PyPI only for package installation. It does not use an API
key and does not access market data.

### `--catalog`

This is the only mode that reads `LSE_API_KEY`. The key is inherited
from the current process and is never printed or written.

The isolated worker may call only:

```python
client.catalog("futures")
```

It cannot call candles, history, dataset, streaming or strategy code.

The catalog rows are canonicalized and retained for review. Candidate
discovery does not resolve identity automatically. Catalog-only output
cannot authorize history because the NQ/MNQ contract identity, roll
construction and price adjustment must still be evidenced.

## Output boundary

Generated probe and catalog files are written only beneath ignored
`data/` and `results/` directories.

No EXP-005 through EXP-014 data or result path is writable from the
implementation.

## Safety boundary

This implementation:

- does not replace frozen Quantower data;
- does not search strategies or parameters;
- does not download historical bars;
- does not replay a strategy;
- does not qualify all London Strategic Edge data;
- does not authorize paper or live trading.
