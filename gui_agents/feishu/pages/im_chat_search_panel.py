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
            "role": "conversation_search_panel",
            "semantic_position": "right_overlay",
        },
        "conversation_search_close_button_area": {
            "role": "conversation_search_close_button",
            "semantic_position": "top_right_of_search_panel",
        },
        "conversation_search_entry_area": {
            "role": "conversation_search_entry",
            "semantic_position": "top_of_search_panel",
        },
        "search_filters_row_area": {
            "role": "search_filters_row",
            "semantic_position": "below_search_entry",
        },
        "search_empty_hint_area": {
            "role": "search_empty_hint",
            "semantic_position": "center_of_search_panel",
        },
        "conversation_search_result_list_area": {
            "role": "conversation_search_result_list",
            "semantic_position": "search_panel_results",
        },
        "conversation_search_result_item_area": {
            "role": "conversation_search_result_item",
            "semantic_position": "first_visible_search_result",
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
    "ui_version_tag": "feishu-desktop-dark",
}
