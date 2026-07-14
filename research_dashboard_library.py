from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import html
import json
import os
from pathlib import Path
import re
from typing import Any, Iterable

import numpy as np
import pandas as pd


SUPPORTED_EXTENSIONS = {
    ".html",
    ".htm",
    ".md",
    ".json",
    ".csv",
    ".png",
    ".jpg",
    ".jpeg",
    ".svg",
    ".txt",
    ".log",
}

EXCLUDED_NAMES = {
    "research_dashboard.csv",
    "research_dashboard_artifacts.csv",
}

EXCLUDED_PARTS = {
    "__pycache__",
    ".git",
    ".pytest_cache",
}

TEXT_PREVIEW_LIMIT = 250_000
CSV_PREVIEW_ROWS = 100


@dataclass(frozen=True)
class ResearchArtifact:
    experiment_id: str
    path: Path
    project_relative_path: str
    category: str
    label: str
    extension: str
    size_bytes: int
    modified_utc: str

    def to_dict(self) -> dict[str, Any]:
        record = asdict(self)
        record["path"] = str(self.path)
        return record


def normalize_experiment_id(value: str) -> str:
    cleaned = value.strip().upper().replace("_", "-")
    if cleaned.startswith("EXP-"):
        suffix = cleaned[4:]
    elif cleaned.startswith("EXP"):
        suffix = cleaned[3:].lstrip("-")
    else:
        suffix = cleaned

    if not suffix.isdigit():
        raise ValueError(
            "Experiment ID must look like EXP-005 or 005."
        )

    return f"EXP-{int(suffix):03d}"


def _experiment_pattern(experiment_id: str) -> re.Pattern[str]:
    number = int(normalize_experiment_id(experiment_id).split("-")[1])
    return re.compile(
        rf"(?i)(?:^|[^a-z0-9])exp[-_ ]?0*{number}(?:[^0-9]|$)"
    )


def detect_experiment_id(
    path: Path,
    experiment_ids: Iterable[str],
) -> str | None:
    searchable = path.as_posix()
    matches = [
        normalize_experiment_id(experiment_id)
        for experiment_id in experiment_ids
        if _experiment_pattern(experiment_id).search(searchable)
    ]

    if len(matches) == 1:
        return matches[0]

    return None


def humanize(value: str) -> str:
    cleaned = re.sub(
        r"(?i)\bexp[-_ ]?0*\d+\b",
        "",
        value,
    )
    cleaned = cleaned.replace("_", " ").replace("-", " ")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    replacements = {
        "mcpt": "MCPT",
        "nq": "NQ",
        "mnq": "MNQ",
        "qqq": "QQQ",
        "oos": "OOS",
        "ohlc": "OHLC",
        "pnl": "P&L",
    }

    words = []
    for word in cleaned.split():
        lowered = word.lower()
        words.append(
            replacements.get(lowered, word.capitalize())
        )

    return " ".join(words) or "Research artifact"


def classify_artifact(path: Path) -> str:
    name = path.name.lower()
    stem = path.stem.lower()
    extension = path.suffix.lower()

    if extension in {".html", ".htm"}:
        return "Visual report"

    if extension in {".png", ".jpg", ".jpeg", ".svg"}:
        return "Chart"

    if "preregistration" in name:
        return "Preregistration"

    if "paper" in name:
        return "Paper-testing record"

    if "review" in name:
        return "Review record"

    if "decision" in name:
        return "Decision record"

    if any(
        token in name
        for token in (
            "audit",
            "resolution",
            "recheck",
            "missing_session",
            "duplicate",
            "alignment",
        )
    ):
        return "Data-quality record"

    if "trade" in stem and extension == ".csv":
        return "Trade ledger"

    if "yearly" in stem:
        return "Yearly results"

    if "cost" in stem:
        return "Cost sensitivity"

    if "summary" in stem:
        return "Summary table"

    if extension == ".csv":
        return "Results table"

    if extension == ".json":
        return "Structured record"

    if extension == ".md":
        return "Research note"

    if extension in {".txt", ".log"}:
        return "Text record"

    return "Research artifact"


def artifact_label(path: Path) -> str:
    if path.name.lower() in {"report.html", "index.html"}:
        return humanize(path.parent.name)

    return humanize(path.stem)


def _is_supported(path: Path) -> bool:
    if not path.is_file():
        return False

    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        return False

    if path.name in EXCLUDED_NAMES:
        return False

    if any(part in EXCLUDED_PARTS for part in path.parts):
        return False

    if path.name.endswith(".tmp"):
        return False

    return True


