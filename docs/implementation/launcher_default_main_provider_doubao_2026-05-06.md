# Launcher Default Main Provider Doubao

Date: 2026-05-06

## Module Analysis

The launcher already defines `DEFAULT_CONFIG["main_provider"]` as `volcano`
(Doubao). However, `_apply_env_defaults()` can switch the main provider to
`openai_gpt` when an older config has no explicit main-provider routing and the
OpenAI/GPT environment values are present.

That behavior makes GPT win by environment availability rather than by explicit
user choice. The desired behavior is:

- default main provider: Doubao / `volcano`
- explicit saved `main_provider`: preserved
- legacy flat GPT config: still migrates as a user-configured legacy choice
- OpenAI env values: fill the GPT provider fields, but do not make GPT active by default

## Boundary

In scope:

- Launcher config default and env-default behavior.
- Launcher tests for default provider selection.

Out of scope:

- No runtime model invocation changes.
- No Feishu agent route changes.
- No grounding provider default changes.

## Target Files

- `launcher.py`
- `tests/test_launcher_env_config.py`

## Manual Plan

- Owner: Codex
- Depends on: existing launcher provider config contract.
- Outputs:
  - Doubao remains selected by default even when GPT env variables exist.
  - Explicit GPT selection remains supported.
- Verification:
  - launcher env/config tests
  - startup gate
  - architecture constraint check
- Risks / rollback:
  - Risk: users who relied on implicit GPT activation from env now need to
    select GPT explicitly.
  - Rollback: restore the implicit env-based provider switch.

## Verification Evidence

- `python -m unittest tests.test_launcher_env_config -v`
  passed, 6 tests OK
- `python -m unittest tests.test_agent_startup -v`
  passed, 172 tests OK
- `python scripts/check_constraints.py`
  passed, all constraints OK
- `python -m black --check launcher.py tests/test_launcher_env_config.py`
  passed
