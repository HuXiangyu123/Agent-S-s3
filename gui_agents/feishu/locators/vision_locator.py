"""Minimal vision locator for Track B MVP."""

from __future__ import annotations

from typing import Any

from gui_agents.feishu.contracts import FailureType, FeishuState, LocatorResult
from gui_agents.feishu.observation import (
    get_named_runtime_region_bounds,
    get_runtime_region_bounds,
    normalize_observation,
)
from gui_agents.feishu.pages.registry import get_page_descriptor


def _success_result(
    target: str,
    page_id: str | None,
    bounds: list[int],
) -> LocatorResult:
    x1, y1, x2, y2 = bounds
    return LocatorResult(
        matched=True,
        strategy="runtime_region",
        page_id=page_id,
        target=target,
        action_target={
            "kind": "point",
            "point": [round((x1 + x2) / 2), round((y1 + y2) / 2)],
            "source": "runtime_observation",
        },
    )


def _failure_result(
    failure_type: FailureType,
    reason: str,
    page_id: str | None = None,
) -> LocatorResult:
    return LocatorResult(
        matched=False,
        strategy="runtime_region",
        page_id=page_id,
        target=None,
        action_target=None,
        failure_type=failure_type,
        failure_reason=reason,
    )


def _canonical_target(target: str, state: FeishuState) -> str:
    if target == "chat_search_box":
        return "global_search_entry"
    if target == "chat_result_item":
        if state.get("product_state", {}).get("search_result_list_visible", False):
            return "search_result_item"
        return "conversation_list_item"
    return target


def _descriptor_from_state(state: FeishuState) -> str | None:
    base_page_types = {
        "base_home": "base_home",
        "base_new_menu": "base_new_menu",
        "base_template_gallery": "base_template_gallery",
        "base_browser_table": "base_browser_table",
        "base_share_panel": "base_share_panel",
        "base_dashboard": "base_dashboard",
        "base_automation": "base_automation",
        "base_app_market": "base_app_market",
    }
    if state.get("page_type") in base_page_types:
        return base_page_types[state["page_type"]]
    if state.get("page_type") == "chat_main":
        return "im_chat_main"
    if state.get("page_type") == "chat_search_panel":
        return "im_chat_search_panel"
    if state.get("page_type") == "shell_search":
        return "feishu_shell_search"
    vc_page_types = {
        "vc_home": "vc_home",
        "vc_start_preview": "vc_start_preview",
        "vc_meeting_active": "vc_meeting_active",
        "vc_join_preview": "vc_join_preview",
        "vc_invite_dialog": "vc_invite_dialog",
    }
    if state.get("page_type") in vc_page_types:
        return vc_page_types[state["page_type"]]
    return None


