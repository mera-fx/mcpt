# EXP-024 Evidence-Only Recovery Authorization

**Authorization ID:** `EXP-024-EVIDENCE-RECOVERY-AUTH-001`

**Locked implementation commit:** `a57ebcbc237e2e8e8696e9d6b3b13f584102beee`

**Attempt-002 failure commit:** `7acf180c9640079c560c992a00c4fd413f3b13b7`

**Authorization record SHA-256:** `8d5b319b8550dcf12ebb616905a15793209eb996ee49663191ab8607671c3c7c`

## Authorized action

One evidence-only publication recovery is authorized. The protected runner may
verify and read the nine hash-locked attempt-002 artifacts, create the five
missing publication files, verify the original nine artifacts remain
unchanged, and atomically rename the partial directory to the final directory.

## Locked result

- Classification: `ATTRIBUTION_DIAGNOSTIC_NOT_QUALIFIED`
- Candidate-session rows: 51
- Quantower reference rebuild matches: 8/51
- Quantower reference rebuild failures: 43
- Transfer rebuild matches: 51/51
- Unresolved rows: 43

## Prohibited actions

This authorization does not permit:

- reading market Parquet files;
- reconstructing features or recalculating attribution;
- rebuilding charts;
- network or Databento API access;
- retrying attempt 001 or attempt 002;
- strategy replay or performance evaluation;
- optimization, MCPT, bootstrap or walk-forward analysis;
- selecting a source or candidate winner;
- paper or live trading.

## Execution sequence

1. Commit and push this authorization separately.
2. Run the protected authorized preflight.
3. Run the evidence-only recovery exactly once with the explicit confirmation
   flag.
4. Never rerun the recovery after success.
