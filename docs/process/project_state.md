# Project State

Last updated: 2026-05-06

## Goal

Build a Windows-first Feishu desktop GUI agent on top of `Agent-S`, with the
active product route centered on:

- `classic_s3`: `AgentS3 + OSWorldACI`
- `feishu_agent`: `AgentS3 + WindowsFeishuACI`

The current codebase no longer treats deterministic `planner/ -> workflow`
stage machines as the product runtime.

## Active Runtime

Current effective Feishu runtime:

```text
Natural language / user instruction
  -> AgentS3 LLM loop
  -> WindowsFeishuACI
  -> Feishu semantic priors:
     pages / detectors / tool_router / verifiers / reports
```

Current implications:

- `feishu_agent` is the active Feishu-specific route.
- `FeishuWorker` and product `*_workflow.py` runtime controllers have been removed.
- Page metadata for new product slices is constrained to semantic facts only.
- `Track ABCD` now acts as an agentic knowledge/tool layer, not a fixed executor.

## Requirement Snapshot

This section checks the current repository state against `docs/项目需求.md`.

### Must-Have Capabilities

1. Visual perception: largely implemented at the semantic layer.
   Evidence:
   - Page descriptors and state detectors exist for `IM`, `Docs`, `Calendar`,
     `Base`, and `VC`.
   - Startup and Feishu test suite cover registry/detector imports and fixture
     compatibility.

2. Semantic understanding: partially implemented.
   Current status:
   - `IM` text send-message parsing is stable.
   - `Docs` and `VC` still have parser coverage for structured testcase inputs.
   - `Calendar` and `Base` no longer compile fixed workflows and are expected to
     run through `feishu_agent` semantic guidance instead.

3. Autonomous operation: partially implemented.
   Current status:
   - `IM` has the strongest runtime support, including Feishu-specific click/type
     helpers and grounded fallback.
   - Browser-aware helpers exist for Docs-related browser surfaces.
   - `Calendar`, `Base`, and `VC` currently rely more on semantic tool guidance
     than on fully validated live task execution.

4. State verification: partially implemented.
   Current status:
   - `IM`, `Docs`, and `Base` assertions are implemented in
     `AssertionVerifier`.
   - `Calendar` and `VC` detector coverage exists, but dedicated verifier
     branches are still missing.

5. Evaluation report: partially to substantially implemented.
   Current status:
   - Per-run artifacts are generated through `S3RuntimeRecorder`,
     `ReportBuilder`, and `ArtifactManager`.
   - `summary.json`, `report.md`, `actions.jsonl`, and screenshot persistence
     are in place.
   - Batch-level success-rate aggregation and a regression dashboard are not yet
     implemented.

### Milestone Snapshot

| Milestone | Requirement target | Current status |
| --- | --- | --- |
| `M0` | Agent startup baseline | Done |
| `M1` | 5 single-step actions | Mostly done at runtime/tool level |
| `M2` | 1 product, 3 end-to-end flows | Partially done; IM main path exists, but 3 stable E2E flows are not yet complete |
| `M3` | 2+ products stable runnable | Partially done; 5 products have semantic/domain coverage, but stable live runnable coverage still lags |
| `M4` | structured evaluation system | Partially done; per-run artifact layer exists, batch evaluation not yet done |
| `M5` | 1-2 advanced features | Partially done; exception handling and self-heal primitives exist, others remain open |

## Product Coverage

### IM

Current status: strongest and closest to production use.

Implemented:

- IM page descriptors and detectors
- search-panel and shell-search state handling
- Feishu-specific IM typing/click helpers
- tool routing for composer, send, search, and emoji fallback
- IM assertion verification
- runtime artifact recording

Not yet complete:

- broader IM workflow matrix beyond the current text send path
- richer live-validated paths such as file send, image send, `@` mention, and
  emoji end-to-end completion

### Docs

Current status: semantic/domain slice mostly present, runtime completeness not
yet at IM level.

Implemented:

- Docs page descriptors
- Docs state detector
- title/body-related verifier branches
- historical parser support

Missing or weaker:

