"""Feishu active Video Conference meeting descriptor."""

from __future__ import annotations

from gui_agents.feishu.contracts import PageDescriptor


VC_MEETING_ACTIVE_DESCRIPTOR: PageDescriptor = {
    "page_id": "vc_meeting_active",
    "page_type": "vc_meeting_active",
    "display_name": "Feishu VC Active Meeting",
    "layout_hints": {
        "surface": "floating_active_meeting",
        "controls": "bottom_toolbar",
        "content": "meeting_stage",
    },
    "key_regions": {
        "vc_meeting_window_area": {
            "role": "active_meeting_window",
        },
        "vc_invite_button_area": {
            "role": "invite_participant_button",
        },
        "vc_leave_button_area": {
            "role": "leave_meeting_button",
        },
        "vc_microphone_toggle_area": {
            "role": "microphone_toggle",
        },
        "vc_camera_toggle_area": {
            "role": "camera_toggle",
        },
    },
    "text_anchors": [
        "会议信息",
        "布局",
        "AI 总结",
        "孙思超",
    ],
    "supported_workflows": [],
    "ui_version_tag": "feishu-desktop-vc-active",
}
