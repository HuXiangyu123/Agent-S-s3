"""Feishu state detectors."""

from .base_state_detector import detect_base_state
from .calendar_state_detector import detect_calendar_state
from .docs_state_detector import detect_docs_state
from .im_state_detector import detect_feishu_state, detect_im_state
from .vc_state_detector import detect_vc_state

__all__ = [
    "detect_base_state",
    "detect_calendar_state",
    "detect_docs_state",
    "detect_feishu_state",
    "detect_im_state",
    "detect_vc_state",
]
