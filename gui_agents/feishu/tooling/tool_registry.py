"""Static Feishu tool knowledge built on top of existing S3 agent actions."""

from __future__ import annotations

from gui_agents.feishu.tooling.tool_contracts import FeishuToolSpec


TOOL_REGISTRY: dict[str, FeishuToolSpec] = {
    "feishu_focus": FeishuToolSpec(
        tool_name="feishu_focus",
        agent_action="feishu_focus",
        summary="Bring the Feishu desktop window to the foreground before UIA actions.",
        supported_page_types=(
            "unknown",
            "chat_main",
            "chat_search_panel",
            "shell_search",
        ),
        examples=("agent.feishu_focus()",),
    ),
    "feishu_click": FeishuToolSpec(
        tool_name="feishu_click",
        agent_action="feishu_click",
        summary="Click a Feishu desktop control by exact visible text via UIA, with grounded fallback reserved for icon-like relational descriptions.",
        supported_page_types=(
            "unknown",
            "chat_main",
            "chat_search_panel",
            "shell_search",
        ),
        examples=(
            'agent.feishu_click("bot功能测试")',
            'agent.feishu_click("搜索")',
        ),
    ),
    "feishu_type": FeishuToolSpec(
        tool_name="feishu_type",
        agent_action="feishu_type",
        summary="Paste text into a Feishu desktop input, optionally targeting a visible placeholder first.",
        supported_page_types=(
            "unknown",
            "chat_main",
            "chat_search_panel",
            "shell_search",
        ),
        examples=(
            'agent.feishu_type("hello", "发送给 bot功能测试", overwrite=True, enter=False)',
            'agent.feishu_type("bot功能测试", "搜索", overwrite=True, enter=True)',
        ),
    ),
    "feishu_click_message_input": FeishuToolSpec(
        tool_name="feishu_click_message_input",
        agent_action="feishu_click_message_input",
        summary="Focus the IM composer using the known chat_main message-input region.",
        supported_page_types=("chat_main",),
        examples=("agent.feishu_click_message_input()",),
    ),
    "feishu_type_message": FeishuToolSpec(
        tool_name="feishu_type_message",
        agent_action="feishu_type_message",
        summary="Type into the IM composer using the known chat_main message-input region.",
        supported_page_types=("chat_main",),
        examples=(
            'agent.feishu_type_message("hello", overwrite=False, enter=False)',
            'agent.feishu_type_message("hello", focus_first=False)  # input already focused',
        ),
        notes=(
            "Set focus_first=False when the composer is already focused from a prior "
            "feishu_click_message_input() call, to avoid re-clicking and potentially "
            "unfocusing it.",
        ),
    ),
    "feishu_click_send_button": FeishuToolSpec(
        tool_name="feishu_click_send_button",
        agent_action="feishu_click_send_button",
        summary="Click the IM send button using the known chat_main send-button region.",
        supported_page_types=("chat_main",),
        examples=("agent.feishu_click_send_button()",),
    ),
    "hotkey": FeishuToolSpec(
        tool_name="hotkey",
        agent_action="hotkey",
        summary="Use reliable keyboard shortcuts for search, send, confirm, or escape flows.",
        supported_page_types=(
            "unknown",
            "chat_main",
            "chat_search_panel",
            "shell_search",
        ),
        examples=(
            "agent.hotkey(['ctrl', 'f'])",
            "agent.hotkey(['enter'])",
        ),
    ),
    "click": FeishuToolSpec(
        tool_name="click",
        agent_action="click",
        summary="Fallback visual-grounding click for browser content or popup content not exposed by UIA text.",
        supported_page_types=(
            "unknown",
            "chat_main",
            "chat_search_panel",
            "shell_search",
        ),
        examples=('agent.click("the emoji option inside the popup panel", 1, "left")',),
        notes=(
            "Prefer this for icon-only controls, popup content, or browser content not exposed by UIA text.",
        ),
    ),
    "type": FeishuToolSpec(
        tool_name="type",
        agent_action="type",
        summary="Fallback visual-grounding typing for browser content or non-Feishu-hosted inputs.",
        supported_page_types=(
            "unknown",
            "chat_main",
            "chat_search_panel",
            "shell_search",
        ),
        examples=('agent.type(text="hello", overwrite=False, enter=False)',),
        notes=("Prefer feishu_type when the target is a Feishu desktop input.",),
    ),
    "wait": FeishuToolSpec(
        tool_name="wait",
        agent_action="wait",
        summary="Allow the UI to settle after search, popup, or navigation actions.",
        supported_page_types=(
            "unknown",
            "chat_main",
            "chat_search_panel",
            "shell_search",
        ),
        examples=("agent.wait(1.5)",),
    ),
}


def get_tool_spec(tool_name: str) -> FeishuToolSpec | None:
    return TOOL_REGISTRY.get(tool_name)


def get_tool_specs(tool_names: tuple[str, ...]) -> list[FeishuToolSpec]:
    specs: list[FeishuToolSpec] = []
    for tool_name in tool_names:
        spec = get_tool_spec(tool_name)
        if spec is not None:
            specs.append(spec)
    return specs
