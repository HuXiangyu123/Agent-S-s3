# Docs Track ABCD Create Doc 2026-05-06

## Status

Superseded for fixed planner/workflow portions by
`docs/implementation/feishu_agent_migration_remove_workflows_2026-05-06.md`.
Docs support now enters `feishu_agent = AgentS3 + WindowsFeishuACI` as semantic
page/state knowledge, tool guidance, verifier hints, and passive report
artifacts. References below to `WorkflowPlan`, `workflow_selector.py`, or
`gui_agents/feishu/workflows/` are historical and not active implementation
targets.

## Goal

Complete a minimal Docs A/B/C/D domain chain for `create_doc_and_edit`.

The chain is:

```text
Natural language instruction
  -> TestCase
  -> WorkflowPlan
  -> Docs page/state facts
  -> Docs workflow stages
  -> Docs assertions
  -> RuntimeContext-compatible report artifacts
```

This is not a broad Docs automation rollout. It is the smallest structured path needed to prove Docs can reuse the existing Feishu domain architecture without copying all IM internals.

## Module Responsibilities

### Track A

Responsibilities:

- Extend shared contracts with minimal Docs action and assertion ids.
- Parse a Docs create/edit instruction into a structured `TestCase`.
- Select `create_doc_and_edit` workflow and bind `doc_title` / optional `body_text`.

Non-responsibilities:

- Free-form Docs task planning.
- Share/permission/upload/folder workflows.
- Runtime fallback or retry.

### Track B

Already started in `docs_track_b_pages_and_detector_2026-05-06.md`.

Responsibilities:

- Provide Docs page descriptors.
- Provide metadata-backed Docs state detection.
- Keep Docs-specific facts under `FeishuState.product_state`.

### Track C

Responsibilities:

- Build a deterministic `CreateDocAndEditWorkflow`.
- Verify Docs assertions from `FeishuState`, fixture metadata, runtime context, or OCR fallback.

Non-responsibilities:

- Real GUI action execution details.
- Browser helper implementation.

### Track D

Responsibilities:

- Reuse existing `ReportBuilder` and `ArtifactManager`.
- Add Docs coverage proving `RuntimeContext` and Docs `TestCase` can produce summary/report artifacts.

Non-responsibilities:

- Product-specific report format.

## Target Files

Code:

- `gui_agents/feishu/contracts.py`
- `gui_agents/feishu/testcases/scenario_schema.py`
- `gui_agents/feishu/testcases/nl_parser.py`
- `gui_agents/feishu/planner/workflow_selector.py`
- `gui_agents/feishu/workflows/create_doc_workflow.py`
- `gui_agents/feishu/workflows/__init__.py`
- `gui_agents/feishu/verifiers/assertion_verifier.py`

Tests:

- `tests/feishu/testcases/test_nl_parser.py`
- `tests/feishu/planner/test_task_planner.py`
- `tests/feishu/workflows/test_create_doc_workflow.py`
- `tests/feishu/verifiers/test_assertion_verifier.py`
- `tests/feishu/reports/test_report_builder.py`

## Manual Plan

Target files:

- Shared contracts and schema validation.
- Parser/planner selectors for Docs.
- New Docs workflow module.
- Existing assertion verifier with Docs branches.
- Existing report tests for Docs artifact compatibility.

Owner:

- Codex.

Depends on:

- Existing `FeishuState.product_state`.
- Existing Docs Track B descriptors and fixture metadata.
- Existing generic `ReportBuilder`.

Outputs:

- `TestCase(product="docs")` for create/edit instructions.
- `WorkflowPlan(workflow="create_doc_and_edit")`.
- Ordered Docs workflow steps.
- Verifier support for Docs readiness/title/body assertions.
- Report artifact compatibility for Docs runs.

Verification:

- Startup self-check.
- Docs parser/planner/workflow/verifier/report tests.
- Full `tests/feishu` discovery.
- Full `tests` discovery.

Risks:

- Existing Chinese parser text has mojibake legacy patterns; add clean Chinese patterns without removing old IM behavior.
- Docs body text is optional; title-only instructions must remain valid.
- Worker runtime still needs a later GUI execution pass before real desktop/browser E2E.

Rollback:

- Revert the new Docs workflow file and Docs-specific branches in parser/planner/verifier/contracts/tests. Track B descriptors and fixture metadata can remain useful even if Track C is redesigned.
