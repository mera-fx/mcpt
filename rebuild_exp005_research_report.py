from __future__ import annotations

import argparse
import os

from exp005_research_report import write_report


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Rebuild the polished EXP-005 research report "
            "from frozen saved result files only."
        )
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Open the rebuilt report on Windows.",
    )
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    report, metadata = write_report()

    print()
    print("EXP-005 polished research report rebuilt.")
    print("Research rerun: False")
    print("MCPT rerun: False")
    print("Data import rerun: False")
    print(f"Report:   {report.resolve()}")
    print(f"Metadata: {metadata.resolve()}")

    if arguments.open:
        if hasattr(os, "startfile"):
            os.startfile(report)
        else:
            print("--open is automatically supported on Windows only.")


if __name__ == "__main__":
    main()
