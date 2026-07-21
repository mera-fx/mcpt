# EXP-016 Timestamp Schema Correction

**Basis:** vendor Parquet schema inspection only

**Vendor market values inspected:** no

**Audit result created:** no

**Remote request performed:** no

The six downloaded Parquet samples consistently expose their timestamp as a
timezone-aware UTC field named `ts`. The original canonical parser supported
several timestamp aliases but did not include `ts`, causing the local audit to
stop before any result files were created.

This pre-result correction adds `ts` as an accepted timestamp alias. It does
not infer a timezone: timezone-aware values are preserved and naive `ts`
values remain unresolved.

The sample files, hashes, fixed windows, Quantower reference, measurement
definitions, qualification thresholds, methodology limits, request counts,
strategy prohibitions and paper/live trading prohibitions remain unchanged.
