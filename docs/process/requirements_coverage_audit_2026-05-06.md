# Requirements Coverage Audit

Date: 2026-05-06

This audit checks the current repository against `docs/项目需求.md`. It uses
the active architecture only:

```text
feishu_agent = AgentS3 + WindowsFeishuACI + Feishu semantic priors
```

Deterministic product workflows, `FeishuWorker`, and static screenshot
coordinates are treated as removed architecture, not as implementation gaps.

## Audit Method

Coverage is graded by evidence level:

| Level | Meaning |
| --- | --- |
| Semantic | Page descriptors, detectors, parser/router guidance, or verifier contracts express the scenario. |
| Unit Tested | The behavior has repository tests or fixture-backed assertions. |
| Runtime Artifact | The active route can emit `summary.json`, `report.md`, `actions.jsonl`, screenshots, or aggregate evaluation reports. |
| Live E2E | A real Feishu desktop run has produced usable execution evidence. |

Status marks:

- `✅`: implemented with unit or runtime evidence.
- `⚠️`: partially implemented, usually semantic/tooling exists but live evidence or verifier depth is missing.
- `❌`: not implemented in the current active route.

## Executive Summary

Current project state:

- Core CUA architecture is in place across perception, planning, execution,
  verification, and reporting.
- The Feishu route has been migrated away from fixed workflows to
  `AgentS3 + WindowsFeishuACI`.
- Static page descriptors and fixture metadata are semantic-only. They must not
  carry `relative_bounds`, `bbox`, `confidence`, image dimensions, or fixed
  workflow fields.
- Five Feishu products have semantic coverage: IM, Docs, Calendar, Base, VC.
  Mail is deferred.
- IM, Docs, Base, and VC have verifier coverage. Calendar still needs stronger
  verifier branches.
- Batch evaluation has an initial implementation through
  `evaluation_aggregator.py` and `scripts/build_feishu_eval_report.py`.
- The largest remaining acceptance gap is live E2E evidence, not domain
  knowledge representation.

## Part 1: Must-Have Requirements

### 1.1 System Architecture

| Module | Current implementation | Status |
| --- | --- | --- |
| Visual perception | `WindowsFeishuACI` screenshot capture, OCR, VLM coordinate generation, Feishu page detectors | ✅ |
| Planning and decision | AgentS3 `Worker` LLM loop with per-step reasoning and code extraction | ✅ |
| Execution | `WindowsFeishuACI`, `_feishu_exec.py`, UIA click/type helpers, PyAutoGUI hotkeys, semantic Feishu helper tools | ✅ |
| State verification | `AssertionVerifier`, product detectors for IM/Docs/Calendar/Base/VC, OCR fallback in key branches | ✅ |
| Evaluation report | `S3RuntimeRecorder`, `ReportBuilder`, `ArtifactManager`, `evaluation_aggregator.py` | ✅ |

Result: 5/5 architecture modules are present. Some modules are stronger at
unit-test level than at live desktop E2E level.

### 1.2 Basic GUI Operations

| Operation | Support | Evidence |
| --- | --- | --- |
| Single click | ✅ | `build_win32_click_code()`, `build_feishu_uia_click_code()`, `agent.click(...)` |
| Double click | ✅ | `num_clicks=2` in click builder tests |
| Right click | ✅ | `button_type="right"` Win32 flags |
| Drag | ⚠️ | Generic `OSWorldACI.drag_and_drop()` exists, but Feishu route currently discourages or skips it for stability |
| Scroll | ✅ | Generic `OSWorldACI.scroll()` and tool registry exposure |
| Text input | ✅ | `feishu_type`, `feishu_type_message`, `feishu_doc_type`, generic grounded `type` |
| Hotkey | ✅ | `hotkey` tool and PyAutoGUI hotkey execution |
| Multi-step chaining | ✅ | AgentS3 loop observes, acts, verifies, and continues |

Result: 7/8 directly supported in the Feishu route. Drag exists at the generic
Agent-S layer but is not yet a stable Feishu acceptance capability.

### 1.3 Product Coverage Matrix