- product-specific tool-router branch comparable to IM/Calendar/VC
- live end-to-end validation in the active `feishu_agent` route

### Calendar

Current status: semantic/domain slice present, runtime still shallow.

Implemented:

- Calendar page descriptors
- Calendar detector
- semantic-only fixture constraints
- Calendar tool-router guidance

Missing:

- dedicated verifier branches
- validated end-to-end create-event runtime path

### Base

Current status: semantic/domain slice present after cleanup.

Implemented:

- Base page descriptors
- Base detector
- Base tool-router guidance
- semantic-only metadata constraints
- explicit rejection of fixed workflow parsing and fixed coordinate locating

Missing:

- validated end-to-end live runtime path
- dedicated batch evaluation around Base tasks

### VC

Current status: in progress and currently the main remaining app-level repair
item.

Implemented:

- VC page descriptors
- VC detector
- VC tool-router guidance
- semantic-only fixture constraints

Missing:

- verifier branches
- stable live runtime path validation for start/join/invite flows

## Auto Evaluation Status

### Implemented

- `tests.test_agent_startup` as session startup gate
- `tests.test_launcher_env_config` for launcher env routing
- `scripts/run_ci_checks.py` for local/GitHub CI parity
- `scripts/check_constraints.py` for architecture guardrails
- `S3RuntimeRecorder` passive runtime capture
- `ArtifactManager` stable artifact persistence
- `ReportBuilder` for `summary.json` and `report.md`

### Output Currently Available

Per-run outputs under `artifacts/test_runs/<run_id>/`:

- `summary.json`
- `report.md`
- `actions.jsonl`
- `screenshots/`

### Still Missing

- regression runner over a test suite
- aggregate success-rate reporting across runs
- dashboard / visualization layer
- trend comparison between runs

## Advanced Feature Status

Checked against the advanced requirements in `docs/项目需求.md`.

### 1. Exception handling

Status: partially implemented.

Evidence:

- detectors preserve `modal_type`
- tool routing includes popup/dialog-aware branches
- runtime can classify recognition/location/action/verification failures

Gap:

- no unified abnormal-scene recovery matrix across all products

### 2. Self-healing execution

Status: partially implemented.

Evidence:

- `Worker` supports `reflection_mode=on_failure`
- runtime detects when the previous action had no effect
- `feishu_click(...)` can prepare a grounded fallback for icon-only controls
- verifier supports OCR fallback in several assertions

Gap:

- no generalized multi-strategy retry engine per product task

### 3. Cross-product linked testing

Status: not implemented.

Current state:

- no active IM -> Calendar -> IM linked runtime flow

### 4. Testcase auto generation

Status: not implemented.

Current state:

- no generator from Feishu docs, recordings, or product specs into structured
  testcases

### 5. Mixed locator strategy

Status: design placeholder only.

Current state:

- `VisionLocator` is active
- `AccessibilityLocator` / `HybridLocator` remain documented placeholders

### 6. Multi-turn orchestration

Status: partially implemented at the agent loop level, not as a dedicated
feature module.

Evidence:

- `AgentS3` adjusts next action from current screenshot
- reasoning effort and reflection escalate after failures

Gap:

- no explicit product-facing multi-round test orchestration feature or policy

### 7. Record and replay

Status: not implemented.

Current state:

- screenshots and action logs are recorded
- there is no replay engine that turns captured actions into reusable scripts

## Current Priority

The main app-level remaining repair item is `VC`.

Recommended order:

1. finish VC verifier/runtime repair
2. close one more stable live product path beyond IM
3. then decide whether to deepen `Calendar` or `Docs`
4. only after that, raise M4/M5 with batch evaluation and advanced features

## Historical Drift Notes

- Many `docs/implementation/*` files still contain historical references to
  deterministic workflows. They are useful as implementation records, not as
  current runtime contracts.
- `docs/implementation/feishu_agent_migration_remove_workflows_2026-05-06.md`
  is the cutover record for the current architecture.
- For session-level delivery details, see
  `docs/process/development_log_2026-05-06.md`.
