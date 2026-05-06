# VC Track A/B/C/D Video Meeting Implementation

## Status

Superseded for fixed planner/workflow portions by
`docs/implementation/feishu_agent_migration_remove_workflows_2026-05-06.md`.
VC support now enters `feishu_agent = AgentS3 + WindowsFeishuACI` as semantic
page/state knowledge and tool guidance. VC screenshot metadata must remain
semantic only; references below to workflow selector, `WorkflowPlan`, or
`gui_agents/feishu/workflows/` are historical and not active implementation
targets.

## Module Analysis

This change adds the first Video Conference (`vc`) product slice to the existing
Feishu GUI Agent domain layer. The implementation follows the current single
workspace, serial delivery mode and reuses the established A/B/C/D layering:

- Track A: NL parser, testcase schema, workflow selector.
- Track B: page descriptors, state detector, vision locator, fixture metadata.
- Track C: explicit workflow state machines and assertion verifier.
- Track D: report compatibility through existing `ReportBuilder` contract.

The VC slice is GUI-first and does not assume Feishu Open Platform access.

## Responsibilities

VC support covers two controlled workflows:

1. Start an instant meeting from the VC home screen.
2. Join a meeting by meeting ID from the VC home screen.

The module recognizes the captured VC pages:

- VC home: entry cards for start and join meeting.
- VC start preview: microphone/camera controls and start button.
- VC active meeting: active meeting toolbar and participant status.
- VC join preview: meeting ID input and join button.
- VC invite popover/dialog states are retained as observable VC states for
  follow-up invite workflows, but not wired into Track A/C in this change.

## Boundaries

- Business logic stays under `gui_agents/feishu/`.
- `gui_agents/s3/` runtime integration is not changed in this slice.
- Existing IM and Docs contracts remain backward compatible.
- Shared `ActionId`, `TargetId`, and `AssertionId` are extended only with VC ids.
- `ReportBuilder` is not specialized for VC because it already consumes generic
  `testcase` and `RuntimeContext` fields.

## Key Interactions

```text
Natural language
  -> parse_instruction()
  -> TestCase(product="vc")
  -> plan_testcase()
  -> start_vc_meeting / join_vc_meeting plan
  -> VC workflow next_step()
  -> detect_vc_state()
  -> locate_target()
  -> AssertionVerifier
  -> ReportBuilder
```

## Target Files

- `docs/interfaces/feishu_gui_agent_interfaces.md`
- `gui_agents/feishu/contracts.py`
- `gui_agents/feishu/testcases/scenario_schema.py`
- `gui_agents/feishu/testcases/nl_parser.py`
- `gui_agents/feishu/planner/workflow_selector.py`
- `gui_agents/feishu/pages/registry.py`
- `gui_agents/feishu/pages/vc_home.py`
- `gui_agents/feishu/pages/vc_start_preview.py`
- `gui_agents/feishu/pages/vc_meeting_active.py`
- `gui_agents/feishu/pages/vc_join_preview.py`
- `gui_agents/feishu/pages/vc_invite_dialog.py`
- `gui_agents/feishu/detectors/vc_state_detector.py`
- `gui_agents/feishu/detectors/__init__.py`
- `gui_agents/feishu/locators/vision_locator.py`
- `gui_agents/feishu/workflows/vc_meeting_workflow.py`
- `gui_agents/feishu/workflows/__init__.py`
- `gui_agents/feishu/verifiers/assertion_verifier.py`
- `tests/fixtures/vc/*.json`
- `tests/fixtures/vc/manifest.json`
- `tests/feishu/testcases/test_nl_parser.py`
- `tests/feishu/planner/test_task_planner.py`
- `tests/feishu/pages/test_vc_registry.py`
- `tests/feishu/detectors/test_vc_state_detector.py`
- `tests/feishu/locators/test_vision_locator.py`
- `tests/feishu/workflows/test_vc_meeting_workflow.py`
- `tests/feishu/verifiers/test_assertion_verifier.py`
- `tests/feishu/reports/test_report_builder.py`

## Design Choices

- VC fixture JSON is the source of truth for page recognition in tests, matching
  the current Docs and IM fixture pattern.
- Detection falls back to OCR keyword heuristics when metadata is absent.
- Locators use page descriptors and fixture `key_regions`, returning structured
  location failures instead of dummy coordinates.
- Workflows are explicit stage machines. Planner selects only the workflow and
  binds parameters; retry/fallback remains in workflow output.
- Invite states are observable only. This avoids adding an invite workflow before
  the action contract and success gate are stable.

## Manual Plan

- Target files: files listed above.
- Owner: Codex.
- Depends on: existing `TestCase`, `WorkflowPlan`, `FeishuState`,
  `LocatorResult`, `RuntimeContext`, `ReportBuilder` contracts.
- Outputs:
  - VC shared ids in interface and code contracts.
  - VC parser/planner support for start and join meeting instructions.
  - VC page descriptors, detector, locator targets, workflows, assertions.
  - Fixture metadata for captured VC screenshots.
  - Module tests and CI parity evidence.
- Verification:
  - `python -m unittest tests.feishu.testcases.test_nl_parser -v`
  - `python -m unittest tests.feishu.planner.test_task_planner -v`
  - `python -m unittest tests.feishu.pages.test_vc_registry -v`
  - `python -m unittest tests.feishu.detectors.test_vc_state_detector -v`
  - `python -m unittest tests.feishu.locators.test_vision_locator -v`
  - `python -m unittest tests.feishu.workflows.test_vc_meeting_workflow -v`
  - `python -m unittest tests.feishu.verifiers.test_assertion_verifier -v`
  - `python scripts/run_ci_checks.py`
- Risks / rollback:
  - Risk: coarse screenshot regions may need later adjustment after live UI drift.
    Rollback by removing VC descriptor registrations and VC parser/planner branch.
  - Risk: join button can be disabled until a real meeting ID is entered; current
    tests verify the disabled fixture and OCR/metadata state, not live enablement.
  - Risk: invite UI is documented and detected but intentionally not part of the
    first controlled workflow.
