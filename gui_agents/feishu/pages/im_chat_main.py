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
            "relative_bounds": [0.03, 0.06, 0.21, 0.98],
            "role": "conversation_list",
        },
        "active_chat_list_item_area": {
            "relative_bounds": [0.034, 0.112, 0.205, 0.175],
            "role": "conversation_list_item",
        },
        "header": {
            "relative_bounds": [0.15, 0.0, 1.0, 0.14],
            "role": "chat_header",
        },
        "chat_body": {
            "relative_bounds": [0.15, 0.14, 1.0, 0.9],
            "role": "message_history",
        },
        "message_input_area": {
            "relative_bounds": [0.16, 0.9, 0.995, 0.985],
            "role": "composer_input",
        },
        "send_button_area": {
            "relative_bounds": [0.95, 0.9, 0.995, 0.985],
            "role": "composer_send",
        },
    },
    "text_anchors": [
        "消息",
        "文件",
        "发送给",
    ],
    "supported_workflows": ["open_chat", "send_message"],
    "ui_version_tag": "feishu-desktop-dark",
}
