"""Registry for Feishu page descriptors."""

from __future__ import annotations

from gui_agents.feishu.contracts import PageDescriptor

from .feishu_shell_search import FEISHU_SHELL_SEARCH_DESCRIPTOR
from .im_chat_main import IM_CHAT_MAIN_DESCRIPTOR
from .im_chat_search_panel import IM_CHAT_SEARCH_PANEL_DESCRIPTOR


PAGE_REGISTRY: dict[str, PageDescriptor] = {
    FEISHU_SHELL_SEARCH_DESCRIPTOR["page_id"]: FEISHU_SHELL_SEARCH_DESCRIPTOR,
    IM_CHAT_MAIN_DESCRIPTOR["page_id"]: IM_CHAT_MAIN_DESCRIPTOR,
    IM_CHAT_SEARCH_PANEL_DESCRIPTOR["page_id"]: IM_CHAT_SEARCH_PANEL_DESCRIPTOR,
}


def get_page_ids() -> list[str]:
    return list(PAGE_REGISTRY)


def get_page_descriptor(page_id: str) -> PageDescriptor | None:
    return PAGE_REGISTRY.get(page_id)
