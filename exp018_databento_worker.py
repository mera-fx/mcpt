from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any


def _safe_error(exc: BaseException) -> str:
    text = f"{type(exc).__name__}: {exc}"
    secret = os.environ.get("DATABENTO_API_KEY")
    if secret:
        text = text.replace(secret, "<redacted>")
    return text[:1000]


def estimate_cost(
    *,
    raw_symbol: str,
    start: str,
    end: str,
) -> float:
    import databento as db

    client = db.Historical()
    return float(
        client.metadata.get_cost(
            dataset="GLBX.MDP3",
            symbols=[raw_symbol],
            schema="ohlcv-1m",
            stype_in="raw_symbol",
            start=start,
            end=end,
        )
    )


def download(
    *,
    raw_symbol: str,
    expected_instrument_id: int,
    start: str,
    end: str,
    destination: Path,
) -> dict[str, Any]:
    key = os.environ.get("DATABENTO_API_KEY")
    if not key:
        raise RuntimeError(
            "DATABENTO_API_KEY is not set. Supply it only through the "
            "current PowerShell environment."
        )

    import databento as db

    destination = destination.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise RuntimeError("The locked destination already exists.")

    partial = destination.with_name(
        destination.stem + ".partial" + destination.suffix
    )
    if partial.exists():
        raise RuntimeError("A partial artifact already exists; review required.")

    client = db.Historical()
    client.timeseries.get_range(
        dataset="GLBX.MDP3",
        symbols=[raw_symbol],
        schema="ohlcv-1m",
        stype_in="raw_symbol",
        stype_out="instrument_id",
        start=start,
        end=end,
        path=str(partial),
    )

    if not partial.is_file() or partial.stat().st_size <= 0:
        raise RuntimeError("Databento did not produce a non-empty DBN file.")
    partial.replace(destination)

    return {
        "raw_symbol": raw_symbol,
        "expected_instrument_id": expected_instrument_id,
        "dataset": "GLBX.MDP3",
        "schema": "ohlcv-1m",
        "stype_in": "raw_symbol",
        "stype_out": "instrument_id",
        "start": start,
        "end": end,
        "path": str(destination),
        "size_bytes": int(destination.stat().st_size),
        "remote_method": "timeseries.get_range",
        "batch_called": False,
        "continuous_symbol_used": False,
        "strategy_called": False,
    }


def extract(
    *,
    source: Path,
    destination: Path,
) -> dict[str, Any]:
    import databento as db
    import numpy as np

    source = source.resolve()
    destination = destination.resolve()
    if not source.is_file():
        raise RuntimeError("The DBN source file is missing.")
    destination.parent.mkdir(parents=True, exist_ok=True)

    store = db.read_dbn(source)
    array = store.to_ndarray()
    names = set(array.dtype.names or ())
    required = {
        "ts_event",
        "publisher_id",
        "instrument_id",
        "open",
        "high",
        "low",
        "close",
        "volume",
    }
    missing = sorted(required - names)
    if missing:
        raise RuntimeError(
            "DBN OHLCV extraction is missing fields: " + ", ".join(missing)
        )

    temporary = destination.with_suffix(destination.suffix + ".tmp")
    with temporary.open("wb") as handle:
        np.savez_compressed(
            handle,
            ts_event=array["ts_event"].astype("uint64", copy=False),
            publisher_id=array["publisher_id"].astype("uint16", copy=False),
            instrument_id=array["instrument_id"].astype("uint32", copy=False),
            open=array["open"].astype("int64", copy=False),
            high=array["high"].astype("int64", copy=False),
            low=array["low"].astype("int64", copy=False),
            close=array["close"].astype("int64", copy=False),
            volume=array["volume"].astype("uint64", copy=False),
        )
    temporary.replace(destination)

    return {
        "source": str(source),
        "destination": str(destination),
        "rows": int(len(array)),
        "fields": sorted(required),
        "prices_preserved_as_raw_int64": True,
        "timestamps_preserved_as_uint64_nanoseconds": True,
        "vendor_rows_written_only_to_ignored_local_path": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="mode", required=True)

    cost_parser = subparsers.add_parser("estimate-cost")
    cost_parser.add_argument("--raw-symbol", required=True)
    cost_parser.add_argument("--start", required=True)
    cost_parser.add_argument("--end", required=True)

    download_parser = subparsers.add_parser("download")
    download_parser.add_argument("--raw-symbol", required=True)
    download_parser.add_argument("--instrument-id", type=int, required=True)
    download_parser.add_argument("--start", required=True)
    download_parser.add_argument("--end", required=True)
    download_parser.add_argument("--destination", type=Path, required=True)

    extract_parser = subparsers.add_parser("extract")
    extract_parser.add_argument("--source", type=Path, required=True)
    extract_parser.add_argument("--destination", type=Path, required=True)

    args = parser.parse_args()
    try:
        if args.mode == "estimate-cost":
            result = {
                "estimated_cost_usd": estimate_cost(
                    raw_symbol=args.raw_symbol,
                    start=args.start,
                    end=args.end,
                )
            }
        elif args.mode == "download":
            result = download(
                raw_symbol=args.raw_symbol,
                expected_instrument_id=args.instrument_id,
                start=args.start,
                end=args.end,
                destination=args.destination,
            )
        else:
            result = extract(
                source=args.source,
                destination=args.destination,
            )
        print(json.dumps(result, allow_nan=False))
    except Exception as exc:
        print(_safe_error(exc), file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
