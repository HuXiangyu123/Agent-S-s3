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
            "relative_bounds": [0.0, 0.0, 1.0, 1.0],
            "role": "new_type_dropdown",
        },
        "document_option_area": {
            "relative_bounds": [0.0, 0.18, 1.0, 0.29],
            "role": "document_type_option",
        },
        "folder_option_area": {
            "relative_bounds": [0.0, 0.62, 1.0, 0.72],
            "role": "folder_type_option",
        },
        "more_types_area": {
            "relative_bounds": [0.0, 0.52, 1.0, 0.62],
            "role": "more_types_option",
        },
    },
    "text_anchors": [
        "新建",
        "文档",
        "多维表格",
        "文件夹",
    ],
    "supported_workflows": ["create_doc_and_edit"],
    "ui_version_tag": "feishu-desktop-cloud-docs",
}
