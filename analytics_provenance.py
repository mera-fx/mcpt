from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Iterable

from analytics_evidence_registry import (
    AnalyticsSeriesSpec,
    ExperimentEvidenceSpec,
    all_series,
)


ALLOWED_EVIDENCE_ROOTS = {"data", "results"}
ROBUSTNESS_SUFFIXES = {".csv", ".json", ".md", ".txt"}
ROBUSTNESS_TOKENS = (
    "annual",
    "bootstrap",
    "cost_sensitivity",
    "decision",
    "grid",
    "mcpt",
    "monthly",
    "result",
    "review",
    "robust",
    "sensitivity",
    "walk_forward",
    "walkforward",
    "yearly",
)


@dataclass(frozen=True)
class EvidenceRecord:
    path: str
    sha256: str
    size_bytes: int
    roles: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "roles": list(self.roles),
        }


@dataclass(frozen=True)
class EvidenceInventory:
    records: tuple[EvidenceRecord, ...]
    robustness_by_series: dict[str, tuple[str, ...]]

    @property
    def record_map(self) -> dict[str, EvidenceRecord]:
        return {record.path: record for record in self.records}

    @property
    def digest(self) -> str:
        payload = [
            record.to_dict()
            for record in self.records
        ]
        encoded = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


def sha256_file(path: Path, *, chunk_size: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def _project_relative(project_dir: Path, path: Path) -> Path:
    root = project_dir.resolve()
    resolved = path.resolve()
    try:
        relative = resolved.relative_to(root)
    except ValueError as error:
        raise ValueError(
            f"Evidence path escapes the project directory: {path}."
        ) from error
    if not relative.parts or relative.parts[0] not in (
        ALLOWED_EVIDENCE_ROOTS
    ):
        raise ValueError(
            f"Unsupported frozen-evidence root: {relative}."
        )
    if "analytics_expansion" in {
        part.lower()
        for part in relative.parts
    }:
        raise ValueError(
            "Generated analytics output cannot become frozen input."
        )
    return relative


def _is_robustness_artifact(path: Path) -> bool:
    if path.suffix.lower() not in ROBUSTNESS_SUFFIXES:
        return False
    name = path.name.lower()
    if not any(token in name for token in ROBUSTNESS_TOKENS):
        return False
    if (
        any(token in name for token in ("trade", "equity"))
        and not any(
            token in name
            for token in ("annual", "monthly", "yearly")
        )
    ):
        return False
    return True


def _experiment_robustness_candidates(
    project_dir: Path,
    experiment_id: str,
) -> tuple[Path, ...]:
    result_root = project_dir / "results"
    experiment_root = result_root / experiment_id
    candidates: set[Path] = set()
    if experiment_root.is_dir():
        candidates.update(
            path
            for path in experiment_root.rglob("*")
            if path.is_file() and _is_robustness_artifact(path)
        )
    if result_root.is_dir():
        candidates.update(
            path
            for path in result_root.glob(f"{experiment_id}*")
            if path.is_file() and _is_robustness_artifact(path)
        )
    return tuple(
        sorted(
            candidates,
            key=lambda path: path.as_posix().lower(),
        )
    )


def _matches_series_scope(
    project_dir: Path,
    path: Path,
    series: AnalyticsSeriesSpec,
) -> bool:
    relative = _project_relative(project_dir, path)
    parts = [part.lower() for part in relative.parts]

    if "candidates" in parts:
        position = parts.index("candidates")
        if position + 1 >= len(parts):
            return False
        if not series.candidate_id:
            return False
        if parts[position + 1] != series.candidate_id.lower():
            return False

    if "rows" in parts:
        position = parts.index("rows")
        variant_parts = [
            part.lower()
            for part in series.variant_id.split("/")
        ]
        scoped_parts = parts[
            position + 1 : position + 1 + len(variant_parts)
        ]
        if scoped_parts != variant_parts:
            return False

    return True


def discover_robustness_paths(
    project_dir: Path,
    series: AnalyticsSeriesSpec,
    *,
    candidates: Iterable[Path] | None = None,
) -> tuple[Path, ...]:
    available = (
        tuple(candidates)
        if candidates is not None
        else _experiment_robustness_candidates(
            project_dir,
            series.experiment_id,
        )
    )
    return tuple(
        path
        for path in available
        if _matches_series_scope(project_dir, path, series)
    )


def build_evidence_inventory(
    project_dir: Path,
    registry: dict[str, ExperimentEvidenceSpec],
) -> EvidenceInventory:
    project_dir = project_dir.resolve()
    roles_by_path: dict[Path, set[str]] = {}
    robustness_by_series: dict[str, tuple[str, ...]] = {}
    candidates_by_experiment = {
        experiment_id: _experiment_robustness_candidates(
            project_dir,
            experiment_id,
        )
        for experiment_id in registry
    }

    def register(path: Path, role: str) -> str:
        relative = _project_relative(project_dir, path)
        absolute = project_dir / relative
        if not absolute.is_file():
            raise FileNotFoundError(
                f"Missing frozen analytics evidence: {absolute}"
            )
        roles_by_path.setdefault(relative, set()).add(role)
        return relative.as_posix()

    for series in all_series(registry):
        register(
            project_dir / series.trades_path,
            "trade_ledger",
        )
        register(
            project_dir / series.equity_path,
            "equity_series",
        )
        for path in series.benchmark_paths:
            register(project_dir / path, "benchmark")

        robustness = discover_robustness_paths(
            project_dir,
            series,
            candidates=candidates_by_experiment[
                series.experiment_id
            ],
        )
        robustness_by_series[series.series_id] = tuple(
            register(path, "existing_robustness")
            for path in robustness
        )

    records = tuple(
        EvidenceRecord(
            path=relative.as_posix(),
            sha256=sha256_file(project_dir / relative),
            size_bytes=(project_dir / relative).stat().st_size,
            roles=tuple(sorted(roles)),
        )
        for relative, roles in sorted(
            roles_by_path.items(),
            key=lambda item: item[0].as_posix().lower(),
        )
    )
    return EvidenceInventory(
        records=records,
        robustness_by_series=robustness_by_series,
    )


def assert_evidence_unchanged(
    before: EvidenceInventory,
    after: EvidenceInventory,
) -> None:
    before_records = {
        record.path: (
            record.sha256,
            record.size_bytes,
            record.roles,
        )
        for record in before.records
    }
    after_records = {
        record.path: (
            record.sha256,
            record.size_bytes,
            record.roles,
        )
        for record in after.records
    }
    if before_records == after_records:
        return

    changed = sorted(
        path
        for path in before_records.keys() | after_records.keys()
        if before_records.get(path) != after_records.get(path)
    )
    preview = ", ".join(changed[:8])
    if len(changed) > 8:
        preview += f", and {len(changed) - 8} more"
    raise RuntimeError(
        "Frozen analytics evidence changed during the read-only "
        f"build: {preview}."
    )


def records_for_series(
    inventory: EvidenceInventory,
    series: AnalyticsSeriesSpec,
) -> tuple[EvidenceRecord, ...]:
    wanted = {
        series.trades_path.as_posix(),
        series.equity_path.as_posix(),
        *(path.as_posix() for path in series.benchmark_paths),
        *inventory.robustness_by_series.get(series.series_id, ()),
    }
    return tuple(
        record
        for record in inventory.records
        if record.path in wanted
    )
