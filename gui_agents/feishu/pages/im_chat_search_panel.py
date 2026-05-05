"""IM in-chat search panel page descriptor."""

from __future__ import annotations

from gui_agents.feishu.contracts import PageDescriptor


IM_CHAT_SEARCH_PANEL_DESCRIPTOR: PageDescriptor = {
    "page_id": "im_chat_search_panel",
    "page_type": "chat_search_panel",
    "display_name": "Feishu IM Chat Search Panel",
    "layout_hints": {
        "search_scope": "current_conversation",
        "panel_position": "right_overlay",
        "search_entry": "panel_top",
    },
    "key_regions": {
        "search_panel_area": {
            "relative_bounds": [0.05, 0.08, 0.95, 0.98],
            "role": "conversation_search_panel",
        },
        "conversation_search_close_button_area": {
            "relative_bounds": [0.86, 0.12, 0.94, 0.20],
            "role": "conversation_search_close_button",
        },
        "conversation_search_entry_area": {
            "relative_bounds": [0.10, 0.23, 0.90, 0.28],
            "role": "conversation_search_entry",
        },
        "search_filters_row_area": {
            "relative_bounds": [0.10, 0.29, 0.70, 0.35],
            "role": "search_filters_row",
        },
        "search_empty_hint_area": {
            "relative_bounds": [0.26, 0.62, 0.82, 0.78],
            "role": "search_empty_hint",
        },
        "conversation_search_result_list_area": {
            "relative_bounds": [0.09, 0.36, 0.92, 0.82],
            "role": "conversation_search_result_list",
        },
        "conversation_search_result_item_area": {
            "relative_bounds": [0.10, 0.37, 0.90, 0.45],
            "role": "conversation_search_result_item",
        },
    },
    "text_anchors": [
        "搜索会话内容",
        "搜索",
        "来自用户",
        "时间",
        "高级搜索",
        "输入关键词或使用过滤器查找消息记录",
    ],
    "supported_workflows": [],
    "ui_version_tag": "feishu-desktop-dark",
}
