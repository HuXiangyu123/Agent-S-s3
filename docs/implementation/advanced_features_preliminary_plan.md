# Advanced Features Preliminary Implementation Plan

Date: 2026-05-06

## Status

Preliminary plan for 4 low-risk advanced features targeting M5 capabilities.
This plan is architectural guidance — not a sprint commitment. Each feature
must go through its own `module analysis → manual plan → code → test → review`
cycle before implementation.

## Selection Rationale

4 features selected from the 7 M5 candidates by lowest risk and highest
architectural alignment with the current `feishu_agent = AgentS3 +
WindowsFeishuACI` runtime:

| Feature | Risk | Rationale |
|---------|------|-----------|
| 异常场景处理 | Lowest | Extends existing `modal_type` + `product_state` pattern; no new runtime path |
| 自愈式执行 | Low | Worker already has `_detect_plan_failure` + `last_step_failed` + `reflection_mode` |
| 多轮对话编排 | Low-Med | Reuses `build_dynamic_guidance` + `route_feishu_tools` per-step injection |
| 录制回放语义轨迹版 | Low | Extends `S3RuntimeRecorder` output — pure data, no execution control |

**Excluded for now:**
- 混合定位策略 (Accessibility/UIA/DOM fusion): environment risk too high
- 测试用例自动生成 (doc parsing / recording understanding / quality control): scope explosion risk
- 跨产品联动测试 (IM→Calendar→Docs): depends on stable live product paths not yet validated

## Why Serial Is Required

Serial delivery is an architectural constraint, not a process preference.
All 4 features share the same runtime hot path and the same output contract:

### 1. Execution Entry Is Highly Coupled

The active runtime is a single pipeline:

```
cli_app.py → Worker.__init__ → WindowsFeishuACI.__init__
  → _prepare_generator_system_prompt → build_worker_system_prompt
  → [per-step] generate_coords → generate_action → _detect_plan_failure
```

Key files on this path:

- `gui_agents/s3/agents/worker.py` (Worker loop + plan generation)
- `gui_agents/s3/agents/grounding_feishu.py` (WindowsFeishuACI + agent actions)
- `gui_agents/s3/cli_app.py` (CLI entry + execution_mode routing)
- `gui_agents/feishu/reports/s3_runtime_recorder.py` (passive recorder)

Parallel development on these files would produce merge conflicts at the
prompt assembly and state injection points. Self-healing and multi-turn
orchestration both modify the same `_prepare_generator_system_prompt` and
`build_dynamic_guidance` call sites.

### 2. Single RuntimeContext Shared by All Features

```
Exception handling → writes anomaly_events into RuntimeContext
Self-healing      → reads last_step_failed, writes recovery_attempts
Multi-turn        → writes state_summary per turn
Semantic trace    → reads all of the above + step_results
```

If these land in parallel with different field schemas, `ReportBuilder` and
`S3RuntimeRecorder.finalize()` cannot produce consistent outputs. Serial
delivery guarantees the RuntimeContext schema is frozen before the next
feature writes to it.

Current RuntimeContext (`contracts.py:152-168`):

```python
class RuntimeContext(TypedDict):
    run_id: str
    status: str
    intent: str | None
    params: dict[str, Any]
    page_id: str | None
    precondition_results: list[dict[str, Any]]
    action_logs: list[ActionLog]
    screenshots: list[str]
    step_results: list[StepResult]
    failure_type: FailureType | None
    failure_reason: str | None
    started_at: str
    product: NotRequired[str | None]
    task_id: NotRequired[str | None]
    task_title: NotRequired[str | None]
    assertion_plan: NotRequired[list[dict[str, Any]]]
```

This is already clean of workflow remnants. Before any advanced feature
implementation, add the shared fields needed by all 4 features:

```python
# Proposed additions (step 0 — freeze before feature work)
recovery_attempts: NotRequired[int]
anomaly_events: NotRequired[list[dict[str, Any]]]
semantic_steps: NotRequired[list[dict[str, Any]]]
```

### 3. Prevents Fixed Workflow Regression

The highest risk for M5 is that recovery logic silently becomes a
deterministic fallback chain:

```
# ANTI-PATTERN — must not happen:
if page_type == "blocked_by_modal":
    click("close_button")        # hardcoded step 1
    wait(1.0)                     # hardcoded step 2
    verify("modal_gone")          # hardcoded step 3
```

