from __future__ import annotations

from pathlib import Path
import re

from PIL import Image


PROJECT_DIR = Path(__file__).resolve().parent
REPORT_FILES = tuple(
    PROJECT_DIR
    / "reports"
    / f"EXP-{index:03d}-research-lab"
    / "report.html"
    for index in range(5, 12)
) + (
    PROJECT_DIR
    / "reports"
    / "research_dashboard"
    / "strategy_comparison.html",
)
OPAQUE_WHITE = (255, 255, 255, 255)


def referenced_local_images(report: Path) -> list[Path]:
    document = report.read_text(encoding="utf-8")
    sources = re.findall(r'<img[^>]+src="([^"]+)', document)
    return [
        (report.parent / source).resolve()
        for source in sources
        if not source.startswith(("http:", "https:", "data:"))
    ]


def image_corners(path: Path) -> tuple[tuple[int, int, int, int], ...]:
    with Image.open(path) as source:
        image = source.convert("RGBA")
        return (
            image.getpixel((0, 0)),
            image.getpixel((image.width - 1, 0)),
            image.getpixel((0, image.height - 1)),
            image.getpixel((image.width - 1, image.height - 1)),
        )


def main() -> None:
    missing_reports = [path for path in REPORT_FILES if not path.is_file()]
    if missing_reports:
        raise FileNotFoundError(
            "Missing current report files: "
            + ", ".join(str(path) for path in missing_reports)
        )

    references: list[tuple[Path, Path]] = []
    for report in REPORT_FILES:
        references.extend(
            (report, image) for image in referenced_local_images(report)
        )

    failures: list[str] = []
    for report, image in references:
        if not image.is_file():
            failures.append(f"{report.name}: missing {image}")
            continue
        corners = image_corners(image)
        if any(pixel != OPAQUE_WHITE for pixel in corners):
            failures.append(
                f"{report.name}: {image} has outer corners {corners}"
            )

    print(f"Referenced charts checked: {len(references)}")
    print(
        "Charts with a non-white, transparent, or missing outer corner: "
        f"{len(failures)}"
    )
    if failures:
        raise ValueError("\n".join(failures))


if __name__ == "__main__":
    main()
