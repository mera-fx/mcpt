from __future__ import annotations

from pathlib import Path
import sys
import unittest


PROJECT_DIR = Path(__file__).resolve().parent
TESTS_DIR = PROJECT_DIR / "tests"


def main() -> None:
    suite = unittest.defaultTestLoader.discover(
        str(TESTS_DIR),
        pattern="test_*.py",
        top_level_dir=str(PROJECT_DIR),
    )

    result = unittest.TextTestRunner(
        verbosity=2,
    ).run(suite)

    if not result.wasSuccessful():
        sys.exit(1)


if __name__ == "__main__":
    main()
