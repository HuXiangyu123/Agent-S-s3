"""Feishu Video Conference start preview descriptor."""

from __future__ import annotations

from gui_agents.feishu.contracts import PageDescriptor


VC_START_PREVIEW_DESCRIPTOR: PageDescriptor = {
    "page_id": "vc_start_preview",
    "page_type": "vc_start_preview",
    "display_name": "Feishu VC Start Preview",
    "layout_hints": {
        "surface": "floating_meeting_preview",
        "controls": "bottom_bar",
    },
    "key_regions": {
        "vc_preview_window_area": {
            "role": "preview_window",
        },
        "vc_start_button_area": {
            "role": "start_meeting_button",
        },
        "vc_microphone_toggle_area": {
            "role": "microphone_toggle",
        },
        "vc_camera_toggle_area": {
            "role": "camera_toggle",
        },
    },
    "text_anchors": [
        "视频会议",
        "麦克风",
        "摄像头",
        "开始会议",
    ],
    "supported_workflows": [],
    "ui_version_tag": "feishu-desktop-vc-preview",
}
