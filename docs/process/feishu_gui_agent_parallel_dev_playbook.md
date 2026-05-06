# Feishu GUI Agent Parallel Development Playbook

Current status: reference only. The default delivery mode is the
single-workspace serial flow in `AGENTS.md`.

Use this playbook only when the team explicitly switches to parallel track
development. It does not override the active runtime:

```text
feishu_agent = AgentS3 + WindowsFeishuACI + Feishu semantic priors
```

Do not use this document to restore `FeishuWorker`,
`planner/workflow_selector.py`, or product `*_workflow.py` stage machines.

## 1. Why Tracks Still Exist

Track names are retained as ownership and knowledge-layer boundaries. They no
longer mean that runtime execution is a fixed planner/workflow pipeline.

| Track | Current meaning | Typical files |
| --- | --- | --- |
| A | Natural-language input, testcase schema, semantic guidance artifacts | `gui_agents/feishu/testcases/`, `tests/feishu/testcases/` |
| B | Page knowledge, detectors, runtime-only locator contracts | `pages/`, `detectors/`, `locators/` |
| C | Tool guidance and verifier logic | `tooling/`, `verifiers/` |
| D | Runtime artifacts, reports, maintenance, evaluation aggregation | `reports/`, `maintenance/` |
| Serial | High-coupling AgentS3 / WindowsFeishuACI integration | `gui_agents/s3/agents/*`, `gui_agents/s3/cli_app.py` |

The purpose of this split is to keep ownership clear when multiple people or
agents work at the same time.

## 2. Default Serial Flow

Unless explicitly changed, development follows:

```text
analysis -> manual plan -> docs -> coding -> testing -> review
```

Required gates:

1. Run startup self-check before coding:
   `python -m unittest tests.test_agent_startup -v`
2. Write module analysis/plan under `docs/implementation/`.
3. Keep Feishu business logic under `gui_agents/feishu/`.
4. Do not put static coordinates, bounds, confidence, image dimensions, or
   workflow fields into page descriptors or screenshot fixtures.
5. Run module tests and `python scripts/run_ci_checks.py` before review.

## 3. Parallel Mode Entry Conditions

Parallel mode is allowed only after a contract freeze.

Freeze must cover:

- `docs/spec/feishu_gui_agent_technical_spec.md`
- `docs/interfaces/feishu_gui_agent_interfaces.md`
- `gui_agents/feishu/contracts.py`
- track ownership and write scopes
- current milestone scope

Freeze record should include:

- freeze commit SHA
- date
- owner
- reviewer
- affected tracks

If shared contracts change after freeze, pause affected tracks, update
spec/interfaces/contracts first, review, then resume from a new freeze point.

## 4. Parallel Ownership Boundaries

| Track | Owns | Must not edit without coordination |
| --- | --- | --- |
| A | `testcases/` and testcase tests | `contracts.py`, `runtime/`, `s3/` |
| B | `pages/`, `detectors/`, `locators/` and related tests | `tooling/`, `reports/`, `s3/` |
| C | `tooling/`, `verifiers/` and related tests | page descriptor contracts without B agreement |
| D | `reports/`, `maintenance/`, evaluation tooling | agent execution files |
| Serial | AgentS3 and WindowsFeishuACI integration files | broad product-domain rewrites |

High-coupling files remain serial even in parallel mode:

- `gui_agents/s3/agents/worker.py`
- `gui_agents/s3/agents/grounding.py`
- `gui_agents/s3/agents/grounding_feishu.py`
- `gui_agents/s3/agents/_feishu_exec.py`
- `gui_agents/s3/cli_app.py`
- `gui_agents/s3/memory/procedural_memory.py`

## 5. Worktree / Branch Rules

Use these only in explicit parallel mode:

1. Check existing worktrees first with `git worktree list`.
2. One active branch per worktree.
3. One active worktree per branch.
4. Start track branches from the same freeze SHA.
5. Keep the integration baseline clean.
6. Rebase or merge only after module tests pass.
7. If conflict resolution touches reviewed code, run review again.

## 6. Merge Order

Recommended merge order:

```text
Track A + Track B contracts
  -> Track C tooling/verifiers
  -> Track D reports/evaluation
  -> Serial integration
```

Serial integration should start after product-domain contracts are stable.

## 7. Review Gates

### Gate 1: Self-check

- module plan exists
- target files match ownership
- tests added or updated
- local verification output recorded

### Gate 2: Module review

- no contract drift
- failure paths are explicit
- no static quantitative screenshot metadata
- no fixed workflow runtime

### Gate 3: Integration review

Required for high-coupling files or cross-track merges:

- `python scripts/run_ci_checks.py`
- relevant Feishu tests
- constraint check passes
- runtime artifacts reviewed if live execution was involved

## 8. Current Architecture Guardrails

These rules are not optional:

- `feishu_agent` is the active Feishu runtime.
- No `FeishuWorker` runtime.
- No product-level fixed workflow controllers.
- Static Feishu metadata is semantic-only.
- Locator success may expose runtime action targets, but persisted page or
  fixture metadata must not contain coordinate priors.
- Reports should use `intent` and `params`, not workflow identity fields.

For current status and priorities, read:

- `docs/process/project_state.md`
- `docs/process/requirements_coverage_audit_2026-05-06.md`
- `docs/implementation/README.md`
