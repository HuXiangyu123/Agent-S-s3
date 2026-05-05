# S3 Feishu Agentic Tools Refactor (2026-05-05)

## Goal

Refactor the current Feishu runtime path so that Feishu automation stays on top of the existing `s3` agent architecture instead of branching into a separate deterministic worker.

Target outcome:

- keep `AgentS3 -> Worker -> grounding agent` as the main execution chain
- keep legacy `classic_s3` behavior unchanged
- make `feishu_agent` mode an enhanced `s3` mode, not a second standalone agent
- provide state-aware "agentic tools" guidance so the model can choose a narrowed Feishu-specific tool subset with prior knowledge

## Current Problem

The repository currently has two different Feishu execution ideas:

1. `gui_agents/s3/agents/grounding_feishu.py`
   - already exposes Feishu-specific `@agent_action` tools such as:
     - `feishu_focus`
     - `feishu_click`
     - `feishu_type`
     - `feishu_doc_click`
     - `feishu_doc_type`
2. `gui_agents/feishu/agents/feishu_worker.py`
   - bypasses `AgentS3`
   - runs `parse_instruction -> workflow -> verifier -> runtime step executor`

This split is the wrong long-term direction for the current product goal.

The user requirement is not "build another Feishu agent from scratch".
It is "preserve the `s3` foundation and enhance it with prior-knowledge-driven tools".

## Required Boundary

### Keep

- `gui_agents/s3/agents/agent_s.py`
- `gui_agents/s3/agents/worker.py`
- `gui_agents/s3/agents/grounding.py`
- `gui_agents/s3/agents/grounding_feishu.py`
- the existing `@agent_action` exposure mechanism

### Add

- a Feishu tool contract / registry / router layer under `gui_agents/feishu/`
- dynamic per-step Feishu guidance injected into the worker prompt
- a small Feishu context builder that turns current instruction + observation into routing hints

### De-emphasize

- `gui_agents/feishu/agents/feishu_worker.py` as the main runtime path

It may remain temporarily for compatibility imports or fallback reference, but new runtime capability should not keep growing there.

## Design

### 1. Tool Registry

Add a small registry in `gui_agents/feishu/tooling/` that defines:

- tool id
- backing agent action name
- supported product / page types
- when the tool is preferred
- when it should be avoided
- parameter guidance / examples

This is not a second action system.
It is a Feishu-side knowledge layer over the existing `@agent_action` methods.

### 2. Tool Router

The router consumes:

- user instruction
- current screenshot observation
- detected `FeishuState`
- page descriptor / page type

The router returns a structured bundle such as:

- `enabled_tools`
- `preferred_tools`
- `discouraged_tools`
- `hints`
- `next_step_focus`
- `rationale`

The router does not execute actions.
It only shapes model choice.

### 3. Worker Prompt Injection

`Worker.reset()` currently builds one static system prompt from `PROCEDURAL_MEMORY.construct_simple_worker_procedural_memory(...)`.

That stays as the base prompt.

For each step in `generate_next_action(...)`, if the grounding agent supports Feishu routing, append an additional dynamic guidance block into the user-turn message. Example content:

- current detected Feishu page
- current likely state
- recommended tools to use first
- tools to avoid unless the first-line tools fail
- exact text-anchor hints or parameter suggestions

This gives the model function-call-like prior knowledge while keeping the underlying `s3` planning loop intact.

### 4. Feishu-Aware Grounding Agent Hook

The clean ownership point is the grounding agent instance, not the launcher.

`WindowsFeishuACI` should expose a lightweight hook such as:

- `build_dynamic_guidance(instruction: str, obs: dict) -> str`

This hook can internally call the Feishu router and return a prompt-ready guidance block.

That keeps Feishu business logic in `gui_agents/feishu/`, while `Worker` only knows how to append optional dynamic guidance when the grounding agent provides it.

### 5. Execution Mode Semantics

After refactor:

- `classic_s3`
  - unchanged
  - `OSWorldACI`
  - generic desktop behavior
- `feishu_agent`
  - still uses `AgentS3`
  - uses `WindowsFeishuACI`
  - uses dynamic Feishu tool routing / prior knowledge

So `feishu_agent` becomes "S3 enhanced for Feishu", not "standalone workflow executor".

## First Milestone Scope

This round only needs enough routing to improve the current Feishu IM path.

In scope:

- IM chat main page
- IM in-chat search panel
- Feishu shell/global search page
- primary tools:
  - `feishu_focus`
  - `feishu_click`
  - `feishu_type`
  - `hotkey`
  - generic `click` / `type` only as fallback or browser-content path

Out of scope:

- replacing all planning with workflow plans
- deleting old `feishu_worker`
- non-Feishu app routing
- large browser document flows redesign

## Target Files

### Docs

- `docs/implementation/s3_feishu_agentic_tools_refactor_2026-05-05.md`
- `docs/interfaces/interface_compatibility.md`

### Feishu Tooling

- `gui_agents/feishu/tooling/__init__.py`
- `gui_agents/feishu/tooling/tool_contracts.py`
- `gui_agents/feishu/tooling/tool_registry.py`
- `gui_agents/feishu/tooling/tool_router.py`

### S3 Integration

- `gui_agents/s3/agents/worker.py`
- `gui_agents/s3/agents/grounding_feishu.py`
- `gui_agents/s3/cli_app.py`

### Tests

- `tests/test_agent_startup.py`
- `tests/feishu/tooling/test_tool_router.py`

## Manual Plan

### target files

- `gui_agents/feishu/tooling/__init__.py`
- `gui_agents/feishu/tooling/tool_contracts.py`
- `gui_agents/feishu/tooling/tool_registry.py`
- `gui_agents/feishu/tooling/tool_router.py`
- `gui_agents/s3/agents/worker.py`
- `gui_agents/s3/agents/grounding_feishu.py`
- `gui_agents/s3/cli_app.py`
- `docs/interfaces/interface_compatibility.md`
- `tests/test_agent_startup.py`
- `tests/feishu/tooling/test_tool_router.py`

### depends on

- `gui_agents/feishu/detectors/im_state_detector.py`
- `gui_agents/feishu/pages/registry.py`
- `gui_agents/s3/memory/procedural_memory.py`
- `gui_agents/s3/agents/grounding.py`
- `gui_agents/s3/agents/agent_s.py`

### outputs

- state-aware Feishu tool registry
- instruction + observation -> guidance router
- worker-side dynamic prompt injection
- `feishu_agent` mode routed back onto `AgentS3`

### verification

- `python -m unittest tests.test_agent_startup -v`
- `python -m unittest discover -s tests/feishu -t . -v`
- `python -m black --check launcher.py gui_agents tests`

### risks / rollback

1. Risk: dynamic guidance is too weak and the model still picks generic actions too often.
   Rollback: keep classic mode unchanged and strengthen only the Feishu guidance text without touching action contracts.
2. Risk: router misclassifies some screenshots because detection is still OCR/metadata-light.
   Rollback: fall back to conservative generic Feishu guidance instead of state-specific guidance.
3. Risk: `feishu_agent` mode behavior changes abruptly for users relying on the deterministic runtime.
   Rollback: keep `feishu_worker` importable and reintroduce a compatibility switch if needed, but do not block the main refactor on that.

## Success Criteria

The refactor is correct when:

- `feishu_agent` no longer uses the standalone deterministic worker as its main path
- `Worker` can consume dynamic Feishu guidance without affecting non-Feishu modes
- the guidance clearly narrows recommended tools per page/state
- current tests still pass and the legacy `classic_s3` path remains intact
