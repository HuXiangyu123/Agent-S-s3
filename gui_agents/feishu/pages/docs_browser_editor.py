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
            "relative_bounds": [0.38, 0.18, 0.62, 0.32],
            "role": "document_title_input",
        },
        "body_editor_area": {
            "relative_bounds": [0.36, 0.38, 0.66, 0.54],
            "role": "document_body_editor",
        },
        "share_button_area": {
            "relative_bounds": [0.835, 0.02, 0.895, 0.085],
            "role": "share_button",
        },
        "toolbar_area": {
            "relative_bounds": [0.72, 0.0, 1.0, 0.10],
            "role": "top_toolbar",
        },
    },
    "text_anchors": [
        "飞书云文档",
        "请输入标题",
        "输入 / 快速插入内容",
        "分享",
    ],
    "supported_workflows": ["create_doc_and_edit"],
    "ui_version_tag": "feishu-browser-cloud-docs",
}
