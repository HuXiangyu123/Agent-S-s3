"""Feishu Video Conference join preview descriptor."""

from __future__ import annotations

from gui_agents.feishu.contracts import PageDescriptor


VC_JOIN_PREVIEW_DESCRIPTOR: PageDescriptor = {
    "page_id": "vc_join_preview",
    "page_type": "vc_join_preview",
    "display_name": "Feishu VC Join Preview",
    "layout_hints": {
        "surface": "floating_join_preview",
        "meeting_id_input": "top_center",
        "controls": "bottom_bar",
    },
    "key_regions": {
        "vc_join_window_area": {
            "role": "join_preview_window",
        },
        "vc_meeting_id_input_area": {
            "role": "meeting_id_input",
        },
        "vc_join_button_area": {
            "role": "join_meeting_button",
        },
        "vc_microphone_toggle_area": {
            "role": "microphone_toggle",
        },
        "vc_camera_toggle_area": {
            "role": "camera_toggle",
        },
    },
    "text_anchors": [
        "会议 ID",
        "麦克风",
        "摄像头",
        "加入会议",
    ],
    "supported_workflows": [],
    "ui_version_tag": "feishu-desktop-vc-join-preview",
}
