from __future__ import annotations

import argparse
from importlib import metadata
import inspect
import json
import os
from pathlib import Path
import sys
from typing import Any


DUMMY_KEY = "EXP015_NON_SECRET_IMPORT_PROBE"


def _atomic_json(payload: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, allow_nan=False),
        encoding="utf-8",
    )
    temporary.replace(path)


def _safe_error(exc: BaseException) -> str:
    text = f"{type(exc).__name__}: {exc}"
    secret = os.environ.get("LSE_API_KEY")
    if secret:
        text = text.replace(secret, "<redacted>")
    return text[:1000]


def probe_client() -> dict[str, Any]:
    # A real key is explicitly ignored for the import/constructor probe.
    os.environ.pop("LSE_API_KEY", None)

    from lse import LSE

    client = LSE(api_key=DUMMY_KEY)
    signature = str(inspect.signature(LSE))
    result = {
        "status": "PASS",
        "distribution": "lse-data",
        "version": metadata.version("lse-data"),
        "python_version": sys.version.split()[0],
        "class_name": type(client).__name__,
        "constructor_signature": signature,
        "dummy_key_used": True,
        "real_api_key_used": False,
        "network_market_data_call": False,
    }
    del client
    return result


def fetch_futures_catalog(output: Path) -> None:
    key = os.environ.get("LSE_API_KEY")
    if not key:
        raise RuntimeError(
            "LSE_API_KEY is not set. Set it in the current PowerShell "
            "session without placing it in a file or command history."
        )

    from lse import LSE

    client = LSE()
    rows = client.catalog("futures")
    if not isinstance(rows, list):
        raise RuntimeError("The official client returned a non-list catalog.")

    _atomic_json(rows, output)


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--probe", action="store_true")
    group.add_argument("--catalog", type=Path)
    args = parser.parse_args()

    try:
        if args.probe:
            print(json.dumps(probe_client(), allow_nan=False))
        else:
            fetch_futures_catalog(args.catalog)
    except Exception as exc:
        print(_safe_error(exc), file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
