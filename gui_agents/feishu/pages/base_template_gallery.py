"""Feishu Base template gallery descriptor."""

from __future__ import annotations

from gui_agents.feishu.contracts import PageDescriptor


BASE_TEMPLATE_GALLERY_DESCRIPTOR: PageDescriptor = {
    "page_id": "base_template_gallery",
    "page_type": "base_template_gallery",
    "display_name": "Feishu Base Template Gallery",
    "layout_hints": {
        "surface": "feishu_desktop_base",
        "overlay": "template_center_modal",
        "category_nav": "left_column",
    },
    "key_regions": {
        "base_template_search_area": {
            "role": "template_search",
            "description": "template search box inside the template center modal",
        },
        "base_blank_table_card_area": {
            "role": "blank_base_table_card",
            "description": "blank Base table template card in the recommendation grid",
        },
        "base_template_category_area": {
            "role": "template_category_list",
            "description": "left-side category navigation for Base templates",
        },
        "base_template_grid_area": {
            "role": "template_grid",
            "description": "main grid of Base template cards",
        },
    },
    "text_anchors": [
        "模板中心",
        "推荐",
        "热门应用",
        "今天你想搭建什么呢",
        "新建多维表格",
    ],
    "ui_version_tag": "feishu-desktop-base-template-gallery",
}
