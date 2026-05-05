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
            "relative_bounds": [0.02, 0.02, 0.96, 0.08],
            "role": "global_search_entry",
        },
        "search_scope_tab_row": {
            "relative_bounds": [0.01, 0.08, 0.82, 0.15],
            "role": "search_scope_tabs",
        },
        "search_result_list_area": {
            "relative_bounds": [0.0, 0.15, 0.34, 0.62],
            "role": "search_result_list",
        },
        "search_result_item_area": {
            "relative_bounds": [0.01, 0.19, 0.28, 0.34],
            "role": "search_result_item",
        },
    },
    "text_anchors": [
        "问你想问的问题",
        "搜索关键词",
        "消息",
        "联系人",
        "群组",
    ],
    "supported_workflows": ["open_chat"],
    "ui_version_tag": "feishu-desktop-dark",
}