def discover_artifacts(
    project_dir: Path,
    experiment_ids: Iterable[str],
) -> list[ResearchArtifact]:
    project_dir = Path(project_dir).resolve()
    normalized_ids = [
        normalize_experiment_id(item)
        for item in experiment_ids
    ]

    artifacts: list[ResearchArtifact] = []

    for root_name in ("reports", "results", "research"):
        root = project_dir / root_name
        if not root.exists():
            continue

        for path in sorted(root.rglob("*")):
            if not _is_supported(path):
                continue

            relative = path.relative_to(project_dir)

            if (
                relative.parts[:2]
                == ("reports", "research_dashboard")
            ):
                continue

            experiment_id = detect_experiment_id(
                relative,
                normalized_ids,
            )
            if experiment_id is None:
                continue

            stat = path.stat()
            artifacts.append(
                ResearchArtifact(
                    experiment_id=experiment_id,
                    path=path.resolve(),
                    project_relative_path=relative.as_posix(),
                    category=classify_artifact(path),
                    label=artifact_label(path),
                    extension=path.suffix.lower(),
                    size_bytes=int(stat.st_size),
                    modified_utc=datetime.fromtimestamp(
                        stat.st_mtime,
                        tz=timezone.utc,
                    ).isoformat(timespec="seconds"),
                )
            )

    return sorted(
        artifacts,
        key=lambda item: (
            int(item.experiment_id.split("-")[1]),
            artifact_priority(item),
            item.project_relative_path.lower(),
        ),
    )


def artifact_priority(artifact: ResearchArtifact) -> tuple[int, int]:
    category_order = {
        "Visual report": 0,
        "Decision record": 1,
        "Review record": 2,
        "Paper-testing record": 3,
        "Preregistration": 4,
        "Summary table": 5,
        "Yearly results": 6,
        "Cost sensitivity": 7,
        "Trade ledger": 8,
        "Data-quality record": 9,
        "Results table": 10,
        "Structured record": 11,
        "Research note": 12,
        "Chart": 13,
        "Text record": 14,
    }
    return (
        category_order.get(artifact.category, 99),
        len(artifact.project_relative_path),
    )


def choose_primary_report(
    artifacts: Iterable[ResearchArtifact],
    experiment_id: str,
) -> ResearchArtifact | None:
    experiment_id = normalize_experiment_id(experiment_id)
    candidates = [
        item
        for item in artifacts
        if item.experiment_id == experiment_id
        and item.extension in {".html", ".htm"}
    ]

    if not candidates:
        return None

    preferred_fragments = (
        f"reports/{experiment_id}-research-lab/report.html",
        f"reports/{experiment_id}-full-validation/report.html",
        f"reports/{experiment_id}-quick-screen/report.html",
        f"reports/{experiment_id.lower()}-research-lab/report.html",
        f"reports/{experiment_id.lower()}-full-validation/report.html",
    )

    lowered = {
        item.project_relative_path.lower(): item
        for item in candidates
    }

    for preferred in preferred_fragments:
        match = lowered.get(preferred.lower())
        if match is not None:
            return match

    return sorted(
        candidates,
        key=lambda item: (
            artifact_priority(item),
            item.project_relative_path.lower(),
        ),
    )[0]


def relative_link(
    source_directory: Path,
    target: Path,
) -> str:
    return Path(
        os.path.relpath(
            Path(target).resolve(),
            Path(source_directory).resolve(),
        )
    ).as_posix()


