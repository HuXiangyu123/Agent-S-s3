"""Feishu Docs template gallery descriptor."""

from __future__ import annotations

from gui_agents.feishu.contracts import PageDescriptor


DOCS_TEMPLATE_GALLERY_DESCRIPTOR: PageDescriptor = {
    "page_id": "docs_template_gallery",
    "page_type": "docs_template_gallery",
    "display_name": "Feishu Docs Template Gallery",
    "layout_hints": {
        "surface": "feishu_desktop_cloud_docs",
        "gallery": "template_gallery",
    },
    "key_regions": {
        "template_search_area": {
            "relative_bounds": [0.36, 0.015, 0.642, 0.05],
            "role": "template_search_entry",
        },
        "blank_doc_card_area": {
            "relative_bounds": [0.18, 0.13, 0.365, 0.39],
            "role": "blank_document_card",
        },
        "template_grid_area": {
            "relative_bounds": [0.18, 0.13, 0.98, 0.98],
            "role": "template_grid",
        },
        "close_button_area": {
            "relative_bounds": [0.965, 0.015, 0.99, 0.045],
            "role": "close_button",
        },
    },
    "text_anchors": [
        "新建到",
        "搜索模板",
        "新建空白文档",
        "为你推荐",
    ],
    "supported_workflows": ["create_doc_and_edit"],
    "ui_version_tag": "feishu-desktop-cloud-docs",
}
