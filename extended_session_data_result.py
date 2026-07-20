from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from extended_session_data import (
    AUDIT_FILE,
    OUTPUT_FILES,
    SESSION_QUALITY_FILE,
    SOURCE_MANIFEST_FILE,
)


PROJECT_DIR = Path(__file__).resolve().parent
TRACKED_RESULT_FILE = (
    PROJECT_DIR
    / "research"
    / "EXTENDED_SESSION_DATA_RESULT.json"
)

EXPECTED_IMPLEMENTATION_COMMIT = (
    "73dc3650ad5d3ebffd817fe5b2851729b03fe7d4"
)
EXPECTED_AUDIT_SHA256 = (
    "3bc9218afbff654fa6aa006cd3242ecc0b232ae324255166625e67dc800ff775"
)
EXPECTED_SESSION_QUALITY_SHA256 = (
    "6b55077783ad2c1cd8ef99f10d50ed7d691aad7cafcdb7e8fa37639d90724712"
)
EXPECTED_SOURCE_MANIFEST_SHA256 = (
    "f9ef1694625b4dbbdda00b6c416b6a799952d7ac871135a784d8bc7aef9e3374"
)
EXPECTED_OUTPUTS = {
    "NQ_1m": {
        "rows": 1_849_560,
        "sha256": (
            "b1679f833d03c2f2aedeaf4ec442a34a284edd307942e13918a0488c71a669cc"
        ),
    },
    "MNQ_1m": {
        "rows": 1_849_560,
        "sha256": (
            "30156c6c1af559833ffb10ca84d99680bb9f8d572c37bdc5d15e2da925fba285"
        ),
    },
    "NQ_5m": {
        "rows": 369_912,
        "sha256": (
            "06598e2dd4cf2b89cd6777fb85881db7feb00faa0a5b4cda435e664a4c3c660a"
        ),
    },
    "MNQ_5m": {
        "rows": 369_912,
        "sha256": (
            "c8cda74e0b87a0386c500ec5f40ee4966b2542c64f885212c34d4a1b9a7b2ec7"
        ),
    },
}
EXPECTED_YEAR_COUNTS = {
    2019: {
        "total": 162,
        "complete_aligned": 13,
        "nq_complete": 119,
        "mnq_complete": 13,
    },
    2020: {
        "total": 246,
        "complete_aligned": 221,
        "nq_complete": 227,
        "mnq_complete": 230,
    },
    2021: {
        "total": 250,
        "complete_aligned": 224,
        "nq_complete": 225,
        "mnq_complete": 246,
    },
    2022: {
        "total": 248,
        "complete_aligned": 233,
        "nq_complete": 233,
        "mnq_complete": 246,
    },
    2023: {
        "total": 246,
        "complete_aligned": 215,
        "nq_complete": 215,
        "mnq_complete": 244,
    },
    2024: {
        "total": 248,
        "complete_aligned": 216,
        "nq_complete": 216,
        "mnq_complete": 248,
    },
    2025: {
        "total": 239,
        "complete_aligned": 222,
        "nq_complete": 222,
        "mnq_complete": 237,
    },
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(block)
    return digest.hexdigest()


def _read_json(path: Path) -> Any:
    return json.loads(
        Path(path).read_text(encoding="utf-8")
    )


def _verify_tracked_result(
    path: Path,
) -> dict[str, Any]:
    value = _read_json(path)
    if not isinstance(value, dict):
        raise ValueError(
            "Tracked extended-session result must be an object."
        )
    required = {
        "dataset",
        "status",
        "implementation_commit",
        "complete_aligned_sessions",
        "excluded_incomplete_sessions",
        "first_included_session",
        "last_included_session",
        "outputs",
        "year_counts",
        "research_boundary",
    }
    missing = required.difference(value)
    if missing:
        raise ValueError(
            "Tracked extended-session result is missing: "
            f"{sorted(missing)}"
        )
    if (
        value["implementation_commit"]
        != EXPECTED_IMPLEMENTATION_COMMIT
    ):
        raise ValueError(
            "Extended-session implementation commit changed."
        )
    if value["outputs"] != EXPECTED_OUTPUTS:
        raise ValueError(
            "Tracked extended-session output measurements changed."
        )
    tracked_years = {
        int(year): counts
        for year, counts in value["year_counts"].items()
    }
    if tracked_years != EXPECTED_YEAR_COUNTS:
        raise ValueError(
            "Tracked extended-session year counts changed."
        )
    boundary = value["research_boundary"]
    if (
        boundary.get("strategy_results_calculated") is not False
        or boundary.get("optimization_calculated") is not False
        or boundary.get("mcpt_calculated") is not False
        or boundary.get("missing_bars_filled") is not False
        or boundary.get("trading_authorized") is not False
    ):
        raise ValueError(
            "Extended-session research boundary changed."
        )
    return value


def _verify_year_counts(
    path: Path,
) -> None:
    frame = pd.read_csv(path)
    frame["year"] = pd.to_datetime(
        frame["session_date"]
    ).dt.year
    actual: dict[int, dict[str, int]] = {}
    for year, group in frame.groupby("year", sort=True):
        actual[int(year)] = {
            "total": int(len(group)),
            "complete_aligned": int(
                group["complete_aligned"].astype(bool).sum()
            ),
            "nq_complete": int(
                group["nq_missing_rows"].eq(0).sum()
            ),
            "mnq_complete": int(
                group["mnq_missing_rows"].eq(0).sum()
            ),
        }
    if actual != EXPECTED_YEAR_COUNTS:
        raise ValueError(
            "Local extended-session year counts changed."
        )


def verify_extended_session_data_result(
    *,
    tracked_result_path: Path = TRACKED_RESULT_FILE,
    audit_path: Path = AUDIT_FILE,
    session_quality_path: Path = SESSION_QUALITY_FILE,
    source_manifest_path: Path = SOURCE_MANIFEST_FILE,
    output_files: Mapping[str, Path] = OUTPUT_FILES,
) -> dict[str, Any]:
    tracked = _verify_tracked_result(
        Path(tracked_result_path)
    )
    audit_path = Path(audit_path)
    session_quality_path = Path(session_quality_path)
    source_manifest_path = Path(source_manifest_path)

    if sha256_file(audit_path) != EXPECTED_AUDIT_SHA256:
        raise ValueError(
            "Local extended-session audit hash changed."
        )
    if (
        sha256_file(session_quality_path)
        != EXPECTED_SESSION_QUALITY_SHA256
    ):
        raise ValueError(
            "Local extended-session quality hash changed."
        )
    if (
        sha256_file(source_manifest_path)
        != EXPECTED_SOURCE_MANIFEST_SHA256
    ):
        raise ValueError(
            "Local extended-session source manifest hash changed."
        )

    audit = _read_json(audit_path)
    if (
        audit.get("complete_aligned_sessions") != 1_344
        or audit.get("excluded_incomplete_sessions") != 295
        or audit.get("first_included_session") != "2019-08-02"
        or audit.get("last_included_session") != "2025-12-31"
    ):
        raise ValueError(
            "Local extended-session audit summary changed."
        )
    if (
        audit.get("strategy_results_calculated") is not False
        or audit.get("optimization_calculated") is not False
        or audit.get("mcpt_calculated") is not False
        or audit.get("cash_session_data_changed") is not False
        or audit.get("source_files_edited") is not False
    ):
        raise ValueError(
            "Local extended-session safety boundary changed."
        )

    if set(output_files) != set(EXPECTED_OUTPUTS):
        raise ValueError(
            "Extended-session output file set changed."
        )
    for name, expected in EXPECTED_OUTPUTS.items():
        path = Path(output_files[name])
        if not path.exists():
            raise FileNotFoundError(
                f"Extended-session output is missing: {path}"
            )
        if sha256_file(path) != expected["sha256"]:
            raise ValueError(
                f"{name} extended-session output hash changed."
            )
        if audit["outputs"][name]["rows"] != expected["rows"]:
            raise ValueError(
                f"{name} extended-session row count changed."
            )

    _verify_year_counts(session_quality_path)
    return tracked


if __name__ == "__main__":
    verify_extended_session_data_result()
    print(
        "Local extended-session data foundation is frozen and valid."
    )