def _preview_template(
    *,
    title: str,
    subtitle: str,
    body: str,
    dashboard_link: str,
    source_link: str,
) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>
:root {{
  color-scheme: light dark;
  --bg: #0f172a;
  --panel: #111c32;
  --text: #e5edf8;
  --muted: #9fb0c8;
  --line: #2a3953;
  --accent: #7dd3fc;
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: Inter, Segoe UI, Arial, sans-serif;
}}
main {{
  width: min(1500px, calc(100% - 32px));
  margin: 24px auto 60px;
}}
.toolbar {{
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 18px;
}}
a {{
  color: var(--accent);
  text-decoration: none;
}}
.button {{
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 9px 13px;
  background: var(--panel);
}}
.panel {{
  border: 1px solid var(--line);
  border-radius: 16px;
  background: var(--panel);
  padding: 18px;
  overflow: auto;
}}
h1 {{ margin-bottom: 6px; }}
.subtitle {{ color: var(--muted); margin-bottom: 18px; }}
pre {{
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  line-height: 1.45;
}}
table {{
  border-collapse: collapse;
  min-width: 100%;
  font-size: 0.9rem;
}}
th, td {{
  border-bottom: 1px solid var(--line);
  padding: 8px 10px;
  text-align: left;
  white-space: nowrap;
}}
th {{
  position: sticky;
  top: 0;
  background: #17243d;
}}
</style>
</head>
<body>
<main>
<div class="toolbar">
<a class="button" href="{html.escape(dashboard_link)}">← Dashboard</a>
<a class="button" href="{html.escape(source_link)}">Open original file</a>
</div>
<h1>{html.escape(title)}</h1>
<div class="subtitle">{html.escape(subtitle)}</div>
<div class="panel">{body}</div>
</main>
</body>
</html>
"""


def build_artifact_preview(
    artifact: ResearchArtifact,
    dashboard_directory: Path,
) -> Path | None:
    if artifact.extension in {
        ".html",
        ".htm",
        ".png",
        ".jpg",
        ".jpeg",
        ".svg",
    }:
        return None

    key = hashlib.sha256(
        artifact.project_relative_path.encode("utf-8")
    ).hexdigest()[:12]
    preview_directory = (
        Path(dashboard_directory)
        / "previews"
        / artifact.experiment_id
    )
    preview_directory.mkdir(
        parents=True,
        exist_ok=True,
    )
    preview_file = (
        preview_directory
        / f"{key}_{artifact.path.stem}.html"
    )

    source_link = relative_link(
        preview_directory,
        artifact.path,
    )
    dashboard_link = relative_link(
        preview_directory,
        Path(dashboard_directory) / "index.html",
    )

    title = artifact.label
    subtitle = artifact.project_relative_path

    try:
        if artifact.extension == ".csv":
            frame = pd.read_csv(artifact.path)
            preview = frame.head(
                CSV_PREVIEW_ROWS
            )
            body = (
                f"<p>Rows: {len(frame):,} · "
                f"Columns: {len(frame.columns):,} · "
                f"Showing first {len(preview):,} rows.</p>"
                + preview.to_html(
                    index=False,
                    escape=True,
                    border=0,
                )
            )
        elif artifact.extension == ".json":
            value = json.loads(
                artifact.path.read_text(
                    encoding="utf-8"
                )
            )
            body = (
                "<pre>"
                + html.escape(
                    json.dumps(
                        value,
                        indent=2,
                        ensure_ascii=False,
                    )
                )
                + "</pre>"
            )
        else:
            text = artifact.path.read_text(
                encoding="utf-8",
                errors="replace",
            )
            truncated = (
                text[:TEXT_PREVIEW_LIMIT]
                + "\n\n[Preview truncated]"
                if len(text) > TEXT_PREVIEW_LIMIT
                else text
            )
            body = (
                "<pre>"
                + html.escape(truncated)
                + "</pre>"
            )
    except Exception as error:
        body = (
            "<p>Preview could not be generated.</p>"
            f"<pre>{html.escape(str(error))}</pre>"
        )

    preview_file.write_text(
        _preview_template(
            title=title,
            subtitle=subtitle,
            body=body,
            dashboard_link=dashboard_link,
            source_link=source_link,
        ),
        encoding="utf-8",
    )
    return preview_file


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}

    try:
        value = json.loads(
            path.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError):
        return {}

    return value if isinstance(value, dict) else {}


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def _metric_record_from_full_result(
    payload: dict[str, Any],
) -> dict[str, Any]:
    results = payload.get("results")
    if not isinstance(results, dict):
        return {}

    symbol = (
        "NQ"
        if isinstance(results.get("NQ"), dict)
        else next(
            (
                key
                for key, value in results.items()
                if isinstance(value, dict)
            ),
            None,
        )
    )

    if symbol is None:
        return {}

    metrics = results[symbol]
    mcpt = payload.get("mcpt", {})
    evaluation = payload.get("evaluation", {})

    return {
        "metric_source": "Frozen full-validation result",
        "primary_symbol": symbol,
        "profit_factor": _safe_float(
            metrics.get(
                "trade_profit_factor",
                metrics.get("profit_factor"),
            )
        ),
        "net_profit_usd": _safe_float(
            metrics.get(
                "net_profit_usd",
                metrics.get("net_profit"),
            )
        ),
        "win_rate_percent": _safe_float(
            metrics.get("win_rate_percent")
        ),
        "max_drawdown_usd": _safe_float(
            metrics.get(
                "maximum_drawdown_usd",
                metrics.get("max_drawdown_usd"),
            )
        ),
        "total_trades": _safe_float(
            metrics.get(
                "completed_trades",
                metrics.get("total_trades"),
            )
        ),
        "mcpt_p_value": _safe_float(
            mcpt.get(
                "p_value",
                payload.get("mcpt_p_value"),
            )
        ),
        "result_decision": (
            evaluation.get("decision")
            or payload.get("decision")
            or ""
        ),
    }


def _best_full_result_payload(
    project_dir: Path,
    experiment_id: str,
) -> dict[str, Any]:
    candidates = [
        project_dir
        / "research"
        / f"{experiment_id}_full_validation_result.json",
        project_dir
        / "results"
        / experiment_id
        / "full_validation"
        / "full_validation_decision.json",
        project_dir
        / "research"
        / f"{experiment_id}_quick_transfer_result.json",
        project_dir
        / "research"
        / f"{experiment_id}_quick_screen_result.json",
    ]

    for path in candidates:
        payload = _read_json(path)
        if payload:
            return payload

    return {}


def _generic_summary_metrics(
    project_dir: Path,
    experiment_id: str,
) -> dict[str, Any]:
    summary_path = (
        project_dir
        / "results"
        / experiment_id
        / "summary.csv"
    )
    metadata_path = (
        project_dir
        / "results"
        / experiment_id
        / "run_metadata.json"
    )

    if not summary_path.exists():
        return {}

    try:
        summary = pd.read_csv(
            summary_path,
            index_col=0,
        )
    except Exception:
        return {}

    if summary.empty:
        return {}

    row_name = (
        "Fixed parameters"
        if "Fixed parameters" in summary.index
        else str(summary.index[0])
    )
    row = summary.loc[row_name]
    metadata = _read_json(metadata_path)

    return {
        "metric_source": "Saved research summary",
        "primary_symbol": "",
        "profit_factor": _safe_float(
            row.get("trade_profit_factor")
        ),
        "net_profit_usd": _safe_float(
            row.get(
                "net_profit_cash",
                row.get("net_profit"),
            )
        ),
        "win_rate_percent": _safe_float(
            row.get("win_rate_percent")
        ),
        "max_drawdown_percent": _safe_float(
            row.get("max_drawdown_percent")
        ),
        "total_return_percent": _safe_float(
            row.get("total_return_percent")
        ),
        "total_trades": _safe_float(
            row.get(
                "total_trades",
                row.get("completed_trades"),
            )
        ),
        "mcpt_p_value": _safe_float(
            metadata.get("mcpt_p_value")
        ),
        "result_decision": "",
    }




def _research_lab_report_metrics(
    project_dir: Path,
    experiment_id: str,
) -> dict[str, Any]:
    metadata_path = (
        Path(project_dir)
        / "reports"
        / f"{experiment_id}-research-lab"
        / "report_metadata.json"
    )
    payload = _read_json(metadata_path)

    if not payload:
        return {}

    if payload.get("experiment_id") != experiment_id:
        return {}

    metrics = payload.get("primary_metrics")
    if not isinstance(metrics, dict):
        return {}

    allowed = {
        "primary_symbol",
        "profit_factor",
        "net_profit_usd",
        "total_return_percent",
        "win_rate_percent",
        "max_drawdown_usd",
        "max_drawdown_percent",
        "total_trades",
        "mcpt_p_value",
        "result_decision",
        "review_decision",
        "drawdown_percent_note",
    }

    output = {
        key: value
        for key, value in metrics.items()
        if key in allowed
    }
    output["metric_source"] = (
        "Polished saved-results report"
    )
    return output

def load_experiment_metrics(
    project_dir: Path,
    experiment_id: str,
) -> dict[str, Any]:
    project_dir = Path(project_dir)
    experiment_id = normalize_experiment_id(
        experiment_id
    )

    metrics = _generic_summary_metrics(
        project_dir,
        experiment_id,
    )
    full_payload = _best_full_result_payload(
        project_dir,
        experiment_id,
    )
    full_metrics = _metric_record_from_full_result(
        full_payload
    )

    if full_metrics:
        metrics.update(full_metrics)

    report_metrics = _research_lab_report_metrics(
        project_dir,
        experiment_id,
    )
    if report_metrics:
        metrics.update(report_metrics)

    review_path = (
        project_dir
        / "results"
        / experiment_id
        / "review"
        / "review_decision.json"
    )
    review = _read_json(review_path)
    review_evaluation = review.get("evaluation", {})

    if isinstance(review_evaluation, dict):
        metrics["review_decision"] = (
            review_evaluation.get("decision", "")
        )
    else:
        metrics["review_decision"] = ""

    metrics.setdefault("metric_source", "")
    metrics.setdefault("primary_symbol", "")
    metrics.setdefault("profit_factor", float("nan"))
    metrics.setdefault("net_profit_usd", float("nan"))
    metrics.setdefault("win_rate_percent", float("nan"))
    metrics.setdefault("max_drawdown_usd", float("nan"))
    metrics.setdefault("max_drawdown_percent", float("nan"))
    metrics.setdefault("total_return_percent", float("nan"))
    metrics.setdefault("total_trades", float("nan"))
    metrics.setdefault("mcpt_p_value", float("nan"))
    metrics.setdefault("result_decision", "")
    metrics.setdefault("review_decision", "")

    if (
        experiment_id == "EXP-005"
        and np.isnan(
            _safe_float(
                metrics["max_drawdown_percent"]
            )
        )
    ):
        metrics["drawdown_percent_note"] = (
            "Build the polished EXP-005 report to apply "
            "the explicit starting-capital basis."
        )
    else:
        metrics.setdefault(
            "drawdown_percent_note",
            "",
        )

    return metrics
