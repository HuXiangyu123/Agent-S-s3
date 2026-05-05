"""Agent startup smoke test — run each time a new coding session starts.

Verifies:
1. Feishu domain layer imports cleanly
2. S3 execution layer imports cleanly
3. core pipeline (NL -> TestCase -> WorkflowPlan) works end-to-end
4. all existing feishu tests still pass
"""

import sys
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
            WorkflowPlan,
            PageDescriptor,
            FeishuState,
            LocatorResult,
            ActionLog,
            StepResult,
            RuntimeContext,
        )

        self.assertIsNotNone(FailureType)
        self.assertIsNotNone(TestCase)
        self.assertIsNotNone(WorkflowPlan)

    def test_feishu_testcases_import(self) -> None:
        from gui_agents.feishu.testcases.scenario_schema import (
            build_testcase,
            validate_testcase,
        )
        from gui_agents.feishu.testcases.nl_parser import parse_instruction

        self.assertTrue(callable(build_testcase))
        self.assertTrue(callable(parse_instruction))

    def test_feishu_planner_import(self) -> None:
        from gui_agents.feishu.planner.task_planner import plan_testcase
        from gui_agents.feishu.planner.workflow_selector import select_workflow
        from gui_agents.feishu.tooling.tool_router import build_feishu_tool_guidance
        from gui_agents.feishu.workflows.send_message_workflow import (
            SendMessageWorkflow,
        )
        from gui_agents.feishu.verifiers.assertion_verifier import AssertionVerifier
        from gui_agents.feishu.agents.feishu_worker import FeishuWorker

        self.assertTrue(callable(plan_testcase))
        self.assertTrue(callable(select_workflow))
        self.assertTrue(callable(build_feishu_tool_guidance))
        self.assertIsNotNone(SendMessageWorkflow)
        self.assertIsNotNone(AssertionVerifier)
        self.assertIsNotNone(FeishuWorker)

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
        from gui_agents.feishu.planner.task_planner import plan_testcase

        result = parse_instruction('在"测试群"发送"Hello World"并验证发送成功')
        self.assertEqual(result["product"], "im")
        self.assertEqual(len(result["steps"]), 3)

        plan = plan_testcase(result)
        self.assertEqual(plan["workflow"], "send_message")
        self.assertIsNone(plan["failure_type"])


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