Serial review at each feature merge ensures every recovery/guidance
mechanism stays within the `guidance → AgentS3 LLM decides → act` pattern
and never becomes `if state X then do Y`.

### 4. Unified CI Evidence

`scripts/run_ci_checks.py` is the single local/CI entry point. Serial
delivery means every feature merge runs the full constraint check +
startup test + all feishu tests before the next feature starts.

---

## Feature 1: 异常场景处理 (Exception Handling)

### Goal

Let the agent recognize *why* it cannot proceed — popup blocking,
permission denied, loading, wrong surface — and surface a recovery hint.

### Code Landing Points

- `gui_agents/feishu/detectors/*_state_detector.py` — detect anomaly state
- `gui_agents/feishu/tooling/tool_router.py` — inject recovery hints
- `gui_agents/feishu/verifiers/assertion_verifier.py` — verify anomaly resolved
- `gui_agents/feishu/reports/s3_runtime_recorder.py` — record anomaly event

### Semantics (NOT coordinates)

Extend `FeishuState.product_state` with anomaly flags. No new top-level
fields needed — `product_state` is the spec-approved extension point
(`spec 5.2`):

```python
product_state = {
    # ... existing per-product fields ...

    # Anomaly flags (add to detectors that observe them)
    "blocking_modal_visible": True,
    "permission_denied_visible": False,
    "loading_visible": False,
    "wrong_surface": False,

    # Recovery guidance (semantic only — never coordinates)
    "recovery_hint": "close_modal_or_wait",
}
```

`recovery_hint` values are semantic labels, not action sequences:
`close_modal_or_wait`, `retry_after_load`, `navigate_to_correct_page`,
`request_permission`, `dismiss_and_continue`.

### Detection Strategy

Each detector's `_fallback_state()` already reads OCR text. Add anomaly
keyword detection as a pre-check before page classification:

```python
# In detectors/*_state_detector.py fallback path
ANOMALY_KEYWORDS = {
    "blocking_modal": ("确定", "取消", "知道了", "关闭", "重试"),
    "permission_denied": ("权限不足", "无权限", "需要权限", "申请权限"),
    "loading": ("加载中", "正在加载", "请稍候"),
    "wrong_surface": ("页面不存在", "已删除", "已归档"),
}
```

When anomaly keywords are detected, set the corresponding flags + recovery_hint
*before* page classification.

### Tool Router Integration

In `route_feishu_tools()`, add an anomaly pre-check before the page_type
branch:

```python
# Before the page_type elif chain:
anomaly_hints = _build_anomaly_guidance(product_state)
hints.extend(anomaly_hints)
if product_state.get("blocking_modal_visible"):
    next_step_focus = "dismiss_blocking_modal"
    # Allow click tool for dismissal buttons
    enabled_tools.append("click")
```

### Verifier

Add assertions for anomaly states:

- `modal_dismissed` — modal no longer visible after dismiss action
- `loading_completed` — loading indicator gone, surface ready

### Report

`S3RuntimeRecorder.record_action()` records `anomaly_events` when
`blocking_modal_visible` or similar flags are true.

### Verification

- Fixture-based detector tests: OCR text containing "权限不足", "加载中",
  "取消" → detector outputs correct anomaly flags.
- Tool router test: anomaly state → recovery hint in guidance output.
- Constraint check: no new `workflow`, `steps`, `ordered` in anomaly path.

---

## Feature 2: 自愈式执行 (Self-Healing)

### Goal

When the previous step failed (page unchanged, wrong action), inject
recovery guidance into the next Worker prompt instead of letting the
LLM repeat the same failing action.

### Code Landing Points

- `gui_agents/s3/agents/worker.py` — inject recovery context
- `gui_agents/s3/agents/grounding_feishu.py` — `build_dynamic_guidance` extension
- `gui_agents/feishu/tooling/tool_router.py` — anomaly-aware guidance

### Existing Foundation

Worker already has the core mechanism (`worker.py:171-198, 478-479`):

```python
@staticmethod
def _detect_plan_failure(plan: str) -> bool:
    # Checks (State Verification) for "Behind:", "no effect", "still empty", etc.

# After plan parsing:
if not self.last_step_failed and self._detect_plan_failure(plan):
    self.last_step_failed = True
```

`reasoning_effort_for_step()` already escalates thinking when `last_step_failed=True`.

