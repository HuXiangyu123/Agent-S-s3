"""Feishu Calendar home page descriptor."""

from __future__ import annotations

from gui_agents.feishu.contracts import PageDescriptor


CALENDAR_HOME_DESCRIPTOR: PageDescriptor = {
    "page_id": "calendar_home",
    "page_type": "calendar_home",
    "display_name": "Feishu Calendar Home",
    "layout_hints": {
        "surface": "feishu_desktop_calendar",
        "navigation": "calendar_sidebar",
        "main_view": "weekly_calendar_grid",
    },
    "key_regions": {
        "create_event_button": {
            "role": "primary_create_event_button",
            "visible_text": "创建日程",
        },
        "week_grid": {
            "role": "calendar_week_grid",
            "description": "weekly schedule grid with day columns and time slots",
        },
        "mini_month": {
            "role": "mini_month_picker",
            "description": "small month navigation calendar in the sidebar",
        },
    },
    "text_anchors": [
        "日历",
        "会议室",
        "预约活动",
        "创建日程",
        "今天",
    ],
    "ui_version_tag": "feishu-desktop-calendar",
}
