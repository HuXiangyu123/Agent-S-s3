"""Feishu Base secondary surface descriptors."""

from __future__ import annotations

from gui_agents.feishu.contracts import PageDescriptor


BASE_SHARE_PANEL_DESCRIPTOR: PageDescriptor = {
    "page_id": "base_share_panel",
    "page_type": "base_share_panel",
    "display_name": "Feishu Base Share Panel",
    "layout_hints": {"surface": "browser_base_editor", "overlay": "share_panel"},
    "key_regions": {
        "base_share_panel_area": {
            "role": "share_panel",
            "description": "share side panel opened from the Base browser editor",
        }
    },
    "text_anchors": ["分享", "链接分享", "邀请", "权限"],
    "ui_version_tag": "feishu-browser-base-share-panel",
}

BASE_DASHBOARD_DESCRIPTOR: PageDescriptor = {
    "page_id": "base_dashboard",
    "page_type": "base_dashboard",
    "display_name": "Feishu Base Dashboard",
    "layout_hints": {"surface": "browser_base_editor", "view": "dashboard"},
    "key_regions": {
        "base_dashboard_canvas_area": {
            "role": "dashboard_canvas",
            "description": "dashboard canvas area shown after switching from grid view",
        }
    },
    "text_anchors": ["仪表盘", "添加组件"],
    "ui_version_tag": "feishu-browser-base-dashboard",
}

BASE_AUTOMATION_DESCRIPTOR: PageDescriptor = {
    "page_id": "base_automation",
    "page_type": "base_automation",
    "display_name": "Feishu Base Automation",
    "layout_hints": {"surface": "browser_base_editor", "view": "automation"},
    "key_regions": {
        "base_automation_panel_area": {
            "role": "automation_panel",
            "description": "automation or workflow panel within the Base browser surface",
        }
    },
    "text_anchors": ["自动化", "创建自动化流程", "工作流"],
    "ui_version_tag": "feishu-browser-base-automation",
}

BASE_APP_MARKET_DESCRIPTOR: PageDescriptor = {
    "page_id": "base_app_market",
    "page_type": "base_app_market",
    "display_name": "Feishu Base App Market",
    "layout_hints": {"surface": "feishu_desktop_base", "view": "app_market"},
    "key_regions": {
        "base_app_market_grid_area": {
            "role": "app_market_grid",
            "description": "main app-market content grid for Base apps and components",
        }
    },
    "text_anchors": ["应用", "热门应用", "应用市场", "添加组件"],
    "ui_version_tag": "feishu-desktop-base-app-market",
}
