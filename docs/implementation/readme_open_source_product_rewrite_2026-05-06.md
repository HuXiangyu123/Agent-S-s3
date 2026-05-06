# README Open Source Product Rewrite

Date: 2026-05-06

## Module Analysis

The existing root `README.md` still contains a large amount of upstream
Agent-S project material, including benchmark updates, paper descriptions,
generic SDK usage, and badges. This repository is now a Feishu desktop GUI
agent project built on top of Agent-S, so the public README should describe
this product first.

## Boundary

In scope:

- Rewrite the root README as this repository's open-source product entry.
- Cover introduction, architecture, installation, configuration, usage,
  evaluation artifacts, development checks, and upstream attribution.
- Keep Agent-S as an upstream reference instead of copying most upstream
  README content.

Out of scope:

- No runtime behavior changes.
- No config schema changes.
- No launcher UI changes.

## Target Files

- `README.md`

## Manual Plan

- Owner: Codex
- Depends on: current runtime architecture in `docs/process/project_state.md`
  and `docs/process/requirements_coverage_audit_2026-05-06.md`.
- Outputs: concise product README for a Windows-first Feishu GUI agent.
- Verification: documentation review plus existing startup/constraint checks.
- Risks / rollback: If the README omits an important upstream usage path, add
  it back as a short reference link instead of restoring the full upstream text.

## Verification Evidence

- `python -m unittest tests.test_agent_startup -v`
  passed, 172 tests OK
- `python scripts/check_constraints.py`
  passed, all constraints OK
