"""Feishu shell global search page descriptor."""

from __future__ import annotations

from gui_agents.feishu.contracts import PageDescriptor


FEISHU_SHELL_SEARCH_DESCRIPTOR: PageDescriptor = {
    "page_id": "feishu_shell_search",
    "page_type": "shell_search",
    "display_name": "Feishu Shell Global Search",
    "layout_hints": {
        "search_entry": "top_overlay",
        "search_results": "left_panel",
        "search_scope_tabs": "top_tab_row",
    },
    "key_regions": {
        "global_search_entry_area": {
            "role": "global_search_entry",
            "semantic_position": "top_search_overlay",
        },
        "search_scope_tab_row": {
            "role": "search_scope_tabs",
            "semantic_position": "below_global_search_entry",
        },
        "search_result_list_area": {
            "role": "search_result_list",
            "semantic_position": "left_results_panel",
        },
        "search_result_item_area": {
            "role": "search_result_item",
            "semantic_position": "first_visible_result",
        },
    },
    "text_anchors": [
        "问你想问的问题",
        "搜索关键词",
        "消息",
        "联系人",
        "群组",
    ],
    "ui_version_tag": "feishu-desktop-dark",
}
