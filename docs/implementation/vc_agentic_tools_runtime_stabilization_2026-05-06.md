# VC Agentic Tools Runtime Stabilization 2026-05-06

## Module Analysis

Current `VC` support in `feishu_agent` is split across three layers:

1. semantic state coverage already exists:
   - page descriptors
   - `vc_state_detector`
   - tool-router guidance
   - final-state assertions and Track D reporting
2. active runtime execution is still weaker than `IM`
3. the main missing piece is not another executor, but `VC`-specific agentic tools that reduce ambiguous natural-language grounding

The present gap is structural:

- `IM` has dedicated helpers such as `feishu_type_message()` and `feishu_click_send_button()`
- `VC` still relies mostly on generic `feishu_click(...)`, `feishu_type(...)`, `click(...)`, and `type(...)`
- this forces the worker model to repeatedly describe meeting cards, preview buttons, meeting-ID input, or invite controls in long natural language
- `tool_router` can describe what should happen, but its recommendations are not the primary live control surface today; the worker prompt and available `agent_action` helpers matter more

From an M4 perspective, runtime reporting is now able to say whether a `VC` task semantically succeeded. The next missing step is runtime action stability:

- start-meeting path should have explicit helper affordances
- join-meeting path should have explicit helper affordances
- invite path should have explicit helper affordances
- invite popover/dialog transitions should be represented semantically enough for routing and verification

## Scope

This pass covers:

- `VC`-specific agentic helper actions inside `WindowsFeishuACI`
- `VC` tool registry / tool-router recommendations aligned with those helpers
- worker system-prompt guidance for `VC` tasks
- detector improvements for invite-related visible states where current fixtures already exist
- focused tests for detector/router/startup/runtime prompt surface

This pass does not cover:

- deterministic workflow restoration
- `planner -> workflow -> executor` runtime
- batch regression runner or dashboard work
- adding quantified screenshot metadata

## Boundaries

- Keep `feishu_agent = AgentS3 + WindowsFeishuACI`.
- Do not reintroduce `workflow.py` runtime control.
- Do not add fixed step chains for `VC`.
- Keep screenshot knowledge semantic-only.
- Specialized `VC` helpers are allowed only as reusable single-step semantic tools, not as a hidden workflow executor.

## Target Files

Primary implementation files:

- `gui_agents/s3/agents/grounding_feishu.py`
- `gui_agents/feishu/tooling/tool_registry.py`
- `gui_agents/feishu/tooling/tool_router.py`
- `gui_agents/feishu/detectors/vc_state_detector.py`

Planned test updates:

- `tests/feishu/detectors/test_vc_state_detector.py`
- `tests/feishu/tooling/test_tool_router.py`
- `tests/test_agent_startup.py`

Supporting process updates if implementation lands:

- `docs/process/project_state.md`
- `docs/process/development_log_2026-05-06.md`

## Implementation Plan

1. Add `VC` helper actions that encapsulate frequent semantic operations such as:
   - click start-meeting card
   - click join-meeting card
   - click start-meeting button
   - type meeting ID into the join preview
   - click join-meeting button
   - click invite toolbar control
   - click invite-menu entry / share button when relevant
2. Extend the worker prompt with a `VC` prior-tool strategy so the model sees these helpers as preferred first-class actions.
3. Update `tool_registry` and `tool_router` so tests and future recovery guidance reflect the new helper set.
4. Improve `vc_state_detector` for existing invite-related semantic fixtures.
5. Add targeted tests proving:
   - `VC` routes recommend the new helpers
   - invite-related state is detected semantically
   - startup gate still recognizes `VC` runtime support

## Verification

Planned verification for this pass:

- `python -m unittest tests.feishu.detectors.test_vc_state_detector -v`
- `python -m unittest tests.feishu.tooling.test_tool_router -v`
- `python -m unittest tests.test_agent_startup -v`
- `python scripts/run_ci_checks.py`

If `run_ci_checks.py` is too broad for the current environment, record the failing/blocked portion explicitly.

## Risks

1. Too many `VC` helpers can become a disguised workflow.
   Mitigation: keep helpers single-step and composable.

2. Invite flow has two visible layers (`meeting toolbar` -> `invite popover` -> `invite dialog`).
   Mitigation: represent the popover as semantic state and expose only the next visible control, not a fixed chain.

3. Worker prompt growth can reduce signal.
   Mitigation: keep the `VC` strategy short and only enable it for `VC`-like instructions.

## Rollback

If the new helpers degrade behavior:

1. revert the added `VC` agent actions in `grounding_feishu.py`
2. revert `tool_registry` / `tool_router` `VC` preferences
3. revert detector changes for invite popover classification

This rollback leaves Track D verification intact.
