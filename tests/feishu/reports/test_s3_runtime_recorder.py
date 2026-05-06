import json
import tempfile
import unittest
from pathlib import Path

from gui_agents.feishu.reports.s3_runtime_recorder import S3RuntimeRecorder


class TestS3RuntimeRecorder(unittest.TestCase):
    def _vc_observation(self, filename: str) -> dict:
        return {"image_path": str(Path("tests/fixtures/vc") / filename)}

    def _unknown_live_observation(self) -> dict:
        return {"ocr_text": "Qs\nSHMESREWN"}

    def test_records_agent_s3_runtime_and_writes_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = S3RuntimeRecorder(artifact_root=tmpdir)

            runtime = recorder.start("发起视频会议并验证进入成功")
            recorder.record_observation(1, {"screenshot": b"png"})
            recorder.record_action(
                1,
                "import pyautogui\npyautogui.click(10, 20)\n",
                "executed",
            )
            paths = recorder.finalize(
                "completed",
                final_observation=self._vc_observation("正在会议的页面.png"),
            )

            self.assertIsNotNone(paths)
            assert paths is not None
            summary = json.loads(Path(paths["summary"]).read_text("utf-8"))
            self.assertEqual(summary["intent"], "agent_s3_feishu")
            self.assertEqual(summary["status"], "completed")
            self.assertEqual(summary["product"], "vc")
            self.assertEqual(summary["task_id"], "agentic_vc_start_meeting")
            self.assertGreaterEqual(summary["passed_steps"], 1)
            self.assertEqual(summary["failed_steps"], 0)
            self.assertEqual(summary["assertions"][0]["name"], "vc_meeting_active")
            self.assertTrue(summary["assertions"][0]["passed"])
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

    def test_final_verification_can_flip_done_run_to_failed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = S3RuntimeRecorder(artifact_root=tmpdir)

            recorder.start("发起视频会议并验证进入成功")
            recorder.record_action(
                1,
                "agent.done()",
                "done",
            )
            paths = recorder.finalize(
                "completed",
                final_observation=self._vc_observation("会议主页面.png"),
            )

            self.assertIsNotNone(paths)
            assert paths is not None
            summary = json.loads(Path(paths["summary"]).read_text("utf-8"))
            self.assertEqual(summary["status"], "failed")
            self.assertEqual(summary["failure_type"], "verification")
            self.assertEqual(summary["assertions"][0]["name"], "vc_meeting_active")
            self.assertFalse(summary["assertions"][0]["passed"])

    def test_final_verification_uses_runtime_hint_for_unknown_vc_meeting_state(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = S3RuntimeRecorder(artifact_root=tmpdir)

            runtime = recorder.start("发起视频会议并验证进入成功")
            recorder.record_action(
                1,
                "agent.done()",
                "done",
            )
            paths = recorder.finalize(
                "completed",
                final_observation=self._unknown_live_observation(),
            )

            self.assertIsNotNone(paths)
            assert paths is not None
            summary = json.loads(Path(paths["summary"]).read_text("utf-8"))
            self.assertEqual(summary["status"], "completed")
            self.assertTrue(summary["assertions"][0]["passed"])
            self.assertEqual(runtime["page_id"], "vc_meeting_active")
            self.assertEqual(runtime["final_state_source"], "runtime_semantic_hint")
            self.assertEqual(
                runtime["step_results"][-1]["locator_result"]["strategy"],
                "runtime_semantic_hint",
            )

    def test_final_verification_uses_runtime_hint_for_unknown_vc_invite_dialog(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = S3RuntimeRecorder(artifact_root=tmpdir)

            runtime = recorder.start("在当前视频会议中打开邀请面板")
            recorder.record_action(
                1,
                "agent.done()",
                "done",
            )
            paths = recorder.finalize(
                "completed",
                final_observation=self._unknown_live_observation(),
            )

            self.assertIsNotNone(paths)
            assert paths is not None
            summary = json.loads(Path(paths["summary"]).read_text("utf-8"))
            self.assertEqual(summary["status"], "completed")
            self.assertTrue(summary["assertions"][0]["passed"])
            self.assertEqual(runtime["page_id"], "vc_invite_dialog")
            self.assertEqual(runtime["final_state_source"], "runtime_semantic_hint")


if __name__ == "__main__":
    unittest.main()
