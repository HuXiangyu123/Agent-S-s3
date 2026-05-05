"""Contracts for Feishu state-aware tool routing."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FeishuToolSpec:
    tool_name: str
    agent_action: str
    summary: str
    supported_page_types: tuple[str, ...]
    examples: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class FeishuToolRecommendation:
    page_type: str
    product: str
    state_summary: str
    next_step_focus: str
    enabled_tools: tuple[str, ...]
    preferred_tools: tuple[str, ...]
    discouraged_tools: tuple[str, ...]
    hints: tuple[str, ...]
    rationale: tuple[str, ...]
    target_chat_name: str | None = None
    detected_chat_name: str | None = None
