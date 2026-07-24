from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import io
import json
import os
from pathlib import Path
from typing import Any, Iterable, Mapping

from analytics_canonical_adapter import (
    load_canonical_benchmark,
    load_canonical_equity,
    load_canonical_trades,
)
from analytics_evidence_registry import (
    AnalyticsKind,
    BenchmarkSchema,
    ExperimentEvidenceSpec,
    MetricFamily,
    NOT_APPLICABLE_MESSAGE,
    all_series,
    validate_analytics_evidence_registry,
)
from analytics_metrics import (
    ANALYTICS_SCHEMA_VERSION,
    compute_series_analytics,
    json_safe,
    summary_row,
)
from analytics_provenance import (
    EvidenceInventory,
    assert_evidence_unchanged,
    build_evidence_inventory,
    records_for_series,
)
from analytics_reporting import (
    render_experiment_report,
    render_root_index,
    render_series_report,
    series_slug,
)


DEFAULT_OUTPUT_RELATIVE = Path("results") / "analytics_expansion"


@dataclass(frozen=True)
class AnalyticsBuildResult:
    output_dir: Path
    evidence_digest: str
    evidence_file_count: int
    strategy_series_count: int
    experiment_count: int
    files_written: int
    files_unchanged: int
    preflight_only: bool


class _Writer:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.written = 0
        self.unchanged = 0

    def _write_bytes(self, relative: Path, content: bytes) -> None:
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.is_file() and target.read_bytes() == content:
            self.unchanged += 1
            return
        temporary = target.with_name(f".{target.name}.tmp")
        temporary.write_bytes(content)
        os.replace(temporary, target)
        self.written += 1

    def json(self, relative: Path, payload: Any) -> None:
        safe = json_safe(payload)
        encoded = (
            json.dumps(
                safe,
                ensure_ascii=False,
                indent=2,
                allow_nan=False,
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8")
        self._write_bytes(relative, encoded)

    def text(self, relative: Path, content: str) -> None:
        normalized = content.replace("\r\n", "\n")
        self._write_bytes(relative, normalized.encode("utf-8"))

    def csv(
        self,
        relative: Path,
        rows: Iterable[Mapping[str, Any]],
    ) -> None:
        records = [
            dict(json_safe(row))
            for row in rows
        ]
        columns: list[str] = []
        for row in records:
            for column in row:
                if column not in columns:
                    columns.append(column)
        buffer = io.StringIO(newline="")
        writer = csv.DictWriter(
            buffer,
            fieldnames=columns,
            extrasaction="ignore",
            lineterminator="\n",
        )
        if columns:
            writer.writeheader()
            for row in records:
                serialized = {
                    column: _csv_value(row.get(column))
                    for column in columns
                }
                writer.writerow(serialized)
        self.text(relative, buffer.getvalue())


def _csv_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list)):
        return json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    return value


def _validate_output_dir(
    project_dir: Path,
    output_dir: Path,
) -> Path:
    project = project_dir.resolve()
    output = output_dir.resolve()
    try:
        relative = output.relative_to(project)
    except ValueError as error:
        raise ValueError(
            "Analytics output must remain inside the project directory."
        ) from error
    lowered = [part.lower() for part in relative.parts]
    if not lowered:
        raise ValueError(
            "The project directory cannot be used as analytics output."
        )
    if lowered[0] == "data":
        raise ValueError(
            "Analytics output cannot be written beneath frozen data."
        )
    if (
        len(lowered) >= 2
        and lowered[0] == "results"
        and lowered[1].startswith("exp-")
    ):
        raise ValueError(
            "Analytics output cannot be written inside a frozen "
            "experiment result directory."
        )
    if lowered[0] in {
        "paper_data",
        "paper_results",
        "paper_state",
    }:
        raise ValueError(
            "Analytics output cannot be written inside frozen paper "
            "evidence."
        )
    return output


def _selected_experiment_ids(
    registry: Mapping[str, ExperimentEvidenceSpec],
    requested: Iterable[str] | None,
) -> tuple[str, ...]:
    if requested is None:
        return tuple(sorted(registry))
    selected = tuple(
        sorted(
            {
                str(value).strip().upper()
                for value in requested
                if str(value).strip()
            }
        )
    )
    unknown = set(selected) - set(registry)
    if unknown:
        raise ValueError(
            "Unknown analytics experiment IDs: "
            + ", ".join(sorted(unknown))
        )
    return selected


def _robustness_records(
    inventory: EvidenceInventory,
    series_id: str,
) -> list[dict[str, Any]]:
    records = inventory.record_map
    return [
        records[path].to_dict()
        for path in inventory.robustness_by_series.get(
            series_id,
            (),
        )
    ]


