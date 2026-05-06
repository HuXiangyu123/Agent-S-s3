"""Feishu Docs browser editor descriptor."""

from __future__ import annotations

from gui_agents.feishu.contracts import PageDescriptor


DOCS_BROWSER_EDITOR_DESCRIPTOR: PageDescriptor = {
    "page_id": "docs_browser_editor",
    "page_type": "docs_browser_editor",
    "display_name": "Feishu Docs Browser Editor",
    "layout_hints": {
        "surface": "browser_cloud_doc",
        "editor": "document_editor",
    },
    "key_regions": {
        "title_input_area": {
            "role": "document_title_input",
            "semantic_position": "document_title",
        },
        "body_editor_area": {
            "role": "document_body_editor",
            "semantic_position": "document_body",
        },
        "share_button_area": {
            "role": "share_button",
            "semantic_position": "top_toolbar",
        },
        "toolbar_area": {
            "role": "top_toolbar",
            "semantic_position": "top_toolbar",
        },
    },
    "text_anchors": [
        "飞书云文档",
        "请输入标题",
        "输入 / 快速插入内容",
        "分享",
    ],
    "ui_version_tag": "feishu-browser-cloud-docs",
}
