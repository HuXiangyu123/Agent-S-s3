"""Feishu Video Conference invite states descriptor."""

from __future__ import annotations

from gui_agents.feishu.contracts import PageDescriptor


VC_INVITE_DIALOG_DESCRIPTOR: PageDescriptor = {
    "page_id": "vc_invite_dialog",
    "page_type": "vc_invite_dialog",
    "display_name": "Feishu VC Invite Dialog",
    "layout_hints": {
        "surface": "meeting_invite_overlay",
        "tabs": "top",
        "search": "left_panel",
    },
    "key_regions": {
        "vc_invite_dialog_area": {
            "role": "invite_dialog",
        },
        "vc_invite_search_area": {
            "role": "invite_search_input",
        },
        "vc_invite_contact_result_area": {
            "role": "invite_contact_result",
        },
        "vc_share_button_area": {
            "role": "share_invite_button",
        },
        "vc_copy_invite_info_button_area": {
            "role": "copy_invite_info_button",
        },
    },
    "text_anchors": [
        "分享邀请",
        "电话邀请",
        "搜索",
        "复制入会信息",
        "分享",
    ],
    "supported_workflows": [],
    "ui_version_tag": "feishu-desktop-vc-invite-dialog",
}
