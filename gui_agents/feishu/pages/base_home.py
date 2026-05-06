"""Feishu Base home page descriptor."""

from __future__ import annotations

from gui_agents.feishu.contracts import PageDescriptor


BASE_HOME_DESCRIPTOR: PageDescriptor = {
    "page_id": "base_home",
    "page_type": "base_home",
    "display_name": "Feishu Base Home",
    "layout_hints": {
        "surface": "feishu_desktop_base",
        "navigation": "left_sidebar",
        "document_list": "main_table_or_home_cards",
    },
    "key_regions": {
        "base_sidebar_search_area": {
            "role": "base_search_entry",
            "description": "left-side Base search entry near the top navigation",
        },
        "base_home_new_button_area": {
            "role": "new_base_menu_button",
            "description": "top-right New button that opens Base creation entry points",
        },
        "base_home_card_area": {
            "role": "recent_or_recommended_base_cards",
            "description": "main content cards for recent or recommended Base entries",
        },
        "base_list_area": {
            "role": "base_list",
            "description": "central list of available Base workspaces and tables",
        },
    },
    "text_anchors": [
        "飞书多维表格",
        "多维表格",
        "应用",
        "新建",
        "全部多维表格",
    ],
    "ui_version_tag": "feishu-desktop-base-home",
}
