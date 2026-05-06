# Audit Remediation Track C D Connectivity 2026-05-06

## Scope

This round remediates the actionable findings from the audit without rewriting the current S3-enhanced Feishu path.

In scope:

- preserve the existing `classic_s3` and `feishu_agent` modes
- keep `feishu_agent` on `AgentS3 + WindowsFeishuACI`, not `FeishuWorker`
- add tests for `_feishu_exec.py` pure builders and CLI runtime mode selection
- replace silent exception swallowing in the user-facing launcher and trace-writing path with observable warnings

Out of scope:

- large-scale dedup of `s2` / `s2_5` / `s3`
- wildcard-import cleanup in legacy setup scripts
- fixture size reduction
- secrets rotation or env file redesign

## Current State

The audit was partly based on stale state and partly correct:

- `gui_agents/feishu/agents/__init__.py` and `gui_agents/feishu/locators/__init__.py` currently import valid files
- `gui_agents/feishu/agents/__init__.py` and `gui_agents/feishu/locators/__init__.py` currently import valid files
- `gui_agents/s3/cli_app.py` intentionally stays on the LLM-driven runtime path
- current `feishu_agent` mode runs `AgentS3 + WindowsFeishuACI`
- Track C remains a reusable internal module and is not exposed as an alternate non-LLM execution route
- Track D is connected to `feishu_agent` as a best-effort runtime recorder; it observes S3 loop facts but does not control execution

## Boundary Decision

Do not replace the current S3-enhanced Feishu route, and do not add a separate non-LLM workflow route.

Execution modes remain:

- `classic_s3`: legacy AgentS3
- `feishu_agent`: S3-enhanced Feishu path

Track C should only be consumed as an internal module or future enhancement inside the LLM-driven Feishu route.

Track D is allowed to observe the LLM-driven route and write runtime artifacts. It must not parse instructions into a deterministic workflow, call Track C workflows, or decide the next action.

## Target Files

Updated files:

- `gui_agents/s3/cli_app.py`
- `launcher.py`
- `gui_agents/s3/agents/grounding_feishu.py`
- `gui_agents/feishu/detectors/__init__.py`
- `gui_agents/feishu/locators/__init__.py`
- `tests/test_agent_startup.py`
- `tests/feishu/agents/test_cli_feishu_agent_route.py`
- `tests/feishu/reports/test_s3_cli_recorder_integration.py`
- `scripts/run_ci_checks.py`
- `AGENTS.md` only if the test entry changes

New files:

- `tests/feishu/tooling/test_feishu_exec_builders.py`

## Implementation Plan

1. Keep only `classic_s3` and `feishu_agent` as user-facing runtime modes.
2. Keep `feishu_agent` as the S3-enhanced path: `AgentS3 + WindowsFeishuACI`.
3. Add focused tests for `_feishu_exec.py` string builders.
4. Replace silent `except` blocks in launcher and trace writing with visible stderr warnings or trace diagnostics.
5. Wire Track D only as a passive recorder in the existing S3 loop.

## Depends On

- existing `WindowsFeishuACI`
- current Track A/B/C/D contracts remaining unchanged

## Outputs

- non-silent failure signals for launcher process-stop / output-read / config-load edge cases
- regression tests covering pure exec-code builders

## Verification

- `python -m unittest tests.test_agent_startup -v`
- `python -m unittest tests.test_launcher_env_config -v`
- `python -m black --check launcher.py gui_agents tests`
- `python scripts/run_ci_checks.py`

## Risks

1. Warning output could become noisy.
   Mitigation: only emit warnings on exceptional paths that were previously silent.

2. Track C remains underused at runtime until it is deliberately redesigned as LLM-route guidance or verification.
   Mitigation: keep it internal and do not expose a workflow execution mode.

3. Track D recorder could be mistaken for a controller.
   Mitigation: tests cover that recorder hooks consume observations/actions from `run_agent()` only.

## Rollback

If the remediation causes confusion or instability:

1. keep `classic_s3` and `feishu_agent` only
2. retain the added tests for builder coverage and warning behavior where they remain useful
