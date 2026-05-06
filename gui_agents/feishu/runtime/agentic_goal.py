"""Instruction-derived semantic goals for agentic Feishu runtime verification."""

from __future__ import annotations

import hashlib
import re
from typing import Any, TypedDict

from gui_agents.feishu.testcases.nl_parser import parse_instruction


VC_KEYWORDS = (
    "视频会议",
    "发起会议",
    "开始会议",
    "加入会议",
    "会议 ID",
    "会议ID",
    "会议号",
    "会议码",
    "邀请",
)
DOCS_KEYWORDS = ("文档", "云文档", "标题", "分享")
BASE_KEYWORDS = ("多维表格", "Base", "base")
CALENDAR_KEYWORDS = ("日历", "日程", "会议室", "创建日程")
IM_KEYWORDS = ("消息", "聊天", "群", "会话", "回复", "发送")


class AgenticAssertionGoal(TypedDict):
    assertion: str
    expected: dict[str, Any]


class AgenticRunGoal(TypedDict):
    task_id: str
    product: str
    title: str
    assertions: list[AgenticAssertionGoal]


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword and keyword in text for keyword in keywords)


def _hashed_token(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:8]


def _extract_meeting_id(instruction: str) -> str | None:
    match = re.search(
        r"(?:会议\s*ID|会议ID|会议号|会议码)\s*(?:是|为|:|：)?\s*([A-Za-z0-9-]{4,})",
        instruction,
    )
    if match:
        return match.group(1).strip()
    return None


def _detect_product(instruction: str) -> str:
    if _contains_any(instruction, VC_KEYWORDS):
        return "vc"
    if _contains_any(instruction, BASE_KEYWORDS):
        return "base"
    if _contains_any(instruction, CALENDAR_KEYWORDS):
        return "calendar"
    if _contains_any(instruction, DOCS_KEYWORDS):
        return "docs"
    if _contains_any(instruction, IM_KEYWORDS):
        return "im"
    return "unknown"


def _expected_from_testcase(testcase: dict[str, Any]) -> dict[str, Any]:
    expected: dict[str, Any] = {}
    for step in testcase.get("steps", []):
        action = step.get("action")
        payload = step.get("payload") or {}
        if action == "open_chat" and step.get("target"):
            expected["chat_name"] = step["target"]
        if action == "type_message" and payload.get("text"):
            expected["message_text"] = payload["text"]
            expected["text"] = payload["text"]
        if action == "type_doc_title" and payload.get("text"):
            expected["doc_title"] = payload["text"]
            expected["title"] = payload["text"]
            expected["text"] = payload["text"]
        if action == "type_doc_body" and payload.get("text"):
            expected["body_text"] = payload["text"]
            expected["text"] = payload["text"]
    return expected


def _goal_from_testcase(testcase: dict[str, Any]) -> AgenticRunGoal:
    expected = _expected_from_testcase(testcase)
    return AgenticRunGoal(
        task_id=testcase["id"],
        product=testcase["product"],
        title=testcase["title"],
        assertions=[
            AgenticAssertionGoal(assertion=assertion, expected=dict(expected))
            for assertion in testcase.get("assertions", [])
        ],
    )


def _build_vc_goal(instruction: str) -> AgenticRunGoal:
    meeting_id = _extract_meeting_id(instruction)
    expected = {"meeting_id": meeting_id} if meeting_id else {}

    if any(
        keyword in instruction
        for keyword in ("分享邀请", "电话邀请", "复制入会信息", "邀请")
    ):
        task_id = "agentic_vc_open_invite_dialog"
        title = "打开会议邀请面板"
        assertions = [
            AgenticAssertionGoal(
                assertion="vc_invite_dialog_opened",
                expected=dict(expected),
            )
        ]
    elif any(
        keyword in instruction
        for keyword in ("加入会议", "会议 ID", "会议ID", "会议号", "会议码")
    ):
        task_id = "agentic_vc_join_meeting"
        title = "加入视频会议并验证进入成功"
        assertions = [
            AgenticAssertionGoal(assertion="vc_joined", expected=dict(expected))
        ]
    elif any(
        keyword in instruction
        for keyword in ("发起会议", "发起视频会议", "开始会议", "开始视频会议")
    ):
        task_id = "agentic_vc_start_meeting"
        title = "发起视频会议并验证进入成功"
        assertions = [
            AgenticAssertionGoal(assertion="vc_meeting_active", expected=dict(expected))
        ]
    else:
        task_id = "agentic_vc_home"
        title = "打开视频会议主页"
        assertions = [
            AgenticAssertionGoal(assertion="vc_home_ready", expected=dict(expected))
        ]

    return AgenticRunGoal(
        task_id=task_id,
        product="vc",
        title=title,
        assertions=assertions,
    )


def build_agentic_run_goal(instruction: str) -> AgenticRunGoal:
    normalized = instruction.strip()
    if not normalized:
        return AgenticRunGoal(
            task_id=f"agentic_unknown_{_hashed_token(instruction)}",
            product="unknown",
            title="",
            assertions=[],
        )

    product = _detect_product(normalized)
    if product == "vc":
        return _build_vc_goal(normalized)

    try:
        testcase = parse_instruction(normalized)
    except ValueError:
        testcase = None

    if testcase is not None:
        return _goal_from_testcase(testcase)

    return AgenticRunGoal(
        task_id=f"agentic_{product}_{_hashed_token(normalized)}",
        product=product,
        title=normalized,
        assertions=[],
    )
