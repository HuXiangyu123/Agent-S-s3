# Development Log 2026-05-06

Last updated: 2026-05-06

## 1. Scope

This log records the current Feishu GUI Agent delivery state in software-engineering form:

- objective and active architecture
- major implementation increments already landed
- requirement-to-implementation mapping
- automated evaluation and advanced-feature status
- open issues, risks, and next actions

This file is a process log, not a product contract. Runtime source of truth remains:

- `docs/项目需求.md`
- `docs/feishu_gui_agent_master_plan.md`
- `docs/product/feishu_gui_agent_prd.md`
- `docs/spec/feishu_gui_agent_technical_spec.md`
- `docs/interfaces/feishu_gui_agent_interfaces.md`

## 2. Active Architecture Decision

### Decision

Current Feishu delivery is based on `feishu_agent`, not on a deterministic workflow engine.

### Effective runtime

```text
user instruction
  -> AgentS3 LLM loop
  -> WindowsFeishuACI
  -> Feishu semantic priors:
     testcases / tooling / pages / detectors / verifiers / reports
```

### Enforced constraints

- Keep `classic_s3` intact as the original general route.
- Keep `feishu_agent` as `AgentS3 + WindowsFeishuACI`.
- Do not restore `FeishuWorker` or product `*_workflow.py` runtime controllers.
- Do not route product execution through `planner -> workflow.steps()`.
- New screenshot-derived metadata must remain semantic only.
- New product capability work must be added to `feishu_agent`, not to a second non-LLM executor.

### Rationale

- The user requirement is a GUI-first Feishu desktop agent, not an API-first or fixed-playbook executor.
- The S3 agent loop already provides planning, reflection, and action generation.
- Product-specific Track ABCD modules are more valuable as semantic priors and tool guidance than as a separate executor.

## 3. Delivered Increments

### 2026-05-05: Track A foundation

Delivered:

- Feishu shared contracts
- natural-language testcase parsing baseline
- scenario schema normalization and validation
- IM-focused minimal testcase path for `send_message`

Outcome:

- Feishu tasks can be normalized into structured task facts instead of staying as raw prompts.
- Parser/schema responsibilities are separated from runtime action generation.

Evidence:

- `gui_agents/feishu/contracts.py`
- `gui_agents/feishu/testcases/nl_parser.py`
- `gui_agents/feishu/testcases/scenario_schema.py`
- `tests/feishu/testcases/`
- `docs/implementation/track_a_foundation_2026-05-05.md`

### 2026-05-05 to 2026-05-06: Track B semantic page and detector layer

Delivered:

- IM page descriptors and detector strengthening
- semantic page registries and detectors for `Docs`, `Calendar`, `Base`, and `VC`
- Feishu tool routing with state-aware hints
- UIA-first helpers plus grounded fallback for icon-only or browser-like targets

Outcome:

- Feishu runtime has product-aware page-state understanding instead of purely generic grounding.
- IM remains the strongest runtime slice.
- Other products now have semantic coverage, though not all have stable live runtime validation.

Evidence:

- `gui_agents/feishu/pages/`
- `gui_agents/feishu/detectors/`
- `gui_agents/feishu/tooling/tool_router.py`
- `tests/feishu/pages/`
- `tests/feishu/detectors/`
- `tests/feishu/tooling/test_tool_router.py`

### 2026-05-06: Runtime cutover away from deterministic workflows

Delivered:

- removal of product workflow runtime controllers
- startup/test expectations migrated from workflow runtime to agentic runtime
- documentation updated to mark workflow modules as historical, not active runtime

Outcome:

- repository runtime now aligns with the engineering rule that feature development must happen on `feishu_agent`
- Track ABCD remains as semantic support layers instead of a second executor

Evidence:

- `docs/implementation/feishu_agent_migration_remove_workflows_2026-05-06.md`
- deleted `gui_agents/feishu/agents/feishu_worker.py`
- deleted `gui_agents/feishu/workflows/*`
- updated `tests/test_agent_startup.py`

### 2026-05-06: Track D artifacts and maintenance

Delivered:

- runtime recorder
- artifact manager
- report builder
- per-run screenshots, action log, summary, and markdown report output

Outcome:

- every Feishu run can now leave reviewable execution artifacts
- the project moved from "only able to act" toward "able to audit and review"

