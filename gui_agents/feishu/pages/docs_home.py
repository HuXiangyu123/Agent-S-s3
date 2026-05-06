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
            "relative_bounds": [0.035, 0.08, 0.19, 0.14],
            "role": "search_entry",
        },
        "new_card_area": {
            "relative_bounds": [0.215, 0.145, 0.36, 0.245],
            "role": "new_document_entry",
        },
        "upload_card_area": {
            "relative_bounds": [0.375, 0.145, 0.515, 0.245],
            "role": "upload_entry",
        },
        "template_card_area": {
            "relative_bounds": [0.535, 0.145, 0.67, 0.245],
            "role": "template_entry",
        },
        "document_list_area": {
            "relative_bounds": [0.205, 0.32, 0.96, 0.98],
            "role": "document_list",
        },
    },
    "text_anchors": [
        "云文档",
        "主页",
        "新建",
        "上传",
        "模板库",
    ],
    "supported_workflows": ["create_doc_and_edit"],
    "ui_version_tag": "feishu-desktop-cloud-docs",
}
