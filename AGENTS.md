# AGENTS

## Purpose

This repo is `Agent-S` secondary development for a Feishu GUI agent.
Current stable baseline is:

- `launcher.py` as the product shell
- `gui_agents/s3/` as the generic execution kernel
- `sop_executor.py` + `sops/` as the lightweight scripted path

Feishu-specific capability should be added as a new domain layer, not by continuously polluting `gui_agents/s3/`.
Current product direction is desktop GUI automation, not Feishu CLI/bot integration.

## Collaboration Rules

1. Use multiple coding agents only for modules with clear boundaries and disjoint ownership.
2. Every module change must follow `analysis -> manual plan -> coding -> review`.
3. Do not start coding a module until the manual plan is understood and confirmed by the human.
4. After coding, the same agent should run basic verification; a different agent should review when possible.
5. Do not mix architecture design, feature coding, and regression judgment in one uncontrolled pass.
6. Do not assume Feishu open-platform or bot capability exists unless the task explicitly targets that deployment mode.

## Ownership Boundaries

Prefer parallel work in these areas:

- `launcher.py`
- `sop_executor.py` and `sops/`
- new `gui_agents/feishu/pages/`, `anchors/`, `maintenance/`
- new `gui_agents/feishu/workflows/`, `verifiers/`, `router/`
- isolated provider work in `gui_agents/s3/core/`

Treat these as high-coupling modules and change them serially:

- `gui_agents/s3/agents/worker.py`
- `gui_agents/s3/agents/grounding.py`
- `gui_agents/s3/cli_app.py`
- `gui_agents/s3/memory/procedural_memory.py`

## Architecture Constraints

1. Keep `s3` as the generic GUI kernel.
2. Add Feishu domain logic under `gui_agents/feishu/`.
3. New Feishu work should be split by responsibility: `agents`, `detectors/pages`, `workflows`, `verifiers`, `router`, `memory/skills`.
4. Reuse `s2` knowledge retrieval selectively; do not reintroduce the full `s2` orchestration/DAG into the main path.
5. Do not treat memory as the primary solution. Build stable actions, state detection, verifier gates, and fallback first.
6. Any future Feishu open-platform or API adapter must stay optional and isolated from the GUI-first main path.

## Planning Standard

Before coding any module, write a short manual plan with:

- target files and ownership
- interface changes
- dependencies on `worker`, `grounding`, or `cli_app`
- test or regression path
- rollback/risk notes

If the change touches a high-coupling module, the plan must be reviewed before any edit.

## Delivery Standard

Each completed module should include:

- explicit module boundary
- success criteria or verifier
- fallback or failure handling
- minimal regression evidence
- short review summary with risks and follow-ups