Evidence:

- `gui_agents/feishu/reports/s3_runtime_recorder.py`
- `gui_agents/feishu/reports/report_builder.py`
- `gui_agents/feishu/maintenance/artifact_manager.py`
- `tests/feishu/reports/`
- `tests/feishu/maintenance/`
- `docs/implementation/track_d_reports_and_maintenance_2026-05-06.md`
- `docs/implementation/s3_feishu_agent_track_d_artifacts_2026-05-06.md`

### 2026-05-06: VC agentic runtime stabilization

Delivered:

- `VC`-specific helper actions for start/join/invite flows
- invite-popover semantic detection for active-meeting state
- `VC` tool-router recommendations upgraded from generic click/type toward
  product-specific helpers
- worker prompt guidance for `VC` tasks

Outcome:

- `VC` runtime now has a dedicated agentic tool layer comparable in spirit to
  the earlier IM helper set
- the active route stays inside `feishu_agent`, without restoring deterministic
  workflows
- invite flow now has an explicit semantic handoff from toolbar -> popover ->
  dialog

Evidence:

- `gui_agents/s3/agents/grounding_feishu.py`
- `gui_agents/feishu/tooling/tool_registry.py`
- `gui_agents/feishu/tooling/tool_router.py`
- `gui_agents/feishu/detectors/vc_state_detector.py`
- `tests/feishu/runtime/test_feishu_agentic_helpers.py`
- `tests/feishu/detectors/test_vc_state_detector.py`
- `tests/feishu/tooling/test_tool_router.py`
- `docs/implementation/vc_agentic_tools_runtime_stabilization_2026-05-06.md`

### 2026-05-06: CI parity and startup gate hardening

Delivered:

- local CI parity script
- architecture constraints script
- launcher env routing checks
- startup import/runtime gate checks

Outcome:

- local verification is closer to GitHub checks
- regressions around startup wiring, env routing, and architecture drift are more likely to be caught before push

Evidence:

- `scripts/run_ci_checks.py`
- `scripts/check_constraints.py`
- `tests/test_agent_startup.py`
- `tests/test_launcher_env_config.py`
- `docs/implementation/ci_parity_checks_2026-05-06.md`

## 4. Requirement Coverage Snapshot

This section checks the current repository against `docs/项目需求.md`.

### Must-have capabilities

| Requirement | Current status | Notes |
| --- | --- | --- |
| Visual perception | Largely implemented | Semantic page descriptors and detectors exist for `IM`, `Docs`, `Calendar`, `Base`, `VC`. |
| Semantic understanding | Partially implemented | IM instruction parsing is strongest; other products rely more on semantic guidance than mature task decomposition. |
| Autonomous operation | Partially implemented | IM has Feishu-specific click/type helpers and grounded fallback; other products are not yet equally stable live paths. |
| State verification | Partially implemented | `IM`, `Docs`, `Base` are better covered; `Calendar` and `VC` still lack stronger dedicated verifier branches. |
| Evaluation reports | Partially to substantially implemented | Per-run artifacts exist, but batch regression analytics and dashboards are still missing. |

### Milestone view

| Milestone | Target | Current status |
| --- | --- | --- |
| `M0` | agent startup baseline | Done |
| `M1` | 5 single-step operations | Mostly done |
| `M2` | 1 product with 3 end-to-end flows | Partially done |
| `M3` | 2+ stable products | Partially done |
| `M4` | structured evaluation system | Partially done |
| `M5` | 1-2 advanced features | Partially done |

## 5. Product Coverage Snapshot

### IM

Status: current mainline and strongest slice.

Implemented:

- page descriptors
- detectors
- composer/send/search/emoji-oriented tool routing
- Feishu-specific input and click helpers
- verifier coverage
- runtime artifact capture

Still missing:

- broader IM task matrix beyond the current dominant message-send path
- more live-validated coverage for `@` mention, file/image send, emoji full completion

### Docs

Status: semantic/domain slice present, but not yet as runtime-complete as IM.

Implemented:

- pages and detectors
- title/body-related verification coverage
- browser-aware helper path

Still missing:

- stronger product-specific tool-routing depth
- stable live end-to-end validation on the active route

### Calendar

Status: semantic slice present, live runtime still shallow.

