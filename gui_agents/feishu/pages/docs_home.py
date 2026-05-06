"""Feishu Docs home page descriptor."""

from __future__ import annotations

from gui_agents.feishu.contracts import PageDescriptor


DOCS_HOME_DESCRIPTOR: PageDescriptor = {
    "page_id": "docs_home",
    "page_type": "docs_home",
    "display_name": "Feishu Docs Home",
    "layout_hints": {
        "surface": "feishu_desktop_cloud_docs",
        "navigation": "left_sidebar",
        "document_list": "main_table",
    },
    "key_regions": {
        "search_entry_area": {
            "role": "search_entry",
            "semantic_position": "left_sidebar_top",
        },
        "new_card_area": {
            "role": "new_document_entry",
            "semantic_position": "top_action_card",
        },
        "upload_card_area": {
            "role": "upload_entry",
            "semantic_position": "top_action_card",
        },
        "template_card_area": {
            "role": "template_entry",
            "semantic_position": "top_action_card",
        },
        "document_list_area": {
            "role": "document_list",
            "semantic_position": "main_document_table",
        },
    },
    "text_anchors": [
        "云文档",
        "主页",
        "新建",
        "上传",
        "模板库",
    ],
    "ui_version_tag": "feishu-desktop-cloud-docs",
}
