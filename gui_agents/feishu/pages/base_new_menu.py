"""Feishu Base new menu descriptor."""

from __future__ import annotations

from gui_agents.feishu.contracts import PageDescriptor


BASE_NEW_MENU_DESCRIPTOR: PageDescriptor = {
    "page_id": "base_new_menu",
    "page_type": "base_new_menu",
    "display_name": "Feishu Base New Menu",
    "layout_hints": {
        "surface": "feishu_desktop_base",
        "overlay": "top_right_new_menu",
    },
    "key_regions": {
        "base_new_menu_area": {
            "role": "new_menu_overlay",
            "description": "floating new-menu overlay opened from the Base home New button",
        },
        "base_new_table_option_area": {
            "role": "new_base_table_option",
            "description": "menu item for creating a new Base table",
        },
        "base_new_app_option_area": {
            "role": "new_base_app_option",
            "description": "menu item for creating a new Base app",
        },
        "base_template_center_entry_area": {
            "role": "template_center_entry",
            "description": "lower menu entry that opens template center content",
        },
    },
    "text_anchors": [
        "新建多维表格",
        "新建应用",
        "新建收集表",
        "新建仪表盘",
        "导入 Excel/在线表格",
    ],
    "ui_version_tag": "feishu-desktop-base-new-menu",
}
