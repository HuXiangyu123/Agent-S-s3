# Track D Reports And Maintenance 2026-05-06

## Status

Partially superseded for runtime integration.

The `reports/` and `maintenance/` module responsibilities remain valid. The original deterministic integration path is not the active product runtime. Current runtime artifact generation is connected through `S3RuntimeRecorder` inside the LLM-driven `feishu_agent` route:

- `feishu_agent`: `AgentS3 + WindowsFeishuACI`
- Track D: passive recorder only
- Track C workflows: not a runtime controller

Do not use this document to route user instructions through a non-LLM workflow executor.

## Scope

Deliver the minimal Track D closure for the current Feishu IM MVP:

- consume `RuntimeContext`, `ActionLog`, and `StepResult`
- generate stable run artifacts under `artifacts/test_runs/<run_id>/`
- produce `summary.json`, `report.md`, and `actions.jsonl`
- persist runtime screenshots collected during execution
- keep the implementation scoped to the current IM `send_message` path

This round is not about adding new IM actions. It is about making the current runtime output reviewable and reusable.

## Current State

Track A, B, and C already exist in code:

- `gui_agents/feishu/testcases/`
- `gui_agents/feishu/planner/`
- `gui_agents/feishu/pages/`
- `gui_agents/feishu/detectors/`
- `gui_agents/feishu/locators/`
- `gui_agents/feishu/workflows/`
- `gui_agents/feishu/verifiers/`

The worker already returns a `RuntimeContext`, but Track D is still missing:

- no `gui_agents/feishu/reports/`
- no `gui_agents/feishu/maintenance/`
- no stable artifact writer
- no `summary.json` / `report.md` generation
- `RuntimeContext["screenshots"]` is currently unused

## Module Responsibilities

### `reports/`

Responsible for transforming runtime facts into stable outputs:

- build a structured summary from `TestCase + RuntimeContext`
- render a short Markdown report for review and debugging
- keep output deterministic and easy for later tooling to consume

### `maintenance/`

Responsible for artifact persistence and low-level run output management:

- prepare run directories
- write JSON / JSONL / Markdown files
- persist screenshots into a stable subdirectory

This round will not implement long-term drift detection or anchor maintenance. That is future maintenance work, not the minimal Track D gate.

## Boundaries

Track D must not:

- change parser / planner business semantics
- redefine workflow stage logic
- introduce new Feishu action primitives
- make `RuntimeContext` consumers depend on `AgentS3` private state

Track D may:

- read `RuntimeContext`
- infer assertion pass/fail from existing `step_results`
- write run artifacts to disk

## Target Files

New files:

- `gui_agents/feishu/reports/__init__.py`
- `gui_agents/feishu/reports/report_builder.py`
- `gui_agents/feishu/maintenance/__init__.py`
- `gui_agents/feishu/maintenance/artifact_manager.py`
- `tests/feishu/reports/__init__.py`
- `tests/feishu/reports/test_report_builder.py`
- `tests/feishu/maintenance/__init__.py`
- `tests/feishu/maintenance/test_artifact_manager.py`

Updated files:

- `gui_agents/feishu/agents/__init__.py`
- `tests/test_agent_startup.py`

## Implementation Plan

1. Add an `ArtifactManager` that owns:
   - run directory creation
   - `screenshots/` creation
   - writing `summary.json`
   - writing `report.md`
   - writing `actions.jsonl`
   - writing screenshot files
2. Add a `ReportBuilder` that:
   - builds a minimal structured summary
   - renders a compact Markdown report
   - delegates file persistence to `ArtifactManager`
3. Integrate Track D into `cli_app.py` via `S3RuntimeRecorder`:
   - initialize Track D helpers
   - save screenshots after step observations
   - finalize every run path with artifact generation
4. Add tests for:
   - summary generation
   - Markdown rendering
   - artifact file writing
   - worker import coverage

## Output Contract

The minimal artifact layout will be:

```text
artifacts/
  test_runs/
    <run_id>/
      screenshots/
      actions.jsonl
      summary.json
      report.md
```

`summary.json` should contain at least:

- `task_id`
- `product`
- `workflow`
- `status`
- `steps`
- `passed_steps`
- `failed_steps`
- `duration_sec`
- `assertions`
- `failure_type`
- `failure_reason`
- `run_id`

## Verification

Automated verification for this round:

- `tests/feishu/reports/test_report_builder.py`
- `tests/feishu/maintenance/test_artifact_manager.py`
- existing `tests/feishu/*`
- `tests.test_agent_startup`
- `python -m black --check launcher.py gui_agents tests`

## Risks

1. Worker-side artifact writing could accidentally couple runtime execution to filesystem failures.
   Mitigation: artifact writing should be best-effort and not crash a run result if persistence fails.

2. Duration calculation may be inconsistent if a run fails early.
   Mitigation: derive completion time at finalize time and keep the computation local to `ReportBuilder`.

3. Screenshot persistence could grow artifact size quickly.
   Mitigation: only store the observation screenshots already captured by the worker, with stable per-step names.

## Rollback

If Track D integration causes runtime instability:

1. revert `gui_agents/feishu/reports/`
2. revert `gui_agents/feishu/maintenance/`
3. remove the finalization hook from `cli_app.py`

Track A/B/C logic should remain intact because Track D only consumes their outputs.
