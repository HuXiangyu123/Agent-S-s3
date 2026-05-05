"""Minimal explicit workflow for IM send_message."""

from __future__ import annotations

from typing import Any, TypedDict

from gui_agents.feishu.contracts import FeishuState, RuntimeContext, WorkflowPlan


class WorkflowStep(TypedDict):
    step_id: str
    stage: str
    action: str
    target: str | None
    params: dict[str, Any]
    success_gate: str | None
    fallback: str | None
    retry_limit: int


def _build_steps(chat_name: str, message_text: str) -> list[WorkflowStep]:
    return [
        WorkflowStep(
            step_id="wf_step_1",
            stage="ENSURE_CHAT_OPEN",
            action="open_chat",
            target="conversation_list_item",
            params={"chat_name": chat_name},
            success_gate="chat_title_matched",
            fallback="replan",
            retry_limit=0,
        ),
        WorkflowStep(
            step_id="wf_step_2",
            stage="TYPE_MESSAGE",
            action="type_message",
            target="message_input",
            params={"chat_name": chat_name, "text": message_text},
            success_gate="message_input_contains_text",
            fallback="refocus_message_input",
            retry_limit=1,
        ),
        WorkflowStep(
            step_id="wf_step_3",
            stage="SEND_MESSAGE",
            action="send_message",
            target="send_button",
            params={"text": message_text},
            success_gate="message_sent",
            fallback="retry_send_once",
            retry_limit=1,
        ),
    ]


class SendMessageWorkflow:
    workflow_id = "send_message"

    def __init__(self, plan: WorkflowPlan) -> None:
        if plan.get("workflow") != self.workflow_id:
            raise ValueError("send_message workflow requires workflow=send_message")

        params = plan.get("workflow_params", {})
        chat_name = params.get("chat_name")
        message_text = params.get("message_text")
        if not chat_name or not message_text:
            raise ValueError(
                "send_message workflow requires chat_name and message_text"
            )

        self.chat_name = str(chat_name)
        self.message_text = str(message_text)
        self.entry_assertions = list(plan.get("entry_assertions", []))
        self.preconditions = list(plan.get("preconditions", []))
        self._steps = _build_steps(self.chat_name, self.message_text)

    def steps(self) -> list[WorkflowStep]:
        return [WorkflowStep(**step) for step in self._steps]

    def next_step(
        self,
        state: FeishuState | None,
        runtime_context: RuntimeContext | dict[str, Any] | None,
    ) -> WorkflowStep | None:
        del state

        completed_step_ids: set[str] = set()
        if runtime_context:
            for result in runtime_context.get("step_results", []):
                if result.get("status") == "passed":
                    step_id = result.get("step_id")
                    if step_id:
                        completed_step_ids.add(str(step_id))

        for step in self._steps:
            if step["step_id"] not in completed_step_ids:
                return WorkflowStep(**step)
        return None

    def is_done(
        self,
        state: FeishuState | None,
        runtime_context: RuntimeContext | dict[str, Any] | None,
    ) -> bool:
        del state
        return self.next_step(None, runtime_context) is None


def build_send_message_workflow(plan: WorkflowPlan) -> SendMessageWorkflow:
    return SendMessageWorkflow(plan)
