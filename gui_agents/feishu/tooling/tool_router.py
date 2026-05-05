"""State-aware Feishu tool routing for the S3 worker."""

from __future__ import annotations

import re
from typing import Iterable

from gui_agents.feishu.contracts import FeishuState
from gui_agents.feishu.detectors.im_state_detector import detect_feishu_state

from .tool_contracts import FeishuToolRecommendation
from .tool_registry import get_tool_specs


COMPOSE_MESSAGE_KEYWORDS = (
    "发送",
    "发消息",
    "回复",
    "消息",
    "输入",
    "鍙戦€?",
    "鍥炲",
    "娑堟伅",
    "杈撳叆",
)

SEND_MESSAGE_KEYWORDS = (
    "发送",
    "回复",
    "回车",
    "enter",
    "鍙戦€?",
    "鍥炲",
    "鍥炶溅",
)

SEARCH_KEYWORDS = (
    "搜索",
    "查找",
    "检索",
    "定位",
    "鎼滅储",
    "鏌ユ壘",
    "妫€绱?",
    "瀹氫綅",
)

EMOJI_KEYWORDS = (
    "表情",
    "emoji",
    "颜文字",
    "琛ㄦ儏",
    "棰滄枃瀛?",
)

OPEN_CHAT_KEYWORDS = (
    "群",
    "群聊",
    "会话",
    "聊天",
    "消息中的",
    "缇?",
    "浼氳瘽",
    "鑱婂ぉ",
    "娑堟伅涓殑",
)

BROWSER_SURFACE_KEYWORDS = (
    "文档",
    "云文档",
    "分享",
    "浏览器",
    "鏂囨。",
    "浜戞枃妗?",
    "鍒嗕韩",
    "娴忚鍣?",
)


def _contains_any(text: str, keywords: Iterable[str]) -> bool:
    return any(keyword and keyword in text for keyword in keywords)