### Self-Healing Injection

When `last_step_failed=True`, append recovery context to the next round's
dynamic guidance:

```python
# In WindowsFeishuACI.build_dynamic_guidance() (called per-step):
def build_dynamic_guidance(self, instruction, obs):
    guidance = build_feishu_tool_guidance(instruction, obs)
    if self._worker_last_step_failed:  # needs to be exposed from Worker
        guidance += (
            "\n## Recovery Mode\n"
            "- The previous action had no effect or failed.\n"
            "- Do NOT repeat the same action.\n"
            "- First verify the current screen state, then choose an alternative path.\n"
            "- If a modal/popup blocks the surface, dismiss it before continuing.\n"
            "- If the expected element is not visible, search for an alternative entry point.\n"
        )
    return guidance
```

Worker exposes `last_step_failed` via `grounding_agent` attribute or shared
context dict — avoid tight coupling.

### Recovery Attempt Tracking

```python
# In S3RuntimeRecorder.record_action():
if runtime_context["recovery_attempts"] > 0:
    step_result["recovery"] = True
    step_result["recovery_attempt"] = runtime_context["recovery_attempts"]
```

### Constraint

Recovery guidance MUST be hints only. The self-healing module MUST NOT
contain `if page_type == X then action Y` logic. All action decisions
remain with AgentS3 LLM loop.

### Verification

- Unit test: simulate `last_step_failed=True` → `build_dynamic_guidance`
  output contains recovery block.
- Integration test: detector fixture with blocking modal → tool router
  injects "dismiss modal" hint → recovery guidance present in output.
- Constraint: `check_constraints.py` confirms no new `*_workflow.py` or
  deterministic step executor.

---

## Feature 3: 多轮对话编排 (Multi-Turn Orchestration)

### Goal

Feed concise per-turn state/guidance into the Worker prompt so the Agent
dynamically adjusts across turns without a fixed workflow.

### Code Landing Points

- `gui_agents/s3/agents/grounding_feishu.py` — `build_worker_system_prompt` extension
- `gui_agents/feishu/tooling/tool_router.py` — per-turn guidance formatting
- `gui_agents/feishu/reports/s3_runtime_recorder.py` — per-turn state recording

### Existing Foundation

`build_dynamic_guidance()` (`grounding_feishu.py:741-747`) already calls
`build_feishu_tool_guidance()` which internally calls `route_feishu_tools()`
with state detection. The per-turn pipeline exists:

```
observation → detect state → route guidance → build guidance text
```

### Turn State Injection

Format a concise per-turn context block (NOT full history dump):

```
## Current Feishu State
product=vc, page_type=vc_start_preview, start_button=visible

## Tool Guidance
Next focus: start_meeting_button
Preferred: feishu_click, click, wait
Avoid: fixed step replay
```

This is derived from `FeishuToolRecommendation` fields that already exist:

- `state_summary` → "Current Feishu State" line
- `next_step_focus` + `preferred_tools` → "Tool Guidance" block

### Integration Point

Inject the turn state block at the start of each Worker step, before the
LLM generates the next plan. The `build_worker_system_prompt()` sets up the
system-level prompt (called once). The per-turn injection goes through
`build_dynamic_guidance()` (called before each action generation).

### Avoid Duplicate Detection

`route_feishu_tools()` already accepts `state: FeishuState | None`.
Multi-turn orchestration should:

1. Call detector once per turn: `state = detect_*_state(obs)`
2. Pass to router: `route_feishu_tools(instruction, obs, state=state)` — skips internal re-detection
3. Format guidance from the returned `FeishuToolRecommendation`

### Verification

- Test: different page_type inputs → `next_step_focus` changes accordingly.
- Test: same page_type, different product_state → hints adapt to state.
- Constraint: no ordered step sequence in guidance output.

---

## Feature 4: 录制回放语义轨迹版 (Semantic Trace Recording)

### Goal

Record a semantic trace (NOT coordinate scripts) for post-run review and
future replay draft generation. Satisfies the M5 recording/replay
requirement without the fragility of coordinate-based scripts.

### Code Landing Points

- `gui_agents/feishu/reports/s3_runtime_recorder.py` — new `record_semantic_step()`
- `gui_agents/feishu/reports/report_builder.py` — new `build_replay_draft()`
- Output: `artifacts/test_runs/<run_id>/semantic_trace.json`
- Output: `artifacts/test_runs/<run_id>/replay_draft.md`

