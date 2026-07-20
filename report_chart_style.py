from __future__ import annotations

from pathlib import Path
from typing import Any

from matplotlib.figure import Figure


REPORT_CHART_BACKGROUND = "#ffffff"


def save_report_figure(
    figure: Figure,
    output: Path,
    *,
    dpi: int,
    bbox_inches: str | None = None,
    **kwargs: Any,
) -> None:
    """Save report charts on an opaque light canvas.

    Report pages use a dark theme, while Matplotlib chart text uses a light
    theme.  A transparent or dark outer figure canvas therefore makes titles,
    tick labels, and axis labels unreadable.  Keep the complete bitmap light,
    including the margins outside each plotting axis.
    """

    figure.patch.set_facecolor(REPORT_CHART_BACKGROUND)
    for axis in figure.axes:
        axis.set_facecolor(REPORT_CHART_BACKGROUND)

    save_kwargs: dict[str, Any] = {
        "dpi": dpi,
        "facecolor": REPORT_CHART_BACKGROUND,
        "edgecolor": REPORT_CHART_BACKGROUND,
        "transparent": False,
    }
    if bbox_inches is not None:
        save_kwargs["bbox_inches"] = bbox_inches
    save_kwargs.update(kwargs)
    figure.savefig(output, **save_kwargs)
