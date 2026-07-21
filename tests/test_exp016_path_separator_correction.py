from __future__ import annotations

from pathlib import Path
import re
import unittest

from apply_exp016_path_separator_correction import (
    HELPER_BLOCK,
    LOAD_JSON_BLOCK,
    NEW_PATH_COMPARISON,
    apply_correction,
)


PROJECT_DIR = Path(__file__).resolve().parents[1]


def _fixture() -> str:
    return (
        "from pathlib import Path\n"
        "from typing import Any\n"
        "import json\n"
        "PROJECT_DIR = Path('.')\n\n"
        + LOAD_JSON_BLOCK
        + "\n"
        + "def verify(record, expected, output):\n"
        + "    value = {\n"
        + '            "local_path": str(output.relative_to(PROJECT_DIR)),\n'
        + "    }\n"
        + "    if (\n"
        + "        False\n"
        + '            or record.get("local_path") != expected["local_path"]\n'
        + "    ):\n"
        + "        raise RuntimeError\n"
        + '    path = PROJECT_DIR / record["local_path"]\n'
        + "    return value, path\n\n"
        + "def audit(record, output):\n"
        + "    value = {\n"
        + '        "local_path": str(output.relative_to(PROJECT_DIR)),\n'
        + "    }\n"
        + '    path = PROJECT_DIR / record["local_path"]\n'
        + "    return value, path\n"
    )


class Exp016PathSeparatorCorrectionTests(unittest.TestCase):
    def test_mixed_indentation_fixture_is_corrected(self) -> None:
        corrected = apply_correction(_fixture())
        compile(corrected, "<corrected>", "exec")
        self.assertIn(HELPER_BLOCK, corrected)
        self.assertIn(NEW_PATH_COMPARISON, corrected)
        self.assertEqual(corrected.count(".as_posix()"), 2)
        self.assertEqual(
            len(
                re.findall(
                    r'(?m)^\s*path = '
                    r'_project_path_from_relative\(record\["local_path"\]\)$',
                    corrected,
                )
            ),
            2,
        )

    def test_windows_and_posix_paths_normalize_equally(self) -> None:
        corrected = apply_correction(_fixture())
        namespace: dict[str, object] = {}
        exec(compile(corrected, "<corrected>", "exec"), namespace)
        normalize = namespace["_portable_relative_path"]
        self.assertEqual(
            normalize(r"data\EXP-016\nq_f_samples\raw\sample.parquet"),
            normalize("data/EXP-016/nq_f_samples/raw/sample.parquet"),
        )

    def test_project_path_rejects_parent_traversal(self) -> None:
        corrected = apply_correction(_fixture())
        namespace: dict[str, object] = {}
        exec(compile(corrected, "<corrected>", "exec"), namespace)
        resolver = namespace["_project_path_from_relative"]
        with self.assertRaisesRegex(RuntimeError, "safe project-relative"):
            resolver("../outside.txt")

    def test_correction_is_one_time(self) -> None:
        corrected = apply_correction(_fixture())
        with self.assertRaisesRegex(RuntimeError, "already appears applied"):
            apply_correction(corrected)

    def test_repository_runner_contains_correction_after_application(self) -> None:
        runner = PROJECT_DIR / "run_exp016_audit.py"
        if not runner.is_file():
            self.skipTest("Repository runner is not present in package fixture.")
        source = runner.read_text(encoding="utf-8")
        self.assertIn("def _portable_relative_path", source)
        self.assertIn(NEW_PATH_COMPARISON, source)
        self.assertEqual(source.count(".as_posix()"), 2)
        self.assertNotIn(
            'record.get("local_path") != expected["local_path"]',
            source,
        )
        self.assertNotIn(
            '"local_path": str(output.relative_to(PROJECT_DIR)),',
            source,
        )
        self.assertEqual(
            len(
                re.findall(
                    r'(?m)^\s*path = '
                    r'_project_path_from_relative\(record\["local_path"\]\)$',
                    source,
                )
            ),
            2,
        )


if __name__ == "__main__":
    unittest.main()
