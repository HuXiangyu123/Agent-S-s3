"""Feishu Video Conference home page descriptor."""

from __future__ import annotations

from gui_agents.feishu.contracts import PageDescriptor


VC_HOME_DESCRIPTOR: PageDescriptor = {
    "page_id": "vc_home",
    "page_type": "vc_home",
    "display_name": "Feishu VC Home",
    "layout_hints": {
        "surface": "feishu_desktop_video_meeting",
        "entry_grid": "left_content_area",
        "history": "right_content_area",
    },
    "key_regions": {
        "vc_home_area": {
            "role": "vc_home_surface",
        },
        "vc_start_card_area": {
            "role": "start_meeting_entry",
        },
        "vc_join_card_area": {
            "role": "join_meeting_entry",
        },
        "vc_history_area": {
            "role": "meeting_history",
        },
    },
    "text_anchors": [
        "视频会议",
        "发起会议",
        "加入会议",
        "历史记录",
    ],
    "ui_version_tag": "feishu-desktop-vc",
}
