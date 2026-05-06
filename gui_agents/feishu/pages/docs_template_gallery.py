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
            "role": "template_search_entry",
            "semantic_position": "top_gallery_search",
        },
        "blank_doc_card_area": {
            "role": "blank_document_card",
            "semantic_position": "visible_template_card",
        },
        "template_grid_area": {
            "role": "template_grid",
            "semantic_position": "gallery_grid",
        },
        "close_button_area": {
            "role": "close_button",
            "semantic_position": "top_right_close",
        },
    },
    "text_anchors": [
        "新建到",
        "搜索模板",
        "新建空白文档",
        "为你推荐",
    ],
    "ui_version_tag": "feishu-desktop-cloud-docs",
}
