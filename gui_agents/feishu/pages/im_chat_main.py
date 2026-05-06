"""IM chat main page descriptor."""

from __future__ import annotations

from gui_agents.feishu.contracts import PageDescriptor


IM_CHAT_MAIN_DESCRIPTOR: PageDescriptor = {
    "page_id": "im_chat_main",
    "page_type": "chat_main",
    "display_name": "Feishu IM Chat Main",
    "layout_hints": {
        "composer": "bottom_bar",
        "message_input_placeholder_prefix": "发送给",
        "conversation_list": "left_sidebar",
    },
    "key_regions": {
        "conversation_list_area": {
            "role": "conversation_list",
            "semantic_position": "left_sidebar",
        },
        "active_chat_list_item_area": {
            "role": "conversation_list_item",
            "semantic_position": "left_sidebar_selected_item",
        },
        "header": {
            "role": "chat_header",
            "semantic_position": "top_of_chat_pane",
        },
        "chat_body": {
            "role": "message_history",
            "semantic_position": "main_chat_pane",
        },
        "message_input_area": {
            "role": "composer_input",
            "semantic_position": "bottom_composer",
        },
        "send_button_area": {
            "role": "composer_send",
            "semantic_position": "right_side_of_composer",
        },
    },
    "text_anchors": [
        "消息",
        "文件",
        "发送给",
    ],
    "ui_version_tag": "feishu-desktop-dark",
}