| Product | Scenario | Semantic | Tool route | Verifier | Unit tests | Live E2E |
| --- | --- | --- | --- | --- | --- | --- |
| IM | Send text message | ✅ | ✅ | ✅ | ✅ | ⚠️ limited path |
| IM | Search message/history | ✅ | ✅ | ❌ | ✅ detector/router | ❌ |
| IM | Emoji reply | ⚠️ | ✅ | ❌ | ✅ router | ❌ |
| IM | Image/file message | ❌ | ❌ | ❌ | ❌ | ❌ |
| IM | Group creation / @ mention | ❌ | ❌ | ❌ | ❌ | ❌ |
| Docs | Create document | ✅ | ✅ | ✅ | ✅ | ❌ |
| Docs | Edit title/body | ✅ | ✅ | ✅ | ✅ | ❌ |
| Docs | Share document | ⚠️ | ⚠️ `feishu_doc_click` | ❌ | ✅ helper smoke | ❌ |
| Docs | Insert heading/list | ❌ | ❌ | ❌ | ❌ | ❌ |
| Calendar | Create event | ✅ | ✅ agent-guided | ❌ | ✅ detector/router | ❌ |
| Calendar | Invite attendee | ⚠️ semantic fixture only | ⚠️ guidance only | ❌ | ✅ detector | ❌ |
| Calendar | Modify time / busy-free | ❌ | ❌ | ❌ | ❌ | ❌ |
| Base | Create table | ✅ | ✅ agent-guided | ✅ | ✅ | ❌ |
| Base | Add field / enter data / switch view | ❌ | ❌ | ❌ | ❌ | ❌ |
| VC | Start meeting | ✅ | ✅ VC helpers | ✅ | ✅ | ❌ |
| VC | Join meeting | ✅ | ✅ VC helpers | ✅ | ✅ | ❌ |
| VC | Invite/share meeting | ✅ | ✅ VC helpers | ✅ invite dialog | ✅ | ❌ |
| VC | Camera/microphone toggles | ⚠️ detector hints | ❌ | ❌ | ❌ | ❌ |
| Mail | All scenarios | ❌ | ❌ | ❌ | ❌ | ❌ |

Result: the "at least 2 sub-products" requirement is satisfied at semantic and
unit-test levels by IM and Docs, with Base and VC also partially complete. Live
E2E coverage still needs explicit run evidence.

### 1.4 Natural Language Driven Testing

| Example | Parser | Route | Verify | Status |
| --- | --- | --- | --- | --- |
| Create a document named "项目周报" and enter "2026年Q2项目进展" | ✅ Docs structured testcase | ✅ Docs router | ✅ title/body/editor assertions | Complete at unit level |
| Open Calendar, create tomorrow 2 PM meeting, invite 张三 | ❌ Calendar parser entry missing | ✅ Calendar tool guidance | ❌ Calendar verifier missing | Broken before full acceptance |
| Search "测试群" in IM, send "Hello World", confirm sent | ✅ IM parser | ✅ IM router/helpers | ✅ `message_sent` | Complete at unit level |
| Start a video meeting and verify meeting active | ✅ VC semantic guidance testcase | ✅ VC helper route | ✅ VC assertions | Complete at unit level |
| Create a Base table | ✅ Base semantic guidance testcase | ✅ Base router | ✅ Base ready assertions | Complete at semantic/unit level |

Calendar remains the main official-example gap.

### 1.5 Milestone Coverage

| Milestone | Requirement target | Current status | Judgment |
| --- | --- | --- | --- |
| M1 | 5 single-step operations | Click/type/hotkey/scroll/wait/open plus Feishu helpers are present | ✅ |
| M2 | 1 product, 3 E2E flows | IM has the strongest path, but 3 live-validated flows are not yet proven | ⚠️ |
| M3 | 3 products, 2+ runnable cases each | 5 products have semantic coverage; live runnable matrix is incomplete | ⚠️ |
| M4 | Success rate, duration, step statistics | Per-run artifacts and batch aggregation exist; dashboard/trend runner missing | ⚠️ |
| M5 | 1-2 advanced features | RuntimeContext fields and foundations exist; advanced features need final runtime wiring | ⚠️ |

## Part 2: Advanced Requirements

| Capability | Current foundation | Remaining gap | Status |
| --- | --- | --- | --- |
| Exception handling | `modal_type`, detector dialog states, structured failure types | Unified anomaly keyword model and `recovery_hint` injection | ⚠️ |
| Cross-product linked tests | None in active acceptance route | IM -> Calendar -> IM or Docs -> IM linked live flow | ❌ |
| Self-healing execution | Worker reflection on failure, plan-failure detection, reasoning escalation, grounded fallback | Recovery prompt injection and `recovery_attempts` runtime updates | ⚠️ |
| Testcase auto generation | Parser/schema foundation only | Generator from docs, recordings, or product specs | ❌ |
| Mixed locator strategy | `VisionLocator` exists but is runtime-region only; static bounds removed | Accessibility/DOM/hybrid locator implementation | ❌ |
| Multi-turn orchestration | AgentS3 loop, dynamic tool guidance, `FeishuToolRecommendation` state summary | Concise per-turn guidance block and action history summary injection | ⚠️ |
| Record/replay | `S3RuntimeRecorder`, per-run reports, actions, screenshots | `semantic_trace.json` and `replay_draft.md` without coordinate scripts | ⚠️ |

