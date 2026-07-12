from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PaperSchedulerFilesTests(
    unittest.TestCase
):
    def test_installer_uses_hourly_schedule(
        self,
    ) -> None:
        text = (
            ROOT
            / "install_exp003_paper_task.ps1"
        ).read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "New-TimeSpan -Hours 1",
            text,
        )

        self.assertIn(
            "MinuteAfterHour = 7",
            text,
        )

        self.assertIn(
            "-MultipleInstances IgnoreNew",
            text,
        )

    def test_scheduled_runner_is_paper_only(
        self,
    ) -> None:
        text = (
            ROOT
            / "run_exp003_paper_task.ps1"
        ).read_text(
            encoding="utf-8"
        ).lower()

        self.assertIn(
            "run_exp003_paper_update.py",
            text,
        )

        self.assertNotIn(
            "api_key",
            text,
        )

        self.assertNotIn(
            "create_order",
            text,
        )

        self.assertNotIn(
            "place_order",
            text,
        )

    def test_scheduler_logs_are_ignored(
        self,
    ) -> None:
        text = (
            ROOT / ".gitignore"
        ).read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "paper_logs/",
            text,
        )


if __name__ == "__main__":
    unittest.main()
