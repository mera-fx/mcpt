from __future__ import annotations

import argparse
from pathlib import Path
import re

from strategy_explanations import (
    FAMILY_EXPLANATIONS,
    FAMILY_REPORT_HEADINGS,
    STRATEGY_EXPLANATIONS,
    STRATEGY_EXPLANATION_CSS,
    family_explanation_html,
    strategy_explanation_html,
)


PROJECT_DIR = Path(__file__).resolve().parent
REPORTS_DIR = PROJECT_DIR / "reports"
STYLE_MARKER = "strategy-explanation-section .plain-language-lead"


def experiment_id_from_report(path: Path) -> str | None:
    for parent in (path.parent, *path.parents):
        match = re.match(r"^(EXP-\d{3})", parent.name.upper())
        if match:
            return match.group(1)
        if parent == REPORTS_DIR:
            break
    return None


def discover_experiment_reports(
    reports_dir: Path = REPORTS_DIR,
) -> tuple[tuple[str, Path], ...]:
    discovered: list[tuple[str, Path]] = []
    if not reports_dir.exists():
        return ()
    for path in sorted(reports_dir.rglob("report.html")):
        experiment_id = experiment_id_from_report(path)
        if experiment_id is not None:
            discovered.append((experiment_id, path))
    return tuple(discovered)


def _insert_css(document: str) -> str:
    if STYLE_MARKER in document:
        return document
    if "</style>" in document:
        return document.replace(
            "</style>",
            STRATEGY_EXPLANATION_CSS + "\n</style>",
            1,
        )
    if "</head>" in document:
        return document.replace(
            "</head>",
            f"<style>{STRATEGY_EXPLANATION_CSS}</style>\n</head>",
            1,
        )
    return document


def _insert_nav_link(document: str) -> str:
    link = '<a href="#strategy-rules">How the strategy works</a>'
    if link in document or "<nav" not in document:
        return document
    overview = re.search(
        r'(<a[^>]+href=["\']#overview["\'][^>]*>.*?</a>)',
        document,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if overview:
        return (
            document[: overview.end()]
            + "\n"
            + link
            + document[overview.end() :]
        )
    nav_open = re.search(r"<nav[^>]*>", document, flags=re.IGNORECASE)
    if nav_open:
        return (
            document[: nav_open.end()]
            + "\n"
            + link
            + document[nav_open.end() :]
        )
    return document


def _insert_main_explanation(document: str, experiment_id: str) -> str:
    explanation = strategy_explanation_html(experiment_id)
    existing = re.search(
        r"<section\b[^>]*\bid=[\"']strategy-rules[\"'][^>]*>.*?</section>",
        document,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if existing:
        return (
            document[: existing.start()]
            + explanation
            + document[existing.end() :]
        )
    patterns = (
        r"(</header>)",
        r"(<section[^>]*(?:class=[\"'][^\"']*hero[^\"']*[\"'])?[^>]*>.*?</section>)",
        r"(<div[^>]+class=[\"'][^\"']*subtitle[^\"']*[\"'][^>]*>.*?</div>)",
        r"(</h1>)",
    )
    for pattern in patterns:
        match = re.search(
            pattern,
            document,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if match:
            return (
                document[: match.end()]
                + "\n"
                + explanation
                + "\n"
                + document[match.end() :]
            )
    body = re.search(r"<body[^>]*>", document, flags=re.IGNORECASE)
    if body:
        return (
            document[: body.end()]
            + "\n"
            + explanation
            + "\n"
            + document[body.end() :]
        )
    return document


def _insert_exp009_family_explanations(document: str) -> str:
    for family_id in FAMILY_EXPLANATIONS:
        identifier = f'family-rules-{family_id}'
        if f'id="{identifier}"' in document:
            continue
        heading = re.escape(FAMILY_REPORT_HEADINGS[family_id])
        match = re.search(
            rf"(<h2>{heading}</h2>)",
            document,
            flags=re.IGNORECASE,
        )
        if not match:
            continue
        detail = family_explanation_html(family_id)
        document = (
            document[: match.end()]
            + "\n"
            + detail
            + "\n"
            + document[match.end() :]
        )
    return document


def upgrade_report_document(document: str, experiment_id: str) -> str:
    upgraded = _insert_css(document)
    upgraded = _insert_nav_link(upgraded)
    upgraded = _insert_main_explanation(upgraded, experiment_id)
    if experiment_id == "EXP-009":
        upgraded = _insert_exp009_family_explanations(upgraded)
    return upgraded


def upgrade_reports(
    reports: tuple[tuple[str, Path], ...],
    *,
    write: bool,
) -> tuple[Path, ...]:
    changed: list[Path] = []
    for experiment_id, path in reports:
        if experiment_id not in STRATEGY_EXPLANATIONS:
            continue
        before = path.read_text(encoding="utf-8")
        after = upgrade_report_document(before, experiment_id)
        if before == after:
            continue
        changed.append(path)
        if write:
            path.write_text(after, encoding="utf-8")
    return tuple(changed)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Add the shared plain-English strategy explanation to existing "
            "generated reports without rerunning any research."
        )
    )
    parser.add_argument(
        "--preflight",
        action="store_true",
        help="List reports that would change without writing them.",
    )
    args = parser.parse_args()

    reports = discover_experiment_reports()
    changed = upgrade_reports(reports, write=not args.preflight)

    print()
    print("PLAIN-ENGLISH STRATEGY EXPLANATION UPGRADE")
    print("==========================================")
    print(f"Experiment reports found: {len(reports)}")
    print(f"Reports needing an update: {len(changed)}")
    print("Research calculations run: 0")
    print("Frozen result files changed: 0")
    for path in changed:
        print(f"- {path}")
    if args.preflight:
        print("Preflight passed. No report file was written.")
    else:
        print("Existing report HTML was updated from the shared explanation catalog.")


if __name__ == "__main__":
    main()
