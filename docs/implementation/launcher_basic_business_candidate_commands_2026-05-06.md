# Launcher Basic Business Candidate Commands

Date: 2026-05-06

## Module Analysis

This implementation follows `docs/process/requirements_coverage_audit_2026-05-06.md`
and only updates launcher-side candidate instructions for basic business
coverage.

The audit shows that the active architecture already has semantic coverage for
IM, Docs, Calendar, Base, and VC, but the launcher fallback command list still
contains only two examples. One example also asks for random emoji behavior,
which is not a stable basic acceptance path.

## Boundary

In scope:

- Expand the launcher fallback candidate command list.
- Cover basic product entries from the audit: IM, Docs, Calendar, Base, VC.
- Merge new defaults into existing command history so current users see them.
- Add tests for coverage and history merge behavior.

Out of scope:

- No runtime execution changes.
- No parser, router, verifier, detector, or Worker changes.
- No deterministic workflow restoration.
- No screenshot-derived metadata changes.

## Target Files

- `launcher.py`
- `tests/test_launcher_candidate_commands.py`

## Manual Plan

- Owner: Codex
- Depends on: `requirements_coverage_audit_2026-05-06.md`
- Outputs:
  - broader launcher candidate commands
  - history/default merge behavior
  - launcher candidate command tests
- Verification:
  - launcher candidate command tests
  - launcher env tests
  - startup gate
  - architecture constraint check
- Risks / rollback:
  - Too many candidate commands could clutter the combobox; keep examples concise.
  - Some product paths are semantic/unit-covered but not live-stable; these are
    still useful launcher probes, not guaranteed acceptance evidence.
  - Rollback by restoring the old candidate list and removing the new test file.

## Verification Evidence

- `python -m unittest tests.test_launcher_candidate_commands tests.test_launcher_env_config -v`
  passed, 7 tests OK
- `python -m unittest tests.test_agent_startup -v`
  passed, 172 tests OK
- `python scripts/check_constraints.py`
  passed, all constraints OK
- `python -m black --check launcher.py tests/test_launcher_candidate_commands.py tests/test_launcher_env_config.py`
  passed
