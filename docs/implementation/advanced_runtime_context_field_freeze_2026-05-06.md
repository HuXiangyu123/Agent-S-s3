# Advanced RuntimeContext Field Freeze

Date: 2026-05-06

## Module Analysis

This implementation follows `docs/implementation/advanced_features_preliminary_plan.md`
and only lands Step 0: freeze the shared optional `RuntimeContext` fields needed by
the selected advanced features.

The four advanced features in that plan are not safe to implement in parallel with
the current repair work because they all touch the runtime hot path:

- exception handling writes anomaly facts into runtime context and router guidance
- self-healing reads failure state and injects recovery guidance into per-step prompt
- multi-turn orchestration formats per-turn state in the same guidance path
- semantic trace recording consumes recorder and report-builder outputs

Given the current dirty workspace includes `worker.py`, `grounding_feishu.py`,
`cli_app.py`, recorder/report files, detectors, router, and fixture updates, the
non-conflicting task is limited to the shared contract addition.

## Boundary

In scope:

- Add optional shared fields to `RuntimeContext`
- Add a focused contract test that verifies the fields are present and optional
- Keep the change semantic-only and free of fixed workflow behavior

Out of scope:

- No anomaly detection implementation
- No recovery prompt injection
- No multi-turn prompt assembly changes
- No semantic trace artifact generation
- No coordinate, bbox, confidence, image-size, or other quantitative metadata

## Target Files

- `gui_agents/feishu/contracts.py`
- `tests/feishu/runtime/test_runtime_context_contract.py`

## Manual Plan

- Owner: Codex
- Depends on: `advanced_features_preliminary_plan.md` Step 0
- Outputs: `recovery_attempts`, `anomaly_events`, and `semantic_steps` as
  `NotRequired` fields on `RuntimeContext`
- Verification: startup gate, focused contract test, constraint check
- Rollback: remove the three optional annotations and the focused test

## Design Choice

The fields are optional to preserve compatibility with existing runtime contexts
and report artifacts. This freezes the schema without forcing all call sites to
populate the fields immediately.

The change deliberately avoids executable recovery logic. The future advanced
features must still follow the `guidance -> AgentS3 decides -> act` path rather
than adding deterministic workflows.

## Risks

- Contract drift if later feature work adds different field names
- Hidden runtime assumptions if future code treats optional fields as required
- Merge conflicts if another repair modifies `RuntimeContext` simultaneously

## Verification Evidence

- `python -m unittest tests.feishu.runtime.test_runtime_context_contract -v`
  passed, 2 tests OK
- `python -m unittest tests.test_agent_startup -v`
  passed, 165 tests OK
- `python scripts/check_constraints.py`
  passed, all constraints OK
