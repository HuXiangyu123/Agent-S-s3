# Feishu Agent Migration And Workflow Removal

Date: 2026-05-06

## Module Analysis

The active Feishu runtime is `feishu_agent = AgentS3 + WindowsFeishuACI`. It is
LLM-driven and receives Feishu-specific tool guidance at runtime. The older
domain workflow stack (`planner/`, `workflows/`, `FeishuWorker`) is not the
product execution path and conflicts with the current principle that feature
development must be based on `feishu_agent`, not deterministic fixed workflows.

The user also clarified that information extracted from screenshots must remain
semantic. New VC screenshot metadata and VC page facts must not encode
quantitative coordinates, ratios, confidence scores, or step counts.

## Responsibilities

This pass does three things:

- Migrate startup and tests away from `WorkflowPlan` / deterministic workflow
  expectations.
- Remove all concrete workflow stage-machine modules and their tests.
- Keep product knowledge as semantic facts for `feishu_agent` guidance:
  page state, visible controls, intent hints, verifier/report facts.

## Boundaries

- Do not reintroduce `FeishuWorker`.
- Do not wire product scenarios through `planner -> workflow.steps()`.
- Do not add coordinate-like metadata for new VC fixtures.
- Keep `classic_s3` unchanged.
- Keep `feishu_agent` routed through `AgentS3 + WindowsFeishuACI`.

## Target Files

- `docs/implementation/vc_track_abcd_video_meeting_2026-05-06.md`
- `gui_agents/feishu/planner/*`
- `gui_agents/feishu/workflows/*`
- `gui_agents/feishu/pages/vc_*.py`
- `gui_agents/feishu/detectors/vc_state_detector.py`
- `gui_agents/feishu/tooling/tool_router.py`
- `tests/test_agent_startup.py`
- `tests/feishu/planner/*`
- `tests/feishu/workflows/*`
- `tests/feishu/tooling/test_tool_router.py`

## Manual Plan

- Target files: files listed above.
- Owner: Codex.
- Depends on: existing `feishu_agent` CLI route, `WindowsFeishuACI`,
  `S3RuntimeRecorder`, semantic detectors, and tool router.
- Outputs:
  - No concrete `gui_agents/feishu/workflows/*_workflow.py` modules.
  - No workflow stage-machine tests under `tests/feishu/workflows`.
  - Startup check verifies parser, semantic detectors, tool guidance, reports,
    and `AgentS3 + WindowsFeishuACI` routing instead of `WorkflowPlan`.
  - VC page descriptors use semantic roles only, not bounds.
  - VC guidance routes start/join/invite meeting instructions to appropriate
    Feishu tools.
- Verification:
  - `python -m unittest tests.test_agent_startup -v`
  - `python -m unittest tests.feishu.tooling.test_tool_router -v`
  - `python -m unittest discover tests/feishu -v`
  - `python scripts/run_ci_checks.py`
- Risks / rollback:
  - Existing docs may still mention historical workflows. This pass updates the
    active implementation evidence and startup gate; broader documentation
    cleanup can follow if needed.
  - Existing legacy locators may still contain coordinate contracts for older
    tests. They are not used by `feishu_agent` as a fixed runtime path.
