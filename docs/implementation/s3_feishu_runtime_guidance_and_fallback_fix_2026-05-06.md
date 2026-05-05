# S3 Feishu Runtime Guidance And Fallback Fix

Date: 2026-05-06
Owner: Codex
Scope: `gui_agents/s3/agents/worker.py`, `gui_agents/feishu/tooling/tool_router.py`, `gui_agents/feishu/tooling/tool_registry.py`, `gui_agents/feishu/detectors/im_state_detector.py`, `gui_agents/s3/agents/grounding_feishu.py`, `gui_agents/s3/agents/_feishu_exec.py`, related tests

## Context

Current Feishu runtime behavior still has three structural problems:

1. Dynamic tool guidance is appended to the worker's per-step user message before the model reasons over the screenshot.
2. Runtime guidance text is still treated as a steering mechanism at step start, even when no tool has failed yet.
3. `feishu_click(...)` is UIA text-only, so icon-only controls such as emoji cannot be completed reliably through that tool alone.

These problems break the intended architecture: keep S3 agent reasoning as the primary path, and use Feishu prior knowledge only as acceleration or fallback.

## Module Responsibilities

- `worker.py`
  - Owns per-step prompt assembly.
  - Must not front-load hard tool-routing instructions that bypass screenshot reasoning.
- `tool_router.py`
  - Produces soft runtime recommendations based on instruction plus detected state.
  - Must not overstate certainty or force tool choice when the screenshot has not yet been reasoned over.
- `grounding_feishu.py`
  - Exposes Feishu-specific runtime tools.
  - Must preserve S3 agent flow while making Feishu helpers reliable for known desktop surfaces.
- `_feishu_exec.py`
  - Builds exec-time UIA helper code.
  - Must support safe fallback signaling for host-side composed actions.

## Boundaries

- Do not replace the S3 worker/planner loop.
- Do not turn Feishu runtime into a separate agent stack.
- Do not make `feishu_click(...)` a pure visual-grounding alias; it remains UIA-first.
- Do not print pre-step guidance blocks in launcher output.

## Planned Changes

### 1. Worker guidance injection

- Remove per-step injection of dynamic guidance into the generator user message.
- Keep screenshot reasoning as the first-class path on every step.
- Move Feishu IM prior-tool strategy into the worker system prompt as soft, static guidance instead of runtime coercion.

### 2. Router guidance wording

- Replace "source of truth" phrasing with soft recommendation language.
- Keep icon-only controls explicitly routed toward grounded `click(...)`.
- Keep composer-first sequencing when the task asks for both typing and emoji.
- Repair current mojibake Chinese literals in the router and OCR-state detector.

### 3. `feishu_click(...)` fallback behavior

- Keep UIA text matching as the first attempt.
- When the target is described with relational/icon-only language and UIA misses, fall back to host-side grounded click using the current screenshot.
- Emit trace only from real tool execution paths, not from pre-step guidance construction.

## Target Files

- `gui_agents/s3/agents/worker.py`
- `gui_agents/feishu/tooling/tool_router.py`
- `gui_agents/feishu/tooling/tool_registry.py`
- `gui_agents/feishu/detectors/im_state_detector.py`
- `gui_agents/s3/agents/grounding_feishu.py`
- `gui_agents/s3/agents/_feishu_exec.py`
- `tests/feishu/tooling/test_tool_router.py`
- new/updated worker and fallback tests under `tests/feishu/tooling/`
- runtime OCR detector tests under `tests/feishu/detectors/`

## Verification

- Worker-level test: first step does not inject dynamic guidance into the user message.
- Worker-level test: Feishu IM static prior-tool strategy is present in system prompt.
- Tool test: `feishu_click(...)` returns composed code that includes UIA attempt plus grounded fallback when applicable.
- Router tests: emoji + draft routes to grounded click; compose+emoji routes to composer first.
- Detector test: runtime OCR text can classify `chat_main` and `chat_search_panel` without fixture metadata.
- Existing related suites:
  - `python -m unittest discover -s tests/feishu -t . -v`
  - `python -m unittest tests.test_agent_startup -v`
  - `python -m black --check launcher.py gui_agents tests`

## Risks

- Too little guidance after removal could reduce success for genuinely ambiguous pages.
- Automatic fallback inside `feishu_click(...)` must stay narrow enough to avoid hiding real UIA mismatches for plain text controls.
- Router string repairs must not accidentally change existing detector semantics.

## Rollback

- Revert worker guidance gating independently if failure recovery becomes too weak.
- Revert `feishu_click(...)` fallback independently if it introduces false positive clicks.