def _calculate_results(
    project_dir: Path,
    registry: Mapping[str, ExperimentEvidenceSpec],
    selected: set[str],
    inventory: EvidenceInventory,
) -> dict[str, list[dict[str, Any]]]:
    calculated: dict[str, list[dict[str, Any]]] = {
        experiment_id: []
        for experiment_id in selected
    }
    for series in all_series(dict(registry)):
        if series.experiment_id not in selected:
            continue
        trades = load_canonical_trades(project_dir, series)
        equity = load_canonical_equity(project_dir, series)
        benchmark = (
            None
            if series.benchmark_schema == BenchmarkSchema.NONE
            else load_canonical_benchmark(project_dir, series)
        )
        evidence = [
            record.to_dict()
            for record in records_for_series(
                inventory,
                series,
            )
        ]
        result = compute_series_analytics(
            trades,
            equity,
            series,
            benchmark=benchmark,
            evidence_records=evidence,
            robustness_records=_robustness_records(
                inventory,
                series.series_id,
            ),
        )
        if not result["integrity"]["trade_equity_reconciled"]:
            raise ValueError(
                f"{series.series_id} trade and equity evidence do "
                "not reconcile under its declared reference-capital "
                "model."
            )
        calculated[series.experiment_id].append(result)
    for results in calculated.values():
        results.sort(
            key=lambda item: item["series"]["series_id"]
        )
    return calculated


def _write_series_tables(
    writer: _Writer,
    base: Path,
    result: Mapping[str, Any],
) -> None:
    families = result["metric_families"]
    for family_name, family in families.items():
        for table_name, rows in family.get("tables", {}).items():
            if not isinstance(rows, list):
                continue
            writer.csv(
                base
                / (
                    f"{family_name}--{table_name}"
                    ".csv"
                ),
                rows,
            )


def _data_source_payload(
    experiment: ExperimentEvidenceSpec,
) -> dict[str, Any]:
    return {
        "schema_version": ANALYTICS_SCHEMA_VERSION,
        "experiment": {
            "experiment_id": experiment.experiment_id,
            "experiment_name": experiment.experiment_name,
            "analytics_kind": experiment.analytics_kind.value,
        },
        "analysis_boundary": {
            "mode": "frozen_evidence_reporting_only",
            "strategy_rerun": False,
            "market_data_request": False,
        },
        "metric_families": {
            family.value: {
                "family": family.value,
                "status": "NOT_APPLICABLE",
                "message": NOT_APPLICABLE_MESSAGE,
                "metrics": {},
                "tables": {},
            }
            for family in MetricFamily
        },
    }


def _write_outputs(
    *,
    output_dir: Path,
    registry: Mapping[str, ExperimentEvidenceSpec],
    selected_ids: tuple[str, ...],
    calculated: Mapping[str, list[dict[str, Any]]],
    inventory: EvidenceInventory,
    output_root_label: str,
) -> _Writer:
    writer = _Writer(output_dir)
    selected = set(selected_ids)
    all_summary_rows: list[dict[str, Any]] = []
    series_index: list[dict[str, Any]] = []
    result_counts: dict[str, int] = {}

    for experiment_id in selected_ids:
        experiment = registry[experiment_id]
        experiment_results = calculated.get(experiment_id, [])
        result_counts[experiment_id] = len(experiment_results)
        experiment_dir = Path(experiment_id)

        if experiment.analytics_kind == AnalyticsKind.STRATEGY:
            summary_rows = [
                summary_row(result)
                for result in experiment_results
            ]
            all_summary_rows.extend(summary_rows)
            writer.csv(
                experiment_dir / "summary.csv",
                summary_rows,
            )
            for result in experiment_results:
                series = result["series"]
                slug = series_slug(series["series_id"])
                series_dir = experiment_dir / slug
                writer.json(
                    series_dir / "analytics.json",
                    result,
                )
                writer.text(
                    series_dir / "report.html",
                    render_series_report(result),
                )
                _write_series_tables(
                    writer,
                    series_dir,
                    result,
                )
                series_index.append(
                    {
                        **series,
                        "analytics_path": (
                            series_dir / "analytics.json"
                        ).as_posix(),
                        "report_path": (
                            series_dir / "report.html"
                        ).as_posix(),
                    }
                )
            writer.json(
                experiment_dir / "analytics.json",
                {
                    "schema_version": ANALYTICS_SCHEMA_VERSION,
                    "experiment": {
                        "experiment_id": experiment.experiment_id,
                        "experiment_name": experiment.experiment_name,
                        "analytics_kind": (
                            experiment.analytics_kind.value
                        ),
                    },
                    "series_count": len(experiment_results),
                    "series": [
                        item
                        for item in series_index
                        if item["experiment_id"] == experiment_id
                    ],
                    "summary": summary_rows,
                },
            )
        else:
            writer.json(
                experiment_dir / "analytics.json",
                _data_source_payload(experiment),
            )

        writer.text(
            experiment_dir / "report.html",
            render_experiment_report(
                experiment,
                experiment_results,
            ),
        )

    writer.csv(Path("summary.csv"), all_summary_rows)
    manifest = {
        "schema_version": ANALYTICS_SCHEMA_VERSION,
        "build_mode": "frozen_evidence_reporting_only",
        "output_root": output_root_label,
        "selected_experiments": list(selected_ids),
        "experiment_count": len(selected_ids),
        "strategy_series_count": len(series_index),
        "evidence_file_count": len(inventory.records),
        "evidence_digest_sha256": inventory.digest,
        "evidence": [
            record.to_dict()
            for record in inventory.records
        ],
        "series": series_index,
        "prohibited_actions": {
            "strategy_rerun": False,
            "optimization_rerun": False,
            "walk_forward_rerun": False,
            "mcpt_rerun": False,
            "bootstrap_rerun": False,
            "paper_simulation": False,
            "market_data_request": False,
            "frozen_result_mutation": False,
        },
    }
    writer.json(Path("manifest.json"), manifest)
    writer.text(
        Path("index.html"),
        render_root_index(
            (
                registry[experiment_id]
                for experiment_id in selected_ids
            ),
            result_counts=result_counts,
            evidence_digest=inventory.digest,
            evidence_file_count=len(inventory.records),
        ),
    )
    return writer