def locate_target(
    target: str,
    state: FeishuState,
    observation: dict[str, Any],
    page_context: dict[str, Any] | None = None,
) -> LocatorResult:
    target = _canonical_target(target, state)
    metadata = normalize_observation(observation)

    page_descriptor = None
    if page_context and isinstance(page_context.get("page_descriptor"), dict):
        page_descriptor = page_context["page_descriptor"]
    elif metadata.get("page_id"):
        page_descriptor = get_page_descriptor(metadata["page_id"])
    else:
        descriptor_id = _descriptor_from_state(state)
        if descriptor_id:
            page_descriptor = get_page_descriptor(descriptor_id)

    if not page_descriptor:
        return _failure_result("recognition", "page descriptor unavailable")

    def region_bounds(name: str) -> list[int]:
        runtime_bounds = get_runtime_region_bounds(observation, name)
        if runtime_bounds:
            return runtime_bounds
        region = page_descriptor["key_regions"].get(name)
        if not isinstance(region, dict):
            raise KeyError(name)
        raise KeyError(name)

    if state.get("product") == "base" or target.startswith("base_"):
        return _failure_result(
            "location",
            "Base semantic priors do not expose fixed coordinates; use grounded browser actions instead",
            page_descriptor["page_id"],
        )

    if target == "message_input":
        if page_descriptor["page_id"] != "im_chat_main":
            return _failure_result(
                "location",
                "message input unsupported on current page",
                page_descriptor["page_id"],
            )
        try:
            bounds = region_bounds("message_input_area")
            return _success_result(
                target=target,
                page_id=page_descriptor["page_id"],
                bounds=bounds,
            )
        except KeyError:
            return _failure_result(
                "location",
                "runtime region unavailable for message_input_area",
                page_descriptor["page_id"],
            )

    if target == "send_button":
        if page_descriptor["page_id"] != "im_chat_main":
            return _failure_result(
                "location",
                "send button unsupported on current page",
                page_descriptor["page_id"],
            )
        if not state.get("send_button_visible", False):
            return _failure_result(
                "location", "send button not visible", page_descriptor["page_id"]
            )
        try:
            bounds = region_bounds("send_button_area")
            return _success_result(
                target=target,
                page_id=page_descriptor["page_id"],
                bounds=bounds,
            )
        except KeyError:
            return _failure_result(
                "location",
                "runtime region unavailable for send_button_area",
                page_descriptor["page_id"],
            )

    if target == "conversation_list_item":
        if page_descriptor["page_id"] != "im_chat_main":
            return _failure_result(
                "location",
                "conversation list item unsupported on current page",
                page_descriptor["page_id"],
            )
        target_text = page_context.get("target_text") if page_context else None
        if not target_text:
            target_text = state.get("chat_name")

        visible_items = state.get("product_state", {}).get(
            "visible_conversation_items", []
        )
        active_item = state.get("product_state", {}).get(
            "active_conversation_item_text"
        )
        if target_text and visible_items and target_text not in visible_items:
            return _failure_result(
                "location",
                f"conversation item not visible: {target_text}",
                page_descriptor["page_id"],
            )
        if target_text and active_item and target_text != active_item:
            return _failure_result(
                "location",
                f"active visible conversation does not match target: {target_text}",
                page_descriptor["page_id"],
            )

        named_region = None
        if target_text:
            named_region = get_named_runtime_region_bounds(
                observation,
                "conversation_list_items",
                target_text,
            )
        try:
            if named_region:
                bounds = named_region
            else:
                bounds = region_bounds("active_chat_list_item_area")
            return _success_result(
                target=target,
                page_id=page_descriptor["page_id"],
                bounds=bounds,
            )
        except KeyError:
            return _failure_result(
                "location",
                "runtime region unavailable for conversation_list_item",
                page_descriptor["page_id"],
            )

    if target == "conversation_search_close_button":
        if page_descriptor["page_id"] != "im_chat_search_panel":
            return _failure_result(
                "location",
                "conversation search close button unsupported on current page",
                page_descriptor["page_id"],
            )
        try:
            bounds = region_bounds("conversation_search_close_button_area")
            return _success_result(
                target=target,
                page_id=page_descriptor["page_id"],
                bounds=bounds,
            )
        except KeyError:
            return _failure_result(
                "location",
                "runtime region unavailable for conversation_search_close_button_area",
                page_descriptor["page_id"],
            )

    if target == "conversation_search_entry":
        if page_descriptor["page_id"] != "im_chat_search_panel":
            return _failure_result(
                "location",
                "conversation search entry unsupported on current page",
                page_descriptor["page_id"],
            )
        if not state.get("search_box_visible", False):
            return _failure_result(
                "location",
                "conversation search entry not visible in current state",
                page_descriptor["page_id"],
            )
        try:
            bounds = region_bounds("conversation_search_entry_area")
            return _success_result(
                target=target,
                page_id=page_descriptor["page_id"],
                bounds=bounds,
            )
        except KeyError:
            return _failure_result(
                "location",
                "runtime region unavailable for conversation_search_entry_area",
                page_descriptor["page_id"],
            )

    if target == "conversation_search_result_item":
        if page_descriptor["page_id"] != "im_chat_search_panel":
            return _failure_result(
                "location",
                "conversation search result item unsupported on current page",
                page_descriptor["page_id"],
            )
        if not state.get("product_state", {}).get(
            "local_search_result_list_visible", False
        ):
            return _failure_result(
                "location",
                "conversation search result list not visible in current state",
                page_descriptor["page_id"],
            )
        target_text = page_context.get("target_text") if page_context else None
        visible_results = state.get("product_state", {}).get(
            "visible_conversation_search_results", []
        )
        if target_text and visible_results and target_text not in visible_results:
            return _failure_result(
                "location",
                f"conversation search result not visible: {target_text}",
                page_descriptor["page_id"],
            )
        named_region = None
        if target_text:
            named_region = get_named_runtime_region_bounds(
                observation,
                "conversation_search_result_items",
                target_text,
            )
        try:
            if named_region:
                bounds = named_region
            else:
                bounds = region_bounds("conversation_search_result_item_area")
            return _success_result(
                target=target,
                page_id=page_descriptor["page_id"],
                bounds=bounds,
            )
        except KeyError:
            return _failure_result(
                "location",
                "runtime region unavailable for conversation_search_result_item",
                page_descriptor["page_id"],
            )

    if target == "global_search_entry":
        if page_descriptor["page_id"] != "feishu_shell_search":
            return _failure_result(
                "location",
                "global search entry unsupported on current page",
                page_descriptor["page_id"],
            )
        if not state.get("search_box_visible", False):
            return _failure_result(
                "location",
                "global search entry not visible in current state",
                page_descriptor["page_id"],
            )
        try:
            bounds = region_bounds("global_search_entry_area")
            return _success_result(
                target=target,
                page_id=page_descriptor["page_id"],
                bounds=bounds,
            )
        except KeyError:
            return _failure_result(
                "location",
                "runtime region unavailable for global_search_entry_area",
                page_descriptor["page_id"],
            )

    if target == "search_result_item":
        if page_descriptor["page_id"] != "feishu_shell_search":
            return _failure_result(
                "location",
                "search result item unsupported on current page",
                page_descriptor["page_id"],
            )
        if not state.get("product_state", {}).get("search_result_list_visible", False):
            return _failure_result(
                "location",
                "search result list not visible in current state",
                page_descriptor["page_id"],
            )

        target_text = page_context.get("target_text") if page_context else None
        if not target_text:
            target_text = state.get("chat_name")

        visible_results = state.get("product_state", {}).get(
            "visible_search_results", []
        )
        if target_text and visible_results and target_text not in visible_results:
            return _failure_result(
                "location",
                f"search result not visible: {target_text}",
                page_descriptor["page_id"],
            )

        named_region = None
        if target_text:
            named_region = get_named_runtime_region_bounds(
                observation,
                "search_result_items",
                target_text,
            )
        try:
            if named_region:
                bounds = named_region
            else:
                bounds = region_bounds("search_result_item_area")
            return _success_result(
                target=target,
                page_id=page_descriptor["page_id"],
                bounds=bounds,
            )
        except KeyError:
            return _failure_result(
                "location",
                "runtime region unavailable for search_result_item",
                page_descriptor["page_id"],
            )

    return _failure_result(
        "location",
        f"unsupported target: {target}",
        page_descriptor["page_id"],
    )
