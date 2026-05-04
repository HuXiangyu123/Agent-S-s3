"""
Auto-switching reasoning_effort strategy for GPT/o-series models.

Default: medium
Complex scenarios (cross-window, app switching, multi-app workflows): xhigh
Step failure retry: xhigh (escalation)

Only effective when the model supports reasoning_effort (gpt-5.x, o-series).
Non-GPT models ignore the parameter (passed via **kwargs to API).
"""

from enum import Enum
from typing import Optional


class ReasoningEffort(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    XHIGH = "xhigh"


# Keywords indicating complex multi-window / cross-app operations.
# Target: operations that require reasoning across different UI contexts.
COMPLEX_PATTERNS = [
    # Explicit cross-window / app switching
    "切换应用",
    "切换窗口",
    "切换到",
    "切换程序",
    "跨窗口",
    "跨应用",
    "switch_app",
    "switch application",
    "switch window",
    "switch to",
    "alt+tab",
    "win+tab",
    # Multi-app data transfer workflows
    "复制到",
    "粘贴到",
    "移动到",
    "分享到",
    "同步到",
    "发送到",
    "转发到",
    # Complex Feishu cross-module (消息↔云文档, 消息↔日历, etc.)
    "从消息",
    "从云文档",
    "从日历",
    "到云文档",
    "到日历",
    "到邮箱",
    "到审批",
    # Complex file/import operations
    "导入到",
    "导出到",
    "另存为",
    "上传文件",
    "发送文件",
    # Multi-step batch operations
    "批量处理",
    "批量操作",
    "批处理",
    "合并文件",
    "合并文档",
]

# Simple, single-window operations — always use default effort
SIMPLE_PATTERNS = [
    "点击",
    "click",
    "输入",
    "type",
    "按",
    "press",
    "等待",
    "wait",
    "关闭",
    "close",
    "最小化",
    "最大化",
    "打开",
    "open",
]


def detect_complexity(
    task: str,
    last_action: Optional[str] = None,
    step_failed: bool = False,
    screenshot_complex: bool = False,
) -> ReasoningEffort:
    """
    Determine the appropriate reasoning_effort based on task/action context.

    Args:
        task: The current task instruction.
        last_action: The last executed action (plan text).
        step_failed: Whether the previous step failed and this is a retry.
        screenshot_complex: Whether the screenshot is visually complex (many windows).

    Returns:
        ReasoningEffort value to use for the next model call.
    """
    # Step failure always escalates to maximum effort
    if step_failed:
        return ReasoningEffort.XHIGH

    # Visually complex screens (many overlapping windows) need more reasoning
    if screenshot_complex:
        return ReasoningEffort.XHIGH

    # Check for complex multi-window / cross-app patterns
    task_lower = task.lower()
    for pattern in COMPLEX_PATTERNS:
        if pattern.lower() in task_lower:
            return ReasoningEffort.XHIGH

    # Also check the last action for complexity signals
    if last_action:
        action_lower = last_action.lower()
        complex_hits = sum(
            1 for p in COMPLEX_PATTERNS if p.lower() in action_lower
        )
        simple_hits = sum(
            1 for p in SIMPLE_PATTERNS if p.lower() in action_lower
        )
        if complex_hits > simple_hits:
            return ReasoningEffort.XHIGH

    return ReasoningEffort.MEDIUM


def reasoning_effort_for_step(
    task: str,
    step: int,
    last_action: Optional[str] = None,
    last_step_failed: bool = False,
    screenshot_complex: bool = False,
    default_effort: ReasoningEffort = ReasoningEffort.MEDIUM,
) -> ReasoningEffort:
    """
    Full reasoning_effort decision for a single step execution.

    Integrates default config with complexity detection and failure escalation.

    Args:
        task: The current task instruction.
        step: Current step number (0-indexed).
        last_action: The last executed action plan.
        last_step_failed: Whether the previous step failed.
        screenshot_complex: Whether the current screenshot is visually complex.
        default_effort: The configured default from env.txt / config.

    Returns:
        The ReasoningEffort to use for this step's model call.
    """
    # Override: step failure always forces xhigh
    if last_step_failed:
        return ReasoningEffort.XHIGH

    # Complex scenario detection
    return detect_complexity(
        task=task,
        last_action=last_action,
        step_failed=last_step_failed,
        screenshot_complex=screenshot_complex,
    )
