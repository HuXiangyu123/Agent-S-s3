import unittest

from gui_agents.feishu.contracts import RuntimeContext, WorkflowPlan
from gui_agents.feishu.workflows.send_message_workflow import (
    SendMessageWorkflow,
    build_send_message_workflow,
)


class TestSendMessageWorkflow(unittest.TestCase):
    def _plan(self) -> WorkflowPlan:
        return WorkflowPlan(
            workflow="send_message",
            reason="matched product=im and action intent=send_message",
            workflow_params={
                "chat_name": "测试群",
                "message_text": "Hello World",
            },
            entry_assertions=["chat_title_matched"],
            preconditions=["飞书桌面端已登录"],
            failure_type=None,
            failure_reason=None,
        )

    def test_builds_explicit_send_message_steps(self) -> None:
        workflow = build_send_message_workflow(self._plan())

        steps = workflow.steps()

        self.assertEqual(len(steps), 3)
        self.assertEqual(steps[0]["stage"], "ENSURE_CHAT_OPEN")
        self.assertEqual(steps[0]["action"], "open_chat")
        self.assertEqual(steps[0]["success_gate"], "chat_title_matched")
        self.assertEqual(steps[1]["stage"], "TYPE_MESSAGE")
        self.assertEqual(steps[1]["params"]["text"], "Hello World")
        self.assertEqual(steps[2]["stage"], "SEND_MESSAGE")
        self.assertEqual(steps[2]["success_gate"], "message_sent")

    def test_next_step_advances_by_passed_step_results(self) -> None:
        workflow = SendMessageWorkflow(self._plan())
        runtime_context = RuntimeContext(
            run_id="run-1",
            status="running",
            workflow="send_message",
            workflow_params={"chat_name": "测试群", "message_text": "Hello World"},
            page_id="im_chat_main",
            precondition_results=[],
            action_logs=[],
            screenshots=[],
            step_results=[
                {
                    "step_id": "wf_step_1",
                    "stage": "ENSURE_CHAT_OPEN",
                    "action": "open_chat",
                    "target": "conversation_list_item",
                    "status": "passed",
                    "locator_result": {},
                    "verification_result": {"passed": True},
                    "failure_type": None,
                    "failure_reason": None,
                }
            ],
            failure_type=None,
            failure_reason=None,
            started_at="2026-05-05T20:30:00+08:00",
        )

        next_step = workflow.next_step(None, runtime_context)

        self.assertIsNotNone(next_step)
        self.assertEqual(next_step["step_id"], "wf_step_2")
        self.assertFalse(workflow.is_done(None, runtime_context))

    def test_is_done_after_all_steps_pass(self) -> None:
        workflow = SendMessageWorkflow(self._plan())
        runtime_context = RuntimeContext(
            run_id="run-1",
            status="passed",
            workflow="send_message",
            workflow_params={"chat_name": "测试群", "message_text": "Hello World"},
            page_id="im_chat_main",
            precondition_results=[],
            action_logs=[],
            screenshots=[],
            step_results=[
                {
                    "step_id": "wf_step_1",
                    "stage": "ENSURE_CHAT_OPEN",
                    "action": "open_chat",
                    "target": "conversation_list_item",
                    "status": "passed",
                    "locator_result": {},
                    "verification_result": {"passed": True},
                    "failure_type": None,
                    "failure_reason": None,
                },
                {
                    "step_id": "wf_step_2",
                    "stage": "TYPE_MESSAGE",
                    "action": "type_message",
                    "target": "message_input",
                    "status": "passed",
                    "locator_result": {},
                    "verification_result": {"passed": True},
                    "failure_type": None,
                    "failure_reason": None,
                },
                {
                    "step_id": "wf_step_3",
                    "stage": "SEND_MESSAGE",
                    "action": "send_message",
                    "target": "send_button",
                    "status": "passed",
                    "locator_result": {},
                    "verification_result": {"passed": True},
                    "failure_type": None,
                    "failure_reason": None,
                },
            ],
            failure_type=None,
            failure_reason=None,
            started_at="2026-05-05T20:30:00+08:00",
        )

        self.assertIsNone(workflow.next_step(None, runtime_context))
        self.assertTrue(workflow.is_done(None, runtime_context))

    def test_rejects_non_send_message_plan(self) -> None:
        plan = self._plan()
        plan["workflow"] = "unsupported"

        with self.assertRaises(ValueError):
            SendMessageWorkflow(plan)


if __name__ == "__main__":
    unittest.main()
