"""Rule-based parser for natural-language Feishu test instructions."""

from __future__ import annotations

import re

from gui_agents.feishu.contracts import TestCase
from gui_agents.feishu.testcases.scenario_schema import build_testcase


QUOTED_TEXT_PATTERN = re.compile(r"""["'“”‘’]([^"'“”‘’]+)["'“”‘’]""")
UNSUPPORTED_INTENT_KEYWORDS = (
    "表情",
    "emoji",
    "随机",
    "右侧",
    "表情图标",
)


def _extract_quoted_texts(instruction: str) -> list[str]:
    return [match.strip() for match in QUOTED_TEXT_PATTERN.findall(instruction)]


def _detect_product(instruction: str) -> str:
    # Current milestone supports IM only; Docs/Calendar will be added later.
    return "im"


def _reject_unsupported_intents(instruction: str) -> None:
    matched = [
        keyword
        for keyword in UNSUPPORTED_INTENT_KEYWORDS
        if keyword.lower() in instruction.lower()
    ]
    if matched:
        raise ValueError(
            "current Feishu MVP supports text send_message only; unsupported intents: "
            + ", ".join(matched)
        )


def _extract_chat_name(instruction: str, quoted_texts: list[str]) -> str | None:
    if len(quoted_texts) >= 2:
        return quoted_texts[0]

    for pattern in (
        r"打开(?:消息中的)?(.+?)(?:群聊|会话|聊天|对话)",
        r"(?:在|向|给)(.+?)(?:发送|发|回复|输入)",
    ):
        match = re.search(pattern, instruction)
        if match:
            candidate = match.group(1).strip(" 的里中到给向在消息")
            if candidate:
                return candidate

    # Current milestone supports a single chat target only. Expressions such as
    # "在测试群和产品群发送消息" are not disambiguated yet and will need a richer
    # parser once multi-target workflows are introduced.
    return None


def _extract_message_text(instruction: str, quoted_texts: list[str]) -> str | None:
    if len(quoted_texts) >= 2:
        return quoted_texts[1]

    if len(quoted_texts) == 1 and any(
        keyword in instruction for keyword in ("发送", "发消息", "回复", "输入")
    ):
        return quoted_texts[0]

    for pattern in (
        r"消息发送框输入(.+?)(?:并且|并|然后|再|，|。|$)",
        r"(?:输入|发送|回复|发)(.+?)(?:并且|并|然后|再|，|。|$)",
    ):
        match = re.search(pattern, instruction)
        if match:
            candidate = match.group(1).strip("消息内容为:： ")
            candidate = re.sub(r"^(?:框输入|输入)", "", candidate).strip()
            if candidate:
                return candidate

    return None


def parse_instruction(instruction: str) -> TestCase:
    normalized = instruction.strip()
    if not normalized:
        raise ValueError("instruction cannot be empty")

    _reject_unsupported_intents(normalized)
    product = _detect_product(normalized)
    quoted_texts = _extract_quoted_texts(normalized)
    chat_name = _extract_chat_name(normalized, quoted_texts)
    message_text = _extract_message_text(normalized, quoted_texts)
    if not chat_name:
        raise ValueError("unable to extract chat_name from instruction")
    if not message_text:
        raise ValueError("unable to extract message_text from instruction")

    title = f"在{chat_name}发送消息并验证发送成功"

    return build_testcase(
        product=product,
        title=title,
        steps=[
            {
                "action": "open_chat",
                "target": chat_name,
                "payload": None,
                "assertion": "chat_title_matched",
            },
            {
                "action": "type_message",
                "target": "message_input",
                "payload": {"text": message_text},
                "assertion": "message_input_contains_text",
            },
            {
                "action": "send_message",
                "target": "send_button",
                "payload": None,
                "assertion": "message_sent",
            },
        ],
    )
