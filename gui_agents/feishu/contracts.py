"""Shared contracts for the Feishu GUI agent domain layer."""

from __future__ import annotations

from typing import Any, Literal, NotRequired, TypedDict

FailureType = Literal[
    "recognition",
    "location",
    "action",
    "verification",
    "timeout",
    "precondition",
]

ActionId = Literal[
    "open_chat",
    "focus_message_input",
    "type_message",
    "send_message",
]

TargetId = Literal[
    "global_search_entry",
    "conversation_list_item",
    "conversation_search_entry",
    "conversation_search_close_button",
    "conversation_search_result_item",
    "search_result_item",
    "message_input",
    "send_button",
]

AssertionId = Literal[
    "chat_title_matched",
    "message_input_contains_text",
    "message_sent",
]


class TestStep(TypedDict):
    step_id: str
    action: ActionId
    target: str | None
    payload: dict[str, Any] | None
    assertion: str | None


class TestCase(TypedDict):
    id: str
    product: str
    title: str
    preconditions: list[str]
    steps: list[TestStep]
    assertions: list[str]
    artifacts: NotRequired[dict[str, Any]]


class WorkflowPlan(TypedDict):
    workflow: str | None
    reason: str
    workflow_params: dict[str, Any]
    entry_assertions: list[str]
    preconditions: list[str]
    failure_type: FailureType | None
    failure_reason: str | None


class PageDescriptor(TypedDict):
    page_id: str
    page_type: str
    display_name: str
    layout_hints: dict[str, Any]
    key_regions: dict[str, Any]
    text_anchors: list[str]
    supported_workflows: list[str]
    ui_version_tag: str


class FeishuState(TypedDict):
    page_type: str
    product: str
    chat_name: str | None
    message_input_visible: bool
    send_button_visible: bool
    search_box_visible: bool
    modal_type: str | None
    last_error_banner: str | None
    product_state: dict[str, Any]


class LocatorResult(TypedDict):
    matched: bool
    strategy: str
    x: int | None
    y: int | None
    confidence: float
    bbox: list[int] | None
    page_id: str | None
    failure_type: NotRequired[FailureType | None]
    failure_reason: NotRequired[str | None]


class ActionLog(TypedDict):
    timestamp: str
    step_id: str
    stage: str
    action: str
    target: str | None
    params: dict[str, Any]
    status: str


class StepResult(TypedDict):
    step_id: str
    stage: str
    action: str
    target: str | None
    status: str
    locator_result: dict[str, Any]
    verification_result: dict[str, Any]
    failure_type: FailureType | None
    failure_reason: str | None


class RuntimeContext(TypedDict):
    run_id: str
    status: str
    workflow: str | None
    workflow_params: dict[str, Any]
    page_id: str | None
    precondition_results: list[dict[str, Any]]
    action_logs: list[ActionLog]
    screenshots: list[str]
    step_results: list[StepResult]
    failure_type: FailureType | None
    failure_reason: str | None
    started_at: str
