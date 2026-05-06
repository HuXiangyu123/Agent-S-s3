# Calendar Track ABCD Create Event

Date: 2026-05-06

## Status

Runtime route corrected.

The current product runtime is `feishu_agent = AgentS3 + WindowsFeishuACI`. Calendar must be implemented as semantic page/state knowledge and recovery guidance for the agent route. It must not introduce a deterministic `FeishuWorker` branch or a fixed `create_calendar_event` workflow controller.

## Module Responsibility

Implement the first Calendar vertical slice as a Feishu domain knowledge layer:

`screenshot/observation -> Calendar page descriptor -> Calendar detector -> FeishuState.product_state -> tool_router guidance -> AgentS3 + WindowsFeishuACI`

The output is state-aware guidance such as which visible text/control the agent should prefer next. It is not a pre-compiled step list.

## Scope

In scope:

- Calendar home and create-event modal page descriptors.
- Metadata-backed Calendar detector using `tests/fixtures/calendar` screenshots.
- Semantic fixture metadata for Calendar screenshots.
- Calendar branch in `tool_router` that gives `feishu_agent` recovery guidance.
- Tests for page registry, detector, fixture constraints, tool routing, and startup import path.

Out of scope for this pass:

- Event sharing workflow.
- Adding attendees.
- Video meeting settings.
- Calendar group binding.
- Arbitrary time-slot drag scheduling.

## Boundary Decisions

- Calendar business logic lives under `gui_agents/feishu/`.
- No new Feishu open-platform API dependency is introduced.
- No changes to high-coupling S3 worker internals are needed for Calendar.
- Calendar runtime facts stay in `FeishuState.product_state`.
- Screenshot metadata is the source of truth for B-layer tests; OCR fallback is only coarse runtime support.
- Screenshot-derived metadata must be semantic only: visible text, control names, modal/page state booleans, and intent names are allowed.
- Screenshot-derived metadata must not contain quantitative values: no coordinates, `relative_bounds`, `bbox`, confidence/score, pixel sizes, ratios, or measured counts.

## Target Files

- `gui_agents/feishu/pages/calendar_home.py`
- `gui_agents/feishu/pages/calendar_event_modal.py`
- `gui_agents/feishu/pages/registry.py`
- `gui_agents/feishu/detectors/calendar_state_detector.py`
- `gui_agents/feishu/detectors/__init__.py`
- `gui_agents/feishu/tooling/tool_router.py`
- `tests/fixtures/calendar/*.json`
- `tests/feishu/**/test_*calendar*`

## Manual Plan

- Owner: Codex.
- Depends on: Calendar screenshots, page registry, detector contracts, and `feishu_agent` tool routing.
- Outputs: Calendar page descriptors, semantic fixture metadata, Calendar detector, and `tool_router` guidance for opening Calendar, creating an event, typing title, saving, and recognizing related modal states.
- Verification: targeted Calendar tests, startup self-check, all Feishu tests, full unittest discovery, plus grep for forbidden quantitative metadata in Calendar-owned files.
- Risks: real UI field focus can differ from screenshots; save confirmation/toast is not covered until manual GUI validation.
- Rollback: remove Calendar descriptors, detector, tool routing branch, tests, and fixture metadata. No runtime worker branch should need rollback.

## Agent Guidance Contract

Calendar guidance is advisory and state-aware. It may recommend examples such as:

- `agent.feishu_click("日历")` when Calendar is not visible and the instruction clearly targets Calendar.
- `agent.feishu_click("创建日程")` when Calendar home is visible and creation is requested.
- `agent.feishu_type(title, "添加主题", overwrite=True, enter=False)` when the create-event modal is visible.
- `agent.feishu_click("保存")` when required event fields appear ready.

The agent must still re-check the current screenshot before acting; the guidance must not execute or force a fixed step sequence.

## Deferred Calendar States

The following screenshots are retained as future B-layer evidence but are not part of this first workflow:

- Event share pages.
- Attendee picker.
- Video meeting settings.
- Date picker/dropdown states.
