import unittest

from gui_agents.feishu.runtime import build_agentic_run_goal


class TestAgenticRunGoal(unittest.TestCase):
    def test_builds_vc_start_goal(self) -> None:
        goal = build_agentic_run_goal("发起视频会议并验证进入成功")

        self.assertEqual(goal["product"], "vc")
        self.assertEqual(goal["task_id"], "agentic_vc_start_meeting")
        self.assertEqual(goal["assertions"][0]["assertion"], "vc_meeting_active")

    def test_builds_vc_join_goal(self) -> None:
        goal = build_agentic_run_goal("加入会议，会议ID为123456789")

        self.assertEqual(goal["product"], "vc")
        self.assertEqual(goal["task_id"], "agentic_vc_join_meeting")
        self.assertEqual(goal["assertions"][0]["assertion"], "vc_joined")
        self.assertEqual(goal["assertions"][0]["expected"]["meeting_id"], "123456789")

    def test_builds_vc_invite_goal(self) -> None:
        goal = build_agentic_run_goal("在当前视频会议中打开邀请面板")

        self.assertEqual(goal["product"], "vc")
        self.assertEqual(goal["task_id"], "agentic_vc_open_invite_dialog")
        self.assertEqual(goal["assertions"][0]["assertion"], "vc_invite_dialog_opened")

    def test_reuses_structured_im_testcase_for_runtime_goal(self) -> None:
        goal = build_agentic_run_goal('在"bot功能测试"发送"hello"并验证发送成功')

        self.assertEqual(goal["product"], "im")
        self.assertTrue(goal["task_id"].startswith("tc_im_"))
        self.assertEqual(goal["assertions"][-1]["assertion"], "message_sent")
        self.assertEqual(goal["assertions"][-1]["expected"]["message_text"], "hello")


if __name__ == "__main__":
    unittest.main()
