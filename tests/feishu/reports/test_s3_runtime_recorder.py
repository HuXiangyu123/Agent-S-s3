import json
import tempfile
import unittest
from pathlib import Path

from gui_agents.feishu.reports.s3_runtime_recorder import S3RuntimeRecorder


class TestS3RuntimeRecorder(unittest.TestCase):
    def test_records_agent_s3_runtime_and_writes_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = S3RuntimeRecorder(artifact_root=tmpdir)

            runtime = recorder.start("打开消息并发送 hello")
            recorder.record_observation(1, {"screenshot": b"png"})
            recorder.record_action(
                1,
                "import pyautogui\npyautogui.click(10, 20)\n",
                "executed",
            )
            paths = recorder.finalize("completed")

            self.assertIsNotNone(paths)
            assert paths is not None
            summary = json.loads(Path(paths["summary"]).read_text("utf-8"))
            self.assertEqual(summary["workflow"], "agent_s3_feishu")
            self.assertEqual(summary["status"], "completed")
            self.assertEqual(summary["passed_steps"], 1)
            self.assertEqual(summary["failed_steps"], 0)
            self.assertTrue(runtime["screenshots"])
            self.assertTrue(Path(runtime["screenshots"][0]).exists())
            self.assertIn("pyautogui.click", Path(paths["actions"]).read_text("utf-8"))

    def test_marks_runtime_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = S3RuntimeRecorder(artifact_root=tmpdir)

            recorder.start("打开消息")
            recorder.record_action(
                1,
                "raise RuntimeError('boom')",
                "failed",
                "RuntimeError('boom')",
            )
            paths = recorder.finalize()

            self.assertIsNotNone(paths)
            assert paths is not None
            summary = json.loads(Path(paths["summary"]).read_text("utf-8"))
            self.assertEqual(summary["status"], "failed")
            self.assertEqual(summary["failed_steps"], 1)
            self.assertEqual(summary["failure_type"], "runtime")


if __name__ == "__main__":
    unittest.main()
