from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any


def _safe_error(exc: BaseException) -> str:
    text = f"{type(exc).__name__}: {exc}"
    secret = os.environ.get("LSE_API_KEY")
    if secret:
        text = text.replace(secret, "<redacted>")
    return text[:1000]


def download_window(
    *,
    window_id: str,
    start: str,
    end: str,
    destination: Path,
) -> dict[str, Any]:
    key = os.environ.get("LSE_API_KEY")
    if not key:
        raise RuntimeError(
            "LSE_API_KEY is not set. Supply it only through the current "
            "PowerShell environment."
        )

    from lse import LSE

    destination.mkdir(parents=True, exist_ok=False)
    client = LSE()
    output = client.history(
        "NQ.F",
        dataset="futures",
        timeframe="1m",
        start=start,
        end=end,
        dest=str(destination),
        dataframe=False,
        poll_seconds=1.5,
        timeout=1800.0,
    )
    path = Path(output).resolve()
    destination_resolved = destination.resolve()
    if destination_resolved not in path.parents:
        raise RuntimeError("The client wrote outside the locked destination.")
    if not path.is_file():
        raise RuntimeError("The official client did not return a Parquet file.")
    if path.suffix.lower() != ".parquet":
        raise RuntimeError("The official client returned a non-Parquet artifact.")

    return {
        "window_id": window_id,
        "symbol": "NQ.F",
        "dataset": "futures",
        "timeframe": "1m",
        "start": start,
        "end": end,
        "path": str(path),
        "size_bytes": int(path.stat().st_size),
        "remote_method": "history",
        "catalog_called": False,
        "strategy_called": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--window-id", required=True)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()

    try:
        result = download_window(
            window_id=args.window_id,
            start=args.start,
            end=args.end,
            destination=args.destination,
        )
        print(json.dumps(result, allow_nan=False))
    except Exception as exc:
        print(_safe_error(exc), file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
