# Feishu Batch Evaluation Aggregation

Date: 2026-05-06

## Module Analysis

This implementation targets the M4 evaluation gap: per-run artifacts already
exist, but there is no batch-level aggregation across runs.

The feature is intentionally offline. It reads existing `summary.json` files
under `artifacts/test_runs/` and writes aggregate evaluation outputs. It does
not change `AgentS3`, `WindowsFeishuACI`, tool routing, detectors, verifiers, or
runtime execution.

## Boundary

In scope:

- Discover completed run summaries from an artifact root
- Aggregate success rate, duration, step counts, product/task grouping, and
  failure types from existing report data
- Write machine-readable and markdown evaluation reports
- Add focused unit tests using temporary summary fixtures

Out of scope:

- No live Feishu execution
- No dashboard UI
- No trend chart rendering
- No semantic trace or replay generation
- No screenshot-derived quantitative metadata

## Target Files

- `gui_agents/feishu/reports/evaluation_aggregator.py`
- `scripts/build_feishu_eval_report.py`
- `tests/feishu/reports/test_evaluation_aggregator.py`

## Manual Plan

- Owner: Codex
- Depends on: existing `summary.json` contract from `ReportBuilder`
- Outputs:
  - `evaluation_summary.json`
  - `evaluation_report.md`
- Verification:
  - focused unit tests for aggregation and file output
  - startup gate
  - architecture constraint check
- Risks / rollback:
  - If summary schema changes, aggregation can miss fields; keep defaults
    defensive and read-only.
  - Rollback by deleting the new module, CLI, and test.

## Design Choice

Evaluation metrics here come from runtime reports, not from screenshots or
page metadata. This is compatible with the semantic-only metadata rule: the
rule blocks coordinate-like or visual quantitative facts in extracted screen
metadata, while M4 explicitly requires run-level success, duration, and step
statistics.

The module has no dependency on the runtime hot path. Future dashboard work can
consume `evaluation_summary.json` without coupling back into agent execution.

## Verification Evidence

- `python -m unittest tests.feishu.reports.test_evaluation_aggregator -v`
  passed, 5 tests OK
- `python scripts/build_feishu_eval_report.py --artifact-root artifacts/test_runs --output-dir artifacts/evaluation`
  passed and wrote aggregate report paths
- `python -m unittest tests.test_agent_startup -v`
  passed, 170 tests OK
- `python scripts/check_constraints.py`
  passed, all constraints OK
- `python -m black --check gui_agents/feishu/reports/evaluation_aggregator.py scripts/build_feishu_eval_report.py tests/feishu/reports/test_evaluation_aggregator.py`
  passed
