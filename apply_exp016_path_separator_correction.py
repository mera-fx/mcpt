from __future__ import annotations

from pathlib import Path
import re


TARGET = Path(__file__).resolve().parent / "run_exp016_audit.py"

LOAD_JSON_BLOCK = """def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"Expected JSON object: {path}")
    return value
"""

HELPER_BLOCK = """

def _portable_relative_path(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace(chr(92), "/")


def _project_path_from_relative(value: Any) -> Path:
    normalized = _portable_relative_path(value)
    parts = [
        part for part in normalized.split("/")
        if part not in ("", ".")
    ]
    if (
        not normalized
        or normalized.startswith("/")
        or not parts
        or any(part == ".." for part in parts)
        or ":" in parts[0]
    ):
        raise RuntimeError("Expected a safe project-relative path.")
    return PROJECT_DIR.joinpath(*parts)
"""

OLD_PATH_COMPARISON = (
    '            or record.get("local_path") != expected["local_path"]\n'
)

NEW_PATH_COMPARISON = (
    '            or _portable_relative_path(record.get("local_path")) '
    '!= _portable_relative_path(expected["local_path"])\n'
)

OLD_PROJECT_PATH_PATTERN = (
    r'(?m)^(\s*)path = PROJECT_DIR / record\["local_path"\]$'
)

NEW_PROJECT_PATH_TEMPLATE = (
    r'\1path = _project_path_from_relative(record["local_path"])'
)

OLD_SERIALIZATION_PATTERN = (
    r'(?m)^(\s*)"local_path": '
    r'str\(output\.relative_to\(PROJECT_DIR\)\),$'
)

NEW_SERIALIZATION_TEMPLATE = (
    r'\1"local_path": output.relative_to(PROJECT_DIR).as_posix(),'
)


def apply_correction(source: str) -> str:
    if "_portable_relative_path" in source:
        raise RuntimeError(
            "The EXP-016 path-separator correction already appears applied."
        )

    if source.count(LOAD_JSON_BLOCK) != 1:
        raise RuntimeError(
            "The expected _load_json insertion point was not found exactly once."
        )
    if source.count(OLD_PATH_COMPARISON) != 1:
        raise RuntimeError(
            "The vulnerable local_path comparison was not found exactly once."
        )

    corrected = source.replace(
        LOAD_JSON_BLOCK,
        LOAD_JSON_BLOCK + HELPER_BLOCK,
        1,
    )
    corrected = corrected.replace(
        OLD_PATH_COMPARISON,
        NEW_PATH_COMPARISON,
        1,
    )

    corrected, project_path_count = re.subn(
        OLD_PROJECT_PATH_PATTERN,
        NEW_PROJECT_PATH_TEMPLATE,
        corrected,
    )
    if project_path_count != 2:
        raise RuntimeError(
            "The two expected project-path constructions were not found."
        )

    corrected, serialization_count = re.subn(
        OLD_SERIALIZATION_PATTERN,
        NEW_SERIALIZATION_TEMPLATE,
        corrected,
    )
    if serialization_count != 2:
        raise RuntimeError(
            "The two expected local_path serializations were not found."
        )

    compile(corrected, str(TARGET), "exec")
    return corrected


def main() -> None:
    if not TARGET.is_file():
        raise RuntimeError(f"Missing target file: {TARGET}")

    original = TARGET.read_text(encoding="utf-8")
    corrected = apply_correction(original)
    TARGET.write_text(corrected, encoding="utf-8", newline="\n")

    print("Applied EXP-016 path-separator correction.")
    print("Research rules changed: False")
    print("Frozen hashes changed: False")
    print("Original request locks changed: False")
    print("Remote request performed: False")
    print("API key accessed: False")


if __name__ == "__main__":
    main()
