"""Feishu Calendar create-event modal descriptor."""

from __future__ import annotations

from gui_agents.feishu.contracts import PageDescriptor


CALENDAR_EVENT_MODAL_DESCRIPTOR: PageDescriptor = {
    "page_id": "calendar_event_modal",
    "page_type": "calendar_event_modal",
    "display_name": "Feishu Calendar Event Modal",
    "layout_hints": {
        "surface": "feishu_desktop_calendar",
        "container": "create_event_modal",
        "preview": "right_side_calendar_preview",
    },
    "key_regions": {
        "title_input": {
            "role": "event_title_input",
            "visible_placeholder": "添加主题",
        },
        "attendee_input": {
            "role": "attendee_input",
            "visible_placeholder": "添加联系人、群或邮箱",
        },
        "time_range": {
            "role": "event_time_range",
            "description": "event start and end time controls",
        },
        "save_button": {
            "role": "save_event_button",
            "visible_text": "保存",
        },
    },
    "text_anchors": [
        "创建日程",
        "添加主题",
        "添加联系人、群或邮箱",
        "保存",
        "取消",
    ],
    "ui_version_tag": "feishu-desktop-calendar",
}