Implemented:

- pages and detector
- semantic-only fixture constraints
- tool-router guidance

Still missing:

- stronger verifier coverage
- stable live create-event path

### Base

Status: semantic slice present after cleanup.

Implemented:

- pages and detector
- semantic-only metadata discipline
- tool guidance
- explicit rejection of fixed-coordinate/fixed-workflow path

Still missing:

- validated live runtime path
- stronger evaluation around Base tasks

### VC

Status: still in progress and the main remaining app-level repair item.

Implemented:

- pages and detector
- tool-router guidance
- semantic-only fixture constraints
- dedicated verifier branches and final-state reporting
- specialized start/join/invite helper tools on the active `feishu_agent` route
- invite-popover semantic detection

Still missing:

- stable live runtime validation for start/join/invite flows

## 6. Automated Evaluation Status

### Already delivered

- startup gate: `tests.test_agent_startup`
- launcher env routing checks: `tests.test_launcher_env_config`
- local/GitHub parity entry: `scripts/run_ci_checks.py`
- architecture guardrails: `scripts/check_constraints.py`
- passive run recorder: `S3RuntimeRecorder`
- artifact persistence: `ArtifactManager`
- human-readable and machine-readable reports: `ReportBuilder`

### Current artifact outputs

Per-run output under `artifacts/test_runs/<run_id>/`:

- `summary.json`
- `report.md`
- `actions.jsonl`
- `screenshots/`

### Missing for full M4 closure

- batch regression runner over multiple testcases
- aggregate success-rate reporting across runs
- trend comparison between runs
- dashboard or visualization layer

## 7. Advanced Feature Status

### Exception handling

Status: partially implemented.

Evidence:

- page detectors preserve modal facts such as `modal_type`
- tool routing includes popup/dialog-aware guidance
- runtime failure can be categorized into recognition/location/action/verification style outcomes

Gap:

- no unified abnormal-scene recovery matrix across products

### Self-healing execution

Status: partially implemented.

Evidence:

- `Worker` supports `reflection_mode=on_failure`
- runtime can detect when the previous action had no visible effect
- Feishu-specific helpers can redirect some actions toward grounded fallback

Gap:

- no generalized product-level retry strategy library

### Cross-product linked testing

Status: not implemented.

Gap:

- no active IM -> Calendar -> IM or similar linked end-to-end runtime

### Testcase auto generation

Status: not implemented.

Gap:

- no generator from product docs, screenshots, or recordings into structured testcase suites

### Mixed locator strategy

Status: design placeholder only.

Evidence:

- visual grounding is the active path
- accessibility/hybrid locator concepts remain architectural placeholders

### Multi-turn orchestration

Status: partially implemented at the agent-loop level.

Evidence:

- `AgentS3` iterates on screenshot observations step by step
- reflection escalates after failures

Gap:

- no separate product-level orchestration policy layer

### Record and replay

Status: not implemented.

Evidence:

- actions and screenshots are recorded

Gap:

- no replay engine that converts captured traces into reusable scripts

## 8. Verification Evidence

Relevant automated checks already present in the repository:

- `tests.test_agent_startup`
- `tests.test_launcher_env_config`
- `tests/feishu/reports/*`
- `tests/feishu/maintenance/*`
- `tests/feishu/detectors/*`
- `tests/feishu/pages/*`
- `tests/feishu/tooling/test_tool_router.py`
- `scripts/run_ci_checks.py`

For this document update itself:

- only process documentation was added/updated
- no runtime code path was changed in this pass

## 9. Open Issues

1. `VC` is still the main remaining app-level repair area.
2. IM is the only comparatively strong live route; the second stable product path is not yet closed.
3. M4 is only partially complete because evaluation is per-run, not yet batch/regression oriented.
4. M5 is only partially complete because advanced features are fragmented and not yet product-complete.
5. Several historical docs still contain old deterministic-workflow wording and should be treated as implementation history, not current runtime contract.

## 10. Next Actions

Recommended next order:

1. finish `VC` runtime and verifier repair
2. close one additional stable live product path beyond `IM`
3. consolidate product-level verification depth for `Calendar` or `Docs`
4. add regression-runner and aggregate evaluation to push `M4`
5. only after runtime stability improves, deepen `M5` advanced capabilities
