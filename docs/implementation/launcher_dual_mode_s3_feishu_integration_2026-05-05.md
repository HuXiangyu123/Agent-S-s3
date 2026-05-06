# Launcher Dual-Mode S3 / Feishu Integration (2026-05-05)

## Status

Superseded for runtime routing.

The current valid route is:

- `classic_s3`: `AgentS3 + OSWorldACI`
- `feishu_agent`: `AgentS3 + WindowsFeishuACI`

Do not use this document to reintroduce a `FeishuWorker` or deterministic workflow execution path behind `feishu_agent`. See `docs/implementation/s3_feishu_agentic_tools_refactor_2026-05-05.md` and `docs/implementation/s3_feishu_agent_track_d_artifacts_2026-05-06.md` for the active route.

## Goal

Integrate the new Feishu domain pipeline into the existing launcher + `s3` runtime chain without breaking the current stable path.

The launcher should let the user choose between:

- legacy stable `s3` execution
- new Feishu agent flow

## Current Understanding

The current launcher starts exactly one backend entry:

- `launcher.py`
  - starts `gui_agents/s3/cli_app.py`
  - waits for `Query:` to mark the subprocess ready
  - writes user instructions to stdin

`cli_app.py` currently always builds:

- `OSWorldACI`
- `AgentS3`
- the old `run_agent(...)` loop

That means the newly added `gui_agents/feishu/` modules are tested in isolation, but are not yet reachable from the launcher.

## Required Boundary

To keep compatibility, mode switching should happen in three layers:

### 1. Launcher Layer

Responsibilities:

- expose an execution-mode selector
- persist it into `config.json`
- pass it to `cli_app.py`

Non-responsibilities:

- parsing Feishu instructions
- choosing workflow
- executing Feishu-specific actions

### 2. CLI Entry Layer

Responsibilities:

- parse `--execution_mode`
- instantiate the correct grounding / execution branch
- keep the existing stdin/stdout `Query:` protocol unchanged

Non-responsibilities:

- launcher UI state
- Feishu workflow internals

### 3. Feishu Runtime Layer

Responsibilities:

- parse instruction -> `TestCase`
- plan -> `WorkflowPlan`
- build `send_message` workflow
- execute minimal runtime steps using existing Windows Feishu ACI actions
- verify step/case assertions

Non-responsibilities:

- free-form desktop planning like legacy `AgentS3`
- launcher process lifecycle

## Integration Strategy

### Legacy Mode

Keep the current path unchanged:

- `execution_mode = "classic_s3"`
- `OSWorldACI`
- `AgentS3`
- `run_agent(...)`

### New Mode

Add a new Feishu runtime path:

- `execution_mode = "feishu_agent"`
- prefer `WindowsFeishuACI` on Windows
- route each query to `AgentS3 + WindowsFeishuACI` (LLM-driven agent loop)

The first new-mode milestone only targets the already-frozen IM MVP:

- parse Chinese instruction
- support `send_message`
- use the Track A planner
- use the Track C workflow + verifier

## Execution Semantics For The New Mode

### Open Chat

Use a minimal pragmatic strategy:

1. focus Feishu
2. try to click the exact chat name via `feishu_click`
3. if needed later, extend to top-left global search fallback

This round should keep the implementation minimal and explicit. It does not need to solve all hidden-chat and off-screen-chat cases yet.

### Type Message

Use `feishu_type` with:

- exact placeholder or explicit input description when available
- overwrite enabled

### Send Message

Prefer pressing `Enter` after typing if the input is already focused, or click the visible send affordance if needed by the current worker implementation.

### Verification

Verifier logic must no longer be fixture-only.

It should support OCR-text fallback for real runtime, so assertions can pass when:

- chat title / placeholder text appears in OCR text
- drafted message text appears in OCR text
- sent message text appears in OCR text

## Target Files

### Docs

- `docs/implementation/launcher_dual_mode_s3_feishu_integration_2026-05-05.md`
- `docs/interfaces/feishu_gui_agent_interfaces.md`

### Launcher / CLI

- `launcher.py`
- `gui_agents/s3/cli_app.py`

### New Runtime Layer

- `gui_agents/feishu/agents/__init__.py`
- `gui_agents/feishu/agents/__init__.py`

### Existing Runtime Support

- `gui_agents/feishu/verifiers/assertion_verifier.py`
- `gui_agents/feishu/workflows/send_message_workflow.py`

### Tests

- `tests/test_agent_startup.py`
- `tests/feishu/verifiers/test_assertion_verifier.py`

## Manual Plan

### target files

- `launcher.py`
- `gui_agents/s3/cli_app.py`
- `gui_agents/feishu/agents/__init__.py`
- `gui_agents/feishu/verifiers/assertion_verifier.py`
- `gui_agents/feishu/workflows/send_message_workflow.py`
- `tests/test_agent_startup.py`
- `tests/feishu/verifiers/test_assertion_verifier.py`

### depends on

- existing `gui_agents/feishu/testcases/`
- existing `gui_agents/feishu/planner/`
- existing `gui_agents/feishu/workflows/`
- existing `gui_agents/feishu/verifiers/`
- existing `gui_agents/s3/agents/grounding_feishu.py`

### outputs

- launcher mode selector
- CLI execution-mode switch
- `S3RuntimeRecorder` integration into `cli_app.py`
- OCR-backed runtime verification fallback

### verification

- startup imports still pass
- `tests/feishu` still pass
- `black --check gui_agents tests`
- launcher can start both modes without breaking the `Query:` protocol

### risks / rollback

- Risk: `WindowsFeishuACI` may not be available or stable on non-Windows hosts.
  - Rollback: reject `feishu_agent` outside Windows and keep classic mode unchanged.
- Risk: OCR fallback may be noisy on real screenshots.
  - Rollback: keep fixture-backed assertions intact and use OCR only as runtime fallback.
- Risk: launcher config migration may break older `config.json`.
  - Rollback: default missing mode to `classic_s3`.