def build_analytics_expansion(
    project_dir: Path,
    *,
    output_dir: Path | None = None,
    experiment_ids: Iterable[str] | None = None,
    preflight_only: bool = False,
) -> AnalyticsBuildResult:
    project_dir = project_dir.resolve()
    destination = _validate_output_dir(
        project_dir,
        output_dir or project_dir / DEFAULT_OUTPUT_RELATIVE,
    )
    registry = validate_analytics_evidence_registry(
        project_dir,
        require_files=True,
    )
    selected_ids = _selected_experiment_ids(
        registry,
        experiment_ids,
    )
    before = build_evidence_inventory(project_dir, registry)
    calculated = _calculate_results(
        project_dir,
        registry,
        set(selected_ids),
        before,
    )
    after_calculation = build_evidence_inventory(
        project_dir,
        registry,
    )
    assert_evidence_unchanged(before, after_calculation)

    if preflight_only:
        return AnalyticsBuildResult(
            output_dir=destination,
            evidence_digest=before.digest,
            evidence_file_count=len(before.records),
            strategy_series_count=sum(
                len(results)
                for results in calculated.values()
            ),
            experiment_count=len(selected_ids),
            files_written=0,
            files_unchanged=0,
            preflight_only=True,
        )

    writer = _write_outputs(
        output_dir=destination,
        registry=registry,
        selected_ids=selected_ids,
        calculated=calculated,
        inventory=before,
        output_root_label=(
            destination.relative_to(project_dir).as_posix()
        ),
    )
    after_output = build_evidence_inventory(
        project_dir,
        registry,
    )
    assert_evidence_unchanged(before, after_output)
    return AnalyticsBuildResult(
        output_dir=destination,
        evidence_digest=before.digest,
        evidence_file_count=len(before.records),
        strategy_series_count=sum(
            len(results)
            for results in calculated.values()
        ),
        experiment_count=len(selected_ids),
        files_written=writer.written,
        files_unchanged=writer.unchanged,
        preflight_only=False,
    )


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build reporting-only analytics from registered frozen "
            "evidence. This command never runs a strategy."
        )
    )
    parser.add_argument(
        "--experiment",
        action="append",
        dest="experiments",
        help=(
            "Limit calculation to an experiment ID. Repeat the option "
            "to select more than one. The default is EXP-001 through "
            "EXP-018."
        ),
    )
    parser.add_argument(
        "--preflight",
        action="store_true",
        help=(
            "Load, reconcile, calculate, and hash all selected evidence "
            "without writing analytics output."
        ),
    )
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    project_dir = Path(__file__).resolve().parent
    result = build_analytics_expansion(
        project_dir,
        experiment_ids=arguments.experiments,
        preflight_only=arguments.preflight,
    )
    mode = "PREFLIGHT" if result.preflight_only else "BUILD"
    print(f"\nANALYTICS EXPANSION {mode}")
    print("=" * 44)
    print(f"Experiments:           {result.experiment_count}")
    print(f"Strategy series:       {result.strategy_series_count}")
    print(f"Evidence files:        {result.evidence_file_count}")
    print(f"Evidence SHA-256:       {result.evidence_digest}")
    print(f"Files written:         {result.files_written}")
    print(f"Files unchanged:       {result.files_unchanged}")
    print(f"Output:                {result.output_dir}")
    print("Strategy rerun:        disabled")
    print("Optimization rerun:    disabled")
    print("MCPT/bootstrap rerun:  disabled")
    print("Market-data request:   disabled")
    print("Frozen result writes:  none")
    print("=" * 44)


if __name__ == "__main__":
    main()
