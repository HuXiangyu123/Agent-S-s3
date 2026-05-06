import json
import tempfile
import unittest
from pathlib import Path

from gui_agents.feishu.maintenance.artifact_manager import ArtifactManager


class TestArtifactManager(unittest.TestCase):
    def test_writes_json_text_and_jsonl_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ArtifactManager(tmpdir)

            summary_path = manager.write_json("run_1", "summary.json", {"status": "ok"})
            report_path = manager.write_text("run_1", "report.md", "# report\n")
            actions_path = manager.write_actions_jsonl(
                "run_1",
                [{"step_id": "step_1", "status": "passed"}],
            )

            self.assertEqual(
                json.loads(Path(summary_path).read_text("utf-8"))["status"],
                "ok",
            )
            self.assertEqual(Path(report_path).read_text("utf-8"), "# report\n")
            self.assertIn(
                '"step_id": "step_1"',
                Path(actions_path).read_text("utf-8"),
            )

    def test_writes_screenshot_into_run_subdirectory(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ArtifactManager(tmpdir)
            screenshot_path = manager.write_screenshot(
                "run_2",
                "step_1_post_action",
                b"png",
            )

            path = Path(screenshot_path)
            self.assertTrue(path.exists())
            self.assertEqual(path.read_bytes(), b"png")
            self.assertEqual(path.parent.name, "screenshots")
