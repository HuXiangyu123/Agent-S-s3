"""Agent startup smoke test — run each time a new coding session starts.

Verifies:
1. Feishu domain layer imports cleanly
2. S3 execution layer imports cleanly
3. core semantic layer and feishu_agent guidance work end-to-end
4. all existing feishu tests still pass
"""

import unittest


class AgentStartupTest(unittest.TestCase):
    def test_feishu_contracts_import(self) -> None:
        from gui_agents.feishu.contracts import (
            ActionId,
            AssertionId,
            FailureType,
            TargetId,
            TestCase,
            TestStep,
            PageDescriptor,
            FeishuState,
            LocatorResult,
            ActionLog,
            StepResult,
            RuntimeContext,
        )

        self.assertIsNotNone(FailureType)
        self.assertIsNotNone(TestCase)
        self.assertIsNotNone(RuntimeContext)

    def test_feishu_testcases_import(self) -> None:
        from gui_agents.feishu.testcases.scenario_schema import (
            build_testcase,
            validate_testcase,
        )
        from gui_agents.feishu.testcases.nl_parser import parse_instruction

        self.assertTrue(callable(build_testcase))
        self.assertTrue(callable(parse_instruction))

    def test_feishu_agent_guidance_import(self) -> None:
        from gui_agents.feishu.tooling.tool_router import build_feishu_tool_guidance
        from gui_agents.feishu.detectors.base_state_detector import detect_base_state
        from gui_agents.feishu.detectors.docs_state_detector import detect_docs_state
        from gui_agents.feishu.detectors.im_state_detector import detect_feishu_state
        from gui_agents.feishu.detectors.vc_state_detector import detect_vc_state
        from gui_agents.feishu.runtime import build_agentic_run_goal
        from gui_agents.feishu.reports.report_builder import ReportBuilder
        from gui_agents.feishu.reports.s3_runtime_recorder import S3RuntimeRecorder
        from gui_agents.feishu.maintenance.artifact_manager import ArtifactManager
        from gui_agents.feishu.verifiers.assertion_verifier import AssertionVerifier
        from gui_agents.s3.agents.grounding_feishu import WindowsFeishuACI

        self.assertTrue(callable(build_feishu_tool_guidance))
        self.assertTrue(callable(detect_base_state))
        self.assertTrue(callable(detect_docs_state))
        self.assertTrue(callable(detect_feishu_state))
        self.assertTrue(callable(detect_vc_state))
        self.assertTrue(callable(build_agentic_run_goal))
        self.assertIsNotNone(ReportBuilder)
        self.assertIsNotNone(S3RuntimeRecorder)
        self.assertIsNotNone(ArtifactManager)
        self.assertIsNotNone(AssertionVerifier)
        self.assertIsNotNone(WindowsFeishuACI)

    def test_s3_agents_import(self) -> None:
        try:
            from gui_agents.s3.agents.grounding import OSWorldACI
            from gui_agents.s3.agents.worker import Worker
        except ImportError as exc:
            self.skipTest(f"S3 agents unavailable in this env: {exc}")

        self.assertIsNotNone(OSWorldACI)
        self.assertIsNotNone(Worker)

    def test_core_pipeline_e2e(self) -> None:
        from gui_agents.feishu.testcases.nl_parser import parse_instruction
        from gui_agents.feishu.runtime import build_agentic_run_goal
        from gui_agents.feishu.tooling.tool_router import route_feishu_tools
        from gui_agents.feishu.detectors.base_state_detector import detect_base_state

        result = parse_instruction('在"测试群"发送"Hello World"并验证发送成功')
        self.assertEqual(result["product"], "im")
        self.assertEqual(len(result["steps"]), 3)

        guidance = route_feishu_tools(
            '在"测试群"发送"Hello World"并验证发送成功',
            {"ocr_text": "消息\n发送给 测试群\n发送"},
        )
        self.assertIn("feishu_type_message", guidance.preferred_tools)

        docs_result = parse_instruction("新建一个云文档，标题为“项目周报”。")
        self.assertEqual(docs_result["product"], "docs")
        self.assertEqual(docs_result["steps"][-1]["action"], "type_doc_title")

        base_result = parse_instruction("新建一个多维表格")
        self.assertEqual(base_result["product"], "base")
        self.assertEqual(base_result["steps"], [])
        self.assertTrue(base_result["artifacts"]["semantic_guidance_only"])

        base_guidance = route_feishu_tools(
            "新建一个多维表格",
            {"image_path": "tests/fixtures/base/点击新建后.png"},
            state=detect_base_state(
                {"image_path": "tests/fixtures/base/点击新建后.png"}
            ),
        )
        self.assertEqual(base_guidance.product, "base")
        self.assertIn("click", base_guidance.preferred_tools)

        vc_guidance = route_feishu_tools(
            "发起视频会议并验证入会成功",
            {"ocr_text": "视频会议\n发起会议\n加入会议\n历史记录"},
        )
        self.assertEqual(vc_guidance.product, "vc")
        self.assertEqual(vc_guidance.next_step_focus, "start_meeting_card")
        self.assertIn("feishu_vc_click_start_card", vc_guidance.preferred_tools)

        vc_goal = build_agentic_run_goal("发起视频会议并验证进入成功")
        self.assertEqual(vc_goal["product"], "vc")
        self.assertEqual(vc_goal["assertions"][0]["assertion"], "vc_meeting_active")


def load_tests(loader, standard_tests, pattern):
    """Aggregate startup checks + all existing feishu tests."""
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(AgentStartupTest))
    suite.addTests(
        loader.discover("tests/feishu", pattern="test_*.py", top_level_dir=".")
    )
    return suite


if __name__ == "__main__":
    unittest.main()
