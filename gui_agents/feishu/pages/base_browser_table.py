"""Feishu Base browser table editor descriptor."""

from __future__ import annotations

from gui_agents.feishu.contracts import PageDescriptor


BASE_BROWSER_TABLE_DESCRIPTOR: PageDescriptor = {
    "page_id": "base_browser_table",
    "page_type": "base_browser_table",
    "display_name": "Feishu Base Browser Table",
    "layout_hints": {
        "surface": "browser_base_editor",
        "navigation": "left_view_sidebar",
        "grid": "main_table",
    },
    "key_regions": {
        "base_grid_area": {
            "role": "base_grid",
            "description": "main table grid area of the Base browser editor",
        },
        "base_add_record_area": {
            "role": "add_record",
            "description": "grid toolbar control for adding a record",
        },
        "base_share_button_area": {
            "role": "share_button",
            "description": "top toolbar share button in the browser editor",
        },
        "base_automation_button_area": {
            "role": "automation_button",
            "description": "top toolbar automation entry in the browser editor",
        },
        "base_sidebar_views_area": {
            "role": "base_view_sidebar",
            "description": "left-side view list for table, form, dashboard, and automation entries",
        },
    },
    "text_anchors": [
        "未命名多维表格",
        "数据表",
        "表格",
        "添加记录",
        "分享",
        "自动化",
    ],
    "ui_version_tag": "feishu-browser-base-table",
}