### Semantic Trace Format

Each step records semantic facts only:

```json
{
  "step_index": 0,
  "step_id": "s3_step_001",
  "page_type": "vc_home",
  "product": "vc",
  "visible_controls": ["发起会议", "加入会议", "历史记录"],
  "action_summary": "click start meeting card",
  "action_code": "agent.feishu_click('发起会议')",
  "verification": "vc_start_preview_ready",
  "verification_passed": true,
  "failure_type": null,
  "recovery_attempt": false,
  "timestamp": "2026-05-06T15:30:00+08:00"
}
```

### Replay Draft

`replay_draft.md` is a human-reviewable natural-language sequence, NOT
an executable script:

```markdown
# Replay Draft — Run s3_feishu_20260506_150000_a1b2c3d4
## Step 1
- Page: VC Home (视频会议主页面)
- Action: 点击"发起会议"卡片
- Verify: 确认进入开始会议预览页面

## Step 2
- Page: VC Start Preview
- Action: 点击"开始会议"按钮
- Verify: 确认进入会议中页面
```

### Implementation

`S3RuntimeRecorder` already records per-step `action_logs` and
`step_results`. Add a parallel `record_semantic_step()` method that captures
the FeishuState snapshot + action summary. Call it from the Worker loop
after each action completes.

`ReportBuilder` already generates `summary.json`, `report.md`, and
`actions.jsonl`. Add `build_replay_draft()` that reads `semantic_steps`
from `RuntimeContext` and generates the markdown.

### Constraint

replay_draft.md MUST NOT include coordinates, bbox, confidence scores,
or image dimensions. It MUST NOT be auto-executed by any runtime path.
It is a documentation artifact only.

### Verification

- Test: a completed RuntimeContext with semantic_steps →
  `build_replay_draft()` produces valid markdown.
- Test: replay_draft.md contains no coordinates or quantitative metrics.
- Constraint: no `exec(replay_code)` or equivalent in any module.

---

## Recommended Implementation Order

### Step 0: RuntimeContext Field Freeze (prerequisite)

Target: `gui_agents/feishu/contracts.py`

Add shared fields needed by all 4 features:

```python
class RuntimeContext(TypedDict):
    # ... existing fields ...
    recovery_attempts: NotRequired[int]
    anomaly_events: NotRequired[list[dict[str, Any]]]
    semantic_steps: NotRequired[list[dict[str, Any]]]
```

Freeze and commit before any feature implementation begins.

### Step 1: 异常场景处理

Depends on: Step 0.
Delivers: anomaly detection + recovery hints + report recording.

### Step 2: 自愈式执行

Depends on: Step 1 (anomaly detection output).
Delivers: recovery prompt injection when `last_step_failed=True`.

### Step 3: 多轮对话编排

Depends on: Step 2 (guidance injection point).
Delivers: per-turn concise state/guidance block in Worker prompt.

Can be developed in parallel with Step 2 if the injection point contract
is frozen first (both use `build_dynamic_guidance()`).

### Step 4: 录制回放语义轨迹版

Depends on: Steps 1-3 (semantic_steps populated by previous features).
Delivers: `semantic_trace.json` + `replay_draft.md`.

Lowest dependency — could start after Step 0 if desired, but best done
last since it consumes output from all other features.

---

## Risk Assessment

| Risk | Affected Feature | Mitigation |
|------|-----------------|------------|
| Anomaly keywords overlap with normal UI text | 异常场景处理 | `recovery_hint` requires multiple keyword matches or context check |
| Self-healing hints become deterministic fallback | 自愈式执行 | Serial review gate; constraint check for `if state then action` |
| Per-turn prompt grows too large | 多轮编排 | Concise format (≤200 chars); full history stays in `RuntimeContext` |
| Semantic trace grows unboundedly | 录制回放 | Fixed fields; no screenshot embedding in trace |
| RuntimeContext field drift | All | Step 0 freeze; contract change requires AGENTS.md review |

---

## Verification Strategy

Each feature merge runs:

```
python scripts/check_constraints.py   # No dead code regression
python -m unittest tests.test_agent_startup -v  # All imports + core pipeline
python -m unittest discover tests/feishu -v     # All feishu tests
python scripts/run_ci_checks.py      # Full CI parity
```

Feature-specific verification described in each section above.