Additional progress: the shared `RuntimeContext` already freezes optional
advanced fields: `recovery_attempts`, `anomaly_events`, and `semantic_steps`.

## Part 3: Architecture Guardrails

| Guardrail | Current status | Evidence |
| --- | --- | --- |
| Active runtime is `feishu_agent` | ✅ | `AgentS3 + WindowsFeishuACI` route in `cli_app.py` |
| No `FeishuWorker` runtime | ✅ | `scripts/check_constraints.py` |
| No product `*_workflow.py` stage machines | ✅ | `scripts/check_constraints.py` |
| Static metadata is semantic-only | ✅ | page/fixture constraints reject coordinate and workflow fields |
| Locator does not read static `relative_bounds` | ✅ | `VisionLocator` uses runtime regions only |
| Reports use intent/params, not workflow/workflow_params | ✅ | `RuntimeContext`, `ReportBuilder`, `S3RuntimeRecorder` |
| CI parity entry exists | ✅ | `python scripts/run_ci_checks.py` |

These guardrails are part of the current acceptance criteria. A future change
that reintroduces deterministic product workflows should be treated as an
architecture regression unless the source-of-truth docs are explicitly changed.

## Part 4: Capability Overview

```text
                    Semantic   Router    Verifier   Unit Test   Live E2E
IM send_message       yes       yes       yes        yes         partial
IM search             yes       yes       no         yes         no
IM emoji              partial   yes       no         yes         no
Docs create/edit      yes       yes       yes        yes         no
Docs share            partial   partial   no         partial     no
Calendar create       yes       yes       no         partial     no
Calendar invite       partial   partial   no         partial     no
Base create           yes       yes       yes        yes         no
VC start              yes       yes       yes        yes         no
VC join               yes       yes       yes        yes         no
VC invite             yes       yes       partial    yes         no
```

Main conclusion: the repository now has broad product-domain knowledge and
unit-level guardrails. It still needs live Feishu desktop evidence to prove the
agentic route is stable under real UI timing and account state.

## Part 5: Gap Priority

| Priority | Gap | Why it matters |
| --- | --- | --- |
| P0 | Calendar parser + Calendar verifier | Closes the official Calendar natural-language example and improves M3 evidence |
| P0 | Live E2E evidence pack | Converts semantic/unit coverage into competition-grade proof |
| P1 | IM 3-flow acceptance pack | M2 requires 1 product with 3 end-to-end flows |
| P1 | Record/replay semantic trace | Low-risk advanced feature building on existing recorder artifacts |
| P1 | Exception recovery hints | Low-risk advanced feature building on detectors and failure types |
| P2 | Docs share verifier and richer Docs formatting actions | Deepens Docs beyond create/edit |
| P2 | VC camera/microphone toggles | Completes VC suggested scenario coverage |
| P3 | Mail product domain | Useful later, but outside current 5-product semantic scope |

## Part 6: Verification Evidence

Recent local evidence from 2026-05-06:

| Command | Result |
| --- | --- |
| `python -m unittest tests.test_agent_startup -v` | Passed |
| `python -m unittest discover tests/feishu -v` | Passed in prior cleanup pass |
| `python scripts/run_ci_checks.py` | Passed in prior cleanup pass |
| `python scripts/check_constraints.py` | Passed in prior cleanup pass |
| `python -m unittest tests.feishu.reports.test_evaluation_aggregator tests.feishu.runtime.test_runtime_context_contract -v` | Passed |

Session startup evidence currently shows 170 Feishu-related startup tests
passing through `tests.test_agent_startup`.

## Part 7: How To Use This Audit

- Use this document to decide what to implement next.
- Use `docs/process/project_state.md` for the current runtime architecture.
- Use `docs/implementation/README.md` to distinguish active implementation
  records from historical workflow-era records.
- Do not use old `Track A/B/C workflow` records as permission to restore
  deterministic product workflows.
