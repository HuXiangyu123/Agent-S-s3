# CI Parity Checks 2026-05-06

## Scope

Add one shared check entry for local development and GitHub CI so the Feishu GUI Agent branch no longer relies on different validation paths before merge.

This round is about parity and stability, not new product behavior.

## Current State

Before this change:

- local verification was manual and inconsistent
- `.github/workflows/lint.yml` only ran `black --check gui_agents`
- startup smoke tests and launcher env tests were not part of GitHub CI
- Windows PowerShell could display UTF-8 Chinese as mojibake when no encoding was specified, creating false alarms during review

## Problem

The current setup allows three avoidable failure modes:

1. local passes because only ad hoc tests were run
2. GitHub fails because CI covers a different command set
3. maintainers misdiagnose encoding display issues as file corruption

## Boundaries

This change may:

- add a shared CI runner script
- update `AGENTS.md` to require the shared runner before submit
- update the GitHub workflow to call that same script
- fix confirmed mojibake literals that would otherwise keep formatting or tests unstable

This change must not:

- widen product scope
- add GUI runtime dependencies to the test path
- turn CI into a real desktop E2E runner

## Target Files

New files:

- `scripts/run_ci_checks.py`

Updated files:

- `AGENTS.md`
- `.github/workflows/lint.yml`
- `gui_agents/feishu/detectors/im_state_detector.py`
- `tests/feishu/locators/__init__.py`
- `gui_agents/s3/agents/worker.py` if formatting is required for parity

## Shared Check Contract

The parity entry should execute exactly these commands in order:

1. `python -m black --check launcher.py gui_agents tests`
2. `python -m unittest tests.test_agent_startup -v`
3. `python -m unittest tests.test_launcher_env_config -v`

Rationale:

- `tests.test_agent_startup` already aggregates the Feishu module suite
- `tests.test_launcher_env_config` covers launcher routing regressions not included in the startup suite
- `black --check` catches formatting drift that has already blocked CI before

## Verification

After implementation, run:

1. `python scripts/run_ci_checks.py`
2. any module-level tests touched by the implementation if the shared runner is insufficient

If a check still fails, record the exact blocking file or module instead of silently narrowing the CI scope.

## Risks

1. A shared script can still drift if developers edit the workflow directly.
   Mitigation: workflow should invoke the script instead of duplicating commands inline.

2. Formatting checks may fail on unrelated dirty files.
   Mitigation: report the exact file and either format it safely or stop and document the blocker.

3. Cross-platform import differences can break CI if GUI-only modules enter the test path.
   Mitigation: keep the parity suite limited to current import-safe unit and smoke tests.
