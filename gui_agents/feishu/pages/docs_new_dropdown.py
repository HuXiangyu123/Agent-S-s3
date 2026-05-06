"""Feishu Docs new dropdown descriptor."""

from __future__ import annotations

from gui_agents.feishu.contracts import PageDescriptor


DOCS_NEW_DROPDOWN_DESCRIPTOR: PageDescriptor = {
    "page_id": "docs_new_dropdown",
    "page_type": "docs_new_dropdown",
    "display_name": "Feishu Docs New Dropdown",
    "layout_hints": {
        "surface": "feishu_desktop_cloud_docs",
        "menu": "new_type_dropdown",
    },
    "key_regions": {
        "new_dropdown_area": {
            "role": "new_type_dropdown",
            "semantic_position": "opened_new_menu",
        },
        "document_option_area": {
            "role": "document_type_option",
            "semantic_position": "visible_menu_option",
        },
        "folder_option_area": {
            "role": "folder_type_option",
            "semantic_position": "visible_menu_option",
        },
        "more_types_area": {
            "role": "more_types_option",
            "semantic_position": "visible_menu_option",
        },
    },
    "text_anchors": [
        "新建",
        "文档",
        "多维表格",
        "文件夹",
    ],
    "ui_version_tag": "feishu-desktop-cloud-docs",
}
