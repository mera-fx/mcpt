from __future__ import annotations

from pathlib import Path
import shutil

import exp005_quantower_import as base
from exp005_confirmation_import import (
    INCOMING_ROOT,
    SESSION_RETRY_ROOT,
)
from exp005_confirmation_missing_session_resolution import (
    get_exp005_confirmation_missing_session_resolution,
    validate_exp005_confirmation_missing_session_resolution,
)


def _csvs(
    root: Path,
    symbol: str,
) -> list[Path]:
    return sorted(
        (root / symbol).glob("*.csv"),
        key=lambda item: item.name.lower(),
    )


def main() -> None:
    validate_exp005_confirmation_missing_session_resolution()
    record = (
        get_exp005_confirmation_missing_session_resolution()
    )

    print()
    print(
        "===== EXP-005 CONFIRMATION SESSION RETRY ORGANIZER ====="
    )
    print(
        "Purpose: move only the six locked one-day retries"
    )
    print(
        "Strategy calculations: DISABLED"
    )
    print()

    for symbol in ("NQ", "MNQ"):
        incoming = INCOMING_ROOT / symbol
        destination = (
            SESSION_RETRY_ROOT
            / symbol
        )
        incoming.mkdir(
            parents=True,
            exist_ok=True,
        )
        destination.mkdir(
            parents=True,
            exist_ok=True,
        )

        expected = {
            specification["sha256"]: session
            for session, specification
            in record["retry_files"][
                symbol
            ].items()
        }
        located: dict[str, Path] = {}

        for path in (
            _csvs(INCOMING_ROOT, symbol)
            + _csvs(SESSION_RETRY_ROOT, symbol)
        ):
            digest = base.sha256_file(
                path
            )

            if digest in expected:
                if digest in located:
                    raise RuntimeError(
                        f"Duplicate locked {symbol} retry "
                        f"for {expected[digest]}."
                    )

                located[digest] = path

        missing = set(expected).difference(
            located
        )

        if missing:
            missing_dates = sorted(
                expected[digest]
                for digest in missing
            )
            raise FileNotFoundError(
                f"{symbol} is missing locked retry files "
                f"for: {', '.join(missing_dates)}."
            )

        moved = 0

        for digest, source in located.items():
            target = (
                destination
                / source.name
            )

            if source.resolve() == target.resolve():
                continue

            if target.exists():
                if (
                    base.sha256_file(target)
                    != digest
                ):
                    raise RuntimeError(
                        f"Retry destination conflict: "
                        f"{target}"
                    )
                source.unlink()
            else:
                shutil.move(
                    str(source),
                    str(target),
                )

            moved += 1

        incoming_files = _csvs(
            INCOMING_ROOT,
            symbol,
        )
        retry_files = _csvs(
            SESSION_RETRY_ROOT,
            symbol,
        )

        if len(incoming_files) != 1:
            raise RuntimeError(
                f"{symbol} incoming folder must contain "
                "exactly one full export after organization. "
                f"Observed: {len(incoming_files)}."
            )

        retry_hashes = {
            base.sha256_file(path)
            for path in retry_files
        }

        if retry_hashes != set(expected):
            raise RuntimeError(
                f"{symbol} session_retry folder does not "
                "contain the exact locked retry set."
            )

        print(
            f"{symbol}: {moved} moved, "
            "1 full export retained, "
            "3 locked retries ready"
        )

    print()
    print(
        "Session retry organization completed."
    )
    print(
        "No source CSV was edited and no strategy result "
        "was calculated."
    )
    print(
        "========================================================"
    )


if __name__ == "__main__":
    main()