def _ordered_unique(items: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            ordered.append(item)
    return tuple(ordered)


def _remove_tool(items: list[str], tool_name: str) -> None:
    while tool_name in items:
        items.remove(tool_name)


def _detect_intents(instruction: str) -> set[str]:
    intents: set[str] = set()
    if _contains_any(instruction, COMPOSE_MESSAGE_KEYWORDS):
        intents.add("compose_message")
    if _contains_any(instruction, SEND_MESSAGE_KEYWORDS):
        intents.add("send_message")
    if _contains_any(instruction, SEARCH_KEYWORDS):
        intents.add("search")
    if _contains_any(instruction, EMOJI_KEYWORDS):
        intents.add("emoji")
    if _contains_any(instruction, OPEN_CHAT_KEYWORDS):
        intents.add("open_chat")
    if _contains_any(instruction, BROWSER_SURFACE_KEYWORDS):
        intents.add("browser_surface")
    return intents


def _extract_target_chat_name(instruction: str) -> str | None:
    patterns = (
        r'(?:打开消息中的|打开|进入)\s*["“]?([^"”\n]+?)["”]?(?:群聊|群|会话|聊天)',
        r'(?:在|向|给)\s*["“]([^"”\n]+)["”]\s*(?:群聊|群|会话|聊天)?(?:中)?(?:发送|发|回复)',
        r'(?:在|向|给)\s*["“]?([^"”\n]+?)["”]?(?:群聊|群|会话|聊天)?(?:中)?(?:发送|发|回复)',
        r'(?:鎵撳紑娑堟伅涓殑|鎵撳紑|杩涘叆)\s*["鈥淽]?([^"鈥漒n]+?)["鈥漖]?(?:缇よ亰|缇?|浼氳瘽|鑱婂ぉ)',
        r'(?:鍦?|鍚?|缁?)[\s"]*([^"\n]+?)(?:缇よ亰|缇?|浼氳瘽|鑱婂ぉ)?(?:涓?)?(?:鍙戦€?|鍙?|鍥炲)',
    )
    for pattern in patterns:
        match = re.search(pattern, instruction)
        if match:
            return match.group(1).strip()
    return None


def _build_state_summary(state: FeishuState) -> str:
    parts = [
        f"page_type={state.get('page_type', 'unknown')}",
        f"product={state.get('product', 'unknown')}",
    ]
    if state.get("chat_name"):
        parts.append(f"chat={state['chat_name']}")
    if state.get("message_input_visible"):
        parts.append("message_input=visible")
    if state.get("send_button_visible"):
        parts.append("send_button=visible")
    if state.get("search_box_visible"):
        parts.append("search_box=visible")

    product_state = state.get("product_state", {})
    if product_state.get("draft_present"):
        parts.append("draft=present")
    if product_state.get("send_button_enabled"):
        parts.append("send_button=enabled")
    if product_state.get("local_search_result_list_visible"):
        parts.append("conversation_search_results=visible")
    if product_state.get("search_result_list_visible"):
        parts.append("global_search_results=visible")

    return ", ".join(parts)


def route_feishu_tools(
    instruction: str,
    observation: dict,
    state: FeishuState | None = None,
) -> FeishuToolRecommendation:
    state = state or detect_feishu_state(observation)
    page_type = state.get("page_type", "unknown")
    intents = _detect_intents(instruction)
    target_chat_name = _extract_target_chat_name(instruction)
    detected_chat_name = state.get("chat_name")
    product_state = state.get("product_state", {})
    draft_present = bool(product_state.get("draft_present"))

    enabled_tools = ["feishu_focus", "feishu_click", "feishu_type", "hotkey", "wait"]
    preferred_tools = ["feishu_focus"]
    discouraged_tools: list[str] = []
    hints: list[str] = []
    rationale: list[str] = []
    next_step_focus = "current_feishu_surface"

    if page_type == "shell_search":
        preferred_tools.extend(["feishu_type", "feishu_click", "hotkey"])
        discouraged_tools.extend(["click", "type"])
        next_step_focus = "global_search_entry"
        rationale.append(
            "Global Feishu search is visible, so text-driven UIA search is safer than generic visual clicks."
        )
        hints.append(
            'Use `agent.feishu_type(target, "搜索", overwrite=True, enter=True)` to refine or launch global search.'
        )
        hints.append(
            "After results appear, click the exact result text with `agent.feishu_click(...)` instead of a generic grounded click."
        )
        if target_chat_name:
            hints.append(f"Instruction target chat hint: {target_chat_name}.")

    elif page_type == "chat_search_panel":
        preferred_tools.extend(["feishu_type", "feishu_click", "hotkey"])
        discouraged_tools.extend(["type"])
        if "emoji" in intents:
            enabled_tools.append("click")
        next_step_focus = "conversation_search_entry_or_result"
        rationale.append(
            "The in-chat search panel is already open; stay inside this branch until it is closed or the required result is selected."
        )
        hints.append(
            'Use `agent.feishu_type(query, "搜索会话内容", overwrite=True, enter=False)` for the panel input.'
        )
        hints.append(
            "Use `agent.feishu_click(...)` with exact result text for visible search results."
        )
        hints.append(
            "If the search panel is blocking composer actions, close it before trying to type into the message box."
        )

    elif page_type == "chat_main":
        enabled_tools.extend(
            [
                "click",
                "feishu_click_message_input",
                "feishu_type_message",
                "feishu_click_send_button",
            ]
        )
        next_step_focus = "chat_main_primary_action"
        rationale.append(
            "The main IM chat surface is visible, so prefer Feishu desktop helpers before generic grounded actions."
        )

        if "search" in intents:
            preferred_tools.extend(["hotkey", "feishu_click", "feishu_type"])
            next_step_focus = "open_or_use_conversation_search"
            hints.append(
                "If you need in-chat search, prefer `agent.hotkey(['ctrl', 'f'])` or click the visible search control first."
            )

        if "open_chat" in intents:
            preferred_tools.extend(["feishu_click", "feishu_type"])
            hints.append(
                "When switching chats, click the exact conversation title in the left sidebar first; use search only if the target is not visible."
            )
            if target_chat_name:
                hints.append(f"Instruction target chat hint: {target_chat_name}.")

        if "compose_message" in intents or state.get("message_input_visible"):
            preferred_tools.insert(1, "feishu_type_message")
            preferred_tools.insert(2, "feishu_click_message_input")
            preferred_tools.append("hotkey")
            next_step_focus = "message_composer"
            hints.append(
                "For normal IM typing, prefer `agent.feishu_type_message(...)` instead of describing the input box in natural language."
            )

        if (
            "send_message" in intents
            and state.get("send_button_visible")
            and draft_present
        ):
            preferred_tools.append("feishu_click_send_button")
            hints.append(
                "If a draft is already present, prefer `agent.hotkey(['enter'])`; if Enter is unsuitable, use `agent.feishu_click_send_button()`."
            )

        if "emoji" in intents and draft_present:
            _remove_tool(preferred_tools, "feishu_click")
            preferred_tools.insert(1, "click")
            discouraged_tools.extend(["feishu_click", "type"])
            next_step_focus = "emoji_icon_or_picker"
            hints.append(
                "For icon-only composer controls such as emoji, prefer a grounded `agent.click(...)` because `feishu_click(...)` is text-based and may miss icon-only buttons."
            )
        elif "emoji" in intents:
            hints.append(
                "Do not go to emoji first. Finish the message draft in the composer before opening the emoji picker."
            )

    else:
        enabled_tools.extend(
            [
                "click",
                "type",
                "feishu_click_message_input",
                "feishu_type_message",
            ]
        )
        preferred_tools.extend(["feishu_click", "feishu_type"])
        rationale.append(
            "The page is not confidently classified, so start from screenshot reasoning and then prefer dedicated Feishu helpers for known IM surfaces."
        )
        hints.append(
            "Re-check whether the IM composer is already visible before re-clicking chat titles or search entry points."
        )
        if ("compose_message" in intents and not draft_present) or state.get(
            "message_input_visible"
        ):
            preferred_tools.insert(1, "feishu_type_message")
            preferred_tools.insert(2, "feishu_click_message_input")
            next_step_focus = "message_composer"
            hints.append(
                "If the chat composer is visible, prefer `agent.feishu_type_message(...)` or `agent.feishu_click_message_input()` before using later-step tools."
            )
        if "emoji" in intents and draft_present:
            _remove_tool(preferred_tools, "feishu_click")
            preferred_tools.insert(1, "click")
            discouraged_tools.append("feishu_click")
            next_step_focus = "emoji_icon_or_picker"
            hints.append(
                "For emoji or other icon-only controls, do not assume `feishu_click(...)` can find them by text; prefer a grounded `agent.click(...)`."
            )
        elif "compose_message" in intents and not draft_present:
            hints.append(
                "If the active chat is already open, go directly to the composer instead of re-clicking the chat title."
            )
        if target_chat_name:
            hints.append(f"Instruction target chat hint: {target_chat_name}.")

    preferred = _ordered_unique(preferred_tools)
    enabled = _ordered_unique(list(preferred) + enabled_tools)
    discouraged = _ordered_unique(discouraged_tools)

    return FeishuToolRecommendation(
        page_type=page_type,
        product=state.get("product", "unknown"),
        state_summary=_build_state_summary(state),
        next_step_focus=next_step_focus,
        enabled_tools=enabled,
        preferred_tools=preferred,
        discouraged_tools=discouraged,
        hints=tuple(hints),
        rationale=tuple(rationale),
        target_chat_name=target_chat_name,
        detected_chat_name=detected_chat_name,
    )


def build_feishu_tool_guidance(
    instruction: str,
    observation: dict,
    state: FeishuState | None = None,
) -> str:
    recommendation = route_feishu_tools(instruction, observation, state=state)
    lines = [
        "Use this only as recovery guidance after the previous action did not reach the expected state.",
        "Re-check the current screenshot before choosing the next tool.",
        "Prefer the listed tools when they match what you see, but do not override the screenshot.",
        f"Detected state: {recommendation.state_summary}",
        f"Next-step focus: {recommendation.next_step_focus}",
        "Preferred tools: " + ", ".join(recommendation.preferred_tools),
        "Allowed tools: " + ", ".join(recommendation.enabled_tools),
    ]
    if recommendation.discouraged_tools:
        lines.append(
            "Discouraged tools: " + ", ".join(recommendation.discouraged_tools)
        )
    if recommendation.detected_chat_name:
        lines.append(f"Detected active chat: {recommendation.detected_chat_name}")
    if recommendation.target_chat_name:
        lines.append(f"Instruction target chat: {recommendation.target_chat_name}")
    for rationale in recommendation.rationale:
        lines.append(f"Rationale: {rationale}")
    for hint in recommendation.hints:
        lines.append(f"Hint: {hint}")

    for spec in get_tool_specs(recommendation.preferred_tools[:3]):
        if spec.examples:
            lines.append(f"Example {spec.tool_name}: {spec.examples[0]}")

    return "\n".join(lines)
